"""Node that transforms the current table without fetching new raw data."""

from ...graph.state import AgentGraphState
from ...services.runtime_service import run_followup_analysis


def followup_analysis_node(state: AgentGraphState) -> AgentGraphState:
    current_data = state.get("current_data")
    if not isinstance(current_data, dict):
        return {
            "result": {
                "response": "현재 분석할 데이터가 없습니다. 먼저 데이터를 조회해 주세요.",
                "tool_results": [],
                "current_data": current_data,
                "extracted_params": state.get("extracted_params", {}),
                "awaiting_analysis_choice": False,
            }
        }

    return {
        "result": run_followup_analysis(
            user_input=state["user_input"],
            chat_history=state.get("chat_history", []),
            current_data=current_data,
            extracted_params=state.get("extracted_params", {}),
        )
    }
