from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Literal
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


class ExperimentStatus(StrEnum):
    RUNNING = "running"
    LQC_COMPLETED = "lqc_completed"
    PLANNING = "planning"
    COMPLETED = "completed"


class ExperimentCreateRequest(BaseModel):
    question: str


class Reference(BaseModel):
    id: str
    title: str
    authors: str
    journal: str
    year: int
    doi: str
    similarity: float
    type: Literal["preprint", "journal", "review"]


class QCSummaryParagraph(BaseModel):
    text: str
    citations: list[int] = Field(default_factory=list)
    continuation: str | None = None


class ExperimentFeedback(BaseModel):
    rating: int
    issue_tags: list[str] = Field(default_factory=list)
    annotation: str
    corrections: str


class QCResult(BaseModel):
    signal: Literal["not_found", "similar_work", "exact_match"]
    noveltyScore: float
    scanDuration: float
    databases: list[str] = Field(default_factory=list)
    references: list[Reference] = Field(default_factory=list)
    summary: list[QCSummaryParagraph] | None = None
    label_names: list[str] | None = None


class ProtocolStep(BaseModel):
    id: int
    title: str
    detail: str
    duration: str
    critical: bool
    notes: str | None = None


class ProtocolPhase(BaseModel):
    phase: str
    weekRange: str
    steps: list[ProtocolStep] = Field(default_factory=list)


class Material(BaseModel):
    id: int
    name: str
    catalog: str
    supplier: str
    unitCost: float
    qty: int
    unit: str
    total: float
    category: str
    leadTime: str


class BudgetCategory(BaseModel):
    name: str
    amount: float
    color: str
    percentage: float


class Budget(BaseModel):
    total: float
    categories: list[BudgetCategory] = Field(default_factory=list)


class TimelinePhase(BaseModel):
    phase: str
    start: float
    duration: float
    tasks: list[str] = Field(default_factory=list)
    color: str
    dependencies: list[str] | None = None


class ValidationMetric(BaseModel):
    metric: str
    target: str
    method: str
    critical: bool
    timepoint: str


class ExperimentPlanData(BaseModel):
    title: str
    question: str
    createdAt: str
    complexity: Literal["Low", "Medium", "High", "Very High"]
    teamSize: int
    totalWeeks: int
    overview: str
    hypothesis: str
    protocol: list[ProtocolPhase] = Field(default_factory=list)
    materials: list[Material] = Field(default_factory=list)
    budget: Budget
    timeline: list[TimelinePhase] = Field(default_factory=list)
    validation: list[ValidationMetric] = Field(default_factory=list)


class ExperimentResponse(BaseModel):
    experiment_id: str
    question: str
    status: ExperimentStatus
    created_at: str
    LQC: QCResult | None = Field(default=None, alias="LQC")
    plan: ExperimentPlanData | None = None
    feedback: ExperimentFeedback | None = None
