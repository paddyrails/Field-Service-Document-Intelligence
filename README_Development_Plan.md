# Field Service Document Intelligence — Development Plan

## Overview

An AI-powered assistant for **RiteCare** field service operations. Field officers and customer support staff interact via **Slack**. Messages are processed by a **LangGraph** agent that uses **MCP tools** to call RiteCare microservices, reasons with **OpenAI GPT-4o-mini**, persists data in **MongoDB Atlas**, and responds back to Slack.

---

## Architecture Summary

```
Slack Message
    → Python Slack Gateway (FastAPI)
    → LangGraph Agent
        → MCP Tools (@tool)
            → RiteCare Microservices (FastAPI)
                → MongoDB Atlas
    → LLM (OpenAI GPT-4o-mini)
    → Response back to Slack
```

### RiteCare Business Units

| Unit | Microservice | Responsibility |
|------|-------------|----------------|
| BU1  | Customer Onboarding | New customer registration, KYC, account setup |
| BU2  | Sales & Maintenance | Service contracts, field visits, maintenance schedules |
| BU3  | Billing & Subscription | Invoices, subscription plans, payment tracking |
| BU4  | Support & Fulfillment | Tickets, SLAs, parts fulfillment, escalations |

### Slack Back-Office Channels

| Channel | Purpose |
|---------|---------|
| `help-sales-backoffice` | BU1 + BU2 queries |
| `help-customer-profile-backoffice` | Customer profile lookups |
| `help-billing-fulfillment-backoffice` | BU3 + BU4 queries |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.12 |
| Microservices | FastAPI |
| AI Orchestration | LangGraph |
| Tool Protocol | MCP (Model Context Protocol) |
| LLM | OpenAI GPT-4o-mini |
| Database | MongoDB Atlas (Motor async driver) |
| Data Validation | Pydantic v2 |
| Package Manager | uv (pyproject.toml) |
| Testing | pytest + httpx |
| Containerisation | Docker + docker-compose |
| Slack Integration | Slack Bolt for Python (Phase 6) |

---

## Repository Structure

Each BU microservice lives in its **own repository**. The main repo is the AI orchestration layer.

### Repositories

| Repository | Port | Description |
|------------|------|-------------|
| `Field-Service-Document-Intelligence` | — | Main repo: agent, MCP, Slack gateway |
| `ritecare-bu1-onboarding` | 8001 | Customer Onboarding microservice |
| `ritecare-bu2-sales-maintenance` | 8002 | Sales & Maintenance microservice |
| `ritecare-bu3-billing-subscription` | 8003 | Billing & Subscription microservice |
| `ritecare-bu4-support-fulfillment` | 8004 | Support & Fulfillment microservice |

---

### Main Repo — `Field-Service-Document-Intelligence`

```
Field-Service-Document-Intelligence/
│
├── agent/
│   ├── __init__.py
│   ├── graph.py                     # LangGraph graph definition
│   ├── state.py                     # Agent state (TypedDict)
│   ├── nodes/
│   │   ├── __init__.py
│   │   ├── intent_classifier.py     # Classify user intent → correct BU
│   │   ├── tool_executor.py         # Execute MCP tools
│   │   └── responder.py             # Format final response
│   └── prompts/
│       ├── __init__.py
│       └── system_prompt.py         # LLM system prompt templates
│
├── mcp/
│   ├── __init__.py
│   ├── server.py                    # MCP server entry point
│   └── tools/
│       ├── __init__.py
│       ├── bu1_tools.py             # @tool wrappers → BU1 API
│       ├── bu2_tools.py             # @tool wrappers → BU2 API
│       ├── bu3_tools.py             # @tool wrappers → BU3 API
│       └── bu4_tools.py             # @tool wrappers → BU4 API
│
├── db/
│   ├── __init__.py
│   ├── client.py                    # MongoDB Atlas Motor client (singleton)
│   ├── collections.py               # Collection name constants
│   └── models/
│       ├── __init__.py
│       └── conversation.py          # Agent conversation history model
│
├── slack_gateway/                   # Phase 6 — Slack event receiver
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
│   │   └── test_mcp_tools.py
│   ├── integration/
│   │   └── test_agent.py
│   └── e2e/
│       └── test_slack_flow.py       # Phase 6
│
├── docker/
│   └── Dockerfile.agent
│
├── .env.example
├── .gitignore
├── docker-compose.yml               # Orchestrates all 5 services locally
├── pyproject.toml
└── README_Development_Plan.md
```

---

### BU Microservice Repos — Layered Architecture (repeated × 4)

