# Field Service Document Intelligence — Development Plan

## Overview

An AI-powered assistant for **RiteCare** field service operations. Field officers and customer support staff interact via **Slack**. Messages are processed by a **LangGraph** agent that uses **MCP tools** to call RiteCare microservices and perform **RAG** over domain documents, reasons with **OpenAI GPT-4o-mini**, persists data in **MongoDB Atlas**, and responds back to Slack.

---

## Architecture Summary

```
Slack Message
    → Python Slack Gateway (FastAPI)
    → LangGraph Agent
        → MCP Tools (@tool)
            ├── RiteCare Microservices (FastAPI) → MongoDB Atlas (CRUD)
            └── RAG Tools → MongoDB Atlas Vector Search (semantic search)
    → LLM (OpenAI GPT-4o-mini)
    → Response back to Slack

Document Upload (offline / async)
    → Document Ingestion Pipeline (per BU)
        → Chunking + Embedding (OpenAI gemini-embedding-001)
        → MongoDB Atlas Vector Search index
```

### RiteCare Business Units

| Unit | Microservice           | Responsibility                                         | RAG Documents                                                |
| ---- | ---------------------- | ------------------------------------------------------ | ------------------------------------------------------------ |
| BU1  | Customer Onboarding    | New customer registration, KYC, account setup          | KYC forms, ID scans, onboarding checklists                   |
| BU2  | Sales & Maintenance    | Service contracts, field visits, maintenance schedules | Equipment manuals, service procedures, contract PDFs         |
| BU3  | Billing & Subscription | Invoices, subscription plans, payment tracking         | Invoice PDFs, billing statements, plan documents             |
| BU4  | Support & Fulfillment  | Tickets, SLAs, parts fulfillment, escalations          | KB articles, resolved ticket history, troubleshooting guides |

### Slack Back-Office Channels

| Channel                               | Purpose                  |
| ------------------------------------- | ------------------------ |
| `help-sales-backoffice`               | BU1 + BU2 queries        |
| `help-customer-profile-backoffice`    | Customer profile lookups |
| `help-billing-fulfillment-backoffice` | BU3 + BU4 queries        |

---

## Tech Stack

| Layer             | Technology                         |
| ----------------- | ---------------------------------- |
| Language          | Python 3.12                        |
| Microservices     | FastAPI                            |
| AI Orchestration  | LangGraph                          |
| Tool Protocol     | MCP (Model Context Protocol)       |
| LLM               | OpenAI GPT-4o-mini                 |
| Embeddings        | OpenAI gemini-embedding-001        |
| Vector Search     | MongoDB Atlas Vector Search        |
| Database          | MongoDB Atlas (Motor async driver) |
| Data Validation   | Pydantic v2                        |
| Package Manager   | uv (pyproject.toml)                |
| Testing           | pytest + httpx                     |
| Containerisation  | Docker + docker-compose            |
| Slack Integration | Slack Bolt for Python (Phase 6)    |

---

## Repository Structure

This is a **monorepo**. All BU microservices and the AI orchestration layer live in the same repository under a `services/` directory.

### Service Ports

| Service                      | Path                                 | Port |
| ---------------------------- | ------------------------------------ | ---- |
| BU1 — Customer Onboarding    | `services/bu1_onboarding/`           | 8001 |
| BU2 — Sales & Maintenance    | `services/bu2_sales_maintenance/`    | 8002 |
| BU3 — Billing & Subscription | `services/bu3_billing_subscription/` | 8003 |
| BU4 — Support & Fulfillment  | `services/bu4_support_fulfillment/`  | 8004 |

---

### Monorepo — `Field-Service-Document-Intelligence`

