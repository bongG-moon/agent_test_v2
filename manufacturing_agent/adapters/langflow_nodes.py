"""Langflow-friendly wrappers around the same service layer.

Each function accepts and returns plain dictionaries so the logic can be used
both inside LangGraph and in future Langflow custom components.
"""

from typing import Any, Dict

from ..services.parameter_service import resolve_required_params
from ..services.query_mode import choose_query_mode
from ..services.retrieval_planner import build_retrieval_jobs, plan_retrieval_request
from ..services.runtime_service import run_followup_analysis, run_multi_retrieval_jobs, run_retrieval
from ..services.request_context import build_recent_chat_text, get_current_table_columns


def extract_params_component(input_state: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "extracted_params": resolve_required_params(
            user_input=input_state.get("user_input", ""),
            chat_history_text=build_recent_chat_text(input_state.get("chat_history", [])),
            current_data_columns=get_current_table_columns(input_state.get("current_data")),
            context=input_state.get("context", {}),
        )
    }


def decide_query_mode_component(input_state: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "query_mode": choose_query_mode(
            input_state.get("user_input", ""),
            input_state.get("current_data"),
            input_state.get("extracted_params", {}),
        )
    }


def plan_retrieval_component(input_state: Dict[str, Any]) -> Dict[str, Any]:
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
    return run_retrieval(
        user_input=input_state.get("user_input", ""),
        chat_history=input_state.get("chat_history", []),
        current_data=input_state.get("current_data"),
        extracted_params=input_state.get("extracted_params", {}),
    )


def multi_retrieval_component(input_state: Dict[str, Any]) -> Dict[str, Any]:
    return run_multi_retrieval_jobs(
        user_input=input_state.get("user_input", ""),
        chat_history=input_state.get("chat_history", []),
        current_data=input_state.get("current_data"),
        jobs=input_state.get("retrieval_jobs", []),
        retrieval_plan=input_state.get("retrieval_plan"),
    )


def followup_analysis_component(input_state: Dict[str, Any]) -> Dict[str, Any]:
    return run_followup_analysis(
        user_input=input_state.get("user_input", ""),
        chat_history=input_state.get("chat_history", []),
        current_data=input_state.get("current_data") or {},
        extracted_params=input_state.get("extracted_params", {}),
    )
