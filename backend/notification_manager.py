import json
import os
from datetime import datetime, timezone
from pathlib import Path

import boto3


PROJECT_ROOT = Path(__file__).resolve().parent.parent

LOCAL_NOTIFICATION_FILE = (
    PROJECT_ROOT
    / "backend"
    / "notifications.log"
)


class LocalNotificationManager:
    """
    Local notification system used during development
    and testing.
    """

    def send_notification(
        self,
        subject,
        message
    ):
        timestamp = datetime.now(
            timezone.utc
        ).isoformat()

        notification = {
            "timestamp": timestamp,
            "subject": subject,
            "message": message
        }

        LOCAL_NOTIFICATION_FILE.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        with open(
            LOCAL_NOTIFICATION_FILE,
            "a",
            encoding="utf-8"
        ) as file:

            file.write(
                json.dumps(notification)
                + "\n"
            )

        print("========================================")
        print("       DEPLOYGUARD NEXUS")
        print("        NOTIFICATION SYSTEM")
        print("========================================")
        print()
        print(f"Subject : {subject}")
        print(f"Message : {message}")
        print()
        print("✅ Notification generated.")
        print(
            f"Log file: {LOCAL_NOTIFICATION_FILE}"
        )

        return notification


class SNSNotificationManager:
    """
    AWS SNS notification manager.

    This will be used when the project is connected
    to an AWS account.
    """

    def __init__(self):

        self.topic_arn = os.getenv(
            "SNS_TOPIC_ARN"
        )

        self.region = os.getenv(
            "AWS_REGION",
            "us-east-1"
        )

        if not self.topic_arn:
            raise ValueError(
                "SNS_TOPIC_ARN environment variable "
                "is required."
            )

        self.sns = boto3.client(
            "sns",
            region_name=self.region
        )

    def send_notification(
        self,
        subject,
        message
    ):

        response = self.sns.publish(
            TopicArn=self.topic_arn,
            Subject=subject,
            Message=message
        )

        return response


def create_notification_manager():
    """
    Select the notification backend.

    USE_SNS=true
        -> Amazon SNS

    Otherwise
        -> Local notification log
    """

    use_sns = os.getenv(
        "USE_SNS",
        "false"
    ).lower() == "true"

    if use_sns:
        return SNSNotificationManager()

    return LocalNotificationManager()


notification_manager = (
    create_notification_manager()
)


def send_notification(
    subject,
    message
):
    return notification_manager.send_notification(
        subject,
        message
    )


if __name__ == "__main__":

    send_notification(
        "DeployGuard Nexus Test Notification",
        "This is a test notification."
    )