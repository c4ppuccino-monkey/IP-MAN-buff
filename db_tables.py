"""SQLite schema definitions and index setup for the Dota match analytics database."""

import os
import sqlite3
from logging_config import get_logger


logger = get_logger(__name__)


# Database bootstrap
def create_database():
    """Create or open the account-scoped SQLite database and initialize all schema objects."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    new_dir = os.path.join(base_dir, 'data_base')
    os.makedirs(new_dir, exist_ok=True)

    # Open (or create) the SQLite database file
    try:
        database = os.path.join(new_dir,f"database.db")
        conn = sqlite3.connect(database)
        conn.execute("PRAGMA foreign_keys = ON;")
        cur = conn.cursor()

        base_table(cur)
        account_matches_table(cur)
        stats_table(cur)

        fights_table(cur)
        fights_players(cur)
        fights_actions(cur)

        objectives(cur)
        max_hit(cur)
        xp_gold(cur)
        perma_buffs(cur)
        ability_upgrades(cur)
        neutral_item(cur)
        damage_received(cur)
        damage_taken(cur)
        damage_inflictor(cur)
        damage(cur)
        damage_targets(cur)
        ability_uses(cur)
        ability_targets(cur)
        hero_hits(cur)
        multi_kills(cur)
        kill_streaks(cur)
        killed_by(cur)
        player_actions(cur)
        ward_instances(cur)
        units_killed(cur)
        purchase_log(cur)
        item_uses(cur)
        player_heals(cur)
        player_runes(cur)
        timings(cur)
        benchmarks(cur)

        gold_constants(cur)
        xp_constants(cur)
        rune_constants(cur)

        xp_reasons(cur)
        gold_reasons(cur)

        create_indices(cur)

        conn.commit()
        logger.info("Database initialized successfully. path=%s", database)

        return conn, cur
    
    except Exception:
        logger.exception("Failed to initialize database.")
        raise

        
# Core match table
def base_table(cur):
    """Create the per-match summary table used as the parent for match-scoped data."""
    cur.execute('''CREATE TABLE IF NOT EXISTS player_matches (
		match_id	INTEGER,
		game_mode	INTEGER,
		lobby_type	INTEGER,
	                
		average_rank	INTEGER,
		start_time	INTEGER,
	    duration      INTEGER,
	                
	    dire_score     INTEGER,
	    radiant_score  INTEGER,
	    
	    patch    INTEGER,
	    version  INTEGER,
	    retries  INTEGER,
                
    unparsed_pop  INTEGER,
    parsed_pop    INTEGER,
    
	PRIMARY KEY(match_id)
)
''')


def account_matches_table(cur):
    """Create account-scoped match metadata from /players/{account_id}/matches."""
    cur.execute('''
    CREATE TABLE IF NOT EXISTS account_matches (
        account_id     INTEGER NOT NULL,
        match_id       INTEGER NOT NULL,
        player_slot    INTEGER,
        party_size     INTEGER,
        outcome        INTEGER,
        leaver_status  INTEGER,

        PRIMARY KEY (account_id, match_id),

        FOREIGN KEY (match_id)
            REFERENCES player_matches(match_id)
            ON DELETE CASCADE
    )
''')


# Per-player stats table
def stats_table(cur):
    """Create the per-player core stats table for each match and player slot."""
    cur.execute('''CREATE TABLE IF NOT EXISTS players_stats (
	match_id	    INTEGER NOT NULL,
	account_id	    INTEGER,
	personaname	    TEXT,
	player_slot	    INTEGER NOT NULL,
	hero_id	        INTEGER,
	hero_name	    TEXT,
    hero_localized_name TEXT,
	hero_variant	INTEGER,
    facet_name      TEXT,
    buyback_count   INTEGER,
    predict_victory INTEGER,
    abandons        INTEGER,
    leaver_status   INTEGER,
                
    obs_placed          INTEGER,
    sentries_placed     INTEGER,
    creeps_stacked      INTEGER,
    camps_stacked       INTEGER,
    rune_pickups        INTEGER,
    firstblood_claimed  INTEGER,
                
    team_fight_participation   REAL,         
    stuns                      REAL,
    
    lane                  INTEGER,
    lane_role             INTEGER,
    lane_efficiency       REAL,
    lane_efficiency_pct   REAL,
                
    lane_kills        INTEGER,
    neutral_kills     INTEGER,
    ancient_kills     INTEGER,
    roshan_kills      INTEGER,
    necronomicon      INTEGER,
    courier_kills     INTEGER,
    hero_kills        INTEGER,
    tower_kills       INTEGER,
    observer_kills    INTEGER,
    sentry_kills      INTEGER,
    
    sentry_uses     INTEGER,
    observer_uses   INTEGER,
                 
	item_0	TEXT,
	item_1	TEXT,
	item_2	TEXT,
	item_3	TEXT,
	item_4	TEXT,
	item_5	TEXT,
                
	backpack_0	TEXT,
	backpack_1	TEXT,
	backpack_2	TEXT,
                
	item_neutral	TEXT,
	item_neutral2	TEXT,
                
	kills	       INTEGER,
    kills_per_min  REAL,
    kda            REAL,
    
	deaths	      INTEGER,
	assists	      INTEGER,
	last_hits	  INTEGER,
	denies	      INTEGER,
    
    total_gold    INTEGER,
	gold_per_min  INTEGER,
    gold          INTEGER,
    gold_spent    INTEGER,
    total_xp      INTEGER,
	xp_per_min	  INTEGER,
	level	      INTEGER,
	net_worth	  INTEGER,
                
	aghanims_scepter	INTEGER,
	aghanims_shard	    INTEGER,
	moonshard	        INTEGER,
                
	hero_damage	    INTEGER,
	tower_damage	INTEGER,
                
	isRadiant	    INTEGER,
	radiant_win	    INTEGER,

    hero_healing   INTEGER,          
	calculated_kda	REAL,
	win	            INTEGER,
	lose	        INTEGER,
                
	PRIMARY KEY (match_id, player_slot),
    FOREIGN KEY (match_id) REFERENCES player_matches(match_id)
        ON DELETE CASCADE
)
''')


# Teamfight summary table
def fights_table(cur):
    """Create the team fight summary table keyed by match and teamfight sequence."""
    cur.execute('''CREATE TABLE IF NOT EXISTS team_fights(
        match_id    INTEGER NOT NULL,
        tf_seq      INTEGER NOT NULL,
        start_time  INTEGER,
        end_time    INTEGER,
        deaths      INTEGER,
        duration    INTEGER,
    
    PRIMARY KEY (match_id, tf_seq),
                
    FOREIGN KEY (match_id) 
        REFERENCES player_matches(match_id) 
        ON DELETE CASCADE
)
''')
    

# Teamfight player table
def fights_players(cur):
    """Create per-player rows for each recorded team fight."""
    cur.execute(''' CREATE TABLE IF NOT EXISTS fight_players(
    match_id     INTEGER NOT NULL,
    tf_seq       INTEGER NOT NULL,
    player_slot  INTEGER NOT NULL,
             
    deaths      INTEGER,
    buybacks    INTEGER,
    damage      INTEGER,
    healing     INTEGER,
    gold_delta  INTEGER,
    xp_delta    INTEGER,
    xp_start    INTEGER,
    xp_end      INTEGER,
             
    PRIMARY KEY (match_id, tf_seq, player_slot),
             
    FOREIGN KEY (match_id, tf_seq)
        REFERENCES team_fights(match_id, tf_seq)
        ON DELETE CASCADE
)
''')


# Teamfight action aggregates table
def fights_actions(cur):
    """Create the normalized action table for ability and item usage inside team fights."""
    cur.execute(''' CREATE TABLE IF NOT EXISTS fight_actions(
    match_id       INTEGER NOT NULL, 
    tf_seq         INTEGER NOT NULL,
    player_slot    INTEGER NOT NULL,
    
    action_type    TEXT NOT NULL,
    action_key     TEXT NOT NULL,
    action_value   INTEGER,
    
    PRIMARY KEY (match_id, tf_seq, player_slot, 
                action_type, action_key),
                
    FOREIGN KEY (match_id, tf_seq) 
        REFERENCES team_fights(match_id, tf_seq) 
        ON DELETE CASCADE
)
''')


# Match objectives table
def objectives(cur):
    """Create the match objectives table for towers, roshan, and other objective events."""
    cur.execute(''' CREATE TABLE IF NOT EXISTS objectives(
    match_id  INTEGER NOT NULL,
    time      INTEGER NOT NULL,

    objective_id INTEGER NOT NULL,

    objective_type TEXT,
    key            TEXT,
    unit           TEXT,
    slot           INTEGER,
    player_slot    INTEGER,

    PRIMARY KEY (match_id, objective_id),
    FOREIGN KEY (match_id)
        REFERENCES player_matches(match_id)
        ON DELETE CASCADE
)
''')


# Player action counts table
def player_actions(cur):
    """Create aggregated action counts per player per match."""
    cur.execute('''
    CREATE TABLE IF NOT EXISTS player_actions(
        match_id     INTEGER NOT NULL,
        player_slot  INTEGER NOT NULL,
        action_id    INTEGER NOT NULL,
        count        INTEGER NOT NULL,
                
        PRIMARY KEY (match_id, player_slot, action_id),
        
        FOREIGN KEY (match_id, player_slot)
            REFERENCES players_stats(match_id, player_slot)
            ON DELETE CASCADE
)                
''')
    

# Maximum hero hit table
def max_hit(cur):
    """Create table for each player's maximum hero hit metadata."""
    cur.execute(''' CREATE TABLE IF NOT EXISTS max_hit(
    match_id     INTEGER,
    player_slot  INTEGER,
                
    type      TEXT NOT NULL,
    time      INTEGER NOT NULL,
    highest   INTEGER NOT NULL,
    inflictor TEXT NOT NULL,
    unit      TEXT NOT NULL,
    key       TEXT NOT NULL,
    value     INTEGER NOT NULL,
    
    PRIMARY KEY (match_id, player_slot, type),
    FOREIGN KEY (match_id, player_slot)
        REFERENCES players_stats(match_id, player_slot)
        ON DELETE CASCADE
)
''')
    

