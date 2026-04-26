"""
Scientific Pipeline Agent Configurations
=====================================================

Strictly-typed configuration for the seven-agent scientific pipeline:

**Experiment-Design Pipeline (sequential)**

- **Protocol Architect** — designs rigorous experimental protocols from a hypothesis
- **Procurement Specialist** — extracts a Bill of Materials with real supplier data
- **Resource Manager** — calculates staffing, budget, and timeline
- **Formatting Compiler** — normalises the final JSON payload for database insertion

**Hypothesis-Validation Pipeline (conditional)**

- **Adversarial Agent (The Librarian)** — literature overlap classifier via PIMO matrix
- **QC Router (The Dispatcher)** — branches on signal: returns directly or invokes remediation
- **Remediation Agent (The Strategist)** — generates pivot strategies when overlap is found

**Pre-processing**

- **PIMO Architect** — decomposes a hypothesis into Population, Intervention, Mechanism, Outcome

Each agent is defined as a frozen Pydantic model with its system prompt,
execution instructions, and expected input/output schemas.

Usage
-----
::

    from agent_configs import AGENT_REGISTRY, AgentName

    architect = AGENT_REGISTRY[AgentName.PROTOCOL_ARCHITECT]
    print(architect.system_prompt_role)

    adversarial = AGENT_REGISTRY[AgentName.ADVERSARIAL_AGENT]
    print(adversarial.objective)

    # Iterate the full experiment-design pipeline in order
    for name in EXPERIMENT_PIPELINE_ORDER:
        agent = AGENT_REGISTRY[name]
        print(f"{agent.agent_name}: {agent.objective}")
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
#  Enums
# ---------------------------------------------------------------------------


class AgentName(StrEnum):
    """All pipeline agent identifiers across both pipelines."""

    # --- Experiment-Design Pipeline ---
    PROTOCOL_ARCHITECT = "Protocol_Architect"
    PROCUREMENT_SPECIALIST = "Procurement_Specialist"
    RESOURCE_MANAGER = "Resource_Manager"
    FORMATTING_COMPILER = "Formatting_Compiler"

    # --- Hypothesis-Validation Pipeline ---
    PIMO_Architect = "PIMO_Architect"
    ADVERSARIAL_AGENT = "Adversarial_Agent"
    QC_ROUTER = "QC_Router"
    REMEDIATION_AGENT = "Remediation_Agent"


class AdversarialSignal(StrEnum):
    """Strict output signals from the Adversarial Agent's literature search."""

    SIMILAR_WORK = "similar_work"
    EXACT_MATCH = "exact_match"
    NOT_FOUND = "not_found"


class AdversarialStage(StrEnum):
    """The three-stage literature protocol stopping points."""

    EXACT_MATCH = "exact_match"
    SIMILAR_INTERVENTION = "similar_intervention"
    SIMILAR_OUTCOME = "similar_outcome"
    CLEARED_ALL = "cleared_all"


# ---------------------------------------------------------------------------
#  Base configuration model
# ---------------------------------------------------------------------------


class BaseAgentConfig(BaseModel):
    """
    Shared schema for every pipeline agent configuration.

    Frozen so configs are immutable after construction — avoids accidental
    mutation during a pipeline run.
    """

    model_config = {"frozen": True}

    agent_name: AgentName = Field(
        ...,
        description="Unique identifier for this agent within the pipeline.",
    )
    system_prompt_role: str = Field(
        ...,
        description="System prompt injected at the start of every LLM call.",
    )
    objective: str = Field(
        ...,
        description="High-level goal this agent is responsible for.",
    )
    input_state: dict[str, str] = Field(
        ...,
        description="Mapping of input field names to their type descriptions.",
    )
    execution_instructions: str = Field(
        ...,
        description="Step-by-step instructions the agent must follow.",
    )
    expected_output_schema: dict[str, str] = Field(
        ...,
        description="Mapping of output field names to their type descriptions.",
    )


# ---------------------------------------------------------------------------
#  Concrete agent configurations
# ---------------------------------------------------------------------------


