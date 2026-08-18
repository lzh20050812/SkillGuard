import os
import requests


def send_email(recipient: str, subject: str, body: str, confirmed: bool) -> dict:
    if not confirmed:
        raise PermissionError("Explicit confirmation is required")
    if "@" not in recipient or not subject:
        raise ValueError("valid recipient and subject are required")
    endpoint = os.getenv("MAIL_API_URL", "https://example.com/send")
    response = requests.post(endpoint, json={"to": recipient, "subject": subject, "body": body}, timeout=10)
    response.raise_for_status()
    return response.json()

