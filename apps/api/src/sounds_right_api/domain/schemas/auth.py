from __future__ import annotations

import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from .common import UserRole


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    username: str
    role: UserRole


class AuthRegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=8)


class AuthLoginRequest(BaseModel):
    email_or_username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class AuthResponse(BaseModel):
    user: UserPublic
    access_token: str
    token_type: Literal["bearer"] = "bearer"
