import uuid
from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from app.models.tournament import SeriesFormat, TournamentFormat, TournamentStatus, TournamentType


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
    tournament_type: TournamentType = TournamentType.online
    venue_name: str | None = Field(default=None, max_length=200)
    venue_address: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def venue_name_required_for_physical(self) -> "TournamentCreate":
        if self.tournament_type in (TournamentType.physical, TournamentType.hybrid) and not self.venue_name:
            raise ValueError("venue_name is required for physical and hybrid tournaments")
        return self


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
    tournament_type: TournamentType | None = None
    venue_name: str | None = Field(default=None, max_length=200)
    venue_address: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def venue_name_required_for_physical(self) -> "TournamentUpdate":
        if self.tournament_type in (TournamentType.physical, TournamentType.hybrid) and not self.venue_name:
            raise ValueError("venue_name is required for physical and hybrid tournaments")
        return self


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
    tournament_type: TournamentType
    venue_name: str | None
    venue_address: str | None

    model_config = {"from_attributes": True}
