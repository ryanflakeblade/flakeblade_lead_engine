import json

import pandas as pd

from canada_leads.export import build_public_summary, export_companies
from canada_leads.config import Settings
from canada_leads.parser import collect_companies
from canada_leads.phone import to_e164


def test_build_public_summary_counts_companies_and_marks_services_without_phone():
    df = pd.DataFrame(
        [
            {"search_region": "Toronto", "search_city": "Toronto", "search_term": "Snow removal", "phone": "111", "latitude": 43.1, "longitude": -79.1},
            {"search_region": "Toronto", "search_city": "Toronto", "search_term": "Lawn Mowing", "phone": "", "latitude": 43.1, "longitude": -79.1},
            {"search_region": "Vancouver", "search_city": "Vancouver", "search_term": "Snow removal", "phone": "222", "latitude": 49.2, "longitude": -123.1},
        ]
    )

    summary = build_public_summary(df)

    assert summary["totals"]["companies"] == 3
    assert summary["totals"]["cities"] == 2
    assert summary["totals"]["service_status"] == "both"
    assert summary["totals"]["services"] == ["lawn_mowing", "snow_removal"]
    assert summary["totals"]["service_counts"] == {"lawn_mowing": 1, "snow_removal": 2}
    assert summary["cities"][0]["service_status"] == "both"
    assert "phone" not in json.dumps(summary).lower()


def test_export_companies_writes_private_csv_and_public_json(tmp_path):
    df = pd.DataFrame(
        [
            {
                "search_region": "Toronto",
                "search_city": "Toronto",
                "search_term": "Snow removal",
                "phone": "+14165550101",
                "display_phone": "+1 416-555-0101",
                "latitude": 43.1,
                "longitude": -79.1,
            },
            {
                "search_region": "Toronto",
                "search_city": "Toronto",
                "search_term": "Lawn Mowing",
                "phone": "+14165550102",
                "display_phone": "+1 416-555-0102",
                "latitude": 43.1,
                "longitude": -79.1,
            },
        ]
    )

    csv_path = tmp_path / "processed" / "companies.csv"
    json_path = tmp_path / "public" / "canada_leads.json"

    export_companies(df, csv_path, json_path)

    csv_text = csv_path.read_text(encoding="utf-8")
    json_text = json_path.read_text(encoding="utf-8")
    data = json.loads(json_text)

    assert "+14165550101" in csv_text
    assert "display_phone" in csv_text
    assert "phone" not in json_text.lower()
    assert data["totals"]["service_status"] == "both"
    assert data["totals"]["services"] == ["lawn_mowing", "snow_removal"]


def test_collect_companies_filters_non_canadian_businesses(monkeypatch):
    def fake_search_by_service(term, settings):
        return pd.DataFrame(
            [
                {"name": "Canadian Co", "country": "CA", "phone": "111", "review_count": 5},
                {"name": "US Co", "country": "US", "phone": "222", "review_count": 10},
            ]
        )

    monkeypatch.setattr("canada_leads.parser.search_by_service", fake_search_by_service)

    settings = Settings(yelp_api_key="test")
    companies = collect_companies(settings, terms=["Snow removal"])

    assert companies["country"].tolist() == ["CA"]
    assert companies["name"].tolist() == ["Canadian Co"]


def test_to_e164_normalizes_yelp_phone_formats():
    assert to_e164("+1 647-576-2688") == "+16475762688"
    assert to_e164("(315) 212-3143") == "+13152123143"
    assert to_e164("") == ""
