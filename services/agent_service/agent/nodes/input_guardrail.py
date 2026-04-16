from agent.state import AgentState
from shared.guardrails import detect_prompt_injection, check_topic_relevance

async def input_guardrail(state: AgentState) -> dict:
    """
    Block obvious prompt injection or off-topic queries before LLM/tool calls
    """
    user_text = state["messages"][-1].content if state["messages"] else ""

    for check in (detect_prompt_injection, check_topic_relevance):
        error = check(user_text)
        if error:
            return {
                "blocked": True,
                "final_response": error
            }
        
    return {"blocked": False}