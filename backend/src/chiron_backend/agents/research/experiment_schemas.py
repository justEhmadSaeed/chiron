"""
Experiment Design Pipeline Schemas
====================================
All list fields are fully typed so Gemini's function-calling API
can derive the `items` schema correctly. `list[Any]` is not allowed.
"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
#  Shared sub-models
# ---------------------------------------------------------------------------

class ProtocolStep(BaseModel):
    id: int = 0
    title: str = ""
    detail: str = ""
    duration: str = ""
    critical: bool = False
    notes: Optional[str] = None


class ProtocolPhase(BaseModel):
    phase: str = ""
    weekRange: Optional[str] = None
    steps: list[ProtocolStep] = Field(default_factory=list)


class ValidationMetric(BaseModel):
    metric: str = ""
    target: str = ""
    method: str = ""
    critical: bool = False
    timepoint: str = ""


class Material(BaseModel):
    id: int = 0
    name: str = ""
    catalog: str = ""
    supplier: str = ""
    unitCost: float = 0.0
    qty: int = 0
    unit: str = ""
    total: float = 0.0
    category: str = ""
    leadTime: str = ""


class BudgetCategory(BaseModel):
    name: str = ""
    amount: float = 0.0
    color: str = ""
    percentage: float = 0.0


class Budget(BaseModel):
    total: float = 0.0
    categories: list[BudgetCategory] = Field(default_factory=list)


class TimelinePhase(BaseModel):
    phase: str = ""
    start: int = 0
    duration: int = 0
    tasks: list[str] = Field(default_factory=list)
    color: str = ""
    dependencies: Optional[list[str]] = None


# ---------------------------------------------------------------------------
#  Agent output schemas (fully typed, no list[Any])
# ---------------------------------------------------------------------------

class ProtocolArchitectOutput(BaseModel):
    title: str = ""
    question: str = ""
    hypothesis: str = ""
    overview: str = ""
    protocol: list[ProtocolPhase] = Field(default_factory=list)
    validation: list[ValidationMetric] = Field(default_factory=list)


class ProcurementSpecialistOutput(BaseModel):
    title: str = ""
    question: str = ""
    hypothesis: str = ""
    overview: str = ""
    protocol: list[ProtocolPhase] = Field(default_factory=list)
    validation: list[ValidationMetric] = Field(default_factory=list)
    materials: list[Material] = Field(default_factory=list)


class ResourceManagerOutput(BaseModel):
    title: str = ""
    question: str = ""
    hypothesis: str = ""
    overview: str = ""
    protocol: list[ProtocolPhase] = Field(default_factory=list)
    validation: list[ValidationMetric] = Field(default_factory=list)
    materials: list[Material] = Field(default_factory=list)
    teamSize: int = 0
    totalWeeks: int = 0
    budget: Optional[Budget] = None
    timeline: list[TimelinePhase] = Field(default_factory=list)


# ---------------------------------------------------------------------------
#  Final report (matches FormattingCompilerConfig.expected_output_schema)
# ---------------------------------------------------------------------------

class FinalExperimentReport(BaseModel):
    title: str = ""
    question: str = ""
    createdAt: str = ""
    complexity: str = "Medium"
    teamSize: int = 0
    totalWeeks: int = 0
    hypothesis: str = ""
    overview: str = ""
    protocol: list[ProtocolPhase] = Field(default_factory=list)
    materials: list[Material] = Field(default_factory=list)
    budget: Optional[Budget] = None
    timeline: list[TimelinePhase] = Field(default_factory=list)
    validation: list[ValidationMetric] = Field(default_factory=list)
