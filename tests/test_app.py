import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app")))

from app import app


def test_home_page():
    client = app.test_client()

    response = client.get("/")

    assert response.status_code == 200
    assert b"DeployGuard Nexus Application is Running" in response.data


def test_health_status_code():
    client = app.test_client()

    response = client.get("/health")

    assert response.status_code == 200


def test_health_response():
    client = app.test_client()

    response = client.get("/health")

    data = response.get_json()

    assert data["status"] == "healthy"


def test_health_content_type():
    client = app.test_client()

    response = client.get("/health")

    assert response.content_type == "application/json"