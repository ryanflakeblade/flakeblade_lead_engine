from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    yelp_api_key: str
    google_maps_api_key: str | None = None
    twilio_account_sid: str | None = None
    twilio_auth_token: str | None = None
    twilio_from_number: str | None = None
    output_csv: Path = PROJECT_ROOT / "data" / "processed" / "companies.csv"
    output_json: Path = PROJECT_ROOT / "data" / "public" / "canada_leads.json"
    radius_meters: int = 40000
    page_limit: int = 50
    max_search_results: int = 240
    target_country: str = "CA"


def load_settings() -> Settings:
    load_dotenv(PROJECT_ROOT / ".env")
    api_key = os.getenv("YELP_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Missing YELP_API_KEY. Set it in your environment or in a local .env file."
        )
    return Settings(
        yelp_api_key=api_key,
        google_maps_api_key=os.getenv("GOOGLE_MAPS_API_KEY"),
        twilio_account_sid=os.getenv("TWILIO_ACCOUNT_SID"),
        twilio_auth_token=os.getenv("TWILIO_AUTH_TOKEN"),
        twilio_from_number=os.getenv("TWILIO_FROM_NUMBER"),
    )


def load_sms_settings() -> Settings:
    load_dotenv(PROJECT_ROOT / ".env")
    return Settings(
        yelp_api_key=os.getenv("YELP_API_KEY", ""),
        google_maps_api_key=os.getenv("GOOGLE_MAPS_API_KEY"),
        twilio_account_sid=os.getenv("TWILIO_ACCOUNT_SID"),
        twilio_auth_token=os.getenv("TWILIO_AUTH_TOKEN"),
        twilio_from_number=os.getenv("TWILIO_FROM_NUMBER"),
    )


def load_google_places_settings() -> Settings:
    load_dotenv(PROJECT_ROOT / ".env")
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Missing GOOGLE_MAPS_API_KEY. Set it in your environment or in a local .env file."
        )
    return Settings(
        yelp_api_key=os.getenv("YELP_API_KEY", ""),
        google_maps_api_key=api_key,
        twilio_account_sid=os.getenv("TWILIO_ACCOUNT_SID"),
        twilio_auth_token=os.getenv("TWILIO_AUTH_TOKEN"),
        twilio_from_number=os.getenv("TWILIO_FROM_NUMBER"),
    )