# Incoming damage by raw source table
def damage_received(cur):
    """Create table for incoming damage grouped by raw source."""
    cur.execute(''' CREATE TABLE IF NOT EXISTS damage_inflictor_received(
    match_id      INTEGER NOT NULL,
    player_slot   INTEGER NOT NULL,
    
    source  TEXT NOT NULL,
    value   INTEGER NOT NULL,
    
    PRIMARY KEY (match_id, player_slot, source),
    
    FOREIGN KEY (match_id, player_slot)
        REFERENCES players_stats(match_id, player_slot)
        ON DELETE CASCADE
)
''')


# Damage taken table
def damage_taken(cur):
    """Create table for damage taken grouped by damage source category."""
    cur.execute('''
    CREATE TABLE IF NOT EXISTS damage_taken(
        match_id     INTEGER NOT NULL,
        player_slot  INTEGER NOT NULL,
        dmg_source   TEXT NOT NULL,
        value        INTEGER NOT NULL,
                
        PRIMARY KEY (match_id, player_slot, dmg_source),
        FOREIGN KEY (match_id, player_slot)
            REFERENCES players_stats(match_id, player_slot)
            ON DELETE CASCADE
)
''')
    

# Outgoing damage by inflictor table
def damage_inflictor(cur):
    """Create table for outgoing damage grouped by inflictor/ability source."""
    cur.execute('''
    CREATE TABLE IF NOT EXISTS damage_inflictor(
        match_id     INTEGER NOT NULL,
        player_slot  INTEGER NOT NULL,
        inflictor    TEXT NOT NULL,
        value        INTEGER NOT NULL,
        
        PRIMARY KEY (match_id, player_slot, inflictor),
        FOREIGN KEY (match_id, player_slot)
            REFERENCES players_stats(match_id, player_slot)
            ON DELETE CASCADE
)            
''')
    

