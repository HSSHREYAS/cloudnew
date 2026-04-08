from fastapi.testclient import TestClient

from app.api.dependencies import (
    get_current_user,
    get_estimation_service,
    get_recommendation_service,
)
from app.auth.models import UserContext
from app.main import create_app


class StubEstimationService:
    def estimate(self, payload):
        return {
            "total_cost": 1.23,
            "currency": "USD",
            "breakdown": [],
            "metadata": {"service": payload.service},
        }

    def compare(self, payload):
        return {
            "results": [
                {
                    "region": payload.comparisons[0].region,
                    "service": payload.service,
                    "total_cost": 1.23,
                    "currency": "USD",
                    "breakdown": [],
                    "metadata": {},
                },
                {
                    "region": payload.comparisons[1].region,
                    "service": payload.service,
                    "total_cost": 2.34,
                    "currency": "USD",
                    "breakdown": [],
                    "metadata": {},
                },
            ],
            "best_option": {
                "region": payload.comparisons[0].region,
                "service": payload.service,
                "total_cost": 1.23,
                "currency": "USD",
                "breakdown": [],
                "metadata": {},
            },
        }


class StubRecommendationService:
    def generate(self, _payload):
        return {
            "recommendations": [
                {
                    "type": "cost_optimization",
                    "suggestion": "Use Reserved pricing",
                    "estimated_savings": 0.75,
                    "risk_level": "low",
                    "explanation": "Fixture response",
                }
            ]
        }


def build_client():
    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: UserContext(uid="test-user", email="user@example.com")
    app.dependency_overrides[get_estimation_service] = lambda: StubEstimationService()
    app.dependency_overrides[get_recommendation_service] = lambda: StubRecommendationService()
    return TestClient(app)


def test_health_endpoint_is_public():
    client = build_client()
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_estimate_endpoint_returns_success_envelope():
    client = build_client()
    response = client.post(
        "/api/v1/estimate",
        json={
            "service": "EC2",
            "region": "us-east-1",
            "duration_hours": 100,
            "configuration": {
                "instance_type": "t3.micro",
                "operating_system": "Linux",
                "pricing_model": "OnDemand",
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["data"]["currency"] == "USD"


def test_auth_guard_rejects_missing_token_when_not_overridden():
    app = create_app()
    client = TestClient(app)
    response = client.post(
        "/api/v1/estimate",
        json={
            "service": "S3",
            "region": "us-east-1",
            "duration_hours": 24,
            "configuration": {
                "storage_gb": 100,
                "storage_class": "Standard",
            },
        },
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"

