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

from recovery_manager import perform_rollback
from deployment_store import save_deployment


def test_rollback_with_no_deployment():

    result = perform_rollback(
        "DOES-NOT-EXIST"
    )

    assert result["success"] is False


def test_rollback_finds_previous_stable():

    # Create a previous stable deployment
    save_deployment({
        "id": "TEST-STABLE-001",
        "commitId": "stable-test-001",
        "riskScore": 10,
        "riskLevel": "SAFE",
        "decision": "APPROVED",
        "status": "SUCCESS",
        "rollback": False
    })

    # Create the deployment that will fail
    save_deployment({
        "id": "TEST-FAILED-001",
        "commitId": "failed-test-001",
        "riskScore": 80,
        "riskLevel": "HIGH",
        "decision": "BLOCKED",
        "status": "SUCCESS",
        "rollback": False
    })

    # Perform automatic rollback
    result = perform_rollback(
        "TEST-FAILED-001"
    )

    assert result["success"] is True

    recovery = result["recovery"]

    assert recovery["rolledBackDeployment"] == (
        "TEST-FAILED-001"
    )

    assert recovery["restoredDeployment"] == (
        "TEST-STABLE-001"
    )

    assert recovery["status"] == (
        "ROLLBACK_COMPLETED"
    )

    assert recovery["rollback"] is True