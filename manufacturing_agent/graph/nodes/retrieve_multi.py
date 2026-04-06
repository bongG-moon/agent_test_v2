"""Node for multi-dataset or multi-date retrieval jobs."""

from ...graph.state import AgentGraphState
from ...services.runtime_service import run_multi_retrieval_jobs


def multi_retrieval_node(state: AgentGraphState) -> AgentGraphState:
    return {
        "result": run_multi_retrieval_jobs(
            user_input=state["user_input"],
            chat_history=state.get("chat_history", []),
            current_data=state.get("current_data"),
            jobs=state.get("retrieval_jobs", []),
            retrieval_plan=state.get("retrieval_plan"),
        )
    }
