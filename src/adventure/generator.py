
from typing import List, Tuple
import networkx as nx
from .schema import Adventure, Room, Exit
from .utils import rng_from_seed

def _grid_dirs(x1, y1, x2, y2) -> List[str]:
    dirs = []
    if y2 < y1: dirs.append("n")
    if y2 > y1: dirs.append("s")
    if x2 > x1: dirs.append("e")
    if x2 < x1: dirs.append("w")
    return dirs or ["e"]

def build_topology(seed: int, n_rooms: int = 24) -> Tuple[List[Room], str]:
    rng = rng_from_seed(seed)
    # Start with a tree using a randomized DFS on a grid-ish arrangement
    side = max(3, int((n_rooms * 1.2) ** 0.5))
    coords = []
    while len(coords) < n_rooms:
        x, y = rng.randrange(side), rng.randrange(side)
        if (x, y) not in coords:
            coords.append((x, y))
    g = nx.Graph()
    for i in range(n_rooms):
        g.add_node(f"R{i+1}", pos=coords[i])
    # Build a random spanning tree
    nodes = list(g.nodes())
    rng.shuffle(nodes)
    visited = {nodes[0]}
    edges = []
    while len(visited) < n_rooms:
        a = rng.choice(list(visited))
        b = rng.choice([u for u in g.nodes() if u not in visited])
        edges.append((a, b))
        visited.add(b)
    # Add a few extra edges for loops
    for _ in range(max(1, n_rooms // 6)):
        a, b = rng.sample(list(g.nodes()), 2)
        if a != b and (a, b) not in edges and (b, a) not in edges:
            edges.append((a, b))
    # Convert to rooms with exits
    rooms = []
    for node in g.nodes():
        rooms.append(Room(id=node, name=f"Room {node}", description="(to be written)", exits=[]))
    pos = {n: g.nodes[n].get("pos") for n in g.nodes()}
    idx = {r.id: r for r in rooms}
    for a, b in edges:
        x1, y1 = pos[a]
        x2, y2 = pos[b]
        dirs_ab = _grid_dirs(x1, y1, x2, y2)
        # pick one direction
        d = rng_from_seed(seed + hash((a, b))).choice(dirs_ab)
        idx[a].exits.append(Exit(dir=d, to=b))
        # opposite will be ensured by validator
    start = rooms[0].id
    return rooms, start

def make_adventure(title: str, seed: int, n_rooms: int = 24) -> Adventure:
    rooms, start = build_topology(seed=seed, n_rooms=n_rooms)
    return Adventure(title=title, seed=seed, rooms=rooms, start_room=start)
