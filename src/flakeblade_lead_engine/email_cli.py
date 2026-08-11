from __future__ import annotations

import argparse
from pathlib import Path

from .config import PROJECT_ROOT, load_email_settings
from .email_outreach.client import EmailClient
from .email_outreach.pipeline import filter_email_recipients, load_email_recipients, send_email_campaign


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Send or preview email outreach from a CRM CSV.")
    parser.add_argument(
        "--input",
        type=Path,
        default=PROJECT_ROOT / "data" / "crm_sources" / "rgcq" / "rgcq_leads.csv",
        help="Input CRM CSV with an email or Email column.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "data" / "processed" / "email_results.csv",
        help="Output CSV with email status columns.",
    )
    parser.add_argument("--limit", type=int, help="Maximum number of recipients to process.")
    parser.add_argument("--list", action="store_true", help="List email recipient count, then exit.")
    parser.add_argument("--send", action="store_true", help="Actually send email through SMTP.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.list:
        recipients = filter_email_recipients(load_email_recipients(args.input), limit=args.limit)
        print(f"Email recipients: {len(recipients)}")
        return

    settings = load_email_settings()
    client = EmailClient(settings, dry_run=not args.send)
    send_email_campaign(args.input, args.output, client, limit=args.limit)


if __name__ == "__main__":
    main()
