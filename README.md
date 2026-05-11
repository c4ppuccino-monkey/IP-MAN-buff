# Dota Match Dashboard

This is a small Python app for collecting Dota 2 match data from OpenDota, saving it into a local SQLite database, and viewing simple stats in a Streamlit dashboard.

## Accounts
You can add ypur steam account name and ID in the accounts JSON

## Database population

`main.py` is the command-line entry point for the app.

When it starts, it:

1. Syncs the local OpenDota constants repo.
2. Loads maps for heroes, abilities, items, buffs, objectives, and other OpenDota lookup data.
3. Opens or creates the local SQLite database.
4. Loads saved Dota account IDs from `accounts.json`.
5. Fetches match history for each saved account.
6. Adds new match IDs and account-match rows to the database.
7. Opens a small CLI menu for ingestion and parsing.

Run it with:

```bash
python main.py
```

## Database

The database is created automatically by `db_tables.create_database()`.

It creates this folder and file:

```text
data_base/database.db
```

The API calls happen on multiple levels:
- Collect all of the player/s' matches with some general match info
- For each match you run a second API call to collect that matches data
- For each match data, there is basic players' stats, and there are supplementery (advanced) stats that can be acquired after requesting the match to be parsed through the API.
- On each ingestion cycle, the program will populate the available data Basic stats and advanced stats (if available)

The schema stores:

- basic match rows in `player_matches`
- account-specific match rows in `account_matches`
- player stats in `players_stats`
- parsed match details like team fights, objectives, damage, purchases, wards, runes, timings, benchmarks, and ability upgrades
- OpenDota constants such as gold, XP, and rune reasons

The app uses two flags on each match:

- `unparsed_pop`: whether the basic match/player data has been populated
- `parsed_pop`: whether detailed (advanced) parsed data has been populated

These flags help the app know which matches still need more ingestion work.


### Ingest New Matches

This option loads match details from OpenDota and writes them into the database.

The prompts let you choose:

- how many matches to process
- a specific OpenDota version (a null version means the match is unparsed, thats why (no opendota version)
- whether to include matches where basic data is already populated
- whether to include matches where parsed data is already populated

Leaving a filter blank means "ignore this filter".


### Parse Matches

This option asks OpenDota to parse matches that do not have detailed data yet.

It uses the same filtering style:

- match limit
- version filter
- `unparsed_pop` filter
- `parsed_pop` filter

The app waits between requests to avoid hitting the API too quickly.

## Dashboard

The Streamlit dashboard reads from the same SQLite database.

Run it with:

```bash
streamlit run streamlit/dashboard.py
```

The main dashboard lets you:

- choose one saved account
- compare multiple accounts
- filter by result, match count, parse status, hero, peer account, item, and item order
- view overview stats like analyzed matches, win rate, match dates, average duration, and most played hero
- view farming stats like GPM, XPM, net worth, last hits, and denies
- view combat stats like KDA, kills, deaths, assists, hero damage, and tower damage
- view benchmark percentiles when parsed benchmark data is available
- see charts for hero distribution, rolling win rate, farming over time, KDA over time, and damage vs net worth

There is also a database management page:

```bash
streamlit run streamlit/pages/1_db_management.py
```

That page lets you add/remove saved accounts, update match history, load basic details, load detailed stats, request missing OpenDota parses, and preview ingestion queue counts.
