import os
import sqlite3


# creating new database dir
def create_database(my_id):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    new_dir = os.path.join(base_dir, 'data_bases')
    os.makedirs(new_dir, exist_ok=True)

    # creating/loading the database
    try:
        database = os.path.join(new_dir,f"{my_id}.db")
        conn = sqlite3.connect(database)
        conn.execute("PRAGMA foreign_keys = ON;")
        cur = conn.cursor()

        base_table(cur)
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

        conn.commit()

        return conn, cur
    
    except Exception as e:
        print('There was an error while loading/creating database: ', e)
        raise    

        
# wont need it anymore
def base_table(cur):
    cur.execute('''CREATE TABLE IF NOT EXISTS player_matches (
	match_id	INTEGER,
	game_mode	INTEGER,
	lobby_type	INTEGER,
                
	average_rank	INTEGER,
	party_size	INTEGER,
	start_time	INTEGER,
    duration      INTEGER,
                
    outcome       INTEGER,
    leaver_status INTEGER,
    
    dire_score     INTEGER,
    radiant_score  INTEGER,
    
    version  INTEGER,
    retries  INTEGER,
                
    unparsed_pop  INTEGER,
    parsed_pop    INTEGER,
    
	PRIMARY KEY(match_id)
)
''')


# creating stats table
def stats_table(cur):
    cur.execute('''CREATE TABLE IF NOT EXISTS players_stats (
	match_id	    INTEGER NOT NULL,
	account_id	    INTEGER,
	personaname	    TEXT,
	player_slot	    INTEGER NOT NULL,
	hero_id	        INTEGER,
	hero_name	    TEXT,
	hero_variant	INTEGER,
    buyback_count   INTEGER,
    predict_victory INTEGER,
    abandons        INTEGER,
                
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


# creating fights table
def fights_table(cur):
    cur.execute('''CREATE TABLE IF NOT EXISTS team_fights(
        match_id    INTEGER NOT NULL,
        tf_seq      INTEGER NOT NULL,
        start_time  INTEGER NOT NULL,
        end_time    INTEGER NOT NULL,
        deaths      INTEGER NOT NULL,
        duration    INTEGER NOT NULL,
    
    PRIMARY KEY (match_id, tf_seq),
                
    FOREIGN KEY (match_id) 
        REFERENCES player_matches(match_id) 
        ON DELETE CASCADE
)
''')
    

# creating fights players
def fights_players(cur):
    cur.execute(''' CREATE TABLE IF NOT EXISTS fight_players(
    match_id     INTEGER NOT NULL,
    tf_seq       INTEGER NOT NULL,
    player_slot  INTEGER NOT NULL,
             
    deaths      INTEGER NOT NULL DEFAULT 0,
    buybacks    INTEGER NOT NULL DEFAULT 0,
    damage      INTEGER NOT NULL DEFAULT 0,
    healing     INTEGER NOT NULL DEFAULT 0,
    gold_delta  INTEGER NOT NULL DEFAULT 0,
    xp_delta    INTEGER NOT NULL DEFAULT 0,
    xp_start    INTEGER,
    xp_end      INTEGER,
             
    PRIMARY KEY (match_id, tf_seq, player_slot),
             
    FOREIGN KEY (match_id, tf_seq)
        REFERENCES team_fights(match_id, tf_seq)
        ON DELETE CASCADE
)
''')


# storing fights actions 
def fights_actions(cur):
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


# creating/initiating objectives table
def objectives(cur):
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


# player actions
def player_actions(cur):
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
    

# max hero hit table
def max_hit(cur):
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
    

# damage recieved by raw source (different from who did dmg)
def damage_received(cur):
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


# damage taken
def damage_taken(cur):
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
    

# source of dmg output from the hero
def damage_inflictor(cur):
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
    

# wards
def ward_instances(cur):
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
    

# dmg done distribution
def damage(cur):
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
    

# dmg targets
def damage_targets(cur):
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
    

# hero hits
def hero_hits(cur):
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


# units killed
def units_killed(cur):
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


# purchase log
def purchase_log(cur):
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


# item uses
def item_uses(cur):
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


# ability uses
def ability_uses(cur):
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
    

# ability targets
def ability_targets(cur):
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
    

# Exp/Gold graph base
def xp_gold(cur):
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


# perma buffs table
def perma_buffs(cur):
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
    

# ability_upgrades
def ability_upgrades(cur):
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


# neutral items table
def neutral_item(cur):
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


# healing
def player_heals(cur):
    cur.execute(''' CREATE TABLE IF NOT EXISTS heal(
    match_id     INTEGER NOT NULL,
    player_slot  INTEGER NOT NULL,
    healing_source   INTEGER NOT NULL,
    value  INTEGER NOT NULL,
                
    PRIMARY KEY (match_id, player_slot, healing_source),
                
    FOREIGN KEY (match_id, player_slot)
        REFERENCES players_stats(match_id, player_slot)
        ON DELETE CASCADE
)
''')
    

# multi kills table
def multi_kills(cur):
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
    

# kill streaks
def kill_streaks(cur):
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
    

# killed by table
def killed_by(cur):
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
    

# runes taken by player
def player_runes(cur):
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
    

# timings
def timings(cur):
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
    

# benchmarks
def benchmarks(cur):
    cur.execute('''
    CREATE TABLE IF NOT EXISTS benchmarks(
    match_id     INTEGER NOT NULL,
    player_slot  INTEGER NOT NULL,
    
    raw_gold  INTEGER NOT NULL,
    pct_gold  REAL NOT NULL, 
                
    raw_xp  INTEGER NOT NULL,
    pct_xp  REAL NOT NULL,
                
    raw_lh  INTEGER NOT NULL,
    pct_lh  REAL NOT NULL,
                
    raw_kills  INTEGER NOT NULL,
    pct_kills  REAL NOT NULL,
                
    raw_hero_dmg  INTEGER NOT NULL,
    pct_hero_dmg  REAL NOT NULL,
                
    raw_heal  INTEGER NOT NULL,
    pct_heal  REAL NOT NULL,
                
    raw_tower_dmg  INTEGER NOT NULL,
    pct_tower_dmg  REAL NOT NULL,
                
    PRIMARY KEY (match_id, player_slot),
                
    FOREIGN KEY (match_id, player_slot)
        REFERENCES players_stats(match_id, player_slot)
        ON DELETE CASCADE
)
''')
    

# gold sources 'constants' table (It won't change)
def gold_constants(cur):
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


# gold reasons
def gold_reasons(cur):
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
    

# xp sources 'constants' table (it won't change)
def xp_constants(cur):
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


# xp sources
def xp_reasons(cur):
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


# runes 'constants' table (it won't change)
def rune_constants(cur):
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


# Please come back here later when you start sorting out stuff lil bro
def create_indices(cur):
    cur.execute("CREATE INDEX IF NOT EXISTS idx_players_stats_account ON players_stats(account_id)")

    cur.execute("CREATE INDEX IF NOT EXISTS idx_team_fights_match ON team_fights(match_id)")

    cur.execute("CREATE INDEX IF NOT EXISTS idx_tfp_match_slot ON fight_players(match_id, player_slot)")
                
    cur.execute("CREATE INDEX IF NOT EXISTS idx_tfp_match ON fight_players(match_id)")

    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_tfpa_tf "
        "ON fight_actions(match_id, tf_seq)"
    )

    cur.execute("CREATE INDEX IF NOT EXISTS idx_tfpa_lookup ON fight_actions(action_type, action_key)")
