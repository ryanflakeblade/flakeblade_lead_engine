from __future__ import annotations

from pathlib import Path

import pandas as pd

from ..config import PROJECT_ROOT
from ..google_places.exporter import DEFAULT_GOOGLE_PLACES_OUTPUT
from ..sms.phone import to_e164


DEFAULT_YELP_COMPANIES_PATH = PROJECT_ROOT / "data" / "processed" / "companies.csv"
DEFAULT_CRM_COMPANIES_PATH = PROJECT_ROOT / "data" / "processed" / "crm_companies.csv"

CRM_COLUMNS = [
    "source",
    "source_id",
    "name",
    "search_term",
    "search_region",
    "search_city",
    "rating",
    "review_count",
    "latitude",
    "longitude",
    "address",
    "city",
    "zip_code",
    "state",
    "country",
    "phone",
    "display_phone",
    "email",
    "website",
    "source_url",
    "categories",
    "business_status",
    "is_closed",
    "lead_segment",
    "priority",
    "status",
    "next_action",
    "notes",
    "sms_status",
    "sms_message_sid",
    "sms_error",
]


def _empty_crm_frame() -> pd.DataFrame:
    return pd.DataFrame(columns=CRM_COLUMNS)


def _column(df: pd.DataFrame, name: str, default: str = "") -> pd.Series:
    if name in df.columns:
        return df[name].fillna("")
    return pd.Series([default] * len(df), index=df.index)


def normalize_yelp_companies(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return _empty_crm_frame()

    normalized = pd.DataFrame(index=df.index)
    normalized["source"] = "Yelp"
    normalized["source_id"] = _column(df, "id")
    normalized["name"] = _column(df, "name")
    normalized["search_term"] = _column(df, "search_term")
    normalized["search_region"] = _column(df, "search_region")
    normalized["search_city"] = _column(df, "search_city")
    normalized["rating"] = _column(df, "rating")
    normalized["review_count"] = _column(df, "review_count")
    normalized["latitude"] = _column(df, "latitude")
    normalized["longitude"] = _column(df, "longitude")
    normalized["address"] = ""
    normalized["city"] = _column(df, "city")
    normalized["zip_code"] = _column(df, "zip_code")
    normalized["state"] = _column(df, "state")
    normalized["country"] = _column(df, "country")
    normalized["phone"] = _column(df, "phone").map(to_e164)
    normalized["display_phone"] = _column(df, "display_phone")
    normalized["email"] = ""
    normalized["website"] = ""
    normalized["source_url"] = _column(df, "url")
    normalized["categories"] = _column(df, "categories")
    normalized["business_status"] = ""
    normalized["is_closed"] = _column(df, "is_closed")
    normalized["lead_segment"] = ""
    normalized["priority"] = ""
    normalized["status"] = "New"
    normalized["next_action"] = "Qualify fit, then preview SMS before sending"
    normalized["notes"] = "Imported from Yelp processed companies.csv"
    return _ensure_crm_columns(normalized)


def normalize_google_places(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return _empty_crm_frame()

    phone = _column(df, "sms_phone")
    fallback_phone = _column(df, "international_phone").map(to_e164)
    national_fallback = _column(df, "national_phone").map(to_e164)
    phone = phone.where(phone.astype(str).str.startswith("+"), fallback_phone)
    phone = phone.where(phone.astype(str).str.startswith("+"), national_fallback)

    normalized = pd.DataFrame(index=df.index)
    normalized["source"] = "Google Places"
    normalized["source_id"] = _column(df, "place_id")
    normalized["name"] = _column(df, "company_name")
    normalized["search_term"] = _column(df, "keyword")
    normalized["search_region"] = "Greater Montreal"
    normalized["search_city"] = _column(df, "search_area")
    normalized["rating"] = _column(df, "rating")
    normalized["review_count"] = _column(df, "review_count")
    normalized["latitude"] = _column(df, "latitude")
    normalized["longitude"] = _column(df, "longitude")
    normalized["address"] = _column(df, "address")
    normalized["city"] = ""
    normalized["zip_code"] = ""
    normalized["state"] = "QC"
    normalized["country"] = "CA"
    normalized["phone"] = phone
    normalized["display_phone"] = _column(df, "national_phone")
    normalized["email"] = _column(df, "email")
    normalized["website"] = _column(df, "website")
    normalized["source_url"] = _column(df, "google_maps_url")
    normalized["categories"] = _column(df, "types")
    normalized["business_status"] = _column(df, "business_status")
    normalized["is_closed"] = _column(df, "business_status").ne("OPERATIONAL")
    normalized["lead_segment"] = _column(df, "lead_segment")
    normalized["priority"] = _column(df, "priority")
    normalized["status"] = _column(df, "status", "New")
    normalized["next_action"] = _column(df, "next_action")
    normalized["notes"] = _column(df, "notes")
    return _ensure_crm_columns(normalized)


def _ensure_crm_columns(df: pd.DataFrame) -> pd.DataFrame:
    for column in CRM_COLUMNS:
        if column not in df.columns:
            df[column] = ""
    return df[CRM_COLUMNS]


def combine_crm_companies(frames: list[pd.DataFrame]) -> pd.DataFrame:
    non_empty = [frame for frame in frames if not frame.empty]
    if not non_empty:
        return _empty_crm_frame()

    combined = pd.concat(non_empty, ignore_index=True)
    combined["phone"] = combined["phone"].fillna("").map(to_e164)
    combined["name"] = combined["name"].fillna("").astype(str).str.strip()

    with_phone = combined[combined["phone"].ne("")].copy()
    without_phone = combined[combined["phone"].eq("")].copy()

    with_phone = with_phone.sort_values(
        ["phone", "source", "review_count"],
        ascending=[True, True, False],
        kind="stable",
    ).drop_duplicates(subset=["phone"], keep="first")
    without_phone = without_phone.drop_duplicates(subset=["source", "source_id", "name"], keep="first")

    result = pd.concat([with_phone, without_phone], ignore_index=True)
    return _ensure_crm_columns(result.sort_values(["source", "name"], kind="stable").reset_index(drop=True))


def build_crm_companies(
    yelp_path: Path = DEFAULT_YELP_COMPANIES_PATH,
    google_places_path: Path = DEFAULT_GOOGLE_PLACES_OUTPUT,
) -> pd.DataFrame:
    frames = []
    if yelp_path.exists():
        frames.append(normalize_yelp_companies(pd.read_csv(yelp_path, keep_default_na=False)))
    if google_places_path.exists():
        frames.append(normalize_google_places(pd.read_csv(google_places_path, keep_default_na=False)))
    return combine_crm_companies(frames)


def export_crm_companies(df: pd.DataFrame, output_path: Path = DEFAULT_CRM_COMPANIES_PATH) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    _ensure_crm_columns(df).to_csv(output_path, index=False, encoding="utf-8-sig")
