from __future__ import annotations

import random
from pathlib import Path

import numpy as np
import pandas as pd

from ..config import BRAND_PRICE_BASELINES, DATA_DIR, SUSPICIOUS_PHRASES
from .public_data import load_public_product_catalog, load_public_review_text

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


def _maybe_inject_marketplace_noise(
    title: str,
    description: str,
    is_counterfeit: int,
    seller_rating: float,
    seller_age_days: int,
) -> tuple[str, str]:
    # Legit listings can still look messy, and strong counterfeit sellers can look polished.
    legit_noisy_phrases = [
        "No box included but purchased from brand store.",
        "Receipt misplaced after moving, serial available on request.",
        "Open-box unit with minor wear from personal collection.",
    ]
    counterfeit_polished_phrases = [
        "Includes invoice photo on request and tracked shipping.",
        "Trusted repeat seller with premium packaging presentation.",
        "Looks authentic in hand and ships with fast dispatch.",
    ]

    if is_counterfeit:
        if seller_rating > 4.2 and seller_age_days > 180 and np.random.binomial(1, 0.22):
            description = f"{description} {random.choice(counterfeit_polished_phrases)}"
    else:
        if np.random.binomial(1, 0.1):
            description = f"{description} {random.choice(legit_noisy_phrases)}"
        if np.random.binomial(1, 0.05):
            title = title.replace("Original", "Open Box").replace("Verified", "Resale")

    return title, description


