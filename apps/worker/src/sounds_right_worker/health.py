from typing import Literal

from pydantic import BaseModel


class WorkerHealth(BaseModel):
    status: Literal["ok"]
    service: str
    environment: str


def get_health(service: str, environment: str) -> WorkerHealth:
    return WorkerHealth(status="ok", service=service, environment=environment)
