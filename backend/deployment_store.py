import json
import os
from pathlib import Path
from datetime import datetime, timezone

import boto3


# =========================================================
# PATHS
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

LOCAL_DATA_FILE = (
    PROJECT_ROOT
    / "dashboard"
    / "deployments.json"
)


# =========================================================
# DEFAULT DATA
# =========================================================

DEFAULT_DATA = {
    "summary": {
        "riskScore": 0,
        "riskLevel": "SAFE",
        "decision": "APPROVED"
    },
    "deployments": []
}


# =========================================================
# LOCAL JSON STORAGE
# =========================================================

class LocalDeploymentStore:
    """Deployment storage using local JSON."""

    def _load_data(self):

        if not LOCAL_DATA_FILE.exists():

            return {
                "summary":
                    DEFAULT_DATA["summary"].copy(),

                "deployments": []
            }

        try:

            with open(
                LOCAL_DATA_FILE,
                "r",
                encoding="utf-8"
            ) as file:

                return json.load(file)

        except (
            json.JSONDecodeError,
            OSError
        ):

            return {
                "summary":
                    DEFAULT_DATA["summary"].copy(),

                "deployments": []
            }

    def _save_data(self, data):

        LOCAL_DATA_FILE.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        with open(
            LOCAL_DATA_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                data,
                file,
                indent=4
            )

    def get_deployments(self):

        data = self._load_data()

        return data.get(
            "deployments",
            []
        )

    def get_summary(self):

        data = self._load_data()

        return data.get(
            "summary",
            DEFAULT_DATA["summary"]
        )

    def get_deployment(
        self,
        deployment_id
    ):

        deployments = self.get_deployments()

        for deployment in deployments:

            if deployment.get("id") == deployment_id:

                return deployment

        return None

    def save_deployment(
        self,
        deployment
    ):

        data = self._load_data()

        deployments = data.get(
            "deployments",
            []
        )

        deployment = dict(
            deployment
        )

        # Add timestamp if missing
        deployment.setdefault(
            "createdAt",
            datetime.now(
                timezone.utc
            ).isoformat()
        )

        # Newest deployment first
        deployments.insert(
            0,
            deployment
        )

        data["deployments"] = deployments

        # Update dashboard summary
        data["summary"] = {

            "riskScore":
                deployment.get(
                    "riskScore",
                    0
                ),

            "riskLevel":
                deployment.get(
                    "riskLevel",
                    "SAFE"
                ),

            "decision":
                deployment.get(
                    "decision",
                    "APPROVED"
                )
        }

        self._save_data(
            data
        )

        return deployment

    def update_deployment(
        self,
        deployment_id,
        updates
    ):

        data = self._load_data()

        deployments = data.get(
            "deployments",
            []
        )

        for deployment in deployments:

            if deployment.get("id") == deployment_id:

                deployment.update(
                    updates
                )

                self._save_data(
                    data
                )

                return deployment

        return None


# =========================================================
# DYNAMODB STORAGE
# =========================================================

