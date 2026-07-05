import logging
from typing import Literal

from pydantic import BaseModel

from sounds_right_api.config import get_settings
from sounds_right_api.db.session import check_database

logger = logging.getLogger(__name__)

CheckStatus = Literal["ok", "error", "skipped"]


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str
    environment: str
    checks: dict[str, CheckStatus]


async def get_health() -> HealthResponse:
    settings = get_settings()
    checks: dict[str, CheckStatus] = {}

    try:
        checks["database"] = await check_database()
    except Exception:  # pragma: no cover - defensive path
        logger.exception("database health check failed")
        checks["database"] = "error"

    checks["minio"] = "skipped"
    checks["kafka"] = "skipped"

    return HealthResponse(
        status="ok",
        service="sounds-right-api",
        environment=settings.app_env,
        checks=checks,
    )
