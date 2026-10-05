import json

from deployment_store import (
    get_deployments,
    get_deployment,
    get_summary
)


def response(status_code, body):
    """Create a standard API response."""

    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(body)
    }


def lambda_handler(event, context):
    """
    AWS Lambda entry point.

    Supported routes:

    GET /deployments
    GET /deployments/{id}
    GET /summary
    """

    path = event.get("path", "")
    http_method = event.get(
        "httpMethod",
        "GET"
    )

    if http_method != "GET":
        return response(
            405,
            {
                "error": "Method not allowed"
            }
        )

    # GET /summary
    if path == "/summary":
        return response(
            200,
            get_summary()
        )

    # GET /deployments
    if path == "/deployments":
        return response(
            200,
            {
                "deployments": get_deployments()
            }
        )

    # GET /deployments/{id}
    if path.startswith("/deployments/"):

        deployment_id = path.split(
            "/deployments/",
            1
        )[1]

        deployment = get_deployment(
            deployment_id
        )

        if deployment is None:
            return response(
                404,
                {
                    "error": "Deployment not found"
                }
            )

        return response(
            200,
            deployment
        )

    return response(
        404,
        {
            "error": "Route not found"
        }
    )