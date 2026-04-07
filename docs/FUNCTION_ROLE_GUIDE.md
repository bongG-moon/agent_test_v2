# Function And Element Guide

이 문서는 주요 함수와 요소가 어떤 목적을 위해 만들어졌는지 설명합니다.

## 1. 실행 진입 함수

### [manufacturing_agent/agent.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/agent.py)

- `run_agent(user_input, chat_history=None, context=None, current_data=None)`
  - 역할: LangGraph 기반 제조 에이전트 전체 실행 시작점

- `extract_params_component(input_state)`
  - 역할: Langflow나 외부 노드 시스템에서 파라미터 추출만 따로 쓰기 위한 래퍼

- `decide_query_mode_component(input_state)`
  - 역할: 현재 질문이 retrieval인지 follow-up인지 따로 판단하기 위한 래퍼

- `plan_retrieval_component(input_state)`
  - 역할: 필요한 dataset과 retrieval job을 만드는 래퍼

- `retrieval_component(input_state)`
  - 역할: 일반 retrieval 실행 래퍼

- `multi_retrieval_component(input_state)`
  - 역할: 여러 retrieval job을 묶어 실행하는 래퍼

- `followup_analysis_component(input_state)`
  - 역할: 현재 데이터 기반 후속 분석 래퍼

## 2. 그래프 구성 요소

### [manufacturing_agent/graph/state.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/graph/state.py)

- `QueryMode`
  - 역할: 현재 질문이 `retrieval`인지 `followup_transform`인지 구분

- `AgentGraphState`
  - 역할: 그래프 전체에서 공유하는 상태 구조

### [manufacturing_agent/graph/builder.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/graph/builder.py)

- `route_after_resolve(state)`
  - 역할: 질문 해석 이후 follow-up으로 갈지, retrieval 계획으로 갈지 결정

- `route_after_retrieval_plan(state)`
  - 역할: 계획 결과를 보고 finish, single retrieval, multi retrieval 중 어디로 갈지 결정

- `get_agent_graph()`
  - 역할: LangGraph를 조립하고 compile된 graph를 반환

## 3. 그래프 노드 함수

### [manufacturing_agent/graph/nodes/resolve_request.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/graph/nodes/resolve_request.py)
- `resolve_request_node(state)`
  - 역할: 파라미터를 추출하고 query mode를 결정

### [manufacturing_agent/graph/nodes/plan_retrieval.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/graph/nodes/plan_retrieval.py)
- `plan_retrieval_node(state)`
  - 역할: dataset 계획과 retrieval job 생성

### [manufacturing_agent/graph/nodes/retrieve_single.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/graph/nodes/retrieve_single.py)
- `single_retrieval_node(state)`
  - 역할: 단일 dataset 조회 실행

### [manufacturing_agent/graph/nodes/retrieve_multi.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/graph/nodes/retrieve_multi.py)
- `multi_retrieval_node(state)`
  - 역할: 다중 dataset 조회 실행

### [manufacturing_agent/graph/nodes/followup_analysis.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/graph/nodes/followup_analysis.py)
- `followup_analysis_node(state)`
  - 역할: 현재 표 기반 후속 분석 수행

### [manufacturing_agent/graph/nodes/finish.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/graph/nodes/finish.py)
- `finish_node(state)`
  - 역할: 최종 결과 정리

## 4. 파라미터 추출 함수

### [manufacturing_agent/services/parameter_service.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/services/parameter_service.py)

- `resolve_required_params(...)`
  - 역할: 질문에서 조회 필터를 추출하는 메인 함수

- `_inherit_from_context(...)`
  - 역할: 이전 문맥 필터를 이어받음

- `_fallback_date(text)`
  - 역할: today, yesterday 같은 표현을 날짜로 보정

- `_detect_oper_num(text)`
  - 역할: `OPER_NUM` 패턴 감지

- `_canonicalize_group_values(...)`
  - 역할: `DA`, `WB` 같은 그룹 표현을 실제 공정 목록으로 확장

- `_apply_domain_overrides(...)`
  - 역할: 제조 도메인 규칙으로 값을 보정

## 5. query mode 판단 함수

### [manufacturing_agent/services/query_mode.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/services/query_mode.py)

- `has_explicit_date_reference(user_input)`
  - 역할: 날짜를 새로 지정했는지 확인

- `mentions_grouping_expression(user_input)`
  - 역할: `공정별`, `MODE별`, `group by` 같은 집계 표현 감지

