import uuid
from datetime import datetime, timezone
from enum import Enum

from sqlmodel import Field, SQLModel


class TeamMemberRole(str, Enum):
    roamer = "roamer"
    gold = "gold"
    exp = "exp"
    mid = "mid"
    jungler = "jungler"
    substitute = "substitute"


class Team(SQLModel, table=True):
    __tablename__ = "teams"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(max_length=100, index=True)
    region: str | None = Field(default=None, max_length=10)
    captain_id: uuid.UUID = Field(foreign_key="users.id", index=True)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TeamMember(SQLModel, table=True):
    __tablename__ = "team_members"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    team_id: uuid.UUID = Field(foreign_key="teams.id", index=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    role: TeamMemberRole | None = Field(default=None)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
