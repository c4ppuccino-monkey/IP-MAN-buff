"""Load and transform Dota constants into lightweight lookup dictionaries."""

import json
from pathlib import Path

repo_path = Path("dotaconstants")
json_dir = repo_path/"build"
required_constant_files = [
    "heroes.json",
    "items.json",
    "hero_abilities.json",
]


def missing_constant_files():
    """Return required dotaconstants JSON files that are not available locally."""
    missing = []
    for filename in required_constant_files:
        path = json_dir / filename
        if not path.exists():
            missing.append(str(path))

    return missing


def constants_available():
    """Return True when the Streamlit app can load the required Dota constants."""
    return not missing_constant_files()

# Load hero constants
def load_heroes():
    """Load hero constants and return a hero ID -> localized name mapping."""
    heroes_path = json_dir/ "heroes.json"
    try:
        with open(heroes_path,"r") as f:
            heroes = json.load(f)
        return heroes
    except FileNotFoundError:
        print(f'The file {heroes_path} not found, make sure the file exists in the right dir')
        raise


# Load item constants
def load_items():
    """Load item constants and return an item ID -> item name mapping."""
    items_path = json_dir/ "items.json"
    try:
        with open(items_path, "r") as f:
            items = json.load(f)
        return items
    except FileNotFoundError:
        print(f"The file {items_path} was not found, make sure it was downloaded correctly and in the correct dir")
        raise


# Load hero ability and facet constants
def load_hero_abilities():
    """Load hero ability metadata for facet and ability resolution."""
    abilities_path = json_dir/ "hero_abilities.json"
    try:
        with open(abilities_path, "r") as f:
            abilities = json.load(f)
        return abilities
    except FileNotFoundError:
        print(f"The file {abilities_path} was not found, make sure it was downloaded correctly and in the correct dir")
        raise


# Load ancients constants
def load_ancients():
    """Load ancient creep constants for neutral unit lookups."""
    ancients_path = json_dir/ "ancients.json"
    try:
        with open(ancients_path, "r") as f:
            ancients = json.load(f)
        return ancients
    except FileNotFoundError:
        print(f"The file {ancients_path} was not found, make sure it was downloaded correctly and in the correct dir")
        raise

# Load Aghanim's descriptions
def load_aghs_desc():
    """Load Aghanim's upgrade descriptions by ability."""
    aghs_path = json_dir/ "aghs_desc.json"
    try:
        with open(aghs_path, "r") as f:
            aghs_desc = json.load(f)
        return aghs_desc
    except FileNotFoundError:
        print(f"The file {aghs_path} was not found, make sure it was downloaded correctly and in the correct dir")
        raise


# Load order type constants
def load_order_types():
    """Load order/action type constants used in action decoding."""
    order_path = json_dir/ "order_types.json"
    try:
        with open(order_path, "r") as f:
            order_types = json.load(f)
        return order_types
    except FileNotFoundError:
        print(f"The file {order_path} was not found, make sure it was downloaded correctly and in the correct dir")
        raise


# Load permanent buff constants
def load_perma_buffs():
    """Load permanent buff constants used in buff decoding."""
    buffs_path = json_dir/ "permanent_buffs.json"
    try:
        with open(buffs_path, "r") as f:
            perma_buffs = json.load(f)
        return perma_buffs
    except FileNotFoundError:
        print(f"The file {buffs_path} was not found, make sure it was downloaded correctly and in the correct dir")
        raise


# Resolve and attach hero names
def get_hero_name(p, heroes_map):
    """Populate hero_name fields for players in a parsed match payload."""
    id = p.get("hero_id")
    hero_localized_name = None
    hero_name = None
    for item,value in heroes_map.items():
        if value.get("id") == id:
            hero_localized_name = value.get("localized_name")
            hero_name = value.get("name")
            break

    p["hero_localized_name"] = hero_localized_name
    p["hero_name"] = hero_name
    return hero_localized_name, hero_name 


# Resolve facet name
def get_facet_name(p, abilities_map, hero_name):
    """Populate hero_variant names using hero ability facet data."""
    variant = int(p.get("hero_variant"))
    facet_id = variant - 1
    hero_data = abilities_map.get(hero_name,{})
    facets = hero_data.get('facets', [])
    for facet in facets:
        if facet.get('id') == facet_id:
            return facet.get('name')


# Resolve item names
def get_item_name(p, items_map):
    """Populate item slot names from item IDs in player payloads."""
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

