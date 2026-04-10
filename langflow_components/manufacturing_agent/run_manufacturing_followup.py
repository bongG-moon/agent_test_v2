"""Langflow custom component: Run Manufacturing Followup."""

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


class RunManufacturingFollowupComponent(Component):
    display_name = "후속 분석 실행"
    description = "현재 테이블을 재사용하는 후속 분석 흐름만 따로 실행합니다."
    documentation = "https://docs.langflow.org/components-custom-components"
    icon = "RefreshCw"
    name = "run_manufacturing_followup"

    inputs = [DataInput(name="state", display_name="State", info="current_data와 extracted_params가 포함된 state")]
    outputs = [Output(name="followup_state", display_name="후속 분석 결과 State", method="run_followup")]

    def run_followup(self):
        _ensure_repo_root()
        from langflow_version.component_base import make_data, read_data_payload
        from manufacturing_agent.services.runtime_service import run_followup_analysis

        payload = read_data_payload(getattr(self, "state", None))
        state = payload.get("state") if isinstance(payload.get("state"), dict) else payload
        result = run_followup_analysis(
            user_input=state.get("user_input", ""),
            chat_history=state.get("chat_history", []),
            current_data=state.get("current_data", {}),
            extracted_params=state.get("extracted_params", {}),
        )
        updated_state = {**state, "result": result}
        self.status = "후속 분석 실행 완료"
        return make_data({"state": updated_state})
