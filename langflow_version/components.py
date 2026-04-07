"""제조 에이전트를 Langflow 컴포넌트 형태로 감싼 클래스 모음."""

from __future__ import annotations

from typing import Any, Dict

from .component_base import Component, DataInput, MessageTextInput, MultilineInput, Output, make_data, read_data_payload
from .workflow import (
    build_initial_state,
    finish_step,
    plan_retrieval_step,
    resolve_request_step,
    run_langflow_workflow,
    run_next_branch,
)


def _state_from_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Langflow Data 객체 안에 들어 있는 실제 state 딕셔너리를 꺼낸다."""

    state = payload.get("state")
    return state if isinstance(state, dict) else payload


class ManufacturingStateComponent(Component):
    display_name = "제조 State 입력"
    description = "제조 에이전트가 공통으로 사용하는 상태 딕셔너리를 만든다."
    documentation = "https://docs.langflow.org/components-custom-components"
    icon = "Package"
    name = "manufacturing_state_input"

    inputs = [
        MessageTextInput(name="user_input", display_name="사용자 질문", info="자연어 제조 질의"),
        MultilineInput(name="chat_history", display_name="대화 이력 JSON", info="선택 사항: 대화 목록 JSON"),
        MultilineInput(name="context", display_name="컨텍스트 JSON", info="선택 사항: 상속할 필터 딕셔너리"),
        MultilineInput(name="current_data", display_name="현재 데이터 JSON", info="선택 사항: 현재 결과/테이블 payload"),
    ]
    outputs = [Output(name="state", display_name="State", method="build_state")]

    def build_state(self):
        state = build_initial_state(
            user_input=getattr(self, "user_input", ""),
            chat_history=getattr(self, "chat_history", None),
            context=getattr(self, "context", None),
            current_data=getattr(self, "current_data", None),
        )
        self.status = "초기 상태 생성 완료"
        return make_data({"state": state})


class ResolveRequestComponent(Component):
    display_name = "질문 해석"
    description = "필터를 추출하고 새 조회인지 후속 분석인지 판단한다."
    documentation = "https://docs.langflow.org/components-custom-components"
    icon = "Route"
    name = "resolve_manufacturing_request"

    inputs = [DataInput(name="state", display_name="State", info="이전 컴포넌트에서 만든 상태")]
    outputs = [Output(name="state", display_name="해석된 State", method="resolve_state")]

    def resolve_state(self):
        payload = read_data_payload(getattr(self, "state", None))
        state = resolve_request_step(_state_from_payload(payload))
        self.status = f"질문 해석 완료: mode={state.get('query_mode', 'unknown')}"
        return make_data({"state": state})


class PlanRetrievalComponent(Component):
    display_name = "조회 계획"
    description = "질문에 필요한 원천 데이터셋과 조회 job 을 만든다."
    documentation = "https://docs.langflow.org/components-custom-components"
    icon = "Database"
    name = "plan_manufacturing_retrieval"

    inputs = [DataInput(name="state", display_name="State", info="해석 단계가 끝난 상태")]
    outputs = [Output(name="state", display_name="계획된 State", method="plan_state")]

    def plan_state(self):
        payload = read_data_payload(getattr(self, "state", None))
        state = plan_retrieval_step(_state_from_payload(payload))
        planned_jobs = len(state.get("retrieval_jobs", []))
        self.status = f"조회 계획 완료: {planned_jobs}개 job"
        return make_data({"state": state})


class RunWorkflowBranchComponent(Component):
    display_name = "다음 분기 실행"
    description = "현재 상태를 보고 필요한 다음 흐름 하나를 실행한다."
    documentation = "https://docs.langflow.org/components-custom-components"
    icon = "GitBranch"
    name = "run_manufacturing_branch"

    inputs = [DataInput(name="state", display_name="State", info="질문 해석 또는 조회 계획 이후 상태")]
    outputs = [Output(name="state", display_name="갱신된 State", method="run_branch")]

    def run_branch(self):
        payload = read_data_payload(getattr(self, "state", None))
        state = run_next_branch(_state_from_payload(payload))
        has_result = bool(state.get("result"))
        self.status = "분기 실행 완료" if has_result else "분기 실행 완료, 다음 단계 대기"
        return make_data({"state": state})


class FinishManufacturingResultComponent(Component):
    display_name = "결과 마무리"
    description = "최종 상태를 정리하고 결과 payload 를 꺼낸다."
    documentation = "https://docs.langflow.org/components-custom-components"
    icon = "CheckCheck"
    name = "finish_manufacturing_result"

    inputs = [DataInput(name="state", display_name="State", info="Run Manufacturing Branch 결과")]
    outputs = [
        Output(name="state", display_name="완료된 State", method="finish_state", group_outputs=True),
        Output(name="result", display_name="Result", method="result_data", group_outputs=True),
    ]

    def finish_state(self):
        payload = read_data_payload(getattr(self, "state", None))
        state = finish_step(_state_from_payload(payload))
        self.status = "최종 결과 정리 완료"
        return make_data({"state": state})

    def result_data(self):
        payload = read_data_payload(getattr(self, "state", None))
        state = finish_step(_state_from_payload(payload))
        return make_data(state.get("result", {}))


class ManufacturingAgentComponent(Component):
    display_name = "제조 에이전트"
    description = "제조 에이전트 전체 흐름을 하나의 Langflow 컴포넌트로 실행한다."
    documentation = "https://docs.langflow.org/components-custom-components"
    icon = "Bot"
    name = "manufacturing_agent_component"

    inputs = [
        MessageTextInput(name="user_input", display_name="사용자 질문", info="자연어 제조 질의"),
        MultilineInput(name="chat_history", display_name="대화 이력 JSON", info="선택 사항: 대화 목록 JSON"),
        MultilineInput(name="context", display_name="컨텍스트 JSON", info="선택 사항: 상속할 필터 딕셔너리"),
        MultilineInput(name="current_data", display_name="현재 데이터 JSON", info="선택 사항: 현재 결과/테이블 payload"),
    ]
    outputs = [Output(name="result", display_name="Result", method="run_component")]

    def run_component(self):
        result = run_langflow_workflow(
            user_input=getattr(self, "user_input", ""),
            chat_history=getattr(self, "chat_history", None),
            context=getattr(self, "context", None),
            current_data=getattr(self, "current_data", None),
        )
        self.status = f"전체 워크플로우 실행 완료: success={bool(result.get('tool_results'))}"
        return make_data(result)
