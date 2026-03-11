from __future__ import annotations

from typing import Any


def load_public_review_text(limit: int = 3000) -> list[dict[str, Any]]:
    """
    Optional public text augmentation using a fake-review corpus from Hugging Face.
    This is adjacent to counterfeit detection rather than a perfect domain match,
    but it adds more realistic noisy deceptive language to the text side.
    """
    try:
        from datasets import load_dataset

        dataset = load_dataset("debojit01/fake-review-dataset", split="train")
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
                    "public_source": "debojit01/fake-review-dataset",
                }
            )
        return rows
    except Exception:
        return []
