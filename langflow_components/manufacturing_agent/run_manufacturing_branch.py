"""Langflow custom component: Run Manufacturing Branch."""

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


class RunWorkflowBranchComponent(Component):
    display_name = "다음 분기 실행"
    description = "현재 state를 보고 필요한 다음 실행 흐름 하나를 처리합니다."
    documentation = "https://docs.langflow.org/components-custom-components"
    icon = "GitBranch"
    name = "run_manufacturing_branch"

    inputs = [DataInput(name="state", display_name="State", info="질문 해석 또는 조회 계획 이후 state")]
    outputs = [Output(name="updated_state", display_name="갱신된 State", method="run_branch")]

    def run_branch(self):
        _ensure_repo_root()
        from langflow_version.component_base import make_data, read_data_payload
        from langflow_version.workflow import run_next_branch

        payload = read_data_payload(getattr(self, "state", None))
        state = payload.get("state") if isinstance(payload.get("state"), dict) else payload
        updated = run_next_branch(state)
        has_result = bool(updated.get("result"))
        self.status = "분기 실행 완료" if has_result else "분기 실행 완료, 다음 단계 대기"
        return make_data({"state": updated})
