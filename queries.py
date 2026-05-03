import os
import sqlite3


def get_database_path():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, "data_base", "database.db")


def get_database_version():
    """Return a lightweight value that changes whenever SQLite is updated."""
    db_path = get_database_path()
    if not os.path.exists(db_path):
        return 0

    return os.path.getmtime(db_path)


# Connecting to the databse
def get_connection():
    db_path = get_database_path()

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def get_matches_by_account(
        cur, account_id, results_filter, matches_filter,
        peer_id, parse_filter, item, 
        first_item=None, second_item=None
        ):
    sql = '''
        SELECT
            ps.account_id,
            ps.personaname,
            ps.hero_id,
            ps.hero_localized_name,

            ps.hero_damage,
            ps.tower_damage,
            
            ps.net_worth,
            ps.gold_per_min,
            ps.xp_per_min,
            ps.last_hits,
            ps.denies,

            ps.kills,
            ps.deaths,
            ps.assists,
            ps.kda,
            ps.hero_healing,
            ps.win,

            pm.match_id,
            pm.duration,
            pm.start_time,
            pm.parsed_pop,

            b.pct_gold,
            b.pct_xp,
            b.pct_lh,
            b.pct_kills,
            b.pct_hero_dmg,
            b.pct_heal,
            b.pct_tower_dmg

        FROM players_stats ps
        JOIN player_matches pm
            ON pm.match_id = ps.match_id
        LEFT JOIN benchmarks b
            ON b.match_id = ps.match_id
            AND b.player_slot = ps.player_slot
        WHERE ps.account_id = ?
'''

    params = [account_id]

    # Results filter
    if results_filter == "Wins":
       sql += " AND ps.win = 1"
    elif results_filter == "Losses":
       sql += " AND ps.win = 0"

    # Parse status filter
    if parse_filter == "Parsed":
        sql += " AND pm.parsed_pop = 1"
    elif parse_filter == "Unparsed":
        sql += " AND pm.parsed_pop = 0"

    # Item in inventory
    if item != None:
        sql += '''
            AND (
                ps.item_0 = ?
                OR ps.item_1 = ?
                OR ps.item_2 = ?
                OR ps.item_3 = ?
                OR ps.item_4 = ?
                OR ps.item_5 = ?
                OR ps.backpack_0 = ?
                OR ps.backpack_1 = ?
                OR ps.backpack_2 = ?)
'''
        params.extend([item]*9)

    # Item purchase sequence filter
    if first_item and second_item:
        sql += '''
            AND EXISTS (
                SELECT 1
                FROM (
                    SELECT
                        match_id,
                        player_slot,
                        MIN(CASE WHEN p_key = ? THEN p_time END) AS first_time,
                        MIN(CASE WHEN p_key = ? THEN p_time END) AS second_time
                    FROM purchase_log
                    WHERE match_id = ps.match_id
                    AND player_slot = ps.player_slot
                    GROUP BY match_id, player_slot
                ) item_times
                WHERE item_times.first_time IS NOT NULL
                AND item_times.second_time IS NOT NULL
                AND item_times.first_time < item_times.second_time
            )
'''
        params.extend([first_item, second_item])

    # Peers filter
    if peer_id:
        sql += '''
            AND ps.match_id IN (
                SELECT match_id
                FROM players_stats
                WHERE account_id = ?
            )
        '''
        params.append(peer_id)


    # Number of matches filter
    if matches_filter != "all":
        sql += " ORDER BY pm.match_id DESC LIMIT ?"
        params.append(matches_filter)
    else:
        sql+= " ORDER BY pm.match_id DESC"
    
       
    cur.execute(sql, params)
    return cur.fetchall()

  
# List of matches for an account 
def get_account_matches():
    sql = '''
        
'''
# Match overview from player_matches table
def get_match_overview(cur, match_id, account_id=None):
    sql = '''
        SELECT
            pm.match_id,
            pm.lobby_type,
            pm.average_rank,
            am.party_size,
            pm.start_time,
            pm.duration,
            am.outcome,
            am.leaver_status,
            pm.dire_score,
            pm.radiant_score,
            pm.patch,
            pm.version,
            pm.unparsed_pop,
            pm.parsed_pop
        FROM player_matches pm
        LEFT JOIN account_matches am
            ON am.match_id = pm.match_id
            AND (? IS NULL OR am.account_id = ?)
        WHERE pm.match_id = ?
        ORDER BY am.account_id
        LIMIT 1
'''

    cur.execute(sql, (account_id, account_id, match_id))
    return cur.fetchone()