# Ward events table
def ward_instances(cur):
    """Create table for observer and sentry placement/removal events."""
    cur.execute('''
    CREATE TABLE IF NOT EXISTS ward_instances (
        match_id      INTEGER NOT NULL,
        player_slot   INTEGER NOT NULL,

        ward_type     TEXT NOT NULL,      
        ward_seq      INTEGER NOT NULL,  

        x             INTEGER NOT NULL,
        y             INTEGER NOT NULL,

        placed_time   INTEGER NOT NULL,
        has_left      INTEGER NOT NULL,
        removed_time  INTEGER,      
        attacker_name TEXT,     

        PRIMARY KEY (match_id, player_slot, ward_type, ward_seq),

        FOREIGN KEY (match_id, player_slot)
            REFERENCES players_stats(match_id, player_slot)
            ON DELETE CASCADE
)
''')
    

# Total damage done to targets regarless of the dmg source
def damage(cur):
    """Create table for outgoing damage grouped by victim."""
    cur.execute('''
    CREATE TABLE IF NOT EXISTS damage(
        match_id      INTEGER NOT NULL,
        player_slot   INTEGER NOT NULL,
        victim        TEXT NOT NULL,
        value         INTEGER NOT NULL,
                
        PRIMARY KEY (match_id, player_slot, victim),
        FOREIGN KEY (match_id, player_slot)
            REFERENCES players_stats(match_id, player_slot)
            ON DELETE CASCADE
                )        
''')
    

