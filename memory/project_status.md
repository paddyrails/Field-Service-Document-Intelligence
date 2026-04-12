---
name: RiteCare Project Status
description: Current build status, completed phases, pending work, and key architectural decisions
type: project
---

## Project: Field Service Document Intelligence — RiteCare AI Assistant

**Why:** Interview/work project for Synechron. AI-powered Slack assistant for RiteCare field officers using LangGraph, MCP tools, OpenAI GPT-4o-mini, MongoDB Atlas, FastAPI microservices.

**How to apply:** Use this to understand exactly where we left off and what needs to be done next.

---

## Completed

### Phase 1 — Foundation (Main Repo)
- `pyproject.toml`, `.env.example`, `shared/config.py`, `shared/logging.py`, `shared/exceptions.py`, `shared/utils/http_client.py`, `db/client.py`, `db/collections.py`

### Phase 2 — MongoDB Models
- `db/models/conversation.py`

### Phase 3 — BU Microservices (all 4 complete)
- BU1 `services/bu1_onboarding/` — port 8001
- BU2 `services/bu2_sales_maintenance/` — port 8002
- BU3 `services/bu3_billing_subscription/` — port 8003
- BU4 `services/bu4_support_fulfillment/` — port 8004
- Each has: `api/`, `service/`, `dao/`, `common/`, `ingestion/`, `Dockerfile`

### Phase 4 — LangGraph Agent (all files written)
- `agent/state.py`, `agent/prompts/system_prompt.py`
- `agent/nodes/intent_classifier.py`, `agent/nodes/tool_executor.py`, `agent/nodes/responder.py`
- `agent/graph.py`
- `ritecare_tools/tools/bu1_tools.py` through `bu4_tools.py`, `rag_tools.py`

### Infrastructure
- `docker-compose.yml` — all 4 BU services with volume mounts
- `docs/bu1`, `docs/bu2`, `docs/bu3`, `docs/bu4` — mounted as `/docs/buN:ro` in containers
- `seed_data.py` — seeds all 4 BUs via REST APIs
- `test_agent.py` — 10 test cases covering CRUD, RAG, cross-BU
- `run_agent.py` — interactive CLI chat runner
- `ARCHITECTURE.md` — Mermaid diagram of full system

---

## In Progress — BU1 Ingestion (last active work)

### What was just fixed
- `pipeline.py` was inserting into MongoDB directly — fixed to return `list[dict]` instead
- `customer_service.py` calls `run_pipeline()` → gets documents → calls `vector_dao.insert_chunks()`
- `vector_dao.py` — replaced `insert_chunk()` with `insert_chunks()` batch method
- `dependencies.py` — added `get_vector_dao()`, updated `get_customer_service()` to pass both DAOs
- `router.py` — added `ingest_router` with `POST /ingest` and `POST /rag/search` (separate from `/customers`)
- `main.py` — registered `ingest_router`

### Still needed — BU2, BU3, BU4 ingestion
BU1 ingestion is now correct. BU2, BU3, BU4 need the same treatment:
- `ingestion/__init__.py`, `ingestion/loaders/__init__.py`
- `ingestion/loaders/pdf_loader.py`, `ingestion/loaders/text_loader.py`
- `ingestion/chunker.py`, `ingestion/embedder.py`
- `ingestion/pipeline.py` — same as BU1 (returns list[dict], no DB insert)
- `dao/vector_dao.py` — same as BU1 but with BU-specific collection name
- `api/dependencies.py` — add `get_vector_dao()`
- `api/router.py` — add `ingest_router` with `/ingest` and `/rag/search`
- `api/main.py` — register `ingest_router`

---

## Pending

### Phase 5 — Slack Gateway (deferred)
- `slack_gateway/main.py`, `handlers.py`, `channel_router.py`

---

## Key Architecture Decisions

- `mcp/` renamed to `ritecare_tools/` — conflicts with installed `mcp>=1.0` package
- Rate limiting via `SlowAPIMiddleware` only — no per-route `@limiter` decorators
- `pipeline.py` returns `list[dict]`, does NOT insert — VectorDAO handles persistence
- Ingestion endpoint is `POST /ingest` on separate `ingest_router` (not under `/customers`)
- Docker volumes: `./docs/buN` → `/docs/buN:ro` (read-only)
- MongoDB Atlas Vector Search index must be named `vector_index` on each `buN_document_chunks` collection
- Atlas M10+ required for vector search (M0 free tier does not support it)

---

## Ports
- BU1: 8001, BU2: 8002, BU3: 8003, BU4: 8004

## Run Commands
```bash
docker compose up --build -d     # start all services
uv run python seed_data.py       # seed databases
uv run python run_agent.py       # interactive agent
uv run python test_agent.py      # run all tests
```
