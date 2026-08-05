from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd


def _with_phone(series: pd.Series) -> int:
    return int(series.fillna("").astype(str).str.strip().ne("").sum())


def build_public_summary(df: pd.DataFrame) -> dict:
    if df.empty:
        return {
            "updated_at": datetime.now(UTC).date().isoformat(),
            "totals": {"companies": 0, "cities": 0, "with_phone": 0},
            "regions": [],
            "cities": [],
            "services": [],
        }

    city_group = df.groupby(["search_region", "search_city"], dropna=False)
    cities = []
    for (region, city), group in city_group:
        cities.append(
            {
                "region": region,
                "city": city,
                "companies": int(len(group)),
                "with_phone": _with_phone(group["phone"]),
                "latitude": float(group["latitude"].dropna().mean()) if group["latitude"].notna().any() else None,
                "longitude": float(group["longitude"].dropna().mean()) if group["longitude"].notna().any() else None,
            }
        )

    region_group = df.groupby("search_region", dropna=False)
    regions = [
        {
            "region": region,
            "companies": int(len(group)),
            "with_phone": _with_phone(group["phone"]),
        }
        for region, group in region_group
    ]

    service_group = df.groupby("search_term", dropna=False)
    services = [
        {
            "service": service,
            "companies": int(len(group)),
            "with_phone": _with_phone(group["phone"]),
        }
        for service, group in service_group
    ]

    return {
        "updated_at": datetime.now(UTC).date().isoformat(),
        "totals": {
            "companies": int(len(df)),
            "cities": int(df["search_city"].nunique()),
            "with_phone": _with_phone(df["phone"]),
        },
        "regions": sorted(regions, key=lambda item: item["companies"], reverse=True),
        "cities": sorted(cities, key=lambda item: item["companies"], reverse=True),
        "services": sorted(services, key=lambda item: item["companies"], reverse=True),
    }


def export_companies(df: pd.DataFrame, csv_path: Path, json_path: Path) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(csv_path, index=False)

    summary = build_public_summary(df)
    json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

