from __future__ import annotations

from typing import Any

import requests

from ..config import Settings


YELP_SEARCH_URL = "https://api.yelp.com/v3/businesses/search"


class YelpClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.session = requests.Session()
        self.session.headers.update(
            {
                "accept": "application/json",
                "authorization": f"Bearer {settings.yelp_api_key}",
            }
        )

    def search_page(
        self,
        location: dict[str, Any],
        term: str,
        offset: int = 0,
        limit: int | None = None,
    ) -> dict[str, Any]:
        params = {
            "latitude": location["latitude"],
            "longitude": location["longitude"],
            "term": term,
            "radius": self.settings.radius_meters,
            "categories": "snow removal",
            "sort_by": "best_match",
            "limit": limit or self.settings.page_limit,
            "offset": offset,
        }
        response = self.session.get(YELP_SEARCH_URL, params=params, timeout=30)
        if response.status_code >= 400:
            print(f"Yelp API error for {location['city']} {term} offset={offset}: {response.text}")
        response.raise_for_status()
        return response.json()

    def search_all_pages(self, location: dict[str, Any], term: str) -> list[dict[str, Any]]:
        businesses: list[dict[str, Any]] = []
        offset = 0

        while True:
            remaining = self.settings.max_search_results - offset
            limit = min(self.settings.page_limit, remaining)
            if limit <= 0:
                break

            data = self.search_page(location, term, offset=offset, limit=limit)
            page_businesses = data.get("businesses", [])
            businesses.extend(page_businesses)

            total = min(data.get("total", 0), self.settings.max_search_results)
            offset += limit
            if not page_businesses or offset >= total:
                break

        print(f"Get {location['city']} {term} {len(businesses)} records")
        return businesses
