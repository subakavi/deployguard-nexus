import os
import sys
from datetime import datetime, timezone
from pathlib import Path


# Add the project root to Python's import path
PROJECT_ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(
    0,
    str(PROJECT_ROOT / "backend")
)


from deployment_store import (
    get_deployments,
    save_deployment,
    update_deployment
)

from notification_manager import (
    send_notification
)


def find_previous_stable_deployment(
    current_deployment_id
):
    """
    Find the most recent successful deployment
    different from the failed deployment.
    """

    deployments = get_deployments()

    for deployment in deployments:

        deployment_id = deployment.get(
            "id"
        )

        if deployment_id == current_deployment_id:
            continue

        if deployment.get("status") == "SUCCESS":
            return deployment

    return None


def find_deployment(
    deployment_id
):
    """
    Find a deployment by ID.
    """

    deployments = get_deployments()

    for deployment in deployments:

        if deployment.get("id") == deployment_id:
            return deployment

    return None


def perform_rollback(
    current_deployment_id
):
    """
    Simulate automatic rollback.

    The failed deployment is marked FAILED.
    The most recent successful deployment
    is identified as the stable version.
    A rollback event is created.
    A notification is generated.

    In AWS this logic will later trigger
    CodeDeploy and SNS.
    """

    # Find failed deployment
    current_deployment = find_deployment(
        current_deployment_id
    )

    if current_deployment is None:

        return {
            "success": False,
            "message": "Current deployment not found."
        }


    # Find previous stable deployment
    previous_stable = (
        find_previous_stable_deployment(
            current_deployment_id
        )
    )

    if previous_stable is None:

        return {
            "success": False,
            "message": (
                "No previous stable deployment found."
            )
        }


    # Mark current deployment as failed
    updated_deployment = update_deployment(
        current_deployment_id,
        {
            "status": "FAILED",
            "failureDetected": True,
            "failureTimestamp": (
                datetime.now(
                    timezone.utc
                ).isoformat()
            )
        }
    )

    if updated_deployment is None:

        return {
            "success": False,
            "message": (
                "Unable to update failed deployment."
            )
        }


    # Create rollback ID
    recovery_id = (
        "ROLLBACK-"
        + datetime.now(
            timezone.utc
        ).strftime(
            "%Y%m%d%H%M%S"
        )
    )


    # Create rollback event
    recovery_event = {

        "id": recovery_id,

        "commitId": previous_stable.get(
            "commitId",
            "unknown"
        ),

        "riskScore": previous_stable.get(
            "riskScore",
            0
        ),

        "riskLevel": previous_stable.get(
            "riskLevel",
            "SAFE"
        ),

        "decision": "ROLLBACK",

        "status": "ROLLBACK_COMPLETED",

        "rollback": True,

        "rolledBackDeployment": (
            current_deployment_id
        ),

        "restoredDeployment": (
            previous_stable.get(
                "id"
            )
        ),

        "timestamp": (
            datetime.now(
                timezone.utc
            ).isoformat()
        ),

        "message": (
            "Previous stable deployment restored."
        )
    }


    # Save rollback event
    save_deployment(
        recovery_event
    )


    # Create developer notification
    notification_subject = (
        "DeployGuard Nexus - "
        "Automatic Rollback"
    )

    notification_message = (
        f"Deployment failure detected.\n\n"
        f"Failed Deployment: "
        f"{current_deployment_id}\n"
        f"Restored Deployment: "
        f"{previous_stable.get('id')}\n"
        f"Rollback ID: "
        f"{recovery_id}\n"
        f"Status: ROLLBACK_COMPLETED\n\n"
        f"Previous stable version restored."
    )


    send_notification(
        notification_subject,
        notification_message
    )


    return {

        "success": True,

        "message": (
            "Automatic rollback completed."
        ),

        "recovery": recovery_event
    }


def main():

    current_deployment_id = os.environ.get(
        "CURRENT_DEPLOYMENT_ID"
    )


    if not current_deployment_id:

        print(
            "ERROR: CURRENT_DEPLOYMENT_ID "
            "environment variable is required."
        )

        raise SystemExit(1)


    result = perform_rollback(
        current_deployment_id
    )


    print(
        "========================================"
    )

    print(
        "       DEPLOYGUARD NEXUS"
    )

    print(
        "        SELF-HEALING ENGINE"
    )

    print(
        "========================================"
    )

    print()


    if result["success"]:

        recovery = result["recovery"]


        print(
            "⚠️ Application failure detected."
        )

        print()


        print(
            f"Failed Deployment : "
            f"{recovery['rolledBackDeployment']}"
        )


        print(
            f"Restored Version  : "
            f"{recovery['restoredDeployment']}"
        )


        print(
            f"Recovery ID       : "
            f"{recovery['id']}"
        )


        print()


        print(
            "✅ Automatic rollback completed."
        )

        print(
            "✅ Developer notification generated."
        )


    else:

        print(
            "❌ Automatic rollback failed."
        )

        print(
            f"Reason: "
            f"{result['message']}"
        )

        raise SystemExit(1)


if __name__ == "__main__":
    main()