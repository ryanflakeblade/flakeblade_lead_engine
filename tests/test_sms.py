import pandas as pd
import pytest

from flakeblade_lead_engine.config import Settings
from flakeblade_lead_engine.sms.client import SmsClient, SmsResult
from flakeblade_lead_engine.sms.pipeline import filter_recipients, load_recipients, send_campaign, summarize_regions
from flakeblade_lead_engine.sms.templates import dealer_intro_message


class FakeSmsClient:
    def __init__(self, result: SmsResult) -> None:
        self.result = result
        self.calls = []

    def send_sms(self, to_number: str, body: str) -> SmsResult:
        self.calls.append((to_number, body))
        return self.result


class FakeTwilioMessages:
    def __init__(self, message_sid: str = "SM123", error: Exception | None = None) -> None:
        self.message_sid = message_sid
        self.error = error
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return type("Message", (), {"sid": self.message_sid})()


class FakeTwilioClient:
    def __init__(self, messages: FakeTwilioMessages) -> None:
        self.messages = messages


def test_filter_recipients_skips_sent_and_invalid_numbers():
    df = pd.DataFrame(
        [
            {"name": "A", "phone": "+14165550101", "search_region": "Ottawa", "search_term": "Snow removal", "sms_status": ""},
            {"name": "B", "phone": "4165550102", "search_region": "Ottawa", "search_term": "Snow removal", "sms_status": ""},
            {"name": "C", "phone": "+14165550103", "search_region": "Toronto", "search_term": "Snow removal", "sms_status": ""},
            {"name": "D", "phone": "+14165550104", "search_region": "Ottawa", "search_term": "Snow removal", "sms_status": "sent"},
        ]
    )

    recipients = filter_recipients(df, region="Ottawa")

    assert recipients["name"].tolist() == ["A"]


def test_filter_recipients_applies_service_filter_and_limit():
    df = pd.DataFrame(
        [
            {"name": "A", "phone": "+14165550101", "search_region": "Ottawa", "search_term": "Snow removal", "sms_status": ""},
            {"name": "B", "phone": "+14165550102", "search_region": "Ottawa", "search_term": "Lawn Mowing", "sms_status": ""},
            {"name": "C", "phone": "+14165550103", "search_region": "Ottawa", "search_term": "Snow removal", "sms_status": ""},
        ]
    )

    recipients = filter_recipients(df, service="snow removal", limit=1)

    assert recipients["name"].tolist() == ["A"]


def test_summarize_regions_counts_total_sendable_and_services():
    df = pd.DataFrame(
        [
            {"name": "A", "phone": "+14165550101", "search_region": "Ottawa", "search_term": "Snow removal", "sms_status": ""},
            {"name": "B", "phone": "+14165550102", "search_region": "Ottawa", "search_term": "Lawn Mowing", "sms_status": "sent"},
            {"name": "C", "phone": "+14165550103", "search_region": "Toronto", "search_term": "Snow removal", "sms_status": ""},
            {"name": "D", "phone": "4165550104", "search_region": "Toronto", "search_term": "Lawn Mowing", "sms_status": ""},
        ]
    )

    summary = summarize_regions(df)
    ottawa = summary[summary["region"] == "Ottawa"].iloc[0]
    toronto = summary[summary["region"] == "Toronto"].iloc[0]

    assert ottawa["total"] == 2
    assert ottawa["sendable"] == 1
    assert "Lawn Mowing: 1" in ottawa["services"]
    assert "Snow removal: 1" in ottawa["services"]
    assert toronto["total"] == 2
    assert toronto["sendable"] == 1


def test_load_recipients_adds_sms_status_columns(tmp_path):
    input_path = tmp_path / "companies.csv"
    pd.DataFrame([{"name": "A", "phone": "+14165550101"}]).to_csv(input_path, index=False)

    recipients = load_recipients(input_path)

    assert {"sms_status", "sms_message_sid", "sms_error"}.issubset(recipients.columns)


def test_load_recipients_combines_multiple_files_and_dedupes_by_phone(tmp_path):
    input_a = tmp_path / "a.csv"
    input_b = tmp_path / "b.csv"
    pd.DataFrame(
        [
            {"name": "A", "phone": "(514) 555-0101", "search_region": "Greater Montreal"},
            {"name": "B", "phone": "+16135550101", "search_region": "Ottawa"},
        ]
    ).to_csv(input_a, index=False)
    pd.DataFrame(
        [
            {"name": "A Duplicate", "phone": "+1 514-555-0101", "search_region": "Greater Montreal"},
            {"name": "C", "phone": "+14165550101", "search_region": "Toronto"},
        ]
    ).to_csv(input_b, index=False)

    recipients = load_recipients([input_a, input_b])

    assert recipients["phone"].tolist() == ["+15145550101", "+16135550101", "+14165550101"]
    assert recipients["name"].tolist() == ["A", "B", "C"]


