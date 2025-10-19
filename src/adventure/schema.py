from typing import List, Literal, Optional
from pydantic import BaseModel, Field, field_validator

Direction = Literal[
    "n","s","e","w","ne","nw","se","sw","up","down","in","out","enter","exit"
]

class Exit(BaseModel):
    dir: Direction
    to: str  # room id

class Room(BaseModel):
    id: str
    name: str
    description: str
    exits: List[Exit] = Field(default_factory=list)
    # NEW (optional) fields for themed roles
    type: Optional[str] = None
    tags: List[str] = Field(default_factory=list)

class Adventure(BaseModel):
    schema_version: int = 1
    title: str
    seed: int
    rooms: List[Room]
    start_room: str
    # NEW global flavor
    lore: Optional[str] = None
    style_guide: List[str] = Field(default_factory=list)

    @field_validator("rooms")
    @classmethod
    def unique_ids(cls, v):
        ids = [r.id for r in v]
        if len(ids) != len(set(ids)):
            raise ValueError("Room IDs must be unique")
        return v
