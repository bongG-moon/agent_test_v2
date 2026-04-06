"""Node for the common single-dataset retrieval path."""

from ...graph.state import AgentGraphState
from ...services.request_context import attach_result_metadata
from ...services.response_service import generate_response
from ...services.runtime_service import mark_primary_result, run_analysis_after_retrieval
from ...services.retrieval_planner import execute_retrieval_jobs


def single_retrieval_node(state: AgentGraphState) -> AgentGraphState:
    extracted_params = state.get("extracted_params", {})
    chat_history = state.get("chat_history", [])
    current_data = state.get("current_data")
    jobs = state.get("retrieval_jobs", [])
    single_job = jobs[0]

    result = execute_retrieval_jobs([single_job])[0]
    result = attach_result_metadata(result, single_job["params"], result.get("tool_name", ""))

    if result.get("success"):
        post_processed = run_analysis_after_retrieval(
            user_input=state["user_input"],
            chat_history=chat_history,
            source_results=[result],
            extracted_params=single_job["params"],
            retrieval_plan=state.get("retrieval_plan"),
        )
        if post_processed is not None:
            return {"result": post_processed}

    tool_results = mark_primary_result([result], primary_index=0)
    return {
        "result": {
            "response": generate_response(state["user_input"], result, chat_history)
            if result.get("success")
            else result.get("error_message", "조회 결과를 처리하지 못했습니다."),
            "tool_results": tool_results,
            "current_data": result if result.get("success") else current_data,
            "extracted_params": single_job["params"] or extracted_params,
            "awaiting_analysis_choice": bool(result.get("success")),
        }
    }
