
import os
from typing import List
from openai import OpenAI
from .schema import Room

_SYSTEM = (
    "You are a game writer. Given a room id and minimal tags, "
    "return JSON with name and description for that room only. "
    "Do not change exits or ids. Keep to 1-2 vivid sentences."
)

def _tools():
    # Function-calling tool definition to force JSON
    return [{
        "type": "function",
        "function": {
            "name": "submit_room",
            "description": "Return creative text for one room",
            "parameters": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "description": {"type": "string"}
                },
                "required": ["id", "name", "description"],
                "additionalProperties": False
            }
        }
    }]

def describe_rooms(rooms: List[Room], theme: str = "ruins", dry_run: bool = False) -> List[Room]:
    if dry_run:
        for r in rooms:
            r.name = f"{theme.title()} — {r.id}"
            r.description = f"A {theme} chamber with dust and echoes. Exits lead elsewhere."
        return rooms

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    for r in rooms:
        user = (
            f"Theme: {theme}. Room id: {r.id}. "
            f"Current placeholder name: {r.name}. "
            f"Exit count: {len(r.exits)}. "
            "Write a punchy name and a short atmospheric description."
        )
        resp = client.chat.completions.create(
            model="gpt-4o-mini",  # adjust as you like
            temperature=0.9,
            tools=_tools(),
            tool_choice={"type":"function","function":{"name":"submit_room"}},
            messages=[
                {"role":"system","content":_SYSTEM},
                {"role":"user","content":user}
            ]
        )
        tool = resp.choices[0].message.tool_calls[0]
        args = tool.function.arguments  # JSON string
        import json
        data = json.loads(args)
        r.name = data.get("name", r.name)
        r.description = data.get("description", r.description)
    return rooms
