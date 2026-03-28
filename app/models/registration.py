import uuid
from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from sqlmodel import Field, SQLModel, UniqueConstraint


class RegistrationStatus(str, Enum):
    pending = "pending"
    confirmed = "confirmed"
    cancelled = "cancelled"


class Registration(SQLModel, table=True):
    __tablename__ = "registrations"
    __table_args__ = (UniqueConstraint("tournament_id", "user_id", name="uq_registration_tournament_user"),)

    id: uuid.UUID = Field(default_factory=uuid4, primary_key=True)
    tournament_id: uuid.UUID = Field(foreign_key="tournaments.id", index=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    status: RegistrationStatus = Field(default=RegistrationStatus.pending)
    registered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
