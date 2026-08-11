# Flakeblade Lead Engine

Collect Canadian lawn mowing and snow removal companies from Yelp, dedupe them,
and export files that can be consumed by WordPress.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` and set:

```text
YELP_API_KEY=your_yelp_api_key
GOOGLE_MAPS_API_KEY=your_google_maps_api_key
SMTP_HOST=your_smtp_host
SMTP_PORT=587
SMTP_USERNAME=your_smtp_username
SMTP_PASSWORD=your_smtp_password
SMTP_FROM_EMAIL=your_from_email
```

## Run

```powershell
python -m flakeblade_lead_engine.cli
```

Outputs:

```text
data/processed/companies.csv
data/public/canada_leads.json
```

`data/public/canada_leads.json` is the file your WordPress site can read.

## Google Places CRM Source

Google Places exports are private CRM source data. They are written under:

```text
data/crm_sources/google_places/
```

Run the Greater Montreal snow contractor search:

```powershell
.\.venv\Scripts\python.exe -m flakeblade_lead_engine.google_places_cli
```

Default output:

```text
data/crm_sources/google_places/greater_montreal_snow_contractors.csv
```

The export includes phone, website, address, Google Maps URL, rating, search
keyword, search area, and SMS readiness fields:

```text
sms_phone
sms_sendable
```

`sms_phone` is normalized to E.164 format for the SMS pipeline, such as
`+15145926615`. After export, the CLI prints counts for total leads, leads with
any phone number, SMS-ready phone numbers, and missing/invalid SMS numbers.

Google Places does not return email directly, so the email column is left empty
for a later website/contact-page enrichment step. `sms_sendable` means the phone
number has a valid SMS format; it does not confirm mobile carrier status or
marketing opt-in.

## Unified CRM Companies

Yelp and Google Places exports can be normalized into one SMS-compatible CRM
file:

```powershell
.\.venv\Scripts\python.exe -m flakeblade_lead_engine.crm_cli
```

Output:

```text
data/processed/crm_companies.csv
```

This file keeps source-specific fields normalized into shared columns like
`source`, `source_id`, `name`, `search_term`, `search_region`, `phone`,
`display_phone`, `website`, `source_url`, `categories`, `priority`, and
`next_action`.

Use it with the SMS preview pipeline:

```powershell
.\.venv\Scripts\python.exe -m flakeblade_lead_engine.sms_cli --input data/processed/crm_companies.csv --list-regions
.\.venv\Scripts\python.exe -m flakeblade_lead_engine.sms_cli --input data/processed/crm_companies.csv --region "Greater Montreal" --limit 10
```

### Run SMS Across Yelp + Google Places

Recommended workflow:

```powershell
# 1. Generate or refresh Yelp leads.
.\.venv\Scripts\python.exe -m flakeblade_lead_engine.cli

# 2. Generate or refresh Google Places leads.
.\.venv\Scripts\python.exe -m flakeblade_lead_engine.google_places_cli

# 3. Build one normalized CRM file from both sources.
.\.venv\Scripts\python.exe -m flakeblade_lead_engine.crm_cli

# 4. Preview available regions and sendable counts.
.\.venv\Scripts\python.exe -m flakeblade_lead_engine.sms_cli --input data/processed/crm_companies.csv --list-regions

# 5. Dry-run a small batch before sending.
.\.venv\Scripts\python.exe -m flakeblade_lead_engine.sms_cli --input data/processed/crm_companies.csv --region "Greater Montreal" --limit 10
```

Only add `--send` after reviewing the SMS template and dry-run output:

```powershell
.\.venv\Scripts\python.exe -m flakeblade_lead_engine.sms_cli --input data/processed/crm_companies.csv --region "Greater Montreal" --limit 10 --send
```

`sms_cli` can also read Yelp and Google Places CSV files directly. It combines
them, normalizes phone numbers to E.164, and dedupes by phone before previewing
or sending, so the same phone number is contacted only once:

```powershell
.\.venv\Scripts\python.exe -m flakeblade_lead_engine.sms_cli --input data/processed/companies.csv data/crm_sources/google_places/greater_montreal_snow_contractors.csv --list-regions
```

The unified `crm_companies.csv` path is safer for regular outreach because it
maps source-specific columns into the shared SMS columns `name`, `phone`,
`search_region`, and `search_term`.

Generate a public SVG coverage image from the JSON:

```powershell
.\.venv\Scripts\python.exe scripts\generate_coverage_image.py
```

Output:

```text
data/public/canada_leads_coverage.svg
```

## Tests

Install development dependencies:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

Run tests manually:

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
```

