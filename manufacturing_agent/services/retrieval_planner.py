"""원천 데이터 조회 계획을 세우는 서비스."""

from datetime import datetime, timedelta
from typing import Any, Dict, List

from langchain_core.messages import HumanMessage, SystemMessage

from ..data.retrieval import (
    DATASET_REGISTRY,
    dataset_requires_date,
    execute_retrieval_tools,
    pick_retrieval_tools,
)
from ..domain.registry import build_registered_domain_prompt, match_registered_analysis_rules
from ..shared.config import SYSTEM_PROMPT
from ..shared.filter_utils import normalize_text
from .query_mode import mentions_grouping_expression
from .request_context import (
    POST_PROCESSING_KEYWORDS,
    build_dataset_catalog_text,
    build_recent_chat_text,
    extract_text_from_response,
    get_current_table_columns,
    get_dataset_labels_for_message,
    get_llm_for_task,
    parse_json_block,
)


def plan_retrieval_request(
    user_input: str,
    chat_history: List[Dict[str, str]],
    current_data: Dict[str, Any] | None,
    retry_context: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """질문에 필요한 원천 데이터셋을 고른다.

    이 함수는 "무슨 데이터를 가져와야 최종 답을 만들 수 있는가?" 에 집중한다.
    단순 키워드 매칭만 쓰지 않고, LLM 계획 + 규칙 기반 보강을 함께 사용한다.
    """

    current_columns = get_current_table_columns(current_data)
    retry_section = ""
    if retry_context:
        retry_section = f"""

Previous selection review:
- already selected datasets: {", ".join(retry_context.get("selected_dataset_keys", [])) or "(none)"}
- currently available columns: {", ".join(retry_context.get("available_columns", [])) or "(none)"}
- current analysis outcome: {retry_context.get("analysis_outcome", "")}
- current analysis goal: {retry_context.get("analysis_goal", "")}

If the previous selection was not enough to answer the user's real question,
add the missing base datasets this time.
"""
    prompt = f"""You are planning which registered datasets should be retrieved for a manufacturing assistant.
Return JSON only.

Rules:
- Choose only dataset keys from the registered dataset list.
- If the user asks for a derived metric or comparison, include every base dataset needed for that final answer.
- Set `needs_post_processing` to true when the final answer requires grouping, joining, comparing, ranking, or creating a derived column after retrieval.
- Do not invent dataset keys.

Registered dataset list:
{build_dataset_catalog_text()}

Custom domain registry:
{build_registered_domain_prompt()}

Recent chat:
{build_recent_chat_text(chat_history)}

Current data columns:
{", ".join(current_columns) if current_columns else "(none)"}

User question:
{user_input}
{retry_section}

Return only:
{{
  "dataset_keys": ["production"],
  "needs_post_processing": false,
  "analysis_goal": "short description"
}}"""

    try:
        llm = get_llm_for_task("retrieval_plan")
        response = llm.invoke([SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=prompt)])
        parsed = parse_json_block(extract_text_from_response(response.content))
    except Exception:
        parsed = {}

    dataset_keys = [key for key in parsed.get("dataset_keys", []) if key in DATASET_REGISTRY]
    rule_based_keys = [key for key in pick_retrieval_tools(user_input) if key in DATASET_REGISTRY]
    matched_rules = match_registered_analysis_rules(user_input)
    normalized_query = normalize_text(user_input)

    # 단순한 단일 조회 질문은 규칙 기반 결과를 우선 믿어도 충분하다.
    if (
        rule_based_keys
        and not matched_rules
        and len(rule_based_keys) == 1
        and len(dataset_keys) <= 1
        and not parsed.get("needs_post_processing", False)
    ):
        dataset_keys = list(rule_based_keys)
    elif len(rule_based_keys) >= 2 and len(dataset_keys) <= 1:
        dataset_keys = list(dict.fromkeys([*dataset_keys, *rule_based_keys]))

    for rule in matched_rules:
        for dataset_key in rule.get("required_datasets", []):
            if dataset_key in DATASET_REGISTRY and dataset_key not in dataset_keys:
                dataset_keys.append(dataset_key)

    simple_single_dataset_request = (
        len(dataset_keys) == 1
        and not matched_rules
        and not mentions_grouping_expression(user_input)
        and not any(token in normalized_query for token in POST_PROCESSING_KEYWORDS)
    )

    return {
        "dataset_keys": dataset_keys,
        "needs_post_processing": False
        if simple_single_dataset_request
        else bool(parsed.get("needs_post_processing", False) or matched_rules),
        "analysis_goal": str(parsed.get("analysis_goal", "")).strip()
        or ", ".join(str(rule.get("display_name") or rule.get("name")) for rule in matched_rules[:2]),
    }


