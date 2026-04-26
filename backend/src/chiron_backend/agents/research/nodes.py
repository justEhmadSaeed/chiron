import json
import logging
from typing import Any, Dict
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from tavily import TavilyClient

from chiron_backend.common.config import get_settings
from chiron_backend.agents.research.state import AgentState
from chiron_backend.agents.research.schemas import (
    PIMOArchitectOutput,
    AdversarialAgentOutput,
    RemediationAgentOutput,
    QCRouterOutput,
)
from chiron_backend.agents.research.agents_config import AGENT_REGISTRY, AgentName
from chiron_backend.agents.research.retriever import (
    store_and_retrieve_rag_chunks,
    store_agent_memory,
    retrieve_agent_memory,
    store_hypothesis_vector,
)

logger = logging.getLogger("research_agent")
settings = get_settings()

llm = ChatGoogleGenerativeAI(
    model=settings.llm_model,
    api_key=settings.gemini_api_key,
    temperature=0.7,
)

tavily_client = TavilyClient(api_key=settings.tavily_api_key)


def pimo_generator_node(state: AgentState) -> Dict[str, Any]:
    prompt = state.get("research_prompt", "")
    config = AGENT_REGISTRY[AgentName.PIMO_Architect]

    system_prompt = (
        f"{config.system_prompt_role}\n\n"
        f"Objective: {config.objective}\n\n"
        f"Execution Instructions:\n{config.execution_instructions}"
    )

    structured_llm = llm.with_structured_output(PIMOArchitectOutput)
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=prompt),
    ]

    result = structured_llm.invoke(messages)
    return {"pimo_json": result.model_dump()}


def adversarial_evaluator_node(state: AgentState) -> Dict[str, Any]:
    hypothesis = state.get("research_prompt", "")
    experiment_id = state.get("experiment_id", "")
    pimo_json = state.get("pimo_json", {})

    config = AGENT_REGISTRY[AgentName.ADVERSARIAL_AGENT]
    system_prompt = (
        f"{config.system_prompt_role}\n\n"
        f"Objective: {config.objective}\n\n"
        f"Execution Instructions:\n{config.execution_instructions}"
    )

    search_query = " ".join(filter(None, [
        pimo_json.get("population", ""),
        pimo_json.get("intervention", ""),
        pimo_json.get("mechanism", ""),
        pimo_json.get("outcome", ""),
    ])).strip() or hypothesis

    top_chunks: list[str] = []
    raw_results: list[dict] = []
    try:
        logger.info(f"Tavily: Searching → '{search_query}'")
        search_res = tavily_client.search(
            query=search_query, search_depth="advanced", include_raw_content=True
        )
        raw_results = search_res.get("results", [])
        logger.info(f"Tavily: Got {len(raw_results)} results.")

        top_chunks = store_and_retrieve_rag_chunks(
            query_text=search_query,
            raw_search_results=raw_results,
            experiment_id=experiment_id,
            top_k=5,
        )
        logger.info(f"RAG: Retrieved {len(top_chunks)} chunks.")
    except Exception as e:
        logger.error(f"Tavily/RAG Error: {e}")

    evidence_str = "\n\n".join(top_chunks) if top_chunks else "No literature found."

    # Pull any prior memory for this exact run (e.g. retries)
    past_memory = retrieve_agent_memory(experiment_id, search_query, top_k=2)
    memory_str = "\n\n".join(past_memory) if past_memory else "No prior memory for this run."

    human_msg = (
        f"Hypothesis to Evaluate:\n{hypothesis}\n\n"
        f"PIMO Components:\n{json.dumps(pimo_json, indent=2)}\n\n"
        f"Prior Agent Memory:\n{memory_str}\n\n"
        f"Retrieved Evidence Chunks:\n{evidence_str}"
    )

    structured_llm = llm.with_structured_output(AdversarialAgentOutput)
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_msg),
    ]

    eval_result = structured_llm.invoke(messages)

    # Build a concise references summary for memory storage
    refs_summary = "; ".join(
        f"{r.get('title', 'Unknown')} ({r.get('year', '?')}) — similarity {r.get('similarity', 0.0):.2f}"
        for r in (eval_result.references if eval_result.references else [])
    ) or "No references."

    # Store the full reasoning + metadata in the experiment's memory namespace
    if experiment_id:
        store_agent_memory(
            experiment_id=experiment_id,
            hypothesis_text=hypothesis,
            reasoning=eval_result.reasoning,
            signal=eval_result.signal,
            novelty_score=eval_result.noveltyScore,
            references_summary=refs_summary,
        )

        # Also index the hypothesis itself so it's searchable across all runs
        store_hypothesis_vector(experiment_id=experiment_id, hypothesis_text=hypothesis)

    return {
        "adversarial_json": eval_result.model_dump(),
        "search_evidence": evidence_str,
    }


def remediation_agent_node(state: AgentState) -> Dict[str, Any]:
    adversarial_json = state.get("adversarial_json", {})
    evidence_str = state.get("search_evidence", "")

    config = AGENT_REGISTRY[AgentName.REMEDIATION_AGENT]
    system_prompt = (
        f"{config.system_prompt_role}\n\n"
        f"Objective: {config.objective}\n\n"
        f"Execution Instructions:\n{config.execution_instructions}"
    )

    human_msg = (
        f"Signal: {adversarial_json.get('signal')}\n"
        f"Novelty Score: {adversarial_json.get('noveltyScore')}\n"
        f"References:\n{json.dumps(adversarial_json.get('references', []), indent=2)}\n\n"
        f"Full Retrieved Evidence Context:\n{evidence_str}"
    )

    structured_llm = llm.with_structured_output(RemediationAgentOutput)
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_msg),
    ]

    result = structured_llm.invoke(messages)

    if result is None:
        logger.warning("RemediationAgent: Structured output failed, using fallback.")
        fallback = llm.invoke(messages)
        sug_text = fallback.content if hasattr(fallback, "content") else str(fallback)
    else:
        sug_text = result.suggestion

    return {"remediation_suggestion": sug_text}


def qc_router_node(state: AgentState) -> Dict[str, Any]:
    adversarial_json = state.get("adversarial_json", {})
    suggestion = state.get("remediation_suggestion", None)

    config = AGENT_REGISTRY[AgentName.QC_ROUTER]
    system_prompt = (
        f"{config.system_prompt_role}\n\n"
        f"Objective: {config.objective}\n\n"
        f"Execution Instructions:\n{config.execution_instructions}"
    )

    human_msg = (
        f"Adversarial Output:\n{json.dumps(adversarial_json, indent=2)}\n\n"
        f"Remediation Suggestion (if any):\n{suggestion}"
    )

    structured_llm = llm.with_structured_output(QCRouterOutput)
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_msg),
    ]

    result = structured_llm.invoke(messages)
    final_dict = result.model_dump()

    return {"final_client_report": json.dumps(final_dict, indent=2, ensure_ascii=False)}
