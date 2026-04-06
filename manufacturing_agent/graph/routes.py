"""Routing helpers for the LangGraph workflow."""

from .state import AgentGraphState


def route_after_resolve(state: AgentGraphState) -> str:
    if state.get("query_mode") == "followup_transform" and isinstance(state.get("current_data"), dict):
        return "followup_analysis"
    return "plan_retrieval"


def route_after_retrieval_plan(state: AgentGraphState) -> str:
    if state.get("result"):
        return "finish"

    jobs = state.get("retrieval_jobs", [])
    if len(jobs) > 1:
        return "multi_retrieval"
    return "single_retrieval"