def review_retrieval_sufficiency(
    user_input: str,
    source_results: List[Dict[str, Any]],
    retrieval_plan: Dict[str, Any] | None,
) -> Dict[str, Any]:
    """선택한 데이터셋만으로 진짜 답을 만들 수 있는지 재검토한다.

    예를 들어 처음에는 `production` 만 뽑았지만,
    실제 질문이 달성률이었다면 `target` 도 더 필요할 수 있다.
    """

    if not source_results:
        return {"is_sufficient": True, "missing_dataset_keys": [], "reason": ""}

    selected_dataset_keys = [
        str(result.get("dataset_key", ""))
        for result in source_results
        if result.get("dataset_key")
    ]
    available_columns = get_current_table_columns(source_results[-1])
    prompt = f"""You are reviewing whether the currently selected manufacturing datasets are sufficient.
Return JSON only.

Rules:
- Judge sufficiency based on the user's real question, not on what is already available.
- If the final answer needs a comparison, ratio, achievement rate, or multi-source calculation, make sure every raw dataset needed for that answer is selected.
- If the current selection is insufficient, list the missing dataset keys from the registered dataset list.
- Do not invent dataset keys.

Registered dataset list:
{build_dataset_catalog_text()}

User question:
{user_input}

Current retrieval plan:
{retrieval_plan}

Currently selected dataset keys:
{", ".join(selected_dataset_keys) if selected_dataset_keys else "(none)"}

Currently available columns:
{", ".join(available_columns) if available_columns else "(none)"}

Return only:
{{
  "is_sufficient": true,
  "missing_dataset_keys": [],
  "reason": "short explanation"
}}"""

    try:
        llm = get_llm_for_task("sufficiency_review")
        response = llm.invoke([SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=prompt)])
        parsed = parse_json_block(extract_text_from_response(response.content))
    except Exception:
        parsed = {}

    missing_dataset_keys = [key for key in parsed.get("missing_dataset_keys", []) if key in DATASET_REGISTRY]
    return {
        "is_sufficient": bool(parsed.get("is_sufficient", True)),
        "missing_dataset_keys": missing_dataset_keys,
        "reason": str(parsed.get("reason", "")).strip(),
    }


def build_missing_date_message(retrieval_keys: List[str]) -> str:
    """날짜가 빠졌을 때 사용자에게 보여줄 안내 문구를 만든다."""

    labels = get_dataset_labels_for_message([key for key in retrieval_keys if dataset_requires_date(key)])
    if labels:
        return (
            "이 질문은 날짜 기준이 필요한 조회입니다"
            f" ({', '.join(labels)}). "
            "예를 들어 오늘, 어제, 20260324 처럼 날짜를 함께 적어 주세요."
        )
    return "이 조회는 날짜 조건이 있어야 실행할 수 있습니다."


def extract_date_slices(user_input: str, default_date: str | None) -> List[Dict[str, str]]:
    """질문 안에서 날짜 범위를 추출해 retrieval job 단위로 나눈다."""

    normalized = normalize_text(user_input)
    slices: List[Dict[str, str]] = []
    now = datetime.now()

    if "어제" in normalized or "yesterday" in normalized:
        slices.append({"label": "어제", "date": (now - timedelta(days=1)).strftime("%Y%m%d")})
    if "오늘" in normalized or "today" in normalized:
        slices.append({"label": "오늘", "date": now.strftime("%Y%m%d")})

    import re

    for explicit_date in re.findall(r"\b(20\d{6})\b", str(user_input or "")):
        if explicit_date not in {item["date"] for item in slices}:
            slices.append({"label": explicit_date, "date": explicit_date})

    if not slices and default_date:
        slices.append({"label": default_date, "date": default_date})

    return slices


def build_retrieval_jobs(user_input: str, extracted_params: Dict[str, Any], retrieval_keys: List[str]) -> List[Dict[str, Any]]:
    """조회 계획을 실제 실행 단위(job) 리스트로 변환한다."""

    jobs: List[Dict[str, Any]] = []
    date_slices = extract_date_slices(user_input, extracted_params.get("date"))
    use_repeated_date_slices = len(retrieval_keys) == 1 and len(date_slices) > 1

    for dataset_key in retrieval_keys:
        if use_repeated_date_slices:
            for date_slice in date_slices:
                job_params = dict(extracted_params)
                job_params["date"] = date_slice["date"]
                jobs.append({"dataset_key": dataset_key, "params": job_params, "result_label": date_slice["label"]})
            continue

        job_params = dict(extracted_params)
        if len(date_slices) == 1:
            job_params["date"] = date_slices[0]["date"]
        jobs.append({"dataset_key": dataset_key, "params": job_params, "result_label": None})

    return jobs


def execute_retrieval_jobs(jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """job 리스트를 실제 조회 함수 실행으로 바꾼다."""

    import re

    results: List[Dict[str, Any]] = []
    repeated_dataset_keys = len({job["dataset_key"] for job in jobs}) != len(jobs)

    for index, job in enumerate(jobs, start=1):
        result = execute_retrieval_tools([job["dataset_key"]], job["params"])[0]
        result_label = job.get("result_label")
        if result_label:
            result["result_label"] = result_label
        if repeated_dataset_keys and result_label:
            result["dataset_key"] = f"{job['dataset_key']}__{result_label}"
            dataset_label = str(result.get("dataset_label", job["dataset_key"]))
            result["dataset_label"] = f"{dataset_label} ({result_label})"
        normalized = re.sub(r"\W+", "_", str(result.get("result_label") or result.get("dataset_label") or result.get("tool_name", ""))).strip("_")
        result["source_tag"] = normalized or f"source_{index}"
        results.append(result)

    return results


def should_retry_retrieval_plan(
    retrieval_plan: Dict[str, Any] | None,
    source_results: List[Dict[str, Any]],
    analysis_result: Dict[str, Any],
) -> bool:
    """초기 조회 계획이 부족해서 다시 계획을 세워야 하는지 판단한다."""

    if not retrieval_plan or not retrieval_plan.get("needs_post_processing"):
        return False
    if len(source_results) != 1:
        return False

    analysis_logic = str(analysis_result.get("analysis_logic", "")).strip()
    if analysis_logic == "minimal_fallback":
        return True

    if not analysis_result.get("success") and analysis_result.get("missing_columns"):
        return True

    return False
