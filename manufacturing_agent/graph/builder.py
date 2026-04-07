"""제조 에이전트용 LangGraph 구성 파일.

예전에는 그래프를 만드는 코드와 라우팅 함수를 분리했지만,
파일 수가 늘어나는 것보다 "그래프 흐름을 한 파일에서 읽는 경험" 이 더 중요하다고 판단해
`builder.py` 안에 같이 배치했다.
"""

from langgraph.graph import END, START, StateGraph

from .nodes.finish import finish_node
from .nodes.followup_analysis import followup_analysis_node
from .nodes.plan_retrieval import plan_retrieval_node
from .nodes.resolve_request import resolve_request_node
from .nodes.retrieve_multi import multi_retrieval_node
from .nodes.retrieve_single import single_retrieval_node
from .state import AgentGraphState


def route_after_resolve(state: AgentGraphState) -> str:
    """첫 번째 분기점.

    `resolve_request_node` 가 질문을 해석한 뒤,
    바로 현재 테이블 후처리로 갈지 아니면 새 조회 계획으로 갈지를 결정한다.
    """

    if state.get("query_mode") == "followup_transform" and isinstance(state.get("current_data"), dict):
        return "followup_analysis"
    return "plan_retrieval"


def route_after_retrieval_plan(state: AgentGraphState) -> str:
    """두 번째 분기점.

    조회 계획이 끝난 뒤 바로 종료할지,
    단일 조회로 갈지,
    다중 조회로 갈지를 결정한다.
    """

    if state.get("result"):
        return "finish"

    jobs = state.get("retrieval_jobs", [])
    if len(jobs) > 1:
        return "multi_retrieval"
    return "single_retrieval"


def get_agent_graph():
    """현재 코드 기준의 LangGraph 워크플로우를 새로 만들어 반환한다.

    Streamlit 환경에서는 코드가 자주 다시 로드되므로,
    그래프를 전역으로 캐시하기보다 호출할 때마다 새로 만드는 편이 안전하다.
    """

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