- `needs_post_processing(...)`
  - 역할: 추가 계산이 필요한 질문인지 판단

- `looks_like_new_data_request(user_input)`
  - 역할: 새 dataset이 필요한 질문인지 판단

- `prune_followup_params(...)`
  - 역할: 후속 분석에서 불필요한 필터 정리

- `choose_query_mode(user_input, current_data, extracted_params)`
  - 역할: `retrieval`과 `followup_transform` 중 최종 결정

## 6. 요청 문맥 함수

### [manufacturing_agent/services/request_context.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/services/request_context.py)

- `build_recent_chat_text(chat_history)`
  - 역할: 대화 이력을 문자열로 변환

- `get_current_table_columns(current_data)`
  - 역할: 현재 표 컬럼 목록 추출

- `has_current_data(current_data)`
  - 역할: 후속 분석 가능한 현재 데이터가 있는지 확인

- `collect_applied_params(current_data)`
  - 역할: 현재 결과에 적용된 필터 읽기

- `attach_result_metadata(...)`
  - 역할: 결과 payload에 메타데이터 덧붙이기

- `collect_current_source_dataset_keys(current_data)`
  - 역할: 현재 표가 어떤 dataset에서 왔는지 추적

- `has_explicit_filter_change(...)`
  - 역할: 사용자가 필터를 새로 바꿨는지 확인

- `build_current_data_profile(current_data)`
  - 역할: 현재 데이터 요약 생성

- `build_unknown_retrieval_message()`
  - 역할: 알 수 없는 조회 요청에 대한 안내 메시지 생성

## 7. retrieval 계획 함수

### [manufacturing_agent/services/retrieval_planner.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/services/retrieval_planner.py)

- `plan_retrieval_request(...)`
  - 역할: 필요한 raw dataset 계획

- `review_retrieval_sufficiency(...)`
  - 역할: 선택한 dataset 조합이 충분한지 검토

- `build_missing_date_message(retrieval_keys)`
  - 역할: 날짜 부족 안내 문구 생성

- `extract_date_slices(user_input, default_date)`
  - 역할: 여러 날짜 표현을 slice로 정리

- `build_retrieval_jobs(...)`
  - 역할: 실행 가능한 조회 job 생성

- `execute_retrieval_jobs(jobs)`
  - 역할: 계획된 job 실행

- `should_retry_retrieval_plan(...)`
  - 역할: planning 재시도 필요 여부 판단

## 8. 병합 함수

### [manufacturing_agent/services/merge_service.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/services/merge_service.py)

- `KNOWN_DIMENSION_COLUMNS`
  - 역할: join 기준 후보가 되는 차원 컬럼 집합

- `DATE_COLUMNS`
  - 역할: 날짜 컬럼 집합

- `LIKELY_METRIC_COLUMNS`
  - 역할: 지표 컬럼으로 보이는 이름 모음

- `should_suffix_metrics(tool_results)`
  - 역할: metric 이름 충돌 방지 여부 판단

- `should_exclude_date_from_join(tool_results)`
  - 역할: 날짜를 join key에서 빼야 하는지 판단

- `resolve_requested_dimensions(user_input, frames)`
  - 역할: 사용자가 보고 싶은 차원 추론

- `pick_join_columns(...)`
  - 역할: join key 선택

- `classify_join_cardinality(...)`
  - 역할: 1:1, 1:N, N:1, N:M 판별

- `refine_join_columns_for_cardinality(...)`
  - 역할: 위험한 N:M join 방지

- `find_join_rule(left_dataset, right_dataset)`
  - 역할: custom join rule 조회

- `plan_merge_strategy(...)`
  - 역할: 병합 순서와 기준 계획

- `build_analysis_base_table(tool_results, user_input)`
  - 역할: 여러 dataset을 하나의 분석용 표로 합치는 핵심 함수

- `build_multi_dataset_overview(tool_results)`
  - 역할: merge 전 개요 표 생성

## 9. 실행 조율 함수

### [manufacturing_agent/services/runtime_service.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/services/runtime_service.py)

- `mark_primary_result(tool_results, primary_index)`
  - 역할: 대표 결과 지정

- `run_analysis_after_retrieval(...)`
  - 역할: 조회 후 필요한 분석까지 연결

- `run_multi_retrieval_jobs(...)`
  - 역할: 다중 조회, 병합, 후처리 분석까지 조율

