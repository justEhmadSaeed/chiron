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

# Suppress noisy schema-conversion warnings from the LangChain Gemini adapter
logging.getLogger("langchain_google_genai").setLevel(logging.ERROR)

llm = ChatGoogleGenerativeAI(
    model=settings.llm_model,
    api_key=settings.gemini_api_key,
    temperature=0.7,
)

tavily_client = TavilyClient(api_key=settings.tavily_api_key)


def pimo_generator_node(state: AgentState) -> Dict[str, Any]:
    prompt = state.get("research_prompt", "")
    logger.info("--- [1/4] PIMO Architect")
    logger.info(f"  ↳ Decomposing hypothesis into PIMO components...")
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
    logger.info(f"  ✓ PIMO done. Population='{result.population[:60]}...'")
    return {"pimo_json": result.model_dump()}


def adversarial_evaluator_node(state: AgentState) -> Dict[str, Any]:
    hypothesis = state.get("research_prompt", "")
    experiment_id = state.get("experiment_id", "")
    pimo_json = state.get("pimo_json", {})

    logger.info("--- [2/4] Adversarial Evaluator")
    logger.info(f"  ↳ Experiment ID : {experiment_id or '(not set)'}")

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

    logger.info(f"  ↳ Tavily search query: '{search_query[:80]}...'")
    top_chunks: list[str] = []
    raw_results: list[dict] = []
    try:
        search_res = tavily_client.search(
            query=search_query, search_depth="advanced", include_raw_content=True
        )
        raw_results = search_res.get("results", [])
        logger.info(f"  ↳ Tavily returned {len(raw_results)} result(s).")

        logger.info("  ↳ Indexing results → Pinecone RAG cache...")
        top_chunks = store_and_retrieve_rag_chunks(
            query_text=search_query,
            raw_search_results=raw_results,
            experiment_id=experiment_id,
            top_k=5,
        )
        logger.info(f"  ↳ RAG retrieved {len(top_chunks)} relevant chunk(s).")
    except Exception as e:
        logger.error(f"  ✗ Tavily/RAG Error: {e}")

    evidence_str = "\n\n".join(top_chunks) if top_chunks else "No literature found."

    logger.info("  ↳ Fetching prior memory from Pinecone...")
    past_memory = retrieve_agent_memory(experiment_id, search_query, top_k=2)
    memory_str = "\n\n".join(past_memory) if past_memory else "No prior memory for this run."
    logger.info(f"  ↳ Memory chunks: {len(past_memory)}.")

    human_msg = (
        f"Hypothesis to Evaluate:\n{hypothesis}\n\n"
        f"PIMO Components:\n{json.dumps(pimo_json, indent=2)}\n\n"
        f"Prior Agent Memory:\n{memory_str}\n\n"
        f"Retrieved Evidence Chunks:\n{evidence_str}"
    )

    logger.info("  ↳ Calling LLM → running three-stage literature protocol...")
    structured_llm = llm.with_structured_output(AdversarialAgentOutput)
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_msg),
    ]

    eval_result = structured_llm.invoke(messages)
    logger.info(f"  ✓ Adversarial done. Signal: '{eval_result.signal}', "
                f"Novelty Score: {eval_result.noveltyScore}, "
                f"References found: {len(eval_result.references)}.")

    refs_summary = "; ".join(
        f"{getattr(r, 'title', 'Unknown')} ({getattr(r, 'year', '?')}) — similarity {getattr(r, 'similarity', 0.0):.2f}"
        for r in (eval_result.references if eval_result.references else [])
    ) or "No references."

    if experiment_id:
        logger.info("  ↳ Storing full reasoning in Pinecone memory...")
        store_agent_memory(
            experiment_id=experiment_id,
            hypothesis_text=hypothesis,
            reasoning=eval_result.reasoning,
            signal=eval_result.signal,
            novelty_score=eval_result.noveltyScore,
            references_summary=refs_summary,
        )
        logger.info("  ↳ Indexing hypothesis vector in Pinecone...")
        store_hypothesis_vector(experiment_id=experiment_id, hypothesis_text=hypothesis)
        logger.info("  ✓ Memory & hypothesis index updated.")

    return {
        "adversarial_json": eval_result.model_dump(),
        "search_evidence": evidence_str,
    }


def remediation_agent_node(state: AgentState) -> Dict[str, Any]:
    adversarial_json = state.get("adversarial_json", {})
    evidence_str = state.get("search_evidence", "")

    logger.info("--- [3/4] Remediation Agent")
    logger.info(f"  ↳ Signal: '{adversarial_json.get('signal')}', "
                f"Novelty: {adversarial_json.get('noveltyScore')}")

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

    logger.info("  ↳ Calling LLM → generating pivot suggestions...")
    structured_llm = llm.with_structured_output(RemediationAgentOutput)
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_msg),
    ]

    result = structured_llm.invoke(messages)

    if result is None:
        logger.warning("  ↳ Structured output failed, using fallback invoke.")
        fallback = llm.invoke(messages)
        sug_text = fallback.content if hasattr(fallback, "content") else str(fallback)
    else:
        sug_text = result.suggestion

    logger.info(f"  ✓ Remediation done. Suggestion length: {len(sug_text or '')} chars.")
    return {"remediation_suggestion": sug_text}


def qc_router_node(state: AgentState) -> Dict[str, Any]:
    adversarial_json = state.get("adversarial_json", {})
    suggestion = state.get("remediation_suggestion", None)

    logger.info("--- [4/4] QC Router")
    has_suggestion = bool(suggestion)
    logger.info(f"  ↳ Compiling final report. Remediation included: {has_suggestion}")

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

    logger.info("  ↳ Calling LLM → generating final QC report...")
    structured_llm = llm.with_structured_output(QCRouterOutput)
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_msg),
    ]

    result = structured_llm.invoke(messages)
    final_dict = result.model_dump()

    # Post-process references for frontend compatibility
    for i, ref in enumerate(final_dict.get("references", [])):
        ref["id"] = f"ref{i + 1}"
        if "reference_type" in ref:
            ref["type"] = ref.pop("reference_type")
        if "type" not in ref:
            ref["type"] = "journal"
        ref.pop("url", None)
        ref.pop("reasoning", None)

    # Strip internal fields the frontend doesn't need
    final_dict.pop("reasoning", None)
    final_dict.pop("final_report_text", None)

    logger.info(f"  ✓ QC Router done. Final signal: '{final_dict.get('signal')}', "
                f"Novelty: {final_dict.get('noveltyScore')}, "
                f"Summary paragraphs: {len(final_dict.get('summary', []))}.")
    logger.info("--- ADVERSARIAL PIPELINE COMPLETE")

    return {"final_client_report": json.dumps(final_dict, indent=2, ensure_ascii=False)}

