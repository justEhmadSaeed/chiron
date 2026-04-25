from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(UTC)


class AgentRunStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentRunCreateRequest(BaseModel):
    agent_name: str = Field(min_length=1)
    input: dict[str, Any] = Field(default_factory=dict)


class AgentRun(BaseModel):
    run_id: str = Field(default_factory=lambda: str(uuid4()))
    agent_name: str
    status: AgentRunStatus = AgentRunStatus.QUEUED
    created_at: datetime = Field(default_factory=utc_now)


class AgentEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    run_id: str
    event_type: str
    created_at: datetime = Field(default_factory=utc_now)
    payload: dict[str, Any] = Field(default_factory=dict)
