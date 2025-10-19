from typing import Dict, List
from .schema import Adventure
from .utils import rng_from_seed

def _pick_by_slug(locs: List[dict], candidates: List[str]):
    by_slug = {l.get("slug"): l for l in locs}
    for s in candidates:
        if s in by_slug:
            return by_slug[s]
    return None

def _eligible(l: dict, assigned: Dict[str, int]) -> bool:
    mx = int(l.get("max", 1))
    return assigned.get(l["slug"], 0) < mx

def assign_room_types(adv: Adventure, catalog: dict, seed: int) -> None:
    rng = rng_from_seed(seed)
    locs: List[dict] = list(catalog.get("locations", []))
    if not locs:
        return

    assigned_counts: Dict[str, int] = {l["slug"]: 0 for l in locs}

    degree = {r.id: len(r.exits) for r in adv.rooms}
    rooms_sorted = sorted(adv.rooms, key=lambda r: degree[r.id], reverse=True)

    hub_candidates = ["control_center","server_core","observation_dome","command_deck","central_hub"]
    hub_loc = _pick_by_slug(locs, hub_candidates)
    for r in rooms_sorted[:2]:
        if r.type is None and hub_loc and _eligible(hub_loc, assigned_counts):
            r.type = hub_loc["slug"]
            r.tags = list(hub_loc.get("tags", []))
            assigned_counts[r.type] += 1

    choke_candidates = ["airlock","vacuum_corridor","corridor","decom_room","pressure_tunnel"]
    choke = _pick_by_slug(locs, choke_candidates)
    for r in adv.rooms:
        if r.type is None and degree[r.id] <= 2 and choke and _eligible(choke, assigned_counts):
            r.type = choke["slug"]
            r.tags = list(choke.get("tags", []))
            assigned_counts[r.type] += 1

    untyped = [r for r in adv.rooms if r.type is None]
    for l in locs:
        mn = int(l.get("min", 0))
        while assigned_counts.get(l["slug"], 0) < mn and untyped:
            r = untyped.pop(0)
            r.type = l["slug"]
            r.tags = list(l.get("tags", []))
            assigned_counts[r.type] = assigned_counts.get(r.type, 0) + 1

    untyped = [r for r in adv.rooms if r.type is None]
    pool = [l for l in locs if int(l.get("max", 1)) > 0]
    while untyped and pool:
        r = untyped.pop(0)
        rng.shuffle(pool)
        choice = None
        for l in pool:
            if _eligible(l, assigned_counts):
                choice = l
                break
        if not choice:
            break
        r.type = choice["slug"]
        r.tags = list(choice.get("tags", []))
        assigned_counts[r.type] = assigned_counts.get(r.type, 0) + 1
