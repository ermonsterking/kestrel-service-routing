import os

import pandas as pd
from fastapi.testclient import TestClient

from app.main import app


MODEL_PATH = "models/kestrel_router.joblib"

client = TestClient(app)


VALID_TEAMS = {
    "Billing",
    "Filters & Consumables",
    "Installs & Demo",
    "Product Advice",
    "Repairs",
    "Returns & Replacement",
    "Warranty Claims",
}


def test_model_exists():
    assert os.path.exists(MODEL_PATH)


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["model"] == "kestrel_router"


def test_route_endpoint():
    payload = {
        "request_text": "my water purifier is leaking water",
        "product_family": "Water Purifier",
        "warranty_status": "in_warranty",
        "channel": "whatsapp",
        "source": "crm",
    }

    response = client.post("/route", json=payload)

    assert response.status_code == 200

    data = response.json()

    assert "predicted_team" in data
    assert "reason" in data

    assert data["predicted_team"] in VALID_TEAMS
    assert isinstance(data["reason"], str)
    assert len(data["reason"]) > 0


def test_route_requires_request_text():
    payload = {
        "product_family": "Water Purifier",
        "warranty_status": "in_warranty",
        "channel": "whatsapp",
        "source": "crm",
    }

    response = client.post("/route", json=payload)

    assert response.status_code == 422


def test_submission_file():
    predictions = pd.read_csv("outputs/predictions.csv")

    assert list(predictions.columns) == [
        "request_id",
        "team",
    ]

    assert len(predictions) == 2178
    assert predictions["request_id"].notna().all()
    assert predictions["team"].notna().all()
    assert predictions["request_id"].is_unique
    assert set(predictions["team"]).issubset(VALID_TEAMS)