```
Field-Service-Document-Intelligence/
│
├── services/                        # All BU microservices
│   ├── bu1_onboarding/              # BU1 — port 8001
│   │   ├── api/
│   │   ├── service/
│   │   ├── dao/
│   │   ├── common/
│   │   ├── .env.example
│   │   └── pyproject.toml
│   │
│   ├── bu2_sales_maintenance/       # BU2 — port 8002
│   │   ├── api/
│   │   ├── service/
│   │   ├── dao/
│   │   ├── common/
│   │   ├── .env.example
│   │   └── pyproject.toml
│   │
│   ├── bu3_billing_subscription/    # BU3 — port 8003
│   │   ├── api/
│   │   ├── service/
│   │   ├── dao/
│   │   ├── common/
│   │   ├── .env.example
│   │   └── pyproject.toml
│   │
│   └── bu4_support_fulfillment/     # BU4 — port 8004
│       ├── api/
│       ├── service/
│       ├── dao/
│       ├── common/
│       ├── .env.example
│       └── pyproject.toml
│
├── agent/
│   ├── __init__.py
│   ├── graph.py                     # LangGraph StateGraph definition + compilation
│   ├── state.py                     # AgentState TypedDict
│   ├── nodes/
│   │   ├── __init__.py
│   │   ├── intent_classifier.py     # LLM node: classify query → BU context
│   │   ├── tool_executor.py         # Node: invoke MCP tools
│   │   └── responder.py             # LLM node: compose final response
│   └── prompts/
│       ├── __init__.py
│       └── system_prompt.py         # RiteCare-aware system prompt template
│
├── mcp/
│   ├── __init__.py
│   ├── server.py                    # MCP server entry point (FastMCP)
│   └── tools/
│       ├── __init__.py
│       ├── bu1_tools.py             # CRUD @tools → BU1 API
│       ├── bu2_tools.py             # CRUD @tools → BU2 API
│       ├── bu3_tools.py             # CRUD @tools → BU3 API
│       ├── bu4_tools.py             # CRUD @tools → BU4 API
│       └── rag_tools.py             # RAG @tools → Atlas Vector Search (all BUs)
│
├── db/
│   ├── __init__.py
│   ├── client.py                    # MongoDB Atlas Motor client (singleton)
│   ├── collections.py               # Collection name constants (CRUD + vector)
│   └── models/
│       ├── __init__.py
│       └── conversation.py          # Agent conversation history model
│
├── slack_gateway/                   # Phase 5 — Slack event receiver
│   ├── __init__.py
│   ├── main.py
│   ├── handlers.py
│   └── channel_router.py
│
├── shared/
│   ├── __init__.py
│   ├── config.py                    # Settings (pydantic-settings, .env)
│   ├── exceptions.py                # Custom exception classes
│   ├── logging.py                   # Structured logging setup
│   └── utils/
│       ├── __init__.py
│       └── http_client.py           # Shared async HTTP client (httpx)
│
├── tests/
│   ├── conftest.py
│   ├── unit/
│   │   ├── test_mcp_tools.py
│   │   └── test_rag_tools.py
│   ├── integration/
│   │   └── test_agent.py
│   └── e2e/
│       └── test_slack_flow.py       # Phase 5
│
├── docker/
│   └── Dockerfile.agent
│
├── .env.example
├── .gitignore
├── docker-compose.yml               # Runs all 5 services locally
├── pyproject.toml                   # Root — agent/mcp/db/shared deps
└── README_Development_Plan.md
```

---

### BU Microservice Repos — Layered Architecture (repeated × 4)

Each BU repo follows a **strict 4-layer architecture**: `api → service → dao → common`.
An `ingestion/` module handles document processing and vector indexing for RAG.

