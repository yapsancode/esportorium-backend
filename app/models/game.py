import uuid
from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


class Game(SQLModel, table=True):
    __tablename__ = "games"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    match_id: uuid.UUID = Field(foreign_key="matches.id", index=True)
    game_number: int
    # References match.participant_1 or match.participant_2 — no FK
    # because participants may be users or teams depending on context.
    winner_id: uuid.UUID | None = Field(default=None)
    duration_minutes: int | None = Field(default=None)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