Each BU repo follows a **strict 4-layer architecture**: `api → service → dao → common`.

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
│   └── {domain}_dao.py              # All MongoDB queries via Motor
│
├── common/                          # Layer 4 — Shared within this microservice
│   ├── __init__.py
│   ├── models/                      # MongoDB document models (Motor/Pydantic)
│   │   ├── __init__.py
│   │   └── {domain}.py
│   ├── schemas/                     # Pydantic request/response schemas (API DTOs)
│   │   ├── __init__.py
│   │   ├── request.py
│   │   └── response.py
│   ├── database/
│   │   ├── __init__.py
│   │   ├── client.py                # MongoDB Atlas Motor client (singleton)
│   │   └── collections.py           # Collection name constants
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
│   │   └── test_dao.py
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

| Layer | Responsibility | May import from |
|-------|---------------|-----------------|
| `api` | HTTP routing, request validation, response serialisation | `service`, `common` |
| `service` | Business rules, orchestration, error handling | `dao`, `common` |
| `dao` | All DB queries — no business logic | `common` |
| `common` | Config, models, schemas, DB client, logging, limiting | nothing above |

---

## Development Phases

---

### Phase 1 — Project Foundation
**Goal:** Working skeleton with config, logging, and shared utilities.

- [ ] `pyproject.toml` — dependencies, project metadata
- [ ] `.env.example` — all required environment variables
- [ ] `shared/config.py` — Pydantic Settings (loads `.env`)
- [ ] `shared/logging.py` — structured JSON logging
- [ ] `shared/exceptions.py` — base exception classes
- [ ] `shared/utils/http_client.py` — shared async httpx client
- [ ] `db/client.py` — MongoDB Atlas Motor singleton
- [ ] `db/collections.py` — collection name constants

**Exit criteria:** `python -c "from shared.config import settings; print(settings)"` runs without error.

---

### Phase 2 — MongoDB Document Models
**Goal:** All Pydantic v2 document models with MongoDB `_id` handling.

- [ ] `db/models/customer.py` — Customer (name, contact, KYC status, onboarding stage)
- [ ] `db/models/contract.py` — Sales contract (customer_id, type, start/end dates, status)
- [ ] `db/models/invoice.py` — Invoice (customer_id, amount, due_date, paid status)
- [ ] `db/models/ticket.py` — Support ticket (customer_id, category, priority, SLA, status)
- [ ] `db/models/conversation.py` — Agent conversation (session_id, messages[], channel, user)

**Exit criteria:** All models instantiate and serialize to/from dict correctly.

---

### Phase 3 — RiteCare Microservices (BU1–BU4)
**Goal:** Four independently runnable FastAPI services, each in its own repo, using the layered architecture (api → service → dao → common).

Each microservice is built in this order per repo:
1. `common/` — config, models, schemas, database client, logger, rate limiter, exceptions
2. `dao/` — MongoDB queries
3. `service/` — business logic
4. `api/` — routes, dependencies, app entry

#### BU1 — Customer Onboarding (`ritecare-bu1-onboarding`, port 8001)
- [ ] `common/` — CustomerModel, CustomerCreateSchema, CustomerResponseSchema, DB client
- [ ] `dao/customer_dao.py` — insert, find_by_id, update_kyc
- [ ] `service/customer_service.py` — register, get profile, update KYC, get onboarding status
- [ ] `api/router.py` — endpoints:
  - `POST /customers` — register new customer
  - `GET /customers/{id}` — get customer profile
  - `PATCH /customers/{id}/kyc` — update KYC status
  - `GET /customers/{id}/onboarding-status` — get onboarding progress

#### BU2 — Sales & Maintenance (`ritecare-bu2-sales-maintenance`, port 8002)
- [ ] `common/` — ContractModel, VisitModel, request/response schemas, DB client
- [ ] `dao/contract_dao.py` + `dao/visit_dao.py`
- [ ] `service/contract_service.py` + `service/visit_service.py`
- [ ] `api/router.py` — endpoints:
  - `POST /contracts` — create service contract
  - `GET /contracts/{id}` — get contract details
  - `POST /visits` — schedule field visit
  - `GET /visits` — list upcoming visits
  - `PATCH /visits/{id}` — update visit status

#### BU3 — Billing & Subscription (`ritecare-bu3-billing-subscription`, port 8003)
- [ ] `common/` — InvoiceModel, SubscriptionModel, request/response schemas, DB client
- [ ] `dao/invoice_dao.py` + `dao/subscription_dao.py`
- [ ] `service/invoice_service.py` + `service/subscription_service.py`
- [ ] `api/router.py` — endpoints:
  - `POST /invoices` — create invoice
  - `GET /invoices/{customer_id}` — list customer invoices
  - `PATCH /invoices/{id}/pay` — mark invoice as paid
  - `GET /subscriptions/{customer_id}` — get subscription plan
  - `PATCH /subscriptions/{customer_id}` — update plan

