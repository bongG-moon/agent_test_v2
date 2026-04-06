"""Node that extracts filters and chooses the first route."""

from ...graph.state import AgentGraphState
from ...services.parameter_service import resolve_required_params
from ...services.query_mode import choose_query_mode
from ...services.request_context import build_recent_chat_text, get_current_table_columns


def resolve_request_node(state: AgentGraphState) -> AgentGraphState:
    chat_history = state.get("chat_history", [])
    context = state.get("context", {})
    current_data = state.get("current_data")

    extracted_params = resolve_required_params(
        user_input=state["user_input"],
        chat_history_text=build_recent_chat_text(chat_history),
        current_data_columns=get_current_table_columns(current_data),
        context=context,
    )
    return {
        "extracted_params": extracted_params,
        "query_mode": choose_query_mode(state["user_input"], current_data, extracted_params),
    }
