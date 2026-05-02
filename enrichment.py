"""Payload enrichment helpers that map IDs to display names."""


def get_hero_name(p, heroes_map):
    """Resolve hero_name for each player row using hero mappings."""
    hero_id = p.get("hero_id")
    hero_localized_name = None
    hero_name = None
    for _, value in heroes_map.items():
        if value.get("id") == hero_id:
            hero_localized_name = value.get("localized_name")
            hero_name = value.get("name")
            break

    p["hero_localized_name"] = hero_localized_name
    p["hero_name"] = hero_name
    return hero_localized_name, hero_name


def get_facet_name(p, abilities_map, hero_name):
    """Resolve hero variant/facet names for each player row when available."""
    variant = p.get("hero_variant")
    if not variant:
        return None
    facet_id = variant - 1
    hero_data = abilities_map.get(hero_name, {})
    facets = hero_data.get("facets", [])

    for facet in facets:
        if facet.get("id") == facet_id:
            return facet.get("name")
    return None


def get_item_name(p, items_map):
    """Resolve item ID fields to readable item names for each player row."""
    slots = [
        p.get("item_0", None),
        p.get("item_1", None),
        p.get("item_2", None),
        p.get("item_3", None),
        p.get("item_4", None),
        p.get("item_5", None),
        p.get("backpack_0", None),
        p.get("backpack_1", None),
        p.get("backpack_2", None),
        p.get("item_neutral", None),
        p.get("item_neutral2", None),
    ]
    names = []
    for slot in slots:
        if not slot:
            names.append(None)
        else:
            names.append(items_map.get(str(slot), None))

    return names