# Damage source-to-target table
def damage_targets(cur):
    """Create table for source-to-target damage distributions."""
    cur.execute('''
    CREATE TABLE IF NOT EXISTS damage_targets(
        match_id     INTEGER NOT NULL,
        player_slot  INTEGER NOT NULL,
                
        damage_source  TEXT NOT NULL,
        damage_target  TEXT NOT NULL,
        value          INTEGER NOT NULL,
        
        PRIMARY KEY (match_id, player_slot, damage_source, damage_target),
                
        FOREIGN KEY (match_id, player_slot)
            REFERENCES players_stats(match_id, player_slot)
            ON DELETE CASCADE            
)    
''')
    

# Hero hit counts table
def hero_hits(cur):
    """Create table for hit counts grouped by hit source."""
    cur.execute('''
    CREATE TABLE IF NOT EXISTS hero_hits(
        match_id     INTEGER NOT NULL,
        player_slot  INTEGER NOT NULL,
        hit_source   TEXT NOT NULL,
        hit_count    INTEGER NOT NULL,
        
        PRIMARY KEY (match_id, player_slot, hit_source),
                
        FOREIGN KEY (match_id, player_slot)
            REFERENCES players_stats(match_id, player_slot)
            ON DELETE CASCADE
)
''')


# Units killed table
def units_killed(cur):
    """Create table for unit kill counts per player."""
    cur.execute('''
    CREATE TABLE IF NOT EXISTS units_killed(
        match_id     INTEGER NOT NULL,
        player_slot  INTEGER NOT NULL,
        unit      TEXT NOT NULL,
        count     INTEGER NOT NULL,
     
        PRIMARY KEY (match_id, player_slot, unit),
        
        FOREIGN KEY (match_id, player_slot)
            REFERENCES players_stats(match_id, player_slot)
            ON DELETE CASCADE
)   
''')


# Purchase timeline table
def purchase_log(cur):
    """Create table for item purchase timeline events per player."""
    cur.execute('''
    CREATE TABLE IF NOT EXISTS purchase_log(
        match_id     INTEGER NOT NULL,
        player_slot  INTEGER NOT NULL,
        
        p_time   INTEGER NOT NULL,
        p_key    TEXT NOT NULL,
        
        PRIMARY KEY (match_id, player_slot, p_time, p_key),
            
        FOREIGN KEY (match_id, player_slot)
            REFERENCES players_stats(match_id, player_slot)
            ON DELETE CASCADE
)                 
''')


