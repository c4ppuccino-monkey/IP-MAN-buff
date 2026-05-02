# Dota Dashboard

A local Streamlit app for collecting and analyzing Dota 2 match data from the OpenDota API.

The app stores match data in a local SQLite database, lets you manage saved accounts, fetch recent matches, request OpenDota parsing, ingest match details, and view dashboard-style player/account statistics.

## Features

- Save Dota account IDs locally
- Fetch recent matches for saved accounts
- Store match metadata in SQLite
- Request match parsing from OpenDota
- Ingest parsed and unparsed match details
- View account dashboards and comparison charts
- Inspect individual matches

## Requirements

- Python 3.10+
- Git
- Internet access for OpenDota API requests

## Installation

Clone this repository:

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
cd YOUR_REPO_NAME
```

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

On Windows:

```bash
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Account Setup

Create a local `accounts.json` file in the project root:

```json
{
    "accounts": [
        {
            "name": "example_player",
            "id": "123456789"
        }
    ]
}
```

Replace the example values with your own Dota account IDs.

`accounts.json` is ignored by Git because it is local user configuration.

## Running The App

Start the Streamlit dashboard:

```bash
streamlit run dashboard.py
```

The app uses a local SQLite database at:

```text
data_base/database.db
```

The database is created automatically when needed.

## Database Management

Use the database management page to:

- add accounts of interest
- fetch new match IDs for saved accounts
- request parsing from OpenDota
- ingest selected matches into the local database

OpenDota has API limits, so large parsing or ingestion runs should be done gradually.

## External Data

This project uses the public OpenDota API.

It also clones the OpenDota `dotaconstants` repository locally to load Dota constants such as heroes, items, abilities, and other metadata.

That cloned repository is not part of this project and is ignored by Git:

```text
dotaconstants/
```

This app may clone or update `dotaconstants` locally, but this project does not modify or push to that repository.

## Local Files Not Committed

The following are intentionally ignored:

- `accounts.json`
- `data_base/*.db`
- `logs/*.log`
- `dotaconstants/`
- `.venv/`
- `.streamlit/secrets.toml`

This keeps private config, local databases, generated logs, virtual environments, and external cloned repositories out of your GitHub repo.

## Project Structure

```text
.
├── dashboard.py
├── pages/
│   ├── 1_db_management.py
│   └── 2_matches.py
├── db_tables.py
├── db_population.py
├── ingestion.py
├── opendota_client.py
├── queries.py
├── accounts_management.py
├── app_functions.py
├── comparison_charts.py
├── maps.py
├── enrichment.py
├── logging_config.py
├── requirements.txt
└── README.md
```

## Notes

The app is designed for local analysis. The SQLite database and account list are local runtime files, not shared project files.
