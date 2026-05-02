import requests
import time
import subprocess
from pathlib import Path
import db_population as popul


# fetching all matches
def fetch_matches(account_id):
    url = f"https://api.opendota.com/api/players/{account_id}/matches"
    all_matches = fetch_json(url)
    print(f"A total number of {len(all_matches)} was retrieved")
    return all_matches


# matching hero id to hero name and appending them to the list of matches lists
def get_hero_name(p, heroes_map):
    id = p.get("hero_id")
    hero_localized_name = None
    hero_name = None
    for item, value in heroes_map.items():
        if value.get("id") == id:
            hero_localized_name = value.get("localized_name")
            hero_name = value.get("name")
            break

    p["hero_localized_name"] = hero_localized_name
    p["hero_name"] = hero_name
    return hero_localized_name, hero_name 


# matching facet name
def get_facet_name(p, abilities_map, hero_name):
    variant = p.get("hero_variant")
    if not variant:
        return None
    facet_id = variant - 1
    hero_data = abilities_map.get(hero_name, {})
    facets = hero_data.get('facets', [])

    for facet in facets:
        if facet.get('id') == facet_id:
            return facet.get('name')


# matching item names
def get_item_name(p, items_map):
    slots = [
        p.get('item_0', None),
        p.get('item_1', None), 
        p.get('item_2', None), 
        p.get('item_3', None), 
        p.get('item_4', None), 
        p.get('item_5', None),
        p.get('backpack_0', None), 
        p.get('backpack_1', None), 
        p.get('backpack_2', None),
        p.get('item_neutral', None),
        p.get('item_neutral2', None)
    ]
    names = []
    for slot in slots:
        if not slot:
            names.append(None)
        else:
            names.append(items_map.get(str(slot), None))

    return names


# extracting matches' ids
def get_match_id(matches):
    matches_id = []
    for m in matches:
        id = m.get('match_id')
        matches_id.append(id)
    return matches_id


# fetching urls with error handling
def fetch_json(url, delay=1, retries=3):
    for attempt in range(retries):
        resp = requests.get(url)
        if resp.status_code == 200:
            return resp.json()
        time.sleep(delay)
    raise RuntimeError(f"failed to fetch {url}, status {resp.status_code}")


# fetching previously populated matches ids to a set
def check_match_id(cur):
    rows = cur.execute('SELECT match_id FROM player_matches')
    results = set()

    for row in rows:
        results.add(row[0])
    
    return results


# new ids
def new_ids(known_matches, all_matches_ids):
    new_ids = []

    for id in all_matches_ids:
        if id not in known_matches:
            new_ids.append(id)
    
    return new_ids


# parsing matches request 
def parse_request(id):
    req = requests.post(f'https://api.opendota.com/api/request/{id}')
    time.sleep(6)


# selecting unparsed matches ID 
def unparsed_matches(cur):
    cur.execute('''SELECT match_id FROM player_matches
                WHERE version IS NULL''')
    unparsed = []
    for n in cur.fetchall():
        unparsed.append(n[0])
    return unparsed


# updating parsing status
def update_ver(cur, conn, matches, unparsed):
    for m in matches:
        id = m.get("match_id")
        if id in unparsed:
            ver = m.get('version')
            cur.execute('''UPDATE player_matches
                        SET version = ?
                        WHERE match_id = ?
                        ''', (ver, id))
    conn.commit()


# downloading/updating the dotaconstants repo
def sync_repo():
    path = Path("dotaconstants")

    if not (path / ".git").exists():
        subprocess.run(["git", "clone", 
                        "https://github.com/odota/dotaconstants.git"], 
                       check=True)
    else:
        subprocess.run(["git", "pull"], cwd=path, check=True)


''' 
selecting latest 20 matches from the matches table,
which were never populated before 
'''


def select_matches(cur):

    cur.execute('''
        SELECT match_id
        FROM player_matches
        WHERE parsed_pop = 0
        ORDER BY match_id DESC
        LIMIT 100
	''')
    
    select_matches = []

    for n in cur.fetchall():
        select_matches.append(n[0])
    return select_matches


# Populating the whole database with new matches, 
# which were never parsed before, 
# and updating the parsing status of the matches, 
# which were already parsed before but never populated before.
def main_pop(cur, conn, matches_ids):
    for id in matches_ids:
        url = f"https://api.opendota.com/api/matches/{id}"
        r = fetch_json(url)
        parsed = r.get("od_data", {}).get("has_parsed")

        if parsed:
            popul.pop_unparsed(r, id, cur, conn)
            popul.pop_all_parsed(r, id, cur, conn)

        else:
            popul.pop_unparsed(r, id, cur, conn)

