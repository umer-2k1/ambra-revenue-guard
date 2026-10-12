"""LLM access layer (LangChain ``ChatOpenAI``).

One provider-agnostic entry point, :func:`ainvoke_json`, that returns a
validated Pydantic object. It tries LangChain structured output first and
falls back to parsing a plain JSON completion, which keeps us resilient across
DeepSeek and Groq (both OpenAI-compatible but with slightly different
function-calling behaviour).
"""
from __future__ import annotations

import re
from typing import Type, TypeVar

import config
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

_client: ChatOpenAI | None = None


def get_llm() -> ChatOpenAI:
    """Return a cached ChatOpenAI configured for the active provider."""
    global _client
    if _client is None:
        api_key, base_url, model = config.llm_settings()
        if not api_key:
            raise RuntimeError(
                f"No API key set for LLM_PROVIDER='{config.LLM_PROVIDER}'. "
                "Add it to .env (see .env.example)."
            )
        _client = ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url=base_url,
            temperature=0.2,
        )
    return _client


def _first_json_object(text: str) -> str:
    """Pull the outermost ``{...}`` object out of a model response."""
    text = (text or "").strip()
    match = re.search(r"\{.*\}", text, re.DOTALL)
    return match.group(0) if match else text


def _content_to_text(content) -> str:
    """Normalise LangChain message content (str or list of blocks) to text."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict):
                parts.append(block.get("text", ""))
            else:
                parts.append(str(block))
        return "".join(parts)
    return str(content)


async def ainvoke_json(system: str, user: str, schema: Type[T]) -> T:
    """Call the configured LLM and return a validated ``schema`` instance."""
    llm = get_llm()
    messages = [("system", system), ("human", user)]

    # Preferred path: native structured output (function calling).
    try:
        structured = llm.with_structured_output(schema)
        result = await structured.ainvoke(messages)
        if isinstance(result, schema):
            return result
        return schema.model_validate(result)
    except Exception:
        # Fallback: ask for plain JSON and parse it ourselves.
        response = await llm.ainvoke(messages)
        return schema.model_validate_json(_first_json_object(_content_to_text(response.content)))
