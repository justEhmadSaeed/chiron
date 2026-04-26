from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator, model_validator


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
    model_config = {"extra": "ignore", "populate_by_name": True}

    id: str = "unknown"
    title: str = "Unknown"
    authors: str = "Unknown"
    journal: str = "Unknown"
    year: int = 0
    doi: str = ""
    similarity: float = 0.0
    type: str = "journal"

    @model_validator(mode="before")
    @classmethod
    def _coerce_fields(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        # year: coerce anything non-int to 0
        raw_year = data.get("year", 0)
        try:
            data = {**data, "year": int(raw_year)}
        except (ValueError, TypeError):
            data = {**data, "year": 0}
        # map reference_type → type
        if "type" not in data and "reference_type" in data:
            data = {**data, "type": data["reference_type"]}
        # authors / journal can be lists — join them
        for field in ("authors", "journal"):
            val = data.get(field)
            if isinstance(val, list):
                data = {**data, field: ", ".join(str(v) for v in val)}
            elif val is None:
                data = {**data, field: "Unknown"}
        return data


class QCSummaryParagraph(BaseModel):
    model_config = {"extra": "ignore"}

    text: str = ""
    citations: list[int] = Field(default_factory=list)
    continuation: str | None = None

    @field_validator("citations", mode="before")
    @classmethod
    def _coerce_citations(cls, v: Any) -> list[int]:
        if not isinstance(v, list):
            return []
        result = []
        for item in v:
            try:
                result.append(int(item))
            except (ValueError, TypeError):
                pass
        return result


class SectionFeedback(BaseModel):
    rating: int
    issue_tags: list[str] = Field(default_factory=list)
    annotation: str
    corrections: str


ExperimentFeedback = dict[str, SectionFeedback]


class QCResult(BaseModel):
    model_config = {"extra": "ignore"}

    signal: str = "not_found"
    noveltyScore: float = 0.0
    scanDuration: float = 0.0
    databases: list[str] = Field(default_factory=list)
    references: list[Reference] = Field(default_factory=list)
    summary: list[QCSummaryParagraph] | None = None
    label_names: list[str] | None = None

    @field_validator("signal", mode="before")
    @classmethod
    def _coerce_signal(cls, v: Any) -> str:
        allowed = {"not_found", "similar_work", "exact_match"}
        if v in allowed:
            return v
        return "not_found"


class ProtocolStep(BaseModel):
    model_config = {"extra": "ignore"}

    id: int = 0
    title: str = ""
    detail: str = ""
    duration: str = ""
    critical: bool = False
    notes: str | None = None

    @field_validator("id", mode="before")
    @classmethod
    def _coerce_id(cls, v: Any) -> int:
        try:
            return int(v)
        except (ValueError, TypeError):
            return 0


class ProtocolPhase(BaseModel):
    model_config = {"extra": "ignore"}

    phase: str = ""
    weekRange: str = ""
    steps: list[ProtocolStep] = Field(default_factory=list)


class Material(BaseModel):
    model_config = {"extra": "ignore"}

    id: int = 0
    name: str = ""
    catalog: str = ""
    supplier: str = ""
    unitCost: float = 0.0
    qty: int = 1
    unit: str = ""
    total: float = 0.0
    category: str = ""
    leadTime: str = ""

    @field_validator("id", "qty", mode="before")
    @classmethod
    def _coerce_int(cls, v: Any) -> int:
        try:
            return int(v)
        except (ValueError, TypeError):
            return 0

    @field_validator("unitCost", "total", mode="before")
    @classmethod
    def _coerce_float(cls, v: Any) -> float:
        try:
            return float(v)
        except (ValueError, TypeError):
            return 0.0


class BudgetCategory(BaseModel):
    model_config = {"extra": "ignore"}

    name: str = ""
    amount: float = 0.0
    color: str = "#888888"
    percentage: float = 0.0

    @field_validator("amount", "percentage", mode="before")
    @classmethod
    def _coerce_float(cls, v: Any) -> float:
        try:
            return float(v)
        except (ValueError, TypeError):
            return 0.0


class Budget(BaseModel):
    model_config = {"extra": "ignore"}

    total: float = 0.0
    categories: list[BudgetCategory] = Field(default_factory=list)

    @field_validator("total", mode="before")
    @classmethod
    def _coerce_total(cls, v: Any) -> float:
        try:
            return float(v)
        except (ValueError, TypeError):
            return 0.0


class TimelinePhase(BaseModel):
    model_config = {"extra": "ignore"}

    phase: str = ""
    start: float = 0.0
    duration: float = 0.0
    tasks: list[str] = Field(default_factory=list)
    color: str = "#888888"
    dependencies: list[str] | None = None


class ValidationMetric(BaseModel):
    model_config = {"extra": "ignore"}

    metric: str = ""
    target: str = ""
    method: str = ""
    critical: bool = False
    timepoint: str = ""


class ExperimentPlanData(BaseModel):
    model_config = {"extra": "ignore"}

    title: str = ""
    question: str = ""
    createdAt: str = ""
    complexity: str = "Medium"
    teamSize: int = 1
    totalWeeks: int = 1
    overview: str = ""
    hypothesis: str = ""
    protocol: list[ProtocolPhase] = Field(default_factory=list)
    materials: list[Material] = Field(default_factory=list)
    budget: Budget = Field(default_factory=Budget)
    timeline: list[TimelinePhase] = Field(default_factory=list)
    validation: list[ValidationMetric] = Field(default_factory=list)

    @field_validator("teamSize", "totalWeeks", mode="before")
    @classmethod
    def _coerce_int(cls, v: Any) -> int:
        try:
            return int(v)
        except (ValueError, TypeError):
            return 1

    @field_validator("complexity", mode="before")
    @classmethod
    def _coerce_complexity(cls, v: Any) -> str:
        allowed = {"Low", "Medium", "High", "Very High"}
        return v if v in allowed else "Medium"


class ExperimentResponse(BaseModel):
    model_config = {"extra": "ignore", "populate_by_name": True}

    experiment_id: str
    question: str
    status: ExperimentStatus
    created_at: str
    LQC: QCResult | None = Field(default=None, alias="LQC")
    plan: ExperimentPlanData | None = None
    feedback: ExperimentFeedback | None = None
