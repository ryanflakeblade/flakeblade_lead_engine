# Canada Leads

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
python -m canada_leads.cli
```

Outputs:

```text
data/processed/companies.csv
data/public/canada_leads.json
```

`data/public/canada_leads.json` is the file your WordPress site can read.

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

## Notes

- Do not commit `.env`.
- The Yelp API key is read from environment variables or `.env`.
- Raw and processed data folders are ignored by Git by default.
- `data/public/canada_leads.json` can be committed if you want GitHub to host it.