class DynamoDBDeploymentStore:
    """Deployment storage using Amazon DynamoDB."""

    def __init__(self):

        self.table_name = os.getenv(
            "DYNAMODB_TABLE",
            "DeployGuardNexus-Deployments"
        )

        self.region = os.getenv(
            "AWS_REGION",
            "us-east-1"
        )

        self.dynamodb = boto3.resource(
            "dynamodb",
            region_name=self.region
        )

        self.table = self.dynamodb.Table(
            self.table_name
        )

    # -----------------------------------------------------
    # GET ALL DEPLOYMENTS
    # -----------------------------------------------------

    def get_deployments(self):

        response = self.table.scan()

        deployments = response.get(
            "Items",
            []
        )

        # DynamoDB scan does not guarantee order.
        # Sort by creation time so newest appears first.
        deployments.sort(
            key=lambda item:
                item.get(
                    "createdAt",
                    ""
                ),
            reverse=True
        )

        return deployments

    # -----------------------------------------------------
    # GET SINGLE DEPLOYMENT
    # -----------------------------------------------------

    def get_deployment(
        self,
        deployment_id
    ):

        response = self.table.get_item(
            Key={
                "deploymentId":
                    deployment_id
            }
        )

        return response.get(
            "Item"
        )

    # -----------------------------------------------------
    # GET SUMMARY
    # -----------------------------------------------------

    def get_summary(self):

        deployments = self.get_deployments()

        if not deployments:

            return DEFAULT_DATA[
                "summary"
            ].copy()

        latest = deployments[0]

        return {

            "riskScore":
                latest.get(
                    "riskScore",
                    0
                ),

            "riskLevel":
                latest.get(
                    "riskLevel",
                    "SAFE"
                ),

            "decision":
                latest.get(
                    "decision",
                    "APPROVED"
                )
        }

    # -----------------------------------------------------
    # SAVE DEPLOYMENT
    # -----------------------------------------------------

    def save_deployment(
        self,
        deployment
    ):

        item = dict(
            deployment
        )

        # DynamoDB partition key
        item["deploymentId"] = item.get(
            "id",
            "UNKNOWN"
        )

        # Creation timestamp
        item.setdefault(
            "createdAt",
            datetime.now(
                timezone.utc
            ).isoformat()
        )

        self.table.put_item(
            Item=item
        )

        return deployment

    # -----------------------------------------------------
    # UPDATE DEPLOYMENT
    # -----------------------------------------------------

    def update_deployment(
        self,
        deployment_id,
        updates
    ):

        if not updates:

            return self.get_deployment(
                deployment_id
            )

        update_parts = []

        expression_names = {}

        expression_values = {}

        for key, value in updates.items():

            safe_name = f"#{key}"

            safe_value = f":{key}"

            update_parts.append(
                f"{safe_name} = {safe_value}"
            )

            expression_names[
                safe_name
            ] = key

            expression_values[
                safe_value
            ] = value

        response = self.table.update_item(

            Key={
                "deploymentId":
                    deployment_id
            },

            UpdateExpression=(
                "SET "
                + ", ".join(
                    update_parts
                )
            ),

            ExpressionAttributeNames=(
                expression_names
            ),

            ExpressionAttributeValues=(
                expression_values
            ),

            ReturnValues="ALL_NEW"
        )

        return response.get(
            "Attributes"
        )


# =========================================================
# STORE FACTORY
# =========================================================

def create_store():
    """
    Select deployment storage backend.

    USE_DYNAMODB=true
        -> Amazon DynamoDB

    USE_DYNAMODB=false
        -> Local JSON storage
    """

    use_dynamodb = os.getenv(
        "USE_DYNAMODB",
        "false"
    ).lower() == "true"

    if use_dynamodb:

        return DynamoDBDeploymentStore()

    return LocalDeploymentStore()


# =========================================================
# ACTIVE STORE
# =========================================================

store = create_store()


# =========================================================
# PUBLIC FUNCTIONS
# =========================================================

def get_deployments():

    return store.get_deployments()


def get_summary():

    return store.get_summary()


def get_deployment(
    deployment_id
):

    return store.get_deployment(
        deployment_id
    )


def save_deployment(
    deployment
):

    return store.save_deployment(
        deployment
    )


def update_deployment(
    deployment_id,
    updates
):

    return store.update_deployment(
        deployment_id,
        updates
    )


# =========================================================
# TEST / DEBUG
# =========================================================

if __name__ == "__main__":

    print(
        "========================================"
    )

    print(
        "DeployGuard Nexus Deployment Store"
    )

    print(
        "========================================"
    )

    mode = (

        "DynamoDB"

        if os.getenv(
            "USE_DYNAMODB",
            "false"
        ).lower() == "true"

        else "LOCAL"
    )

    print(
        f"Storage mode: {mode}"
    )

    print()

    deployments = get_deployments()

    print(
        f"Total deployments: "
        f"{len(deployments)}"
    )

    print()

    for deployment in deployments:

        print(
            deployment.get("id"),
            "| Risk:",
            deployment.get(
                "riskScore"
            ),
            "| Status:",
            deployment.get(
                "status"
            ),
            "| Rollback:",
            deployment.get(
                "rollback",
                False
            )
        )