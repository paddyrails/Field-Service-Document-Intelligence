from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from agent.state import AgentState
from shared.config import settings

_llm = ChatOpenAI(
    model=settings.openai_chat_model,
    temperature=0,
    api_key=settings.openai_api_key
)

CLASSIFIER_PROMPT = """
You are a query router for RiteCare, a field service company.

Given a user query, identify:
1. Which business unit(s) are relevant:
   - BU1 (onboarding): customer registration, KYC status, onboarding progress
   - BU2 (sales/maintenance): service contracts, field visits, maintenance schedules
   - BU3 (billing): invoices, subscription plans, payment status
   - BU4 (support): support tickets, escalations, SLA tracking
   - BU5 (care operations): patient visits, care preparation, personal care, skilled nursing, physical therapy, occupational therapy, respite care
2. What type of tools are needed: CRUD (live data lookup), RAG (document search), or BOTH

Respond in this exact format and nothing else:
INTENT: <BU1|BU2|BU3|BU4|BU5|BU1+BU2|...>, TOOLS: <CRUD|RAG|BOTH>

Examples:
- "What is the KYC status of customer C123?" → INTENT: BU1, TOOLS: CRUD
- "How do I service the X200 pump?" → INTENT: BU2, TOOLS: RAG
- "Has this pressure fault been seen before and is ticket T99 still open?" → INTENT: BU2+BU4, TOOLS: BOTH
- "What visits are scheduled for patient P456?" → INTENT: BU5, TOOLS: CRUD
- "What are the protocols for respite care visits?" → INTENT: BU5, TOOLS: RAG
- "Get visit V789 details and show me the care preparation guidelines" → INTENT: BU5, TOOLS: BOTH
"""

def _infer_tool_type(query: str) -> str:
    """Infer CRUD/RAG/BOTH from simple keyword matching — used when BU is already known."""
    q = query.lower()
    is_rag = any(k in q for k in ("how", "what is", "what are", "procedure", "protocol", "guideline", "manual", "explain", "describe"))
    is_crud = any(k in q for k in ("show", "get", "find", "list", "status", "id", "fetch", "lookup"))
    if is_rag and is_crud:
        return "BOTH"
    if is_rag:
        return "RAG"
    if is_crud:
        return "CRUD"
    return "BOTH"


async def intent_classifier(state: AgentState) -> dict:
    bu_hint = state.get("bu_hint", "")

    if bu_hint:
        # Channel already tells us the BU — skip the LLM call entirely
        tool_type = _infer_tool_type(state["messages"][-1].content)
        return {"intent": f"INTENT: {bu_hint}, TOOLS: {tool_type}"}

    # No BU hint — fall back to LLM classification
    user_message = state["messages"][-1]
    response = await _llm.ainvoke([
        SystemMessage(content=CLASSIFIER_PROMPT),
        HumanMessage(content=user_message.content),
    ])
    return {"intent": response.content.strip()}