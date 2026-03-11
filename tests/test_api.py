from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_analyze_schema_and_response():
    payload = {
        "title": "Apple iPhone 15 Pro Max",
        "description": "Original from official store with invoice and box.",
        "brand": "Apple",
        "category": "Electronics",
        "price": 1050,
        "currency": "USD",
        "seller_age_days": 800,
        "seller_rating": 4.8,
        "seller_sales_count": 1200,
        "review_count": 520,
        "shipping_country": "US",
        "return_policy_days": 30,
    }
    response = client.post("/api/analyze", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert "risk_score" in body
    assert "action" in body
    assert "explanations" in body


def test_analyze_validation_error():
    response = client.post(
        "/api/analyze",
        json={"title": "x", "description": "short", "brand": "A", "category": "B", "price": -10},
    )
    assert response.status_code == 422


def test_metrics_and_model_info():
    metrics_response = client.get("/api/metrics")
    assert metrics_response.status_code == 200
    assert "metrics" in metrics_response.json()

    model_response = client.get("/api/model-info")
    assert model_response.status_code == 200
    assert "version" in model_response.json()
