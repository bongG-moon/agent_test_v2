"""Langflow custom component: Resolve Manufacturing Request."""

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


class ResolveRequestComponent(Component):
    display_name = "질문 해석"
    description = "필터를 추출하고 새 조회인지 후속 분석인지 판단합니다."
    documentation = "https://docs.langflow.org/components-custom-components"
    icon = "Route"
    name = "resolve_manufacturing_request"

    inputs = [DataInput(name="state", display_name="State", info="이전 컴포넌트에서 만든 state")]
    outputs = [Output(name="resolved_state", display_name="해석된 State", method="resolve_state")]

    def resolve_state(self):
        _ensure_repo_root()
        from langflow_version.component_base import make_data, read_data_payload
        from langflow_version.workflow import resolve_request_step

        payload = read_data_payload(getattr(self, "state", None))
        state = payload.get("state") if isinstance(payload.get("state"), dict) else payload
        resolved = resolve_request_step(state)
        self.status = f"질문 해석 완료: mode={resolved.get('query_mode', 'unknown')}"
        return make_data({"state": resolved})
