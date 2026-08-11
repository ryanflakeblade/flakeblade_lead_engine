from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pandas as pd

from ..sms.phone import to_e164
from .search_areas import GREATER_MONTREAL_BOXES, SNOW_REMOVAL_KEYWORDS, SearchBox

if TYPE_CHECKING:
    from .client import GooglePlacesClient


def _nested_get(value: dict[str, Any], *keys: str) -> Any:
    current: Any = value
    for key in keys:
        if not isinstance(current, dict):
            return ""
        current = current.get(key)
    return current if current is not None else ""


def normalize_place(place: dict[str, Any], keyword: str, search_area: str) -> dict[str, Any]:
    types = place.get("types", [])
    national_phone = place.get("nationalPhoneNumber", "")
    international_phone = place.get("internationalPhoneNumber", "")
    sms_phone = to_e164(international_phone) or to_e164(national_phone)

    return {
        "place_id": place.get("id", ""),
        "company_name": _nested_get(place, "displayName", "text"),
        "keyword": keyword,
        "search_area": search_area,
        "national_phone": national_phone,
        "international_phone": international_phone,
        "sms_phone": sms_phone,
        "sms_sendable": bool(sms_phone),
        "email": "",
        "website": place.get("websiteUri", ""),
        "google_maps_url": place.get("googleMapsUri", ""),
        "address": place.get("formattedAddress", ""),
        "short_address": place.get("shortFormattedAddress", ""),
        "rating": place.get("rating", ""),
        "review_count": place.get("userRatingCount", ""),
        "primary_type": place.get("primaryType", ""),
        "primary_type_display": _nested_get(place, "primaryTypeDisplayName", "text"),
        "business_status": place.get("businessStatus", ""),
        "types": "; ".join(str(item) for item in types),
        "latitude": _nested_get(place, "location", "latitude"),
        "longitude": _nested_get(place, "location", "longitude"),
        "lead_source": "Google Places Text Search",
        "lead_segment": "",
        "priority": "",
        "status": "New",
        "next_action": "Check website/contact page for email, then qualify snow removal fit",
        "notes": "Google Places does not return email directly",
    }


def dedupe_places(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: dict[str, dict[str, Any]] = {}
    for row in rows:
        key = row.get("place_id") or f"{row.get('company_name', '')}|{row.get('address', '')}"
        if key not in seen:
            seen[key] = row
            continue

        existing = seen[key]
        for field in ("keyword", "search_area"):
            values = {item.strip() for item in str(existing.get(field, "")).split(";") if item.strip()}
            value = str(row.get(field, "")).strip()
            if value:
                values.add(value)
            existing[field] = "; ".join(sorted(values))

    return list(seen.values())


def collect_places(
    client: "GooglePlacesClient",
    keywords: list[str] | None = None,
    search_boxes: list[SearchBox] | None = None,
    page_size: int = 20,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for keyword in keywords or SNOW_REMOVAL_KEYWORDS:
        for search_box in search_boxes or GREATER_MONTREAL_BOXES:
            places = client.search_all_pages(keyword, search_box, page_size=page_size)
            rows.extend(normalize_place(place, keyword, search_box.name) for place in places)

    return pd.DataFrame(dedupe_places(rows))
