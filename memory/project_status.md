---
name: RiteCare Project Status
description: Current build status, completed phases, pending work, and key architectural decisions
type: project
---

## Project: Field Service Document Intelligence — RiteCare AI Assistant

**Why:** Interview/work project for Synechron. AI-powered Slack assistant for RiteCare field officers using LangGraph, OpenAI GPT-4o-mini, MongoDB Atlas, FastAPI microservices, Airflow.

**How to apply:** Use this to understand exactly where we left off and what needs to be done next.

---

## Completed

### BU Microservices (all 4)
- BU1 `services/bu1_onboarding/` — port 8001 (includes ingestion pipeline + `/ingest` + `/rag/search`)
- BU2 `services/bu2_sales_maintenance/` — port 8002
- BU3 `services/bu3_billing_subscription/` — port 8003
- BU4 `services/bu4_support_fulfillment/` — port 8004

### Agent Service — `services/agent_service/` — port 8000
- `agent/` — LangGraph 3-node pipeline: intent_classifier → tool_executor → responder
- `ritecare_tools/` — HTTP tools (BU1-4 CRUD + RAG) and cross-BU rag_tools
- `agent_api/main.py` — FastAPI `POST /query`, `GET /health`
- `agent_api/dependencies.py` — injects ConversationService
- `service/conversation_service.py` — loads history with `trim_messages` (token trimming), saves turns
- `dao/conversation_dao.py` — MongoDB upsert per session_id
- `db/models/conversation.py`, `db/client.py`, `db/collections.py`
- `shared/config.py` — includes `max_history_tokens`
- `Dockerfile`, `pyproject.toml`

### Slack Gateway — `services/slack_gateway/` — no port (Socket Mode)
- Listens on 3 channels: `rc_help_sales_backoffice`, `rc_help_customer_profile_backoffice`, `rc_help_billing_fulfillment_backoffice`
- `handlers.py` → calls `POST http://agent:8000/query` → replies in Slack thread
- `channel_router.py`, `config.py`, `main.py`
- Working and tested end-to-end

### Ingestion Service — `services/ingestion_service/` — port 8005
- `POST /ingest` — accepts file upload + bu + customer_id, saves to shared volume, triggers Airflow DAG
- `POST /ingest/notify` — Airflow callback, sends Slack webhook notification
- `GET /ingest/{dag_run_id}/status` — proxies to Airflow
- `service/ingestion_orchestrator.py` — saves file + calls Airflow REST API
- `pipeline/chunker.py` — tiktoken-based ~500 token chunks with overlap
- `pipeline/embedder.py` — single OpenAI batch call, returns list[dict] for MongoDB
- `Dockerfile`, `pyproject.toml`

### Airflow — `airflow/dags/bu_ingestion_dag.py` — port 8080
- DAG id: `bu_ingestion`, triggered externally only (`schedule=None`)
- Tasks: load → chunk → embed → store → notify
- Imports chunker/embedder from ingestion_service via shared Docker volume mount
- Stores chunks directly into `buN_document_chunks` via pymongo

### Infrastructure
- `docker-compose.yml` — all 7 services: agent, slack_gateway, ingestion_service, airflow, BU1-4
- Shared volume `uploads` — between ingestion_service and Airflow
- `seed_data.py` — seeds all 4 BUs via REST APIs
- `ARCHITECTURE.md` — Mermaid diagram

---

## Pending / Known Issues

- BU2, BU3, BU4 own `/ingest` + `/rag/search` endpoints not yet wired (BU1 done). Now superseded by ingestion_service — may not be needed.
- `db/client.py` has duplicate `get_database()` function definition (minor bug, doesn't break anything)
- `rag_tools.py` `search_all_bus` and `search_bu_documents` defined but not wired into `tool_executor.py`

---

## Key Architecture Decisions

- All agent code moved to `services/agent_service/` (consistent with BU services)
- `mcp/` renamed to `ritecare_tools/` — conflicts with installed `mcp>=1.0` package
- Rate limiting via `SlowAPIMiddleware` only — no per-route `@limiter` decorators
- `pipeline.py` returns `list[dict]`, does NOT insert — VectorDAO handles persistence
- Ingestion now centralised in `ingestion_service` — Airflow handles async processing
- Airflow mounts `services/ingestion_service` as volume → DAG imports chunker/embedder directly
- Session token trimming via `trim_messages` in `conversation_service.load_history()`
- Session key in Slack gateway: `{channel_name}-{user_id}`
- MongoDB Atlas Vector Search index must be named `vector_index` on each `buN_document_chunks` collection
- Atlas M10+ required for vector search

---

## Ports
- Agent API: 8000
- BU1: 8001, BU2: 8002, BU3: 8003, BU4: 8004
- Ingestion Service: 8005
- Airflow: 8080

## Run Commands
```bash
docker compose up --build -d        # start all services
uv run python seed_data.py          # seed BU databases
cd services/agent_service && uv run python run_agent.py    # CLI agent
cd services/agent_service && uv run python test_agent.py   # run tests
```
