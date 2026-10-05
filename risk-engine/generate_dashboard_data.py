import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


# Add the project root to Python's import path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.deployment_store import save_deployment


RISK_RESULT_FILE = PROJECT_ROOT / "risk-result.json"


def main():

    if not RISK_RESULT_FILE.exists():
        print("ERROR: risk-result.json not found.")
        raise SystemExit(1)

    with open(
        RISK_RESULT_FILE,
        "r",
        encoding="utf-8"
    ) as file:
        risk_data = json.load(file)

    inputs = risk_data["inputs"]
    result = risk_data["result"]

    deployment_id = os.environ.get(
        "DEPLOYMENT_ID",
        "LOCAL-" + datetime.now(
            timezone.utc
        ).strftime("%Y%m%d%H%M%S")
    )

    commit_id = os.environ.get(
        "GITHUB_SHA",
        "local"
    )[:8]

    timestamp = datetime.now(
        timezone.utc
    ).isoformat()

    if result["decision"] == "APPROVED":
        status = "SUCCESS"
    elif result["decision"] == "VALIDATION_REQUIRED":
        status = "VALIDATION"
    else:
        status = "BLOCKED"

    deployment = {
        "id": deployment_id,
        "commitId": commit_id,
        "riskScore": result["risk_score"],
        "riskLevel": result["risk_level"],
        "decision": result["decision"],
        "status": status,
        "rollback": False,
        "timestamp": timestamp,
        "metrics": {
            "testFailures": inputs["test_failures"],
            "coverage": inputs["coverage"],
            "securityIssues": inputs["security_issues"],
            "changedFiles": inputs["changed_files"],
            "previousFailures": inputs["previous_failures"]
        }
    }

    # Save the deployment record
    saved_deployment = save_deployment(
        deployment
    )

    print("========================================")
    print("       DEPLOYGUARD NEXUS")
    print("       DEPLOYMENT RECORD")
    print("========================================")
    print()
    print(
        f"Deployment ID : "
        f"{saved_deployment['id']}"
    )
    print(
        f"Risk Score    : "
        f"{saved_deployment['riskScore']}"
    )
    print(
        f"Risk Level    : "
        f"{saved_deployment['riskLevel']}"
    )
    print(
        f"Decision      : "
        f"{saved_deployment['decision']}"
    )
    print(
        f"Status        : "
        f"{saved_deployment['status']}"
    )
    print()
    print("Deployment saved successfully.")


if __name__ == "__main__":
    main()