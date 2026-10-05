import json
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def run_command(command, cwd, timeout=180):
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout
        )

        return (
            result.returncode,
            result.stdout,
            result.stderr
        )

    except subprocess.TimeoutExpired:
        return (
            -1,
            "",
            "Command timed out."
        )

    except Exception as error:
        return (
            -1,
            "",
            str(error)
        )


def detect_project(project_path):
    """
    Detect the project type.
    """

    if (
        (project_path / "requirements.txt").exists()
        or
        (project_path / "pyproject.toml").exists()
        or
        (project_path / "setup.py").exists()
    ):
        return "python"

    app_directory = project_path / "app"

    if app_directory.exists():

        if (
            (app_directory / "requirements.txt").exists()
            or
            (app_directory / "pyproject.toml").exists()
            or
            (app_directory / "app.py").exists()
        ):
            return "python"

    if (project_path / "pom.xml").exists():
        return "java"

    if (project_path / "package.json").exists():
        return "node"

    return "unknown"


def find_python_test_directory(project_path):
    """
    Find the directory from which pytest should run.
    """

    tests_directory = project_path / "tests"

    if tests_directory.exists():
        return project_path

    return project_path


def run_python_tests(project_path):
    """
    Run pytest and correctly determine the number
    of passed and failed tests.
    """

    test_directory = find_python_test_directory(
        project_path
    )

    return_code, stdout, stderr = run_command(
        [
            "python",
            "-m",
            "pytest",
            "-q",
            "--tb=no"
        ],
        cwd=test_directory
    )

    output = stdout + "\n" + stderr

    passed = 0
    failures = 0

    # Parse only pytest's final summary line.
    #
    # Examples:
    # 25 passed in 0.41s
    # 24 passed, 1 failed in 0.41s

    for line in output.splitlines():

        line = line.strip()

        if " in " not in line:
            continue

        lower_line = line.lower()

        if (
            "passed" not in lower_line
            and
            "failed" not in lower_line
        ):
            continue

        parts = (
            line
            .replace(",", "")
            .split()
        )

        for index, part in enumerate(parts):

            if part.lower() == "passed":

                if index > 0:

                    try:
                        passed = int(
                            parts[index - 1]
                        )

                    except ValueError:
                        pass

            elif part.lower() == "failed":

                if index > 0:

                    try:
                        failures = int(
                            parts[index - 1]
                        )

                    except ValueError:
                        pass

    # If pytest failed but the summary could not
    # be parsed, report at least one failure.
    if return_code != 0 and failures == 0:
        failures = 1

    return {
        "success": return_code == 0,
        "passed": passed,
        "failures": failures,
        "output": output
    }


def run_python_coverage(project_path):
    """
    Run pytest with coverage and extract the
    TOTAL coverage percentage.
    """

    return_code, stdout, stderr = run_command(
        [
            "python",
            "-m",
            "pytest",
            "--cov=app",
            "--cov-report=term"
        ],
        cwd=project_path
    )

    output = stdout + "\n" + stderr

    coverage = 0.0

    for line in output.splitlines():

        if "TOTAL" not in line.upper():
            continue

        parts = line.split()

        for part in reversed(parts):

            if part.endswith("%"):

                try:
                    coverage = float(
                        part.replace(
                            "%",
                            ""
                        )
                    )

                except ValueError:
                    pass

                break

    return {
        "success": return_code == 0,
        "coverage": coverage,
        "output": output
    }


def run_bandit(project_path):
    """
    Run Bandit security analysis.
    """

    report_file = (
        project_path
        / "bandit-analysis.json"
    )

    return_code, stdout, stderr = run_command(
        [
            "python",
            "-m",
            "bandit",
            "-r",
            "app",
            "backend",
            "-f",
            "json",
            "-o",
            str(report_file)
        ],
        cwd=project_path
    )

    security_issues = 0

    if report_file.exists():

        try:

            with open(
                report_file,
                "r",
                encoding="utf-8"
            ) as file:

                result = json.load(file)

            security_issues = len(
                result.get(
                    "results",
                    []
                )
            )

        except (
            json.JSONDecodeError,
            OSError
        ):

            security_issues = 0

    return {
        "success": return_code == 0,
        "security_issues": security_issues,
        "output": stdout + "\n" + stderr
    }


