from __future__ import annotations

from pathlib import Path

import pandas as pd

from .client import SmsClient
from .templates import dealer_intro_message


SENT_STATUSES = {"sent", "dry_run"}


def load_recipients(input_path: Path) -> pd.DataFrame:
    df = pd.read_csv(input_path, dtype={"phone": str}, keep_default_na=False)
    required = {"name", "phone"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required CSV columns: {', '.join(sorted(missing))}")

    if "sms_status" not in df.columns:
        df["sms_status"] = ""
    if "sms_message_sid" not in df.columns:
        df["sms_message_sid"] = ""
    if "sms_error" not in df.columns:
        df["sms_error"] = ""
    return df


def filter_recipients(
    df: pd.DataFrame,
    region: str | None = None,
    service: str | None = None,
    limit: int | None = None,
) -> pd.DataFrame:
    filtered = df.copy()
    filtered = filtered[~filtered["sms_status"].fillna("").isin(SENT_STATUSES)]
    filtered = filtered[filtered["phone"].fillna("").astype(str).str.startswith("+")]

    if region:
        filtered = filtered[filtered["search_region"].fillna("").str.lower() == region.lower()]
    if service:
        filtered = filtered[filtered["search_term"].fillna("").str.lower() == service.lower()]
    if limit:
        filtered = filtered.head(limit)
    return filtered


def summarize_regions(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for region, group in df.groupby("search_region", dropna=False):
        sendable = filter_recipients(group)
        service_counts = group["search_term"].fillna("").value_counts().to_dict()
        rows.append(
            {
                "region": region or "<blank>",
                "total": int(len(group)),
                "sendable": int(len(sendable)),
                "services": ", ".join(
                    f"{service}: {count}" for service, count in sorted(service_counts.items())
                ),
            }
        )
    return pd.DataFrame(rows).sort_values(["sendable", "total"], ascending=[False, False])


def send_campaign(
    input_path: Path,
    output_path: Path,
    client: SmsClient,
    region: str | None = None,
    service: str | None = None,
    limit: int | None = None,
) -> pd.DataFrame:
    df = load_recipients(input_path)
    recipients = filter_recipients(df, region=region, service=service, limit=limit)

    for index, row in recipients.iterrows():
        result = client.send_sms(str(row["phone"]), dealer_intro_message(str(row["name"])))
        df.at[index, "sms_status"] = result.status
        df.at[index, "sms_message_sid"] = result.message_sid
        df.at[index, "sms_error"] = result.error
        if result.error:
            print(f"{result.status}: {row['name']} {row['phone']} - {result.error}")
        else:
            print(f"{result.status}: {row['name']} {row['phone']}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    return df
