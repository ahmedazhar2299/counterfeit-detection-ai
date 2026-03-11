from __future__ import annotations

from dataclasses import dataclass

import httpx

from .config import GEMINI_API_KEY, GEMINI_MODEL


@dataclass
class LLMExplanation:
    summary: str
    provider: str


def build_fallback_summary(payload: dict, action: str, risk_score: float, explanations: list[dict], highlights: list[dict]) -> str:
    top_features = ", ".join(item["feature"].replace("_", " ") for item in explanations[:3])
    highlighted = ", ".join(hit["phrase"] for hit in highlights[:3]) or "no suspicious phrases detected"
    brand = payload.get("brand", "This listing")
    category = payload.get("category", "item")
    return (
        f"{brand} {category} was marked {action.lower()} with a risk score of {risk_score:.0f}/100. "
        f"The strongest signals came from {top_features}. "
        f"Text review found {highlighted}. "
        "Use this as a screening explanation, not a proof of authenticity."
    )


async def maybe_generate_llm_summary(
    payload: dict,
    action: str,
    risk_score: float,
    structured_prob: float,
    text_prob: float,
    fused_prob: float,
    explanations: list[dict],
    highlights: list[dict],
) -> LLMExplanation:
    fallback = build_fallback_summary(payload, action, risk_score, explanations, highlights)
    if not GEMINI_API_KEY:
        return LLMExplanation(summary=fallback, provider="fallback")

    prompt = f"""
You are helping a marketplace analyst understand an ML counterfeit-risk decision.
Rewrite the decision into plain English for a non-technical user.

Listing:
- Title: {payload.get("title")}
- Brand: {payload.get("brand")}
- Category: {payload.get("category")}
- Price: {payload.get("price")} {payload.get("currency", "USD")}
- Seller age days: {payload.get("seller_age_days")}
- Seller rating: {payload.get("seller_rating")}
- Seller sales count: {payload.get("seller_sales_count")}
- Review count: {payload.get("review_count")}

Model outputs:
- Action: {action}
- Risk score: {risk_score}
- Structured probability: {structured_prob}
- Text probability: {text_prob}
- Fused probability: {fused_prob}
- Top explanations: {explanations[:5]}
- Suspicious phrases: {highlights[:5]}

Write:
1. A 2-3 sentence explanation.
2. Keep it concrete and human-readable.
3. Avoid legal claims or certainty.
4. Mention the strongest factors and whether manual review is recommended.
"""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
    params = {"key": GEMINI_API_KEY}
    body = {"contents": [{"parts": [{"text": prompt}]}]}

    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            response = await client.post(url, params=params, json=body)
            response.raise_for_status()
            data = response.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
            return LLMExplanation(summary=text, provider="gemini")
    except Exception:
        return LLMExplanation(summary=fallback, provider="fallback")