- `run_followup_analysis(...)`
  - 역할: 현재 표 기반 후속 분석 수행

- `run_retrieval(...)`
  - 역할: retrieval 경로를 서비스 계층에서 묶어 처리

## 10. 응답 생성 함수

### [manufacturing_agent/services/response_service.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/services/response_service.py)

- `format_result_preview(result)`
  - 역할: LLM 응답용 결과 요약 생성

- `build_response_prompt(user_input, result, chat_history)`
  - 역할: 자연어 응답 프롬프트 작성

- `generate_response(user_input, result, chat_history)`
  - 역할: 최종 사용자 응답 생성

## 11. 분석 함수

### [manufacturing_agent/analysis/helpers.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/analysis/helpers.py)

- `extract_columns(data)`
- `dataset_profile(data)`
- `find_metric_column(columns, query_text=None)`
- `find_requested_dimensions(query_text, columns)`
- `parse_top_n(query_text)`
- `minimal_fallback_plan(query_text, columns)`
- `validate_plan_columns(plan, columns)`
  - 역할: 분석 전 컬럼 탐색과 fallback 보조

### [manufacturing_agent/analysis/llm_planner.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/analysis/llm_planner.py)

- `build_dataset_specific_hints(...)`
- `build_llm_prompt(...)`
- `build_llm_plan(...)`
  - 역할: LLM 분석 계획 생성

### [manufacturing_agent/analysis/safe_executor.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/analysis/safe_executor.py)

- `validate_python_code(code)`
- `execute_safe_dataframe_code(code, data)`
  - 역할: pandas 코드 안전 실행

### [manufacturing_agent/analysis/engine.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/analysis/engine.py)

- `_execute_plan(...)`
- `_execute_with_retry(...)`
- `_build_domain_rule_fallback_plan(...)`
- `execute_analysis_query(query_text, data, source_tool_name="")`
  - 역할: 분석 엔진 중심 실행

## 12. 데이터 함수

### [manufacturing_agent/data/retrieval.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/data/retrieval.py)

대표 dataset 함수:

- `get_production_data`
- `get_target_data`
- `get_equipment_status`
- `get_wip_status`
- `get_hold_lot_data`
- `get_lot_trace_data`

공통 역할:

- 입력 필터를 받아 mock 제조 데이터를 생성
- 표 형식 결과와 요약을 함께 반환

## 13. 도메인 함수와 요소

### [manufacturing_agent/domain/knowledge.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/domain/knowledge.py)

- `PROCESS_GROUPS`
- `PRODUCTS`
- `SPECIAL_PRODUCT_ALIASES`
- `DATASET_METADATA`
  - 역할: 제조 도메인의 기본 지식 정의

- `build_domain_knowledge_prompt()`
  - 역할: 도메인 지식을 LLM 프롬프트용 텍스트로 변환

### [manufacturing_agent/domain/registry.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/domain/registry.py)

- `load_domain_registry`
- `register_domain_submission`
- `validate_domain_payload`
- `expand_registered_values`
- `match_registered_analysis_rules`
- `build_registered_domain_prompt`
  - 역할: 사용자 정의 도메인 규칙 저장과 반영

## 14. Langflow 함수와 요소

### [langflow_version/component_base.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/langflow_version/component_base.py)

- `make_data(payload, text=None)`
  - 역할: Langflow `Data` 생성

- `read_data_payload(value)`
  - 역할: Langflow `Data`를 일반 dict로 변환

### [langflow_version/workflow.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/langflow_version/workflow.py)

- `build_initial_state(...)`
  - 역할: Langflow 입력을 공통 state로 만들기

- `resolve_request_step(state)`
- `plan_retrieval_step(state)`
- `run_followup_step(state)`
- `run_single_retrieval_step(state)`
- `run_multi_retrieval_step(state)`
- `finish_step(state)`
  - 역할: 각 단계를 LangGraph 없이 개별 실행

- `run_next_branch(state)`
  - 역할: 상태를 보고 다음 branch 실행

- `run_langflow_workflow(...)`
  - 역할: Langflow 버전 전체 실행 진입점

### [langflow_version/components.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/langflow_version/components.py)

- `ManufacturingStateComponent`
- `ResolveRequestComponent`
- `PlanRetrievalComponent`
- `RunWorkflowBranchComponent`
- `FinishManufacturingResultComponent`
- `ManufacturingAgentComponent`
  - 역할: Langflow 캔버스에서 사용하는 실제 컴포넌트