# Item usage table
def item_uses(cur):
    """Create table for aggregate item usage counts per player."""
    cur.execute('''
    CREATE TABLE IF NOT EXISTS item_uses(
        match_id     INTEGER NOT NULL,
        player_slot  INTEGER NOT NULL,
        item         TEXT NOT NULL,
        uses         INTEGER NOT NULL,
     
        PRIMARY KEY (match_id, player_slot, item),
        
        FOREIGN KEY (match_id, player_slot)
            REFERENCES players_stats(match_id, player_slot)
            ON DELETE CASCADE
)   
''')


# Ability usage table
def ability_uses(cur):
    """Create table for aggregate ability usage counts per player."""
    cur.execute('''
    CREATE TABLE IF NOT EXISTS ability_uses(
        match_id     INTEGER NOT NULL,
        player_slot  INTEGER NOT NULL,
        ability      TEXT NOT NULL,
        use_count    INTEGER NOT NULL,
     
        PRIMARY KEY (match_id, player_slot, ability),
        
        FOREIGN KEY (match_id, player_slot)
            REFERENCES players_stats(match_id, player_slot)
            ON DELETE CASCADE
)   
''')
    

# Ability target distribution table
def ability_targets(cur):
    """Create table for ability target distributions per player."""
    cur.execute('''
    CREATE TABLE IF NOT EXISTS ability_targets(
        match_id      INTEGER NOT NULL,
        player_slot   INTEGER NOT NULL,

        ability         TEXT NOT NULL,
        target          TEXT NOT NULL,
        count           INTEGER NOT NULL,
                
        PRIMARY KEY (match_id, player_slot, ability, target),
            
        FOREIGN KEY (match_id, player_slot)
            REFERENCES players_stats(match_id, player_slot)
            ON DELETE CASCADE
)                
''')
    

# Radiant advantage timeline table
def xp_gold(cur):
    """Create minute-by-minute radiant gold and XP advantage table."""
    cur.execute(''' CREATE TABLE IF NOT EXISTS radiant_adv(
    match_id INTEGER NOT NULL,
    minute   INTEGER NOT NULL,
    
    radiant_gold_adv INTEGER,
    radiant_xp_adv   INTEGER,
    
    PRIMARY KEY (match_id, minute),
                
    FOREIGN KEY (match_id) 
        REFERENCES player_matches(match_id) 
        ON DELETE CASCADE
)
''')


# Permanent buffs table
def perma_buffs(cur):
    """Create table for permanent buffs and stack counts per player."""
    cur.execute(''' CREATE TABLE IF NOT EXISTS perma_buffs(
    match_id    INTEGER NOT NULL,
    player_slot INTEGER NOT NULL,
    
    buff_id     INTEGER NOT NULL,
    stack_count INTEGER NOT NULL,
    grant_time  INTEGER,
    
    PRIMARY KEY (match_id, player_slot, buff_id),
                
    FOREIGN KEY (match_id, player_slot)
        REFERENCES players_stats(match_id, player_slot) 
        ON DELETE CASCADE                
)
''')
    

# Ability upgrades timeline table
def ability_upgrades(cur):
    """Create table for ordered ability upgrade progression per player."""
    cur.execute(''' CREATE TABLE IF NOT EXISTS ability_upgrades(
    match_id     INTEGER NOT NULL,
    player_slot  INTEGER NOT NULL,
    seq          INTEGER NOT NULL,
    ability_id   INTEGER NOT NULL,
    
    PRIMARY KEY (match_id, player_slot, seq),
    
    FOREIGN KEY (match_id, player_slot) 
        REFERENCES players_stats(match_id, player_slot) 
        ON DELETE CASCADE
)
''')


# Neutral item history table
def neutral_item(cur):
    """Create table for neutral item history timeline entries per player."""
    cur.execute(''' CREATE TABLE IF NOT EXISTS neutral_item_history(
    match_id      INTEGER NOT NULL,
    player_slot   INTEGER NOT NULL,
                
    time               INTEGER NOT NULL,
    item_neutral       TEXT,
    item_enhancement   TEXT,
    
    PRIMARY KEY (match_id, player_slot, time),
                
    FOREIGN KEY (match_id, player_slot)
        REFERENCES players_stats(match_id, player_slot)
        ON DELETE CASCADE
)
''')


