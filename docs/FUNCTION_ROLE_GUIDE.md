# Function And Element Guide

이 문서는 주요 함수, 클래스, 상수 묶음이 어떤 용도로 존재하는지 설명합니다.

읽는 방법:

- 먼저 “실행 흐름 핵심 함수”를 읽습니다.
- 그 다음 “서비스 함수”, “도메인/데이터 함수”, “Langflow 함수”를 보면 전체 그림이 잡힙니다.
- `_` 로 시작하는 함수는 내부 helper 입니다. 대부분 “작은 책임 1개”를 위해 분리되어 있습니다.

## 1. 실행 흐름 핵심 함수

### [manufacturing_agent/agent.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/agent.py)
- `run_agent(user_input, chat_history=None, context=None, current_data=None)`
  - 용도: 외부에서 호출하는 단일 실행 함수
  - 입력: 사용자 질문, 대화 이력, 필터 context, 현재 테이블
  - 출력: 최종 결과 payload 딕셔너리
  - 사용 위치: Streamlit `app.py`, 다른 외부 호출 지점

### [manufacturing_agent/graph/builder.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/graph/builder.py)
- `get_agent_graph()`
  - 용도: LangGraph 노드를 연결한 실제 실행 그래프 생성
  - 출력: `graph.invoke()` 가능한 compiled graph

### [manufacturing_agent/graph/state.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/graph/state.py)
- `QueryMode`
  - 용도: 현재 요청이 `retrieval` 인지 `followup_transform` 인지 표시
- `AgentGraphState`
  - 용도: 노드 사이에 전달되는 상태 구조 정의
  - 핵심 필드: `user_input`, `current_data`, `extracted_params`, `retrieval_plan`, `retrieval_jobs`, `result`

### [manufacturing_agent/graph/routes.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/graph/routes.py)
- `route_after_resolve(state)`
  - 용도: 파라미터 추출 직후 follow-up analysis 로 갈지, retrieval planning 으로 갈지 결정
- `route_after_retrieval_plan(state)`
  - 용도: retrieval plan 이후 finish/single/multi 중 어디로 갈지 결정

## 2. 각 노드 함수

### [manufacturing_agent/graph/nodes/resolve_request.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/graph/nodes/resolve_request.py)
- `resolve_request_node(state)`
  - 역할: 질문 해석의 시작점
  - 내부에서 하는 일:
  - `resolve_required_params()` 호출
  - `choose_query_mode()` 호출
  - 결과로 `extracted_params`, `query_mode` 를 상태에 추가

### [manufacturing_agent/graph/nodes/plan_retrieval.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/graph/nodes/plan_retrieval.py)
- `plan_retrieval_node(state)`
  - 역할: 어떤 dataset 을 어떤 파라미터로 조회할지 결정
  - 내부에서 하는 일:
  - `plan_retrieval_request()` 로 dataset key 선택
  - `build_retrieval_jobs()` 로 실행 job 생성
  - 날짜 부족/미지원 질문이면 바로 사용자용 `result` 생성

### [manufacturing_agent/graph/nodes/retrieve_single.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/graph/nodes/retrieve_single.py)
- `single_retrieval_node(state)`
  - 역할: 단일 dataset 조회
  - 내부에서 하는 일:
  - `execute_retrieval_jobs()` 호출
  - 메타데이터 부착
  - 필요하면 `run_analysis_after_retrieval()` 로 후처리 분석 이어서 수행

### [manufacturing_agent/graph/nodes/retrieve_multi.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/graph/nodes/retrieve_multi.py)
- `multi_retrieval_node(state)`
  - 역할: 다중 dataset 또는 다중 날짜 조회
  - 내부에서 하는 일:
  - `run_multi_retrieval_jobs()` 로 전체 실행 위임

### [manufacturing_agent/graph/nodes/followup_analysis.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/graph/nodes/followup_analysis.py)
- `followup_analysis_node(state)`
  - 역할: 현재 테이블 기반 재분석
  - 내부에서 하는 일:
  - `current_data` 유무 점검
  - `run_followup_analysis()` 실행