```
ritecare-bu{N}-{name}/
│
├── api/                             # Layer 1 — HTTP interface
│   ├── __init__.py
│   ├── main.py                      # FastAPI app entry point + lifespan
│   ├── router.py                    # Route definitions (FastAPI APIRouter)
│   └── dependencies.py              # FastAPI dependency injection (service, limiter)
│
├── service/                         # Layer 2 — Business logic
│   ├── __init__.py
│   └── {domain}_service.py          # Orchestrates dao calls, applies rules
│
├── dao/                             # Layer 3 — Data Access Objects
│   ├── __init__.py
│   ├── {domain}_dao.py              # All MongoDB CRUD queries via Motor
│   └── vector_dao.py                # MongoDB Atlas Vector Search queries
│
├── ingestion/                       # Document ingestion pipeline (async / offline)
│   ├── __init__.py
│   ├── chunker.py                   # Split documents into chunks
│   ├── embedder.py                  # Call OpenAI gemini-embedding-001
│   ├── pipeline.py                  # Orchestrate chunker → embedder → vector_dao
│   └── loaders/
│       ├── __init__.py
│       ├── pdf_loader.py            # Load & extract text from PDFs
│       └── text_loader.py           # Load plain text / markdown docs
│
├── common/                          # Layer 4 — Shared within this microservice
│   ├── __init__.py
│   ├── models/                      # MongoDB document models (Motor/Pydantic)
│   │   ├── __init__.py
│   │   ├── {domain}.py              # CRUD document model
│   │   └── document_chunk.py        # Vector chunk model (text, embedding, metadata)
│   ├── schemas/                     # Pydantic request/response schemas (API DTOs)
│   │   ├── __init__.py
│   │   ├── request.py
│   │   └── response.py
│   ├── database/
│   │   ├── __init__.py
│   │   ├── client.py                # MongoDB Atlas Motor client (singleton)
│   │   └── collections.py           # Collection name constants (CRUD + vector)
│   ├── exceptions/
│   │   ├── __init__.py
│   │   └── handlers.py              # FastAPI exception handlers
│   ├── limiter/
│   │   ├── __init__.py
│   │   └── rate_limiter.py          # Rate limiting (slowapi)
│   ├── logging/
│   │   ├── __init__.py
│   │   └── logger.py                # Structured JSON logging (structlog)
│   └── config.py                    # Pydantic Settings (.env loader)
│
├── tests/
│   ├── conftest.py
│   ├── unit/
│   │   ├── test_service.py
│   │   ├── test_dao.py
│   │   └── test_ingestion.py
│   └── integration/
│       └── test_router.py
│
├── .env.example
├── .gitignore
├── Dockerfile
├── pyproject.toml
└── README.md
```

#### Layer Responsibilities

| Layer       | Responsibility                                                 | May import from     |
| ----------- | -------------------------------------------------------------- | ------------------- |
| `api`       | HTTP routing, request validation, response serialisation       | `service`, `common` |
| `service`   | Business rules, orchestration, error handling                  | `dao`, `common`     |
| `dao`       | All DB queries (CRUD + vector search) — no business logic      | `common`            |
| `ingestion` | Document loading, chunking, embedding, indexing — runs offline | `dao`, `common`     |
| `common`    | Config, models, schemas, DB client, logging, limiting          | nothing above       |

---

## RAG Design

### How RAG works in this project

```
── Ingestion (offline) ──────────────────────────────────────────────
Document (PDF / text)
    → pdf_loader / text_loader        (extract raw text)
    → chunker                         (split into ~500 token chunks)
    → embedder                        (OpenAI gemini-embedding-001)
    → vector_dao.insert_chunk()       (store in MongoDB Atlas Vector index)

── Retrieval (at query time via MCP) ────────────────────────────────
User query
    → embed query (gemini-embedding-001)
    → vector_dao.search(query_vector, top_k=5)   (cosine similarity)
    → top-K chunks returned as context
    → injected into LangGraph agent alongside CRUD tool results
    → LLM reasons over combined context → response
```

### RAG per Business Unit

| BU  | Vector Collection     | Document Types                                        | Example Query                                          |
| --- | --------------------- | ----------------------------------------------------- | ------------------------------------------------------ |
| BU1 | `bu1_document_chunks` | KYC forms, onboarding checklists                      | _"What documents did customer C123 upload?"_           |
| BU2 | `bu2_document_chunks` | Service manuals, contract PDFs, field guides          | _"How do I service the X200 pump unit?"_               |
| BU3 | `bu3_document_chunks` | Invoice PDFs, billing statements, plan terms          | _"Why was customer C456 charged $500 in March?"_       |
| BU4 | `bu4_document_chunks` | KB articles, resolved tickets, troubleshooting guides | _"Has this fault been seen before? How was it fixed?"_ |

