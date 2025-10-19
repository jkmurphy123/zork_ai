from __future__ import annotations
import json
import pathlib
import typer
from rich import print as rprint
from .generator import make_adventure
from .validator import validate_and_fix
from .llm import describe_rooms, generate_location_catalog
from .schema import Adventure
from .utils import new_seed

app = typer.Typer(help="Adventure Agent CLI")

def _neighbor_types(adv: Adventure, room_id: str):
    idx = {r.id: r for r in adv.rooms}
    here = idx[room_id]
    types = []
    for e in here.exits:
        t = idx[e.to].type
        if t:
            types.append(t)
    seen = set()
    out = []
    for t in types:
        if t not in seen:
            out.append(t); seen.add(t)
    return out

@app.command()
def generate(
    title: str = typer.Option("Untitled Adventure", "--title"),
    rooms: int = typer.Option(24, "--rooms", min=6, max=40),
    seed: int | None = typer.Option(None, "--seed"),
    theme: str = typer.Option("ruins", "--theme"),
    dry: bool = typer.Option(False, "--dry", help="No API calls; template text"),
    use_catalog: bool = typer.Option(True, "--use-catalog/--no-catalog", help="Two-phase: catalog then descriptions")
):
    """Generate an adventure JSON (saved to out/adventure.json)."""
    out_dir = pathlib.Path("out")
    out_dir.mkdir(parents=True, exist_ok=True)
    if seed is None:
        seed = new_seed()

    adv = make_adventure(title=title, seed=seed, n_rooms=rooms)

    catalog = None
    if use_catalog and not dry:
        catalog = generate_location_catalog(theme=theme, n_rooms=rooms)
        adv.lore = catalog.get("lore")
        adv.style_guide = catalog.get("style_guide", [])
        from .mapper import assign_room_types
        assign_room_types(adv, catalog=catalog, seed=seed)

    adv.rooms = describe_rooms(
        adv.rooms,
        theme=theme,
        dry_run=dry,
        lore=adv.lore,
        style_guide=adv.style_guide,
        neighbors_fn=lambda r: _neighbor_types(adv, r.id)
    )

    adv = validate_and_fix(adv, cap=30)

    path = out_dir / "adventure.json"
    path.write_text(json.dumps(adv.model_dump(), indent=2), encoding="utf-8")
    rprint(f"[green]Wrote[/green] {path}")

@app.command()
def play(path: str):
    """Play a generated adventure JSON."""
    data = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    adv = Adventure.model_validate(data)
    from .engine import repl
    repl(adv)

if __name__ == "__main__":
    app()
