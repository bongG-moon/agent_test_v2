"""Public entrypoint for the refactored manufacturing agent."""

from typing import Any, Dict, List

from .graph.builder import get_agent_graph
from .graph.state import AgentGraphState


def run_agent(
    user_input: str,
    chat_history: List[Dict[str, str]] | None = None,
    context: Dict[str, Any] | None = None,
    current_data: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    initial_state: AgentGraphState = {
        "user_input": user_input,
        "chat_history": chat_history or [],
        "context": context or {},
        "current_data": current_data if isinstance(current_data, dict) else None,
    }
    final_state = get_agent_graph().invoke(initial_state)
    return dict(final_state.get("result", {}))
