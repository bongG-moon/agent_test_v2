"""Langflow 버전에서 재사용하는 순수 파이썬 워크플로우 헬퍼."""

from __future__ import annotations

import json
from typing import Any, Dict, List

from manufacturing_agent.graph.builder import route_after_resolve, route_after_retrieval_plan
from manufacturing_agent.graph.nodes.finish import finish_node
from manufacturing_agent.graph.nodes.followup_analysis import followup_analysis_node
from manufacturing_agent.graph.nodes.plan_retrieval import plan_retrieval_node
from manufacturing_agent.graph.nodes.resolve_request import resolve_request_node
from manufacturing_agent.graph.nodes.retrieve_multi import multi_retrieval_node
from manufacturing_agent.graph.nodes.retrieve_single import single_retrieval_node
from manufacturing_agent.graph.state import AgentGraphState


def _coerce_json_field(value: Any, default: Any) -> Any:
    """문자열 JSON 입력을 실제 파이썬 객체로 바꾼다."""

    if value is None or value == "":
        return default
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(str(value))
    except Exception:
        return default


def build_initial_state(
    user_input: str,
    chat_history: List[Dict[str, str]] | str | None = None,
    context: Dict[str, Any] | str | None = None,
    current_data: Dict[str, Any] | str | None = None,
) -> AgentGraphState:
    """LangGraph 버전과 동일한 기본 상태를 만든다."""

    return {
        "user_input": str(user_input or ""),
        "chat_history": _coerce_json_field(chat_history, []),
        "context": _coerce_json_field(context, {}),
        "current_data": _coerce_json_field(current_data, None),
    }


def resolve_request_step(state: AgentGraphState) -> AgentGraphState:
    """질문 해석 단계만 실행한다."""

    return {**state, **resolve_request_node(state)}


def plan_retrieval_step(state: AgentGraphState) -> AgentGraphState:
    """조회 계획 단계만 실행한다."""

    return {**state, **plan_retrieval_node(state)}


def run_followup_step(state: AgentGraphState) -> AgentGraphState:
    """현재 테이블 후처리 단계를 실행한다."""

    return {**state, **followup_analysis_node(state)}


def run_single_retrieval_step(state: AgentGraphState) -> AgentGraphState:
    """단일 조회 단계를 실행한다."""

    return {**state, **single_retrieval_node(state)}


def run_multi_retrieval_step(state: AgentGraphState) -> AgentGraphState:
    """다중 조회 단계를 실행한다."""

    return {**state, **multi_retrieval_node(state)}


def finish_step(state: AgentGraphState) -> AgentGraphState:
    """마지막 결과 형태를 Langflow 쪽에서도 동일하게 맞춘다."""

    finished = {**state, **finish_node(state)}
    if finished.get("result"):
        finished["result"]["execution_engine"] = "langflow_v2"
    return finished


def run_next_branch(state: AgentGraphState) -> AgentGraphState:
    """현재 상태를 보고 다음에 실행할 분기 하나를 처리한다."""

    first_route = route_after_resolve(state)
    if first_route == "followup_analysis":
        return run_followup_step(state)

    planned_state = plan_retrieval_step(state)
    second_route = route_after_retrieval_plan(planned_state)
    if second_route == "finish":
        return planned_state
    if second_route == "multi_retrieval":
        return run_multi_retrieval_step(planned_state)
    return run_single_retrieval_step(planned_state)


def run_langflow_workflow(
    user_input: str,
    chat_history: List[Dict[str, str]] | str | None = None,
    context: Dict[str, Any] | str | None = None,
    current_data: Dict[str, Any] | str | None = None,
) -> Dict[str, Any]:
    """LangGraph 런타임 없이 전체 흐름을 끝까지 실행한다."""

    state = build_initial_state(
        user_input=user_input,
        chat_history=chat_history,
        context=context,
        current_data=current_data,
    )
    state = resolve_request_step(state)
    state = run_next_branch(state)
    state = finish_step(state)
    return dict(state.get("result", {}))
