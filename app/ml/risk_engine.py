from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from ..config import ARTIFACTS_DIR, DEFAULT_THRESHOLDS, MODEL_VERSION, SUSPICIOUS_PHRASES
from .train import build_features, train


@dataclass
class RiskResult:
    structured_prob: float
    text_prob: float
    fused_prob: float
    risk_score: float
    action: str
    explanations: list[dict]
    highlights: list[dict]
    model_version: str
    training_timestamp: str


class RiskEngine:
    def __init__(self, artifacts_dir: Path = ARTIFACTS_DIR):
        self.artifacts_dir = artifacts_dir
        self._ensure_artifacts()
        self._load()

    def _ensure_artifacts(self) -> None:
        required = [
            self.artifacts_dir / "structured_model.joblib",
            self.artifacts_dir / "text_model.joblib",
            self.artifacts_dir / "metadata.json",
            self.artifacts_dir / "metrics.json",
        ]
        if not all(path.exists() for path in required):
            train()

    def _load(self) -> None:
        self.structured_model = joblib.load(self.artifacts_dir / "structured_model.joblib")
        self.text_model = joblib.load(self.artifacts_dir / "text_model.joblib")
        self.calibrator = joblib.load(self.artifacts_dir / "fusion_calibrator.joblib")
        with open(self.artifacts_dir / "metadata.json", "r", encoding="utf-8") as f:
            self.metadata = json.load(f)
        with open(self.artifacts_dir / "metrics.json", "r", encoding="utf-8") as f:
            self.metrics = json.load(f)

    def _action_from_score(self, score: float) -> str:
        if score <= DEFAULT_THRESHOLDS["approve_max"]:
            return "APPROVE"
        if score <= DEFAULT_THRESHOLDS["review_max"]:
            return "REVIEW"
        return "BLOCK"

    def _extract_highlights(self, text: str) -> list[dict]:
        hits: list[dict] = []
        lowered = text.lower()
        for phrase in SUSPICIOUS_PHRASES:
            for match in re.finditer(re.escape(phrase), lowered):
                hits.append({"phrase": phrase, "start": match.start(), "end": match.end()})
        return hits

    def _text_explanations(self, text: str) -> list[dict]:
        tfidf = self.text_model.named_steps["tfidf"]
        model = self.text_model.named_steps["model"]
        vec = tfidf.transform([text])
        feature_names = np.array(tfidf.get_feature_names_out())
        coefs = model.coef_[0]
        non_zero = vec.nonzero()[1]
        contrib: list[tuple[str, float]] = []
        for idx in non_zero:
            score = float(coefs[idx] * vec[0, idx])
            contrib.append((feature_names[idx], score))
        contrib.sort(key=lambda item: abs(item[1]), reverse=True)
        return [
            {
                "source": "text",
                "feature": token,
                "contribution": round(score, 4),
                "detail": f"Text token '{token}' contributed {score:+.3f}.",
            }
            for token, score in contrib[:5]
        ]

    def _structured_explanations(self, frame: pd.DataFrame) -> list[dict]:
        row = frame.iloc[0]
        items = [
            ("price_ratio_to_typical", float(row["price_ratio_to_typical"])),
            ("seller_trust_score", float(row["seller_trust_score"])),
            ("seller_new_flag", float(row["seller_new_flag"])),
            ("review_to_sales_ratio", float(row["review_to_sales_ratio"])),
            ("suspicious_phrase_count", float(row["suspicious_phrase_count"])),
        ]
        items.sort(key=lambda item: abs(item[1]), reverse=True)
        return [
            {
                "source": "structured",
                "feature": name,
                "contribution": round(value, 4),
                "detail": f"Observed {name}={value:.3f}.",
            }
            for name, value in items[:5]
        ]

    def analyze(self, payload: dict) -> RiskResult:
        row = build_features(pd.DataFrame([payload]))
        structured_prob = float(self.structured_model.predict_proba(row)[:, 1][0])
        text_input = row["text_combined"].iloc[0]
        text_prob = float(self.text_model.predict_proba([text_input])[:, 1][0])
        fused_default = 0.6 * structured_prob + 0.4 * text_prob
        fused_prob = float(self.calibrator.predict_proba([[structured_prob, text_prob]])[:, 1][0])
        fused_prob = 0.5 * fused_prob + 0.5 * fused_default
        risk_score = round(min(100.0, max(0.0, fused_prob * 100)), 2)
        action = self._action_from_score(risk_score)
        description = str(payload.get("description", ""))

        explanations = self._structured_explanations(row) + self._text_explanations(text_input) + [
            {
                "source": "fusion",
                "feature": "weighted_fusion",
                "contribution": round(fused_prob, 4),
                "detail": f"Fusion combined structured={structured_prob:.3f} and text={text_prob:.3f}.",
            }
        ]
        explanations.sort(key=lambda item: abs(item["contribution"]), reverse=True)

        return RiskResult(
            structured_prob=round(structured_prob, 4),
            text_prob=round(text_prob, 4),
            fused_prob=round(fused_prob, 4),
            risk_score=risk_score,
            action=action,
            explanations=explanations[:10],
            highlights=self._extract_highlights(description),
            model_version=self.metadata.get("version", MODEL_VERSION),
            training_timestamp=self.metadata.get("trained_at", datetime.now(UTC).isoformat()),
        )


engine_singleton: RiskEngine | None = None


def get_engine() -> RiskEngine:
    global engine_singleton
    if engine_singleton is None:
        engine_singleton = RiskEngine()
    return engine_singleton
