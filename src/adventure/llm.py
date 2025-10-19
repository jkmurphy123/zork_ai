import os
import json
from typing import List
from openai import OpenAI
from .schema import Room

_SYSTEM = (
    "You are a game writer. Given a room id and minimal context, "
    "return a strictly valid JSON object that includes a punchy name and a vivid 1-2 sentence description. "
    "Do NOT modify exits or ids; you only write text."
)

# JSON Schema for Structured Outputs
ROOM_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "string"},
        "name": {"type": "string"},
        "description": {"type": "string"}
    },
    "required": ["id", "name", "description"],
    "additionalProperties": False
}

MODEL = os.getenv("ADVENTURE_MODEL", "gpt-4o-mini")

def describe_rooms(rooms: List[Room], theme: str = "ruins", dry_run: bool = False) -> List[Room]:
    """
    Decorate rooms with creative names/descriptions.
    Uses OpenAI Responses API Structured Outputs (json_schema, strict: true).
    Set ADVENTURE_MODEL to override the default model.
    """
    if dry_run:
        for r in rooms:
            r.name = f"{theme.title()} — {r.id}"
            r.description = f"A {theme} chamber with dust and echoes. Exits lead elsewhere."
        return rooms

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    for r in rooms:
        user = (
            f"Theme: {theme}. Room id: {r.id}. "
            f"Placeholder name: {r.name}. "
            f"Exit count: {len(r.exits)}. "
            "Write a punchy 'name' and a short atmospheric 'description'."
        )

        resp = client.responses.create(
            model=MODEL,
            input=[
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": user},
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "room_description",
                    "schema": ROOM_SCHEMA,
                    "strict": True
                }
            },
            temperature=0.9,
        )

        # Try to obtain parsed JSON; fall back to text
        data = None

        try:
            if getattr(resp, "output", None):
                item = resp.output[0]
                if getattr(item, "content", None):
                    chunk = item.content[0]
                    if getattr(chunk, "type", "") == "output_text" and getattr(chunk, "text", None):
                        data = json.loads(chunk.text)
        except Exception:
            data = None

        if data is None:
            text = getattr(resp, "output_text", None)
            if not text and hasattr(resp, "choices"):
                text = resp.choices[0].message.content  # older SDK compat
            if not text and hasattr(resp, "content"):
                text = resp.content
            if not text:
                raise RuntimeError(f"Unrecognized Responses payload shape: {resp}")
            data = json.loads(text)

        r.name = data.get("name", r.name)
        r.description = data.get("description", r.description)

    return rooms
