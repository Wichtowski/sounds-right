from __future__ import annotations

from typing import Any

from jwt import InvalidTokenError
from litestar import Request, get, post
from litestar.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from sounds_right_api.auth.security import decode_access_token
from sounds_right_api.config import get_settings
from sounds_right_api.db.session import SessionLocal
from sounds_right_api.domain.schemas import (
    AuthLoginRequest,
    AuthRegisterRequest,
    AuthResponse,
    UserPublic,
)
from sounds_right_api.models import User
from sounds_right_api.services.auth import (
    AuthError,
    DuplicateUserError,
    InactiveUserError,
    login_user,
    register_user,
)


def unauthorized() -> HTTPException:
    return HTTPException(status_code=401, detail="Missing or invalid bearer token")


async def get_current_user_from_request(
    request: Request[Any, Any, Any],
    session: AsyncSession,
) -> User:
    authorization = request.headers.get("authorization")
    if authorization is None:
        raise unauthorized()
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise unauthorized()

    settings = get_settings()
    try:
        user_id = decode_access_token(token, settings)
    except (InvalidTokenError, ValueError):
        raise unauthorized() from None

    user = await session.get(User, user_id)
    if user is None or not user.is_active:
        raise unauthorized()
    return user


@post("/api/auth/register", status_code=201)
async def register(data: AuthRegisterRequest) -> AuthResponse:
    async with SessionLocal() as session:
        try:
            return await register_user(session, data, get_settings())
        except DuplicateUserError:
            raise HTTPException(
                status_code=409,
                detail="Email or username already exists",
            ) from None


@post("/api/auth/login")
async def login(data: AuthLoginRequest) -> AuthResponse:
    async with SessionLocal() as session:
        try:
            return await login_user(session, data, get_settings())
        except AuthError:
            raise HTTPException(status_code=401, detail="Invalid credentials") from None
        except InactiveUserError:
            raise HTTPException(status_code=403, detail="User is inactive") from None


@get("/api/me")
async def me(request: Request[Any, Any, Any]) -> UserPublic:
    async with SessionLocal() as session:
        user = await get_current_user_from_request(request, session)
        return UserPublic.model_validate(user)
