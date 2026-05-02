"""Data loading helpers that transform OpenDota-style JSON into normalized SQLite rows."""

from logging_config import get_logger


logger = get_logger(__name__)


# Avoiding populating with 0s
def nullable_get(data, key):
    """Return None only when a key is absent; preserve real zero values."""
    return data[key] if key in data else None

# Avoiding populating with 0s
def nested_nullable_get(data, *keys):
    """Read a nested value, returning None when any key is absent."""
    current = data
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    return current


def owner_outcome_from_match_row(m):
    """Return owner outcome (1 win, 0 loss) from OpenDota player match row."""
    player_slot = m.get("player_slot")
    radiant_win = m.get("radiant_win")

    if player_slot is None or radiant_win is None:
        return None

    is_radiant_player = int(player_slot) < 128
    return int(bool(radiant_win) == is_radiant_player)


# Base match population
def populate_base_table(all_matches, account_id, cur, conn):
    """Insert match skeleton and account-scoped match rows."""
    match_sql = """
        INSERT OR IGNORE INTO player_matches (
            match_id, game_mode, lobby_type, average_rank,
            start_time, duration, version, retries, unparsed_pop, parsed_pop
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    account_match_sql = """
        INSERT INTO account_matches (
            account_id, match_id, player_slot, party_size,
            outcome, leaver_status
        ) VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(account_id, match_id) DO UPDATE SET
            player_slot = excluded.player_slot,
            party_size = excluded.party_size,
            outcome = excluded.outcome,
            leaver_status = excluded.leaver_status
    """

    default_retries = 0
    default_unparsed_pop = 0
    default_parsed_pop = 0

    for m in all_matches:
        id = m.get("match_id")

        try:
            cur.execute(
                match_sql,
                (
                    id,
                    nullable_get(m, "game_mode"),
                    nullable_get(m, "lobby_type"),
                    nullable_get(m, "average_rank"),
                    nullable_get(m, "start_time"),
                    nullable_get(m, "duration"),
                    nullable_get(m, "version"),
                    default_retries,
                    default_unparsed_pop,
                    default_parsed_pop,
                ),
            )
            cur.execute(
                account_match_sql,
                (
                    account_id,
                    id,
                    nullable_get(m, "player_slot"),
                    nullable_get(m, "party_size"),
                    owner_outcome_from_match_row(m),
                    nullable_get(m, "leaver_status"),
                ),
            )
            logger.info(
                "Inserted/verified base match rows. account_id=%s match_id=%s",
                account_id,
                id,
            )

        except Exception:
            logger.exception("Failed inserting base match row. match_id=%s", id)
            raise

    conn.commit()


# Unparsed player stats population
def populate_unparsed_stats_table(id, p, cur):
    """Insert base player stats available from unparsed match payloads."""
    columns = [
        "account_id",
        "personaname",
        "player_slot",
        "leaver_status",
        "hero_id",
        "hero_name",
        "hero_localized_name",
        "hero_variant",
        "facet_name",
        "abandons",
        "item_0",
        "item_1",
        "item_2",
        "item_3",
        "item_4",
        "item_5",
        "backpack_0",
        "backpack_1",
        "backpack_2",
        "item_neutral",
        "item_neutral2",
        "kills",
        "kills_per_min",
        "kda",
        "deaths",
        "assists",
        "last_hits",
        "denies",
        "total_gold",
        "gold_per_min",
        "gold",
        "gold_spent",
        "total_xp",
        "xp_per_min",
        "level",
        "net_worth",
        "aghanims_scepter",
        "aghanims_shard",
        "moonshard",
        "hero_damage",
        "tower_damage",
        "hero_healing",
        "isRadiant",
        "radiant_win",
        "win",
        "lose",
    ]

    sql = f"""
        INSERT OR IGNORE INTO players_stats (
            match_id, {", ".join(columns)}
        ) VALUES ({", ".join(["?"] * (len(columns) + 1))})
