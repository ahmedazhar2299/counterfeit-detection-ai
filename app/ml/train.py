from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import calibration_curve
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score, roc_curve
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from ..config import ARTIFACTS_DIR, BRAND_PRICE_BASELINES, MODEL_VERSION, SUSPICIOUS_PHRASES
from .data_gen import generate_dataset


def _try_get_structured_model(seed: int = 42):
    try:
        from xgboost import XGBClassifier

        return (
            XGBClassifier(
                n_estimators=250,
                max_depth=6,
                learning_rate=0.06,
                subsample=0.9,
                colsample_bytree=0.9,
                eval_metric="logloss",
                random_state=seed,
            ),
            "xgboost",
        )
    except Exception:
        return (
            RandomForestClassifier(
                n_estimators=260,
                max_depth=15,
                min_samples_leaf=2,
                random_state=seed,
            ),
            "random_forest",
        )


def _safe_div(a: pd.Series, b: pd.Series) -> pd.Series:
    return np.where(b > 0, a / b, 0.0)


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["brand_baseline"] = out["brand"].map(BRAND_PRICE_BASELINES).fillna(out["price"].median())
    out["price_ratio_to_typical"] = out["price"] / out["brand_baseline"].clip(lower=1)
    out["price_deviation_abs_log"] = np.abs(np.log(out["price_ratio_to_typical"].clip(lower=0.01)))
    out["price_too_low_flag"] = (out["price_ratio_to_typical"] < 0.45).astype(int)
    out["price_too_high_flag"] = (out["price_ratio_to_typical"] > 1.8).astype(int)
    out["seller_trust_score"] = (
        out["seller_rating"].fillna(3.5) * 0.45
        + np.log1p(out["seller_sales_count"].fillna(0)) * 0.25
        + np.log1p(out["seller_age_days"].fillna(0)) * 0.15
        + out["return_policy_days"].fillna(0) * 0.15 / 30
    )
    out["seller_new_flag"] = (out["seller_age_days"].fillna(0) < 60).astype(int)
    out["review_to_sales_ratio"] = _safe_div(out["review_count"].fillna(0), out["seller_sales_count"].fillna(0) + 1)
    out["text_combined"] = (out["title"].fillna("") + " " + out["description"].fillna("")).str.lower()
    out["suspicious_phrase_count"] = out["text_combined"].apply(lambda txt: sum(phrase in txt for phrase in SUSPICIOUS_PHRASES))
    return out


def train(data_path: Path | None = None, seed: int = 42) -> dict:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    if data_path and data_path.exists():
        df = pd.read_csv(data_path)
    else:
        df = generate_dataset(n_rows=6500, seed=seed)

    df = build_features(df)
    y = df["label"].astype(int)

    structured_cols_numeric = [
        "price",
        "seller_age_days",
        "seller_rating",
        "seller_sales_count",
        "review_count",
        "return_policy_days",
        "price_ratio_to_typical",
        "price_deviation_abs_log",
        "price_too_low_flag",
        "price_too_high_flag",
        "seller_trust_score",
        "seller_new_flag",
        "review_to_sales_ratio",
        "suspicious_phrase_count",
    ]
    structured_cols_categorical = ["brand", "category", "shipping_country", "currency"]

    x_train, x_test, y_train, y_test = train_test_split(df, y, test_size=0.2, random_state=seed, stratify=y)

    structured_model, structured_type = _try_get_structured_model(seed=seed)
    structured_pre = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), structured_cols_numeric),
            ("cat", OneHotEncoder(handle_unknown="ignore"), structured_cols_categorical),
        ]
    )
    structured_pipeline = Pipeline(steps=[("prep", structured_pre), ("model", structured_model)])
    structured_pipeline.fit(x_train, y_train)
    structured_prob_test = structured_pipeline.predict_proba(x_test)[:, 1]

    text_pipeline = Pipeline(
        steps=[
            (
                "tfidf",
                TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=8000, stop_words="english"),
            ),
            ("model", LogisticRegression(max_iter=2000)),
        ]
    )
    text_pipeline.fit(x_train["text_combined"], y_train)
    text_prob_test = text_pipeline.predict_proba(x_test["text_combined"])[:, 1]

    fused_prob_test = 0.6 * structured_prob_test + 0.4 * text_prob_test
    calibrator = LogisticRegression(max_iter=1000)
    calibrator.fit(np.column_stack([structured_prob_test, text_prob_test]), y_test)
    pred_label = (fused_prob_test >= 0.5).astype(int)

    roc_fpr, roc_tpr, _ = roc_curve(y_test, fused_prob_test)
    cal_true, cal_pred = calibration_curve(y_test, fused_prob_test, n_bins=10)

    metrics = {
        "precision": precision_score(y_test, pred_label),
        "recall": recall_score(y_test, pred_label),
        "f1": f1_score(y_test, pred_label),
        "roc_auc": roc_auc_score(y_test, fused_prob_test),
        "confusion_matrix": confusion_matrix(y_test, pred_label).tolist(),
        "roc_curve": {"fpr": roc_fpr.tolist(), "tpr": roc_tpr.tolist()},
        "calibration_curve": {"pred": cal_pred.tolist(), "true": cal_true.tolist()},
        "model_types": {
            "structured": structured_type,
            "text": "tfidf_logreg",
            "fusion": "weighted+logreg_calibrator",
        },
    }

    trained_at = datetime.now(UTC).isoformat()
    joblib.dump(structured_pipeline, ARTIFACTS_DIR / "structured_model.joblib")
    joblib.dump(text_pipeline, ARTIFACTS_DIR / "text_model.joblib")
    joblib.dump(calibrator, ARTIFACTS_DIR / "fusion_calibrator.joblib")
    x_train[structured_cols_numeric + structured_cols_categorical + ["text_combined"]].to_csv(
        ARTIFACTS_DIR / "feature_sample.csv",
        index=False,
    )

    metadata = {
        "version": MODEL_VERSION,
        "trained_at": trained_at,
        "structured_columns": {"numeric": structured_cols_numeric, "categorical": structured_cols_categorical},
        "suspicious_phrases": SUSPICIOUS_PHRASES,
    }

    with open(ARTIFACTS_DIR / "metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    with open(ARTIFACTS_DIR / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    return {"metrics": metrics, "metadata": metadata}


if __name__ == "__main__":
    print(json.dumps(train()["metrics"], indent=2))
