import uuid
from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from sqlmodel import Field, SQLModel


class TournamentFormat(str, Enum):
    single_elimination = "single_elimination"
    double_elimination = "double_elimination"
    round_robin = "round_robin"
    swiss = "swiss"


class TournamentStatus(str, Enum):
    draft = "draft"
    open = "open"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"


class Tournament(SQLModel, table=True):
    __tablename__ = "tournaments"

    id: uuid.UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(max_length=100, index=True)
    description: str | None = Field(default=None)
    game: str = Field(max_length=100)
    format: TournamentFormat = Field(default=TournamentFormat.single_elimination)
    status: TournamentStatus = Field(default=TournamentStatus.draft)
    max_teams: int = Field(default=8)
    prize_pool: float | None = Field(default=None)
    start_date: datetime | None = Field(default=None)
    end_date: datetime | None = Field(default=None)

    organizer_id: uuid.UUID = Field(foreign_key="users.id", index=True)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
