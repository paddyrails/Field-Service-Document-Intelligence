from typing import TypedDict

from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    messages: list[BaseMessage] # full conversation history (Langchain message format)
    intent: str # which BUs the query relates to classified by the first node
    tool_calls: list[dict] # tools the agent decided to call
    tool_results: list[dict] # Results returned from those calls
    session_id: str # Links this run to a MongoDB conversation record
    channel: str # Slack channel name (used to inject BU context)
    final_response: str # the composed answer, set by the responder node

    