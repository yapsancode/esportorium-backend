import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.match import MatchStatus


class MatchPublic(BaseModel):
    id: uuid.UUID
    tournament_id: uuid.UUID
    round: int
    match_number: int
    participant_1: uuid.UUID | None
    participant_2: uuid.UUID | None
    winner_id: uuid.UUID | None
    score_1: int
    score_2: int
    status: MatchStatus
    scheduled_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RoundPublic(BaseModel):
    round: int
    matches: list[MatchPublic]


class BracketPublic(BaseModel):
    tournament_id: uuid.UUID
    rounds: list[RoundPublic]
