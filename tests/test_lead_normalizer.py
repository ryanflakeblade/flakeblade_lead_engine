import pandas as pd

from flakeblade_lead_engine.leads.normalizer import (
    CRM_COLUMNS,
    combine_crm_companies,
    normalize_google_places,
    normalize_yelp_companies,
)
from flakeblade_lead_engine.sms.pipeline import filter_recipients, load_recipients


def test_normalize_google_places_outputs_sms_compatible_columns():
    google = pd.DataFrame(
        [
            {
                "place_id": "g1",
                "company_name": "Demo Snow",
                "keyword": "snow removal contractor Montreal",
                "search_area": "montreal_core",
                "national_phone": "(514) 555-0101",
                "international_phone": "+1 514-555-0101",
                "sms_phone": "+15145550101",
                "website": "https://example.com",
                "google_maps_url": "https://maps.example/g1",
                "rating": "4.9",
                "review_count": "12",
                "types": "service",
                "business_status": "OPERATIONAL",
            }
        ]
    )

    normalized = normalize_google_places(google)

    assert normalized.columns.tolist() == CRM_COLUMNS
    assert normalized.loc[0, "source"] == "Google Places"
    assert normalized.loc[0, "name"] == "Demo Snow"
    assert normalized.loc[0, "phone"] == "+15145550101"
    assert normalized.loc[0, "search_region"] == "Greater Montreal"
    assert normalized.loc[0, "search_city"] == "montreal_core"


def test_normalize_yelp_outputs_sms_compatible_columns():
    yelp = pd.DataFrame(
        [
            {
                "id": "y1",
                "name": "Yelp Snow",
                "search_term": "Snow removal",
                "search_region": "Ottawa",
                "search_city": "Ottawa",
                "phone": "+1 613-555-0101",
                "display_phone": "+1 613-555-0101",
                "url": "https://yelp.example/y1",
            }
        ]
    )

    normalized = normalize_yelp_companies(yelp)

    assert normalized.loc[0, "source"] == "Yelp"
    assert normalized.loc[0, "source_id"] == "y1"
    assert normalized.loc[0, "phone"] == "+16135550101"
    assert normalized.loc[0, "source_url"] == "https://yelp.example/y1"


def test_combined_crm_companies_can_feed_sms_pipeline(tmp_path):
    google = normalize_google_places(
        pd.DataFrame(
            [
                {
                    "place_id": "g1",
                    "company_name": "Demo Snow",
                    "keyword": "Snow removal",
                    "search_area": "montreal_core",
                    "sms_phone": "+15145550101",
                }
            ]
        )
    )
    yelp = normalize_yelp_companies(
        pd.DataFrame(
            [
                {
                    "id": "y1",
                    "name": "Yelp Snow",
                    "search_term": "Snow removal",
                    "search_region": "Ottawa",
                    "search_city": "Ottawa",
                    "phone": "+16135550101",
                }
            ]
        )
    )
    combined = combine_crm_companies([google, yelp])
    input_path = tmp_path / "crm_companies.csv"
    combined.to_csv(input_path, index=False)

    recipients = load_recipients(input_path)
    sendable = filter_recipients(recipients)

    assert {"name", "phone", "search_region", "search_term"}.issubset(combined.columns)
    assert sendable["name"].tolist() == ["Demo Snow", "Yelp Snow"]

