import argparse
import json


def calculate_risk(
    test_failures,
    coverage,
    security_issues,
    changed_files,
    previous_failures
):
    # Test failures: maximum 30 points
    test_risk = min(test_failures * 10, 30)

    # Code coverage: maximum 20 points
    if coverage >= 80:
        coverage_risk = 0
    elif coverage >= 60:
        coverage_risk = 10
    else:
        coverage_risk = 20

    # Security issues: maximum 25 points
    security_risk = min(security_issues * 5, 25)

    # Changed files: maximum 10 points
    changed_files_risk = min((changed_files // 10) * 2, 10)

    # Previous deployment failures: maximum 15 points
    previous_failure_risk = min(previous_failures * 5, 15)

    # Total score
    risk_score = (
        test_risk
        + coverage_risk
        + security_risk
        + changed_files_risk
        + previous_failure_risk
    )

    # Deployment decision
    if risk_score <= 30:
        risk_level = "SAFE"
        decision = "APPROVED"
    elif risk_score <= 60:
        risk_level = "CAUTION"
        decision = "VALIDATION_REQUIRED"
    else:
        risk_level = "HIGH"
        decision = "BLOCKED"

    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "decision": decision
    }


def main():
    parser = argparse.ArgumentParser(
        description="DeployGuard Nexus Deployment Risk Engine"
    )

    parser.add_argument("--test-failures", type=int, default=0)
    parser.add_argument("--coverage", type=float, default=0)
    parser.add_argument("--security-issues", type=int, default=0)
    parser.add_argument("--changed-files", type=int, default=0)
    parser.add_argument("--previous-failures", type=int, default=0)

    args = parser.parse_args()

    result = calculate_risk(
        test_failures=args.test_failures,
        coverage=args.coverage,
        security_issues=args.security_issues,
        changed_files=args.changed_files,
        previous_failures=args.previous_failures
    )

    print("========================================")
    print("       DEPLOYGUARD NEXUS")
    print("       DEPLOYMENT RISK REPORT")
    print("========================================")
    print()
    print(f"Test Failures       : {args.test_failures}")
    print(f"Code Coverage       : {args.coverage}%")
    print(f"Security Issues     : {args.security_issues}")
    print(f"Changed Files       : {args.changed_files}")
    print(f"Previous Failures   : {args.previous_failures}")
    print()
    print("----------------------------------------")
    print(f"Risk Score          : {result['risk_score']}")
    print(f"Risk Level          : {result['risk_level']}")
    print(f"Deployment Decision : {result['decision']}")
    print("========================================")

    # Save result for later CI/CD and dashboard integration
    with open("risk-result.json", "w", encoding="utf-8") as file:
        json.dump(
            {
                "inputs": {
                    "test_failures": args.test_failures,
                    "coverage": args.coverage,
                    "security_issues": args.security_issues,
                    "changed_files": args.changed_files,
                    "previous_failures": args.previous_failures
                },
                "result": result
            },
            file,
            indent=2
        )


if __name__ == "__main__":
    main()