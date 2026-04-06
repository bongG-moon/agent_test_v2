"""Pure-Python workflow helpers for a Langflow version of the agent.

The goal of this module is to keep all business logic in reusable service
functions while exposing step-based helpers that match how Langflow flows are
usually built.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

from manufacturing_agent.graph.routes import route_after_resolve, route_after_retrieval_plan
from manufacturing_agent.graph.state import AgentGraphState
from manufacturing_agent.graph.nodes.finish import finish_node
from manufacturing_agent.graph.nodes.followup_analysis import followup_analysis_node
from manufacturing_agent.graph.nodes.plan_retrieval import plan_retrieval_node
from manufacturing_agent.graph.nodes.resolve_request import resolve_request_node
from manufacturing_agent.graph.nodes.retrieve_multi import multi_retrieval_node
from manufacturing_agent.graph.nodes.retrieve_single import single_retrieval_node


def _coerce_json_field(value: Any, default: Any) -> Any:
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
    """Create the same base state shape used by the LangGraph version."""

    return {
        "user_input": str(user_input or ""),
        "chat_history": _coerce_json_field(chat_history, []),
        "context": _coerce_json_field(context, {}),
        "current_data": _coerce_json_field(current_data, None),
    }


def resolve_request_step(state: AgentGraphState) -> AgentGraphState:
    return {**state, **resolve_request_node(state)}


def plan_retrieval_step(state: AgentGraphState) -> AgentGraphState:
    return {**state, **plan_retrieval_node(state)}


def run_followup_step(state: AgentGraphState) -> AgentGraphState:
    return {**state, **followup_analysis_node(state)}


def run_single_retrieval_step(state: AgentGraphState) -> AgentGraphState:
    return {**state, **single_retrieval_node(state)}


def run_multi_retrieval_step(state: AgentGraphState) -> AgentGraphState:
    return {**state, **multi_retrieval_node(state)}


def finish_step(state: AgentGraphState) -> AgentGraphState:
    finished = {**state, **finish_node(state)}
    if finished.get("result"):
        finished["result"]["execution_engine"] = "langflow_v2"
    return finished


def run_next_branch(state: AgentGraphState) -> AgentGraphState:
    """Run the next required branch based on the current workflow state."""

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
    """Run the full workflow without the LangGraph runtime."""

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
