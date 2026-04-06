"""Build the LangGraph workflow from small node functions."""

from langgraph.graph import END, START, StateGraph

from .nodes.finish import finish_node
from .nodes.followup_analysis import followup_analysis_node
from .nodes.plan_retrieval import plan_retrieval_node
from .nodes.resolve_request import resolve_request_node
from .nodes.retrieve_multi import multi_retrieval_node
from .nodes.retrieve_single import single_retrieval_node
from .routes import route_after_resolve, route_after_retrieval_plan
from .state import AgentGraphState


def get_agent_graph():
    """Return a fresh graph so Streamlit reloads always pick up new code."""

    graph = StateGraph(AgentGraphState)
    graph.add_node("resolve_request", resolve_request_node)
    graph.add_node("plan_retrieval", plan_retrieval_node)
    graph.add_node("single_retrieval", single_retrieval_node)
    graph.add_node("multi_retrieval", multi_retrieval_node)
    graph.add_node("followup_analysis", followup_analysis_node)
    graph.add_node("finish", finish_node)

    graph.add_edge(START, "resolve_request")
    graph.add_conditional_edges(
        "resolve_request",
        route_after_resolve,
        {
            "followup_analysis": "followup_analysis",
            "plan_retrieval": "plan_retrieval",
        },
    )
    graph.add_conditional_edges(
        "plan_retrieval",
        route_after_retrieval_plan,
        {
            "finish": "finish",
            "single_retrieval": "single_retrieval",
            "multi_retrieval": "multi_retrieval",
        },
    )
    graph.add_edge("single_retrieval", "finish")
    graph.add_edge("multi_retrieval", "finish")
    graph.add_edge("followup_analysis", "finish")
    graph.add_edge("finish", END)
    return graph.compile()