### [manufacturing_agent/graph/nodes/finish.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/graph/nodes/finish.py)
- `finish_node(state)`
  - 역할: 마지막 정규화
  - 내부에서 하는 일:
  - `result` 보장
  - `execution_engine` 표기

## 3. 파라미터 추출 함수

### [manufacturing_agent/services/parameter_service.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/services/parameter_service.py)

- `resolve_required_params(user_input, chat_history_text, current_data_columns, context=None)`
  - 용도: 질문에서 조회 필터를 뽑아내는 메인 함수
  - 출력: `RequiredParams`

- `_get_llm_for_task(task)`
  - 용도: 태스크별 LLM 선택 래퍼

- `_extract_text_from_response(content)`
  - 용도: LLM 응답에서 순수 텍스트만 추출

- `_parse_json_block(text)`
  - 용도: LLM 응답 안의 JSON 블록만 안전하게 파싱

- `_inherit_from_context(extracted_params, context)`
  - 용도: 사용자가 다시 명시하지 않은 필터를 이전 context 에서 이어받기

- `_fallback_date(text)`
  - 용도: LLM이 날짜를 못 뽑았을 때 today/yesterday 를 직접 보정

- `_detect_oper_num(text)`
  - 용도: `OPER_NUM` 형태를 정규식으로 찾기

- `_detect_pkg_values(text, allowed_values)`
  - 용도: PKG_TYPE 값을 직접 탐지

- `_as_list`, `_dedupe`, `_merge_optional_lists`
  - 용도: 값 정규화와 중복 제거

- `_contains_alias(text, alias)`
  - 용도: 별칭 포함 여부를 느슨하게 판단

- `_canonicalize_group_values(raw_values, groups, literal_values=None)`
  - 용도: DA, WB 같은 그룹 표현을 실제 공정 리스트로 치환

- `_detect_group_values_from_text(text, groups, literal_values=None)`
  - 용도: 텍스트만 보고 그룹/리터럴 값을 탐지

- `_normalize_special_product_name(value)`
  - 용도: HBM/3DS, AUTO 같은 특수 제품군 키로 정규화

- `_apply_domain_overrides(extracted_params, user_input)`
  - 용도: 제조 도메인 규칙을 한 번에 적용
  - 실제로 process, mode, den, tech, pkg, product, line, mcp 를 확장합니다.

## 4. 질의 모드 판단 함수

### [manufacturing_agent/services/query_mode.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/services/query_mode.py)

- `has_explicit_date_reference(user_input)`
  - 용도: 날짜를 새로 명시했는지 판단

- `mentions_grouping_expression(user_input)`
  - 용도: group by, breakdown, 공정별 같은 집계 요구 표현 감지

- `needs_post_processing(user_input, extracted_params, retrieval_plan=None)`
  - 용도: 조회 후 추가 계산/집계가 필요한 질문인지 판단

- `looks_like_new_data_request(user_input)`
  - 용도: 새 raw dataset 조회가 필요한 표현인지 판단

- `prune_followup_params(user_input, extracted_params)`
  - 용도: follow-up analysis 에서 불필요한 retrieval 필터를 정리

- `choose_query_mode(user_input, current_data, extracted_params)`
  - 용도: retrieval vs followup_transform 최종 결정 함수

## 5. 요청 문맥 함수

### [manufacturing_agent/services/request_context.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/services/request_context.py)

- `build_recent_chat_text(chat_history)`
  - 용도: 최근 대화 이력을 LLM prompt 에 넣기 좋은 텍스트로 변환

- `get_current_table_columns(current_data)`
  - 용도: 현재 테이블 컬럼 목록 추출

- `has_current_data(current_data)`
  - 용도: 현재 결과가 재분석 가능한지 체크

- `raw_dataset_key(dataset_key)`
  - 용도: `production__today` 같은 키에서 base dataset key 만 추출

- `collect_applied_params(current_data)`
  - 용도: 현재 결과에 적용된 필터를 읽어오기

- `attach_result_metadata(result, extracted_params, original_tool_name)`
  - 용도: 결과 payload 에 필터, 원본 도구명, source metadata 부착

