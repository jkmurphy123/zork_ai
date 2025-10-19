
import random
from typing import Iterable
CANON = {
    "north":"n","south":"s","east":"e","west":"w",
    "northeast":"ne","north-east":"ne","north east":"ne",
    "northwest":"nw","north-west":"nw","north west":"nw",
    "southeast":"se","south-east":"se","south east":"se",
    "southwest":"sw","south-west":"sw","south west":"sw",
    "u":"up","d":"down","inward":"in","outward":"out"
}
DIR_OPPOSITE = {
    "n":"s","s":"n","e":"w","w":"e",
    "ne":"sw","sw":"ne","nw":"se","se":"nw",
    "up":"down","down":"up","in":"out","out":"in",
    "enter":"out","exit":"in"
}

def canon_dir(s: str) -> str:
    s = s.strip().lower()
    return CANON.get(s, s)

def rng_from_seed(seed: int) -> random.Random:
    return random.Random(seed)

def new_seed() -> int:
    import secrets
    return secrets.randbits(32)
