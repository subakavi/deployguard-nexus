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

from notification_manager import (
    LocalNotificationManager
)


def test_local_notification():

    manager = LocalNotificationManager()

    result = manager.send_notification(
        "Test Subject",
        "Test Message"
    )

    assert result["subject"] == "Test Subject"
    assert result["message"] == "Test Message"
    assert "timestamp" in result