import uuid
from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class DisputeStatus(str, Enum):
    open = "open"
    under_review = "under_review"
    resolved = "resolved"


class Dispute(SQLModel, table=True):
    __tablename__ = "disputes"

    id: uuid.UUID = Field(default_factory=uuid4, primary_key=True)
    match_id: uuid.UUID = Field(foreign_key="matches.id", index=True)
    raised_by: uuid.UUID = Field(foreign_key="users.id", index=True)
    reason: str
    evidence_urls: list[str] | None = Field(default=None, sa_column=Column(JSON, nullable=True))
    status: DisputeStatus = Field(default=DisputeStatus.open)
    resolved_by: uuid.UUID | None = Field(default=None, foreign_key="users.id")
    resolution: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