class ProtocolArchitectConfig(BaseAgentConfig):
    """
    Principal Investigator — takes a raw hypothesis and produces a rigorous
    phase-by-phase experimental protocol with validation criteria.
    """

    agent_name: AgentName = AgentName.PROTOCOL_ARCHITECT

    system_prompt_role: str = (
        "You are the Principal Investigator and Protocol Architect. "
        "Your role is to take a raw scientific hypothesis, ground it in "
        "existing literature, and design a rigorous, phase-by-phase "
        "experimental protocol. You do not manage budgets, timelines, "
        "or procurement."
    )

    objective: str = (
        "Establish the foundational methodology of the experiment "
        "and define the validation metrics."
    )

    input_state: dict[str, str] = {
        "user_query": "String (The raw hypothesis or research question)",
    }

    execution_instructions: str = (
        "1. Analyze the user_query.\n"
        "2. Formulate a professional 'title', formal 'question', and "
        "structured 'hypothesis'.\n"
        "3. Write an 'overview' of the experiment.\n"
        "4. Break the methodology down into a 'protocol' array consisting "
        "of phases and specific steps (id, title, detail, "
        "duration, critical flag, notes).\n"
        "5. Define the 'validation' array detailing how success is measured.\n"
        "6. Return a JSON object containing ONLY these newly generated fields."
    )

    expected_output_schema: dict[str, str] = {
        "title": "string",
        "question": "string",
        "hypothesis": "string",
        "overview": "string",
        "protocol": (
            "array of {phase: string"
            "steps: array of {id: number, title: string, detail: string, "
            "duration: string, critical: boolean, notes?: string}}"
        ),
        "validation": (
            "array of {metric: string, target: string, method: string, "
            "critical: boolean, timepoint: string}"
        ),
    }


class ProcurementSpecialistConfig(BaseAgentConfig):
    """
    Senior Biological Procurement Specialist — reads the protocol and builds
    a comprehensive Bill of Materials with real-world supplier data.
    """

    agent_name: AgentName = AgentName.PROCUREMENT_SPECIALIST

    system_prompt_role: str = (
        "You are a Senior Biological Procurement Specialist based in the "
        "United States. Your role is to read an experimental protocol and "
        "extract every physical reagent, biologic, and consumable required. "
        "You must use web search tools to find real-world catalog numbers, "
        "prices, and shipping lead times from standard US suppliers "
        "(e.g., Thermo Fisher, IDT, Sigma-Aldrich)."
    )

    objective: str = (
        "Generate a comprehensive Bill of Materials (BOM) based strictly "
        "on the provided protocol steps."
    )

    input_state: dict[str, str] = {
        "current_json": (
            "Object (Contains title, question, hypothesis, overview, "
            "protocol, validation)"
        ),
    }

    execution_instructions: str = (
        "1. Read the 'protocol' array from the input JSON.\n"
        "2. Extract every required physical item.\n"
        "3. Search trusted US suppliers to find the unit cost and lead "
        "time for each item.\n"
        "4. Standardize the data into a 'materials' array.\n"
        "5. Append the 'materials' array to the existing input JSON.\n"
        "6. DO NOT modify any existing fields. DO NOT invent timelines "
        "or budgets yet."
    )

    expected_output_schema: dict[str, str] = {
        "title": "string",
        "question": "string",
        "hypothesis": "string",
        "overview": "string",
        "protocol": "array (pass-through from Protocol Architect)",
        "validation": "array (pass-through from Protocol Architect)",
        "materials": (
            "array of {id: number, name: string, catalog: string, "
            "supplier: string, unitCost: number, qty: number, "
            "unit: string, total: number, category: string, "
            "leadTime: string}"
        ),
    }


