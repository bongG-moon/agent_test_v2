"""다중 데이터셋 또는 다중 날짜 조회를 실행하는 노드."""

from ...graph.state import AgentGraphState
from ...services.runtime_service import run_multi_retrieval_jobs


def multi_retrieval_node(state: AgentGraphState) -> AgentGraphState:
    """현재 상태에 들어 있는 retrieval_jobs 를 다중 실행 경로로 넘긴다."""

    return {
        "result": run_multi_retrieval_jobs(
            user_input=state["user_input"],
            chat_history=state.get("chat_history", []),
            current_data=state.get("current_data"),
            jobs=state.get("retrieval_jobs", []),
            retrieval_plan=state.get("retrieval_plan"),
        )
    }