"""

    values = []
    for d in columns:
        if d == "player_slot":
            value = p.get(d, 0)
        else:
            value = nullable_get(p, d)
        values.append(value)

    cur.execute(sql, (id, *values))


# Benchmark population (unparsed stage)
def pop_benchmarks(id, p, cur):
    """Insert per-player benchmark raw values and percentiles."""
    sql = """
        INSERT OR IGNORE INTO benchmarks (
            match_id, player_slot, raw_gold, pct_gold, raw_xp, pct_xp, 
            raw_lh, pct_lh, raw_kills, pct_kills, raw_hero_dmg,
            pct_hero_dmg, raw_heal, pct_heal, raw_tower_dmg, 
            pct_tower_dmg
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
"""
    bench = p.get("benchmarks") or {}
    if not bench:
        return

    cur.execute(
        sql,
        (
            id,
            p.get("player_slot", 0),
            nested_nullable_get(bench, "gold_per_min", "raw"),
            nested_nullable_get(bench, "gold_per_min", "pct"),
            nested_nullable_get(bench, "xp_per_min", "raw"),
            nested_nullable_get(bench, "xp_per_min", "pct"),
            nested_nullable_get(bench, "last_hits_per_min", "raw"),
            nested_nullable_get(bench, "last_hits_per_min", "pct"),
            nested_nullable_get(bench, "kills_per_min", "raw"),
            nested_nullable_get(bench, "kills_per_min", "pct"),
            nested_nullable_get(bench, "hero_damage_per_min", "raw"),
            nested_nullable_get(bench, "hero_damage_per_min", "pct"),
            nested_nullable_get(bench, "hero_healing_per_min", "raw"),
            nested_nullable_get(bench, "hero_healing_per_min", "pct"),
            nested_nullable_get(bench, "tower_damage", "raw"),
            nested_nullable_get(bench, "tower_damage", "pct"),
        ),
    )


# Permanent buffs population (unparsed stage)
def pop_perma_buffs(id, p, cur):
    """Insert permanent buff events for a player."""
    sql = """
        INSERT OR IGNORE INTO perma_buffs (
            match_id, player_slot, buff_id, stack_count, grant_time
) VALUES (?, ?, ?, ?, ?)
"""
    puffs = p.get("permanent_buffs") or []
    p_slot = p.get("player_slot", 0)

    for puff in puffs:
        cur.execute(
            sql,
            (
                id,
                p_slot,
                puff.get("permanent_buff", 0),
                puff.get("stack_count", 0),
                nullable_get(puff, "grant_time"),
            ),
        )


# Ability upgrades population (unparsed stage)
def pop_ability_upgrades(id, p, cur):
    """Insert ordered ability upgrades from ability_upgrades_arr."""
    sql = """
        INSERT OR IGNORE INTO ability_upgrades(
            match_id, player_slot, seq, ability_id
            ) VALUES (?, ?, ?, ?)
"""

    p_slot = p.get("player_slot", 0)
    a_u = p.get("ability_upgrades_arr") or []

    for seq, a in enumerate(a_u):
        cur.execute(sql, (id, p_slot, seq, a))


# Match score update
def pop_score(r, id, cur):
    """Update match-level score fields and mark unparsed population as complete."""
    sql = """
        UPDATE player_matches
        SET dire_score = ?,
            radiant_score = ?,
            patch = ?,
            unparsed_pop = 1
        WHERE match_id = ?
        """

    cur.execute(
        sql,
        (
            nullable_get(r, "dire_score"),
            nullable_get(r, "radiant_score"),
            nullable_get(r, "patch"),
            id,
        ),
    )


# Unparsed-stage orchestration
def pop_unparsed(r, id, cur, conn):

    """Populate all unparsed-stage match/player tables for one match payload."""

    pop_score(r, id, cur)

    for p in r.get("players", []):
        populate_unparsed_stats_table(id, p, cur)
        pop_benchmarks(id, p, cur)
        pop_perma_buffs(id, p, cur)
        pop_ability_upgrades(id, p, cur)

    conn.commit()


# Parsed stats update
def pop_parsed_stats(id, p, cur):
    """Update advanced parsed-only columns in players_stats for one player."""
    sql = """
        UPDATE players_stats
        SET buyback_count = ?,
            predict_victory = ?,
            obs_placed = ?,
            sentries_placed = ?,
            creeps_stacked = ?,
            camps_stacked = ?,
            rune_pickups = ?,
            firstblood_claimed = ?,
            team_fight_participation = ?,
            stuns = ?,
            lane = ?,
            lane_role = ?,
            lane_efficiency = ?,
            lane_efficiency_pct = ?,
            lane_kills = ?,
            neutral_kills = ?,
            ancient_kills = ?,
            roshan_kills = ?,
            necronomicon = ?,
            courier_kills = ?,
            hero_kills = ?,
            tower_kills = ?,
            observer_kills = ?,
            sentry_kills = ?,
            sentry_uses = ?,
            observer_uses = ?
        WHERE match_id = ?
        AND player_slot = ?
"""

    data = [
        "buyback_count",
        "predict_victory",
        "obs_placed",
        "sentries_placed",
        "creeps_stacked",
        "camps_stacked",
        "rune_pickups",
        "firstblood_claimed",
        "team_fight_participation",
        "stuns",
        "lane",
        "lane_role",
        "lane_efficiency",
        "lane_efficiency_pct",
        "lane_kills",
        "neutral_kills",
        "ancient_kills",
        "roshan_kills",
        "necronomicon",
        "courier_kills",
        "hero_kills",
        "tower_kills",
        "observer_kills",
        "sentry_kills",
        "sentry_uses",
        "observer_uses",
    ]

    p_slot = p.get("player_slot", 0)
    values = []

    for d in data:
        value = nullable_get(p, d)
        values.append(value)

    values.append(id)
    values.append(p_slot)

    cur.execute(sql, values)


# Teamfight summary population
def pop_team_fights(id, tf_seq, cur, f):
    """Insert one team fight summary row with normalized timing fields."""
    sql = """
        INSERT OR IGNORE INTO team_fights (
            match_id, tf_seq, start_time, end_time, deaths, duration
            ) VALUES (?, ?, ?, ?, ?, ?)
"""

    f_start = nullable_get(f, "start")
    f_end = nullable_get(f, "end")

    if f_end is not None and f_start is not None:
        f_duration = max(0, f_end - f_start)
    else:
        f_duration = None

    cur.execute(
        sql,
        (
            id,
            tf_seq,
            f_start,
            f_end,
            nullable_get(f, "deaths"),
            f_duration,
        ),
    )


# Teamfight player population
def pop_fight_players(id, tf_seq, p_slot, p, cur):
    """Insert one player's statistics for a specific team fight."""
    sql = """
        INSERT OR IGNORE INTO fight_players (
            match_id, tf_seq, player_slot, deaths, buybacks, damage, 
            healing, gold_delta, xp_delta, xp_start, xp_end
        )   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

    cur.execute(
        sql,
        (
            id,
            tf_seq,
            p_slot,
            nullable_get(p, "deaths"),
            nullable_get(p, "buybacks"),
            nullable_get(p, "damage"),
            nullable_get(p, "healing"),
            nullable_get(p, "gold_delta"),
            nullable_get(p, "xp_delta"),
            nullable_get(p, "xp_start"),
            nullable_get(p, "xp_end"),
        ),
    )


# Teamfight action population
def pop_fight_action(id, tf_seq, p_slot, action_type, action_key, action_value, cur):
    """Insert one normalized action aggregate row for a team fight player."""
    sql = """
        INSERT OR IGNORE INTO fight_actions (
           match_id, tf_seq, player_slot, action_type, 
           action_key, action_value
        ) VALUES (?, ?, ?, ?, ?, ?)
"""

    cur.execute(sql, (id, tf_seq, p_slot, action_type, action_key, action_value))


# Teamfight tables orchestration
def pop_all_fights(r, id, cur):
    """Populate team_fights, fight_players, and fight_actions from parsed match data."""
    for tf_seq, f in enumerate(r.get("teamfights") or []):
        pop_team_fights(id, tf_seq, cur, f)

        p_slots = [0, 1, 2, 3, 4, 128, 129, 130, 131, 132]
        players = f.get("players") or []

        for p_seq, p in enumerate(players):
            if p_seq >= len(p_slots):
                continue
            p_slot = p_slots[p_seq]
            pop_fight_players(id, tf_seq, p_slot, p, cur)

            ab_uses = p.get("ability_uses") or {}
            if isinstance(ab_uses, dict):
                for key, value in ab_uses.items():
                    pop_fight_action(
                        id, tf_seq, p_slot, "ability_uses", key, value, cur
                    )

            item_uses = p.get("item_uses") or {}
            if isinstance(item_uses, dict):
                for key, value in item_uses.items():
                    pop_fight_action(id, tf_seq, p_slot, "item_uses", key, value, cur)


# Objectives population
def pop_objectives(id, r, cur):
    """Insert objective timeline rows for a parsed match."""
    sql = """
        INSERT OR IGNORE INTO objectives (
            match_id, time, objective_id, objective_type, key, unit,
            slot, player_slot
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
"""

    for obj_id, o in enumerate(r.get("objectives") or []):
        cur.execute(
            sql,
            (
                id,
                o.get("time"),
                obj_id,
                o.get("objective_type"),
                o.get("key"),
                o.get("unit"),
                o.get("slot"),
                o.get("player_slot"),
            ),
        )


# Radiant advantage population
def pop_radiant_adv(id, r, cur):
    """Insert minute-wise radiant gold and XP advantage arrays."""
    sql = """
        INSERT OR IGNORE INTO radiant_adv (
            match_id, minute, radiant_gold_adv, radiant_xp_adv
            ) VALUES (?, ?, ?, ?)
    """

    gold_list = r.get("radiant_gold_adv") or []
    xp_list = r.get("radiant_xp_adv") or []

    for m, gold in enumerate(gold_list):

        if m < len(xp_list):
            xp = xp_list[m]

        else:
            xp = None

        cur.execute(sql, (id, m, gold, xp))


# Player actions population
def pop_player_actions(id, p, slot, cur):
    """Insert aggregate action counts for a single player."""
    sql = """
        INSERT OR IGNORE INTO player_actions(
            match_id, player_slot, action_id, count
        ) VALUES (?, ?, ?, ?)
"""

    actions = p.get("actions") or {}

    for key, value in actions.items():
        cur.execute(sql, (id, slot, key, value))


# Max hit population
def pop_max_hit(id, p, slot, cur):
    """Insert maximum hero hit details when present."""
    sql = """
        INSERT OR IGNORE INTO max_hit(
            match_id, player_slot, type, time, highest, 
            inflictor, unit, key, value
        )   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
"""
    m = p.get("max_hero_hit") or {}

    if not isinstance(m, dict) or not m:
        return

    if m.get("max"):
        highest = 1
    else:
        highest = 0

    cur.execute(
        sql,
        (
            id,
            slot,
            m.get("type"),
            m.get("time"),
            highest,
            m.get("inflictor"),
            m.get("unit"),
            m.get("key"),
            m.get("value"),
        ),
    )


# Incoming damage by source population
def pop_damage_received(id, p, slot, cur):
    """Insert incoming damage grouped by source."""
    sql = """
        INSERT OR IGNORE INTO damage_inflictor_received(
            match_id, player_slot, source, value
        )   VALUES (?, ?, ?, ?)
"""

    dmg_rec = p.get("damage_inflictor_received") or {}

    if not dmg_rec:
        return

    for key, value in dmg_rec.items():
        cur.execute(sql, (id, slot, key, value))


# Damage taken population
def pop_damage_taken(id, p, slot, cur):
    """Insert damage taken grouped by source."""
    sql = """
        INSERT OR IGNORE INTO damage_taken(
            match_id, player_slot, dmg_source, value
        ) VALUES (?, ?, ?, ?)
"""

    damage_taken = p.get("damage_taken") or {}

    if not damage_taken:
        return

    for key, value in damage_taken.items():
        cur.execute(sql, (id, slot, key, value))


# Outgoing damage by inflictor population
def pop_damage_inflictor(id, p, slot, cur):
    """Insert outgoing damage grouped by inflictor."""
    sql = """
        INSERT OR IGNORE INTO damage_inflictor(
            match_id, player_slot, inflictor, value
        )   VALUES (?, ?, ?, ?)
"""

    damage_inflictor = p.get("damage_inflictor") or {}
    if not damage_inflictor:
        return

    for key, value in damage_inflictor.items():
        cur.execute(sql, (id, slot, key, value))


# Outgoing damage distribution population
def pop_damage_table(id, p, slot, cur):
    """Insert outgoing damage grouped by victim target."""
    sql = """
        INSERT OR IGNORE INTO damage(
            match_id, player_slot, victim, value
        ) VALUES (?, ?, ?, ?)
"""

    damage = p.get("damage") or {}
    if not damage:
        return

    for key, value in damage.items():
        cur.execute(sql, (id, slot, key, value))


# Damage source-to-target population
def pop_damage_targets(id, p, slot, cur):
    """Insert nested source->target damage distribution rows."""
    sql = """
        INSERT OR IGNORE INTO damage_targets(
            match_id, player_slot, damage_source, damage_target, value
        ) VALUES(?, ?, ?, ?, ?)
"""

    damage_targets = p.get("damage_targets") or {}

    if not damage_targets:
        return

    for source, target in damage_targets.items():
        target = target or {}
        for key, value in target.items():
            cur.execute(sql, (id, slot, source, key, value))


# Single ward event population
def pop_ward(
    id, slot, type, seq, cur, x, y, 
    placed_time, has_left, removed_time, 
    attacker
):
    """Insert one ward placement/removal timeline row."""
    sql = """
        INSERT OR IGNORE INTO ward_instances (
            match_id, player_slot, ward_type, ward_seq,
            x, y, placed_time, has_left, removed_time, 
            attacker_name
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""
    cur.execute(
        sql, (
            id, slot, type, seq, x, y, placed_time, 
            has_left, removed_time, attacker)
    )


# Observer ward population
def pop_observers(id, p, cur):

    """Insert observer ward placement and removal logs."""

    slot = p.get("player_slot", 0)

    obs_log = p.get("obs_log") or []
    if not obs_log:
        return

    obs_left_log = p.get("obs_left_log") or []

    ward_type = "observer"

    for log_seq, obs in enumerate(obs_log):
        x = obs.get("x")
        y = obs.get("y")
        placed_time = nullable_get(obs, "time")
        if placed_time is None:
            continue

        if (
            log_seq < len(obs_left_log)
            and obs_left_log[log_seq].get("entityleft")
        ):

            has_left = 1
            attacker = obs_left_log[log_seq].get("attacker")
            removed_time = obs_left_log[log_seq].get("time")

        else:
            has_left = 0
            attacker = None
            removed_time = None

        pop_ward(
            id,
            slot,
            ward_type,
            log_seq,
            cur,
            x,
            y,
            placed_time,
            has_left,
            removed_time,
            attacker,
        )


# Sentry ward population
def pop_sentries(id, p, cur):

    """Insert sentry ward placement and removal logs."""

    slot = p.get("player_slot", 0)

    sen_log = p.get("sen_log") or []
    if not sen_log:
        return

    sen_left_log = p.get("sen_left_log") or []

    ward_type = "sentry"

    for log_seq, sen in enumerate(sen_log):
        x = sen.get("x")
        y = sen.get("y")
        placed_time = nullable_get(sen, "time")
        if placed_time is None:
            continue

        if (
            log_seq < len(sen_left_log)
            and sen_left_log[log_seq].get("entityleft")
        ):

            has_left = 1
            attacker = sen_left_log[log_seq].get("attacker")
            removed_time = sen_left_log[log_seq].get("time")

        else:
            has_left = 0
            attacker = None
            removed_time = None

        pop_ward(
            id,
            slot,
            ward_type,
            log_seq,
            cur,
            x,
            y,
            placed_time,
            has_left,
            removed_time,
            attacker,
        )


# Hero hit counts population
def pop_hero_hits(id, p, slot, cur):
    """Insert hero hit counts grouped by hit source."""
    sql = '''
        INSERT OR IGNORE INTO hero_hits (
            match_id, player_slot, hit_source, hit_count
        ) VALUES (?, ?, ?, ?)
'''
    hero_hits = p.get("hero_hits") or {}
    if not hero_hits:
        return
    
    for key, value in hero_hits.items():
        cur.execute(sql, (id, slot, key, value))


# Units killed population
def pop_units_killed(id, p, slot, cur):
    """Insert killed unit counts for a player."""
    sql = '''
        INSERT OR IGNORE INTO units_killed (
            match_id, player_slot, unit, count
        ) VALUES (?, ?, ?, ?)
'''
    units_killed = p.get("killed") or {}
    if not units_killed:
        return
    
    for key, value in units_killed.items():
        cur.execute(sql, (id, slot, key, value))


# Purchase log population
def pop_purchase_log(id, p, slot, cur):
    """Insert item purchase events for a player timeline."""
    sql = '''
        INSERT OR IGNORE INTO purchase_log (
            match_id, player_slot, p_time, p_key
            ) VALUES (?, ?, ?, ?)
            '''
    purchase_log = p.get("purchase_log") or []
    for log in purchase_log:
        p_time = nullable_get(log, "time")
        p_key = nullable_get(log, "key")
        if p_time is None or p_key is None:
            continue
        cur.execute(sql, (id, slot, p_time, p_key))


# Item usage population
def pop_item_uses(id, p, slot, cur):
    """Insert aggregate item usage counts for a player."""
    sql = '''
        INSERT OR IGNORE INTO item_uses (
            match_id, player_slot, item, uses
        ) VALUES (?, ?, ?, ?)
'''
    item_uses = p.get("item_uses") or {}
    if not item_uses:
        return
    
    for key, value in item_uses.items():
        cur.execute(sql, (id, slot, key, value))


# Ability usage population
def pop_ability_uses(id, p, slot, cur):
    """Insert aggregate ability usage counts for a player."""
    sql = '''
        INSERT OR IGNORE INTO ability_uses (
            match_id, player_slot, ability, use_count
        ) VALUES (?, ?, ?, ?)
'''
    ability_uses = p.get("ability_uses") or {}
    if not ability_uses:
        return
    
    for key, value in ability_uses.items():
        cur.execute(sql, (id, slot, key, value))


# Ability target population
def pop_ability_targets(id, p, slot, cur):
    """Insert ability target distribution rows for a player."""
    sql = '''
        INSERT OR IGNORE INTO ability_targets (
            match_id, player_slot, ability, target, count
        ) VALUES (?, ?, ?, ?, ?)
'''
    ability_targets = p.get("ability_targets") or {}
    if not ability_targets:
        return
    
    for ability, target in ability_targets.items():
        target = target or {}
        for key, value in target.items():
            cur.execute(sql, (id, slot, ability, key, value))


# Neutral item history population
def pop_neutral_items(id, p, slot, cur):
    """Insert neutral item history timeline rows."""
    sql = '''
        INSERT OR IGNORE INTO neutral_item_history (
            match_id, player_slot, time, item_neutral,
            item_enhancement
        ) VALUES (?, ?, ?, ?, ?)
'''
    neutral_items = p.get("neutral_item_history") or []
    if not neutral_items:
        return
    
    for item in neutral_items:
        item_name = nullable_get(item, "item_neutral")
        item_enhancement = nullable_get(item, "item_neutral_enhancement")
        item_time = nullable_get(item, "time")
        if item_time is None:
            continue
        cur.execute(sql, (
            id, slot, item_time, item_name, 
            item_enhancement))
        

# Player healing population
def pop_player_heals(id, p, slot, cur):
    """Insert healing totals grouped by healing source."""
    sql = '''
        INSERT OR IGNORE INTO heal (
            match_id, player_slot, healing_source, value
        ) VALUES (?, ?, ?, ?)
'''
    player_heals = p.get("healing") or {}
    if not player_heals:
        return
    
    for key, value in player_heals.items():
        cur.execute(sql, (id, slot, key, value))


# Multi-kill population
def pop_multi_kills(id, p, slot, cur):
    """Insert multi-kill frequency rows."""
    sql = '''
        INSERT OR IGNORE INTO multi_kills (
            match_id, player_slot, mult, count
        ) VALUES (?, ?, ?, ?)
'''
    multi_kills = p.get("multi_kills") or {}
    if not multi_kills:
        return
    for key, value in multi_kills.items():
        cur.execute(sql, (id, slot, key, value))


# Kill streak population
def pop_kill_streaks(id, p, slot, cur):
    """Insert kill streak frequency rows."""
    sql = '''
        INSERT OR IGNORE INTO kill_streaks (
            match_id, player_slot, streak, count
        ) VALUES (?, ?, ?, ?)
'''
    kill_streaks = p.get("kill_streaks") or {}
    if not kill_streaks:
        return
    for key, value in kill_streaks.items():
        cur.execute(sql, (id, slot, key, value))


# Killed-by population
def pop_killed_by(id, p, slot, cur):
    """Insert deaths grouped by killer identity."""
    sql = '''
        INSERT OR IGNORE INTO killed_by (
            match_id, player_slot, killer, deaths
        ) VALUES (?, ?, ?, ?)
'''
    killed_by = p.get("killed_by") or {}
    if not killed_by:
        return
    for key, value in killed_by.items():
        cur.execute(sql, (id, slot, key, value))


# Player runes population
def pop_runes(id, p, slot, cur):
    """Insert rune pickup counts for a player."""
    sql = '''
        INSERT OR IGNORE INTO player_runes (
            match_id, player_slot, rune_id, rune_count
        ) VALUES (?, ?, ?, ?)
'''
    runes = p.get("runes") or {}
    if not runes:
        return
    for key, value in runes.items():
        cur.execute(sql, (id, slot, key, value))


# Timings population
def pop_timings(id, p, slot, cur):
    """Insert aligned timeline arrays for gold/xp/lh/denies."""
    sql = '''
        INSERT OR IGNORE INTO timings (
            match_id, player_slot, time_sec, gold_t, xp_t,
            lh_t, dn_t
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
'''
    minutes = p.get("times") or []
    gold_t = p.get("gold_t") or []
    xp_t = p.get("xp_t") or []
    lh_t = p.get("lh_t") or []
    dn_t = p.get("dn_t") or []

    for i, time_sec in enumerate(minutes):

        if (i < len(gold_t) 
            and i < len(xp_t) 
            and i < len(lh_t)
            and i < len(dn_t)):

            cur.execute(sql, (
                id, slot, time_sec, 
                gold_t[i], xp_t[i], 
                lh_t[i], dn_t[i]))


# Gold reasons population
def pop_gold_reasons(id, p, slot, cur):
    """Insert gold reason count rows."""
    sql = '''
        INSERT OR IGNORE INTO gold_reasons (
            match_id, player_slot, reason, count
        ) VALUES (?, ?, ?, ?)
'''
    gold_reasons = p.get("gold_reasons") or {}
    if not gold_reasons:
        return
    for key, value in gold_reasons.items():
        cur.execute(sql, (id, slot, key, value))


# XP reasons population
def pop_xp_reasons(id, p, slot, cur):
    """Insert XP reason count rows."""
    sql = '''
        INSERT OR IGNORE INTO xp_reasons (
            match_id, player_slot, reason, count
        ) VALUES (?, ?, ?, ?)
'''
    xp_reasons = p.get("xp_reasons") or {}
    if not xp_reasons:
        return
    for key, value in xp_reasons.items():
        cur.execute(sql, (id, slot, key, value))


# Parsed-stage orchestration
def pop_all_parsed(r, id, cur, conn):

    """Populate all parsed-stage tables for a single fully parsed match payload."""

    pop_all_fights(r, id, cur)
    pop_objectives(id, r, cur)
    pop_radiant_adv(id, r, cur)

    for p in r.get("players", []):

        slot = p.get("player_slot", 0)

        pop_parsed_stats(id, p, cur)
        pop_player_actions(id, p, slot, cur)
        pop_max_hit(id, p, slot, cur)
        pop_damage_received(id, p, slot, cur)
        pop_damage_taken(id, p, slot, cur)
        pop_damage_inflictor(id, p, slot, cur)
        pop_damage_table(id, p, slot, cur)
        pop_damage_targets(id, p, slot, cur)
        pop_observers(id, p, cur)
        pop_sentries(id, p, cur)
        pop_hero_hits(id, p, slot, cur)
        pop_units_killed(id, p, slot, cur)
        pop_purchase_log(id, p, slot, cur)
        pop_item_uses(id, p, slot, cur)
        pop_ability_uses(id, p, slot, cur)
        pop_ability_targets(id, p, slot, cur)
        pop_neutral_items(id, p, slot, cur)
        pop_player_heals(id, p, slot, cur)
        pop_multi_kills(id, p, slot, cur)
        pop_kill_streaks(id, p, slot, cur)
        pop_killed_by(id, p, slot, cur)
        pop_runes(id, p, slot, cur)
        pop_timings(id, p, slot, cur)
        pop_gold_reasons(id, p, slot, cur)
        pop_xp_reasons(id, p, slot, cur)

        cur.execute('''
            UPDATE player_matches
                SET parsed_pop = 1
                WHERE match_id = ?
            ''', (id,))
        
    conn.commit()
