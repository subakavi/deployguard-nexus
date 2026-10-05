import os
import sys
from pathlib import Path

from flask import Flask, jsonify, request
from flask_cors import CORS


# Allow Python to find the backend package
sys.path.insert(
    0,
    str(
        Path(__file__).resolve().parent.parent / "backend"
    )
)

from deployment_store import (
    get_deployments,
    get_deployment,
    get_summary,
    save_deployment
)


app = Flask(__name__)


# Allow the local dashboard to access the API
CORS(
    app,
    resources={
        r"/api/*": {
            "origins": "http://localhost:8000"
        }
    }
)


@app.route("/")
def home():
    return "DeployGuard Nexus Application is Running"


@app.route("/health")
def health():
    return jsonify({
        "status": "healthy"
    })


@app.route("/api/deployments", methods=["GET"])
def deployments():
    """
    Return deployment history and latest risk summary.
    """

    return jsonify({
        "summary": get_summary(),
        "deployments": get_deployments()
    })


@app.route(
    "/api/deployments/<deployment_id>",
    methods=["GET"]
)
def deployment_details(deployment_id):
    """
    Return details of a specific deployment.
    """

    deployment = get_deployment(
        deployment_id
    )

    if deployment is None:
        return jsonify({
            "error": "Deployment not found"
        }), 404

    return jsonify(deployment)


@app.route("/api/summary", methods=["GET"])
def summary():
    """
    Return only the latest deployment summary.
    """

    return jsonify(
        get_summary()
    )


@app.route("/api/deployments", methods=["POST"])
def create_deployment():
    """
    Save a new deployment record.
    """

    data = request.get_json(
        silent=True
    )

    if not data:
        return jsonify({
            "error": "JSON request body is required"
        }), 400

    required_fields = [
        "id",
        "riskScore",
        "riskLevel",
        "decision",
        "status"
    ]

    missing_fields = [
        field
        for field in required_fields
        if field not in data
    ]

    if missing_fields:
        return jsonify({
            "error": "Missing required fields",
            "fields": missing_fields
        }), 400

    deployment = save_deployment(
        data
    )

    return jsonify({
        "message": "Deployment saved successfully",
        "deployment": deployment
    }), 201


if __name__ == "__main__":

    host = os.getenv(
        "HOST",
        "127.0.0.1"
    )

    port = int(
        os.getenv(
            "PORT",
            "5000"
        )
    )

    app.run(
        host=host,
        port=port
    )