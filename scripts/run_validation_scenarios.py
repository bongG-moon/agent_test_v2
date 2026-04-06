from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path


# Allow running this script directly from the repo root without extra setup.
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from manufacturing_agent import agent
from manufacturing_agent.domain import registry as domain_registry


DOMAIN_TEXTS = [
    (
        "생산포화율은 production 테이블의 production 값을 "
        "wip 테이블의 재공수량으로 나눈 비율이야. "
        "결과 컬럼 이름은 production_saturation_rate 로 두고, "
        "production 과 wip 는 같은 WORK_DT, OPER_NAME, MODE, DEN, TECH, LEAD, FAMILY 기준으로 맞춰서 계산해줘."
    ),
    (
        "홀드 부하지수는 hold 테이블의 hold_qty 와 production 테이블의 production 을 나눈 값이야. "
        "결과 컬럼 이름은 hold_load_index 로 두고, "
        "hold 와 production 은 같은 WORK_DT, OPER_NAME, MODE, DEN, TECH, LEAD, FAMILY 기준으로 맞춰서 계산해줘."
    ),
    (
        "설비재공 복합이상여부는 equipment 테이블의 가동률과 "
        "wip 테이블의 재공수량을 같이 보고 판단해줘. "
        "가동률이 85 미만이면서 재공수량이 1800 이상이면 이상, 아니면 정상으로 판단해. "
        "결과 컬럼 이름은 equipment_wip_abnormal_flag 로 두고, "
        "equipment 와 wip 는 같은 WORK_DT, OPER_NAME, MODE, DEN, TECH, LEAD, FAMILY 기준으로 맞춰서 계산해줘."
    ),
]


QUESTIONS = [
    "오늘 DA공정에서 DDR5제품 생산량 알려줘",
    "어제 DA공정에서 DDR5제품 생산 달성률 알려줘",
    "어제 일자 기준의 생산 달성율과 생산 포화율을 MODE/DEN/TECH/LEAD 그룹화해서 보여줘",
    "어제 일자 기준의 생산 달성율과 생산 포화율을 FAMILY/MODE/DEN/TECH/LEAD 그룹화해서 보여줘",
    "오늘 DA공정 설비재공 복합이상여부 알려줘",
    "오늘 DA공정에서 FAMILY별 생산량 알려줘",
    "오늘 HBM 제품 생산량과 재공 알려줘",
    "오늘 Auto향 제품 생산량 알려줘",
    "오늘 DA공정 홀드 부하지수 알려줘",
    "어제와 오늘 DA공정 생산량을 세부 공정별로 비교해줘",
]


def _configure_temp_registry() -> Path:
    base_dir = Path(tempfile.mkdtemp(prefix="langgraph_validation_"))
    entries_dir = base_dir / "entries"
    entries_dir.mkdir(parents=True, exist_ok=True)
    domain_registry.DOMAIN_REGISTRY_DIR = base_dir
    domain_registry.DOMAIN_REGISTRY_ENTRIES_DIR = entries_dir
    return base_dir


def _register_validation_rules() -> list[dict]:
    return [domain_registry.register_domain_submission(text) for text in DOMAIN_TEXTS]


def _summarize_result(question: str, result: dict) -> dict:
    tool_results = result.get("tool_results", [])
    dataset_keys = [item.get("dataset_key") for item in tool_results if item.get("dataset_key")]
    current_data = result.get("current_data", {}) or {}
    data_rows = current_data.get("data", []) if isinstance(current_data.get("data", []), list) else []
    columns = list(data_rows[0].keys()) if data_rows and isinstance(data_rows[0], dict) else []
    analysis_base_info = current_data.get("analysis_base_info", {}) if isinstance(current_data, dict) else {}
    response = str(result.get("response", "") or "")

    return {
        "question": question,
        "current_tool": current_data.get("tool_name"),
        "dataset_keys": dataset_keys,
        "row_count": len(data_rows),
        "columns_preview": columns[:12],
        "join_columns": analysis_base_info.get("join_columns", []),
        "merge_notes": analysis_base_info.get("merge_notes", []),
        "response_preview": response[:300],
    }


def main() -> None:
    _configure_temp_registry()
    registrations = _register_validation_rules()

    print("=== Registered Domain Rules ===")
    for item in registrations:
        payload = item.get("payload", {})
        print(
            json.dumps(
                {
                    "saved": item.get("saved"),
                    "title": payload.get("title"),
                    "analysis_rules": len(payload.get("analysis_rules", [])),
                    "join_rules": len(payload.get("join_rules", [])),
                    "issues": item.get("issues", []),
                },
                ensure_ascii=False,
            )
        )

    print("\n=== Question Validation Results ===")
    for index, question in enumerate(QUESTIONS, start=1):
        try:
            result = agent.run_agent(question, [], {}, None)
            summary = _summarize_result(question, result)
        except Exception as exc:  # pragma: no cover - manual validation script
            summary = {
                "question": question,
                "error": f"{type(exc).__name__}: {exc}",
            }
        print(f"\n[{index}]")
        print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
