"""LangGraph 노드들이 공유하는 상태 정의.

상태 구조를 작고 명시적으로 유지하면,
파이썬 초보자도 "어느 노드가 어떤 값을 추가하는지" 추적하기 쉬워진다.
"""

from typing import Any, Dict, List, Literal, TypedDict


QueryMode = Literal["retrieval", "followup_transform"]


class AgentGraphState(TypedDict, total=False):
    """그래프 전체에서 주고받는 상태 딕셔너리 모양."""

    user_input: str
    chat_history: List[Dict[str, str]]
    context: Dict[str, Any]
    current_data: Dict[str, Any] | None
    extracted_params: Dict[str, Any]
    query_mode: QueryMode
    retrieval_plan: Dict[str, Any]
    retrieval_keys: List[str]
    retrieval_jobs: List[Dict[str, Any]]
    result: Dict[str, Any]
