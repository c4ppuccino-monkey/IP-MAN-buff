import db_tables as table
import db_population as popul
import maps 
import actions


# player's id
account_id = "1530751344"

actions.sync_repo()

# calling the important maps jsons
heroes_map = maps.load_heroes()
abilities_map = maps.load_hero_abilities()
items_map = maps.load_items()
ancients_map = maps.load_ancients()
aghs_map = maps.load_aghs_desc()
orders_map = maps.load_order_types()
perma_map = maps.load_perma_buffs()

# connecting/creating db
conn, cur = table.create_database(account_id)


# redundant shit
all_matches = actions.fetch_matches(account_id)
known_matches = actions.check_match_id(cur)
all_matches_ids = actions.get_match_id(all_matches)
new_ids = actions.new_ids(known_matches, all_matches_ids)

popul.populate_base_table(all_matches, cur, conn)

select_matches_ids = actions.select_matches(cur)

actions.main_pop(cur, conn, select_matches_ids)

conn.close()

