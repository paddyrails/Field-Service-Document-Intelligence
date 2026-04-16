from google.adk.agents import Agent
from google.adk.models.llm_response import LlmResponse
from google.genai import types
from ritecare_tools.tools.bu1_tools import get_customer_by_id, get_onboarding_status, search_onboarding_docs
from ritecare_tools.tools.bu2_tools import get_contract_by_id, list_contracts, list_visits, search_service_manuals
from ritecare_tools.tools.bu3_tools import get_subscription, list_invoices, search_billing_statements
from ritecare_tools.tools.bu4_tools import get_ticket_by_id, list_tickets, search_knowledge_base, search_resolved_tickets
from ritecare_tools.tools.bu5_tools import get_visit_by_id, list_patient_visits, search_care_documents
from ritecare_tools.tools.rag_tools import search_bu_documents
from shared.guardrails import detect_prompt_injection, check_grounding, check_topic_relevance, redact_pii

SYSTEM_INSTRUCTION = """
  You are the RiteCare AI assistant for a field-service company.

  You have access to 5 business units:
  - BU1 (Onboarding): customer registration, KYC status, insurance
  - BU2 (Sales/Maintenance): service contracts, field visits
  - BU3 (Billing): invoices, subscriptions, payments
  - BU4 (Support): tickets, escalations, SLA tracking
  - BU5 (Care Operations): patient visits, care preparation, nursing, therapy

  Use the appropriate tools based on the query:
  - For live data lookups (status, records): use CRUD tools (get_*, list_*)
  - For knowledge/procedures/protocols: use search/RAG tools
  - You may call multiple tools if the query spans multiple BUs

  Always cite which BU the information came from.
  """

# Tool names whose outputs should count as "retrieved context" for grounding    
RAG_TOOL_NAMES = {                                                            
    "search_onboarding_docs",                                                   
    "search_service_manuals",                                                 
    "search_billing_statements",                                                
    "search_knowledge_base",                                                    
    "search_resolved_tickets",
    "search_care_documents",                                                    
    "search_bu_documents",                                                    
}

def _extract_docs(tool_result) -> list[str]:
    """Normalize a RAG tool result into a list of text chunks"""
    if isinstance(tool_result, list):
        return [str(d.get("text",d)) if isinstance(d, dict) else str(d) for d in tool_result]
    if isinstance(tool_result, dict) and "results" in tool_result:
        return [str(d.get("text")) if isinstance(d, dict) else str(d) for d in tool_result["results"]]
    return [str(tool_result)]


def after_tool_callback(tool, args, tool_context, tool_response):
    """Capture RAG results into session state so we can ground check later"""
    if tool.name in RAG_TOOL_NAMES:
        docs = tool_context.state.get("retrieved_docs", [])
        docs.extend(_extract_docs(tool_response))
        
        tool_context.state["retrieved_docs"] = tool_context.state.get("retrieved_docs",
  []) + _extract_docs(tool_response) 
    return None

def before_model_callback(callback_context, llm_request):
    """Input guardrail - runs before each LLM call"""
    if not llm_request.contents or not llm_request.contents[-1].parts:
        return None
    
    user_text = llm_request.contents[-1].parts[0].text or ""

    #check for prompt injections
    error = detect_prompt_injection(user_text)
    if error:
        return LlmResponse(
            content=types.Content(
                role="model",
                parts=[types.Part(text=error)]
            )
        )
    
    #check topic relevance
    error = check_topic_relevance(user_text)
    if error:
        return LlmResponse(
            content=types.Content(
                role="model",
                parts=[types.Part(text=error)]
            )
        )
    
    #redct sensitive PII (SSN, credit card) in place before sending to LLM
    # llm_request.contents[-1].parts[0].text = redact_pii(user_text)

async def after_model_callback(callback_context, llm_response):
    """Output guardrails - runs after each llm call to redact PII"""
    if not (llm_response.content and llm_response.content.parts):
        return llm_response
    
    for part in llm_response.content.parts:
        if part.text:
            part.text = redact_pii(part.text)

    retrieved_docs = callback_context.state.get("retrieved_docs", [])
    if retrieved_docs:
        response_text = "".join(p.text or "" for p in llm_response.content.parts)
        if response_text.strip():
            verdict = await check_grounding(response_text, retrieved_docs)
            if not verdict.get("grounded", True):
                warning = f"\n\n [Ungrounded: {verdict.get('reason', 'no reason given')}]"
                llm_response.content.parts[-1].text = (
                    (llm_response.content.parts[-1].text or "") + warning
                )
        #clear so next turn starts fresh
        callback_context.state["retrieved_docs"] = []
    return llm_response
    

root_agent = Agent(
    name="ritecare_agent",
    model="gemini-2.5-flash",
    instruction=SYSTEM_INSTRUCTION,
    tools=[
        # BU1
        get_customer_by_id, get_onboarding_status, search_onboarding_docs,
        # BU2
        get_contract_by_id, list_contracts, list_visits, search_service_manuals,
        # BU3
        get_subscription, list_invoices, search_billing_statements,
        # BU4
        get_ticket_by_id, list_tickets, search_knowledge_base, search_resolved_tickets,
        # BU5
        get_visit_by_id, list_patient_visits, search_care_documents,
        # Cross-BU RAG
        search_bu_documents,
    ],
    before_model_callback=before_model_callback,
    after_model_callback=after_model_callback,
    after_tool_callback=after_tool_callback
)