- `collect_current_source_dataset_keys(current_data)`
  - 용도: 현재 테이블이 어떤 원본 dataset 들에서 왔는지 추적

- `collect_requested_dataset_keys(retrieval_plan)`
  - 용도: 사용자가 요구한 dataset 후보 목록 정리

- `normalize_filter_value`, `user_explicitly_mentions_filter`, `has_explicit_filter_change`
  - 용도: 사용자가 필터를 바꿨는지 비교

- `build_current_data_profile(current_data)`
  - 용도: 현재 데이터의 컬럼/행/출처 요약 프로필 생성

- `attach_source_dataset_metadata(result, source_results)`
  - 용도: 후처리 결과에 원본 dataset 정보 부착

- `review_query_mode_with_llm(...)`
  - 용도: 필요 시 LLM으로 query mode 판단을 보조

- `build_unknown_retrieval_message()`
  - 용도: 어떤 dataset 도 고르지 못했을 때 사용자 메시지 생성

- `extract_text_from_response`, `parse_json_block`
  - 용도: request_context 계층 내부의 LLM 응답 파싱 보조

- `build_dataset_catalog_text()`, `get_dataset_labels_for_message()`
  - 용도: dataset 목록을 프롬프트/메시지용 텍스트로 바꾸기

## 6. 리트리벌 계획 함수

### [manufacturing_agent/services/retrieval_planner.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/services/retrieval_planner.py)

- `plan_retrieval_request(user_input, chat_history, current_data, retry_context=None)`
  - 용도: 어떤 raw dataset 이 필요한지 계획
  - 출력: `dataset_keys`, `needs_post_processing`, `analysis_goal`

- `review_retrieval_sufficiency(user_input, source_results, retrieval_plan)`
  - 용도: 선택된 dataset 으로 정말 최종 질문에 답할 수 있는지 재검토

- `build_missing_date_message(retrieval_keys)`
  - 용도: 날짜가 꼭 필요한 dataset 인데 날짜가 없을 때 안내 문구 생성

- `extract_date_slices(user_input, default_date)`
  - 용도: 오늘/어제/명시 날짜를 여러 slice 로 뽑기

- `build_retrieval_jobs(user_input, extracted_params, retrieval_keys)`
  - 용도: dataset key 와 파라미터를 실제 실행 단위 job 리스트로 변환

- `execute_retrieval_jobs(jobs)`
  - 용도: job 리스트를 실제 결과 리스트로 실행

- `should_retry_retrieval_plan(retrieval_plan, source_results, analysis_result)`
  - 용도: 조회 계획이 부족했던 경우 다시 planning 해야 하는지 판단

## 7. 멀티 데이터 병합 함수

### [manufacturing_agent/services/merge_service.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/services/merge_service.py)

중요 상수:

- `KNOWN_DIMENSION_COLUMNS`
  - 용도: join 후보로 우선 취급할 차원 컬럼 목록
- `DATE_COLUMNS`
  - 용도: 날짜 컬럼 집합
- `LIKELY_METRIC_COLUMNS`
  - 용도: 지표 컬럼으로 추정되는 이름 목록

주요 함수:

- `should_suffix_metrics(tool_results)`
  - 용도: 같은 이름 metric 충돌을 막기 위해 suffix 가 필요한지 판단

- `should_exclude_date_from_join(tool_results)`
  - 용도: 동일 dataset 의 날짜 비교일 때 날짜를 join key 에서 빼야 하는지 판단

- `is_probable_dimension_column(column_name)`
  - 용도: 해당 컬럼이 차원 컬럼인지 추정

- `resolve_requested_dimensions(user_input, frames)`
  - 용도: 사용자가 보고 싶어 하는 차원 컬럼 찾기

- `pick_join_columns(left_df, right_df, requested_dimensions, exclude_date)`
  - 용도: 두 테이블을 잇는 join key 후보 선택

- `classify_join_cardinality(left_df, right_df, join_columns)`
  - 용도: 1:1, 1:N, N:1, N:M 판정

- `refine_join_columns_for_cardinality(...)`
  - 용도: N:M 이 나오면 key 를 더 추가해 안전한 merge 로 바꿔보기

