from __future__ import annotations

import ast
from typing import Any

import pandas as pd

AMAZON_PRODUCTS_URL = (
    "https://raw.githubusercontent.com/luminati-io/eCommerce-dataset-samples/main/amazon-products.csv"
)
FAKE_REVIEW_DATASET = "debojit01/fake-review-dataset"


def _normalize_columns(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy()
    frame.columns = [str(col).strip().lower().replace(" ", "_") for col in frame.columns]
    return frame


def _pick(row: dict[str, Any], *keys: str, default: Any = None) -> Any:
    for key in keys:
        value = row.get(key)
        if value is not None and str(value).strip() not in {"", "nan", "None"}:
            return value
    return default


def _parse_price(raw_value: Any) -> float:
    if raw_value is None:
        return 0.0
    text = str(raw_value).replace("$", "").replace(",", "").strip()
    try:
        return float(text)
    except Exception:
        return 0.0


def _parse_category(raw_value: Any) -> str:
    if raw_value is None:
        return "General"
    text = str(raw_value).strip()
    if not text:
        return "General"
    try:
        parsed = ast.literal_eval(text)
        if isinstance(parsed, list) and parsed:
            return str(parsed[0]).strip() or "General"
    except Exception:
        pass
    if ">" in text:
        return text.split(">")[0].strip() or "General"
    return text[:60]


def load_public_product_catalog(limit: int = 3000) -> list[dict[str, Any]]:
    """
    Public product catalog anchor dataset.
    Source: Bright Data / luminati-io eCommerce dataset samples on GitHub.
    """
    try:
        frame = pd.read_csv(AMAZON_PRODUCTS_URL)
        frame = _normalize_columns(frame)
        rows: list[dict[str, Any]] = []
        sample = frame.head(limit).to_dict(orient="records")
        for row in sample:
            price = _parse_price(_pick(row, "final_price", "price", "initial_price"))
            if price <= 0:
                continue
            brand = str(_pick(row, "brand", default="Generic")).strip() or "Generic"
            rating = float(_pick(row, "rating", "stars", default=4.2) or 4.2)
            reviews = int(float(_pick(row, "reviews_count", "ratings_total", default=80) or 80))
            title = str(_pick(row, "title", "name", default="Marketplace listing")).strip()
            description = str(_pick(row, "description", "bullet_points", "about_this_item", default=title)).strip()
            category = _parse_category(_pick(row, "categories", "category", default="General"))
            rows.append(
                {
                    "title": title,
                    "description": description,
                    "brand": brand,
                    "category": category,
                    "price": round(price, 2),
                    "currency": "USD",
                    "seller_age_days": 540,
                    "seller_rating": max(1.0, min(5.0, rating)),
                    "seller_sales_count": max(10, reviews * 3),
                    "review_count": max(0, reviews),
                    "shipping_country": "US",
                    "return_policy_days": 30,
                    "label": 0,
                    "public_source": "luminati-io/eCommerce-dataset-samples",
                }
            )
        return rows
    except Exception:
        return []


def load_public_review_text(limit: int = 3000) -> list[dict[str, Any]]:
    """
    Public deceptive-review augmentation from Hugging Face.
    This improves text realism for suspicious language.
    """
    try:
        from datasets import load_dataset

        dataset = load_dataset(FAKE_REVIEW_DATASET, split="train")
        rows: list[dict[str, Any]] = []
        sample_size = min(limit, len(dataset))
        for row in dataset.select(range(sample_size)):
            label = 1 if str(row.get("label", "")).upper() == "CG" else 0
            rows.append(
                {
                    "title": "Public review sample",
                    "description": row.get("text_", "") or "",
                    "brand": "Generic",
                    "category": "PublicReview",
                    "price": 100.0,
                    "currency": "USD",
                    "seller_age_days": 365,
                    "seller_rating": float(row.get("rating", 4.0) or 4.0),
                    "seller_sales_count": 200,
                    "review_count": 80,
                    "shipping_country": "US",
                    "return_policy_days": 14,
                    "label": label,
                    "public_source": FAKE_REVIEW_DATASET,
                }
            )
        return rows
    except Exception:
        return []
