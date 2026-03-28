import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.registration import RegistrationStatus


class RegistrationPublic(BaseModel):
    id: uuid.UUID
    tournament_id: uuid.UUID
    user_id: uuid.UUID
    status: RegistrationStatus
    registered_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
