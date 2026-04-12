---
name: Collaboration Feedback
description: How the user wants the assistant to behave — corrections and confirmed approaches
type: feedback
---

## Code style
Provide code one file at a time with explanations. User writes the code themselves.
**Why:** User wants to understand what they're writing, not just copy-paste.
**How to apply:** Always explain what each file does and walk through key decisions before or alongside the code.

## Architecture pattern
Strictly follow api → service → dao layering. Ingestion logic belongs in service layer, VectorDAO handles all DB persistence.
**Why:** User explicitly asked to follow the same pattern as existing BU services.
**How to apply:** Never let pipeline.py insert into MongoDB directly — always return data and let the service/DAO layer persist it.

## Rate limiting
Use `SlowAPIMiddleware` globally only. Never add per-route `@limiter.limit()` decorators.
**Why:** Per-route decorators conflict with FastAPI's `Depends()` dependency injection and cause FastAPIError.
**How to apply:** Only set `app.state.limiter` and `app.add_middleware(SlowAPIMiddleware)` in main.py.

## Package naming
Never name local packages the same as installed dependencies.
**Why:** `mcp/` directory conflicted with installed `mcp>=1.0` package — renamed to `ritecare_tools/`.
**How to apply:** Check pyproject.toml dependencies before naming local packages.

## Docker builds
When Docker is not picking up latest changes, use `docker compose build --no-cache`.
**Why:** Docker layer caching can serve stale images when only source code changes.
