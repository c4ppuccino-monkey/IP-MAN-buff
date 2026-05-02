import streamlit as st

# A list of heroes localized names (Axe, Abbadon ..etc to use )
def heroes_names_list(heroes_dicts):
    heroes_names = []
    for key, value in heroes_dicts.items():
        localized_name = value["localized_name"]
        heroes_names.append(localized_name)
    return sorted(heroes_names)


# A list of items names
def items_options_list(items_dicts):
    items = []

    for key, value in items_dicts.items():
        display_name = value.get("dname")
        item_id = value.get("id")

        if display_name:
            items.append({
                "key": key,
                "name": display_name,
                "id": item_id
                })
    return sorted(items, key=lambda item: item["name"])


# Acquiring heroes images and icons
def hero_img_loader(heroes_dicts, selected_hero):
    for key, value in heroes_dicts.items():
        if value["localized_name"] == selected_hero:
            img_path = value["img"]
            icon_path = value["icon"]
            hero_icon_url = f"https://cdn.cloudflare.steamstatic.com{icon_path}"
            hero_img_url = f"https://cdn.cloudflare.steamstatic.com{img_path}"
            return hero_img_url, hero_icon_url
    return None, None


# Aggregating statistics per hero
def hero_aggs(df):
    hero_stats = df.groupby("hero_localized_name").agg(
                matches_played=("hero_localized_name", "count"),
                average_kda=("kda", "mean"),
                average_net_worth=("net_worth", "mean"),
                highest_net_worth=("net_worth","max"),
                average_hero_damage=("hero_damage", "mean"),
                highest_hero_damage=("hero_damage", "max"),
                lowest_hero_damage=("hero_damage", "min"),
                average_tower_damage=("tower_damage", "mean"),
                highest_tower_damage=("tower_damage", "max"),
                wins=("win", "sum"),
            )
    hero_stats["win_rate"] = hero_stats["wins"]/hero_stats["matches_played"]*100
    hero_stats = hero_stats.sort_values("matches_played", ascending=False)
    hero_stats = hero_stats.reset_index()
    return hero_stats


# calculating the mean of a stat after excluding null
# returns the number of included matches, to point out discrepencies later on
def non_null_mean(df, column_name):
    values = df[column_name]
    values = values[values.notna()]

    matches_used = len(values)
    mean_value = values.mean()

    return mean_value, matches_used


# Filtering by stats with peers
def peer_stats(accounts):

    peer_options = [{"name": "None", "id": None}] + accounts
    peers_filter = st.selectbox(
            "Choose peer account", peer_options,
            format_func=lambda acc: F"{acc['name']} ({acc['id']})"
            if acc["id"] is not None
            else acc["name"],
            key = "peer_saved_account"
    )

    if peers_filter["id"] is None:
        return None
    else:
        return int(peers_filter["id"])
        

# Filter results by hero
def hero_filter(heroes_names):
    hero_filter = st.selectbox(
        "Choose a hero", ["All"] + heroes_names, key="hero_filter"
        )
    return hero_filter

# Checking if the item was in the inventory in post
# match stats
def inventory_items_filter(items):
    selected_item = st.selectbox(
        "Choose an item to filter by",
        [{"key":None, "name": "None", "id": None}] + items,
        format_func=lambda item: item["name"],
        key="inventory_item_filter"
    )
    return selected_item["id"]
    

# Items order filter
def item_order():
    # Filtering by items purchase order
    items_order_filter = st.selectbox(
        "Item order",
        ["Any", "Boots before Blink", "Blink before Boots"],
        key="item_order_filter"
    )
    if items_order_filter == "Any":
        first_item = None
        second_item = None
    elif items_order_filter == "Boots before Blink":
        first_item = "boots"
        second_item = "blink"
    else:
        first_item = "blink"
        second_item = "boots"

    return first_item, second_item


# Collecting all filters in one place
def all_filters(accounts, heroes_names, items, compare):
    with st.sidebar:
        st.subheader("Filters")
        parse_filter = st.selectbox(
        "Parse status",
        ["All", "Parsed", "Unparsed"],
        key="parse_filter"
        )

        # Filtering by result (win, lose)
        result_filter = st.selectbox(
            "Result", ["All", "Wins", "Losses"], key="result_filter")

        # Filtering by latest (n) number of matches 
        matches_filter = st.selectbox(
            "Latest number of matches",
            ["all", "200", "100", "10"],
            key="matches_filter")

        if compare == False:
            # Filtering by matches with (x) peer
            peer_id = peer_stats(accounts)
        else:
            peer_id = None

        # Filtering by hero
        filtered_hero = hero_filter(heroes_names)

        # Filtering by Blink-Boots sequence for my homie
        # IP MAN who always buys 'Blink' before 'Boots' <3
        

        # Item filter
        item = inventory_items_filter(items)

        filters = {
            "parse_filter": parse_filter,
            "result_filter": result_filter,
            "matches_filter": matches_filter,
            "peer_filter": peer_id,
            "hero_filter": filtered_hero,
            "item_order": item_order(),
            "item": item
        }
    
    return filters