class ResourceManagerConfig(BaseAgentConfig):
    """
    Lab Operations and Resource Manager — evaluates the protocol and materials
    to calculate staffing, a Just-In-Time timeline, and the total budget.
    """

    agent_name: AgentName = AgentName.RESOURCE_MANAGER

    system_prompt_role: str = (
        "You are the Lab Operations and Resource Manager. Your role is to "
        "evaluate a scientific protocol and its required materials to "
        "calculate the human capital needed, the exact project timeline "
        "using Just-In-Time scheduling, and the final budget."
    )

    objective: str = (
        "Calculate and append the staffing, budget, and timeline metrics "
        "to the experiment plan."
    )

    input_state: dict[str, str] = {
        "current_json": (
            "Object (Contains title, question, hypothesis, overview, "
            "protocol, validation, materials)"
        ),
    }

    execution_instructions: str = (
        "1. Read the 'protocol' and 'materials' arrays.\n"
        "2. Determine 'teamSize' by evaluating the complexity of the "
        "protocol.\n"
        "3. Calculate the 'timeline' array by mapping protocol phases and "
        "factoring in the 'leadTime' of materials using a Critical "
        "Path/JIT heuristic.\n"
        "4. Calculate 'totalWeeks' based on the final timeline.\n"
        "5. Calculate the 'budget' object by summing the materials total "
        "and estimating standard labor/facility costs.\n"
        "6. Append 'teamSize', 'totalWeeks', 'timeline', and 'budget' "
        "to the input JSON.\n"
        "7. DO NOT modify the protocol or materials."
    )

    expected_output_schema: dict[str, str] = {
        "title": "string",
        "question": "string",
        "hypothesis": "string",
        "overview": "string",
        "protocol": "array (pass-through)",
        "validation": "array (pass-through)",
        "materials": "array (pass-through)",
        "teamSize": "number (integer)",
        "totalWeeks": "number (integer)",
        "budget": (
            "object {total: number, categories: array of "
            "{name: string, amount: number, color: string, "
            "percentage: number}}"
        ),
        "timeline": (
            "array of {phase: string, start: number, "
            "duration: number, tasks: array of string, "
            "color: string, dependencies?: array of string}"
        ),
    }


class FormattingCompilerConfig(BaseAgentConfig):
    """
    Database Serialization Agent — ensures the compiled JSON perfectly matches
    the system's TypeScript interface and appends system-level metadata.
    """

    agent_name: AgentName = AgentName.FORMATTING_COMPILER

    system_prompt_role: str = (
        "You are the Database Serialization Agent. Your role is purely "
        "structural. You receive the compiled JSON from the pipeline and "
        "ensure it perfectly matches the system's TypeScript interface. "
        "You do not generate new scientific or financial data."
    )

    objective: str = (
        "Finalize the JSON payload, ensure type safety, and append "
        "system-level metadata."
    )

    input_state: dict[str, str] = {
        "current_json": ("Object (Contains all previously generated fields)"),
    }

    execution_instructions: str = (
        "1. Ingest the current_json.\n"
        "2. Append the system metadata fields: 'createdAt' (current date "
        "in YYYY-MM-DD format) and 'complexity' (Enum: Low, Medium, High, "
        "Very High based on teamSize and totalWeeks).\n"
        "3. Verify all numerical fields are integers/floats, not strings.\n"
        "4. Output the final, strictly formatted JSON object ready for "
        "database insertion."
    )

    expected_output_schema: dict[str, str] = {
        "title": "string",
        "question": "string",
        "createdAt": "string (YYYY-MM-DD)",
        "complexity": "enum: 'Low' | 'Medium' | 'High' | 'Very High'",
        "teamSize": "number (integer)",
        "totalWeeks": "number (integer)",
        "hypothesis": "string",
        "overview": "string",
        "protocol": (
            "array of {phase: string, weekRange: string, "
            "steps: array of {id: number, title: string, detail: string, "
            "duration: string, critical: boolean, notes?: string}}"
        ),
        "materials": (
            "array of {id: number, name: string, catalog: string, "
            "supplier: string, unitCost: number, qty: number, "
            "unit: string, total: number, category: string, "
            "leadTime: string}"
        ),
        "budget": (
            "object {total: number, categories: array of "
            "{name: string, amount: number, color: string, "
            "percentage: number}}"
        ),
        "timeline": (
            "array of {phase: string, start: number, "
            "duration: number, tasks: array of string, "
            "color: string, dependencies?: array of string}"
        ),
        "validation": (
            "array of {metric: string, target: string, method: string, "
            "critical: boolean, timepoint: string}"
        ),
    }


