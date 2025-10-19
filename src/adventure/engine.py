
from typing import Dict
from rich import print as rprint
from .schema import Adventure, Room

PROMPT = "[bold cyan]> [/bold cyan]"

def _idx(adv: Adventure) -> Dict[str, Room]:
    return {r.id: r for r in adv.rooms}

def _exits_str(r: Room) -> str:
    if not r.exits:
        return "[dim]no exits[/dim]"
    return ", ".join(sorted({e.dir for e in r.exits}))

def repl(adv: Adventure) -> None:
    idx = _idx(adv)
    here = adv.start_room
    rprint(f"[bold yellow]{adv.title}[/bold yellow]  [dim](seed {adv.seed})[/dim]")
    while True:
        room = idx[here]
        rprint(f"\n[bold]{room.name}[/bold]\n{room.description}\n[dim]Exits: {_exits_str(room)}[/dim]")
        try:
            cmd = input(PROMPT).strip().lower()
        except EOFError:
            rprint("\nGoodbye!")
            break
        if cmd in {"quit","exit"}:
            rprint("Goodbye!")
            break
        if cmd in {"look","l"}:
            continue
        if cmd in {"where","wut"}:
            rprint(f"[dim]You are in {here}[/dim]")
            continue
        if cmd in {"exits"}:
            rprint(f"[dim]{_exits_str(room)}[/dim]")
            continue
        # normalize 'go north' style
        if cmd.startswith("go "):
            cmd = cmd[3:].strip()
        # try move
        found = None
        for e in room.exits:
            if e.dir == cmd:
                found = e.to
                break
        if found:
            here = found
        else:
            rprint("[red]You can't go that way.[/red]")