### MongoDB Atlas Vector Index (per BU collection)

```json
{
  "fields": [
    {
      "type": "vector",
      "path": "embedding",
      "numDimensions": 1536,
      "similarity": "cosine"
    },
    {
      "type": "filter",
      "path": "customer_id"
    },
    {
      "type": "filter",
      "path": "bu"
    }
  ]
}
```

### RAG MCP Tools (in `mcp/tools/rag_tools.py`)

| Tool                        | BU  | Description                                             |
| --------------------------- | --- | ------------------------------------------------------- |
| `search_onboarding_docs`    | BU1 | Semantic search over KYC / onboarding documents         |
| `search_service_manuals`    | BU2 | Semantic search over equipment manuals and field guides |
| `search_contracts`          | BU2 | Semantic search over contract PDFs                      |
| `search_billing_statements` | BU3 | Semantic search over invoice and billing documents      |
| `search_knowledge_base`     | BU4 | Semantic search over KB articles                        |
| `search_resolved_tickets`   | BU4 | Semantic search over past resolved support tickets      |

---

## Development Phases

---

### Phase 1 — Project Foundation (Main Repo)

**Goal:** Working skeleton with config, logging, and shared utilities.

- [ ] `pyproject.toml` — dependencies, project metadata
- [ ] `.env.example` — all required environment variables
- [ ] `shared/config.py` — Pydantic Settings (loads `.env`)
- [ ] `shared/logging.py` — structured JSON logging
- [ ] `shared/exceptions.py` — base exception classes
- [ ] `shared/utils/http_client.py` — shared async httpx client
- [ ] `db/client.py` — MongoDB Atlas Motor singleton
- [ ] `db/collections.py` — collection name constants (CRUD + vector collections)

**Exit criteria:** `python -c "from shared.config import settings; print(settings)"` runs without error.

---

### Phase 2 — MongoDB Document Models (Main Repo)

**Goal:** Pydantic v2 conversation model for the agent with MongoDB `_id` handling.

- [ ] `db/models/conversation.py` — Agent conversation (session_id, messages[], channel, user_id, created_at)

**Exit criteria:** Model instantiates and serialises to/from dict correctly.

---

### Phase 3 — RiteCare Microservices (BU1–BU4)

**Goal:** Four independently runnable FastAPI services, each in its own repo, using the layered architecture (api → service → dao → common).

Each microservice is built in this order per repo:

1. `common/` — config, models (domain + document_chunk), schemas, database client, logger, rate limiter, exceptions
2. `dao/` — MongoDB CRUD queries + vector search queries
3. `service/` — business logic
4. `api/` — routes, dependencies, app entry

#### BU1 — Customer Onboarding (`ritecare-bu1-onboarding`, port 8001)

- [ ] `common/` — CustomerModel, DocumentChunkModel, CustomerCreateSchema, CustomerResponseSchema, DB client
- [ ] `dao/customer_dao.py` — insert, find_by_id, update_kyc
- [ ] `dao/vector_dao.py` — insert_chunk, search (cosine similarity)
- [ ] `service/customer_service.py` — register, get profile, update KYC, get onboarding status
- [ ] `api/router.py` — endpoints:
  - `POST /customers` — register new customer
  - `GET /customers/{id}` — get customer profile
  - `PATCH /customers/{id}/kyc` — update KYC status
  - `GET /customers/{id}/onboarding-status` — get onboarding progress

#### BU2 — Sales & Maintenance (`ritecare-bu2-sales-maintenance`, port 8002)

