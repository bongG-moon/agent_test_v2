"""조회 직후 컬럼명을 내부 표준명으로 맞추는 유틸리티."""

from typing import Any, Dict, List

from ..domain.knowledge import DATASET_COLUMN_ALIAS_SPECS
from .filter_utils import normalize_text


def _normalize_column_key(value: Any) -> str:
    text = normalize_text(value)
    return text.replace("_", "").replace("-", "").replace("/", "").replace(" ", "")


def build_column_rename_map(rows: List[Dict[str, Any]], dataset_key: str) -> Dict[str, str]:
    """실제 데이터 컬럼명과 내부 표준 컬럼명 사이의 rename 규칙을 만든다."""
    if not rows:
        return {}

    first_row = rows[0]
    if not isinstance(first_row, dict):
        return {}

    alias_spec = DATASET_COLUMN_ALIAS_SPECS.get(dataset_key, {})
    if not alias_spec:
        return {}

    actual_columns = list(first_row.keys())
    normalized_actual_map = {_normalize_column_key(column): column for column in actual_columns}
    rename_map: Dict[str, str] = {}

    for canonical_column, aliases in alias_spec.items():
        if canonical_column in actual_columns:
            continue

        for alias in aliases:
            matched_column = normalized_actual_map.get(_normalize_column_key(alias))
            if matched_column and matched_column not in rename_map:
                rename_map[matched_column] = canonical_column
                break

    return rename_map


def _rename_row_columns(row: Dict[str, Any], rename_map: Dict[str, str]) -> Dict[str, Any]:
    renamed_row: Dict[str, Any] = {}
    for column, value in row.items():
        renamed_row[rename_map.get(column, column)] = value
    return renamed_row


def normalize_dataset_result_columns(result: Dict[str, Any], dataset_key: str) -> Dict[str, Any]:
    """조회 결과의 컬럼명을 표준명으로 바꿔 뒤쪽 분석 코드가 같은 이름을 보게 한다."""
    if not isinstance(result, dict):
        return result

    rows = result.get("data")
    if not isinstance(rows, list) or not rows:
        return result

    rename_map = build_column_rename_map(rows, dataset_key)
    if not rename_map:
        return result

    normalized_rows = [
        _rename_row_columns(row, rename_map) if isinstance(row, dict) else row
        for row in rows
    ]

    normalized_result = dict(result)
    normalized_result["data"] = normalized_rows
    normalized_result["column_rename_map"] = rename_map
    return normalized_result
