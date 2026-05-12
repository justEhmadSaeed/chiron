"""
Instructor-Based Structured Extraction LLM Factory
======================================================
This module replaces LangChain and LangGraph with the industry-standard
`instructor` library and native `google.generativeai` SDK.

By removing heavy LangChain abstractions, we significantly reduce execution
latency while maintaining strict Pydantic parsing and native error-retry loops.
"""

from __future__ import annotations

import structlog
from typing import Any, Type

from groq import Groq
import instructor
from pydantic import BaseModel

from chiron_backend.common.config import get_settings
from chiron_backend.agents.research.agents_config import (
    AGENT_REGISTRY,
    AgentName,
    BaseAgentConfig,
)

logger = structlog.get_logger("research_agent")
settings = get_settings()

_client_cache: dict[str, instructor.Instructor] = {}

def get_client(model_name: str) -> instructor.Instructor:
    if model_name not in _client_cache:
        client = Groq(
            api_key=settings.groq_api_key,
            timeout=120.0
        )
        _client_cache[model_name] = instructor.from_groq(
            client=client,
            mode=instructor.Mode.TOOLS,
        )
    return _client_cache[model_name]


def _build_system_prompt(config: BaseAgentConfig) -> str:
    """
    Builds the system instructions without needing to inject the raw JSON schema
    manually, because Instructor handles schema injection automatically at the API level.
    """
    return (
        f"{config.system_prompt_role}\n\n"
        f"Objective: {config.objective}\n\n"
        f"Instructions:\n{config.execution_instructions}\n\n"
        f"CRITICAL INSTRUCTION: Respond with ONLY a valid JSON object adhering strictly to the expected schema."
    )


# ---------------------------------------------------------------------------
#  Public API
# ---------------------------------------------------------------------------

def call_agent(
    agent_name: AgentName,
    user_message: str,
    output_schema: Type[BaseModel],
    model: str | None = None,
) -> dict[str, Any]:
    """
    Invoke a named agent using Instructor for zero-latency structured extraction.
    Instructor handles parsing the Pydantic schema and natively re-prompts the LLM 
    up to 3 times if it fails validation, avoiding any LangGraph overhead.
    """
    if model is None:
        model = settings.llm_model

    config = AGENT_REGISTRY[agent_name]
    logger.info(f"[AGENT START] {config.agent_name} Started")

    client = get_client(model)
    system_prompt = _build_system_prompt(config)

    try:
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            model=model,
            response_model=output_schema,
            max_retries=3,
        )
        
        final_dict = response.model_dump()
        logger.info(f"[AGENT COMPLETE] {config.agent_name} Completed", output=final_dict)
        return final_dict
        
    except Exception as e:
        logger.error(f"[AGENT ERROR] {config.agent_name} failed validation after 3 retries: {str(e)}")
        raise
