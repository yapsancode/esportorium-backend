import uuid
from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from sqlmodel import Field, SQLModel


class UserRole(str, Enum):
    player = "player"
    team_captain = "team_captain"
    organizer = "organizer"
    moderator = "moderator"
    admin = "admin"
    super_admin = "super_admin"


class UserPlan(str, Enum):
    free = "free"
    pro = "pro"
    business = "business"
    enterprise = "enterprise"


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: uuid.UUID = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(unique=True, index=True, max_length=255)
    username: str = Field(unique=True, index=True, max_length=50)
    hashed_password: str

    display_name: str | None = Field(default=None, max_length=100)
    avatar_url: str | None = Field(default=None)

    role: UserRole = Field(default=UserRole.player)
    plan: UserPlan = Field(default=UserPlan.free)
    plan_expires_at: datetime | None = Field(default=None)

    stripe_customer_id: str | None = Field(default=None, index=True)

    is_active: bool = Field(default=True)
    is_verified: bool = Field(default=False)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
