import uuid
from datetime import datetime, timezone
from enum import Enum

from sqlmodel import Field, SQLModel


class DraftAction(str, Enum):
    pick = "pick"
    ban = "ban"


class DraftEntry(SQLModel, table=True):
    __tablename__ = "draft_entries"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    game_id: uuid.UUID = Field(foreign_key="games.id", index=True)
    team_id: uuid.UUID = Field()  # plain UUID — no FK, may reference teams or users
    hero_name: str = Field(max_length=100)
    action: DraftAction
    phase: int  # draft phase order 1–20
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
