from langgraph.graph import END, StateGraph

from agent.nodes.intent_classifier import intent_classifier
from agent.nodes.tool_executor import tool_executor
from agent.nodes.responder import responder
from agent.state import AgentState

def build_graph():

    graph = StateGraph(AgentState)

    #register nodes
    graph.add_node("classify", intent_classifier)
    graph.add_node("execute_tools", tool_executor)
    graph.add_node("respond", responder)

    #define flow
    graph.set_entry_point("classify")
    graph.add_edge("classify", "execute_tools")
    graph.add_edge("execute_tools", "respond")
    graph.add_edge("respond", END)

    return graph.compile()

agent = build_graph()