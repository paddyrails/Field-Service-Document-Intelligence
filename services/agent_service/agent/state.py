from typing import NotRequired, TypedDict, Annotated

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]   # full conversation history (Langchain message format)
    intent: str                   # which BUs the query relates to, set by classifier or derived from bu_hint
    tool_calls: list[dict]        # tools the agent decided to call
    tool_results: list[dict]      # results returned from those calls
    session_id: str               # links this run to a MongoDB conversation record
    channel: str                  # Slack channel name
    bu_hint: NotRequired[str]     # BU pre-determined from channel mapping — skips LLM classifier
    final_response: str           # the composed answer, set by the responder node
    blocked: NotRequired[bool]
    grounding_retries: NotRequired[int]
    grounding_feedback: NotRequired[str]

    