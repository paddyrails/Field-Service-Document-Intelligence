from google.adk.agents import Agent
from ritecare_tools.tools.bu1_tools import get_customer_by_id, get_onboarding_status, search_onboarding_docs
from ritecare_tools.tools.bu2_tools import get_contract_by_id, list_contracts, list_visits, search_service_manuals
from ritecare_tools.tools.bu3_tools import get_subscription, list_invoices, search_billing_statements
from ritecare_tools.tools.bu4_tools import get_ticket_by_id, list_tickets, search_knowledge_base, search_resolved_tickets
from ritecare_tools.tools.bu5_tools import get_visit_by_id, list_patient_visits, search_care_documents
from ritecare_tools.tools.rag_tools import search_bu_documents

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
)