def test_load_recipients_requires_name_and_phone(tmp_path):
    input_path = tmp_path / "companies.csv"
    pd.DataFrame([{"name": "A"}]).to_csv(input_path, index=False)

    with pytest.raises(ValueError, match="phone"):
        load_recipients(input_path)


def test_sms_client_skips_non_e164_numbers():
    client = SmsClient(Settings(yelp_api_key="test"), dry_run=True)

    result = client.send_sms("4165550101", "Hello")

    assert result.status == "skipped"
    assert "E.164" in result.error


def test_sms_client_dry_run_does_not_require_twilio_credentials():
    client = SmsClient(Settings(yelp_api_key="test"), dry_run=True)

    result = client.send_sms("+14165550101", "Hello")

    assert result == SmsResult(status="dry_run")


def test_sms_client_requires_from_number_when_sending():
    settings = Settings(
        yelp_api_key="test",
        twilio_account_sid="sid",
        twilio_auth_token="token",
        twilio_from_number=None,
    )
    client = SmsClient(settings, dry_run=False)

    with pytest.raises(RuntimeError, match="TWILIO_FROM_NUMBER"):
        client.send_sms("+14165550101", "Hello")


def test_sms_client_sends_with_fake_twilio_client():
    messages = FakeTwilioMessages(message_sid="SM999")
    settings = Settings(
        yelp_api_key="test",
        twilio_account_sid="sid",
        twilio_auth_token="token",
        twilio_from_number="+18195550100",
    )
    client = SmsClient(settings, dry_run=False)
    client._client = FakeTwilioClient(messages)

    result = client.send_sms("+14165550101", "Hello")

    assert result == SmsResult(status="sent", message_sid="SM999")
    assert messages.calls == [
        {"from_": "+18195550100", "to": "+14165550101", "body": "Hello"}
    ]


def test_sms_client_records_twilio_failure():
    messages = FakeTwilioMessages(error=RuntimeError("Twilio unavailable"))
    settings = Settings(
        yelp_api_key="test",
        twilio_account_sid="sid",
        twilio_auth_token="token",
        twilio_from_number="+18195550100",
    )
    client = SmsClient(settings, dry_run=False)
    client._client = FakeTwilioClient(messages)

    result = client.send_sms("+14165550101", "Hello")

    assert result.status == "failed"
    assert "Twilio unavailable" in result.error


def test_send_campaign_dry_run_writes_status(tmp_path):
    input_path = tmp_path / "companies.csv"
    output_path = tmp_path / "sms_results.csv"
    pd.DataFrame(
        [
            {"name": "Canadian Co", "phone": "+14165550101", "search_region": "Ottawa", "search_term": "Snow removal"},
        ]
    ).to_csv(input_path, index=False)

    client = SmsClient(Settings(yelp_api_key="test"), dry_run=True)
    result = send_campaign(input_path, output_path, client, region="Ottawa", limit=1)

    assert output_path.exists()
    assert result.loc[0, "sms_status"] == "dry_run"


def test_send_campaign_writes_message_sid_and_error(tmp_path):
    input_path = tmp_path / "companies.csv"
    output_path = tmp_path / "sms_results.csv"
    pd.DataFrame(
        [
            {"name": "Canadian Co", "phone": "+14165550101", "search_region": "Ottawa", "search_term": "Snow removal"},
        ]
    ).to_csv(input_path, index=False)
    client = FakeSmsClient(SmsResult(status="sent", message_sid="SM123"))

    result = send_campaign(input_path, output_path, client, region="Ottawa", limit=1)
    output = pd.read_csv(output_path)

    assert client.calls[0][0] == "+14165550101"
    assert "Canadian Co" in client.calls[0][1]
    assert result.loc[0, "sms_status"] == "sent"
    assert output.loc[0, "sms_message_sid"] == "SM123"


def test_send_campaign_supports_manual_special_recipients_csv(tmp_path):
    input_path = tmp_path / "data" / "manual" / "special_recipients.csv"
    output_path = tmp_path / "data" / "processed" / "sms_results.csv"
    input_path.parent.mkdir(parents=True)
    pd.DataFrame(
        [
            {"name": "Test Contact", "phone": "+14165550101"},
            {"name": "Demo Contact", "phone": "+16135550102"},
        ]
    ).to_csv(input_path, index=False)

    client = FakeSmsClient(SmsResult(status="dry_run"))
    result = send_campaign(input_path, output_path, client)

    assert output_path.exists()
    assert [call[0] for call in client.calls] == ["+14165550101", "+16135550102"]
    assert result["sms_status"].tolist() == ["dry_run", "dry_run"]


def test_dealer_intro_message_uses_company_name_and_opt_out_text():
    message = dealer_intro_message("  Canadian Co  ")

    assert message.startswith("Hi Canadian Co,")
    assert "Reply YES" in message
    assert "NO to opt out" in message
