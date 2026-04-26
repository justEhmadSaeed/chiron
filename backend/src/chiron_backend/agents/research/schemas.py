from typing import List, Optional
from pydantic import BaseModel, Field


class PIMOArchitectOutput(BaseModel):
    population: str
    intervention: str
    mechanism: str
    outcome: str


class Reference(BaseModel):
    id: str = Field(default="unknown", description="Unique reference ID, e.g. 'ref1', 'ref2'.")
    title: str = Field(default="unknown", description="Title of the paper.")
    authors: str = Field(default="unknown", description="Comma-separated author names.")
    journal: str = Field(default="unknown", description="Journal or conference name.")
    year: str = Field(default="unknown", description="Publication year as a string, e.g. '2023'.")
    doi: str = Field(default="unknown", description="DOI identifier.")
    url: str = Field(default="", description="URL to the paper.")
    similarity: float = Field(default=0.0, description="Similarity percentage 0-100.")
    reference_type: str = Field(default="journal", description="Must be 'journal', 'preprint', or 'review'.")



class AdversarialAgentOutput(BaseModel):
    reasoning: str = Field(default="", description="Step-by-step reasoning for signal and novelty score.")
    signal: str = Field(default="not_found", description="Must be 'similar_work', 'exact_match', or 'not_found'")
    noveltyScore: float = 0.0
    scanDuration: float = 0.0
    databases: List[str] = Field(default_factory=list)
    references: List[Reference] = Field(default_factory=list)


class RemediationAgentOutput(BaseModel):
    suggestion: str = "No suggestion provided."


class SummaryParagraph(BaseModel):
    """A single paragraph of the AI-generated QC summary with inline citation indices."""
    text: str = Field(default="", description="The main text of this paragraph, ending before any inline citations.")
    citations: List[int] = Field(default_factory=list, description="1-based indices into the references array that this paragraph cites. Empty list if none.")
    continuation: Optional[str] = Field(default=None, description="Optional continuation text that appears after the inline citations (e.g. the rest of the sentence).")


class QCRouterOutput(BaseModel):
    reasoning: str = Field(default="", description="Internal routing decision reasoning.")
    signal: str = Field(default="not_found", description="Must be 'similar_work', 'exact_match', or 'not_found'")
    noveltyScore: float = 0.0
    scanDuration: float = 0.0
    databases: List[str] = Field(default_factory=list)
    references: List[Reference] = Field(default_factory=list)
    summary: List[SummaryParagraph] = Field(
        default_factory=list,
        description=(
            "A structured array of paragraphs forming the QC Intelligence Brief. "
            "Each paragraph has 'text' (main content), 'citations' (1-based reference indices), "
            "and optional 'continuation' (text after citations). "
            "Generate 4–6 paragraphs: an overview paragraph, one paragraph per key reference "
            "with an inline citation, and a concluding recommendation paragraph."
        ),
    )
    suggestion: Optional[str] = None
    final_report_text: str = Field(default="", description="Beautifully formatted Markdown report synthesizing all findings.")
