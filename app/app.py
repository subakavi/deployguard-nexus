import os
import sys
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS


# =========================================================
# PATHS
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DASHBOARD_DIR = PROJECT_ROOT / "dashboard"
BACKEND_DIR = PROJECT_ROOT / "backend"


# Allow Python to find backend modules
sys.path.insert(0, str(BACKEND_DIR))


from deployment_store import (
    get_deployments,
    get_deployment,
    get_summary,
    save_deployment
)


# =========================================================
# FLASK APPLICATION
# =========================================================

app = Flask(__name__)


# Allow dashboard/API communication
CORS(app)


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/")
def home():
    """
    Serve the DeployGuard Nexus dashboard.
    """

    return send_from_directory(
        DASHBOARD_DIR,
        "index.html"
    )


@app.route("/style.css")
def dashboard_css():
    """
    Serve dashboard CSS.
    """

    return send_from_directory(
        DASHBOARD_DIR,
        "style.css"
    )


@app.route("/script.js")
def dashboard_js():
    """
    Serve dashboard JavaScript.
    """

    return send_from_directory(
        DASHBOARD_DIR,
        "script.js"
    )


@app.route("/deployments.json")
def dashboard_data():
    """
    Serve dashboard deployment data.
    """

    return send_from_directory(
        DASHBOARD_DIR,
        "deployments.json"
    )


# =========================================================
# HEALTH CHECK
# =========================================================

@app.route("/health")
def health():
    """
    Health check endpoint.
    """

    return jsonify({
        "status": "healthy"
    })


# =========================================================
# DEPLOYMENTS API
# =========================================================

@app.route("/api/deployments", methods=["GET"])
def deployments():
    """
    Return deployment history and latest risk summary.
    """

    return jsonify({
        "summary": get_summary(),
        "deployments": get_deployments()
    })


# =========================================================
# SINGLE DEPLOYMENT
# =========================================================

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

    return jsonify(
        deployment
    )


# =========================================================
# SUMMARY API
# =========================================================

@app.route("/api/summary", methods=["GET"])
def summary():
    """
    Return only the latest deployment summary.
    """

    return jsonify(
        get_summary()
    )


# =========================================================
# CREATE DEPLOYMENT
# =========================================================

@app.route(
    "/api/deployments",
    methods=["POST"]
)
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


# =========================================================
# APPLICATION START
# =========================================================

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
        port=port,
        debug=False
    )