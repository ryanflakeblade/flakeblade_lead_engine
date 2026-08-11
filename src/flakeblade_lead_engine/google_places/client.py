from __future__ import annotations

import time
from typing import Any

import requests

from ..config import Settings
from .search_areas import SearchBox


GOOGLE_PLACES_TEXT_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"

DEFAULT_FIELD_MASK = ",".join(
    [
        "places.id",
        "places.displayName",
        "places.nationalPhoneNumber",
        "places.internationalPhoneNumber",
        "places.formattedAddress",
        "places.shortFormattedAddress",
        "places.websiteUri",
        "places.googleMapsUri",
        "places.rating",
        "places.userRatingCount",
        "places.primaryType",
        "places.primaryTypeDisplayName",
        "places.businessStatus",
        "places.types",
        "places.location",
        "nextPageToken",
    ]
)


class GooglePlacesClient:
    def __init__(
        self,
        settings: Settings,
        field_mask: str = DEFAULT_FIELD_MASK,
        sleep_seconds: float = 2.0,
    ) -> None:
        if not settings.google_maps_api_key:
            raise RuntimeError("Missing GOOGLE_MAPS_API_KEY.")

        self.sleep_seconds = sleep_seconds
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Content-Type": "application/json",
                "X-Goog-Api-Key": settings.google_maps_api_key,
                "X-Goog-FieldMask": field_mask,
            }
        )

    def search_page(
        self,
        keyword: str,
        search_box: SearchBox,
        page_size: int = 20,
        page_token: str | None = None,
        language_code: str = "fr",
        region_code: str = "CA",
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "textQuery": keyword,
            "pageSize": page_size,
            "includePureServiceAreaBusinesses": True,
            "locationRestriction": {"rectangle": search_box.to_places_rectangle()},
            "languageCode": language_code,
            "regionCode": region_code,
        }
        if page_token:
            payload["pageToken"] = page_token

        response = self.session.post(GOOGLE_PLACES_TEXT_SEARCH_URL, json=payload, timeout=30)
        if response.status_code >= 400:
            print(f"Google Places API error for {keyword} in {search_box.name}: {response.text}")
        response.raise_for_status()
        return response.json()

    def search_all_pages(
        self,
        keyword: str,
        search_box: SearchBox,
        page_size: int = 20,
        language_code: str = "fr",
        region_code: str = "CA",
    ) -> list[dict[str, Any]]:
        places: list[dict[str, Any]] = []
        page_token: str | None = None

        while True:
            data = self.search_page(
                keyword=keyword,
                search_box=search_box,
                page_size=page_size,
                page_token=page_token,
                language_code=language_code,
                region_code=region_code,
            )
            places.extend(data.get("places", []))
            page_token = data.get("nextPageToken")
            if not page_token:
                break
            time.sleep(self.sleep_seconds)

        print(f"Get {search_box.name} {keyword} {len(places)} records")
        return places

