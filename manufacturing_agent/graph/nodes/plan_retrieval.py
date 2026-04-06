"""Node that turns a request into executable retrieval jobs."""

from ...data.retrieval import dataset_requires_date, pick_retrieval_tools
from ...graph.state import AgentGraphState
from ...services.request_context import build_unknown_retrieval_message, has_current_data
from ...services.retrieval_planner import build_missing_date_message, build_retrieval_jobs, plan_retrieval_request


def plan_retrieval_node(state: AgentGraphState) -> AgentGraphState:
    user_input = state["user_input"]
    current_data = state.get("current_data")
    extracted_params = state.get("extracted_params", {})
    retrieval_plan = plan_retrieval_request(user_input, state.get("chat_history", []), current_data)
    retrieval_keys = retrieval_plan.get("dataset_keys") or pick_retrieval_tools(user_input)

    if not retrieval_keys:
        return {
            "retrieval_plan": retrieval_plan,
            "retrieval_keys": [],
            "retrieval_jobs": [],
            "result": {
                "response": build_unknown_retrieval_message(),
                "tool_results": [],
                "current_data": current_data,
                "extracted_params": extracted_params,
                "awaiting_analysis_choice": bool(has_current_data(current_data)),
            },
        }

    jobs = build_retrieval_jobs(user_input, extracted_params, retrieval_keys)
    if not jobs:
        return {
            "retrieval_plan": retrieval_plan,
            "retrieval_keys": retrieval_keys,
            "retrieval_jobs": [],
            "result": {
                "response": build_unknown_retrieval_message(),
                "tool_results": [],
                "current_data": current_data,
                "extracted_params": extracted_params,
                "awaiting_analysis_choice": bool(has_current_data(current_data)),
            },
        }

    missing_date_jobs = [job for job in jobs if dataset_requires_date(job["dataset_key"]) and not job["params"].get("date")]
    if missing_date_jobs:
        return {
            "retrieval_plan": retrieval_plan,
            "retrieval_keys": retrieval_keys,
            "retrieval_jobs": jobs,
            "result": {
                "response": build_missing_date_message([job["dataset_key"] for job in missing_date_jobs]),
                "tool_results": [],
                "current_data": current_data,
                "extracted_params": extracted_params,
                "awaiting_analysis_choice": bool(has_current_data(current_data)),
            },
        }

    return {
        "retrieval_plan": retrieval_plan,
        "retrieval_keys": retrieval_keys,
        "retrieval_jobs": jobs,
    }
