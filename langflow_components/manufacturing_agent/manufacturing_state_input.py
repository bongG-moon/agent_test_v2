"""Langflow custom component: Manufacturing State Input."""

from __future__ import annotations

import sys
from pathlib import Path

from lfx.custom.custom_component.component import Component
from lfx.io import MessageTextInput, MultilineInput, Output


def _ensure_repo_root() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    repo_root_text = str(repo_root)
    if repo_root_text not in sys.path:
        sys.path.insert(0, repo_root_text)


class ManufacturingStateComponent(Component):
    display_name = "제조 State 입력"
    description = "제조 에이전트가 사용할 공통 state 딕셔너리를 만듭니다."
    documentation = "https://docs.langflow.org/components-custom-components"
    icon = "Package"
    name = "manufacturing_state_input"

    inputs = [
        MessageTextInput(name="user_input", display_name="사용자 질문", info="자연어 제조 질의"),
        MultilineInput(name="chat_history", display_name="대화 이력 JSON", info="선택 사항: 대화 목록 JSON"),
        MultilineInput(name="context", display_name="컨텍스트 JSON", info="선택 사항: 누적 필터 딕셔너리"),
        MultilineInput(name="current_data", display_name="현재 데이터 JSON", info="선택 사항: 현재 결과/테이블 payload"),
    ]
    outputs = [Output(name="initial_state", display_name="State", method="build_state")]

    def build_state(self):
        _ensure_repo_root()
        from langflow_version.component_base import make_data
        from langflow_version.workflow import build_initial_state

        state = build_initial_state(
            user_input=getattr(self, "user_input", ""),
            chat_history=getattr(self, "chat_history", None),
            context=getattr(self, "context", None),
            current_data=getattr(self, "current_data", None),
        )
        self.status = "초기 state 생성 완료"
        return make_data({"state": state})
