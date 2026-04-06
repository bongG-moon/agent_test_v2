"""Node that transforms the current table without fetching new raw data."""

from ...graph.state import AgentGraphState
from ...services.runtime_service import run_followup_analysis


def followup_analysis_node(state: AgentGraphState) -> AgentGraphState:
    current_data = state.get("current_data")
    if not isinstance(current_data, dict):
        return {
            "result": {
                "response": "?꾩옱 ?꾩냽 遺꾩꽍???ъ슜???곗씠?곌? ?놁뒿?덈떎. 癒쇱? ?곗씠?곕? 議고쉶??二쇱꽭??",
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
