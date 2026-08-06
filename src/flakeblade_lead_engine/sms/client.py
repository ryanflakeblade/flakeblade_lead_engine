from __future__ import annotations

from dataclasses import dataclass

from ..config import Settings


@dataclass(frozen=True)
class SmsResult:
    status: str
    message_sid: str = ""
    error: str = ""


class SmsClient:
    def __init__(self, settings: Settings, dry_run: bool = True) -> None:
        self.settings = settings
        self.dry_run = dry_run
        self._client = None

    def _twilio_client(self):
        if self._client is not None:
            return self._client

        if not self.settings.twilio_account_sid or not self.settings.twilio_auth_token:
            raise RuntimeError("Missing TWILIO_ACCOUNT_SID or TWILIO_AUTH_TOKEN.")

        from twilio.rest import Client

        self._client = Client(self.settings.twilio_account_sid, self.settings.twilio_auth_token)
        return self._client

    def send_sms(self, to_number: str, body: str) -> SmsResult:
        if not to_number.startswith("+"):
            return SmsResult(status="skipped", error="Phone number must be E.164 format.")

        if self.dry_run:
            return SmsResult(status="dry_run")

        if not self.settings.twilio_from_number:
            raise RuntimeError("Missing TWILIO_FROM_NUMBER.")

        try:
            message = self._twilio_client().messages.create(
                from_=self.settings.twilio_from_number,
                to=to_number,
                body=body,
            )
            return SmsResult(status="sent", message_sid=message.sid)
        except Exception as exc:
            return SmsResult(status="failed", error=str(exc))

