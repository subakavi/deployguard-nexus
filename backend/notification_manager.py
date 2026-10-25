import json
import os
from datetime import datetime, timezone
from pathlib import Path

import boto3
from botocore.exceptions import ClientError


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
        message,
        owner_email=None
    ):
        timestamp = datetime.now(
            timezone.utc
        ).isoformat()

        notification = {
            "timestamp": timestamp,
            "subject": subject,
            "message": message
        }

        if owner_email:
            notification["ownerEmail"] = owner_email

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

    def subscribe_user(self, email):
        return None


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
        message,
        owner_email=None
    ):

        arguments = {
            "TopicArn": self.topic_arn,
            "Subject": subject,
            "Message": message
        }

        # Per-user alerts: subscriptions filter on this attribute.
        if owner_email:
            arguments["MessageAttributes"] = {
                "ownerEmail": {
                    "DataType": "String",
                    "StringValue": owner_email.lower()
                }
            }

        return self.sns.publish(**arguments)

    def subscribe_user(self, email):
        """
        Subscribe a user's email to the shared topic with a filter
        so the user only receives alerts about their own deployments.
        AWS sends the user a confirmation email the first time.
        """

        try:
            response = self.sns.subscribe(
                TopicArn=self.topic_arn,
                Protocol="email",
                Endpoint=email,
                Attributes={
                    "FilterPolicy": json.dumps({
                        "ownerEmail": [email.lower()]
                    })
                },
                ReturnSubscriptionArn=True
            )
            return response.get("SubscriptionArn")

        except ClientError as error:
            # e.g. the address already has a subscription
            print(f"SNS subscribe skipped: {error}")
            return None


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
    message,
    owner_email=None
):
    return notification_manager.send_notification(
        subject,
        message,
        owner_email
    )


def subscribe_user_email(email):
    return notification_manager.subscribe_user(email)


if __name__ == "__main__":

    send_notification(
        "DeployGuard Nexus Test Notification",
        "This is a test notification."
    )