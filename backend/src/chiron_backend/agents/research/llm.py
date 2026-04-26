"""
Gemini LLM Factory
====================
Handles both Gemini models (which support response_mime_type) and Gemma models
(which don't). Uses the Pydantic model's real JSON Schema in prompts and
robust extraction to find the actual data JSON in mixed prose.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Type

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel

from chiron_backend.common.config import get_settings
from chiron_backend.agents.research.agents_config import (
    AGENT_REGISTRY,
    AgentName,
    BaseAgentConfig,
)

logger = logging.getLogger("research_agent")
settings = get_settings()

_llm_cache: dict[str, ChatGoogleGenerativeAI] = {}

_JSON_NATIVE_MODELS = {"gemini-2.0-flash", "gemini-2.0-pro", "gemini-1.5-flash", "gemini-1.5-pro"}


def _get_llm(model: str) -> ChatGoogleGenerativeAI:
    if model not in _llm_cache:
        kwargs: dict[str, Any] = {
            "model": model,
            "google_api_key": settings.gemini_api_key,
            "temperature": 0.3,
        }
        if model in _JSON_NATIVE_MODELS:
            kwargs["model_kwargs"] = {"response_mime_type": "application/json"}
        _llm_cache[model] = ChatGoogleGenerativeAI(**kwargs)
    return _llm_cache[model]


def _build_system_prompt(config: BaseAgentConfig, output_schema: Type[BaseModel]) -> str:
    # Use the Pydantic model's real JSON Schema (proper JSON, not hand-written descriptions)
    schema = json.dumps(output_schema.model_json_schema(), indent=2)
    return (
        f"{config.system_prompt_role}\n\n"
        f"Objective: {config.objective}\n\n"
        f"Instructions:\n{config.execution_instructions}\n\n"
        f"CRITICAL: Respond with ONLY a single valid JSON object. "
        f"No explanations, no markdown, no text before or after.\n\n"
        f"JSON Schema:\n{schema}"
    )


def _extract_json(text: str) -> str:
    """
    Extract the largest valid JSON object from text.
    Tries markdown fences first, then finds all top-level brace-matched
    candidates and returns the longest one that parses as valid JSON.
    """
    stripped = text.strip()

    # Case 1: Markdown fenced block
    fence_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", stripped, re.DOTALL)
    if fence_match:
        candidate = fence_match.group(1).strip()
        try:
            json.loads(candidate)
            return candidate
        except json.JSONDecodeError:
            pass

    # Case 2: Find all top-level { ... } candidates via brace matching
    candidates: list[str] = []
    i = 0
    while i < len(stripped):
        if stripped[i] == "{":
            depth = 0
            in_string = False
            escape_next = False
            for j in range(i, len(stripped)):
                ch = stripped[j]
                if escape_next:
                    escape_next = False
                    continue
                if ch == "\\":
                    escape_next = True
                    continue
                if ch == '"' and not escape_next:
                    in_string = not in_string
                    continue
                if in_string:
                    continue
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        candidates.append(stripped[i : j + 1])
                        i = j + 1
                        break
            else:
                i += 1
        else:
            i += 1

    # Sort candidates by length (longest first) and return first valid one
    candidates.sort(key=len, reverse=True)
    for candidate in candidates:
        try:
            json.loads(candidate)
            return candidate
        except json.JSONDecodeError:
            continue

    raise ValueError(f"No valid JSON found in LLM response. First 300 chars: {stripped[:300]}")


def call_agent(
    agent_name: AgentName,
    user_message: str,
    output_schema: Type[BaseModel],
    model: str | None = None,
) -> dict[str, Any]:
    """
    Invoke a named agent and return a validated dict matching output_schema.
    Works with both Gemini (JSON-native) and Gemma (prose-with-JSON) models.
    """
    if model is None:
        model = settings.llm_model

    config = AGENT_REGISTRY[agent_name]
    llm = _get_llm(model)

    messages = [
        SystemMessage(content=_build_system_prompt(config, output_schema)),
        HumanMessage(content=user_message),
    ]

    logger.info(f"  ➤  [{config.agent_name}] calling {model}...")
    response = llm.invoke(messages)

    content = response.content
    if isinstance(content, list):
        raw_text = "".join(
            block.get("text", str(block)) if isinstance(block, dict) else str(block)
            for block in content
        )
    else:
        raw_text = content

    raw_json = _extract_json(raw_text)
    parsed = output_schema.model_validate_json(raw_json)
    logger.info(f"  ✓  [{config.agent_name}] done.")
    return parsed.model_dump()
