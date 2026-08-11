from __future__ import annotations

import argparse
from pathlib import Path

from .config import load_google_places_settings
from .google_places.client import GooglePlacesClient
from .google_places.exporter import DEFAULT_GOOGLE_PLACES_OUTPUT, export_google_places_leads
from .google_places.parser import collect_places
from .google_places.search_areas import GREATER_MONTREAL_BOXES, SNOW_REMOVAL_KEYWORDS


def print_lead_stats(leads) -> None:
    total = int(leads.shape[0])
    if total == 0:
        print("Lead stats: total=0, with_phone=0, sms_sendable=0, missing_or_invalid_phone=0")
        return

    has_phone = (
        leads.get("national_phone", "").fillna("").astype(str).str.strip().ne("")
        | leads.get("international_phone", "").fillna("").astype(str).str.strip().ne("")
    )
    sms_sendable = leads.get("sms_phone", "").fillna("").astype(str).str.strip().ne("")
    with_phone_count = int(has_phone.sum())
    sms_sendable_count = int(sms_sendable.sum())
    missing_or_invalid = total - sms_sendable_count

    print("Lead stats:")
    print(f"  total: {total}")
    print(f"  with any phone: {with_phone_count}")
    print(f"  SMS-ready E.164 phone: {sms_sendable_count}")
    print(f"  missing or invalid for SMS: {missing_or_invalid}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect private CRM leads from Google Places.")
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_GOOGLE_PLACES_OUTPUT,
        help="Output CSV path.",
    )
    parser.add_argument(
        "--keywords",
        nargs="+",
        default=SNOW_REMOVAL_KEYWORDS,
        help="Google Places text search keywords.",
    )
    parser.add_argument("--page-size", type=int, default=20, help="Google Places page size.")
    parser.add_argument(
        "--test-key",
        action="store_true",
        help="Make one tiny Google Places request to verify GOOGLE_MAPS_API_KEY.",
    )
    parser.add_argument(
        "--sleep-seconds",
        type=float,
        default=2.0,
        help="Delay before fetching each nextPageToken page.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = load_google_places_settings()
    client = GooglePlacesClient(settings, sleep_seconds=args.sleep_seconds)

    if args.test_key:
        keyword = args.keywords[0]
        search_box = GREATER_MONTREAL_BOXES[0]
        data = client.search_page(keyword, search_box, page_size=1)
        places = data.get("places", [])
        print("Google Places API key works.")
        print(f"Keyword: {keyword}")
        print(f"Search area: {search_box.name}")
        print(f"Returned places: {len(places)}")
        if places:
            print(f"First place: {places[0].get('displayName', {}).get('text', '')}")
        return

    leads = collect_places(client, keywords=args.keywords, page_size=args.page_size)
    export_google_places_leads(leads, args.output)
    print(f"Exported {leads.shape[0]} Google Places leads")
    print_lead_stats(leads)
    print(f"CSV: {args.output}")


if __name__ == "__main__":
    main()
