"""제조 에이전트의 공용 진입점 모음.

이 파일은 크게 두 가지 역할을 담당한다.

1. `run_agent`
   - LangGraph 런타임을 사용하는 일반 실행 진입점이다.
2. Langflow/외부 연동용 래퍼 함수들
   - 딕셔너리를 입력받아 딕셔너리를 반환한다.
   - 서비스 계층 함수를 직접 호출하므로, LangGraph 없이도 같은 로직을 재사용할 수 있다.

`adapters/langflow_nodes.py` 에 있던 얇은 래퍼를 여기로 모아서,
초보자 입장에서는 "에이전트 관련 진입점은 이 파일에 있다" 라고 이해할 수 있게 정리했다.
"""

from typing import Any, Callable, Dict, List

from .graph.nodes.followup_analysis import followup_analysis_node
from .graph.nodes.plan_retrieval import plan_retrieval_node
from .graph.nodes.resolve_request import resolve_request_node
from .graph.nodes.retrieve_multi import multi_retrieval_node
from .graph.nodes.retrieve_single import single_retrieval_node
from .graph.builder import get_agent_graph
from .graph.state import AgentGraphState
from .services.parameter_service import resolve_required_params
from .services.query_mode import choose_query_mode
from .services.request_context import build_recent_chat_text, get_current_table_columns
from .services.retrieval_planner import build_retrieval_jobs, plan_retrieval_request
from .services.runtime_service import run_followup_analysis, run_multi_retrieval_jobs, run_retrieval


def run_agent(
    user_input: str,
    chat_history: List[Dict[str, str]] | None = None,
    context: Dict[str, Any] | None = None,
    current_data: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """LangGraph 기반 제조 에이전트를 한 번 실행한다.

    사용자가 질문을 입력하면, 이 함수가 그래프의 시작 상태를 만들고
    `get_agent_graph()` 로 생성한 워크플로우를 실행한다.
    최종적으로는 그래프의 `result` 필드만 꺼내서 UI 쪽으로 돌려준다.
    """

    initial_state: AgentGraphState = {
        "user_input": user_input,
        "chat_history": chat_history or [],
        "context": context or {},
        "current_data": current_data if isinstance(current_data, dict) else None,
    }
    final_state = get_agent_graph().invoke(initial_state)
    return dict(final_state.get("result", {}))


def run_agent_with_progress(
    user_input: str,
    chat_history: List[Dict[str, str]] | None = None,
    context: Dict[str, Any] | None = None,
    current_data: Dict[str, Any] | None = None,
    progress_callback: Callable[[str, str], None] | None = None,
) -> Dict[str, Any]:
    """앱에서 실제 단계 진행 상태를 보여줄 수 있도록 노드를 순서대로 실행한다."""

    def notify(title: str, detail: str) -> None:
        if progress_callback is not None:
            progress_callback(title, detail)

    state: AgentGraphState = {
        "user_input": user_input,
        "chat_history": chat_history or [],
        "context": context or {},
        "current_data": current_data if isinstance(current_data, dict) else None,
    }

    notify("1/3 파라미터 해석중", "질문에서 날짜, 공정, 제품, 기준 조건을 정리하고 있습니다.")
    state.update(resolve_request_node(state))

    if state.get("query_mode") == "followup_transform" and isinstance(state.get("current_data"), dict):
        notify("3/3 병합/분석중", "현재 결과를 다시 정리하고 분석하고 있습니다.")
        state.update(followup_analysis_node(state))
        return dict(state.get("result", {}))

    notify("2/3 데이터 조회중", "필요한 데이터셋과 조회 계획을 계산하고 있습니다.")
    state.update(plan_retrieval_node(state))
    if state.get("result"):
        return dict(state.get("result", {}))

    jobs = state.get("retrieval_jobs", [])
    if len(jobs) > 1:
        notify("3/3 병합/분석중", "여러 데이터셋을 조회한 뒤 병합과 분석을 수행하고 있습니다.")
        state.update(multi_retrieval_node(state))
    else:
        notify("3/3 병합/분석중", "데이터를 조회하고 필요한 후처리와 분석을 수행하고 있습니다.")
        state.update(single_retrieval_node(state))

    return dict(state.get("result", {}))


def extract_params_component(input_state: Dict[str, Any]) -> Dict[str, Any]:
    """Langflow 스타일의 파라미터 추출 래퍼.

    입력 상태에서 질문/대화/현재 테이블/컨텍스트를 읽고,
    조회에 필요한 필터 조건을 `extracted_params` 로 반환한다.
    """

    return {
        "extracted_params": resolve_required_params(
            user_input=input_state.get("user_input", ""),
            chat_history_text=build_recent_chat_text(input_state.get("chat_history", [])),
            current_data_columns=get_current_table_columns(input_state.get("current_data")),
            context=input_state.get("context", {}),
        )
    }


def decide_query_mode_component(input_state: Dict[str, Any]) -> Dict[str, Any]:
    """현재 질문이 재조회인지 후속 분석인지 판단한다."""

    return {
        "query_mode": choose_query_mode(
            input_state.get("user_input", ""),
            input_state.get("current_data"),
            input_state.get("extracted_params", {}),
        )
    }


def plan_retrieval_component(input_state: Dict[str, Any]) -> Dict[str, Any]:
    """재조회가 필요할 때 어떤 데이터셋을 가져올지 계획한다."""

    retrieval_plan = plan_retrieval_request(
        input_state.get("user_input", ""),
        input_state.get("chat_history", []),
        input_state.get("current_data"),
    )
    return {
        "retrieval_plan": retrieval_plan,
        "retrieval_jobs": build_retrieval_jobs(
            input_state.get("user_input", ""),
            input_state.get("extracted_params", {}),
            retrieval_plan.get("dataset_keys", []),
        ),
    }


def retrieval_component(input_state: Dict[str, Any]) -> Dict[str, Any]:
    """단일/일반 재조회 흐름을 서비스 계층으로 위임한다."""

    return run_retrieval(
        user_input=input_state.get("user_input", ""),
        chat_history=input_state.get("chat_history", []),
        current_data=input_state.get("current_data"),
        extracted_params=input_state.get("extracted_params", {}),
    )


def multi_retrieval_component(input_state: Dict[str, Any]) -> Dict[str, Any]:
    """이미 생성된 여러 retrieval job 을 실행하고 병합/분석까지 이어간다."""

    return run_multi_retrieval_jobs(
        user_input=input_state.get("user_input", ""),
        chat_history=input_state.get("chat_history", []),
        current_data=input_state.get("current_data"),
        jobs=input_state.get("retrieval_jobs", []),
        retrieval_plan=input_state.get("retrieval_plan"),
    )


def followup_analysis_component(input_state: Dict[str, Any]) -> Dict[str, Any]:
    """현재 테이블을 재사용하는 후속 분석 래퍼."""

    return run_followup_analysis(
        user_input=input_state.get("user_input", ""),
        chat_history=input_state.get("chat_history", []),
        current_data=input_state.get("current_data") or {},
        extracted_params=input_state.get("extracted_params", {}),
    )
