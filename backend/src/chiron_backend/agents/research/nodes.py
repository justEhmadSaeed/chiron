import json
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
from chiron_backend.agents.research.retriever import store_and_retrieve_rag_chunks, store_agent_memory, retrieve_agent_memory

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
    
    system_prompt = f"{config.system_prompt_role}\n\nObjective: {config.objective}\n\nExecution Instructions:\n{config.execution_instructions}"
    
    structured_llm = llm.with_structured_output(PIMOArchitectOutput)
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=prompt)
    ]
    
    result = structured_llm.invoke(messages)
    
    return {
        "pimo_json": result.model_dump()
    }

def adversarial_evaluator_node(state: AgentState) -> Dict[str, Any]:
    # Use the original research prompt as the hypothesis string context
    hypothesis = state.get("research_prompt", "")
    pimo_json = state.get("pimo_json", {})
    
    config = AGENT_REGISTRY[AgentName.ADVERSARIAL_AGENT]
    system_prompt = f"{config.system_prompt_role}\n\nObjective: {config.objective}\n\nExecution Instructions:\n{config.execution_instructions}"
    
    # 1. Search Tavily using the combination of PIMO components to get literature
    search_query = f"{pimo_json.get('population', '')} {pimo_json.get('intervention', '')} {pimo_json.get('mechanism', '')} {pimo_json.get('outcome', '')}".strip()
    if not search_query:
        search_query = hypothesis
        
    try:
        import logging
        logger = logging.getLogger("research_agent")
        logger.info(f"Tavily: Scraping for query -> '{search_query}'")
        search_res = tavily_client.search(query=search_query, search_depth="advanced", include_raw_content=True)
        raw_results = search_res.get('results', [])
        logger.info(f"Tavily: Scraped {len(raw_results)} domains successfully.")
        
        formatted_results = []
        for r in raw_results:
            content = r.get('raw_content') or r.get('content', '')
            formatted_results.append({
                "content": content, 
                "url": r.get('url', ''),
                "title": r.get('title', 'Unknown Title'),
                "score": r.get('score', 0.0),
                "published_date": r.get('published_date', 'Unknown Date')
            })
            
        top_chunks = store_and_retrieve_rag_chunks(query_text=search_query, raw_search_results=formatted_results, top_k=5)
        logger.info(f"Tavily/Chroma: Brought {len(top_chunks)} top relevant chunks into LLM context.")
    except Exception as e:
        import logging
        logging.getLogger("research_agent").error(f"Tavily/Chroma Error: {e}")
        top_chunks = []
        
    evidence_str = "\n\n".join(top_chunks) if top_chunks else "No literature found."
    
    # 2. Memory Context
    past_memory_chunks = retrieve_agent_memory(agent_id="adversarial_evaluator", query_text=search_query, top_k=2)
    memory_str = "\n\n".join(past_memory_chunks) if past_memory_chunks else "No past memory available for this context."
    
    human_msg = (
        f"Hypothesis to Evaluate:\n{hypothesis}\n\n"
        f"PIMO Components:\n{json.dumps(pimo_json, indent=2)}\n\n"
        f"Past Agent Memory:\n{memory_str}\n\n"
        f"Retrieved Evidence Chunks:\n{evidence_str}"
    )
    
    structured_llm = llm.with_structured_output(AdversarialAgentOutput)
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_msg)
    ]
    
    eval_result = structured_llm.invoke(messages)
    
    store_agent_memory(
        agent_id="adversarial_evaluator",
        hypothesis_text=hypothesis,
        reasoning=f"Novelty Score: {eval_result.noveltyScore}. Signal: {eval_result.signal}.",
        status=eval_result.signal
    )
    
    return {
        "adversarial_json": eval_result.model_dump(),
        "search_evidence": evidence_str
    }

def remediation_agent_node(state: AgentState) -> Dict[str, Any]:
    adversarial_json = state.get("adversarial_json", {})
    evidence_str = state.get("search_evidence", "")
    
    config = AGENT_REGISTRY[AgentName.REMEDIATION_AGENT]
    system_prompt = f"{config.system_prompt_role}\n\nObjective: {config.objective}\n\nExecution Instructions:\n{config.execution_instructions}"
    
    human_msg = (
        f"Signal: {adversarial_json.get('signal')}\n"
        f"Novelty Score: {adversarial_json.get('noveltyScore')}\n"
        f"References:\n{json.dumps(adversarial_json.get('references', []), indent=2)}\n\n"
        f"Full Retrieved Evidence Context:\n{evidence_str}"
    )
    
    structured_llm = llm.with_structured_output(RemediationAgentOutput)
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_msg)
    ]
    
    result = structured_llm.invoke(messages)
    
    if result is None:
        import logging
        logging.getLogger("research_agent").warning("RemediationAgent: Structured LLM failed to parse response, using fallback standard invoke.")
        fallback_res = llm.invoke(messages)
        sug_text = fallback_res.content if hasattr(fallback_res, "content") else str(fallback_res)
    else:
        sug_text = result.suggestion
        
    return {
        "remediation_suggestion": sug_text
    }

def qc_router_node(state: AgentState) -> Dict[str, Any]:
    # QC Router acts as final report LLM as requested by user
    adversarial_json = state.get("adversarial_json", {})
    suggestion = state.get("remediation_suggestion", None)
    
    config = AGENT_REGISTRY[AgentName.QC_ROUTER]
    
    # We pass the adversarial fields and the suggestion to generate the final QCResult
    structured_llm = llm.with_structured_output(QCRouterOutput)
    
    system_prompt = f"{config.system_prompt_role}\n\nObjective: {config.objective}\n\nExecution Instructions:\n{config.execution_instructions}"
    
    human_msg = (
        f"Adversarial Output:\n{json.dumps(adversarial_json, indent=2)}\n\n"
        f"Remediation Suggestion (if any):\n{suggestion}"
    )
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_msg)
    ]
    
    result = structured_llm.invoke(messages)
    
    final_dict = result.model_dump()
    
    return {
        "final_client_report": json.dumps(final_dict, indent=2, ensure_ascii=False)
    }