- `find_join_rule(left_dataset, right_dataset)`
  - 용도: 등록된 custom join rule 조회

- `expand_join_rule_columns(rule_columns, left_df, right_df, requested_dimensions, exclude_date)`
  - 용도: rule 에 사용자 요청 차원과 날짜 정책을 추가 반영

- `select_default_join_type(user_input, tool_results, left_dataset, right_dataset)`
  - 용도: rule 이 없을 때 join type 선택

- `plan_merge_strategy(tool_results, frames, user_input)`
  - 용도: 어떤 데이터셋을 base 로 삼고 어떤 순서로 어떻게 합칠지 계획

- `cleanup_duplicate_dimension_columns(merged_df)`
  - 용도: merge 후 생긴 `_x`, `_y` 중 차원 컬럼 정리

- `merge_and_cleanup(merged_df, next_df, join_columns, how)`
  - 용도: 실제 merge 와 정리 수행

- `build_analysis_base_table(tool_results, user_input)`
  - 용도: 여러 raw dataset 을 하나의 분석 테이블로 합치는 핵심 함수

- `build_multi_dataset_overview(tool_results)`
  - 용도: merge 대신 dataset 개요만 보여줄 때 쓰는 요약 테이블 생성

## 8. 런타임 총괄 함수

### [manufacturing_agent/services/runtime_service.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/services/runtime_service.py)

- `mark_primary_result(tool_results, primary_index)`
  - 용도: UI 에서 기본으로 펼쳐 보여줄 결과 표시

- `run_analysis_after_retrieval(user_input, chat_history, source_results, extracted_params, retrieval_plan=None)`
  - 용도: 조회 직후 분석이 필요하면 후처리까지 연결

- `run_multi_retrieval_jobs(user_input, chat_history, current_data, jobs, retrieval_plan=None)`
  - 용도: 다중 조회, 병합, 개요 생성, 다중 분석까지 한 번에 수행

- `run_followup_analysis(user_input, chat_history, current_data, extracted_params)`
  - 용도: 현재 테이블을 기반으로 재분석

- `run_retrieval(user_input, chat_history, current_data, extracted_params)`
  - 용도: 단일/다중 retrieval 전체 진입점

## 9. 응답 생성 함수

### [manufacturing_agent/services/response_service.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/services/response_service.py)

- `format_result_preview(result)`
  - 용도: 응답 프롬프트에 넣을 표 요약 텍스트 생성

- `build_response_prompt(user_input, result, chat_history)`
  - 용도: 사용자에게 보여줄 자연어 응답 생성용 프롬프트 작성

- `generate_response(user_input, result, chat_history)`
  - 용도: 실제 응답 문자열 생성

## 10. 분석 함수

### [manufacturing_agent/analysis/helpers.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/analysis/helpers.py)
- `extract_columns(data)`
  - 용도: row list 에서 컬럼 목록 추출
- `dataset_profile(data)`
  - 용도: 데이터셋의 컬럼/행수/샘플 요약 생성
- `find_metric_column(columns, query_text=None)`
  - 용도: 주 metric 후보 찾기
- `_resolve_requested_column(query_text, columns)`
  - 용도: 사용자가 직접 언급한 컬럼 찾기
- `find_requested_dimensions(query_text, columns)`
  - 용도: group by 후보 차원 찾기
- `find_missing_dimensions(query_text, columns)`
  - 용도: 사용자가 원했지만 없는 컬럼 찾기
- `format_missing_column_message(missing_columns)`
  - 용도: 사용자 친화적 에러 메시지 생성
- `parse_top_n(query_text)`
  - 용도: top-N 요구 해석
- `minimal_fallback_plan(query_text, columns)`
  - 용도: LLM 계획이 실패했을 때 최소 수준 분석 계획 생성
- `extract_derived_columns_from_code(code)`
  - 용도: 코드가 만드는 새 컬럼 이름 추출
- `validate_plan_columns(plan, columns)`
  - 용도: 계획이 실제 컬럼을 사용 가능한지 검사
