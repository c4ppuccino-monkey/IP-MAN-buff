"""Database ingestion orchestration helpers."""

import db_population as popul
import enrichment as en
from logging_config import get_logger
from opendota_client import fetch_json
import time


logger = get_logger(__name__)


def get_match_id(matches):
    """Extract match IDs from a match list payload."""
    matches_id = []
    for m in matches:
        match_id = m.get("match_id")
        matches_id.append(match_id)
    return matches_id


def check_match_id(cur):
    """Read already known match IDs from the local database."""
    rows = cur.execute("SELECT match_id FROM player_matches")
    results = set()

    for row in rows:
        results.add(row[0])

    return results


def new_ids(known_matches, all_matches_ids):
    """Return only match IDs that are not yet present in the database."""
    missing_ids = []

    for match_id in all_matches_ids:
        if match_id not in known_matches:
            missing_ids.append(match_id)

    return missing_ids


def unparsed_matches(cur):
    """Return match IDs that are missing unparsed-stage population."""
    cur.execute(
        """SELECT match_id FROM player_matches
                WHERE version IS NULL"""
    )
    unparsed = []
    for n in cur.fetchall():
        unparsed.append(n[0])
    return unparsed


def update_ver(cur, conn, matches, unparsed):
    """Update match version for rows selected as unparsed."""
    for m in matches:
        match_id = m.get("match_id")
        if match_id in unparsed:
            ver = m.get("version")
            cur.execute(
                """UPDATE player_matches
                        SET version = ?
                        WHERE match_id = ?
                        """,
                (ver, match_id),
            )
    conn.commit()


def select_matches(cur, limit=100, unparsed_pop=None, 
                   parsed_pop=None, version=None):
    """Select match IDs that still require parsed-stage ingestion.
    
    args:
        cur: database cursor
        limit: max number of match IDs to return
        unparsed_pop: If the unparsed population has been done or not,
        parsed_pop: If the parse population has been done or not,
        version: If the match is parsed or not  """

    query = """SELECT match_id
        FROM player_matches
        WHERE 1=1
    """
    params = []

    if unparsed_pop is not None:
        query += " AND unparsed_pop = ?"
        params.append(unparsed_pop)

    if parsed_pop is not None:
        query += " AND parsed_pop = ?"
        params.append(parsed_pop)

    if version is not None:
        if version == "null":
            query += " AND version IS NULL"
        else:
            query += " AND version = ?"
            params.append(version)
        
    query += " ORDER BY match_id DESC LIMIT ?"
    params.append(limit)

    cur.execute(query, params)

    selected = []
    for n in cur.fetchall():
        selected.append(n[0])

    return selected


def main_pop(cur, conn, matches_ids, unparsed_pop,
             heroes_map, abilities_map):
    
    """Drive unparsed+parsed ingestion for all requested match IDs."""

    total_matches = len(matches_ids)
    print(f"A total of {total_matches} matches will be processed")

    for match_id in matches_ids:
        try:
            url = f"https://api.opendota.com/api/matches/{match_id}"
            r = fetch_json(url)

            parsed = r.get("od_data", {}).get("has_parsed")
            players = r.get("players", [])

            for p in players:
                # get_hero_name returns (hero_localized_name, hero_name) and also
                # writes both values into p[...] for DB insertion; "_" only means
                # we do not need a local hero_localized_name variable in this scope.
                _, hero_name = en.get_hero_name(p, heroes_map)
                p["facet_name"] = en.get_facet_name(p, abilities_map, hero_name)

            if parsed and unparsed_pop in (0, None):
                popul.pop_unparsed(r, match_id, cur, conn)
                popul.pop_all_parsed(r, match_id, cur, conn)
                logger.info("Populated unparsed+parsed rows. match_id=%s", match_id)
            
            elif parsed and unparsed_pop == 1:
                popul.pop_all_parsed(r, match_id, cur, conn)
                logger.info("Populated parsed rows only. match_id=%s", match_id)

            elif not parsed and unparsed_pop == 1:
                continue

            else:
                popul.pop_unparsed(r, match_id, cur, conn)
                logger.info("Populated unparsed rows only. match_id=%s", match_id)
                
        except Exception:
            conn.rollback()
            logger.exception("Failed to ingest match payload. match_id=%s", match_id)

        total_matches -= 1
        print(f"\nMatches remaining: {total_matches}\n")

        time.sleep(1)  # Limiting api calls to 60 per minute

    
