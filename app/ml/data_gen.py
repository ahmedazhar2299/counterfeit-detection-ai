from __future__ import annotations

import random
from pathlib import Path

import numpy as np
import pandas as pd

from ..config import BRAND_PRICE_BASELINES, DATA_DIR, SUSPICIOUS_PHRASES

CATEGORIES = ["Sneakers", "Watches", "Handbags", "Electronics", "Audio", "Cameras"]
COUNTRIES = ["US", "GB", "DE", "JP", "CN", "AE", "TR", "IN"]


def _gen_text(brand: str, category: str, suspicious: bool) -> tuple[str, str]:
    normal_titles = [
        f"{brand} {category} in excellent condition",
        f"Original {brand} {category} with full packaging",
        f"Verified {brand} {category} listing",
    ]
    suspicious_titles = [
        f"{brand} {category} {random.choice(SUSPICIOUS_PHRASES)}",
        f"{brand} {category} premium {random.choice(SUSPICIOUS_PHRASES)} deal",
        f"Luxury {brand} {random.choice(SUSPICIOUS_PHRASES)} item",
    ]
    normal_desc = [
        "Purchased from official store. Invoice and original box included.",
        "Serial number available. Fast shipping and returns accepted.",
        "Minimal wear. Verified authenticity by trusted reseller.",
    ]
    suspicious_desc = [
        "No receipt available. Perfect copy and hard to tell.",
        "Factory source stock, no box but same quality as original.",
        "DM for wholesale and better price, limited details.",
    ]
    return (
        random.choice(suspicious_titles if suspicious else normal_titles),
        random.choice(suspicious_desc if suspicious else normal_desc),
    )


def generate_dataset(n_rows: int = 5000, seed: int = 42, out_path: Path | None = None) -> pd.DataFrame:
    random.seed(seed)
    np.random.seed(seed)

    brands = list(BRAND_PRICE_BASELINES.keys())
    rows: list[dict] = []

    for _ in range(n_rows):
        brand = random.choice(brands)
        category = random.choice(CATEGORIES)
        baseline = BRAND_PRICE_BASELINES[brand]
        is_counterfeit = np.random.binomial(1, 0.28)

        if is_counterfeit:
            price = max(10, np.random.normal(baseline * 0.22, baseline * 0.08))
            seller_age_days = int(np.clip(np.random.normal(30, 35), 0, 3650))
            seller_rating = float(np.clip(np.random.normal(2.9, 0.9), 1.0, 5.0))
            seller_sales = int(np.clip(np.random.normal(35, 40), 0, 10000))
            review_count = int(np.clip(np.random.normal(6, 9), 0, 100000))
            return_policy_days = int(np.clip(np.random.normal(3, 4), 0, 30))
            suspicious_text = np.random.binomial(1, 0.72) == 1
        else:
            price = max(15, np.random.normal(baseline * 0.96, baseline * 0.18))
            seller_age_days = int(np.clip(np.random.normal(640, 420), 0, 3650))
            seller_rating = float(np.clip(np.random.normal(4.5, 0.35), 1.0, 5.0))
            seller_sales = int(np.clip(np.random.normal(720, 530), 0, 100000))
            review_count = int(np.clip(np.random.normal(290, 230), 0, 100000))
            return_policy_days = int(np.clip(np.random.normal(24, 12), 0, 90))
            suspicious_text = np.random.binomial(1, 0.03) == 1

        title, description = _gen_text(brand, category, suspicious_text)
        rows.append(
            {
                "title": title,
                "description": description,
                "brand": brand,
                "category": category,
                "price": round(float(price), 2),
                "currency": "USD",
                "seller_age_days": seller_age_days,
                "seller_rating": round(seller_rating, 2),
                "seller_sales_count": seller_sales,
                "review_count": review_count,
                "shipping_country": random.choice(COUNTRIES),
                "return_policy_days": return_policy_days,
                "label": int(is_counterfeit),
            }
        )

    df = pd.DataFrame(rows)
    output_path = out_path or (DATA_DIR / "listings.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    return df


if __name__ == "__main__":
    frame = generate_dataset()
    print(f"Generated {len(frame)} rows")
