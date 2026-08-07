from __future__ import annotations

from typing import Any

import pandas as pd

from .cities import ALL_CITIES
from .client import YelpClient
from ..config import Settings
from ..sms.phone import to_e164


DEFAULT_TERMS = ["Lawn Mowing", "Snow removal"]


def normalize_business(
    biz: dict[str, Any],
    search_location: dict[str, Any],
    term: str,
) -> dict[str, Any]:
    location = biz.get("location", {})
    coordinates = biz.get("coordinates", {})
    categories = biz.get("categories", [])

    display_phone = biz.get("display_phone")

    return {
        "id": biz.get("id"),
        "name": biz.get("name"),
        "search_term": term,
        "search_region": search_location["region"],
        "search_city": search_location["city"],
        "rating": biz.get("rating"),
        "review_count": biz.get("review_count"),
        "latitude": coordinates.get("latitude"),
        "longitude": coordinates.get("longitude"),
        "city": location.get("city"),
        "zip_code": location.get("zip_code"),
        "state": location.get("state"),
        "country": location.get("country"),
        "phone": to_e164(display_phone),
        "display_phone": display_phone,
        "categories": ", ".join(cat.get("title", "") for cat in categories),
        "is_closed": biz.get("is_closed"),
        "url": biz.get("url"),
    }


def search_by_service(term: str, settings: Settings, cities: list[dict[str, Any]] | None = None) -> pd.DataFrame:
    client = YelpClient(settings)
    records = []

    for location in cities or ALL_CITIES:
        businesses = client.search_all_pages(location, term)
        records.extend(normalize_business(biz, location, term) for biz in businesses)

    return pd.DataFrame(records)


def collect_companies(settings: Settings, terms: list[str] | None = None) -> pd.DataFrame:
    frames = [search_by_service(term, settings) for term in (terms or DEFAULT_TERMS)]
    combined = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

    if combined.empty:
        return combined

    combined = combined[combined["country"].fillna("") == settings.target_country].copy()
    if combined.empty:
        return combined

    combined["phone"] = combined["phone"].fillna("")
    combined = combined.sort_values(["phone", "review_count"], ascending=[True, False])
    return combined.drop_duplicates(subset=["phone"], keep="first")
