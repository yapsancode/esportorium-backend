import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.tournament import SeriesFormat, TournamentFormat, TournamentStatus


class TournamentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = None
    game: str = Field(default="mobile_legends", min_length=1, max_length=100)
    region: str | None = Field(default=None, max_length=10)
    format: TournamentFormat = TournamentFormat.single_elimination
    match_format: SeriesFormat = SeriesFormat.bo1
    max_teams: int = Field(default=8, ge=2, le=256)
    prize_pool: float | None = Field(default=None, ge=0)
    start_date: datetime | None = None
    end_date: datetime | None = None


class TournamentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None
    game: str | None = Field(default=None, min_length=1, max_length=100)
    region: str | None = Field(default=None, max_length=10)
    format: TournamentFormat | None = None
    match_format: SeriesFormat | None = None
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
    region: str | None
    format: TournamentFormat
    match_format: SeriesFormat
    status: TournamentStatus
    max_teams: int
    prize_pool: float | None
    start_date: datetime | None
    end_date: datetime | None
    organizer_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
