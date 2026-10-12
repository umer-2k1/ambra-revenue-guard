"""Provider-agnostic text embeddings.

Both supported providers return **768-dimensional** vectors, so the Qdrant
collections never need to know which one produced them:

* ``gemini`` - ``gemini-embedding-001`` via the current ``google-genai`` SDK
               (``output_dimensionality`` pinned to 768; free tier).
* ``groq``   - ``nomic-embed-text-v1_5`` via Groq's OpenAI-compatible
               ``/openai/v1/embeddings`` endpoint. Nomic models want a
               ``search_document:`` / ``search_query:`` task prefix, which we
               add automatically.

The public surface is just :func:`embed_text` and :func:`embed_texts`.
"""
from __future__ import annotations

import config

# Gemini task types (uppercase strings) map onto the same two intents.
TASK_DOC = "RETRIEVAL_DOCUMENT"
TASK_QUERY = "RETRIEVAL_QUERY"

_gemini_client = None
_groq_client = None


def _gemini():
    global _gemini_client
    if _gemini_client is None:
        from google import genai

        if not config.GEMINI_API_KEY:
            raise RuntimeError(
                "GEMINI_API_KEY is not set but EMBEDDING_PROVIDER=gemini."
            )
        _gemini_client = genai.Client(api_key=config.GEMINI_API_KEY)
    return _gemini_client


def _embed_gemini(texts: list[str], task_type: str) -> list[list[float]]:
    from google.genai import types

    client = _gemini()
    response = client.models.embed_content(
        model=config.GEMINI_EMBEDDING_MODEL,
        contents=list(texts),
        config=types.EmbedContentConfig(
            task_type=task_type,
            output_dimensionality=config.EMBEDDING_DIM,
        ),
    )
    return [list(embedding.values) for embedding in response.embeddings]


def _groq():
    global _groq_client
    if _groq_client is None:
        from openai import OpenAI

        if not config.GROQ_API_KEY:
            raise RuntimeError(
                "GROQ_API_KEY is not set but EMBEDDING_PROVIDER=groq."
            )
        _groq_client = OpenAI(api_key=config.GROQ_API_KEY, base_url=config.GROQ_BASE_URL)
    return _groq_client


def _embed_groq(texts: list[str], task_type: str) -> list[list[float]]:
    prefix = "search_query: " if task_type == TASK_QUERY else "search_document: "
    response = _groq().embeddings.create(
        model=config.GROQ_EMBEDDING_MODEL,
        input=[prefix + text for text in texts],
    )
    return [item.embedding for item in response.data]


def embed_texts(texts: str | list[str], task_type: str = TASK_DOC) -> list[list[float]]:
    """Embed one or more texts, returning a list of vectors."""
    batch = [texts] if isinstance(texts, str) else list(texts)
    if config.EMBEDDING_PROVIDER == "groq":
        return _embed_groq(batch, task_type)
    return _embed_gemini(batch, task_type)


def embed_text(text: str, task_type: str = TASK_DOC) -> list[float]:
    """Embed a single text, returning one vector."""
    return embed_texts([text], task_type)[0]