# Match per-player stats from players_stats table
# and benchmarks from Benchmarks table
def get_match_players(cur, match_id):
    sql = '''
        SELECT
            ps.match_id,
            ps.account_id,
            ps.personaname,
            ps.player_slot,
            ps.hero_id,
            ps.hero_localized_name,
            ps.facet_name,

            ps.kills,
            ps.deaths,
            ps.assists,
            ps.kda,
            ps.win,
            ps.lose,

            ps.gold_per_min,
            ps.xp_per_min,
            ps.last_hits,
            ps.denies,
            ps.net_worth,
            ps.level,

            ps.hero_damage,
            ps.tower_damage,
            ps.hero_healing,

            ps.item_0,
            ps.item_1,
            ps.item_2,
            ps.item_3,
            ps.item_4,
            ps.item_5,
            ps.backpack_0,
            ps.backpack_1,
            ps.backpack_2,
            ps.item_neutral,

            ps.isRadiant,
            ps.radiant_win,

            b.pct_gold,
            b.pct_xp,
            b.pct_lh,
            b.pct_kills,
            b.pct_hero_dmg,
            b.pct_heal,
            b.pct_tower_dmg

        FROM players_stats ps
        LEFT JOIN benchmarks b
            ON b.match_id = ps.match_id
            AND b.player_slot = ps.player_slot
        WHERE ps.match_id = ?
        ORDER BY ps.player_slot
'''

    cur.execute(sql,(match_id,))
    return cur.fetchall()


# Match objectives
def get_match_objectives(cur, match_id):
    sql = '''
        SELECT
            match_id,
            time,
            objective_id,
            objective_type,
            key,
            unit,
            slot,
            player_slot
        FROM objectives
        WHERE match_id = ?
        ORDER BY time
'''
    cur.execute(sql, (match_id,))
    return cur.fetchall()


# Match team-fights general
def get_match_tf(cur, match_id):
    sql = '''
        SELECT
            match_id,
            tf_seq,
            start_time,
            end_time,
            deaths,
            duration
        FROM team_fights
        WHERE match_id = ?
        ORDER BY tf_seq
'''

    cur.execute(sql, (match_id,))
    return cur.fetchall()


# Match per player team-fights stats
def get_tf_players(cur, match_id):
    sql= '''
        SELECT
            fp.match_id,
            fp.tf_seq,
            fp.player_slot,
            ps.personaname,
            ps.hero_localized_name,
            fp.deaths,
            fp.buybacks,
            fp.damage,
            fp.healing,
            fp.gold_delta,
            fp.xp_delta,
            fp.xp_start,
            fp.xp_end
        FROM fight_players fp
        LEFT JOIN players_stats ps
            ON ps.match_id = fp.match_id
            AND ps.player_slot = fp.player_slot
        WHERE fp.match_id = ?
        ORDER by fp.tf_seq, fp.player_slot
        '''
    
    cur.execute(sql, (match_id,))
    return cur.fetchall()


# Match item purchases
def get_match_purchase_log(cur, match_id):
    sql = '''
        SELECT
            pl.match_id,
            pl.player_slot,
            ps.personaname,
            ps.hero_localized_name,
            pl.p_time,
            pl.p_key
        FROM purchase_log pl
        LEFT JOIN players_stats ps
            ON ps.match_id = pl.match_id
            AND ps.player_slot = pl.player_slot
        WHERE pl.match_id = ?
        ORDER BY pl.p_time, pl.player_slot
        '''
    
    cur.execute(sql,(match_id,))
    return cur.fetchall()


# Match ability uses per player (hero)
def get_match_ability_uses(cur, match_id):
    sql = '''
        SELECT
            au.match_id,
            au.player_slot,
            ps.personaname,
            ps.hero_localized_name,
            au.ability,
            au.use_count
        FROM ability_uses au
        LEFT JOIN players_stats ps
            ON ps.match_id = au.match_id
            AND ps.player_slot = au.player_slot
        WHERE au.match_id = ?
        ORDER BY au.player_slot, au.use_count DESC
        '''
    
    cur.execute(sql, (match_id,))
    return cur.fetchall()


