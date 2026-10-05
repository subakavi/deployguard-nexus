import sys
import os

sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "app"
        )
    )
)

from app import app


def test_home_page():
    client = app.test_client()

    response = client.get("/")

    assert response.status_code == 200
    assert b"DeployGuard Nexus" in response.data


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


def test_deployments_api():
    client = app.test_client()

    response = client.get("/api/deployments")

    assert response.status_code == 200

    data = response.get_json()

    assert "summary" in data
    assert "deployments" in data


def test_deployments_api_summary():
    client = app.test_client()

    response = client.get("/api/deployments")

    data = response.get_json()

    assert "riskScore" in data["summary"]
    assert "riskLevel" in data["summary"]
    assert "decision" in data["summary"]


def test_deployments_api_list():
    client = app.test_client()

    response = client.get("/api/deployments")

    data = response.get_json()

    assert isinstance(data["deployments"], list)


def test_summary_endpoint():
    client = app.test_client()

    response = client.get("/api/summary")

    assert response.status_code == 200

    data = response.get_json()

    assert "riskScore" in data
    assert "riskLevel" in data
    assert "decision" in data


def test_create_deployment():
    client = app.test_client()

    deployment = {
        "id": "TEST-API-001",
        "riskScore": 15,
        "riskLevel": "SAFE",
        "decision": "APPROVED",
        "status": "SUCCESS",
        "rollback": False
    }

    response = client.post(
        "/api/deployments",
        json=deployment
    )

    assert response.status_code == 201

    data = response.get_json()

    assert data["message"] == "Deployment saved successfully"
    assert data["deployment"]["id"] == "TEST-API-001"


def test_create_deployment_without_json():
    client = app.test_client()

    response = client.post(
        "/api/deployments"
    )

    assert response.status_code == 400

    data = response.get_json()

    assert "error" in data


def test_create_deployment_missing_fields():
    client = app.test_client()

    deployment = {
        "id": "TEST-API-002"
    }

    response = client.post(
        "/api/deployments",
        json=deployment
    )

    assert response.status_code == 400

    data = response.get_json()

    assert data["error"] == "Missing required fields"
    assert len(data["fields"]) > 0


def test_get_existing_deployment():
    client = app.test_client()

    deployment = {
        "id": "TEST-API-003",
        "riskScore": 20,
        "riskLevel": "SAFE",
        "decision": "APPROVED",
        "status": "SUCCESS",
        "rollback": False
    }

    create_response = client.post(
        "/api/deployments",
        json=deployment
    )

    assert create_response.status_code == 201

    response = client.get(
        "/api/deployments/TEST-API-003"
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["id"] == "TEST-API-003"


def test_get_missing_deployment():
    client = app.test_client()

    response = client.get(
        "/api/deployments/DOES-NOT-EXIST"
    )

    assert response.status_code == 404

    data = response.get_json()

    assert data["error"] == "Deployment not found"