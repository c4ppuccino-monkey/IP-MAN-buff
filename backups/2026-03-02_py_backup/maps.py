import json
from pathlib import Path

repo_path = Path("dotaconstants")
json_dir = repo_path/"build"

#Loading heroes stats json file
def load_heroes():
    heroes_path = json_dir/ "heroes.json"
    try:
        with open(heroes_path,"r") as f:
            heroes = json.load(f)
        return heroes
    except FileNotFoundError:
        print(f'The file {heroes_path} not found, make sure the file exists in the right dir')
        raise


#loading items_ids
def load_items():
    items_path = json_dir/ "items.json"
    try:
        with open(items_path, "r") as f:
            items = json.load(f)
        return items
    except FileNotFoundError:
        print(f"The file {items_path} was not found, make sure it was downloaded correctly and in the correct dir")
        raise


#loading hero abilities including facets
def load_hero_abilities():
    abilities_path = json_dir/ "hero_abilities.json"
    try:
        with open(abilities_path, "r") as f:
            abilities = json.load(f)
        return abilities
    except FileNotFoundError:
        print(f"The file {abilities_path} was not found, make sure it was downloaded correctly and in the correct dir")
        raise


#loading ancients
def load_ancients():
    ancients_path = json_dir/ "ancients.json"
    try:
        with open(ancients_path, "r") as f:
            ancients = json.load(f)
        return ancients
    except FileNotFoundError:
        print(f"The file {ancients_path} was not found, make sure it was downloaded correctly and in the correct dir")
        raise

#aghs desc
def load_aghs_desc():
    aghs_path = json_dir/ "aghs_desc.json"
    try:
        with open(aghs_path, "r") as f:
            aghs_desc = json.load(f)
        return aghs_desc
    except FileNotFoundError:
        print(f"The file {aghs_path} was not found, make sure it was downloaded correctly and in the correct dir")
        raise


#order types
def load_order_types():
    order_path = json_dir/ "order_types.json"
    try:
        with open(order_path, "r") as f:
            order_types = json.load(f)
        return order_types
    except FileNotFoundError:
        print(f"The file {order_path} was not found, make sure it was downloaded correctly and in the correct dir")
        raise


#perma buffs
def load_perma_buffs():
    buffs_path = json_dir/ "permanent_buffs.json"
    try:
        with open(buffs_path, "r") as f:
            perma_buffs = json.load(f)
        return perma_buffs
    except FileNotFoundError:
        print(f"The file {buffs_path} was not found, make sure it was downloaded correctly and in the correct dir")
        raise


#matching hero id to hero name and appending them to the list of matches lists
def get_hero_name(p, heroes_map):
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


#matching facet name
def get_facet_name(p, abilities_map, hero_name):
    variant = int(p.get("hero_variant"))
    facet_id = variant - 1
    hero_data = abilities_map.get(hero_name,{})
    facets = hero_data.get('facets', [])
    for facet in facets:
        if facet.get('id') == facet_id:
            return facet.get('name')


#matching item names
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