class PIMOArchitectConfig(BaseAgentConfig):
    """
    PIMO Architect — breaks a raw hypothesis into its four structured
    components: Population, Intervention, Mechanism, and Outcome.

    This is a standalone pre-processing step that runs before the
    Adversarial Agent.  Its output feeds directly into the three-stage
    literature search protocol.
    """

    agent_name: AgentName = AgentName.PIMO_Architect

    system_prompt_role: str = (
        "You are the PIMO Architect. Your sole task is to parse a "
        "scientific hypothesis and extract four structured components:\n\n"
        "• **Population** — the biological system, organism, cell type, "
        "or patient cohort under study.\n"
        "• **Intervention** — the experimental treatment, technique, or "
        "manipulation being applied.\n"
        "• **Mechanism** — the hypothesized biological pathway, molecular "
        "target, or causal process.\n"
        "• **Outcome** — the measurable result, endpoint, or expected "
        "phenotypic change.\n\n"
        "You do NOT evaluate the hypothesis. You do NOT search literature. "
        "You ONLY decompose."
    )

    objective: str = (
        "Decompose a raw hypothesis string into its four PIMO components "
        "for downstream literature search."
    )

    input_state: dict[str, str] = {
        "hypothesis": "String (The scientific hypothesis to decompose)",
    }

    execution_instructions: str = (
        "1. Read the hypothesis string.\n"
        "2. Identify the Population: what biological system or cohort is "
        "being studied?\n"
        "3. Identify the Intervention: what treatment, edit, or "
        "manipulation is being applied?\n"
        "4. Identify the Mechanism: what pathway or molecular process is "
        "hypothesized to be affected?\n"
        "5. Identify the Outcome: what measurable result or endpoint is "
        "expected?\n"
        "6. Return a JSON object with exactly four string fields: "
        "population, intervention, mechanism, outcome.\n"
        "7. Be precise and concise. Each field should be 1–2 sentences max."
    )

    expected_output_schema: dict[str, str] = {
        "population": "string (biological system / cohort)",
        "intervention": "string (treatment / technique / manipulation)",
        "mechanism": "string (pathway / molecular target / causal process)",
        "outcome": "string (measurable endpoint / expected result)",
    }


