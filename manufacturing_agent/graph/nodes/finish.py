"""그래프 최종 결과 형태를 정리하는 노드."""

from ...graph.state import AgentGraphState


def finish_node(state: AgentGraphState) -> AgentGraphState:
    """`result` 필드에 실행 엔진 정보를 보강해 반환한다."""

    result = dict(state.get("result", {}))
    if result:
        result.setdefault("execution_engine", "langgraph_v2")
    return {"result": result}
