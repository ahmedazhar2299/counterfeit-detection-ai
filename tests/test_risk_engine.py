from backend.app.ml.risk_engine import get_engine


def test_threshold_action_mapping():
    engine = get_engine()
    assert engine._action_from_score(10) == "APPROVE"
    assert engine._action_from_score(55) == "REVIEW"
    assert engine._action_from_score(88) == "BLOCK"


def test_suspicious_phrase_highlight_detects_offsets():
    engine = get_engine()
    highlights = engine._extract_highlights("Amazing watch mirror quality with no box")
    phrases = [item["phrase"] for item in highlights]
    assert "mirror quality" in phrases
    assert "no box" in phrases


def test_fusion_probability_range():
    engine = get_engine()
    payload = {
        "title": "Rolex replica 1:1 watch",
        "description": "factory surplus no box wholesale lot",
        "brand": "Rolex",
        "category": "Watches",
        "price": 399,
        "currency": "USD",
        "seller_age_days": 5,
        "seller_rating": 2.1,
        "seller_sales_count": 3,
        "review_count": 0,
        "shipping_country": "CN",
        "return_policy_days": 1,
    }
    result = engine.analyze(payload)
    assert 0 <= result.structured_prob <= 1
    assert 0 <= result.text_prob <= 1
    assert 0 <= result.fused_prob <= 1
    assert 0 <= result.risk_score <= 100
