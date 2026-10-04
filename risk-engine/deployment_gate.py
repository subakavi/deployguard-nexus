import json
import sys


RISK_RESULT_FILE = "risk-result.json"


def main():
    try:
        with open(RISK_RESULT_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        print("ERROR: risk-result.json was not found.")
        sys.exit(1)

    result = data["result"]

    risk_score = result["risk_score"]
    risk_level = result["risk_level"]
    decision = result["decision"]

    print("========================================")
    print("       DEPLOYGUARD NEXUS")
    print("         DEPLOYMENT GATE")
    print("========================================")
    print()
    print(f"Risk Score           : {risk_score}")
    print(f"Risk Level           : {risk_level}")
    print(f"Deployment Decision  : {decision}")
    print()

    if decision == "APPROVED":
        print("✅ Deployment Gate: ALLOWED")
        print("Deployment may continue.")
        sys.exit(0)

    elif decision == "VALIDATION_REQUIRED":
        print("⚠️ Deployment Gate: VALIDATION REQUIRED")
        print("Additional validation is required.")
        print("For the current project phase, deployment may continue.")
        sys.exit(0)

    elif decision == "BLOCKED":
        print("❌ Deployment Gate: BLOCKED")
        print("High-risk deployment detected.")
        print("Deployment must not continue.")
        sys.exit(1)

    else:
        print("ERROR: Unknown deployment decision.")
        sys.exit(1)


if __name__ == "__main__":
    main()