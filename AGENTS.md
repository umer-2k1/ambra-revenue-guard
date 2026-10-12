# AGENTS.md — project conventions

Guidance for AI agents (and humans) working in this repo.

## Package manager
- **Frontend uses `pnpm` — always.** Do **not** use `npm` or `yarn` (no `package-lock.json`).
- Backend uses Python with a local **`.venv`** (`python3 -m venv .venv`).

## Stack
- **Backend:** Python 3.13, FastAPI, LangGraph (agentic workflow), SQLite, Qdrant.
- **LLM providers (switchable):** `LLM_PROVIDER=deepseek|groq`.
- **Embeddings (switchable, 768-dim):** `EMBEDDING_PROVIDER=gemini|groq`.
- **Vector store:** Qdrant — **Cloud** when `QDRANT_URL` is set, otherwise **local embedded** (`data/qdrant_db`).
- **Frontend:** React + Vite, **Tailwind CSS v4**, **shadcn/ui** (used heavily), `lucide-react` icons.

## Secrets
- `.env` holds all API keys and is **gitignored**. Never commit it.
- `.env.example` is the template — keep it in sync when adding config.

## Git
- Commit **frequently**, one logical change per commit, **Conventional Commits** (`feat:`, `fix:`, `chore:`, `docs:`, `test:`).
- Commit to `main`.

## Design system (Ambra)
- Palette: dark `#5C0A05`, orange `#FE4311`, warm `#F8F4F1`, card `#EEE7DE`, border `#DBD0C2`.
- Risk: high `#DC2626`, medium `#F59E0B`, low `#10B981`.
- Buttons are pill-shaped (`border-radius: 50px`). Cards ~16px radius. Warm palette, no harsh shadows.

## Run
- Backend: `cd backend && ../.venv/bin/uvicorn main:app --reload --port 8000`
- Frontend: `cd frontend && pnpm dev`
