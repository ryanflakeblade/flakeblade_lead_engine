import pandas as pd
import pytest

from flakeblade_lead_engine.config import Settings
from flakeblade_lead_engine.email_outreach.client import EmailClient, EmailResult
from flakeblade_lead_engine.email_outreach.pipeline import (
    filter_email_recipients,
    load_email_recipients,
    send_email_campaign,
)
from flakeblade_lead_engine.email_outreach.templates import dealer_intro_email, dealer_intro_subject


class FakeEmailClient:
    def __init__(self, result: EmailResult) -> None:
        self.result = result
        self.calls = []

    def send_email(self, to_email: str, subject: str, body: str) -> EmailResult:
        self.calls.append((to_email, subject, body))
        return self.result


def test_load_email_recipients_supports_rgcq_columns(tmp_path):
    input_path = tmp_path / "rgcq.csv"
    pd.DataFrame(
        [
            {
                "Company Name": "JML INC.",
                "Contact Person": "Chad Quessy",
                "Email": "chad@example.com",
            }
        ]
    ).to_csv(input_path, index=False)

    recipients = load_email_recipients(input_path)

    assert recipients.loc[0, "name"] == "JML INC."
    assert recipients.loc[0, "contact_name"] == "Chad Quessy"
    assert recipients.loc[0, "email"] == "chad@example.com"
    assert {"email_status", "email_message_id", "email_error"}.issubset(recipients.columns)


def test_filter_email_recipients_skips_invalid_sent_and_duplicate_emails():
    df = pd.DataFrame(
        [
            {"name": "A", "email": "a@example.com", "email_status": ""},
            {"name": "Duplicate A", "email": "a@example.com", "email_status": ""},
            {"name": "Invalid", "email": "invalid", "email_status": ""},
            {"name": "Sent", "email": "sent@example.com", "email_status": "sent"},
        ]
    )

    recipients = filter_email_recipients(df)

    assert recipients["name"].tolist() == ["A"]


def test_email_client_dry_run_does_not_require_smtp_credentials():
    client = EmailClient(Settings(yelp_api_key="test"), dry_run=True)

    result = client.send_email("lead@example.com", "Subject", "Body")

    assert result == EmailResult(status="dry_run")


def test_email_client_skips_invalid_email():
    client = EmailClient(Settings(yelp_api_key="test"), dry_run=True)

    result = client.send_email("not-an-email", "Subject", "Body")

    assert result.status == "skipped"
    assert "Invalid email" in result.error


def test_email_client_requires_smtp_settings_when_sending():
    client = EmailClient(Settings(yelp_api_key="test"), dry_run=False)

    with pytest.raises(RuntimeError, match="SMTP_HOST"):
        client.send_email("lead@example.com", "Subject", "Body")


def test_send_email_campaign_dry_run_writes_status(tmp_path):
    input_path = tmp_path / "rgcq.csv"
    output_path = tmp_path / "email_results.csv"
    pd.DataFrame(
        [
            {
                "Company Name": "JML INC.",
                "Contact Person": "Chad Quessy",
                "Email": "chad@example.com",
            }
        ]
    ).to_csv(input_path, index=False)
    client = FakeEmailClient(EmailResult(status="dry_run"))

    result = send_email_campaign(input_path, output_path, client)

    assert output_path.exists()
    assert result.loc[0, "email_status"] == "dry_run"
    assert client.calls[0][0] == "chad@example.com"
    assert "JML INC." in client.calls[0][1]
    assert "Chad Quessy" in client.calls[0][2]


def test_send_email_campaign_output_avoids_duplicate_email_headers(tmp_path):
    input_path = tmp_path / "rgcq.csv"
    output_path = tmp_path / "email_results.csv"
    pd.DataFrame(
        [
            {
                "Company Name": "JML INC.",
                "Email": "chad@example.com",
            }
        ]
    ).to_csv(input_path, index=False)
    client = FakeEmailClient(EmailResult(status="dry_run"))

    send_email_campaign(input_path, output_path, client)
    columns = pd.read_csv(output_path, nrows=0).columns.tolist()

    assert "Email" in columns
    assert "email" not in columns
    assert len([column.lower() for column in columns]) == len(set(column.lower() for column in columns))


def test_dealer_intro_email_uses_company_and_contact():
    subject = dealer_intro_subject("JML INC.")
    body = dealer_intro_email("JML INC.", "Chad")

    assert "JML INC." in subject
    assert body.startswith("Hi Chad,")
    assert "snow removal" in body
