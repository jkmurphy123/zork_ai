
from adventure.generator import make_adventure
from adventure.validator import validate_and_fix
from adventure.schema import Adventure

def test_graph_properties():
    adv = make_adventure(title="Test", seed=123, n_rooms=20)
    adv = validate_and_fix(adv, cap=30)
    assert isinstance(adv, Adventure)
    ids = {r.id for r in adv.rooms}
    # every exit points to valid id
    for r in adv.rooms:
        for e in r.exits:
            assert e.to in ids
    # at least one exit per room
    assert all(len(r.exits) >= 1 for r in adv.rooms)
