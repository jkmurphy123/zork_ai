
from typing import Dict, Set
import networkx as nx
from .schema import Adventure, Room, Exit
from .utils import DIR_OPPOSITE, canon_dir

def normalize_dirs(adv: Adventure) -> None:
    for r in adv.rooms:
        for ex in r.exits:
            ex.dir = canon_dir(ex.dir)  # type: ignore

def build_graph(adv: Adventure) -> nx.Graph:
    g = nx.Graph()
    for r in adv.rooms:
        g.add_node(r.id)
    for r in adv.rooms:
        for ex in r.exits:
            if ex.to in g:
                g.add_edge(r.id, ex.to)
    return g

def ensure_bidirectional(adv: Adventure) -> None:
    idx: Dict[str, Room] = {r.id: r for r in adv.rooms}
    needed = []
    for r in adv.rooms:
        for ex in r.exits:
            opp = DIR_OPPOSITE.get(ex.dir)
            if not opp:
                continue
            back_room = idx.get(ex.to)
            if not back_room:
                continue
            if not any(e.to == r.id for e in back_room.exits):
                needed.append((back_room.id, opp, r.id))
    for rid, d, to in needed:
        idx[rid].exits.append(Exit(dir=d, to=to))

def drop_bad_targets(adv: Adventure) -> None:
    valid_ids = {r.id for r in adv.rooms}
    for r in adv.rooms:
        r.exits = [e for e in r.exits if e.to in valid_ids]

def ensure_connected(adv: Adventure) -> None:
    g = build_graph(adv)
    if len(g) == 0:
        return
    comps = list(nx.connected_components(g))
    if len(comps) == 1:
        return
    # Connect components with corridors chain
    for a, b in zip(comps, comps[1:]):
        a_any = next(iter(a))
        b_any = next(iter(b))
        ra = next(r for r in adv.rooms if r.id == a_any)
        rb = next(r for r in adv.rooms if r.id == b_any)
        ra.exits.append(Exit(dir="e", to=rb.id))
        rb.exits.append(Exit(dir="w", to=ra.id))

def cap_rooms(adv: Adventure, cap: int = 30) -> None:
    if len(adv.rooms) <= cap:
        return
    keep_ids = {r.id for r in adv.rooms[:cap]}
    adv.rooms = [r for r in adv.rooms if r.id in keep_ids]
    drop_bad_targets(adv)

def validate_and_fix(adv: Adventure, cap: int = 30) -> Adventure:
    normalize_dirs(adv)
    drop_bad_targets(adv)
    ensure_bidirectional(adv)
    ensure_connected(adv)
    cap_rooms(adv, cap=cap)
    return adv
