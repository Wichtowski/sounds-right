from __future__ import annotations

import uuid
from typing import Any

from litestar import Request, get
from litestar.exceptions import HTTPException

from sounds_right_api.db.session import SessionLocal
from sounds_right_api.domain.schemas import JobEventsResponse, TranscriptionJobPublic
from sounds_right_api.routes.auth import get_current_user_from_request
from sounds_right_api.services.jobs import JobNotFoundError, get_job, list_job_events


@get("/api/jobs/{job_id:uuid}")
async def get_job_route(
    request: Request[Any, Any, Any],
    job_id: uuid.UUID,
) -> TranscriptionJobPublic:
    async with SessionLocal() as session:
        await get_current_user_from_request(request, session)
        try:
            return await get_job(session, job_id)
        except JobNotFoundError:
            raise HTTPException(status_code=404, detail="Job not found") from None


@get("/api/jobs/{job_id:uuid}/events")
async def list_job_events_route(
    request: Request[Any, Any, Any],
    job_id: uuid.UUID,
) -> JobEventsResponse:
    async with SessionLocal() as session:
        await get_current_user_from_request(request, session)
        try:
            return JobEventsResponse(job_id=job_id, events=await list_job_events(session, job_id))
        except JobNotFoundError:
            raise HTTPException(status_code=404, detail="Job not found") from None