# Healing table
def player_heals(cur):
    """Create table for healing contribution grouped by healing source."""
    cur.execute(''' CREATE TABLE IF NOT EXISTS heal(
    match_id     INTEGER NOT NULL,
    player_slot  INTEGER NOT NULL,
    healing_source    TEXT NOT NULL,
    value  INTEGER NOT NULL,
                
    PRIMARY KEY (match_id, player_slot, healing_source),
                
    FOREIGN KEY (match_id, player_slot)
        REFERENCES players_stats(match_id, player_slot)
        ON DELETE CASCADE
)
''')
    

# Multi-kill frequency table
def multi_kills(cur):
    """Create table for multi-kill frequency per player."""
    cur.execute(''' 
    CREATE TABLE IF NOT EXISTS multi_kills (
        match_id     INTEGER NOT NULL,
        player_slot  INTEGER NOT NULL,
                
        mult   INTEGER NOT NULL,
        count  INTEGER NOT NULL,
        
        PRIMARY KEY (match_id, player_slot, mult),
        
        FOREIGN KEY (match_id, player_slot)
            REFERENCES players_stats(match_id, player_slot)
            ON DELETE CASCADE
)
''')
    

# Kill streak frequency table
def kill_streaks(cur):
    """Create table for kill streak frequency per player."""
    cur.execute('''
    CREATE TABLE IF NOT EXISTS kill_streaks(
        match_id     INTEGER NOT NULL,
        player_slot  INTEGER NOT NULL,
        streak       INTEGER NOT NULL,
        count        INTEGER NOT NULL,
        
        PRIMARY KEY (match_id, player_slot, streak),
            
        FOREIGN KEY (match_id, player_slot)
            REFERENCES players_stats(match_id, player_slot)
            ON DELETE CASCADE
)
''')
    

# Killed-by table
def killed_by(cur):
    """Create table for deaths grouped by killer identity."""
    cur.execute('''
    CREATE TABLE IF NOT EXISTS killed_by(
        match_id    INTEGER NOT NULL,
        player_slot INTEGER NOT NULL,
        killer      TEXT NOT NULL,
        deaths      INTEGER NOT NULL,
                
        PRIMARY KEY (match_id, player_slot, killer),
                
        FOREIGN KEY (match_id, player_slot)
            REFERENCES players_stats(match_id, player_slot)
            ON DELETE CASCADE
)       
''')
    

# Player rune counts table
def player_runes(cur):
    """Create table for rune pickup counts by rune type per player."""
    cur.execute('''
    CREATE TABLE IF NOT EXISTS player_runes(
        match_id      INTEGER NOT NULL,
        player_slot   INTEGER NOT NULL,
        rune_id       INTEGER NOT NULL,
        rune_count    INTEGER NOT NULL,
        
        PRIMARY KEY (match_id, player_slot, rune_id),
        FOREIGN KEY (match_id, player_slot)
            REFERENCES players_stats(match_id, player_slot)
            ON DELETE CASCADE
)                
''')
    

# Timeline progression table
def timings(cur):
    """Create table for per-minute progression arrays (gold/xp/lh/denies)."""
    cur.execute('''
    CREATE TABLE IF NOT EXISTS timings(
        match_id     INTEGER NOT NULL,
        player_slot  INTEGER NOT NULL,
        time_sec     INTEGER NOT NULL,
        gold_t       INTEGER NOT NULL,
        xp_t         INTEGER NOT NULL,
        lh_t         INTEGER NOT NULL,
        dn_t         INTEGER NOT NULL,
                
        PRIMARY KEY (match_id, player_slot, time_sec),
                
        FOREIGN KEY (match_id, player_slot)
            REFERENCES players_stats(match_id, player_slot)
            ON DELETE CASCADE
)                
''')
    

