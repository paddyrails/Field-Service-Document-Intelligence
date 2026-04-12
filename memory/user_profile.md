---
name: User Profile
description: User role, preferences, and working style for this project
type: user
---

## Role
Developer working on a Python AI project for a Synechron interview (2026).

## Working Style
- User writes the code, assistant suggests/provides code with explanations
- Prefers code provided one file at a time with clear explanations
- Asks for clarification before large architectural decisions
- Actively tests code and shares error tracebacks for debugging

## Preferences
- Monorepo structure (not separate repos per service)
- LangGraph for AI orchestration (switched from PydanticAI)
- Wants explanations alongside code — not just raw code dumps
- Prefers clean architecture: api → service → dao layers strictly separated
- Docker for running services
- Uses `uv` as package manager