def count_project_files(project_path):
    """
    Count project files while ignoring generated
    and dependency directories.
    """

    excluded = {
        ".git",
        "__pycache__",
        ".pytest_cache",
        "node_modules",
        ".venv",
        "venv",
        "bandit-analysis.json"
    }

    count = 0

    for path in project_path.rglob("*"):

        if not path.is_file():
            continue

        if any(
            part in excluded
            for part in path.parts
        ):
            continue

        count += 1

    return count


def analyze_repository(repository_url):
    """
    Clone and analyze a public GitHub repository.
    """

    temporary_directory = Path(
        tempfile.mkdtemp(
            prefix="deployguard-"
        )
    )

    repository_directory = (
        temporary_directory
        / "project"
    )

    try:

        print(
            "Cloning repository..."
        )

        clone_result = run_command(
            [
                "git",
                "clone",
                "--depth",
                "1",
                repository_url,
                str(repository_directory)
            ],
            cwd=temporary_directory
        )

        if clone_result[0] != 0:

            return {
                "success": False,
                "error": (
                    "Unable to clone repository."
                ),
                "details": clone_result[2]
            }

        print(
            "Detecting project type..."
        )

        project_type = detect_project(
            repository_directory
        )

        test_failures = 0
        coverage = 0.0
        security_issues = 0
        passed_tests = 0

        if project_type == "python":

            requirements_file = (
                repository_directory
                / "app"
                / "requirements.txt"
            )

            if not requirements_file.exists():

                requirements_file = (
                    repository_directory
                    / "requirements.txt"
                )

            if requirements_file.exists():

                print(
                    "Installing Python dependencies..."
                )

                run_command(
                    [
                        "python",
                        "-m",
                        "pip",
                        "install",
                        "-r",
                        str(requirements_file)
                    ],
                    cwd=repository_directory,
                    timeout=180
                )

            print(
                "Running tests..."
            )

            test_result = run_python_tests(
                repository_directory
            )

            test_failures = (
                test_result["failures"]
            )

            passed_tests = (
                test_result["passed"]
            )

            print(
                "Calculating coverage..."
            )

            coverage_result = (
                run_python_coverage(
                    repository_directory
                )
            )

            coverage = (
                coverage_result["coverage"]
            )

            print(
                "Running security scan..."
            )

            bandit_result = run_bandit(
                repository_directory
            )

            security_issues = (
                bandit_result[
                    "security_issues"
                ]
            )

        elif project_type == "node":

            test_result = run_command(
                [
                    "npm",
                    "test"
                ],
                cwd=repository_directory
            )

            if test_result[0] != 0:
                test_failures = 1

        elif project_type == "java":

            test_result = run_command(
                [
                    "mvn",
                    "test"
                ],
                cwd=repository_directory
            )

            if test_result[0] != 0:
                test_failures = 1

        changed_files = count_project_files(
            repository_directory
        )

        deployment_id = (
            "ANALYSIS-"
            + uuid.uuid4().hex[:8].upper()
        )

        return {
            "success": True,
            "deployment_id": deployment_id,
            "repository": repository_url,
            "project_type": project_type,
            "tests_passed": passed_tests,
            "test_failures": test_failures,
            "coverage": coverage,
            "security_issues": security_issues,
            "changed_files": changed_files,
            "previous_failures": 0
        }

    finally:

        shutil.rmtree(
            temporary_directory,
            ignore_errors=True
        )


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(
        description=(
            "DeployGuard Nexus "
            "Project Analyzer"
        )
    )

    parser.add_argument(
        "repository",
        help=(
            "Public GitHub repository "
            "URL"
        )
    )

    args = parser.parse_args()

    print(
        "========================================"
    )

    print(
        "       DEPLOYGUARD NEXUS"
    )

    print(
        "       PROJECT ANALYZER"
    )

    print(
        "========================================"
    )

    result = analyze_repository(
        args.repository
    )

    print(
        json.dumps(
            result,
            indent=4
        )
    )