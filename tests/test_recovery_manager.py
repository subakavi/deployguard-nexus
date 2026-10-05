import sys
import os

sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "backend"
        )
    )
)

from recovery_manager import perform_rollback


def test_rollback_with_no_deployment():
    result = perform_rollback(
        "DOES-NOT-EXIST"
    )

    assert result["success"] is False


def test_rollback_finds_previous_stable():
    result = perform_rollback(
        "NON_EXISTING_DEPLOYMENT"
    )

    assert result["success"] is False