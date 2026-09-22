from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_qualify_returns_ranked_assessments():
    response = client.post(
        "/v1/qualify",
        json={
            "description": "B2B software and IT services companies with a structured sales organization",
            "database": "SE",
            "min_revenue": 5_000_000,
            "max_revenue": 50_000_000,
            "min_employees": 30,
            "max_employees": 200,
            "limit": 4,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["source"] == "mock"
    assert len(body["assessments"]) == 4
    scores = [item["score"] for item in body["assessments"]]
    assert scores == sorted(scores, reverse=True)
