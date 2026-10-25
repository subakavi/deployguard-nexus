import os
import sys
from pathlib import Path

from flask import Flask, g, jsonify, request, send_from_directory
from flask_cors import CORS


# =========================================================
# PATHS
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DASHBOARD_DIR = PROJECT_ROOT / "dashboard"
BACKEND_DIR = PROJECT_ROOT / "backend"
RISK_ENGINE_DIR = PROJECT_ROOT / "risk-engine"


# Allow Python to find backend modules
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(RISK_ENGINE_DIR))


from deployment_store import (
    get_deployments,
    get_deployment,
    get_summary,
    save_deployment
)

from project_analyzer import analyze_repository
from risk_engine import calculate_risk
from auth import (
    auth_bp,
    auth_enabled,
    login_required,
    page_login_required
)
from notification_manager import send_notification


# =========================================================
# FLASK APPLICATION
# =========================================================

app = Flask(__name__)
CORS(app)

# Session cookie used after Cognito login (only active when
# AUTH_ENABLED=true). The key must be identical for every worker.
app.secret_key = os.getenv(
    "FLASK_SECRET_KEY",
    "dev-only-key-not-for-production"
)

if auth_enabled() and not os.getenv("FLASK_SECRET_KEY"):
    raise RuntimeError(
        "FLASK_SECRET_KEY is required when AUTH_ENABLED=true"
    )

app.config.update(
    SESSION_COOKIE_SECURE=auth_enabled(),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax"
)

app.register_blueprint(auth_bp)


# =========================================================
# PER-USER HELPERS
# =========================================================

def _visible(deployments):
    """With login on, a user only sees their own deployments."""

    if g.user is None:
        return deployments

    return [
        item for item in deployments
        if item.get("ownerId") == g.user["sub"]
    ]


def _summary_for(visible):
    """Summary of the newest visible deployment."""

    if g.user is None:
        return get_summary()

    if not visible:
        return {
            "riskScore": None,
            "riskLevel": None,
            "decision": None
        }

    latest = visible[0]

    return {
        "riskScore": latest.get("riskScore"),
        "riskLevel": latest.get("riskLevel"),
        "decision": latest.get("decision")
    }


def _send_alert(record):
    """Email the owner when a deployment is blocked or needs review."""

    try:
        decision = record.get("decision")

        if decision not in ("BLOCKED", "VALIDATION_REQUIRED"):
            return

        owner = g.user["email"] if g.user else None

        subject = (
            f"DeployGuard Nexus: {decision} "
            f"({record.get('riskScore')}/100)"
        )

        message = (
            f"Deployment {record.get('id')} needs attention.\n\n"
            f"Repository       : {record.get('repository')}\n"
            f"Risk score       : {record.get('riskScore')}\n"
            f"Risk level       : {record.get('riskLevel')}\n"
            f"Decision         : {decision}\n"
            f"Test failures    : {record.get('testFailures')}\n"
            f"Coverage         : {record.get('coverage')}%\n"
            f"Security issues  : {record.get('securityIssues')}\n"
            f"Changed files    : {record.get('changedFiles')}\n"
            f"Previous failures: {record.get('previousFailures')}\n"
        )

        send_notification(
            subject[:100],
            message,
            owner
        )

    except Exception as error:
        # An alert problem must never fail the analysis itself.
        print(f"Alert not sent: {error}")


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/")
@page_login_required
def home():

    return send_from_directory(
        DASHBOARD_DIR,
        "index.html"
    )


@app.route("/style.css")
def dashboard_css():

    return send_from_directory(
        DASHBOARD_DIR,
        "style.css"
    )


@app.route("/script.js")
def dashboard_js():

    return send_from_directory(
        DASHBOARD_DIR,
        "script.js"
    )


@app.route("/deployments.json")
@login_required
def dashboard_data():

    return send_from_directory(
        DASHBOARD_DIR,
        "deployments.json"
    )


# =========================================================
# HEALTH CHECK
# =========================================================

@app.route("/health")
def health():

    return jsonify({
        "status": "healthy"
    })


# =========================================================
# DEPLOYMENTS API
# =========================================================

@app.route(
    "/api/deployments",
    methods=["GET"]
)
@login_required
def deployments():

    visible = _visible(get_deployments())

    return jsonify({
        "summary": _summary_for(visible),
        "deployments": visible
    })


# =========================================================
# SINGLE DEPLOYMENT
# =========================================================

@app.route(
    "/api/deployments/<deployment_id>",
    methods=["GET"]
)
@login_required
def deployment_details(deployment_id):

    deployment = get_deployment(
        deployment_id
    )

    if deployment is None or (
        g.user is not None
        and deployment.get("ownerId") != g.user["sub"]
    ):

        return jsonify({
            "error": "Deployment not found"
        }), 404

    return jsonify(
        deployment
    )


# =========================================================
# SUMMARY API
# =========================================================

@app.route(
    "/api/summary",
    methods=["GET"]
)
@login_required
def summary():

    return jsonify(
        _summary_for(
            _visible(get_deployments())
        )
    )


# =========================================================
# PROJECT ANALYSIS + RISK ENGINE
# =========================================================

