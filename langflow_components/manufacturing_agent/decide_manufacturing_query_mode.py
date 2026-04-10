"""Langflow custom component: Decide Manufacturing Query Mode."""

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


class DecideManufacturingQueryModeComponent(Component):
    display_name = "질의 모드 판단"
    description = "현재 질문이 새 조회인지, 현재 테이블을 활용한 후속 분석인지 결정합니다."
    documentation = "https://docs.langflow.org/components-custom-components"
    icon = "GitCompareArrows"
    name = "decide_manufacturing_query_mode"

    inputs = [DataInput(name="state", display_name="State", info="파라미터가 포함된 state")]
    outputs = [Output(name="state_with_mode", display_name="모드 포함 State", method="decide_mode")]

    def decide_mode(self):
        _ensure_repo_root()
        from langflow_version.component_base import make_data, read_data_payload
        from manufacturing_agent.services.query_mode import choose_query_mode

        payload = read_data_payload(getattr(self, "state", None))
        state = payload.get("state") if isinstance(payload.get("state"), dict) else payload
        query_mode = choose_query_mode(
            state.get("user_input", ""),
            state.get("current_data"),
            state.get("extracted_params", {}),
        )
        updated_state = {**state, "query_mode": query_mode}
        self.status = f"질의 모드 판단 완료: {query_mode}"
        return make_data({"state": updated_state})
