# src/adventure/llm.py
import os, json
from typing import List, Optional
from openai import OpenAI
from .schema import Room

_SYSTEM = (
    "You are a game writer. Given a room id and minimal context, "
    "return JSON with fields 'id', 'name', and 'description' ONLY. "
    "Keep name punchy; description 1–2 atmospheric sentences. "
    "Do NOT invent new fields; do NOT change exits or ids."
)

MODEL_DEFAULT = "gpt-4o-mini"

def _room_request_text(theme: str, r: Room) -> str:
    return (
        f"Theme: {theme}. Room id: {r.id}. "
        f"Current placeholder name: {r.name}. Exit count: {len(r.exits)}. "
        "Return a STRICT JSON object with keys exactly: "
        "id (string), name (string), description (string). "
        "No markdown, no code fences, no commentary—JSON only."
    )

def _parse_json_object_from_responses(resp) -> Optional[dict]:
    # Try various SDK shapes
    # 1) Newer Responses “output_text”
    text = getattr(resp, "output_text", None)
    if isinstance(text, str) and text.strip():
        try:
            return json.loads(text)
        except Exception:
            pass
    # 2) Some SDKs: resp.output[0].content[0].text
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
    # 3) Last resort (rare older shapes)
    if hasattr(resp, "choices") and resp.choices:
        txt = resp.choices[0].message.content
        return json.loads(txt)
    return None

def _parse_json_object_from_chat(resp) -> dict:
    txt = resp.choices[0].message.content
    return json.loads(txt)

def describe_rooms(rooms: List[Room], theme: str = "ruins", dry_run: bool = False, model: Optional[str] = None) -> List[Room]:
    if dry_run:
        for r in rooms:
            r.name = f"{theme.title()} — {r.id}"
            r.description = f"A {theme} chamber with dust and echoes. Exits lead elsewhere."
        return rooms

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    model = model or os.getenv("ADVENTURE_MODEL", MODEL_DEFAULT)

    for r in rooms:
        user = _room_request_text(theme, r)

        # Preferred path: Responses API with JSON mode
        try:
            resp = client.responses.create(
                model=model,
                input=[
                    {"role": "system", "content": _SYSTEM},
                    {"role": "user", "content": user},
                ],
                response_format={"type": "json_object"},
                temperature=0.9,
            )
            data = _parse_json_object_from_responses(resp)
            if not isinstance(data, dict):
                raise ValueError("Could not parse JSON from Responses output.")
        except TypeError as e:
            # Fallback if this method signature doesn't accept response_format
            # or the SDK doesn't support Responses API params yet.
            if "response_format" not in str(e):
                # If it's some other TypeError, propagate it
                raise
            chat = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": _SYSTEM},
                    {"role": "user", "content": user},
                ],
                response_format={"type": "json_object"},
                temperature=0.9,
            )
            data = _parse_json_object_from_chat(chat)
        except Exception:
            # If any other Responses error happens, try Chat JSON mode anyway
            chat = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": _SYSTEM},
                    {"role": "user", "content": user},
                ],
                response_format={"type": "json_object"},
                temperature=0.9,
            )
            data = _parse_json_object_from_chat(chat)

        # Defensive normalization
        if not isinstance(data, dict):
            data = {}
        r.name = str(data.get("name", r.name))
        r.description = str(data.get("description", r.description))

    return rooms
