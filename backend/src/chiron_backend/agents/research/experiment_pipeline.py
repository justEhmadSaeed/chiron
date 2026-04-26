"""
Experiment Design Pipeline Orchestrator
=========================================
Sequential three-agent pipeline:
  1. Protocol Architect  — hypothesis → protocol + validation
  2. Procurement Specialist — protocol → + materials
  3. Resource Manager — materials → + budget + timeline

Each step:
  - performs a Tavily web search grounded on the agent's focus
  - stores results in its own Pinecone namespace (RAG cache)
  - retrieves top-k relevant chunks to enrich the LLM prompt
  - appends its output to a shared global JSON state

After the Resource Manager completes, the final JSON is returned and all
three Pinecone namespaces are cleaned up.
"""

from __future__ import annotations

import json
import logging
from datetime import date
from typing import Any

from tavily import TavilyClient

from chiron_backend.common.config import get_settings
from chiron_backend.agents.research.agents_config import AgentName
from chiron_backend.agents.research.llm import call_agent
from chiron_backend.agents.research.experiment_rag import (
    store_and_retrieve,
    cleanup_namespaces,
    PROTOCOL_NAMESPACE,
    PROCUREMENT_NAMESPACE,
    RESOURCE_NAMESPACE,
)
from chiron_backend.agents.research.experiment_schemas import (
    ProtocolArchitectOutput,
    ProcurementSpecialistOutput,
    ResourceManagerOutput,
    FinalExperimentReport,
)

logger = logging.getLogger("research_agent")
settings = get_settings()


def _tavily_search(query: str, max_results: int = 5) -> list[dict[str, Any]]:
    client = TavilyClient(api_key=settings.tavily_api_key)
    response = client.search(query=query, max_results=max_results)
    return response.get("results", [])


def _complexity(team_size: int, total_weeks: int) -> str:
    score = team_size + total_weeks
    if score <= 6:
        return "Low"
    if score <= 14:
        return "Medium"
    if score <= 24:
        return "High"
    return "Very High"


# ---------------------------------------------------------------------------
#  Agent steps
# ---------------------------------------------------------------------------


def _run_protocol_architect(hypothesis: str, global_state: dict) -> None:
    logger.info("[Orchestrator] Step 1 — Protocol Architect")

    search_results = _tavily_search(
        f"experimental protocol methodology for: {hypothesis}"
    )
    rag_chunks = store_and_retrieve(
        namespace=PROTOCOL_NAMESPACE,
        query_text=hypothesis,
        raw_search_results=search_results,
        top_k=4,
    )

    rag_context = "\n\n---\n".join(rag_chunks) if rag_chunks else "No prior literature found."

    user_message = (
        f"HYPOTHESIS / RESEARCH QUESTION:\n{hypothesis}\n\n"
        f"RELEVANT LITERATURE (RAG):\n{rag_context}\n\n"
        f"Generate the experimental protocol JSON now."
    )

    result = call_agent(AgentName.PROTOCOL_ARCHITECT, user_message, ProtocolArchitectOutput)
    global_state.update(result)
    logger.info("[Orchestrator] Protocol Architect complete.")


def _run_procurement_specialist(global_state: dict) -> None:
    logger.info("[Orchestrator] Step 2 — Procurement Specialist")

    search_query = (
        f"lab reagents suppliers pricing catalog numbers for: "
        f"{global_state.get('title', '')} experiment"
    )
    search_results = _tavily_search(search_query)
    rag_chunks = store_and_retrieve(
        namespace=PROCUREMENT_NAMESPACE,
        query_text=search_query,
        raw_search_results=search_results,
        top_k=4,
    )

    rag_context = "\n\n---\n".join(rag_chunks) if rag_chunks else "No supplier data found."

    user_message = (
        f"CURRENT EXPERIMENT JSON:\n{json.dumps(global_state, indent=2)}\n\n"
        f"SUPPLIER RAG CONTEXT:\n{rag_context}\n\n"
        f"Generate the materials Bill of Materials and append it to the JSON."
    )

    result = call_agent(AgentName.PROCUREMENT_SPECIALIST, user_message, ProcurementSpecialistOutput)
    global_state.update(result)
    logger.info("[Orchestrator] Procurement Specialist complete.")


def _run_resource_manager(global_state: dict) -> None:
    logger.info("[Orchestrator] Step 3 — Resource Manager")

    search_query = (
        f"lab staffing timeline budget estimation for: "
        f"{global_state.get('title', '')} experiment"
    )
    search_results = _tavily_search(search_query)
    rag_chunks = store_and_retrieve(
        namespace=RESOURCE_NAMESPACE,
        query_text=search_query,
        raw_search_results=search_results,
        top_k=3,
    )

    rag_context = "\n\n---\n".join(rag_chunks) if rag_chunks else "No resource data found."

    user_message = (
        f"CURRENT EXPERIMENT JSON:\n{json.dumps(global_state, indent=2)}\n\n"
        f"RESOURCE PLANNING RAG CONTEXT:\n{rag_context}\n\n"
        f"Calculate and append teamSize, totalWeeks, budget, and timeline."
    )

    result = call_agent(AgentName.RESOURCE_MANAGER, user_message, ResourceManagerOutput)
    global_state.update(result)
    logger.info("[Orchestrator] Resource Manager complete.")


# ---------------------------------------------------------------------------
#  Public entry point
# ---------------------------------------------------------------------------


def run_experiment_pipeline(hypothesis: str) -> dict[str, Any]:
    """
    Execute the full three-agent experiment design pipeline.

    Parameters
    ----------
    hypothesis:
        Raw user hypothesis string.

    Returns
    -------
    dict
        Final compiled experiment JSON matching ``FinalExperimentReport``.
    """
    logger.info("[Orchestrator] Starting experiment design pipeline.")

    global_state: dict[str, Any] = {}

    try:
        _run_protocol_architect(hypothesis, global_state)
        _run_procurement_specialist(global_state)
        _run_resource_manager(global_state)

        # Finalize: append system metadata without calling a 4th LLM
        global_state["createdAt"] = date.today().isoformat()
        global_state["complexity"] = _complexity(
            global_state.get("teamSize", 0),
            global_state.get("totalWeeks", 0),
        )

        final = FinalExperimentReport.model_validate(global_state)
        logger.info("[Orchestrator] Pipeline complete. Cleaning up RAG namespaces...")
        return final.model_dump()

    finally:
        cleanup_namespaces()
