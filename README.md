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
