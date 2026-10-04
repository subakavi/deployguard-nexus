def calculate_risk(
    test_failures,
    coverage,
    security_issues,
    changed_files,
    previous_failures
):
    # Test failures: maximum 30 points
    test_risk = min(test_failures * 10, 30)

    # Coverage: maximum 20 points
    if coverage >= 80:
        coverage_risk = 0
    elif coverage >= 60:
        coverage_risk = 10
    else:
        coverage_risk = 20

    # Security issues: maximum 25 points
    security_risk = min(security_issues * 5, 25)

    # Changed files: maximum 10 points
    changed_files_risk = min(changed_files // 10 * 2, 10)

    # Previous deployment failures: maximum 15 points
    previous_failure_risk = min(previous_failures * 5, 15)

    # Total risk score
    risk_score = (
        test_risk
        + coverage_risk
        + security_risk
        + changed_files_risk
        + previous_failure_risk
    )

    # Risk classification
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


if __name__ == "__main__":
    result = calculate_risk(
        test_failures=0,
        coverage=90,
        security_issues=1,
        changed_files=3,
        previous_failures=0
    )

    print("DeployGuard Nexus Risk Analysis")
    print("--------------------------------")
    print(f"Risk Score : {result['risk_score']}")
    print(f"Risk Level : {result['risk_level']}")
    print(f"Decision   : {result['decision']}")