- `build_transformation_summary(plan)`
  - 용도: 어떤 분석을 했는지 간단 설명 문자열 생성

### [manufacturing_agent/analysis/llm_planner.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/analysis/llm_planner.py)
- `_get_llm_for_task(task)`
  - 용도: 분석 계획 전용 LLM 선택
- `build_dataset_specific_hints(source_tool_name, columns)`
  - 용도: dataset 종류에 맞는 힌트 제공
- `extract_text_from_response(content)`
  - 용도: LLM 응답 텍스트 추출
- `extract_json_payload(text)`
  - 용도: JSON payload 파싱
- `build_llm_prompt(query_text, data, source_tool_name, retry_error=None, previous_code=None)`
  - 용도: 분석 계획 생성용 프롬프트 작성
- `build_llm_plan(...)`
  - 용도: 실제 계획 딕셔너리 생성

### [manufacturing_agent/analysis/safe_executor.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/analysis/safe_executor.py)
- `_has_result_assignment(tree)`
  - 용도: 코드 안에 `result = ...` 가 있는지 검사
- `validate_python_code(code)`
  - 용도: AST 안전성 검사
- `execute_safe_dataframe_code(code, data)`
  - 용도: 검증된 pandas 코드를 DataFrame 에 대해 실행

### [manufacturing_agent/analysis/engine.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/analysis/engine.py)
- `_find_semantic_retry_reason(plan, columns)`
  - 용도: 왜 계획을 다시 세워야 하는지 원인 정리
- `_execute_plan(plan, data, source_tool_name)`
  - 용도: 분석 계획 실행
- `_pick_ratio_operands(query_text, columns)`
  - 용도: 비율 계산에 사용할 분자/분모 컬럼 추정
- `_pick_group_columns(query_text, columns)`
  - 용도: group by 컬럼 추정
- `_build_domain_rule_fallback_plan(query_text, columns, source_tool_name)`
  - 용도: 등록된 도메인 규칙 기반 fallback 계획 생성
- `_success_result(...)`, `_error_result(...)`
  - 용도: 결과 payload 표준화
- `_execute_with_retry(...)`
  - 용도: 실패 시 재시도 실행
- `execute_analysis_query(query_text, data, source_tool_name="")`
  - 용도: 분석 엔진 최상위 함수

## 11. 데이터 함수

### [manufacturing_agent/data/retrieval.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/data/retrieval.py)

데이터 생성 helper:

- `_stable_seed`
- `_as_list`
- `_normalize_key`
- `_match_exact`
- `_match_mcp_no`
- `_is_auto_product`
- `_matches_product`
- `_apply_common_filters`
- `_iter_valid_process_product_pairs`
- `_make_lot_id`
- `_derive_business_family`
- `_derive_factory`
- `_derive_org`
- `_build_base_row`
- `_pick_equipment`
- `_apply_signal_overrides`

이 helper 들의 공통 용도:

- 입력 필터 정규화
- mock row 기본값 생성
- 공정/제품 조합 생성
- 특수 제품 규칙 반영

주요 공개 dataset 함수:

- `get_production_data`
- `get_target_data`
- `get_defect_rate`
- `get_equipment_status`
- `get_wip_status`
- `get_yield_data`
- `get_hold_lot_data`
- `get_scrap_data`
- `get_recipe_condition_data`
- `get_lot_trace_data`

공통 역할:

- 입력: `date`, `process_name`, `mode`, `den`, `tech`, `product_name` 등
- 출력: `success`, `tool_name`, `dataset_key`, `dataset_label`, `data`, `summary`

추가 관리 함수:

- `get_dataset_label`
- `list_available_dataset_labels`
- `dataset_requires_date`
- `pick_retrieval_tools`
- `pick_retrieval_tool`
- `execute_retrieval_tools`
- `build_current_datasets`

## 12. 도메인 함수와 요소

### [manufacturing_agent/domain/knowledge.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/domain/knowledge.py)

중요 상수 묶음:

