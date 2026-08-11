import pandas as pd

from flakeblade_lead_engine.google_places.exporter import export_google_places_leads
from flakeblade_lead_engine.google_places.parser import dedupe_places, normalize_place


def test_normalize_place_maps_google_fields_to_private_crm_row():
    place = {
        "id": "ChIJ123",
        "displayName": {"text": "Demo Snow"},
        "nationalPhoneNumber": "(514) 555-0101",
        "internationalPhoneNumber": "+1 514-555-0101",
        "formattedAddress": "1 Rue Demo, Montreal, QC",
        "shortFormattedAddress": "1 Rue Demo",
        "websiteUri": "https://example.com",
        "googleMapsUri": "https://maps.google.com/?cid=123",
        "rating": 4.7,
        "userRatingCount": 28,
        "primaryType": "general_contractor",
        "primaryTypeDisplayName": {"text": "General Contractor"},
        "businessStatus": "OPERATIONAL",
        "types": ["general_contractor", "point_of_interest"],
        "location": {"latitude": 45.5, "longitude": -73.6},
    }

    row = normalize_place(place, "snow removal contractor Montreal", "montreal_core")

    assert row["place_id"] == "ChIJ123"
    assert row["company_name"] == "Demo Snow"
    assert row["national_phone"] == "(514) 555-0101"
    assert row["sms_phone"] == "+15145550101"
    assert row["sms_sendable"] is True
    assert row["email"] == ""
    assert row["website"] == "https://example.com"
    assert row["latitude"] == 45.5
    assert row["notes"] == "Google Places does not return email directly"


def test_dedupe_places_merges_keywords_and_search_areas():
    rows = [
        {"place_id": "same", "company_name": "Demo", "address": "A", "keyword": "one", "search_area": "core"},
        {"place_id": "same", "company_name": "Demo", "address": "A", "keyword": "two", "search_area": "laval"},
    ]

    deduped = dedupe_places(rows)

    assert len(deduped) == 1
    assert deduped[0]["keyword"] == "one; two"
    assert deduped[0]["search_area"] == "core; laval"


def test_export_google_places_leads_writes_private_csv(tmp_path):
    output_path = tmp_path / "google_places" / "leads.csv"
    df = pd.DataFrame([{"company_name": "Demo Snow", "national_phone": "(514) 555-0101"}])

    export_google_places_leads(df, output_path)

    text = output_path.read_text(encoding="utf-8-sig")
    assert "Demo Snow" in text
    assert "(514) 555-0101" in text
