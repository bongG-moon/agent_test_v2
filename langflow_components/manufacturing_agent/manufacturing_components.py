"""LANGFLOW_COMPONENTS_PATH 아래에서 바로 로드할 수 있는 제조 에이전트 컴포넌트 모듈.

이 파일은 Langflow가 커스텀 컴포넌트를 검색할 때 직접 읽는 진입점이다.
실제 구현은 `langflow_version.components`에 두고,
여기서는 저장소 루트를 import path에 추가한 뒤 컴포넌트 클래스를 다시 노출한다.
"""

from __future__ import annotations

import sys
from pathlib import Path


def _ensure_repo_root_on_sys_path() -> Path:
    """현재 파일 기준으로 저장소 루트를 찾아 import 가능 경로에 추가한다."""

    repo_root = Path(__file__).resolve().parents[2]
    repo_root_text = str(repo_root)
    if repo_root_text not in sys.path:
        sys.path.insert(0, repo_root_text)
    return repo_root


REPO_ROOT = _ensure_repo_root_on_sys_path()

from langflow_version.components import (  # noqa: E402
    FinishManufacturingResultComponent,
    ManufacturingAgentComponent,
    ManufacturingStateComponent,
    PlanRetrievalComponent,
    ResolveRequestComponent,
    RunWorkflowBranchComponent,
)


__all__ = [
    "ManufacturingStateComponent",
    "ResolveRequestComponent",
    "PlanRetrievalComponent",
    "RunWorkflowBranchComponent",
    "FinishManufacturingResultComponent",
    "ManufacturingAgentComponent",
]
