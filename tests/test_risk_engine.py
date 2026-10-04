import sys
import os

sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "risk-engine")
    )
)

from risk_engine import calculate_risk


def test_safe_deployment():
    result = calculate_risk(
        test_failures=0,
        coverage=90,
        security_issues=0,
        changed_files=3,
        previous_failures=0
    )

    assert result["risk_level"] == "SAFE"
    assert result["decision"] == "APPROVED"
    assert result["risk_score"] <= 30


def test_caution_deployment():
    result = calculate_risk(
        test_failures=1,
        coverage=70,
        security_issues=2,
        changed_files=15,
        previous_failures=1
    )

    assert result["risk_level"] == "CAUTION"
    assert result["decision"] == "VALIDATION_REQUIRED"
    assert 31 <= result["risk_score"] <= 60


def test_high_risk_deployment():
    result = calculate_risk(
        test_failures=3,
        coverage=40,
        security_issues=4,
        changed_files=50,
        previous_failures=3
    )

    assert result["risk_level"] == "HIGH"
    assert result["decision"] == "BLOCKED"
    assert result["risk_score"] > 60