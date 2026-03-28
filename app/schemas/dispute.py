import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.dispute import DisputeStatus


class DisputeCreate(BaseModel):
    reason: str
    evidence_urls: list[str] | None = None


class DisputeResolve(BaseModel):
    resolution: str


class DisputePublic(BaseModel):
    id: uuid.UUID
    match_id: uuid.UUID
    raised_by: uuid.UUID
    reason: str
    evidence_urls: list[str] | None
    status: DisputeStatus
    resolved_by: uuid.UUID | None
    resolution: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
