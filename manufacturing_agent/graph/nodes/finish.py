"""Final node that normalizes the returned payload."""

from ...graph.state import AgentGraphState


def finish_node(state: AgentGraphState) -> AgentGraphState:
    result = dict(state.get("result", {}))
    if result:
        result.setdefault("execution_engine", "langgraph_v2")
    return {"result": result}
