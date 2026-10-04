import json
import os
import subprocess
import xml.etree.ElementTree as ET

from risk_engine import calculate_risk


def get_test_failures():
    """Read failed/error test count from PyTest JUnit XML."""
    file_path = "test-results.xml"

    if not os.path.exists(file_path):
        return 0

    root = ET.parse(file_path).getroot()

    failures = 0

    for suite in root.iter("testsuite"):
        failures += int(suite.attrib.get("failures", 0))
        failures += int(suite.attrib.get("errors", 0))

    return failures


def get_coverage():
    """Read total coverage percentage from coverage.py JSON."""
    file_path = "coverage.json"

    if not os.path.exists(file_path):
        return 0.0

    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    return float(data["totals"]["percent_covered"])


def get_security_issues():
    """Read the number of Bandit findings from JSON."""
    file_path = "bandit-report.json"

    if not os.path.exists(file_path):
        return 0

    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    return len(data.get("results", []))


def get_changed_files():
    """Count files changed in the latest Git commit."""
    try:
        result = subprocess.run(
            [
                "git",
                "diff-tree",
                "--root",
                "--no-commit-id",
                "--name-only",
                "-r",
                "HEAD"
            ],
            capture_output=True,
            text=True,
            check=True
        )

        files = [
            line.strip()
            for line in result.stdout.splitlines()
            if line.strip()
        ]

        return len(files)

    except subprocess.CalledProcessError:
        return 0


def main():
    test_failures = get_test_failures()
    coverage = get_coverage()
    security_issues = get_security_issues()
    changed_files = get_changed_files()

    # This will come from DynamoDB later.
    previous_failures = int(
        os.environ.get("PREVIOUS_FAILURES", "0")
    )

    result = calculate_risk(
        test_failures=test_failures,
        coverage=coverage,
        security_issues=security_issues,
        changed_files=changed_files,
        previous_failures=previous_failures
    )

    report = {
        "inputs": {
            "test_failures": test_failures,
            "coverage": coverage,
            "security_issues": security_issues,
            "changed_files": changed_files,
            "previous_failures": previous_failures
        },
        "result": result
    }

    with open("risk-result.json", "w", encoding="utf-8") as file:
        json.dump(report, file, indent=2)

    print("========================================")
    print("       DEPLOYGUARD NEXUS")
    print("       DEPLOYMENT RISK REPORT")
    print("========================================")
    print()
    print(f"Test Failures       : {test_failures}")
    print(f"Code Coverage       : {coverage:.2f}%")
    print(f"Security Issues     : {security_issues}")
    print(f"Changed Files       : {changed_files}")
    print(f"Previous Failures   : {previous_failures}")
    print()
    print("----------------------------------------")
    print(f"Risk Score          : {result['risk_score']}")
    print(f"Risk Level          : {result['risk_level']}")
    print(f"Deployment Decision : {result['decision']}")
    print("========================================")


if __name__ == "__main__":
    main()