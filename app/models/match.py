import uuid
from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from sqlmodel import Field, SQLModel


class MatchStatus(str, Enum):
    pending = "pending"
    ongoing = "ongoing"
    completed = "completed"
    bye = "bye"


class Match(SQLModel, table=True):
    __tablename__ = "matches"

    id: uuid.UUID = Field(default_factory=uuid4, primary_key=True)
    tournament_id: uuid.UUID = Field(foreign_key="tournaments.id", index=True)
    round: int
    match_number: int
    participant_1: uuid.UUID | None = Field(default=None, foreign_key="users.id")
    participant_2: uuid.UUID | None = Field(default=None, foreign_key="users.id")
    winner_id: uuid.UUID | None = Field(default=None, foreign_key="users.id")
    score_1: int = Field(default=0)
    score_2: int = Field(default=0)
    status: MatchStatus = Field(default=MatchStatus.pending)
    scheduled_at: datetime | None = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
