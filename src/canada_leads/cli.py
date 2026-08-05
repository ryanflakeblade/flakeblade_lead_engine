from __future__ import annotations

import argparse

from .config import load_settings
from .export import export_companies
from .parser import DEFAULT_TERMS, collect_companies


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect Canada service company leads from Yelp.")
    parser.add_argument(
        "--terms",
        nargs="+",
        default=DEFAULT_TERMS,
        help="Search terms to collect.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = load_settings()
    companies = collect_companies(settings, terms=args.terms)
    export_companies(companies, settings.output_csv, settings.output_json)
    print(f"Exported {companies.shape[0]} companies")
    print(f"CSV: {settings.output_csv}")
    print(f"JSON: {settings.output_json}")


if __name__ == "__main__":
    main()

