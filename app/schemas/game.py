import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.draft import DraftAction


class DraftEntryCreate(BaseModel):
    team_id: uuid.UUID
    hero_name: str = Field(min_length=1, max_length=100)
    action: DraftAction
    phase: int = Field(ge=1, le=20)


class DraftEntryPublic(BaseModel):
    id: uuid.UUID
    game_id: uuid.UUID
    team_id: uuid.UUID
    hero_name: str
    action: DraftAction
    phase: int
    created_at: datetime

    model_config = {"from_attributes": True}


class GameCreate(BaseModel):
    game_number: int = Field(ge=1)
    winner_id: uuid.UUID
    duration_minutes: int | None = Field(default=None, ge=1)
    draft: list[DraftEntryCreate] = []


class GamePublic(BaseModel):
    id: uuid.UUID
    match_id: uuid.UUID
    game_number: int
    winner_id: uuid.UUID | None
    duration_minutes: int | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class GameWithDraftPublic(GamePublic):
    draft: list[DraftEntryPublic] = []
