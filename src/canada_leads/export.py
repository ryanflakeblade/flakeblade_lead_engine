from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd


SERVICE_LABELS = {
    "lawn mowing": "lawn_mowing",
    "snow removal": "snow_removal",
}


def _service_key(search_term: object) -> str:
    value = str(search_term).strip().lower()
    return SERVICE_LABELS.get(value, value.replace(" ", "_"))


def _service_summary(group: pd.DataFrame) -> dict:
    counts = {
        _service_key(service): int(len(service_group))
        for service, service_group in group.groupby("search_term", dropna=False)
    }
    service_keys = sorted(counts)
    if {"lawn_mowing", "snow_removal"}.issubset(service_keys):
        service_status = "both"
    elif service_keys:
        service_status = service_keys[0]
    else:
        service_status = "none"

    return {
        "service_status": service_status,
        "services": service_keys,
        "service_counts": counts,
    }


def build_public_summary(df: pd.DataFrame) -> dict:
    if df.empty:
        return {
            "updated_at": datetime.now(UTC).date().isoformat(),
            "totals": {"companies": 0, "cities": 0},
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
                "latitude": float(group["latitude"].dropna().mean()) if group["latitude"].notna().any() else None,
                "longitude": float(group["longitude"].dropna().mean()) if group["longitude"].notna().any() else None,
                **_service_summary(group),
            }
        )

    region_group = df.groupby("search_region", dropna=False)
    regions = [
        {
            "region": region,
            "companies": int(len(group)),
            **_service_summary(group),
        }
        for region, group in region_group
    ]

    service_group = df.groupby("search_term", dropna=False)
    services = [
        {
            "service": _service_key(service),
            "label": service,
            "companies": int(len(group)),
        }
        for service, group in service_group
    ]

    return {
        "updated_at": datetime.now(UTC).date().isoformat(),
        "totals": {
            "companies": int(len(df)),
            "cities": int(df["search_city"].nunique()),
            **_service_summary(df),
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
