from __future__ import annotations

import csv
import io
import json
from pathlib import Path

from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.orm import Session

from .config import ARTIFACTS_DIR, DEFAULT_THRESHOLDS
from .database import Base, engine, get_db
from .llm import maybe_generate_llm_summary
from .ml.risk_engine import get_engine
from .models import Analysis, Feedback, Listing, TrainingRun
from .schemas import (
    AnalysisResponse,
    CsvAnalyzeResponse,
    FeedbackRequest,
    FeedbackResponse,
    ListingInput,
    ListingResponse,
    ListingWithAnalysis,
    MetricsResponse,
    ModelInfoResponse,
)

Base.metadata.create_all(bind=engine)


def _ensure_analysis_columns() -> None:
    with engine.begin() as connection:
        columns = {
            row[1]
            for row in connection.execute(text("PRAGMA table_info(analyses)")).fetchall()
        }
        if "llm_summary" not in columns:
            connection.execute(text("ALTER TABLE analyses ADD COLUMN llm_summary TEXT"))
        if "llm_provider" not in columns:
            connection.execute(text("ALTER TABLE analyses ADD COLUMN llm_provider VARCHAR(32)"))


_ensure_analysis_columns()

app = FastAPI(title="CounterfeitGuard API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _analysis_to_response(analysis: Analysis) -> AnalysisResponse:
    return AnalysisResponse(
        analysis_id=analysis.id,
        listing_id=analysis.listing_id,
        risk_score=analysis.risk_score,
        action=analysis.action,
        structured_prob=analysis.structured_prob,
        text_prob=analysis.text_prob,
        fused_prob=analysis.fused_prob,
        llm_summary=analysis.llm_summary,
        llm_provider=analysis.llm_provider,
        explanations=analysis.explanations_json,
        highlights=analysis.highlights_json,
        model={
            "version": analysis.model_version,
            "training_timestamp": analysis.training_timestamp or "unknown",
        },
    )


def _listing_to_response(listing: Listing) -> ListingResponse:
    return ListingResponse(
        id=listing.id,
        title=listing.title,
        description=listing.description,
        brand=listing.brand,
        category=listing.category,
        price=listing.price,
        currency=listing.currency,
        seller_age_days=listing.seller_age_days,
        seller_rating=listing.seller_rating,
        seller_sales_count=listing.seller_sales_count,
        review_count=listing.review_count,
        shipping_country=listing.shipping_country,
        return_policy_days=listing.return_policy_days,
        created_at=listing.created_at,
    )


async def _persist_analysis(payload: ListingInput, db: Session, include_llm: bool = True) -> AnalysisResponse:
    listing = Listing(**payload.model_dump())
    db.add(listing)
    db.flush()

    result = get_engine().analyze(payload.model_dump())
    if include_llm:
        llm = await maybe_generate_llm_summary(
            payload=payload.model_dump(),
            action=result.action,
            risk_score=result.risk_score,
            structured_prob=result.structured_prob,
            text_prob=result.text_prob,
            fused_prob=result.fused_prob,
            explanations=result.explanations,
            highlights=result.highlights,
        )
        llm_summary = llm.summary
        llm_provider = llm.provider
    else:
        llm_summary = None
        llm_provider = None

    analysis = Analysis(
        listing_id=listing.id,
        structured_prob=result.structured_prob,
        text_prob=result.text_prob,
        fused_prob=result.fused_prob,
        risk_score=result.risk_score,
        action=result.action,
        explanations_json=result.explanations,
        highlights_json=result.highlights,
        llm_summary=llm_summary,
        llm_provider=llm_provider,
        model_version=result.model_version,
        training_timestamp=result.training_timestamp,
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return _analysis_to_response(analysis)


def _csv_row_to_payload(row: dict[str, str]) -> dict:
    norm = {str(k).strip(): (str(v).strip() if v is not None else "") for k, v in row.items()}
    return {
        "title": norm.get("title", ""),
        "description": norm.get("description", ""),
        "brand": norm.get("brand", ""),
        "category": norm.get("category", ""),
        "price": norm.get("price", ""),
        "currency": norm.get("currency", "") or "USD",
        "seller_age_days": norm.get("seller_age_days") or None,
        "seller_rating": norm.get("seller_rating") or None,
        "seller_sales_count": norm.get("seller_sales_count") or None,
        "review_count": norm.get("review_count") or None,
        "shipping_country": norm.get("shipping_country") or None,
        "return_policy_days": norm.get("return_policy_days") or None,
    }


@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze_listing(payload: ListingInput, db: Session = Depends(get_db)):
    return await _persist_analysis(payload=payload, db=db, include_llm=True)


@app.post("/api/analyze-csv", response_model=CsvAnalyzeResponse)
async def analyze_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a valid .csv file")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="CSV file is empty")

    try:
        text_content = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="CSV must be UTF-8 encoded")

    reader = csv.DictReader(io.StringIO(text_content))
    if not reader.fieldnames:
        raise HTTPException(status_code=400, detail="CSV must include a header row")

    required = {"title", "description", "brand", "category", "price"}
    headers = {h.strip() for h in reader.fieldnames if h}
    missing = sorted(required - headers)
    if missing:
        raise HTTPException(status_code=400, detail=f"CSV missing required columns: {', '.join(missing)}")

    results: list[AnalysisResponse] = []
    errors: list[dict] = []
    max_rows = 500

    for row_index, row in enumerate(reader, start=2):
        if row_index > max_rows + 1:
            errors.append({"row": row_index, "message": f"Row limit exceeded ({max_rows}). Remaining rows skipped."})
            break
        if not row:
            continue
        raw_payload = _csv_row_to_payload(row)
        try:
            payload = ListingInput.model_validate(raw_payload)
        except ValidationError as exc:
            msg = exc.errors()[0]["msg"] if exc.errors() else "Validation failed"
            errors.append({"row": row_index, "message": msg})
            continue
        try:
            analysis = await _persist_analysis(payload=payload, db=db, include_llm=False)
            results.append(analysis)
        except Exception as exc:
            errors.append({"row": row_index, "message": f"Analysis failed: {type(exc).__name__}"})

    return CsvAnalyzeResponse(
        imported=len(results),
        failed=len(errors),
        results=results,
        errors=errors,
    )


@app.get("/api/listings", response_model=list[ListingWithAnalysis])
def list_listings(limit: int = Query(default=50, ge=1, le=200), db: Session = Depends(get_db)):
    rows = db.query(Listing).order_by(Listing.created_at.desc()).limit(limit).all()
    out: list[ListingWithAnalysis] = []
    for listing in rows:
        latest = db.query(Analysis).filter(Analysis.listing_id == listing.id).order_by(Analysis.created_at.desc()).first()
        out.append(ListingWithAnalysis(listing=_listing_to_response(listing), latest_analysis=_analysis_to_response(latest) if latest else None))
    return out


@app.get("/api/listings/{listing_id}", response_model=ListingWithAnalysis)
def get_listing(listing_id: int, db: Session = Depends(get_db)):
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    latest = db.query(Analysis).filter(Analysis.listing_id == listing.id).order_by(Analysis.created_at.desc()).first()
    return ListingWithAnalysis(listing=_listing_to_response(listing), latest_analysis=_analysis_to_response(latest) if latest else None)


@app.post("/api/feedback", response_model=FeedbackResponse)
def submit_feedback(payload: FeedbackRequest, db: Session = Depends(get_db)):
    analysis = db.query(Analysis).filter(Analysis.id == payload.analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    fb = Feedback(analysis_id=payload.analysis_id, label=payload.label, notes=payload.notes)
    db.add(fb)
    db.commit()
    db.refresh(fb)
    return FeedbackResponse(id=fb.id, analysis_id=fb.analysis_id, label=fb.label, notes=fb.notes, created_at=fb.created_at)


@app.get("/api/metrics", response_model=MetricsResponse)
def get_metrics(db: Session = Depends(get_db)):
    metrics_path = ARTIFACTS_DIR / "metrics.json"
    if not metrics_path.exists():
        get_engine()
    with open(metrics_path, "r", encoding="utf-8") as f:
        metrics = json.load(f)
    with open(ARTIFACTS_DIR / "metadata.json", "r", encoding="utf-8") as f:
        metadata = json.load(f)

    existing = db.query(TrainingRun).filter(TrainingRun.model_version == metadata["version"]).order_by(TrainingRun.created_at.desc()).first()
    if not existing:
        db.add(
            TrainingRun(
                model_version=metadata["version"],
                metrics_json=metrics,
                artifacts_json={
                    "structured_model": str(Path("backend/artifacts/structured_model.joblib")),
                    "text_model": str(Path("backend/artifacts/text_model.joblib")),
                    "fusion_calibrator": str(Path("backend/artifacts/fusion_calibrator.joblib")),
                    "metrics": str(Path("backend/artifacts/metrics.json")),
                },
            )
        )
        db.commit()

    analyses = db.query(Analysis).order_by(Analysis.created_at.asc()).all()
    feedback_rows = db.query(Feedback).all()

    action_counts = {"APPROVE": 0, "REVIEW": 0, "BLOCK": 0}
    score_bands = {"0-39": 0, "40-69": 0, "70-100": 0}
    daily_volume: dict[str, int] = {}

    for row in analyses:
        action_counts[row.action] = action_counts.get(row.action, 0) + 1
        if row.risk_score <= 39:
            score_bands["0-39"] += 1
        elif row.risk_score <= 69:
            score_bands["40-69"] += 1
        else:
            score_bands["70-100"] += 1
        day_key = row.created_at.strftime("%Y-%m-%d")
        daily_volume[day_key] = daily_volume.get(day_key, 0) + 1

    total_analyses = len(analyses)
    avg_risk = round(sum(row.risk_score for row in analyses) / total_analyses, 2) if analyses else 0.0
    latest_risk = analyses[-1].risk_score if analyses else None

    live_marketplace = {
        "summary": {
            "total_analyses": total_analyses,
            "total_feedback": len(feedback_rows),
            "average_risk_score": avg_risk,
            "latest_risk_score": latest_risk,
        },
        "action_counts": action_counts,
        "score_bands": score_bands,
        "daily_volume": [{"date": key, "count": value} for key, value in sorted(daily_volume.items())],
    }

    return MetricsResponse(model_validation=metrics, live_marketplace=live_marketplace)


@app.get("/api/model-info", response_model=ModelInfoResponse)
def model_info():
    meta_path = ARTIFACTS_DIR / "metadata.json"
    if not meta_path.exists():
        get_engine()
    with open(meta_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)
    return ModelInfoResponse(
        version=metadata["version"],
        trained_at=metadata["trained_at"],
        thresholds=DEFAULT_THRESHOLDS,
        artifacts={
            "structured": "backend/artifacts/structured_model.joblib",
            "text": "backend/artifacts/text_model.joblib",
            "fusion": "backend/artifacts/fusion_calibrator.joblib",
            "metrics": "backend/artifacts/metrics.json",
        },
    )
