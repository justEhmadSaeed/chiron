import json
import structlog
from typing import Any, Dict


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
from chiron_backend.agents.research.llm import get_client

logger = structlog.get_logger("research_agent")
settings = get_settings()

tavily_client = TavilyClient(api_key=settings.tavily_api_key)



def pimo_generator_node(state: AgentState) -> Dict[str, Any]:
    prompt = state.get("research_prompt", "")
    logger.info("[STAGE 1/4] PIMO Architect Started")
    
    config = AGENT_REGISTRY[AgentName.PIMO_Architect]
    system_prompt = (
        f"{config.system_prompt_role}\n\n"
        f"Objective: {config.objective}\n\n"
        f"Execution Instructions:\n{config.execution_instructions}"
    )

    client = get_client(settings.llm_model)
    try:
        result = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            model=settings.llm_model,
            response_model=PIMOArchitectOutput,
            max_retries=3,
        )
    except Exception as e:
        logger.error("[STAGE 1/4] PIMO structured output failed!", error=str(e))
        raise
        
    final_dict = result.model_dump()
    logger.info("[STAGE 1/4] PIMO Architect Completed", output=final_dict)
    return {"pimo_json": final_dict}

def adversarial_evaluator_node(state: AgentState) -> Dict[str, Any]:
    hypothesis = state.get("research_prompt", "")
    experiment_id = state.get("experiment_id", "")
    pimo_json = state.get("pimo_json", {})

    logger.info(f"[STAGE 2/4] Adversarial Evaluator Started (Experiment ID: {experiment_id})")

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
        search_res = tavily_client.search(
            query=search_query, search_depth="advanced", include_raw_content=True
        )
        raw_results = search_res.get("results", [])

        top_chunks = store_and_retrieve_rag_chunks(
            query_text=search_query,
            raw_search_results=raw_results,
            experiment_id=experiment_id,
            top_k=5,
        )
    except Exception as e:
        logger.error(f"Tavily/RAG Error: {e}")

    evidence_str = "\n\n".join(top_chunks) if top_chunks else "No literature found."

    past_memory = retrieve_agent_memory(experiment_id, search_query, top_k=2)
    memory_str = "\n\n".join(past_memory) if past_memory else "No prior memory for this run."

    human_msg = (
        f"Hypothesis to Evaluate:\n{hypothesis}\n\n"
        f"PIMO Components:\n{json.dumps(pimo_json, indent=2)}\n\n"
        f"Prior Agent Memory:\n{memory_str}\n\n"
        f"Retrieved Evidence Chunks:\n{evidence_str}"
    )

    client = get_client(settings.llm_model)
    try:
        eval_result = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": human_msg}
            ],
            model=settings.llm_model,
            response_model=AdversarialAgentOutput,
            max_retries=3,
        )
    except Exception as e:
        logger.error("[STAGE 2/4] Adversarial structured output failed!", error=str(e))
        raise

    refs_summary = "; ".join(
        f"{getattr(r, 'title', 'Unknown')} ({getattr(r, 'year', '?')}) — similarity {getattr(r, 'similarity', 0.0):.2f}"
        for r in (eval_result.references if eval_result.references else [])
    ) or "No references."

    if experiment_id:
        store_agent_memory(
            experiment_id=experiment_id,
            hypothesis_text=hypothesis,
            reasoning=eval_result.reasoning,
            signal=eval_result.signal,
            novelty_score=eval_result.noveltyScore,
            references_summary=refs_summary,
        )
        store_hypothesis_vector(experiment_id=experiment_id, hypothesis_text=hypothesis)

    final_dict = eval_result.model_dump()
    logger.info("[STAGE 2/4] Adversarial Evaluator Completed", output=final_dict)

    return {
        "adversarial_json": final_dict,
        "search_evidence": evidence_str,
    }

def remediation_agent_node(state: AgentState) -> Dict[str, Any]:
    adversarial_json = state.get("adversarial_json", {})
    evidence_str = state.get("search_evidence", "")

    logger.info("[STAGE 3/4] Remediation Agent Started (Overlap Detected)")

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

    client = get_client(settings.llm_model)
    try:
        result = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": human_msg}
            ],
            model=settings.llm_model,
            response_model=RemediationAgentOutput,
            max_retries=3,
        )
        sug_text = result.suggestion
    except Exception as e:
        logger.error("[STAGE 3/4] Remediation structured output failed!", error=str(e))
        raise

    logger.info("[STAGE 3/4] Remediation Agent Completed", suggestion_length=len(sug_text or ''))
    return {"remediation_suggestion": sug_text}

def qc_router_node(state: AgentState) -> Dict[str, Any]:
    adversarial_json = state.get("adversarial_json", {})
    suggestion = state.get("remediation_suggestion", None)

    logger.info("[STAGE 4/4] QC Router Started (Final Report Generating)")

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

    client = get_client(settings.llm_model)
    try:
        result = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": human_msg}
            ],
            model=settings.llm_model,
            response_model=QCRouterOutput,
            max_retries=3,
        )
    except Exception as e:
        logger.error("[STAGE 4/4] QC Router structured output failed!", error=str(e))
        raise
        
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

    logger.info("[STAGE 4/4] QC Router Completed", output=final_dict)
    logger.info("[PIPELINE COMPLETE] Adversarial Validation Finished")

    return {"final_client_report": json.dumps(final_dict, indent=2, ensure_ascii=False)}
