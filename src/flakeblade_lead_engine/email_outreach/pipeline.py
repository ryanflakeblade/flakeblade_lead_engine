from __future__ import annotations

from pathlib import Path

import pandas as pd

from .client import EmailClient
from .templates import dealer_intro_email, dealer_intro_subject


SENT_STATUSES = {"sent", "dry_run"}


def _first_existing_column(df: pd.DataFrame, candidates: list[str]) -> str:
    for candidate in candidates:
        if candidate in df.columns:
            return candidate
    raise ValueError(f"Missing required CSV column. Expected one of: {', '.join(candidates)}")


def load_email_recipients(input_path: Path) -> pd.DataFrame:
    df = pd.read_csv(input_path, dtype=str, keep_default_na=False)
    email_column = _first_existing_column(df, ["email", "Email"])
    name_column = _first_existing_column(df, ["name", "Company Name", "company_name"])

    df = df.copy()
    df["email"] = df[email_column].fillna("").astype(str).str.strip()
    df["name"] = df[name_column].fillna("").astype(str).str.strip()
    if "contact_name" not in df.columns:
        df["contact_name"] = df["Contact Person"] if "Contact Person" in df.columns else ""
    if "email_status" not in df.columns:
        df["email_status"] = ""
    if "email_message_id" not in df.columns:
        df["email_message_id"] = ""
    if "email_error" not in df.columns:
        df["email_error"] = ""

    return df


def filter_email_recipients(df: pd.DataFrame, limit: int | None = None) -> pd.DataFrame:
    filtered = df.copy()
    filtered = filtered[~filtered["email_status"].fillna("").isin(SENT_STATUSES)]
    filtered = filtered[filtered["email"].fillna("").astype(str).str.contains("@", regex=False)]
    filtered = filtered.drop_duplicates(subset=["email"], keep="first")
    if limit:
        filtered = filtered.head(limit)
    return filtered


def _prepare_email_output(df: pd.DataFrame) -> pd.DataFrame:
    output = df.copy()
    if "Email" in output.columns and "email" in output.columns:
        output["Email"] = output["email"]
        output = output.drop(columns=["email"])
    if "Company Name" in output.columns and "name" in output.columns:
        output = output.drop(columns=["name"])
    return output


def send_email_campaign(
    input_path: Path,
    output_path: Path,
    client: EmailClient,
    limit: int | None = None,
) -> pd.DataFrame:
    df = load_email_recipients(input_path)
    recipients = filter_email_recipients(df, limit=limit)

    for index, row in recipients.iterrows():
        subject = dealer_intro_subject(str(row["name"]))
        body = dealer_intro_email(str(row["name"]), str(row.get("contact_name", "")))
        result = client.send_email(str(row["email"]), subject, body)
        df.at[index, "email_status"] = result.status
        df.at[index, "email_message_id"] = result.message_id
        df.at[index, "email_error"] = result.error
        if result.error:
            print(f"{result.status}: {row['name']} {row['email']} - {result.error}")
        else:
            print(f"{result.status}: {row['name']} {row['email']}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    _prepare_email_output(df).to_csv(output_path, index=False, encoding="utf-8-sig")
    return df