- `FILTER_FIELDS`
- `PROCESS_GROUPS`
- `LITERAL_PROCESSES`
- `INDIVIDUAL_PROCESSES`
- `PROCESS_SPECS`
- `PROCESS_GROUP_SYNONYMS`
- `PROCESS_OPER_NUM_MAP`
- `PRODUCTS`
- `PRODUCT_TECH_FAMILY`
- `TECH_GROUPS`, `MODE_GROUPS`, `DEN_GROUPS`, `PKG_TYPE1_GROUPS`, `PKG_TYPE2_GROUPS`
- `SPECIAL_PRODUCT_ALIASES`
- `AUTO_SUFFIXES`
- `SPECIAL_DOMAIN_RULES`
- `DATASET_METADATA`

공통 용도:

- 제조 도메인을 LLM prompt 와 mock data 생성 모두에서 일관되게 재사용하기

함수:

- `_dedupe_processes()`
  - 용도: 중복 없는 실제 공정명 목록 생성
- `build_domain_knowledge_prompt()`
  - 용도: 위 상수들을 LLM prompt 텍스트로 펼치는 함수

### [manufacturing_agent/domain/registry.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/domain/registry.py)

구성 요소 범주:

- LLM parsing helper
  - `_get_llm_for_task`
  - `_extract_text_from_response`
  - `_parse_json_block`

- payload normalize helper
  - `_as_list`
  - `_dedupe`
  - `_normalize_field_name`
  - `_normalize_value_group`
  - `_normalize_dataset_keyword_rule`
  - `_normalize_source_columns`
  - `_normalize_analysis_rule`
  - `_normalize_join_rule`
  - `_normalize_entry_payload`

- builtin rule builder
  - `_build_builtin_value_groups`
  - `_build_builtin_dataset_keywords`
  - `_keyword_owners`

- registry storage / CRUD
  - `_ensure_registry_dirs`
  - `load_domain_registry`
  - `register_domain_submission`
  - `delete_domain_entry`
  - `list_domain_entries`
  - `get_domain_registry_summary`

- validation / parsing
  - `validate_domain_payload`
  - `_detect_join_keys_from_text`
  - `_infer_join_type_from_text`
  - `_infer_join_rules_from_text`
  - `parse_domain_text_to_payload`
  - `preview_domain_submission`

- rule query / expansion
  - `get_dataset_keyword_map`
  - `get_registered_value_groups`
  - `expand_registered_values`
  - `detect_registered_values`
  - `get_registered_analysis_rules`
  - `get_registered_join_rules`
  - `_normalize_compact_text`
  - `match_registered_analysis_rules`
  - `format_analysis_rule_for_prompt`
  - `build_registered_domain_prompt`

이 파일의 핵심 목적:

- 사용자가 새 도메인 지식을 등록할 수 있게 하기
- 등록된 규칙을 파라미터 추출, dataset 선택, join 규칙, 분석 규칙에 실제로 반영하기

## 13. UI 함수

### [manufacturing_agent/app/ui_renderer.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/app/ui_renderer.py)

- `empty_context()`
- `has_active_context(context)`
- `reset_filter_context(state)`, `reset_filter_session(state)`, `reset_chat_session(state)`
- `init_session_state()`
- `format_display_dataframe(rows)`
- `_build_analysis_logic_labels(tool_result)`
- `render_applied_params(tool_result)`
- `render_context(context)`
- `render_analysis_summary(tool_result)`
- `_get_expanded_indexes(tool_results)`
- `_build_result_title(tool_result, index)`
- `render_tool_results(tool_results, engineer_mode=False)`
- `sync_context(extracted_params)`

공통 목적:

- Streamlit UI 에서 결과와 상태를 읽기 쉽게 보여주고, 세션 상태를 안전하게 유지하기

### [manufacturing_agent/app/ui_domain_knowledge.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/app/ui_domain_knowledge.py)

- `_format_table`
- `_render_issue_messages`
- `_render_payload_section`
- `_render_preview`
- `render_domain_registry_summary_card`
- `_render_summary_cards`
- `_render_entry_list`
- `render_domain_knowledge_page`

공통 목적:

- 사용자가 custom 도메인 규칙을 등록, 검증, 저장, 확인할 수 있는 UI 제공