#### BU4 — Support & Fulfillment (`ritecare-bu4-support-fulfillment`, port 8004)
- [ ] `common/` — TicketModel, request/response schemas, DB client
- [ ] `dao/ticket_dao.py`
- [ ] `service/ticket_service.py`
- [ ] `api/router.py` — endpoints:
  - `POST /tickets` — raise support ticket
  - `GET /tickets/{id}` — get ticket details
  - `GET /tickets/customer/{customer_id}` — list customer tickets
  - `PATCH /tickets/{id}/status` — update ticket status
  - `POST /tickets/{id}/escalate` — escalate ticket

**Exit criteria:** All endpoints return correct responses per BU, verified with pytest + httpx in each repo.

---

### Phase 4 — MCP Tools
**Goal:** MCP `@tool` functions that call BU1–BU4 REST APIs.

- [ ] `mcp/server.py` — MCP server setup
- [ ] `mcp/tools/bu1_tools.py` — tools: `get_customer`, `register_customer`, `update_kyc`, `get_onboarding_status`
- [ ] `mcp/tools/bu2_tools.py` — tools: `get_contract`, `create_contract`, `schedule_visit`, `update_visit`
- [ ] `mcp/tools/bu3_tools.py` — tools: `get_invoices`, `create_invoice`, `pay_invoice`, `get_subscription`, `update_subscription`
- [ ] `mcp/tools/bu4_tools.py` — tools: `raise_ticket`, `get_ticket`, `update_ticket_status`, `escalate_ticket`, `list_tickets`

**Exit criteria:** Each tool callable directly, returns correct data from the microservices.

---

### Phase 5 — LangGraph Agent
**Goal:** Fully working AI agent that receives a user query, selects the right tools, calls microservices, and returns an intelligent response.

- [ ] `agent/state.py` — `AgentState` TypedDict (messages, intent, tool_results, session_id)
- [ ] `agent/prompts/system_prompt.py` — RiteCare-aware system prompt
- [ ] `agent/nodes/intent_classifier.py` — LLM node: classify query to BU1/BU2/BU3/BU4
- [ ] `agent/nodes/tool_executor.py` — execute MCP tool calls
- [ ] `agent/nodes/responder.py` — LLM node: compose final natural language response
- [ ] `agent/graph.py` — wire nodes + conditional edges into LangGraph `StateGraph`
- [ ] Persist conversation to MongoDB (`db/models/conversation.py`)

**Exit criteria:** Agent receives a plain English query (e.g. "What is the onboarding status for customer C123?"), calls the correct tool, and returns a human-readable answer.

---

### Phase 6 — Slack Gateway (Deferred)
**Goal:** Connect everything to Slack.

- [ ] `apps/slack_gateway/main.py` — Slack Bolt app
- [ ] `apps/slack_gateway/handlers.py` — message event handler → LangGraph agent
- [ ] `apps/slack_gateway/channel_router.py` — route by channel to correct BU context
- [ ] Docker-compose update to include gateway service
- [ ] End-to-end test: Slack message → agent → response in Slack thread

**Exit criteria:** Full round-trip working in all 3 back-office channels.

---

## Environment Variables (.env.example)

```env
# OpenAI
OPENAI_API_KEY=

# MongoDB Atlas
MONGODB_URI=
MONGODB_DB_NAME=ritecare

# Microservice URLs (internal)
BU1_BASE_URL=http://localhost:8001
BU2_BASE_URL=http://localhost:8002
BU3_BASE_URL=http://localhost:8003
BU4_BASE_URL=http://localhost:8004

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

```toml
[project]
dependencies = [
    # Web framework
    "fastapi>=0.115",
    "uvicorn[standard]>=0.30",

    # AI
    "openai>=1.50",
    "langgraph>=0.2",
    "langchain-openai>=0.2",

    # MCP
    "mcp>=1.0",

    # Database
    "motor>=3.5",           # Async MongoDB driver
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

---

## Current Status

| Phase | Status |
|-------|--------|
| Phase 1 — Foundation | Not started |
| Phase 2 — MongoDB Models | Not started |
| Phase 3 — RiteCare Microservices | Not started |
| Phase 4 — MCP Tools | Not started |
| Phase 5 — LangGraph Agent | Not started |
| Phase 6 — Slack Gateway | Deferred |
