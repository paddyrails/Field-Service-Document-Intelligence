from langgraph.graph import END, StateGraph
from langgraph.checkpoint.mongodb import MongoDBSaver
from pymongo import MongoClient
from shared.config import settings

from agent.nodes.intent_classifier import intent_classifier
from agent.nodes.tool_executor import tool_executor
from agent.nodes.responder import responder
from agent.nodes.input_guardrail import input_guardrail
from agent.nodes.output_guardrail import output_guardrail
from agent.state import AgentState

def _route_after_input_guardrail(state:AgentState) -> str:
    return "blocked" if state.get("blocked") else "ok"

def _route_after_output_guardrail(state: AgentState) -> str:
    #if final_response was cleared and feedback exists -> retry
    if not state.get("final_response") and state.get("grounding_feedback"):
        return "retry"
    return "done"

client = MongoClient(settings.mongodb_uri)

checkpointer = MongoDBSaver(
    connection_string=settings.mongodb_uri,
    db_name=settings.mongodb_db_name,
    client=client
)

def build_graph():

    graph = StateGraph(AgentState)

    #register nodes
    graph.add_node("input_guardrail", input_guardrail)
    graph.add_node("classify", intent_classifier)
    graph.add_node("execute_tools", tool_executor)
    graph.add_node("respond", responder)
    graph.add_node("output_guardrail", output_guardrail)

    #define flow
    graph.set_entry_point("input_guardrail")
    graph.add_conditional_edges(
        "input_guardrail",
        _route_after_input_guardrail, 
        {
            "ok": "classify",
            "blocked": END
        }
    )    
    graph.add_edge("classify", "execute_tools")
    graph.add_edge("execute_tools", "respond")
    graph.add_edge("respond", "output_guardrail")

    #Conditional: retry or finish
    graph.add_conditional_edges(
        "output_guardrail",
        _route_after_output_guardrail,
        {
            "retry": "respond",
            "done": END
        }
    )    

    return graph.compile(
        checkpointer=checkpointer,
        interrupt_before=["execute_tools"]    
    )

agent = build_graph()