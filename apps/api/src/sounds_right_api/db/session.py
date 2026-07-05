from typing import Literal

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

from sounds_right_api.config import get_settings


def create_engine() -> AsyncEngine:
    settings = get_settings()
    return create_async_engine(settings.database_url, pool_pre_ping=True)


engine = create_engine()
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def check_database() -> Literal["ok"]:
    async with engine.connect() as connection:
        await connection.execute(text("select 1"))
    return "ok"