Install the local pre-commit hook:

```powershell
.\.venv\Scripts\python.exe -m pre_commit install
```

After that, every `git commit` runs the test suite first. GitHub Actions also
runs the tests on push and pull request.

## SMS Outreach

The SMS step reads:

```text
data/processed/companies.csv
```

and writes:

```text
data/processed/sms_results.csv
```

The default mode is a dry run. It does not contact Twilio and does not send
real messages unless `--send` is provided.

List available regions before choosing a target:

```powershell
python -m flakeblade_lead_engine.sms_cli --list-regions
```

The output shows each region's total rows, sendable recipients, and service
breakdown.

### 1. Update Message Template

Edit the SMS copy in:

```text
src/flakeblade_lead_engine/sms/templates.py
```

The current campaign uses:

```python
dealer_intro_message(company_name)
```

Update this function before sending a real campaign.

### 2. Preview Without Sending

```powershell
python -m flakeblade_lead_engine.sms_cli --region Ottawa --limit 10
```

Check:

```text
data/processed/sms_results.csv
```

Rows processed in preview mode will be marked:

```text
sms_status=dry_run
```

### 3. Send Real SMS

Only add `--send` after reviewing the template and dry-run output:

```powershell
python -m flakeblade_lead_engine.sms_cli --region Ottawa --limit 10 --send
```

Rows sent through Twilio will be marked:

```text
sms_status=sent
sms_message_sid=<Twilio message id>
```

Required `.env` values for real sending:

```text
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_FROM_NUMBER=
```

Useful filters:

```powershell
python -m flakeblade_lead_engine.sms_cli --region Ottawa --service "Snow removal" --limit 50
```

Use `--send` with the same filters when ready to send.

## Email Outreach

The email step reads a CRM CSV with an `email` or `Email` column. It is useful
for private source files such as:

```text
data/crm_sources/rgcq/rgcq_leads.csv
```

and writes:

```text
data/processed/email_results.csv
```

The default mode is a dry run. It does not connect to SMTP and does not send
real email unless `--send` is provided.

List available email recipients from the default RGCQ file:

```powershell
python -m flakeblade_lead_engine.email_cli --list
```

Dry-run the first 10 RGCQ email recipients:

```powershell
python -m flakeblade_lead_engine.email_cli --limit 10
```

Rows processed in preview mode will be marked:

```text
email_status=dry_run
```

Required `.env` values for real sending:

```text
SMTP_HOST=
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_FROM_EMAIL=
```

Only add `--send` after reviewing the email template and dry-run output:

```powershell
python -m flakeblade_lead_engine.email_cli --limit 10 --send
```

Use another CRM file:

```powershell
python -m flakeblade_lead_engine.email_cli --input data/crm_sources/rgcq/rgcq_leads.csv --limit 10
```

Edit the email copy in:

```text
src/flakeblade_lead_engine/email_outreach/templates.py
```

### Manual Recipient List

For a small hand-picked list, create:

```text
data/manual/special_recipients.csv
```

Use this format:

```csv
name,phone
Test Contact,+14165550101
Demo Contact,+16135550102
```

There is a safe example file at:

```text
data/manual/special_recipients.example.csv
```

Real manual recipient CSV files are ignored by Git by default.

Dry-run the manual list:

```powershell
python -m flakeblade_lead_engine.sms_cli --input data/manual/special_recipients.csv
```

Send to the manual list:

```powershell
python -m flakeblade_lead_engine.sms_cli --input data/manual/special_recipients.csv --send
```

## Notes

- Do not commit `.env`.
- The Yelp API key is read from environment variables or `.env`.
- Raw and processed data folders are ignored by Git by default.
- `data/public/canada_leads.json` can be committed if you want GitHub to host it.
