from __future__ import annotations

import argparse
from pathlib import Path

from .config import PROJECT_ROOT, load_sms_settings
from .sms.client import SmsClient
from .sms.pipeline import load_recipients, send_campaign, summarize_regions


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Send or preview SMS outreach from companies.csv.")
    parser.add_argument(
        "--input",
        nargs="+",
        type=Path,
        default=[PROJECT_ROOT / "data" / "processed" / "companies.csv"],
        help="Input companies CSV file(s). Multiple files are combined and deduped by phone.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "data" / "processed" / "sms_results.csv",
        help="Output CSV with SMS status columns.",
    )
    parser.add_argument("--region", help="Optional search_region filter, e.g. Ottawa.")
    parser.add_argument("--service", help='Optional search_term filter, e.g. "Snow removal".')
    parser.add_argument("--limit", type=int, help="Maximum number of recipients to process.")
    parser.add_argument(
        "--list-regions",
        action="store_true",
        help="List available regions and sendable recipient counts, then exit.",
    )
    parser.add_argument(
        "--send",
        action="store_true",
        help="Actually send SMS through Twilio. Omit this for dry-run mode.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.list_regions:
        recipients = load_recipients(args.input)
        summary = summarize_regions(recipients)
        print(summary.to_string(index=False))
        return

    settings = load_sms_settings()
    client = SmsClient(settings, dry_run=not args.send)
    send_campaign(
        input_path=args.input,
        output_path=args.output,
        client=client,
        region=args.region,
        service=args.service,
        limit=args.limit,
    )


if __name__ == "__main__":
    main()
