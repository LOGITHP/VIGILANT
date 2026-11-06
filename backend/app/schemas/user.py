import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, ConfigDict


class RoleResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class UserResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool
    is_superuser: bool
    roles: List[str] = []
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