# Match item uses per player
def get_match_item_uses(cur, match_id):
    sql = '''
        SELECT 
            iu.match_id,
            iu.player_slot,
            ps.personaname,
            ps.hero_localized_name,
            iu.item,
            iu.uses
        FROM item_uses iu
        LEFT JOIN players_stats ps
            ON ps.match_id = iu.match_id
            AND ps.player_slot = iu.player_slot
        WHERE iu.match_id = ?
        ORDER BY iu.player_slot, iu.uses DESC
'''

    cur.execute(sql, (match_id,))
    return cur.fetchall()


# Match per player total damage done to enemy heroes
def get_output_damage_total(cur, match_id):
    sql = '''
        SELECT
            d.match_id,
            d.player_slot,
            ps.personaname,
            ps.hero_localized_name,
            d.victim,
            d.value
        FROM damage d
        LEFT JOIN players_stats ps
            ON ps.match_id = d.match_id
            AND ps.player_slot = d.player_slot
        WHERE d.match_id = ?
        ORDER BY d.player_slot, d.value DESC
'''

    cur.execute(sql, (match_id,))
    return cur.fetchall()


# Get match per-player output damage by source (ability, items, attacks...etc)
def get_output_damage_source(cur, match_id):
    sql = '''
        SELECT
            di.match_id,
            di.player_slot,
            ps.personaname,
            ps.hero_localized_name,
            di.inflictor,
            di.value
        FROM damage_inflictor di
        LEFT JOIN players_stats ps
            ON ps.match_id = di.match_id
            AND ps.player_slot = di.player_slot
        WHERE di.match_id = ?
        ORDER BY di.player_slot, di.value DESC
''' 

    cur.execute(sql, (match_id,))
    return cur.fetchall()


# Get match damage-taken per-player
def get_input_damage(cur, match_id):
    sql = '''
        SELECT
            dt.match_id,
            dt.player_slot,
            ps.personaname,
            ps.hero_localized_name,
            dt.dmg_source,
            dt.value
        FROM damage_taken dt
        LEFT JOIN players_stats ps
            ON ps.match_id = dt.match_id
            AND ps.player_slot = dt.player_slot
        WHERE dt.match_id = ?
        ORDER BY dt.player_slot, dt.value DESC
'''

    cur.execute(sql, (match_id,))
    return cur.fetchall()


# Match XP-Gold and LH-Denies timings per player
def get_timings(cur, match_id):
    sql = '''
        SELECT
            t.match_id,
            t.player_slot,
            ps.personaname,
            ps.hero_localized_name,
            t.time_sec,
            t.gold_t,
            t.xp_t,
            t.lh_t,
            t.dn_t
        FROM timings t
        LEFT JOIN players_stats ps
            ON ps.match_id = t.match_id
            AND ps.player_slot = t.player_slot
        WHERE t.match_id = ?
        ORDER BY t.player_slot, t.time_sec
'''

    cur.execute(sql, (match_id,))
    return cur.fetchall()


# Match radiant XP-Gold advantage
def get_match_radiant_adv(cur, match_id):
    sql = '''
        SELECT
            match_id,
            minute,
            radiant_gold_adv,
            radiant_xp_adv
        FROM radiant_adv
        WHERE match_id = ?
        ORDER BY minute
'''

    cur.execute(sql, (match_id,))
    return cur.fetchall()


# All stats for a match
def full_match(cur, match_id):
    match_stats = {}
    match_stats["overview"] = get_match_overview(cur, match_id)
    match_stats["players"] = get_match_players(cur, match_id)
    match_stats["objectives"] = get_match_objectives(cur, match_id)
    match_stats["team_fights"] = get_match_tf(cur, match_id)
    match_stats["fight_players"] = get_tf_players(cur, match_id)
    match_stats["purchase_log"] = get_match_purchase_log(cur, match_id)
    match_stats["ability_uses"] = get_match_ability_uses(cur, match_id)
    match_stats["item_uses"] = get_match_item_uses(cur, match_id)
    match_stats["damage_output_total"] = get_output_damage_total(cur, match_id)
    match_stats["damage_output_source"] = get_output_damage_source(cur, match_id)
    match_stats["damage_input"] = get_input_damage(cur, match_id)
    match_stats["timings"] = get_timings(cur, match_id)
    match_stats["radiant_adv"] = get_match_radiant_adv(cur, match_id)

    return match_stats
