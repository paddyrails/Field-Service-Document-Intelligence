from agent.state import AgentState
from ritecare_tools.tools.bu1_tools import get_customer_by_id, search_onboarding_docs
from ritecare_tools.tools.bu2_tools import get_contract_by_id, list_visits, search_service_manuals
from ritecare_tools.tools.bu3_tools import get_subscription, list_invoices, search_billing_statements
from ritecare_tools.tools.bu4_tools import get_ticket_by_id, list_tickets, search_knowledge_base

_CRUD_TOOLs: dict[str, list] = {
    "BU1": [get_customer_by_id],
    "BU2": [get_contract_by_id, list_visits],
    "BU3": [get_subscription, list_invoices],
    "BU4": [get_ticket_by_id, list_tickets]
}

_RAG_TOOLS: dict[str, list] = {
    "BU1": [search_onboarding_docs],
    "BU2": [search_service_manuals],
    "BU3": [search_billing_statements],
    "BU4": [search_knowledge_base]
}

def _parse_intent(intent: str) -> tuple[list[str], str]:
    """
    Parses 'INTENT: BU2+BU4, TOOLS: BOTH' into (['BU2', 'BU4'],'BOTH')                                        
      Returns (bu_list, tool_type)
    """
    intent_part, tools_part = intent.split(",")
    bus = intent_part.replace("INTENT:", "").strip().split("+")
    tool_type = tools_part.replace("TOOLS:", "").strip()
    return [bu.strip() for bu in bus], tool_type

async def tool_executor(state: AgentState) -> dict:
    user_query = state["messages"][-1].content
    bus, tool_type = _parse_intent(state["intent"])

    tool_results: list[dict] = []

    for bu in bus:
        if tool_type in ("CRUD", "BOTH"):
            for tool_fn in _CRUD_TOOLs.get(bu, []):
                try:
                    result = await tool_fn(user_query)
                    tool_results.append({
                        "tool": tool_fn.__name__,
                        "bu": bu,
                        "type": "CRUD",
                        "result": result
                    })
                except Exception as e:
                    tool_results.append({
                        "tool": tool_fn.__name__,
                        "bu": bu,
                        "type": "CRUD",
                        "result": f"Error: {str(e)}"
                    })
        if(tool_type in ("RAG", "BOTH")):
            for tool_fn in _RAG_TOOLS.get(bu, []):
                try:
                    result = await tool_fn(user_query)
                    tool_results.append({
                        "tool": tool_fn.__name__,
                        "bu": bu,
                        "type": "RAG",
                        "result": result
                    })
                except Exception as e:
                    tool_results.append({
                        "tool": tool_fn.__name__,
                        "bu": bu,
                        "type": "RAG",
                        "result": f"Error: {str(e)}"
                    })

    return {"tool_results": tool_results}