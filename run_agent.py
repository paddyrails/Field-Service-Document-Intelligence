"""
RiteCare AI Agent — CLI runner.

Usage:
    uv run python run_agent.py
"""

import asyncio
import uuid

from langchain_core.messages import HumanMessage

from agent.graph import agent


async def main() -> None:
    print("\n" + "═" * 55)
    print("  RiteCare AI Assistant")
    print("  Type your question and press Enter.")
    print("  Type 'quit' to exit.")
    print("═" * 55 + "\n")

    session_id = str(uuid.uuid4())
    messages = []

    while True:
        try:
            query = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break

        if not query:
            continue
        if query.lower() in ("quit", "exit", "q"):
            print("Goodbye.")
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

        print("\nAgent: thinking...\n")

        try:
            result = await agent.ainvoke(state)
            response = result.get("final_response", "Sorry, I could not generate a response.")

            print(f"Agent: {response}\n")

            # Keep conversation history for multi-turn context
            messages = list(result["messages"])

        except Exception as e:
            print(f"Agent: [Error] {type(e).__name__}: {e}\n")


if __name__ == "__main__":
    asyncio.run(main())