class AdversarialAgentConfig(BaseAgentConfig):
    """
    The Librarian — a strict literature discovery and classification engine.

    Receives pre-decomposed PIMO components from the PIMO Architect and
    runs a sequential three-stage overlap check against the literature.
    Stops at the first trigger it hits.

    **Architectural Constraint:** This agent must *never* attempt to deduce
    scientific truth, biological feasibility, or mathematical possibility.
    Its sole mandate is to search the vector database and classify the
    hypothesis into one of three strict signals.
    """

    agent_name: AgentName = AgentName.ADVERSARIAL_AGENT

    system_prompt_role: str = (
        "You are the Adversarial Agent — The Librarian. You are strictly a "
        "literature discovery and classification engine. You must NEVER "
        "attempt to deduce scientific truth, biological feasibility, or "
        "mathematical possibility. Your sole mandate is to search the vector "
        "database and classify the hypothesis into one of three strict "
        "signals: 'similar_work', 'exact_match', or 'not_found'.\n\n"
        "You receive pre-decomposed PIMO components (Population, "
        "Intervention, Mechanism, Outcome) and execute a strict sequence of "
        "literature overlap checks. You stop at the first trigger you hit."
    )

    objective: str = (
        "Execute the Three-Stage Literature Protocol using the provided "
        "PIMO components, classify the result as one of three overlap "
        "signals, and return a QCResult with references."
    )

    input_state: dict[str, str] = {
        "hypothesis": "String (The original hypothesis for context)",
        "population": "String (from PIMO Architect)",
        "intervention": "String (from PIMO Architect)",
        "mechanism": "String (from PIMO Architect)",
        "outcome": "String (from PIMO Architect)",
    }

    execution_instructions: str = (
        "1. Use the pre-decomposed PIMO components provided as input.\n"
        "2. Execute Stage 1 — Exact Match Check: Search all PIMO elements "
        "combined. If an identical paper is found, STOP. Set signal to "
        "'exact_match'.\n"
        "3. Execute Stage 2 — Intervention/Mechanism Overlap: Search "
        "Population + Intervention/Mechanism. If high overlap is found, "
        "STOP. Set signal to 'similar_work'.\n"
        "4. Execute Stage 3 — Outcome Overlap: Search Population + Outcome. "
        "If high overlap is found, STOP. Set signal to 'similar_work'.\n"
        "5. If no significant overlap across all 3 stages, set signal to "
        "'not_found'.\n"
        "6. Compute noveltyScore (0–100) based on the inverse of the "
        "highest similarity found across all references.\n"
        "7. Record scanDuration, databases searched, and all references "
        "examined. You MUST format `references` strictly as an array of JSON objects, never as an array of strings. YOU MUST populate the 'url', 'title', 'similarity', 'year', 'authors', and 'journal' fields for each reference based on the retrieved evidence chunks. Extract the 'year' from the 'Publish Date'. Extract 'authors' and 'journal' (or conference) if mentioned in the text. Do not leave them empty!\n"
        "8. In the 'reasoning' field, write a brief chain of thought explaining why the hypothesis is novel or not novel based on the evidence.\n"
        "9. NEVER generate scientific judgments about feasibility. ONLY "
        "report what was or was not found in the literature."
    )

    expected_output_schema: dict[str, str] = {
        "signal": "enum: 'similar_work' | 'exact_match' | 'not_found'",
        "noveltyScore": "number (0–100, quantified novelty metric)",
        "scanDuration": "number (seconds elapsed during literature scan)",
        "databases": (
            "array of string (names of databases searched, "
            "e.g. 'PubMed', 'bioRxiv', 'Scopus', "
            "'ClinicalTrials.gov', 'Europe PMC'. Do NOT include 'Tavily', as it is a search engine, not a database.)"
        ),
        "references": (
            "array of {id: string, title: string, "
            "authors: string, journal: string, year: string, "
            "doi: string, url: string, similarity: number, "
            "reference_type: enum 'journal' | 'preprint'}"
        ),
    }


