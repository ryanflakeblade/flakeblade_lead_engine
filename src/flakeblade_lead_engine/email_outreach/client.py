from __future__ import annotations

import smtplib
from dataclasses import dataclass
from email.message import EmailMessage

from ..config import Settings


@dataclass(frozen=True)
class EmailResult:
    status: str
    message_id: str = ""
    error: str = ""


class EmailClient:
    def __init__(self, settings: Settings, dry_run: bool = True) -> None:
        self.settings = settings
        self.dry_run = dry_run

    def send_email(self, to_email: str, subject: str, body: str) -> EmailResult:
        to_email = str(to_email).strip()
        if "@" not in to_email:
            return EmailResult(status="skipped", error="Invalid email address.")

        if self.dry_run:
            return EmailResult(status="dry_run")

        if not self.settings.smtp_host:
            raise RuntimeError("Missing SMTP_HOST.")
        if not self.settings.smtp_from_email:
            raise RuntimeError("Missing SMTP_FROM_EMAIL.")

        message = EmailMessage()
        message["From"] = self.settings.smtp_from_email
        message["To"] = to_email
        message["Subject"] = subject
        message.set_content(body)

        try:
            with smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port, timeout=30) as smtp:
                smtp.starttls()
                if self.settings.smtp_username and self.settings.smtp_password:
                    smtp.login(self.settings.smtp_username, self.settings.smtp_password)
                smtp.send_message(message)
        except Exception as exc:
            return EmailResult(status="failed", error=str(exc))

        return EmailResult(status="sent", message_id=message["Message-ID"] or "")