# Benchmarks table
def benchmarks(cur):
    """Create table for benchmark raw values and percentiles per player."""
    cur.execute('''
    CREATE TABLE IF NOT EXISTS benchmarks(
    match_id     INTEGER NOT NULL,
    player_slot  INTEGER NOT NULL,
    
    raw_gold  INTEGER,
    pct_gold  REAL, 
                
    raw_xp  INTEGER,
    pct_xp  REAL,
                
    raw_lh  INTEGER,
    pct_lh  REAL,
                
    raw_kills  INTEGER,
    pct_kills  REAL,
                
    raw_hero_dmg  INTEGER,
    pct_hero_dmg  REAL,
                
    raw_heal  INTEGER,
    pct_heal  REAL,
                
    raw_tower_dmg  INTEGER,
    pct_tower_dmg  REAL,
                
    PRIMARY KEY (match_id, player_slot),
                
    FOREIGN KEY (match_id, player_slot)
        REFERENCES players_stats(match_id, player_slot)
        ON DELETE CASCADE
)
''')
    

# Gold reason constants table
def gold_constants(cur):
    """Create and seed static lookup values for gold reason codes."""
    cur.execute(''' CREATE TABLE IF NOT EXISTS gold_constants(
    id  INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
)
''')
    
    data = [
        (0,  'unspecified'),
        (1,  'hero_kill'),
        (2,  'creep_kill'),
        (3,  'lane_creep'),
        (4,  'jungle_creep'),
        (5,  'roshan'),
        (6,  'tower'),
        (7,  'hero_assist'),
        (8,  'bounty_rune'),
        (9,  'courier_kill'),
        (10, 'secret_shop'),
        (11, 'buyback_refund'),
        (12, 'ability_gold'),
        (13, 'ward_kill'),
        (14, 'building'),
        (15, 'other')
    ]

    cur.executemany(''' INSERT OR IGNORE INTO gold_constants (id, name)
                    VALUES(?, ?)
                    ''', data)


# Gold reasons table
def gold_reasons(cur):
    """Create table for gold reason counts per player."""
    cur.execute('''
    CREATE TABLE IF NOT EXISTS gold_reasons(
        match_id     INTEGER NOT NULL,
        player_slot  INTEGER NOT NULL,
        reason       INTEGER NOT NULL,
        count        INTEGER NOT NULL,
     
        PRIMARY KEY (match_id, player_slot, reason),
        
        FOREIGN KEY (match_id, player_slot)
            REFERENCES players_stats(match_id, player_slot)
            ON DELETE CASCADE
)   
''')
    

# XP reason constants table
def xp_constants(cur):
    """Create and seed static lookup values for XP reason codes."""
    cur.execute('''
    CREATE TABLE IF NOT EXISTS xp_constants(
        id   INTEGER PRIMARY KEY,
        name TEXT NOT NULL UNIQUE
    )
    ''')

    data = [
        (0,  'unspecified'),
        (1,  'hero_kill'),
        (2,  'creep_kill'),
        (3,  'lane_creep'),
        (4,  'jungle_creep'),
        (5,  'roshan'),
        (6,  'tower'),
        (7,  'hero_assist'),
        (8,  'tome_of_knowledge'),
        (9,  'outpost'),
        (10, 'experience_rune'),
        (11, 'buyback'),
        (12, 'ability_xp'),
        (13, 'other')
    ]

    cur.executemany('''
        INSERT OR IGNORE INTO xp_constants (id, name)
        VALUES (?, ?)
    ''', data)


# XP reasons table
def xp_reasons(cur):
    """Create table for XP reason counts per player."""
    cur.execute('''
    CREATE TABLE IF NOT EXISTS xp_reasons(
        match_id     INTEGER NOT NULL,
        player_slot  INTEGER NOT NULL,
        reason       INTEGER NOT NULL,
        count        INTEGER NOT NULL,
     
        PRIMARY KEY (match_id, player_slot, reason),
        
        FOREIGN KEY (match_id, player_slot)
            REFERENCES players_stats(match_id, player_slot)
            ON DELETE CASCADE
)   
''')


