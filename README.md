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
git clone https://github.com/c4ppuccino-monkey/IP-MAN-buff.git
cd IP-MAN-buff
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

Accounts are managed inside the app. You do not need to create or edit
`accounts.json` by hand.

1. Start the Streamlit app.
2. Open **Database Management** from the sidebar.
3. Add a display name and Dota account ID.
4. Use **Update match history** to fetch and ingest matches for the selected accounts.

The app creates and updates `accounts.json` automatically. The file is ignored by
Git because it is local user configuration.

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

- add or remove saved accounts
- update match history for one or more accounts
- fetch new match IDs from OpenDota
- load basic match details into the local database
- optionally load detailed parsed stats
- optionally request missing parsed data from OpenDota

The normal flow is to choose accounts, set a match limit, and click
**Update match history**. Advanced queue details are available in the page if you
want to inspect which matches still need basic or detailed data.

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
