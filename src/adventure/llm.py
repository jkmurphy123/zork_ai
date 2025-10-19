import os, json
from typing import List, Optional, Dict, Any
from openai import OpenAI
from .schema import Room

MODEL_DEFAULT = "gpt-4o-mini"

_SYSTEM_DESC = (
    "You are a game writer. Given context, return JSON with exactly keys "
    "id, name, description. Name 2–5 evocative words; description 1–2 vivid, sensory sentences. "
    "Do not invent extra keys, markdown, or commentary."
)

def _room_request_text(
    theme: str,
    r: Room,
    lore: Optional[str],
    style: Optional[List[str]],
    neighbor_types: List[str]
) -> str:
    style_text = ", ".join(style or [])
    tags_text = ", ".join(r.tags) if r.tags else ""
    neighbor_text = ", ".join(neighbor_types) if neighbor_types else ""

    lines = [
        f"Theme: {theme}",
        f"Lore: {lore or ''}",
        f"Style guide rules: {style_text}",
        "Room blueprint:",
        f"- id: {r.id}",
        f"- location_type: {r.type}",
        f"- tags: {tags_text}",
        f"- neighbor_location_types: {neighbor_text}",
        "Return STRICT JSON with keys: id (string), name (string), description (string). No markdown.",
    ]
    return "\n".join(lines)

def _parse_json_from_responses(resp):
    text = getattr(resp, "output_text", None)
    if isinstance(text, str) and text.strip():
        return json.loads(text)
    try:
        items = getattr(resp, "output", None)
        if items:
            item0 = items[0]
            content = getattr(item0, "content", None)
            if content:
                chunk0 = content[0]
                t = getattr(chunk0, "text", None)
                if isinstance(t, str) and t.strip():
                    return json.loads(t)
    except Exception:
        pass
    if hasattr(resp, "choices") and resp.choices:
        return json.loads(resp.choices[0].message.content)
    return None

def _parse_json_from_chat(resp):
    return json.loads(resp.choices[0].message.content)

def generate_location_catalog(theme: str, n_rooms: int, model: Optional[str] = None) -> Dict[str, Any]:
    """
    Return a dict with: lore (str), style_guide (list[str]), locations (list[loc]).
    Each location: {slug, name, tags:[...], min:int, max:int}
    Uses JSON mode for broad SDK compatibility.
    """
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    model = model or os.getenv("ADVENTURE_MODEL", MODEL_DEFAULT)

    system = (
        "You are designing a coherent location catalog for a text adventure. "
        "Return JSON ONLY with keys: lore (string), style_guide (array of short rules), locations (array). "
        "Each location has: slug, name, tags (3-6), min, max."
    )
    user = f"""
Theme: {theme}
We will generate exactly {n_rooms} rooms.
Propose 28–36 candidate locations with min/max counts that could plausibly compose the space.
Rules:
- Include hubs (1–2), chokepoints (1–3), corridors/airlocks, labs/workspaces, utilities, living areas, exterior.
- Keep slugs lowercase_with_underscores.
- min and max are integers; max >= min; typical min 0–2, max 2–6.
Output JSON ONLY.
"""

    # Prefer Chat Completions with JSON mode for compatibility
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        response_format={"type": "json_object"},
        temperature=0.5,
    )
    data = _parse_json_from_chat(resp)
    data = data if isinstance(data, dict) else {}
    data.setdefault("lore", "")
    data.setdefault("style_guide", [])
    data.setdefault("locations", [])
    return data

def describe_rooms(
    rooms: List[Room],
    theme: str = "ruins",
    dry_run: bool = False,
    model: Optional[str] = None,
    lore: Optional[str] = None,
    style_guide: Optional[List[str]] = None,
    neighbors_fn=None
) -> List[Room]:
    if dry_run:
        for r in rooms:
            r.name = f"{theme.title()} — {r.id}"
            r.description = f"A {theme} chamber with dust and echoes. Exits lead elsewhere."
        return rooms

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    model = model or os.getenv("ADVENTURE_MODEL", MODEL_DEFAULT)

    for r in rooms:
        neighbor_types = neighbors_fn(r) if callable(neighbors_fn) else []
        user = _room_request_text(theme, r, lore, style_guide, neighbor_types)

        try:
            resp = client.responses.create(
                model=model,
                input=[
                    {"role": "system", "content": _SYSTEM_DESC},
                    {"role": "user", "content": user},
                ],
                response_format={"type": "json_object"},
                temperature=0.8,
            )
            data = _parse_json_from_responses(resp)
            if not isinstance(data, dict):
                raise ValueError("Could not parse JSON from Responses output.")
        except Exception:
            chat = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": _SYSTEM_DESC},
                    {"role": "user", "content": user},
                ],
                response_format={"type": "json_object"},
                temperature=0.8,
            )
            data = _parse_json_from_chat(chat)

        r.name = str(data.get("name", r.name))
        r.description = str(data.get("description", r.description))
    return rooms