# Rune constants table
def rune_constants(cur):
    """Create and seed static lookup values for rune IDs."""
    cur.execute("""
    CREATE TABLE IF NOT EXISTS rune_constants (
        id   INTEGER PRIMARY KEY,
        name TEXT NOT NULL UNIQUE
    );
    """)

    data = [
        (0, 'double_damage'),
        (1, 'haste'),
        (2, 'illusion'),
        (3, 'invisibility'),
        (4, 'regeneration'),
        (5, 'bounty'),
        (6, 'arcane'),
        (7, 'water'),
        (8, 'wisdom'),
        (9, 'shield')
    ]

    cur.executemany("""
        INSERT OR IGNORE INTO rune_constants (id, name)
        VALUES (?, ?)
    """, data)


# Secondary indexes for common analytics queries
def create_indices(cur):
    """Create non-primary indexes that speed up common dashboard and analytics queries."""
    statements = [
        # Core match browsing / status checks
        "CREATE INDEX IF NOT EXISTS idx_player_matches_time ON player_matches(start_time)",
        "CREATE INDEX IF NOT EXISTS idx_player_matches_pop_state ON player_matches(parsed_pop, unparsed_pop)",
        "CREATE INDEX IF NOT EXISTS idx_player_matches_mode_rank ON player_matches(game_mode, average_rank)",
        "CREATE INDEX IF NOT EXISTS idx_account_matches_match ON account_matches(match_id)",
        "CREATE INDEX IF NOT EXISTS idx_account_matches_outcome ON account_matches(account_id, outcome)",

        # Player-level filters and joins
        "CREATE INDEX IF NOT EXISTS idx_players_stats_account ON players_stats(account_id)",
        "CREATE INDEX IF NOT EXISTS idx_players_stats_hero ON players_stats(hero_id)",
        "CREATE INDEX IF NOT EXISTS idx_players_stats_match_hero ON players_stats(match_id, hero_id)",
        "CREATE INDEX IF NOT EXISTS idx_players_stats_kda ON players_stats(kda)",

        # Teamfight views
        "CREATE INDEX IF NOT EXISTS idx_team_fights_match_start ON team_fights(match_id, start_time)",
        "CREATE INDEX IF NOT EXISTS idx_tfp_match_slot ON fight_players(match_id, player_slot)",
        "CREATE INDEX IF NOT EXISTS idx_tfpa_tf ON fight_actions(match_id, tf_seq)",
        "CREATE INDEX IF NOT EXISTS idx_tfpa_lookup ON fight_actions(action_type, action_key)",

        # Timeline / event-heavy views
        "CREATE INDEX IF NOT EXISTS idx_objectives_match_time ON objectives(match_id, time)",
        "CREATE INDEX IF NOT EXISTS idx_radiant_adv_match_minute ON radiant_adv(match_id, minute)",
        "CREATE INDEX IF NOT EXISTS idx_purchase_log_match_slot_time ON purchase_log(match_id, player_slot, p_time)",
        "CREATE INDEX IF NOT EXISTS idx_ward_match_slot_type_time ON ward_instances(match_id, player_slot, ward_type, placed_time)",
        "CREATE INDEX IF NOT EXISTS idx_upgrades_match_slot_seq ON ability_upgrades(match_id, player_slot, seq)",
        "CREATE INDEX IF NOT EXISTS idx_timings_match_slot_time ON timings(match_id, player_slot, time_sec)",

        # Lookup/distribution tables
        "CREATE INDEX IF NOT EXISTS idx_item_uses_item ON item_uses(item)",
        "CREATE INDEX IF NOT EXISTS idx_ability_uses_ability ON ability_uses(ability)",
        "CREATE INDEX IF NOT EXISTS idx_hero_hits_source ON hero_hits(hit_source)",
        "CREATE INDEX IF NOT EXISTS idx_damage_targets_source_target ON damage_targets(damage_source, damage_target)",
    ]

    for stmt in statements:
        cur.execute(stmt)
