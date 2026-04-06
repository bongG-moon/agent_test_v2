"""Typed state objects shared across LangGraph nodes.

We keep the state shape small and explicit so Python beginners can follow
which node creates which field.
"""

from typing import Any, Dict, List, Literal, TypedDict


QueryMode = Literal["retrieval", "followup_transform"]


class AgentGraphState(TypedDict, total=False):
    user_input: str
    chat_history: List[Dict[str, str]]
    context: Dict[str, Any]
    current_data: Dict[str, Any] | None
    extracted_params: Dict[str, Any]
    query_mode: QueryMode
    retrieval_plan: Dict[str, Any]
    retrieval_keys: List[str]
    retrieval_jobs: List[Dict[str, Any]]
    result: Dict[str, Any]
