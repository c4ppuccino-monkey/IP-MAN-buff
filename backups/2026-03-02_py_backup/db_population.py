# Exporting match data to the data base
def populate_base_table(all_matches, cur, conn):
    sql = """
        INSERT OR IGNORE INTO player_matches (
            match_id, game_mode, lobby_type, average_rank,
            party_size, start_time, duration, outcome, leaver_status,
            version, retries, unparsed_pop, parsed_pop
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    default_retries = 0
    default_unparsed_pop = 0
    default_parsed_pop = 0

    for m in all_matches:
        id = m.get("match_id")

        try:
            cur.execute(
                sql,
                (
                    id,
                    m.get("game_mode", 0),
                    m.get("lobby_type", 0),
                    m.get("average_rank", 0),
                    m.get("party_size", 0),
                    m.get("start_time", 0),
                    m.get("duration", 0),
                    m.get("outcome", 0),
                    m.get("leaver_status", 0),
                    m.get("version", 0),
                    default_retries,
                    default_unparsed_pop,
                    default_parsed_pop,
                ),
            )
            print(f"Match {id} was added successfully to base table.")

        except Exception as e:
            print(
                f"""There was an issue in exporting match_id,{id}, 
                  to the base table error={e}"""
            )
            raise

    conn.commit()


# populating stats table (before parsing)
def populate_unparsed_stats_table(id, p, cur):
    sql = """ 
        INSERT OR IGNORE INTO players_stats (
            match_id, account_id, personaname, player_slot, hero_id, 
            hero_variant, abandons, item_0, item_1, 
            item_2, item_3, item_4, item_5, backpack_0, backpack_1, 
            backpack_2, item_neutral, item_neutral2, kills, kills_per_min, 
            kda, deaths, assists, last_hits, denies, total_gold, 
            gold_per_min, gold, gold_spent, total_xp, xp_per_min, level, 
            net_worth, aghanims_scepter, aghanims_shard, moonshard, 
            hero_damage, tower_damage, hero_healing, isRadiant, 
            radiant_win, win, lose
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,
        ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
"""
    data = [
        "account_id",
        "personaname",
        "player_slot",
        "hero_id",
        "hero_variant",
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

    values = []
    for d in data:
        value = p.get(d, 0)
        values.append(value)

    cur.execute(sql, (id, *values))


# populating benchmarks (before parsing)
def pop_benchmarks(id, p, cur):
    sql = """
        INSERT OR IGNORE INTO benchmarks (
            match_id, player_slot, raw_gold, pct_gold, raw_xp, pct_xp, 
            raw_lh, pct_lh, raw_kills, pct_kills, raw_hero_dmg,
            pct_hero_dmg, raw_heal, pct_heal, raw_tower_dmg, 
            pct_tower_dmg
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
"""
    bench = p.get("benchmarks", {})

    cur.execute(
        sql,
        (
            id,
            p.get("player_slot", 0),
            bench.get("gold_per_min", {}).get("raw", 0),
            bench.get("gold_per_min", {}).get("pct", 0),
            bench.get("xp_per_min", {}).get("raw", 0),
            bench.get("xp_per_min", {}).get("pct", 0),
            bench.get("last_hits_per_min", {}).get("raw", 0),
            bench.get("last_hits_per_min", {}).get("pct", 0),
            bench.get("kills_per_min", {}).get("raw", 0),
            bench.get("kills_per_min", {}).get("pct", 0),
            bench.get("hero_damage_per_min", {}).get("raw", 0),
            bench.get("hero_damage_per_min", {}).get("pct", 0),
            bench.get("hero_healing_per_min", {}).get("raw", 0),
            bench.get("hero_healing_per_min", {}).get("pct", 0),
            bench.get("tower_damage", {}).get("raw", 0),
            bench.get("tower_damage", {}).get("pct", 0),
        ),
    )


# pop perma buffs (before parsing)
def pop_perma_buffs(id, p, cur):
    sql = """
        INSERT OR IGNORE INTO perma_buffs (
            match_id, player_slot, buff_id, stack_count, grant_time
) VALUES (?, ?, ?, ?, ?)
"""
    puffs = p.get("permanent_buffs", [])
    p_slot = p.get("player_slot", 0)

    for puff in puffs:
        cur.execute(
            sql,
            (
                id,
                p_slot,
                puff.get("permanent_buff", 0),
                puff.get("stack_count", 0),
                puff.get("grant_time", 0),
            ),
        )


# pop ability_upgrades (before parse)
def pop_ability_upgrades(id, p, cur):
    sql = """
        INSERT OR IGNORE INTO ability_upgrades(
            match_id, player_slot, seq, ability_id
            ) VALUES (?, ?, ?, ?)
"""

    p_slot = p.get("player_slot", 0)
    a_u = p.get("ability_upgrades_arr", [])

    for seq, a in enumerate(a_u):
        cur.execute(sql, (id, p_slot, seq, a))


# Dire and radiant score
def pop_score(r, id, cur):
    sql = """
        UPDATE player_matches
        SET dire_score = ?,
            radiant_score = ?,
            unparsed_pop = 1
        WHERE match_id = ?
        """

    cur.execute(sql, (r.get("dire_score", 0), r.get("radiant_score", 0), id))


# Pop all unparsed
def pop_unparsed(r, id, cur, conn):

    pop_score(r, id, cur)

    for p in r.get("players", []):
        populate_unparsed_stats_table(id, p, cur)
        pop_benchmarks(id, p, cur)
        pop_perma_buffs(id, p, cur)
        pop_ability_upgrades(id, p, cur)

    conn.commit()


# Pop parsed data in players_stats table
def pop_parsed_stats(id, p, cur):
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
        value = p.get(d, 0)
        values.append(value)

    values.append(id)
    values.append(p_slot)

    cur.execute(sql, values)


# Populate team_fights (after parsing)
def pop_team_fights(id, tf_seq, cur, f):
    sql = """
        INSERT OR IGNORE INTO team_fights (
            match_id, tf_seq, start_time, end_time, deaths, duration
            ) VALUES (?, ?, ?, ?, ?, ?)
"""

    cur.execute(
        sql,
        (
            id,
            tf_seq,
            f.get("start_time", 0),
            f.get("end_time", 0),
            f.get("deaths", 0),
            f.get("duration", 0),
        ),
    )


# Populate fight_players (after parsing)
def pop_fight_players(id, tf_seq, p_slot, p, cur):
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
            p.get("deaths", 0),
            p.get("buybacks", 0),
            p.get("damage", 0),
            p.get("healing", 0),
            p.get("gold_delta", 0),
            p.get("xp_delta", 0),
            p.get("xp_start", 0),
            p.get("xp_end", 0),
        ),
    )


# Populate fights actions by player
def pop_fight_action(id, tf_seq, p_slot, action_type, action_key, action_value, cur):
    sql = """
        INSERT OR IGNORE INTO fight_actions (
           match_id, tf_seq, player_slot, action_type, 
           action_key, action_value
        ) VALUES (?, ?, ?, ?, ?, ?)
"""

    cur.execute(sql, (id, tf_seq, p_slot, action_type, action_key, action_value))


# Populating all fights related tables
def pop_all_fights(r, id, cur):
    for tf_seq, f in enumerate(r.get("teamfights", [])):
        pop_team_fights(id, tf_seq, cur, f)

        p_slots = [0, 1, 2, 3, 4, 128, 129, 130, 131, 132]
        players = f.get("players", [])

        for p_seq, p in enumerate(players):
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


# Populating objectives (after parsing)
def pop_objectives(id, r, cur):
    sql = """
        INSERT OR IGNORE INTO objectives (
            match_id, time, objective_id, objective_type, key, unit,
            slot, player_slot
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
"""

    for obj_id, o in enumerate(r.get("objectives", [])):
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


# Populating radiant adv
def pop_radiant_adv(id, r, cur):
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


# Populating player_actions
def pop_player_actions(id, p, slot, cur):
    sql = """
        INSERT OR IGNORE INTO player_actions(
            match_id, player_slot, action_id, count
        ) VALUES (?, ?, ?, ?)
"""

    actions = p.get("actions", {})

    for key, value in actions.items():
        cur.execute(sql, (id, slot, key, value))


# Max hit per player (parsed)
def pop_max_hit(id, p, slot, cur):
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


# Populating damage_inflictor_recieved parsed
def pop_damage_received(id, p, slot, cur):
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


# Pop damage taken
def pop_damage_taken(id, p, slot, cur):
    sql = """
        INSERT OR IGNORE INTO damage_taken(
            match_id, player_slot, dmg_source, value
        ) VALUES (?, ?, ?, ?)
"""

    damage_taken = p.get("damage_taken", {})

    if not damage_taken:
        return

    for key, value in damage_taken.items():
        cur.execute(sql, (id, slot, key, value))


# Populating damage inflictor
def pop_damage_inflictor(id, p, slot, cur):
    sql = """
        INSERT OR IGNORE INTO damage_inflictor(
            match_id, player_slot, inflictor, value
        )   VALUES (?, ?, ?, ?)
"""

    damage_inflictor = p.get("damage_inflictor", {})
    if not damage_inflictor:
        return

    for key, value in damage_inflictor.items():
        cur.execute(sql, (id, slot, key, value))


# Populating damage_table
def pop_damage_table(id, p, slot, cur):
    sql = """
        INSERT OR IGNORE INTO damage(
            match_id, player_slot, victim, value
        ) VALUES (?, ?, ?, ?)
"""

    damage = p.get("damage", {})
    if not damage:
        return

    for key, value in damage.items():
        cur.execute(sql, (id, slot, key, value))


# Populating damage targets
def pop_damage_targets(id, p, slot, cur):
    sql = """
        INSERT OR IGNORE INTO damage_targets(
            match_id, player_slot, damage_source, damage_target, value
        ) VALUES(?, ?, ?, ?, ?)
"""

    damage_targets = p.get("damage_targets", {})

    if not damage_targets:
        return

    for source, target in damage_targets.items():
        for key, value in target.items():
            cur.execute(sql, (id, slot, source, key, value))


# Populating a ward/sentry placement or removal
def pop_ward(
    id, slot, type, seq, cur, x, y, 
    placed_time, has_left, removed_time, 
    attacker
):
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


# populating observers
def pop_observers(id, p, cur):

    slot = p.get("player_slot", 0)

    obs_log = p.get("obs_log", [])
    if not obs_log:
        return

    obs_left_log = p.get("obs_left_log", [])

    ward_type = "observer"

    for log_seq, obs in enumerate(obs_log):
        x = obs.get("x")
        y = obs.get("y")
        placed_time = obs.get("time", 0)

        if (
            log_seq < len(obs_left_log)
            and obs_left_log[log_seq].get("entityleft")
        ):

            has_left = 1
            attacker = obs_left_log[log_seq].get("attacker", 0)
            removed_time = obs_left_log[log_seq].get("time", 0)

        else:
            has_left = 0
            attacker = 0
            removed_time = 0

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


# Populating sentries
def pop_sentries(id, p, cur):

    slot = p.get("player_slot", 0)

    sen_log = p.get("sen_log", [])
    if not sen_log:
        return

    sen_left_log = p.get("sen_left_log", [])

    ward_type = "sentry"

    for log_seq, sen in enumerate(sen_log):
        x = sen.get("x")
        y = sen.get("y")
        placed_time = sen.get("time", 0)

        if (
            log_seq < len(sen_left_log)
            and sen_left_log[log_seq].get("entityleft")
        ):

            has_left = 1
            attacker = sen_left_log[log_seq].get("attacker", 0)
            removed_time = sen_left_log[log_seq].get("time", 0)

        else:
            has_left = 0
            attacker = 0
            removed_time = 0

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


# Populating hero hits (after parsing)
def pop_hero_hits(id, p, slot, cur):
    sql = '''
        INSERT OR IGNORE INTO hero_hits (
            match_id, player_slot, hit_source, hit_count
        ) VALUES (?, ?, ?, ?)
'''
    hero_hits = p.get("hero_hits", {})
    if not hero_hits:
        return
    
    for key, value in hero_hits.items():
        cur.execute(sql, (id, slot, key, value))


# Populating units killed (after parsing)
def pop_units_killed(id, p, slot, cur):
    sql = '''
        INSERT OR IGNORE INTO units_killed (
            match_id, player_slot, unit, count
        ) VALUES (?, ?, ?, ?)
'''
    units_killed = p.get("killed", {})
    if not units_killed:
        return
    
    for key, value in units_killed.items():
        cur.execute(sql, (id, slot, key, value))


# Populating purchase log (after parsing)
def pop_purchase_log(id, p, slot, cur):
    sql = '''
        INSERT OR IGNORE INTO purchase_log (
            match_id, player_slot, p_time, p_key
            ) VALUES (?, ?, ?, ?)
            '''
    purchase_log = p.get("purchase_log", [])
    for log in purchase_log:
        p_time = log.get("time", 0)
        p_key = log.get("key", "")
        cur.execute(sql, (id, slot, p_time, p_key))


# populating items uses
def pop_item_uses(id, p, slot, cur):
    sql = '''
        INSERT OR IGNORE INTO item_uses (
            match_id, player_slot, item, uses
        ) VALUES (?, ?, ?, ?)
'''
    item_uses = p.get("item_uses", {})
    if not item_uses:
        return
    
    for key, value in item_uses.items():
        cur.execute(sql, (id, slot, key, value))


# Populating ability uses
def pop_ability_uses(id, p, slot, cur):
    sql = '''
        INSERT OR IGNORE INTO ability_uses (
            match_id, player_slot, ability, use_count
        ) VALUES (?, ?, ?, ?)
'''
    ability_uses = p.get("ability_uses", {})
    if not ability_uses:
        return
    
    for key, value in ability_uses.items():
        cur.execute(sql, (id, slot, key, value))


# Populating ability targets
def pop_ability_targets(id, p, slot, cur):
    sql = '''
        INSERT OR IGNORE INTO ability_targets (
            match_id, player_slot, ability, target, count
        ) VALUES (?, ?, ?, ?, ?)
'''
    ability_targets = p.get("ability_targets", {})
    if not ability_targets:
        return
    
    for ability, target in ability_targets.items():
        for key, value in target.items():
            cur.execute(sql, (id, slot, ability, key, value))


# Pop neutral items history
def pop_neutral_items(id, p, slot, cur):
    sql = '''
        INSERT OR IGNORE INTO neutral_item_history (
            match_id, player_slot, time, item_neutral,
            item_enhancement
        ) VALUES (?, ?, ?, ?, ?)
'''
    neutral_items = p.get("neutral_item_history", [])
    if not neutral_items:
        return
    
    for item in neutral_items:
        item_name = item.get("item_neutral", "")
        item_enhancement = item.get(
            "item_neutral_enhancement", ""
            )
        item_time = item.get("time", 0)
        cur.execute(sql, (
            id, slot, item_time, item_name, 
            item_enhancement))
        

# populating player heals
def pop_player_heals(id, p, slot, cur):
    sql = '''
        INSERT OR IGNORE INTO heal (
            match_id, player_slot, healing_source, value
        ) VALUES (?, ?, ?, ?)
'''
    player_heals = p.get("healing", {})
    if not player_heals:
        return
    
    for key, value in player_heals.items():
        cur.execute(sql, (id, slot, key, value))


# Populating multi_kills
def pop_multi_kills(id, p, slot, cur):
    sql = '''
        INSERT OR IGNORE INTO multi_kills (
            match_id, player_slot, mult, count
        ) VALUES (?, ?, ?, ?)
'''
    multi_kills = p.get("multi_kills", {})
    if not multi_kills:
        return
    for key, value in multi_kills.items():
        cur.execute(sql, (id, slot, key, value))


# Populating kill_streaks
def pop_kill_streaks(id, p, slot, cur):
    sql = '''
        INSERT OR IGNORE INTO kill_streaks (
            match_id, player_slot, streak, count
        ) VALUES (?, ?, ?, ?)
'''
    kill_streaks = p.get("kill_streaks", {})
    if not kill_streaks:
        return
    for key, value in kill_streaks.items():
        cur.execute(sql, (id, slot, key, value))


# Popuating killed_by table
def pop_killed_by(id, p, slot, cur):
    sql = '''
        INSERT OR IGNORE INTO killed_by (
            match_id, player_slot, killer, deaths
        ) VALUES (?, ?, ?, ?)
'''
    killed_by = p.get("killed_by", {})
    if not killed_by:
        return
    for key, value in killed_by.items():
        cur.execute(sql, (id, slot, key, value))


# Populating player runes
def pop_runes(id, p, slot, cur):
    sql = '''
        INSERT OR IGNORE INTO player_ runes (
            match_id, player_slot, rune_id, rune_count
        ) VALUES (?, ?, ?, ?)
'''
    runes = p.get("runes", {})
    if not runes:
        return
    for key, value in runes.items():
        cur.execute(sql, (id, slot, key, value))


# Populating timings
def pop_timings(id, p, slot, cur):
    sql = '''
        INSERT OR IGNORE INTO timings (
            match_id, player_slot, time_sec, gold_t, xp_t,
            lh_t, dn_t
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
'''
    minutes = p.get("times", [])
    gold_t = p.get("gold_t", [])
    xp_t = p.get("xp_t", [])
    lh_t = p.get("lh_t", [])
    dn_t = p.get("dn_t", [])

    for i, time_sec in enumerate(minutes):

        if (i < len(gold_t) 
            and i < len(xp_t) 
            and i < len(lh_t)
            and i < len(dn_t)):

            cur.execute(sql, (
                id, slot, time_sec, 
                gold_t[i], xp_t[i], 
                lh_t[i], dn_t[i]))


# Populating gold reasons
def pop_gold_reasons(id, p, slot, cur):
    sql = '''
        INSERT OR IGNORE INTO gold_reasons (
            match_id, player_slot, reason, count
        ) VALUES (?, ?, ?, ?)
'''
    gold_reasons = p.get("gold_reasons", {})
    if not gold_reasons:
        return
    for key, value in gold_reasons.items():
        cur.execute(sql, (id, slot, key, value))


# Populating xp reasons
def pop_xp_reasons(id, p, slot, cur):
    sql = '''
        INSERT OR IGNORE INTO xp_reasons (
            match_id, player_slot, reason, count
        ) VALUES (?, ?, ?, ?)
'''
    xp_reasons = p.get("xp_reasons", {})
    if not xp_reasons:
        return
    for key, value in xp_reasons.items():
        cur.execute(sql, (id, slot, key, value))


# finalized pop parsed material
def pop_all_parsed(r, id, cur, conn):

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


