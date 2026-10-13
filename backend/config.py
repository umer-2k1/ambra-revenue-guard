"""Central configuration.

Everything that differs between environments (API keys, provider choice,
storage paths) lives here so no other module reads ``os.environ`` directly.

Paths resolve relative to the **backend directory** (``backend/``), so the
backend is self-contained — important for deploying it as its own Vercel
project with ``Root Directory = backend``.

Two independent provider switches:

* ``LLM_PROVIDER``       = ``deepseek`` (default) | ``groq``
* ``EMBEDDING_PROVIDER`` = ``gemini``   (default) | ``groq``
"""
from __future__ import annotations

import os

from dotenv import load_dotenv

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(BACKEND_DIR)  # repo root (when running from a checkout)

# Load .env from the repo root, then backend/, then the cwd (first one wins).
load_dotenv(os.path.join(BASE_DIR, ".env"))
load_dotenv(os.path.join(BACKEND_DIR, ".env"))
load_dotenv()


def _path(env_key: str, default_rel: str) -> str:
    """Resolve a possibly-relative path against the backend directory."""
    value = os.getenv(env_key, default_rel)
    if not os.path.isabs(value):
        value = os.path.join(BACKEND_DIR, value)
    return os.path.normpath(value)


# ── Paths (relative to backend/) ─────────────────────────────────────────────
DATABASE_PATH = _path("DATABASE_PATH", "data/ambra_demo.db")
QDRANT_PATH = _path("QDRANT_PATH", "data/qdrant_db")
SEED_DATA_PATH = os.path.join(BACKEND_DIR, "data", "seed_denials.json")

# ── Database ─────────────────────────────────────────────────────────────────
# Set DATABASE_URL to use Postgres (e.g. Neon) — required in the cloud, where
# there is no persistent disk. Empty -> local SQLite at DATABASE_PATH.
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

# ── Vector store ─────────────────────────────────────────────────────────────
# Set QDRANT_URL (+ QDRANT_API_KEY) for Qdrant Cloud / any server. Empty ->
# embedded local store at QDRANT_PATH (local dev only).
QDRANT_URL = os.getenv("QDRANT_URL", "").strip()
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "").strip()

# ── Embeddings (768-dim from either provider) ────────────────────────────────
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "gemini").strip().lower()
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "768"))

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001").strip()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_EMBEDDING_MODEL = os.getenv("GROQ_EMBEDDING_MODEL", "nomic-embed-text-v1_5").strip()
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip()
GROQ_BASE_URL = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1").strip()

# ── LLM ──────────────────────────────────────────────────────────────────────
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "deepseek").strip().lower()

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "").strip()
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat").strip()
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com").strip()

# ── CORS ─────────────────────────────────────────────────────────────────────
# Comma-separated list of allowed browser origins (the Vercel frontend URL).
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS", "http://localhost:5173,http://localhost:3000"
    ).split(",")
    if origin.strip()
]


def llm_settings() -> tuple[str, str, str]:
    """Return ``(api_key, base_url, model)`` for the configured LLM provider."""
    if LLM_PROVIDER == "groq":
        return GROQ_API_KEY, GROQ_BASE_URL, GROQ_MODEL
    return DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL
