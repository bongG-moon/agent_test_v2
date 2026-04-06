"""Small compatibility layer for Langflow custom components.

This module lets the repository import and test custom component files even
when Langflow is not installed locally. In a real Langflow environment the
official classes are imported first. Outside Langflow we provide lightweight
fallback objects with the same attribute names used by this project.
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
    """Return a Langflow Data-like object in both real and local test modes."""

    try:
        return Data(data=payload, text=text)
    except TypeError:
        try:
            return Data(payload)
        except Exception:
            return _build_simple_data(payload, text=text)


def read_data_payload(value: Any) -> Dict[str, Any]:
    """Normalize Langflow Data, dicts, or None into a plain dictionary."""

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
