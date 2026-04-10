"""Langflow custom component: Finish Manufacturing Result."""

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


class FinishManufacturingResultComponent(Component):
    display_name = "결과 마무리"
    description = "최종 state를 정리하고 결과 payload를 꺼냅니다."
    documentation = "https://docs.langflow.org/components-custom-components"
    icon = "CheckCheck"
    name = "finish_manufacturing_result"

    inputs = [DataInput(name="state", display_name="State", info="Run Manufacturing Branch 결과")]
    outputs = [
        Output(name="finished_state", display_name="완료된 State", method="finish_state", group_outputs=True),
        Output(name="result", display_name="Result", method="result_data", group_outputs=True),
    ]

    def finish_state(self):
        _ensure_repo_root()
        from langflow_version.component_base import make_data, read_data_payload
        from langflow_version.workflow import finish_step

        payload = read_data_payload(getattr(self, "state", None))
        state = payload.get("state") if isinstance(payload.get("state"), dict) else payload
        finished = finish_step(state)
        self.status = "최종 결과 정리 완료"
        return make_data({"state": finished})

    def result_data(self):
        _ensure_repo_root()
        from langflow_version.component_base import make_data, read_data_payload
        from langflow_version.workflow import finish_step

        payload = read_data_payload(getattr(self, "state", None))
        state = payload.get("state") if isinstance(payload.get("state"), dict) else payload
        finished = finish_step(state)
        return make_data(finished.get("result", {}))
