from typing import List, Optional, Literal, Any
from pydantic import BaseModel, Field

# 1. PIMO Architect Output
class PIMOArchitectOutput(BaseModel):
    population: str
    intervention: str
    mechanism: str
    outcome: str

# 2. Adversarial Agent Output
class Reference(BaseModel):
    id: str = "unknown"
    title: str = "unknown"
    authors: Any = "unknown"
    journal: Any = "unknown"
    year: Any = "unknown"
    doi: str = "unknown"
    url: str = "unknown"
    similarity: float = 0.0
    reference_type: str = Field(default="unknown", description="Must be 'journal' or 'preprint'")

class AdversarialAgentOutput(BaseModel):
    reasoning: str = Field(default="", description="Explain the step-by-step reasoning for the chosen signal and novelty score.")
    signal: str = Field(default="not_found", description="Must be 'similar_work', 'exact_match', or 'not_found'")
    noveltyScore: float = 0.0
    scanDuration: float = 0.0
    databases: List[str] = Field(default_factory=list)
    references: List[Reference] = Field(default_factory=list)

# 3. Remediation Agent Output
class RemediationAgentOutput(BaseModel):
    suggestion: str = "No suggestion provided."

# 4. QC Router Output
class QCRouterOutput(BaseModel):
    reasoning: str = Field(default="", description="Explain the routing decision and summary.")
    signal: str = Field(default="not_found", description="Must be 'similar_work', 'exact_match', or 'not_found'")
    noveltyScore: float = 0.0
    scanDuration: float = 0.0
    databases: List[str] = Field(default_factory=list)
    references: List[Reference] = Field(default_factory=list)
    suggestion: Optional[str] = None
    final_report_text: str = Field(default="", description="A beautifully formatted Markdown report synthesizing all findings.")
