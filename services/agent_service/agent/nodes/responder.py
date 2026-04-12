import json

from langchain_core.messages import AIMessage, SystemMessage
from langchain_openai import ChatOpenAI

from agent.prompts.system_prompt import SYSTEM_PROMPT
from agent.state import AgentState
from shared.config import settings

_llm = ChatOpenAI(
    model=settings.openai_chat_model,
    temperature=0.2,
    api_key=settings.openai_api_key
)

def _format_tool_results(tool_results: list[dict]) -> str:
    """
    Converts tool results in to a readable string block to inject into the LLM context    
    """
    if not tool_results:
        return "NO tool reults available:"
    
    lines = []
    for item in tool_results:
        lines.append(
            f"[{item['type']} | {item["bu"]} | {item['tool']}] \n"
            f"{json.dumps(item['result'], indent = 2, default=str)}"
        )
    return "\n\n".join(lines)

async def responder(state: AgentState) -> dict:
    tool_context = _format_tool_results(state["tool_results"])

    context_message = (
        f"The following data was retrieved to answer the user's question: \n\n"
        f"{tool_context}\n\n"
        f"Use this data to answer the user's question accurately and concisely."
    )

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        *state["messages"],
        SystemMessage(content=context_message)
    ]

    response = await _llm.ainvoke(messages)

    updated_messages = list(state["messages"]) + [
        AIMessage(content=response.content)
    ]

    return {
        "messages": updated_messages,
        "final_response": response.content
    }