def generate_dataset(
    n_rows: int = 15000,
    seed: int = 42,
    out_path: Path | None = None,
    include_public_text: bool = True,
) -> pd.DataFrame:
    random.seed(seed)
    np.random.seed(seed)

    brands = list(BRAND_PRICE_BASELINES.keys())
    rows: list[dict] = []
    target_public_rows = min(3000, max(0, n_rows // 5)) if include_public_text else 0
    synthetic_rows = max(0, n_rows - target_public_rows)
    public_catalog = load_public_product_catalog(limit=min(4000, max(500, synthetic_rows // 2)))
    use_public_catalog = len(public_catalog) > 0

    for _ in range(synthetic_rows):
        anchor = random.choice(public_catalog) if use_public_catalog and np.random.binomial(1, 0.78) else None
        brand = str(anchor["brand"]) if anchor else random.choice(brands)
        category = str(anchor["category"]) if anchor else random.choice(CATEGORIES)
        baseline = BRAND_PRICE_BASELINES.get(brand, float(anchor["price"]) if anchor else 250.0)
        is_counterfeit = np.random.binomial(1, 0.40)

        if is_counterfeit:
            if np.random.binomial(1, 0.22):
                price = max(10, np.random.normal(baseline * 2.4, baseline * 0.8))
            else:
                price = max(10, np.random.normal(baseline * 0.56, baseline * 0.27))

            # Some counterfeit sellers are sophisticated and look stronger on paper.
            if np.random.binomial(1, 0.24):
                seller_age_days = int(np.clip(np.random.normal(320, 230), 0, 3650))
                seller_rating = float(np.clip(np.random.normal(4.0, 0.45), 1.0, 5.0))
                seller_sales = int(np.clip(np.random.normal(250, 190), 0, 10000))
                review_count = int(np.clip(np.random.normal(82, 62), 0, 100000))
                return_policy_days = int(np.clip(np.random.normal(16, 10), 0, 40))
                suspicious_text = np.random.binomial(1, 0.32) == 1
            else:
                seller_age_days = int(np.clip(np.random.normal(120, 135), 0, 3650))
                seller_rating = float(np.clip(np.random.normal(3.42, 0.72), 1.0, 5.0))
                seller_sales = int(np.clip(np.random.normal(92, 130), 0, 10000))
                review_count = int(np.clip(np.random.normal(26, 34), 0, 100000))
                return_policy_days = int(np.clip(np.random.normal(10, 9), 0, 40))
                suspicious_text = np.random.binomial(1, 0.48) == 1
        else:
            if np.random.binomial(1, 0.14):
                price = max(15, np.random.normal(baseline * 0.8, baseline * 0.21))
                seller_age_days = int(np.clip(np.random.normal(250, 220), 0, 3650))
                seller_rating = float(np.clip(np.random.normal(4.08, 0.5), 1.0, 5.0))
                seller_sales = int(np.clip(np.random.normal(260, 180), 0, 100000))
                review_count = int(np.clip(np.random.normal(92, 74), 0, 100000))
                return_policy_days = int(np.clip(np.random.normal(15, 11), 0, 90))
                suspicious_text = np.random.binomial(1, 0.1) == 1
            else:
                price = max(15, np.random.normal(baseline * 0.99, baseline * 0.29))
                seller_age_days = int(np.clip(np.random.normal(520, 390), 0, 3650))
                seller_rating = float(np.clip(np.random.normal(4.25, 0.46), 1.0, 5.0))
                seller_sales = int(np.clip(np.random.normal(560, 430), 0, 100000))
                review_count = int(np.clip(np.random.normal(225, 180), 0, 100000))
                return_policy_days = int(np.clip(np.random.normal(20, 15), 0, 90))
                suspicious_text = np.random.binomial(1, 0.07) == 1

        if anchor and not suspicious_text and np.random.binomial(1, 0.75):
            title = str(anchor["title"])
            description = str(anchor["description"])
        else:
            title, description = _gen_text(brand, category, suspicious_text)

        title, description = _maybe_inject_marketplace_noise(title, description, int(is_counterfeit), float(seller_rating), int(seller_age_days))

        if anchor:
            review_count = max(review_count, int(anchor.get("review_count", review_count) or review_count))
            if not is_counterfeit and np.random.binomial(1, 0.7):
                price = max(15, float(anchor.get("price", price) or price) * np.random.normal(1.0, 0.08))
                seller_rating = float(anchor.get("seller_rating", seller_rating) or seller_rating)
                seller_sales = max(seller_sales, int(anchor.get("seller_sales_count", seller_sales) or seller_sales))
                return_policy_days = int(anchor.get("return_policy_days", return_policy_days) or return_policy_days)

        if np.random.binomial(1, 0.018):
            is_counterfeit = 1 - is_counterfeit

        if np.random.binomial(1, 0.03):
            seller_rating = None
        if np.random.binomial(1, 0.04):
            seller_age_days = None
        if np.random.binomial(1, 0.05):
            review_count = max(0, review_count + int(np.random.normal(0, 45)))
        rows.append(
            {
                "title": title,
                "description": description,
                "brand": brand,
                "category": category,
                "price": round(float(price), 2),
                "currency": "USD",
                "seller_age_days": seller_age_days,
                "seller_rating": round(seller_rating, 2) if seller_rating is not None else None,
                "seller_sales_count": seller_sales,
                "review_count": review_count,
                "shipping_country": random.choice(COUNTRIES),
                "return_policy_days": return_policy_days,
                "label": int(is_counterfeit),
                "public_source": anchor.get("public_source") if anchor else None,
            }
        )

    df = pd.DataFrame(rows)
    if include_public_text:
        public_rows = load_public_review_text(limit=target_public_rows)
        if public_rows:
            public_df = pd.DataFrame(public_rows)
            df = pd.concat([df, public_df], ignore_index=True)
        if len(df) < n_rows:
            remainder = generate_dataset(
                n_rows=n_rows - len(df),
                seed=seed + 1,
                out_path=None,
                include_public_text=False,
            )
            df = pd.concat([df, remainder], ignore_index=True)

    if len(df) > n_rows:
        df = df.sample(n=n_rows, random_state=seed).reset_index(drop=True)
    else:
        df = df.sample(frac=1.0, random_state=seed).reset_index(drop=True)

    output_path = out_path or (DATA_DIR / "listings.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    return df


if __name__ == "__main__":
    frame = generate_dataset()
    print(f"Generated {len(frame)} rows")
