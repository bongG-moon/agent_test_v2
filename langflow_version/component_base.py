"""Langflow 커스텀 컴포넌트를 위한 작은 호환 레이어.

이 저장소의 테스트는 Langflow 가 설치되지 않은 환경에서도 돌아가야 한다.
실제 Langflow 환경에서는 공식 클래스를 우선 사용하고,
로컬 테스트 환경에서는 이 프로젝트가 쓰는 최소한의 속성만 가진 대체 객체를 제공한다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


def _build_simple_data(payload: Dict[str, Any], text: str | None = None):
    @dataclass
    class SimpleData:
        data: Dict[str, Any]
        text: str | None = None

    return SimpleData(data=payload, text=text)


try:  # Langflow 1.7+ style
    from lfx.custom.custom_component.component import Component
    from lfx.io import DataInput, MessageTextInput, MultilineInput, Output
    from lfx.schema import Data
except Exception:  # pragma: no cover - fallback branch depends on environment
    try:  # Older compatible import path
        from langflow.custom import Component
        from langflow.io import DataInput, MessageTextInput, MultilineInput, Output
        from langflow.schema import Data
    except Exception:  # Local test fallback
        class Component:
            display_name = ""
            description = ""
            documentation = ""
            icon = ""
            name = ""
            inputs = []
            outputs = []
            status = ""

        @dataclass
        class _Input:
            name: str
            display_name: str
            info: str = ""
            value: Any = None
            tool_mode: bool = False

        @dataclass
        class Output:
            name: str
            display_name: str
            method: str
            group_outputs: bool = False

        def MessageTextInput(**kwargs):
            return _Input(**kwargs)

        def MultilineInput(**kwargs):
            return _Input(**kwargs)

        def DataInput(**kwargs):
            return _Input(**kwargs)

        class Data:  # pragma: no cover - only used without Langflow
            def __init__(self, data: Dict[str, Any] | None = None, text: str | None = None):
                self.data = data or {}
                self.text = text


def make_data(payload: Dict[str, Any], text: str | None = None):
    """실환경과 로컬 테스트 환경 모두에서 Data 비슷한 객체를 돌려준다."""

    try:
        return Data(data=payload, text=text)
    except TypeError:
        try:
            return Data(payload)
        except Exception:
            return _build_simple_data(payload, text=text)


def read_data_payload(value: Any) -> Dict[str, Any]:
    """Langflow Data, 일반 dict, None 값을 모두 일반 딕셔너리로 맞춘다."""

    if value is None:
        return {}
    if isinstance(value, dict):
        return value

    data = getattr(value, "data", None)
    if isinstance(data, dict):
        return data

    if hasattr(value, "dict"):
        try:
            result = value.dict()
            if isinstance(result, dict):
                return result
        except Exception:
            return {}
    return {}
