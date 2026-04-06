"""High-level workflow helpers used by graph nodes.

These functions compose lower-level services such as retrieval planning,
merging, and analysis. The graph nodes call into this module so the graph
itself stays small and readable.
"""

from typing import Any, Dict, List

from ..analysis.engine import execute_analysis_query
from ..data.retrieval import build_current_datasets, dataset_requires_date, pick_retrieval_tools
from .merge_service import build_analysis_base_table, build_multi_dataset_overview
from .query_mode import needs_post_processing, prune_followup_params
from .request_context import (
    attach_result_metadata,
    attach_source_dataset_metadata,
    build_unknown_retrieval_message,
    collect_current_source_dataset_keys,
    get_current_table_columns,
    has_current_data,
)
from .response_service import generate_response
from .retrieval_planner import (
    build_missing_date_message,
    build_retrieval_jobs,
    execute_retrieval_jobs,
    plan_retrieval_request,
    review_retrieval_sufficiency,
    should_retry_retrieval_plan,
)


def mark_primary_result(tool_results: List[Dict[str, Any]], primary_index: int) -> List[Dict[str, Any]]:
    for index, result in enumerate(tool_results):
        result["display_expanded"] = index == primary_index
    return tool_results


def run_analysis_after_retrieval(
    user_input: str,
    chat_history: List[Dict[str, str]],
    source_results: List[Dict[str, Any]],
    extracted_params: Dict[str, Any],
    retrieval_plan: Dict[str, Any] | None = None,
) -> Dict[str, Any] | None:
    if not source_results:
        return None
    if not needs_post_processing(user_input, extracted_params, retrieval_plan):
        return None

    primary_source = source_results[-1]
    if not primary_source.get("success"):
        return None

    if retrieval_plan and retrieval_plan.get("needs_post_processing") and len(source_results) == 1:
        sufficiency_review = review_retrieval_sufficiency(user_input, source_results, retrieval_plan)
        if not sufficiency_review.get("is_sufficient", True):
            existing_keys = [str(result.get("dataset_key", "")) for result in source_results if result.get("dataset_key")]
            retry_keys = list(dict.fromkeys([*existing_keys, *sufficiency_review.get("missing_dataset_keys", [])]))
            if retry_keys and set(retry_keys) != set(existing_keys):
                retry_jobs = build_retrieval_jobs(user_input, extracted_params, retry_keys)
                return run_multi_retrieval_jobs(
                    user_input=user_input,
                    chat_history=chat_history,
                    current_data=None,
                    jobs=retry_jobs,
                    retrieval_plan=retrieval_plan,
                )

    analysis_result = execute_analysis_query(
        query_text=user_input,
        data=primary_source.get("data", []),
        source_tool_name=primary_source.get("tool_name", ""),
    )
    analysis_result = attach_result_metadata(analysis_result, extracted_params, primary_source.get("tool_name", ""))

    if should_retry_retrieval_plan(retrieval_plan, source_results, analysis_result):
        retry_plan = plan_retrieval_request(
            user_input,
            chat_history,
            primary_source,
            retry_context={
                "selected_dataset_keys": [str(result.get("dataset_key", "")) for result in source_results if result.get("dataset_key")],
                "available_columns": get_current_table_columns(primary_source),
                "analysis_outcome": str(analysis_result.get("analysis_logic", "") or analysis_result.get("error_message", "")),
                "analysis_goal": str(retrieval_plan.get("analysis_goal", "")) if retrieval_plan else "",
            },
        )
        retry_keys = retry_plan.get("dataset_keys") or []
        existing_keys = [str(result.get("dataset_key", "")) for result in source_results if result.get("dataset_key")]
        if retry_keys and set(retry_keys) != set(existing_keys):
            retry_jobs = build_retrieval_jobs(user_input, extracted_params, retry_keys)
            return run_multi_retrieval_jobs(
                user_input=user_input,
                chat_history=chat_history,
                current_data=None,
                jobs=retry_jobs,
                retrieval_plan=retry_plan,
            )

    if analysis_result.get("success"):
        analysis_result["current_datasets"] = build_current_datasets(source_results)
        attach_source_dataset_metadata(analysis_result, source_results)
        tool_results = mark_primary_result([*source_results, analysis_result], primary_index=len(source_results))
        return {
            "response": generate_response(user_input, analysis_result, chat_history),
            "tool_results": tool_results,
            "current_data": analysis_result,
            "extracted_params": extracted_params,
            "awaiting_analysis_choice": True,
        }

    source_summary = generate_response(user_input, primary_source, chat_history)
    response = (
        f"{analysis_result.get('error_message', '?꾩쿂由?遺꾩꽍???ㅽ뙣?덉뒿?덈떎.')}\n\n"
        f"???議고쉶???먮낯 寃곌낵瑜?癒쇱? 蹂댁뿬?쒕┰?덈떎.\n\n{source_summary}"
    )
    tool_results = mark_primary_result([*source_results, analysis_result], primary_index=len(source_results) - 1)
    return {
        "response": response,
        "tool_results": tool_results,
        "current_data": primary_source,
        "extracted_params": extracted_params,
        "awaiting_analysis_choice": True,
    }