## 14. Langflow 함수와 요소

### [manufacturing_agent/adapters/langflow_nodes.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/adapters/langflow_nodes.py)

- `extract_params_component(input_state)`
- `decide_query_mode_component(input_state)`
- `plan_retrieval_component(input_state)`
- `retrieval_component(input_state)`
- `multi_retrieval_component(input_state)`
- `followup_analysis_component(input_state)`

공통 목적:

- Langflow에서 쓰기 쉬운 `dict -> dict` 스타일로 서비스 함수 재사용

### [langflow_version/component_base.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/langflow_version/component_base.py)

- `make_data(payload, text=None)`
  - 용도: Langflow `Data` 또는 그와 비슷한 객체 생성
- `read_data_payload(value)`
  - 용도: Langflow `Data` 객체를 일반 dict 로 복원

추가 요소:

- `Component`, `DataInput`, `MessageTextInput`, `MultilineInput`, `Output`, `Data`
  - 용도: Langflow 설치 시 실제 클래스를 쓰고, 없을 때는 fallback 클래스를 제공

### [langflow_version/workflow.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/langflow_version/workflow.py)

- `build_initial_state(...)`
  - 용도: Langflow 입력값을 `AgentGraphState` 와 같은 형태로 만들기
- `resolve_request_step(state)`
- `plan_retrieval_step(state)`
- `run_followup_step(state)`
- `run_single_retrieval_step(state)`
- `run_multi_retrieval_step(state)`
- `finish_step(state)`
- `run_next_branch(state)`
- `run_langflow_workflow(...)`

공통 목적:

- LangGraph 런타임 없이도 같은 순서로 전체 워크플로우를 실행하기

### [langflow_version/components.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/langflow_version/components.py)

- `_state_from_payload(payload)`
  - 용도: Langflow `Data` 내부의 state 추출

- `ManufacturingStateComponent`
- `ResolveRequestComponent`
- `PlanRetrievalComponent`
- `RunWorkflowBranchComponent`
- `FinishManufacturingResultComponent`
- `ManufacturingAgentComponent`

공통 목적:

- Langflow 캔버스에서 노드처럼 꽂아 사용할 수 있는 컴포넌트 제공

## 15. 루트 앱 함수

### [app.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/app.py)

- `_get_saved_chat_history()`
  - 용도: Streamlit 메시지를 agent 입력 형식으로 변환
- `_render_saved_chat_history()`
  - 용도: 저장된 대화/결과를 화면에 다시 렌더링
- `_run_chat_turn(user_input)`
  - 용도: `run_agent()` 호출 후 세션 상태 갱신
- `_stream_response_text(text)`
  - 용도: 응답을 줄 단위로 스트리밍 출력
- `_render_display_options()`
  - 용도: 엔지니어 모드 토글
- `_render_reset_controls()`
  - 용도: 채팅 리셋, 필터 리셋 버튼 처리

## 16. 테스트와 스크립트 함수

### [scripts/run_validation_scenarios.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/scripts/run_validation_scenarios.py)
- `_configure_temp_registry()`
- `_register_validation_rules()`
- `_summarize_result(question, result)`
- `main()`

공통 목적:

- 여러 질문 시나리오를 자동처럼 반복 실행하면서 수동 검증하기

### [tests/test_v2_structure.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/tests/test_v2_structure.py)
- `_FakeResponse`, `_FakeLLM`
- `_stub_llms(monkeypatch, content="{}")`
- 나머지 `test_*` 함수

공통 목적:

- 실제 LLM 없이 구조와 기본 흐름을 테스트하기

### [tests/conftest.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/tests/conftest.py)
- 전역 fixture 는 없고, import path 설정만 합니다.

## 17. 지금 구조를 어떻게 보면 좋은가

- 실제 실행 코드는 `manufacturing_agent/` 와 `langflow_version/` 에 있습니다.
- 새 기능을 추가할 때도 이 두 경로를 중심으로 보면 됩니다.
- 과거 `core/` 계층은 제거되었으므로, 더 이상 읽기 시작점으로 고려하지 않아도 됩니다.
