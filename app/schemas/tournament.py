import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.tournament import TournamentFormat, TournamentStatus


class TournamentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = None
    game: str = Field(min_length=1, max_length=100)
    format: TournamentFormat = TournamentFormat.single_elimination
    max_teams: int = Field(default=8, ge=2, le=256)
    prize_pool: float | None = Field(default=None, ge=0)
    start_date: datetime | None = None
    end_date: datetime | None = None


class TournamentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None
    game: str | None = Field(default=None, min_length=1, max_length=100)
    format: TournamentFormat | None = None
    status: TournamentStatus | None = None
    max_teams: int | None = Field(default=None, ge=2, le=256)
    prize_pool: float | None = Field(default=None, ge=0)
    start_date: datetime | None = None
    end_date: datetime | None = None


class TournamentPublic(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    game: str
    format: TournamentFormat
    status: TournamentStatus
    max_teams: int
    prize_pool: float | None
    start_date: datetime | None
    end_date: datetime | None
    organizer_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