- [ ] `common/` — ContractModel, VisitModel, DocumentChunkModel, request/response schemas, DB client
- [ ] `dao/contract_dao.py` + `dao/visit_dao.py` + `dao/vector_dao.py`
- [ ] `service/contract_service.py` + `service/visit_service.py`
- [ ] `api/router.py` — endpoints:
  - `POST /contracts` — create service contract
  - `GET /contracts/{id}` — get contract details
  - `POST /visits` — schedule field visit
  - `GET /visits` — list upcoming visits
  - `PATCH /visits/{id}` — update visit status

#### BU3 — Billing & Subscription (`ritecare-bu3-billing-subscription`, port 8003)

- [ ] `common/` — InvoiceModel, SubscriptionModel, DocumentChunkModel, request/response schemas, DB client
- [ ] `dao/invoice_dao.py` + `dao/subscription_dao.py` + `dao/vector_dao.py`
- [ ] `service/invoice_service.py` + `service/subscription_service.py`
- [ ] `api/router.py` — endpoints:
  - `POST /invoices` — create invoice
  - `GET /invoices/{customer_id}` — list customer invoices
  - `PATCH /invoices/{id}/pay` — mark invoice as paid
  - `GET /subscriptions/{customer_id}` — get subscription plan
  - `PATCH /subscriptions/{customer_id}` — update plan

#### BU4 — Support & Fulfillment (`ritecare-bu4-support-fulfillment`, port 8004)

- [ ] `common/` — TicketModel, DocumentChunkModel, request/response schemas, DB client
- [ ] `dao/ticket_dao.py` + `dao/vector_dao.py`
- [ ] `service/ticket_service.py`
- [ ] `api/router.py` — endpoints:
  - `POST /tickets` — raise support ticket
  - `GET /tickets/{id}` — get ticket details
  - `GET /tickets/customer/{customer_id}` — list customer tickets
  - `PATCH /tickets/{id}/status` — update ticket status
  - `POST /tickets/{id}/escalate` — escalate ticket

**Exit criteria:** All endpoints return correct responses per BU, verified with pytest + httpx in each repo.

---

### Phase 4 — LangGraph Agent (Main Repo)

**Goal:** Fully working AI agent that receives a user query, routes through a state graph, selects the right CRUD and/or RAG MCP tools, combines results, persists the conversation, and returns an intelligent response.

- [ ] `agent/state.py` — `AgentState` TypedDict (messages, intent, tool_calls, tool_results, session_id, channel)
- [ ] `agent/prompts/system_prompt.py` — RiteCare-aware system prompt (BU context, tool guidance, RAG instructions)
- [ ] `agent/nodes/intent_classifier.py` — LLM node: classify query to BU1/BU2/BU3/BU4 + determine CRUD vs RAG
- [ ] `agent/nodes/tool_executor.py` — node: invoke MCP tools based on intent, collect results
- [ ] `agent/nodes/responder.py` — LLM node: synthesise tool results into natural language response
- [ ] `agent/graph.py` — wire nodes + conditional edges into LangGraph `StateGraph`, compile
- [ ] Persist conversation turns to MongoDB (`db/models/conversation.py`)

**How LangGraph works here:**

```python
graph = StateGraph(AgentState)
graph.add_node("classify", intent_classifier)
graph.add_node("execute_tools", tool_executor)
graph.add_node("respond", responder)

graph.set_entry_point("classify")
graph.add_edge("classify", "execute_tools")
graph.add_edge("execute_tools", "respond")
graph.add_edge("respond", END)

agent = graph.compile()
result = await agent.ainvoke({"messages": [user_query], "session_id": session_id})
```

**Example combined flow:**

```
Query: "How do I fix the pressure fault on customer C123's pump unit?"
  → classify:       intent=BU2+BU4, mode=CRUD+RAG
  → execute_tools:
      search_service_manuals("pressure fault pump")    [RAG → BU2]
      get_ticket(customer_id="C123", type="pressure")  [CRUD → BU4]
      search_resolved_tickets("pressure fault pump")   [RAG → BU4]
  → respond:        LLM synthesises all results → actionable response
```

