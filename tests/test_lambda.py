import sys
import os

sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "backend"
        )
    )
)

from lambda_function import lambda_handler


def test_get_summary():
    event = {
        "httpMethod": "GET",
        "path": "/summary"
    }

    result = lambda_handler(
        event,
        None
    )

    assert result["statusCode"] == 200

    assert "riskScore" in result["body"]
    assert "riskLevel" in result["body"]
    assert "decision" in result["body"]


def test_get_deployments():
    event = {
        "httpMethod": "GET",
        "path": "/deployments"
    }

    result = lambda_handler(
        event,
        None
    )

    assert result["statusCode"] == 200

    assert "deployments" in result["body"]


def test_get_existing_deployment():

    from deployment_store import save_deployment

    save_deployment({
        "id": "LOCAL-001",
        "riskScore": 10,
        "riskLevel": "SAFE",
        "decision": "APPROVED",
        "status": "SUCCESS"
    })

    event = {
        "httpMethod": "GET",
        "path": "/deployments/LOCAL-001"
    }

    result = lambda_handler(
        event,
        None
    )

    assert result["statusCode"] == 200


def test_get_missing_deployment():
    event = {
        "httpMethod": "GET",
        "path": "/deployments/DOES-NOT-EXIST"
    }

    result = lambda_handler(
        event,
        None
    )

    assert result["statusCode"] == 404


def test_invalid_route():
    event = {
        "httpMethod": "GET",
        "path": "/invalid"
    }

    result = lambda_handler(
        event,
        None
    )

    assert result["statusCode"] == 404


def test_invalid_method():
    event = {
        "httpMethod": "POST",
        "path": "/deployments"
    }

    result = lambda_handler(
        event,
        None
    )

    assert result["statusCode"] == 405