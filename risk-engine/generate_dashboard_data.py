import json
import os
from datetime import datetime, timezone


RISK_RESULT_FILE = "risk-result.json"
OUTPUT_FILE = "dashboard/deployments.json"


def main():
    if not os.path.exists(RISK_RESULT_FILE):
        print("ERROR: risk-result.json not found.")
        raise SystemExit(1)

    with open(RISK_RESULT_FILE, "r", encoding="utf-8") as file:
        risk_data = json.load(file)

    inputs = risk_data["inputs"]
    result = risk_data["result"]

    deployment_id = os.environ.get(
        "DEPLOYMENT_ID",
        "LOCAL-001"
    )

    commit_id = os.environ.get(
        "GITHUB_SHA",
        "local"
    )[:8]

    timestamp = datetime.now(timezone.utc).isoformat()

    deployment = {
        "id": deployment_id,
        "commitId": commit_id,
        "riskScore": result["risk_score"],
        "riskLevel": result["risk_level"],
        "decision": result["decision"],
        "status": (
            "SUCCESS"
            if result["decision"] == "APPROVED"
            else "BLOCKED"
        ),
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

    dashboard_data = {
        "summary": {
            "riskScore": result["risk_score"],
            "riskLevel": result["risk_level"],
            "decision": result["decision"]
        },
        "deployments": [
            deployment
        ]
    }

    os.makedirs("dashboard", exist_ok=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        json.dump(
            dashboard_data,
            file,
            indent=4
        )

    print("Dashboard data generated successfully.")
    print(f"Deployment ID : {deployment_id}")
    print(f"Risk Score    : {result['risk_score']}")
    print(f"Risk Level    : {result['risk_level']}")
    print(f"Decision      : {result['decision']}")
    print(f"Output        : {OUTPUT_FILE}")


if __name__ == "__main__":
    main()