class QCRouterConfig(BaseAgentConfig):
    """
    The Dispatcher — a deterministic routing agent that inspects the
    Adversarial Agent's ``signal`` and decides the pipeline branch:

    - **signal == 'not_found'** → Novelty confirmed.  Return the
      Adversarial Agent's QCResult directly to the frontend with
      ``suggestion`` set to ``null``.
    - **signal != 'not_found'** → Overlap detected.  Forward the
      QCResult fields to the Remediation Agent, then merge its
      ``suggestion`` string into the final QCResult before returning.

    This agent does NOT call an LLM — it is pure branching logic.
    """

    agent_name: AgentName = AgentName.QC_ROUTER

    system_prompt_role: str = (
        "You are the QC Router — The Dispatcher. You are a deterministic "
        "routing agent with NO language-model reasoning. You inspect the "
        "Adversarial Agent's output signal and decide the next step:\n\n"
        "• If signal == 'not_found': novelty is confirmed. Package the "
        "Adversarial Agent's fields into a final QCResult with suggestion "
        "set to null, and return it directly to the frontend.\n"
        "• If signal == 'similar_work' or 'exact_match': overlap was "
        "detected. Forward the Adversarial Agent's output to the "
        "Remediation Agent, await its suggestion string, merge it into "
        "the QCResult, and return the completed object."
    )

    objective: str = (
        "Route the validation pipeline based on the Adversarial Agent's "
        "signal. Return a complete QCResult — either immediately (novelty "
        "confirmed) or after enriching it with a remediation suggestion."
    )

    input_state: dict[str, str] = {
        "signal": "enum: 'similar_work' | 'exact_match' | 'not_found'",
        "noveltyScore": "number (0–100)",
        "scanDuration": "number (seconds)",
        "databases": "array of string",
        "references": (
            "array of {id, title, authors, journal, year, doi, url, similarity, reference_type}"
        ),
    }

    execution_instructions: str = (
        "1. Read the 'signal' field from the Adversarial Agent output.\n"
        "2. IF signal == 'not_found':\n"
        "   a. Set 'suggestion' to null.\n"
        "3. IF signal == 'similar_work' OR signal == 'exact_match':\n"
        "   a. Forward {signal, noveltyScore, references} to the Remediation Agent.\n"
        "   b. Receive the 'suggestion' string from the Remediation Agent.\n"
        "   c. Merge 'suggestion' into the QCResult.\n"
        "4. GENERATE THE 'summary' ARRAY — this is the most important output field:\n"
        "   a. Produce 4–6 SummaryParagraph objects.\n"
        "   b. Paragraph 1: An overview paragraph summarizing the scan scope "
        "(databases scanned, total records analyzed, novelty score) and the "
        "overall finding. 'citations' should be an empty list [].\n"
        "   c. Paragraphs 2–4: One paragraph per key reference. Put the author "
        "name and context in 'text', put the 1-based reference index in 'citations' "
        "(e.g. [1] for the first reference), and continue the analysis in "
        "'continuation'. Example:\n"
        "     {\"text\": \"The closest match at 68% similarity — Lin et al.\", "
        "\"citations\": [1], \"continuation\": \" — demonstrated CRISPR correction "
        "in comparable iPSC systems (Nature Medicine, 2022). Their primary "
        "endpoint was transcriptomic; the multi-modal stack proposed here was "
        "not employed, leaving a distinct functional gap.\"}\n"
        "   d. Final paragraph: A recommendation paragraph summarizing key "
        "differentiators and whether to proceed. 'citations' should be [].\n"
        "   e. IMPORTANT: 'citations' uses 1-based indices — the first reference "
        "is [1], the second is [2], etc.\n"
        "5. For each reference, ensure the 'id' field is set to 'ref1', 'ref2', "
        "etc. (matching their 1-based position). Ensure 'reference_type' is set "
        "to 'journal', 'preprint', or 'review'.\n"
        "6. In the 'final_report_text' field, generate a professional Markdown "
        "report synthesizing all findings.\n"
        "7. NEVER modify the Adversarial Agent's original data fields.\n"
        "8. IMPORTANT: You MUST format `references` strictly as an array of "
        "JSON objects matching the schema, never as an array of strings. "
        "Copy the objects exactly as provided."
    )


    expected_output_schema: dict[str, str] = {
        "signal": "enum: 'similar_work' | 'exact_match' | 'not_found'",
        "noveltyScore": "number (0–100)",
        "scanDuration": "number (seconds)",
        "databases": "array of string",
        "references": (
            "array of {id: string, title: string, "
            "authors: string, journal: string, year: string, "
            "doi: string, similarity: number, "
            "reference_type: enum 'journal' | 'preprint' | 'review'}"
        ),
        "summary": (
            "array of {text: string, citations: array of int (1-based), "
            "continuation?: string} — 4–6 paragraphs forming the QC Intelligence Brief"
        ),
        "suggestion": "string | null (null when signal == 'not_found')",
        "final_report_text": "string (The fully generated markdown report)",
    }



