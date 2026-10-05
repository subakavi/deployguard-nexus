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


# =========================================================
# FLASK APPLICATION
# =========================================================

app = Flask(__name__)

CORS(app)


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/")
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
def deployments():

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

@app.route(
    "/api/summary",
    methods=["GET"]
)
def summary():

    return jsonify(
        get_summary()
    )


# =========================================================
# PROJECT ANALYSIS + RISK ENGINE
# =========================================================

@app.route(
    "/api/analyze",
    methods=["POST"]
)
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


        # -------------------------------------------------
        # STEP 6: Save deployment
        # -------------------------------------------------

        save_deployment(
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