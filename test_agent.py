"""
Test runner for the RiteCare LangGraph agent.

Usage:
    uv run python test_agent.py                  # run all test cases
    uv run python test_agent.py --interactive     # interactive chat mode

Make sure all four BU services are running and seed_data.py has been executed first.
"""

import asyncio
import json
import sys

from langchain_core.messages import HumanMessage

from agent.graph import agent


# ── Test cases ────────────────────────────────────────────────────────────────
# Replace the customer_id/ticket_id values below with the real IDs
# printed by seed_data.py after seeding.

TEST_QUERIES = [
    {
        "name": "BU1 — CRUD — Customer profile lookup",
        "query": "What is the KYC status of customer Alice Johnson?",
        "session_id": "test-session-001",
        "channel": "help-sales-backoffice",
    },
    {
        "name": "BU1 — CRUD — Onboarding status",
        "query": "What is the onboarding status for customer Alice Johnson?",
        "session_id": "test-session-002",
        "channel": "help-sales-backoffice",
    },
    {
        "name": "BU2 — CRUD — List contracts",
        "query": "Show me all service contracts for customer Alice Johnson",
        "session_id": "test-session-003",
        "channel": "help-sales-backoffice",
    },
    {
        "name": "BU2 — CRUD — List visits",
        "query": "What field visits are scheduled for customer Bob Martinez?",
        "session_id": "test-session-004",
        "channel": "help-sales-backoffice",
    },
    {
        "name": "BU3 — CRUD — Subscription lookup",
        "query": "What subscription plan does Carol White have?",
        "session_id": "test-session-005",
        "channel": "help-billing-fulfillment-backoffice",
    },
    {
        "name": "BU3 — CRUD — Invoice list",
        "query": "Show me all invoices for customer Alice Johnson",
        "session_id": "test-session-006",
        "channel": "help-billing-fulfillment-backoffice",
    },
    {
        "name": "BU4 — CRUD — List tickets",
        "query": "What support tickets does Bob Martinez have open?",
        "session_id": "test-session-007",
        "channel": "help-billing-fulfillment-backoffice",
    },
    {
        "name": "BU2 — RAG — Service manual search",
        "query": "How do I diagnose and fix a pressure fault on an X200 pump unit?",
        "session_id": "test-session-008",
        "channel": "help-sales-backoffice",
    },
    {
        "name": "BU4 — RAG — Knowledge base search",
        "query": "What are the common causes of HVAC failure error code E-501?",
        "session_id": "test-session-009",
        "channel": "help-billing-fulfillment-backoffice",
    },
    {
        "name": "BU2+BU4 — BOTH — Cross-BU query",
        "query": (
            "Alice Johnson has a pressure fault on her X200 pump. "
            "Has this fault been seen before and what tickets exist for her?"
        ),
        "session_id": "test-session-010",
        "channel": "help-sales-backoffice",
    },
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def print_divider(title: str) -> None:
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_section(label: str, content: str) -> None:
    print(f"\n  [{label}]")
    print(f"  {content}")


def format_tool_results(tool_results: list[dict]) -> str:
    if not tool_results:
        return "  (no tool results)"
    lines = []
    for item in tool_results:
        result_str = json.dumps(item["result"], indent=6, default=str)
        lines.append(
            f"    • {item['type']} | {item['bu']} | {item['tool']}\n"
            f"      {result_str}"
        )
    return "\n".join(lines)


# ── Single test ───────────────────────────────────────────────────────────────

async def run_single_test(test: dict) -> None:
    print_divider(test["name"])

    initial_state = {
        "messages": [HumanMessage(content=test["query"])],
        "intent": "",
        "tool_calls": [],
        "tool_results": [],
        "session_id": test["session_id"],
        "channel": test["channel"],
        "final_response": "",
    }

    print_section("QUERY", test["query"])

    try:
        result = await agent.ainvoke(initial_state)
        print_section("INTENT", result.get("intent", "—"))
        print(f"\n  [TOOL RESULTS]")
        print(format_tool_results(result.get("tool_results", [])))
        print_section("RESPONSE", result.get("final_response", "—"))

    except Exception as e:
        print(f"\n  [ERROR] {type(e).__name__}: {e}")


# ── Run all tests ─────────────────────────────────────────────────────────────

async def run_all_tests() -> None:
    print("\n" + "═" * 60)
    print("  RiteCare LangGraph Agent — Test Runner")
    print(f"  Running {len(TEST_QUERIES)} test queries")
    print("═" * 60)

    passed = 0
    failed = 0

    for test in TEST_QUERIES:
        try:
            await run_single_test(test)
            passed += 1
        except Exception as e:
            print(f"\n  [FATAL] {test['name']}: {e}")
            failed += 1

    print("\n" + "═" * 60)
    print(f"  Done — {passed} passed, {failed} failed")
    print("═" * 60 + "\n")


# ── Interactive mode ──────────────────────────────────────────────────────────

async def run_interactive() -> None:
    print("\n" + "═" * 60)
    print("  RiteCare LangGraph Agent — Interactive Mode")
    print("  Type your query and press Enter.")
    print("  Type 'quit' to exit.")
    print("═" * 60 + "\n")

    session_id = "interactive-session-001"
    messages = []

    while True:
        try:
            query = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break

        if not query:
            continue
        if query.lower() in ("quit", "exit", "q"):
            print("Exiting.")
            break

        messages.append(HumanMessage(content=query))

        state = {
            "messages": messages,
            "intent": "",
            "tool_calls": [],
            "tool_results": [],
            "session_id": session_id,
            "channel": "help-sales-backoffice",
            "final_response": "",
        }

        try:
            result = await agent.ainvoke(state)
            response = result.get("final_response", "No response generated.")
            intent = result.get("intent", "—")

            print(f"\n  Intent : {intent}")
            print(f"  Agent  : {response}\n")

            # Carry conversation history forward for multi-turn context
            messages = list(result["messages"])

        except Exception as e:
            print(f"  [ERROR] {type(e).__name__}: {e}\n")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        asyncio.run(run_interactive())
    else:
        asyncio.run(run_all_tests())