@app.route(
    "/api/analyze",
    methods=["POST"]
)
@login_required
def analyze_project():

    data = request.get_json(
        silent=True
    )

    if not data:

        return jsonify({
            "error": "JSON request body is required"
        }), 400


    repository_url = data.get(
        "repository"
    )

    if not repository_url:

        return jsonify({
            "error": "GitHub repository URL is required"
        }), 400


    try:

        # -------------------------------------------------
        # STEP 1: Analyze GitHub repository
        # -------------------------------------------------

        analysis = analyze_repository(
            repository_url
        )


        if not analysis.get(
            "success",
            False
        ):

            return jsonify(
                analysis
            ), 500


        # -------------------------------------------------
        # STEP 2: Extract analysis values
        # -------------------------------------------------

        test_failures = analysis.get(
            "test_failures",
            0
        )

        coverage = analysis.get(
            "coverage",
            0
        )

        security_issues = analysis.get(
            "security_issues",
            0
        )

        changed_files = analysis.get(
            "changed_files",
            0
        )

        previous_failures = analysis.get(
            "previous_failures",
            0
        )


        # -------------------------------------------------
        # STEP 3: Run DeployGuard Risk Engine
        # -------------------------------------------------

        risk_result = calculate_risk(

            test_failures=test_failures,

            coverage=coverage,

            security_issues=security_issues,

            changed_files=changed_files,

            previous_failures=previous_failures

        )


        # -------------------------------------------------
        # STEP 4: Combine analysis + risk result
        # -------------------------------------------------

        deployment_id = analysis.get(
            "deployment_id"
        )


        result = {

            "success": True,

            "deployment_id":
                deployment_id,

            "repository":
                repository_url,

            "project_type":
                analysis.get(
                    "project_type",
                    "unknown"
                ),

            "tests_passed":
                analysis.get(
                    "tests_passed",
                    0
                ),

            "test_failures":
                test_failures,

            "coverage":
                coverage,

            "security_issues":
                security_issues,

            "changed_files":
                changed_files,

            "previous_failures":
                previous_failures,

            "risk_score":
                risk_result[
                    "risk_score"
                ],

            "risk_level":
                risk_result[
                    "risk_level"
                ],

            "decision":
                risk_result[
                    "decision"
                ]

        }


        # -------------------------------------------------
        # STEP 5: Create deployment record
        # -------------------------------------------------

        deployment_record = {

            "id":
                deployment_id,

            "repository":
                repository_url,

            "projectType":
                analysis.get(
                    "project_type",
                    "unknown"
                ),

            "testsPassed":
                analysis.get(
                    "tests_passed",
                    0
                ),

            "testFailures":
                test_failures,

            "coverage":
                coverage,

            "securityIssues":
                security_issues,

            "changedFiles":
                changed_files,

            "previousFailures":
                previous_failures,

            "riskScore":
                risk_result[
                    "risk_score"
                ],

            "riskLevel":
                risk_result[
                    "risk_level"
                ],

            "decision":
                risk_result[
                    "decision"
                ],

            "status":
                (
                    "APPROVED"
                    if risk_result[
                        "decision"
                    ] == "APPROVED"
                    else
                    "BLOCKED"
                    if risk_result[
                        "decision"
                    ] == "BLOCKED"
                    else
                    "VALIDATION_REQUIRED"
                ),

            "rollback":
                False

        }
        if g.user is not None:
            deployment_record["ownerId"] = g.user["sub"]
            deployment_record["ownerEmail"] = g.user["email"]



        # -------------------------------------------------
        # STEP 6: Save deployment
        # -------------------------------------------------

        save_deployment(
            deployment_record
        )

        _send_alert(
            deployment_record
        )


        # -------------------------------------------------
        # STEP 7: Print result
        # -------------------------------------------------

        print()
        print(
            "========================================"
        )

        print(
            "       DEPLOYGUARD NEXUS"
        )

        print(
            "       DEPLOYMENT ANALYSIS"
        )

        print(
            "========================================"
        )

        print()

        print(
            f"Repository        : "
            f"{repository_url}"
        )

        print(
            f"Tests Passed      : "
            f"{result['tests_passed']}"
        )

        print(
            f"Test Failures     : "
            f"{result['test_failures']}"
        )

        print(
            f"Coverage          : "
            f"{result['coverage']}%"
        )

        print(
            f"Security Issues   : "
            f"{result['security_issues']}"
        )

        print(
            f"Changed Files     : "
            f"{result['changed_files']}"
        )

        print()

        print(
            "----------------------------------------"
        )

        print(
            f"Risk Score        : "
            f"{result['risk_score']}"
        )

        print(
            f"Risk Level        : "
            f"{result['risk_level']}"
        )

        print(
            f"Decision          : "
            f"{result['decision']}"
        )

        print()

        print(
            "Deployment saved to history."
        )

        print(
            "========================================"
        )

        print()


        # Return complete result
        return jsonify(
            result
        )


    except Exception as error:

        print(
            f"Analysis error: {error}"
        )

        return jsonify({

            "success": False,

            "error": str(error)

        }), 500


# =========================================================
# CREATE DEPLOYMENT
# =========================================================

@app.route(
    "/api/deployments",
    methods=["POST"]
)
@login_required
def create_deployment():

    data = request.get_json(
        silent=True
    )

    if not data:

        return jsonify({
            "error":
                "JSON request body is required"
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

            "error":
                "Missing required fields",

            "fields":
                missing_fields

        }), 400


    data = dict(data)

    # Never trust owner fields sent by a client.
    data.pop("ownerId", None)
    data.pop("ownerEmail", None)

    if g.user is not None:
        data["ownerId"] = g.user["sub"]
        data["ownerEmail"] = g.user["email"]

    deployment = save_deployment(
        data
    )


    return jsonify({

        "message":
            "Deployment saved successfully",

        "deployment":
            deployment

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