**Exit criteria:** Agent handles queries requiring CRUD only, RAG only, and combined CRUD + RAG. Conversation persisted to MongoDB.

---

### Phase 5 — Slack Gateway (Deferred)

**Goal:** Connect everything to Slack.

- [ ] `slack_gateway/main.py` — Slack Bolt app
- [ ] `slack_gateway/handlers.py` — message event handler → LangGraph agent
- [ ] `slack_gateway/channel_router.py` — route by channel to inject BU context into AgentState
- [ ] Docker-compose update to include gateway service
- [ ] End-to-end test: Slack message → agent → response in Slack thread

**Exit criteria:** Full round-trip working in all 3 back-office channels.

---

## Environment Variables (.env.example)

```env
# OpenAI
GOOGLE_API_KEY=
GOOGLE_EMBEDDING_MODEL=gemini-embedding-001
GOOGLE_CHAT_MODEL=gpt-4o-mini

# MongoDB Atlas
MONGODB_URI=
MONGODB_DB_NAME=ritecare

# Microservice URLs (internal)
BU1_BASE_URL=http://localhost:8001
BU2_BASE_URL=http://localhost:8002
BU3_BASE_URL=http://localhost:8003
BU4_BASE_URL=http://localhost:8004

# RAG
RAG_CHUNK_SIZE=500
RAG_CHUNK_OVERLAP=50
RAG_TOP_K=5

# Slack (Phase 6)
SLACK_BOT_TOKEN=
SLACK_SIGNING_SECRET=
SLACK_APP_TOKEN=

# App
LOG_LEVEL=INFO
ENV=development
```

---

## Key Dependencies

### Main Repo (`Field-Service-Document-Intelligence`)

```toml
[project]
dependencies = [
    # AI Orchestration
    "langgraph>=0.2",                 # LangGraph agent framework
    "langchain-openai>=0.2",          # OpenAI LLM + embeddings via LangChain
    "langchain-core>=0.3",            # LangChain base primitives

    # MCP
    "mcp>=1.0",                       # MCP protocol + FastMCP server

    # Database
    "motor>=3.5",                     # Async MongoDB driver
    "pymongo>=4.8",

    # Validation & config
    "pydantic>=2.8",
    "pydantic-settings>=2.4",

    # HTTP client
    "httpx>=0.27",

    # Slack (Phase 6)
    "slack-bolt>=1.20",

    # Utilities
    "python-dotenv>=1.0",
    "structlog>=24.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.24",
    "pytest-httpx>=0.30",
    "ruff>=0.6",
    "mypy>=1.11",
]
```

### BU Microservice Repos (each identical)

```toml
[project]
dependencies = [
    # Web framework
    "fastapi>=0.115",
    "uvicorn[standard]>=0.30",

    # Database
    "motor>=3.5",
    "pymongo>=4.8",

    # Validation & config
    "pydantic>=2.8",
    "pydantic-settings>=2.4",

    # Rate limiting
    "slowapi>=0.1.9",

    # RAG — document ingestion
    "openai>=1.50",                   # Embedding API
    "pypdf>=4.0",                     # PDF text extraction
    "tiktoken>=0.7",                  # Token counting for chunking

    # Utilities
    "python-dotenv>=1.0",
    "structlog>=24.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.24",
    "httpx>=0.27",                    # Test client for FastAPI
    "ruff>=0.6",
    "mypy>=1.11",
]
```

---

## Current Status

| Phase                                      | Status      |
| ------------------------------------------ | ----------- |
| Phase 1 — Foundation (Main Repo)           | Not started |
| Phase 2 — MongoDB Models (Main Repo)       | Not started |
| Phase 3 — RiteCare Microservices (BU1–BU4) | Not started |
| Phase 4 — LangGraph Agent                  | Not started |
| Phase 5 — Slack Gateway                    | Deferred    |
