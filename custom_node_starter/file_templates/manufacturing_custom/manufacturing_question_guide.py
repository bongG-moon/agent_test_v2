"""파일 기반 커스텀 노드 예시: 제조 질문 가이드."""

from __future__ import annotations

import re

from lfx.custom.custom_component.component import Component
from lfx.io import MessageTextInput, Output
from lfx.schema import Data


class ManufacturingQuestionGuideComponent(Component):
    display_name = "Manufacturing Question Guide"
    description = "제조 질문에서 빠진 요소를 찾아 더 좋은 질문 예시를 추천하는 파일 기반 예시 노드입니다."
    documentation = "https://docs.langflow.org/components-custom-components"
    icon = "MessageSquareQuote"
    name = "manufacturing_question_guide"

    inputs = [
        MessageTextInput(
            name="user_question",
            display_name="사용자 질문",
            info="애매하거나 짧은 제조 질문을 넣어보세요.",
        )
    ]

    outputs = [
        Output(
            name="guided_question",
            display_name="질문 가이드",
            method="guide_question",
        )
    ]

    def guide_question(self) -> Data:
        question = str(getattr(self, "user_question", "") or "").strip()
        lowered = question.lower()

        has_date = any(token in question for token in ["오늘", "어제"]) or any(
            token in lowered for token in ["today", "yesterday"]
        ) or bool(re.search(r"\b20\d{6}\b", question))

        has_process = any(token in lowered for token in ["da", "wb", "fcb", "input"]) or any(
            token in question for token in ["공정", "투입"]
        )

        has_product = any(token in lowered for token in ["ddr5", "lpddr5", "hbm", "auto"]) or any(
            token in question for token in ["제품", "품목"]
        )

        metric_keywords = ["생산", "목표", "달성", "포화", "wip", "재공", "hold", "가동률"]
        has_metric = any(token in question.lower() for token in metric_keywords)

        group_keywords = ["mode별", "공정별", "라인별", "den별", "tech별", "by "]
        has_group = any(token in lowered for token in group_keywords)

        missing_items = []
        if not has_date:
            missing_items.append("날짜")
        if not has_process:
            missing_items.append("공정")
        if not has_product:
            missing_items.append("제품")
        if not has_metric:
            missing_items.append("보고 싶은 값")
        if not has_group:
            missing_items.append("기준")

        suggested_question = "오늘 DA공정에서 DDR5제품의 생산 달성율을 MODE별로 알려줘"
        if has_metric and "wip" in lowered:
            suggested_question = "오늘 WB공정에서 DDR5제품의 WIP를 공정별로 알려줘"
        elif has_metric and ("생산" in question or "production" in lowered):
            suggested_question = "오늘 DA공정에서 DDR5제품의 생산량을 공정별로 알려줘"

        result = {
            "original_question": question,
            "missing_items": missing_items,
            "guide": "질문은 날짜 + 공정 + 제품/조건 + 보고 싶은 값 + 기준 형태로 적으면 가장 안정적으로 동작합니다.",
            "suggested_question": suggested_question,
        }
        self.status = "질문 가이드 생성 완료"
        return Data(data=result)