def run_multi_retrieval_jobs(
    user_input: str,
    chat_history: List[Dict[str, str]],
    current_data: Dict[str, Any] | None,
    jobs: List[Dict[str, Any]],
    retrieval_plan: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    source_results = execute_retrieval_jobs(jobs)
    for result, job in zip(source_results, jobs):
        attach_result_metadata(result, job["params"], result.get("tool_name", ""))

    failed_results = [result for result in source_results if not result.get("success")]
    if failed_results:
        first_error = failed_results[0]
        return {
            "response": first_error.get("error_message", "蹂듭닔 議고쉶 以??ㅻ쪟媛 諛쒖깮?덉뒿?덈떎."),
            "tool_results": source_results,
            "current_data": current_data,
            "extracted_params": jobs[0]["params"] if jobs else {},
            "awaiting_analysis_choice": bool(has_current_data(current_data)),
        }

    current_datasets = build_current_datasets(source_results)

    if needs_post_processing(user_input, jobs[0]["params"] if jobs else {}, retrieval_plan):
        analysis_base = build_analysis_base_table(source_results, user_input)
        if not analysis_base.get("success"):
            overview_result = build_multi_dataset_overview(source_results)
            overview_result = attach_result_metadata(
                overview_result,
                jobs[0]["params"] if jobs else {},
                "+".join(job["dataset_key"] for job in jobs),
            )
            overview_result["current_datasets"] = current_datasets
            attach_source_dataset_metadata(overview_result, source_results)
            return {
                "response": analysis_base.get("error_message", "?щ윭 ?곗씠?곗뀑???④퍡 遺꾩꽍??怨듯넻 湲곗???李얠? 紐삵뻽?듬땲??"),
                "tool_results": mark_primary_result([*source_results, overview_result], primary_index=len(source_results)),
                "current_data": overview_result,
                "extracted_params": jobs[0]["params"] if jobs else {},
                "awaiting_analysis_choice": True,
            }

        analysis_result = execute_analysis_query(
            query_text=user_input,
            data=analysis_base.get("data", []),
            source_tool_name=analysis_base.get("tool_name", ""),
        )
        analysis_result = attach_result_metadata(
            analysis_result,
            jobs[0]["params"] if jobs else {},
            "+".join(job["dataset_key"] for job in jobs),
        )

        if analysis_result.get("success"):
            analysis_result["current_datasets"] = current_datasets
            attach_source_dataset_metadata(analysis_result, source_results)
            analysis_result["analysis_base_info"] = {
                "join_columns": analysis_base.get("join_columns", []),
                "source_tool_names": analysis_base.get("source_tool_names", []),
                "merge_notes": analysis_base.get("merge_notes", []),
                "requested_dimensions": analysis_base.get("requested_dimensions", []),
            }
            return {
                "response": generate_response(user_input, analysis_result, chat_history),
                "tool_results": mark_primary_result([*source_results, analysis_result], primary_index=len(source_results)),
                "current_data": analysis_result,
                "extracted_params": jobs[0]["params"] if jobs else {},
                "awaiting_analysis_choice": True,
            }

        overview_result = build_multi_dataset_overview(source_results)
        overview_result = attach_result_metadata(
            overview_result,
            jobs[0]["params"] if jobs else {},
            "+".join(job["dataset_key"] for job in jobs),
        )
        overview_result["current_datasets"] = current_datasets
        attach_source_dataset_metadata(overview_result, source_results)
        return {
            "response": analysis_result.get("error_message", "蹂듭닔 ?곗씠?곗뀑 遺꾩꽍???ㅽ뙣?덉뒿?덈떎."),
            "tool_results": mark_primary_result([*source_results, overview_result], primary_index=len(source_results)),
            "current_data": overview_result,
            "extracted_params": jobs[0]["params"] if jobs else {},
            "awaiting_analysis_choice": True,
        }

    overview_result = build_multi_dataset_overview(source_results)
    overview_result = attach_result_metadata(
        overview_result,
        jobs[0]["params"] if jobs else {},
        "+".join(job["dataset_key"] for job in jobs),
    )
    overview_result["current_datasets"] = current_datasets
    attach_source_dataset_metadata(overview_result, source_results)
    return {
        "response": generate_response(user_input, overview_result, chat_history),
        "tool_results": mark_primary_result([*source_results, overview_result], primary_index=len(source_results)),
        "current_data": overview_result,
        "extracted_params": jobs[0]["params"] if jobs else {},
        "awaiting_analysis_choice": True,
    }


def run_followup_analysis(
    user_input: str,
    chat_history: List[Dict[str, str]],
    current_data: Dict[str, Any],
    extracted_params: Dict[str, Any],
) -> Dict[str, Any]:
    cleaned_params = prune_followup_params(user_input, extracted_params)
    result = execute_analysis_query(
        query_text=user_input,
        data=current_data.get("data", []),
        source_tool_name=current_data.get("original_tool_name") or current_data.get("tool_name", ""),
    )
    result = attach_result_metadata(
        result,
        cleaned_params,
        current_data.get("original_tool_name") or current_data.get("tool_name", ""),
    )
    if result.get("success"):
        result["source_dataset_keys"] = collect_current_source_dataset_keys(current_data)
    tool_results = mark_primary_result([result], primary_index=0)
    return {
        "response": generate_response(user_input, result, chat_history) if result.get("success") else result.get("error_message", "遺꾩꽍???ㅽ뙣?덉뒿?덈떎."),
        "tool_results": tool_results,
        "current_data": result if result.get("success") else current_data,
        "extracted_params": cleaned_params,
        "awaiting_analysis_choice": bool(result.get("success")),
    }


def run_retrieval(
    user_input: str,
    chat_history: List[Dict[str, str]],
    current_data: Dict[str, Any] | None,
    extracted_params: Dict[str, Any],
) -> Dict[str, Any]:
    retrieval_plan = plan_retrieval_request(user_input, chat_history, current_data)
    retrieval_keys = retrieval_plan.get("dataset_keys") or pick_retrieval_tools(user_input)
    if not retrieval_keys:
        return {
            "response": build_unknown_retrieval_message(),
            "tool_results": [],
            "current_data": current_data,
            "extracted_params": extracted_params,
            "awaiting_analysis_choice": bool(has_current_data(current_data)),
        }

    jobs = build_retrieval_jobs(user_input, extracted_params, retrieval_keys)
    missing_date_jobs = [job for job in jobs if dataset_requires_date(job["dataset_key"]) and not job["params"].get("date")]
    if not jobs:
        return {
            "response": build_unknown_retrieval_message(),
            "tool_results": [],
            "current_data": current_data,
            "extracted_params": extracted_params,
            "awaiting_analysis_choice": bool(has_current_data(current_data)),
        }
    if missing_date_jobs:
        return {
            "response": build_missing_date_message([job["dataset_key"] for job in missing_date_jobs]),
            "tool_results": [],
            "current_data": current_data,
            "extracted_params": extracted_params,
            "awaiting_analysis_choice": bool(has_current_data(current_data)),
        }

    if len(jobs) > 1:
        return run_multi_retrieval_jobs(user_input, chat_history, current_data, jobs, retrieval_plan)

    single_job = jobs[0]
    result = execute_retrieval_jobs([single_job])[0]
    result = attach_result_metadata(result, single_job["params"], result.get("tool_name", ""))

    if result.get("success"):
        post_processed = run_analysis_after_retrieval(
            user_input=user_input,
            chat_history=chat_history,
            source_results=[result],
            extracted_params=single_job["params"],
            retrieval_plan=retrieval_plan,
        )
        if post_processed is not None:
            return post_processed

    tool_results = mark_primary_result([result], primary_index=0)
    return {
        "response": generate_response(user_input, result, chat_history) if result.get("success") else result.get("error_message", "議고쉶???ㅽ뙣?덉뒿?덈떎."),
        "tool_results": tool_results,
        "current_data": result if result.get("success") else current_data,
        "extracted_params": single_job["params"],
        "awaiting_analysis_choice": bool(result.get("success")),
    }
