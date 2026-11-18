import smtplib
from email.message import EmailMessage

from .config import settings


class EmailDeliveryError(Exception):
    pass


def send_verification_email(name: str, email: str, raw_token: str) -> None:
    verification_url = f"{settings.verification_base_url}?token={raw_token}"
    message = EmailMessage()
    message["Subject"] = "Confirm your Buy Me A Random Gift account"
    message["From"] = settings.mail_from
    message["To"] = email
    message.set_content(
        f"Hi {name},\n\nConfirm your email address by opening this link:\n{verification_url}\n\nThis link expires in 24 hours.\n"
    )
    try:
        with smtplib.SMTP(settings.mail_host, settings.mail_port) as smtp:
            smtp.send_message(message)
    except OSError as exc:
        raise EmailDeliveryError from exc
