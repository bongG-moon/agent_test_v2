"""Langflow custom component: Extract Manufacturing Params."""

from __future__ import annotations

import sys
from pathlib import Path

from lfx.custom.custom_component.component import Component
from lfx.io import DataInput, Output


def _ensure_repo_root() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    repo_root_text = str(repo_root)
    if repo_root_text not in sys.path:
        sys.path.insert(0, repo_root_text)


class ExtractManufacturingParamsComponent(Component):
    display_name = "제조 파라미터 추출"
    description = "질문과 문맥을 바탕으로 날짜, 공정, 제품 같은 조회 파라미터를 추출합니다."
    documentation = "https://docs.langflow.org/components-custom-components"
    icon = "Filter"
    name = "extract_manufacturing_params"

    inputs = [DataInput(name="state", display_name="State", info="초기 state 또는 직전 단계 state")]
    outputs = [Output(name="state_with_params", display_name="파라미터 포함 State", method="extract_params")]

    def extract_params(self):
        _ensure_repo_root()
        from langflow_version.component_base import make_data, read_data_payload
        from manufacturing_agent.services.parameter_service import resolve_required_params
        from manufacturing_agent.services.request_context import build_recent_chat_text, get_current_table_columns

        payload = read_data_payload(getattr(self, "state", None))
        state = payload.get("state") if isinstance(payload.get("state"), dict) else payload
        chat_history = state.get("chat_history", [])
        context = state.get("context", {})
        current_data = state.get("current_data")

        extracted_params = resolve_required_params(
            user_input=state.get("user_input", ""),
            chat_history_text=build_recent_chat_text(chat_history),
            current_data_columns=get_current_table_columns(current_data),
            context=context,
        )
        updated_state = {**state, "extracted_params": extracted_params}
        self.status = "파라미터 추출 완료"
        return make_data({"state": updated_state})
