from __future__ import annotations

import argparse
from pathlib import Path

from .leads.normalizer import (
    DEFAULT_CRM_COMPANIES_PATH,
    DEFAULT_GOOGLE_PLACES_OUTPUT,
    DEFAULT_YELP_COMPANIES_PATH,
    build_crm_companies,
    export_crm_companies,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a unified private CRM companies CSV.")
    parser.add_argument("--yelp-input", type=Path, default=DEFAULT_YELP_COMPANIES_PATH)
    parser.add_argument("--google-places-input", type=Path, default=DEFAULT_GOOGLE_PLACES_OUTPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_CRM_COMPANIES_PATH)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    companies = build_crm_companies(args.yelp_input, args.google_places_input)
    export_crm_companies(companies, args.output)

    sendable = int(companies["phone"].fillna("").astype(str).str.startswith("+").sum())
    print(f"Exported {companies.shape[0]} unified CRM companies")
    print(f"SMS-sendable rows: {sendable}")
    print(f"CSV: {args.output}")


if __name__ == "__main__":
    main()

