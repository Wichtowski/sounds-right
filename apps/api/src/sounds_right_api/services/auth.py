from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from sounds_right_api.auth.security import create_access_token, hash_password, verify_password
from sounds_right_api.config import ApiSettings
from sounds_right_api.domain.schemas import (
    AuthLoginRequest,
    AuthRegisterRequest,
    AuthResponse,
    UserPublic,
)
from sounds_right_api.models import User


class AuthError(Exception):
    pass


class DuplicateUserError(Exception):
    pass


class InactiveUserError(Exception):
    pass


async def register_user(
    session: AsyncSession,
    payload: AuthRegisterRequest,
    settings: ApiSettings,
) -> AuthResponse:
    existing = await session.scalar(
        select(User).where(or_(User.email == payload.email, User.username == payload.username)),
    )
    if existing is not None:
        raise DuplicateUserError

    user = User(
        email=str(payload.email).lower(),
        username=payload.username,
        password_hash=hash_password(payload.password),
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    return AuthResponse(
        user=UserPublic.model_validate(user),
        access_token=create_access_token(user.id, settings),
    )


async def login_user(
    session: AsyncSession,
    payload: AuthLoginRequest,
    settings: ApiSettings,
) -> AuthResponse:
    login = payload.email_or_username.lower()
    user = await session.scalar(
        select(User).where(or_(User.email == login, User.username == login)),
    )
    if user is None or not verify_password(payload.password, user.password_hash):
        raise AuthError
    if not user.is_active:
        raise InactiveUserError

    return AuthResponse(
        user=UserPublic.model_validate(user),
        access_token=create_access_token(user.id, settings),
    )
