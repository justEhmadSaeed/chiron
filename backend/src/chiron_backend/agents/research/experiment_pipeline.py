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
    logger.info("--- [1/3] Protocol Architect")
    logger.info("  ↳ Searching Tavily for experimental protocol literature...")

    search_results = _tavily_search(
        f"experimental protocol methodology for: {hypothesis}"
    )
    logger.info(f"  ↳ Tavily returned {len(search_results)} result(s).")

    logger.info("  ↳ Indexing results → Pinecone RAG cache...")
    rag_chunks = store_and_retrieve(
        namespace=PROTOCOL_NAMESPACE,
        query_text=hypothesis,
        raw_search_results=search_results,
        top_k=4,
    )
    logger.info(f"  ↳ RAG retrieved {len(rag_chunks)} relevant chunk(s).")

    rag_context = "\n\n---\n".join(rag_chunks) if rag_chunks else "No prior literature found."

    user_message = (
        f"HYPOTHESIS / RESEARCH QUESTION:\n{hypothesis}\n\n"
        f"RELEVANT LITERATURE (RAG):\n{rag_context}\n\n"
        f"Generate the experimental protocol JSON now."
    )

    logger.info("  ↳ Calling LLM → generating protocol + validation...")
    result = call_agent(AgentName.PROTOCOL_ARCHITECT, user_message, ProtocolArchitectOutput)
    global_state.update(result)
    logger.info(f"  ✓ Protocol Architect done. "
                f"Phases: {len(result.get('protocol', []))}, "
                f"Validation metrics: {len(result.get('validation', []))}.")


def _run_procurement_specialist(global_state: dict) -> None:
    logger.info("--- [2/3] Procurement Specialist")
    title = global_state.get('title', 'experiment')
    logger.info(f"  ↳ Experiment title: '{title}'")

    search_query = f"lab reagents suppliers pricing catalog numbers for: {title} experiment"
    logger.info("  ↳ Searching Tavily for supplier & reagent data...")
    search_results = _tavily_search(search_query)
    logger.info(f"  ↳ Tavily returned {len(search_results)} result(s).")

    logger.info("  ↳ Indexing results → Pinecone RAG cache...")
    rag_chunks = store_and_retrieve(
        namespace=PROCUREMENT_NAMESPACE,
        query_text=search_query,
        raw_search_results=search_results,
        top_k=4,
    )
    logger.info(f"  ↳ RAG retrieved {len(rag_chunks)} relevant chunk(s).")

    rag_context = "\n\n---\n".join(rag_chunks) if rag_chunks else "No supplier data found."

    user_message = (
        f"CURRENT EXPERIMENT JSON:\n{json.dumps(global_state, indent=2)}\n\n"
        f"SUPPLIER RAG CONTEXT:\n{rag_context}\n\n"
        f"Generate the materials Bill of Materials and append it to the JSON."
    )

    logger.info("  ↳ Calling LLM → generating Bill of Materials...")
    result = call_agent(AgentName.PROCUREMENT_SPECIALIST, user_message, ProcurementSpecialistOutput)
    global_state.update(result)
    logger.info(f"  ✓ Procurement Specialist done. "
                f"Materials: {len(result.get('materials', []))} line items.")


def _run_resource_manager(global_state: dict) -> None:
    logger.info("--- [3/3] Resource Manager")
    title = global_state.get('title', 'experiment')

    search_query = f"lab staffing timeline budget estimation for: {title} experiment"
    logger.info("  ↳ Searching Tavily for staffing & budget benchmarks...")
    search_results = _tavily_search(search_query)
    logger.info(f"  ↳ Tavily returned {len(search_results)} result(s).")

    logger.info("  ↳ Indexing results → Pinecone RAG cache...")
    rag_chunks = store_and_retrieve(
        namespace=RESOURCE_NAMESPACE,
        query_text=search_query,
        raw_search_results=search_results,
        top_k=3,
    )
    logger.info(f"  ↳ RAG retrieved {len(rag_chunks)} relevant chunk(s).")

    rag_context = "\n\n---\n".join(rag_chunks) if rag_chunks else "No resource data found."

    user_message = (
        f"CURRENT EXPERIMENT JSON:\n{json.dumps(global_state, indent=2)}\n\n"
        f"RESOURCE PLANNING RAG CONTEXT:\n{rag_context}\n\n"
        f"Calculate and append teamSize, totalWeeks, budget, and timeline."
    )

    logger.info("  ↳ Calling LLM → calculating staffing, budget, timeline...")
    result = call_agent(AgentName.RESOURCE_MANAGER, user_message, ResourceManagerOutput)
    global_state.update(result)
    budget_total = (result.get('budget') or {}).get('total', 0)
    logger.info(f"  ✓ Resource Manager done. "
                f"Team: {result.get('teamSize', '?')} people, "
                f"Timeline: {result.get('totalWeeks', '?')} weeks, "
                f"Budget: ${budget_total:,.0f}.")


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
    logger.info("------------------------------------------------------------")
    logger.info("  EXPERIMENT DESIGN PIPELINE  —  Starting")
    logger.info(f"  Hypothesis: {hypothesis[:100]}{'...' if len(hypothesis) > 100 else ''}")
    logger.info("------------------------------------------------------------")

    global_state: dict[str, Any] = {}

    try:
        _run_protocol_architect(hypothesis, global_state)
        _run_procurement_specialist(global_state)
        _run_resource_manager(global_state)

        global_state["createdAt"] = date.today().isoformat()
        complexity = _complexity(
            global_state.get("teamSize", 0),
            global_state.get("totalWeeks", 0),
        )
        global_state["complexity"] = complexity

        final = FinalExperimentReport.model_validate(global_state)
        logger.info("------------------------------------------------------------")
        logger.info(f"  ✅ PIPELINE COMPLETE  |  Complexity: {complexity}  "
                    f"|  Team: {global_state.get('teamSize')}  "
                    f"|  Weeks: {global_state.get('totalWeeks')}")
        logger.info("------------------------------------------------------------")
        return final.model_dump()

    finally:
        logger.info("  ↳ Cleaning up Pinecone RAG namespaces...")
        cleanup_namespaces()
