import pandas as pd

from canada_leads.export import build_public_summary


def test_build_public_summary_counts_companies_and_phone_numbers():
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
    assert summary["totals"]["with_phone"] == 2

