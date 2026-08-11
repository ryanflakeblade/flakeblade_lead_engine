from __future__ import annotations

from pathlib import Path

import pandas as pd

from ..config import PROJECT_ROOT


DEFAULT_GOOGLE_PLACES_OUTPUT = (
    PROJECT_ROOT / "data" / "crm_sources" / "google_places" / "greater_montreal_snow_contractors.csv"
)


def export_google_places_leads(df: pd.DataFrame, output_path: Path = DEFAULT_GOOGLE_PLACES_OUTPUT) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")