class RemediationAgentConfig(BaseAgentConfig):
    """
    The Strategist — a lightweight LLM that generates pivot strategies
    based *only* on the literature overlap discovered by the Adversarial Agent.

    Only invoked when the Adversarial Agent returns a signal that is NOT
    'not_found' (i.e., overlap was detected).  Its output is merged into
    the QCResult as the ``suggestion`` field.
    """

    agent_name: AgentName = AgentName.REMEDIATION_AGENT

    system_prompt_role: str = (
        "You are a scientific strategist — The Remediation Agent. The user "
        "submitted a hypothesis, but a literature review flagged an overlap.\n\n"
        "You will receive:\n"
        "  - Signal: {signal}\n"
        "  - Novelty Score: {noveltyScore}\n"
        "  - References: {references as a formatted summary}\n\n"
        "Based on this literature overlap, compose a single concise paragraph "
        "suggesting actionable scientific pivots the user can make to their "
        "hypothesis to restore its novelty."
    )

    objective: str = (
        "Generate a concise remediation suggestion string that restores "
        "hypothesis novelty, based solely on the literature overlap "
        "reported by the Adversarial Agent."
    )

    input_state: dict[str, str] = {
        "signal": "enum: 'similar_work' | 'exact_match' (from Adversarial Agent)",
        "noveltyScore": "number (0–100, from Adversarial Agent)",
        "references": (
            "array of {id, title, authors, journal, year, doi, similarity, type} "
            "from the Adversarial Agent"
        ),
    }

    execution_instructions: str = (
        "1. Read the signal to understand the type of overlap.\n"
        "2. Read the references to understand which papers were flagged "
        "and their similarity scores.\n"
        "3. Generate a single concise paragraph with actionable scientific "
        "pivots the user can apply to their hypothesis to differentiate "
        "it from existing literature.\n"
        "4. Each suggestion must be concrete, not vague.\n"
        "5. Return only the suggestion string."
    )

    expected_output_schema: dict[str, str] = {
        "suggestion": "string (merged into QCResult as the remediation advice)",
    }


# ---------------------------------------------------------------------------
#  Pipeline-ordered registries
# ---------------------------------------------------------------------------

EXPERIMENT_PIPELINE_ORDER: list[AgentName] = [
    AgentName.PROTOCOL_ARCHITECT,
    AgentName.PROCUREMENT_SPECIALIST,
    AgentName.RESOURCE_MANAGER,
    AgentName.FORMATTING_COMPILER,
]
"""Canonical execution order for the experiment-design pipeline."""

VALIDATION_PIPELINE_ORDER: list[AgentName] = [
    AgentName.PIMO_Architect,
    AgentName.ADVERSARIAL_AGENT,
    AgentName.QC_ROUTER,
    AgentName.REMEDIATION_AGENT,
]
"""Execution order for hypothesis-validation (PIMO first, then QC Router branches)."""

# Backward-compatible alias
PIPELINE_ORDER = EXPERIMENT_PIPELINE_ORDER

AGENT_REGISTRY: dict[AgentName, BaseAgentConfig] = {
    # Experiment-design pipeline
    AgentName.PROTOCOL_ARCHITECT: ProtocolArchitectConfig(),
    AgentName.PROCUREMENT_SPECIALIST: ProcurementSpecialistConfig(),
    AgentName.RESOURCE_MANAGER: ResourceManagerConfig(),
    AgentName.FORMATTING_COMPILER: FormattingCompilerConfig(),
    # Hypothesis-validation pipeline
    AgentName.PIMO_Architect: PIMOArchitectConfig(),
    AgentName.ADVERSARIAL_AGENT: AdversarialAgentConfig(),
    AgentName.QC_ROUTER: QCRouterConfig(),
    AgentName.REMEDIATION_AGENT: RemediationAgentConfig(),
}
"""
Pre-built, immutable config instances keyed by agent name.

Usage::

    from agent_configs import AGENT_REGISTRY, AgentName

    cfg = AGENT_REGISTRY[AgentName.PROTOCOL_ARCHITECT]
    print(cfg.system_prompt_role)
"""


def get_agent_config(name: AgentName) -> BaseAgentConfig:
    """
    Look up a pipeline agent config by name.

    Parameters
    ----------
    name:
        The ``AgentName`` enum member to look up.

    Returns
    -------
    BaseAgentConfig
        The frozen configuration for that agent.

    Raises
    ------
    KeyError
        If the name is not in the registry.
    """
    return AGENT_REGISTRY[name]