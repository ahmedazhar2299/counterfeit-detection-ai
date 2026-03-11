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
from sklearn.inspection import permutation_importance
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
                n_estimators=240,
                max_depth=10,
                min_samples_leaf=4,
                min_samples_split=8,
                max_features="sqrt",
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


def _feature_names_from_preprocessor(preprocessor: ColumnTransformer) -> list[str]:
    names: list[str] = []
    for transformer_name, transformer, columns in preprocessor.transformers_:
        if transformer_name == "remainder":
            continue
        if transformer_name == "num":
            names.extend(list(columns))
            continue
        if hasattr(transformer, "get_feature_names_out"):
            transformed = transformer.get_feature_names_out(columns)
            names.extend([str(name) for name in transformed])
            continue
        names.extend(list(columns))
    return names


def _compute_feature_importance(
    pipeline: Pipeline,
    x_eval: pd.DataFrame,
    y_eval: pd.Series,
    top_k: int = 12,
) -> dict:
    prep = pipeline.named_steps["prep"]
    model = pipeline.named_steps["model"]
    feature_names = _feature_names_from_preprocessor(prep)
    transformed = prep.transform(x_eval)

    try:
        import shap  # type: ignore

        sample = transformed[: min(250, transformed.shape[0])]
        sample_dense = sample.toarray() if hasattr(sample, "toarray") else sample
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(sample_dense)
        if isinstance(shap_values, list):
            shap_values = shap_values[1] if len(shap_values) > 1 else shap_values[0]
        importance = np.abs(np.asarray(shap_values)).mean(axis=0)
        method = "shap"
    except Exception:
        if hasattr(model, "feature_importances_"):
            importance = np.asarray(model.feature_importances_)
            method = "model_importance"
        else:
            result = permutation_importance(
                pipeline,
                x_eval,
                y_eval,
                n_repeats=6,
                random_state=42,
                scoring="roc_auc",
            )
            importance = np.asarray(result.importances_mean)
            method = "permutation"

    pairs = []
    for index, raw_name in enumerate(feature_names[: len(importance)]):
        pairs.append(
            {
                "feature": raw_name.replace("brand_", "brand: ").replace("category_", "category: ").replace("shipping_country_", "ship: "),
                "importance": round(float(importance[index]), 6),
            }
        )
    pairs.sort(key=lambda item: item["importance"], reverse=True)
    return {"method": method, "items": pairs[:top_k]}


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
                TfidfVectorizer(ngram_range=(1, 2), min_df=3, max_df=0.92, max_features=7000, stop_words="english"),
            ),
            ("model", LogisticRegression(max_iter=2000, C=0.95)),
        ]
    )
    text_pipeline.fit(x_train["text_combined"], y_train)
    structured_prob_train = structured_pipeline.predict_proba(x_train)[:, 1]
    text_prob_train = text_pipeline.predict_proba(x_train["text_combined"])[:, 1]
    text_prob_test = text_pipeline.predict_proba(x_test["text_combined"])[:, 1]

    fused_prob_train = 0.6 * structured_prob_train + 0.4 * text_prob_train
    fused_prob_test = 0.6 * structured_prob_test + 0.4 * text_prob_test
    calibrator = LogisticRegression(max_iter=1000)
    calibrator.fit(np.column_stack([structured_prob_test, text_prob_test]), y_test)
    pred_label_train = (fused_prob_train >= 0.5).astype(int)
    pred_label = (fused_prob_test >= 0.5).astype(int)

    roc_fpr, roc_tpr, _ = roc_curve(y_test, fused_prob_test)
    cal_true, cal_pred = calibration_curve(y_test, fused_prob_test, n_bins=10)
    feature_importance = _compute_feature_importance(structured_pipeline, x_test, y_test)

    metrics = {
        "precision": precision_score(y_test, pred_label),
        "recall": recall_score(y_test, pred_label),
        "f1": f1_score(y_test, pred_label),
        "roc_auc": roc_auc_score(y_test, fused_prob_test),
        "train_accuracy": float(np.mean(pred_label_train == y_train)),
        "test_accuracy": float(np.mean(pred_label == y_test)),
        "train_error": float(1.0 - np.mean(pred_label_train == y_train)),
        "test_error": float(1.0 - np.mean(pred_label == y_test)),
        "confusion_matrix": confusion_matrix(y_test, pred_label).tolist(),
        "roc_curve": {"fpr": roc_fpr.tolist(), "tpr": roc_tpr.tolist()},
        "calibration_curve": {"pred": cal_pred.tolist(), "true": cal_true.tolist()},
        "dataset_profile": {
            "row_count": int(len(df)),
            "class_balance": {
                "legit": int((y == 0).sum()),
                "counterfeit": int((y == 1).sum()),
            },
        },
        "feature_importance": feature_importance,
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
