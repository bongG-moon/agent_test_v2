# Function And Element Guide

이 문서는 주요 함수와 요소가 왜 만들어졌는지, 어디에서 사용되는지 빠르게 이해하기 위한 안내서입니다.

## 1. 실행 진입 함수

### [manufacturing_agent/agent.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/agent.py)

- `run_agent(user_input, chat_history=None, context=None, current_data=None)`
  - 역할: 제조 에이전트 전체 실행의 시작점입니다.
  - 사용처: [app.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/app.py), 테스트, 외부 호출부

- `extract_params_component(input_state)`
  - 역할: Langflow 스타일 입력에서 파라미터 추출만 독립 실행할 수 있게 만든 래퍼입니다.

- `decide_query_mode_component(input_state)`
  - 역할: 새 데이터 조회인지, 현재 데이터 후속 분석인지 구분합니다.

- `plan_retrieval_component(input_state)`
  - 역할: 어떤 데이터셋을 불러와야 할지 계획합니다.

- `retrieval_component(input_state)`
  - 역할: 단일 데이터셋 조회를 실행합니다.

- `multi_retrieval_component(input_state)`
  - 역할: 여러 데이터셋 조회를 묶어서 실행합니다.

- `followup_analysis_component(input_state)`
  - 역할: 현재 화면의 테이블을 다시 가공하는 후속 분석을 실행합니다.

## 2. 그래프 구성 요소

### [manufacturing_agent/graph/state.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/graph/state.py)

- `QueryMode`
  - 역할: `retrieval`, `followup_transform` 같은 실행 유형을 구분합니다.

- `AgentGraphState`
  - 역할: 그래프 전체에서 공유하는 상태 구조입니다.

### [manufacturing_agent/graph/builder.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/graph/builder.py)

- `route_after_resolve(state)`
  - 역할: 요청 해석 후 다음 노드를 결정합니다.

- `route_after_retrieval_plan(state)`
  - 역할: 조회 계획 결과를 보고 종료, 단일 조회, 다중 조회 중 하나로 분기합니다.

- `get_agent_graph()`
  - 역할: LangGraph를 조립하고 최종 그래프를 반환합니다.

## 3. 그래프 노드 함수

### [manufacturing_agent/graph/nodes/resolve_request.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/graph/nodes/resolve_request.py)
- `resolve_request_node(state)`
  - 역할: 파라미터를 추출하고 query mode를 정합니다.

### [manufacturing_agent/graph/nodes/plan_retrieval.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/graph/nodes/plan_retrieval.py)
- `plan_retrieval_node(state)`
  - 역할: 필요한 데이터셋과 조회 작업 목록을 만듭니다.

### [manufacturing_agent/graph/nodes/retrieve_single.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/graph/nodes/retrieve_single.py)
- `single_retrieval_node(state)`
  - 역할: 단일 데이터셋 조회와 후처리를 실행합니다.

### [manufacturing_agent/graph/nodes/retrieve_multi.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/graph/nodes/retrieve_multi.py)
- `multi_retrieval_node(state)`
  - 역할: 다중 데이터셋 조회, 병합, 후처리를 실행합니다.

### [manufacturing_agent/graph/nodes/followup_analysis.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/graph/nodes/followup_analysis.py)
- `followup_analysis_node(state)`
  - 역할: 현재 데이터 기반의 후속 분석을 실행합니다.

### [manufacturing_agent/graph/nodes/finish.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/graph/nodes/finish.py)
- `finish_node(state)`
  - 역할: 최종 결과를 정리해 반환합니다.

## 4. 파라미터 추출 함수

### [manufacturing_agent/services/parameter_service.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/services/parameter_service.py)

- `resolve_required_params(...)`
  - 역할: 질문에서 조회용 필터를 추출하는 메인 함수입니다.
  - 흐름: LLM 초안 생성 -> 도메인 스펙 기반 공통 정규화 -> 문맥 상속

- `_merge_unique_values(...)`
  - 역할: 단일 값, 리스트, `None` 을 한 번에 받아 고유 리스트로 정리합니다.
  - 의도: 예전의 `_as_list`, `_dedupe`, `_merge_optional_lists` 역할을 하나로 합친 함수입니다.

- `_match_keyword_rules(...)`
  - 역할: 도메인 파일에 정의된 키워드 규칙을 읽어 목표 값을 찾습니다.
  - 예: `HBM` -> `HBM_OR_3DS`, `투입` -> `INPUT`

- `_expand_group_values(...)`
  - 역할: LLM이 뽑아낸 그룹형 값을 실제 조회값 목록으로 확장합니다.

- `_detect_group_values_from_text(...)`
  - 역할: LLM이 값을 놓쳤을 때 질문 원문에서 그룹형 값을 다시 찾습니다.

- `_detect_candidate_values_from_text(...)`
  - 역할: `OPER_NUM` 같은 코드형 값을 후보 목록과 정규식으로 찾습니다.

- `_normalize_single_value(...)`
  - 역할: 단일 값 필드를 공통 방식으로 정규화합니다.

- `_normalize_multi_value(...)`
  - 역할: 리스트형 필드를 공통 방식으로 정규화합니다.

- `_normalize_field_value(...)`
  - 역할: 도메인 스펙 하나를 기준으로 필드 값을 처리합니다.

- `_build_initial_params(...)`
  - 역할: LLM JSON 응답을 내부 파라미터 구조로 옮깁니다.

- `_apply_domain_specs(...)`
  - 역할: 도메인 파일의 `PARAMETER_FIELD_SPECS` 를 돌면서 모든 필드를 공통 방식으로 처리합니다.

- `_inherit_from_context(...)`
  - 역할: 이번 질문에 빠진 조건을 이전 문맥에서 이어받습니다.

- `_fallback_date(text)`
  - 역할: `오늘`, `어제` 같은 표현을 날짜 문자열로 보정합니다.

## 5. Query Mode 판단 함수

### [manufacturing_agent/services/query_mode.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/services/query_mode.py)

- `has_explicit_date_reference(user_input)`
  - 역할: 날짜를 새로 지정했는지 확인합니다.

- `mentions_grouping_expression(user_input)`
  - 역할: `공정별`, `MODE별`, `group by` 같은 그룹화 요청을 감지합니다.

- `needs_post_processing(...)`
  - 역할: 추가 계산이나 집계가 필요한 질문인지 판단합니다.

- `looks_like_new_data_request(user_input)`
  - 역할: 새로운 조회가 필요한 질문인지 판단합니다.

- `prune_followup_params(...)`
  - 역할: 후속 분석에서 불필요한 필터를 걷어냅니다.

- `choose_query_mode(user_input, current_data, extracted_params)`
  - 역할: `retrieval` 과 `followup_transform` 중 최종 실행 경로를 고릅니다.

## 6. 요청 문맥 함수

### [manufacturing_agent/services/request_context.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/services/request_context.py)

- `build_recent_chat_text(chat_history)`
  - 역할: 최근 대화 내용을 LLM 프롬프트용 텍스트로 정리합니다.

- `get_current_table_columns(current_data)`
  - 역할: 현재 결과 테이블의 컬럼을 추출합니다.

- `has_current_data(current_data)`
  - 역할: 현재 데이터가 있는지 확인합니다.

- `collect_applied_params(current_data)`
  - 역할: 현재 데이터에 적용된 필터를 수집합니다.

- `attach_result_metadata(...)`
  - 역할: 조회 결과에 dataset key, label, applied params 같은 메타데이터를 붙입니다.

## 7. Retrieval 계획 함수

### [manufacturing_agent/services/retrieval_planner.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/services/retrieval_planner.py)

- `plan_retrieval_request(...)`
  - 역할: 어떤 raw dataset 이 필요한지 계획합니다.

- `review_retrieval_sufficiency(...)`
  - 역할: 선택된 dataset 조합이 질문을 처리하기에 충분한지 검토합니다.

- `extract_date_slices(user_input, default_date)`
  - 역할: 여러 날짜가 언급된 질문을 날짜 조각으로 나눕니다.

- `build_retrieval_jobs(...)`
  - 역할: 실제 실행 가능한 조회 작업 목록을 만듭니다.

- `execute_retrieval_jobs(jobs)`
  - 역할: 계획된 조회 작업을 실행합니다.

## 8. 병합 함수

### [manufacturing_agent/services/merge_service.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/services/merge_service.py)

- `pick_join_columns(...)`
  - 역할: 두 데이터셋을 어떤 컬럼으로 연결할지 고릅니다.

- `classify_join_cardinality(...)`
  - 역할: 1:1, 1:N, N:1, N:M 관계를 판단합니다.

- `plan_merge_strategy(...)`
  - 역할: 여러 데이터셋을 어떤 순서와 키로 병합할지 계획합니다.

- `build_analysis_base_table(tool_results, user_input)`
  - 역할: 다중 조회 결과를 분석 가능한 기준 테이블로 만듭니다.

- `build_multi_dataset_overview(tool_results)`
  - 역할: 병합 대신 데이터셋 개요만 보여줘야 할 때 요약 결과를 만듭니다.

## 9. 실행 조립 함수

### [manufacturing_agent/services/runtime_service.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/services/runtime_service.py)

- `ensure_filtered_result_rows(...)`
  - 역할: 최종 표시 직전에 필터가 실제 테이블에도 반영되도록 한 번 더 보정합니다.

- `run_analysis_after_retrieval(...)`
  - 역할: 조회 후 추가 분석이 필요하면 바로 이어서 실행합니다.

- `run_multi_retrieval_jobs(...)`
  - 역할: 다중 조회, 병합, 분석을 한 흐름으로 묶어 처리합니다.

- `run_followup_analysis(...)`
  - 역할: 현재 데이터에 대한 후속 분석을 실행합니다.

- `run_retrieval(...)`
  - 역할: retrieval 경로 전체를 조립해서 실행합니다.

## 10. 응답 생성 함수

### [manufacturing_agent/services/response_service.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/services/response_service.py)

- `format_result_preview(result)`
  - 역할: 결과 요약을 LLM 입력용 텍스트로 만듭니다.

- `build_response_prompt(user_input, result, chat_history)`
  - 역할: 자연어 응답 생성 프롬프트를 구성합니다.

- `generate_response(user_input, result, chat_history)`
  - 역할: 최종 사용자 응답을 생성합니다.

## 11. 분석 함수

### [manufacturing_agent/analysis/helpers.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/analysis/helpers.py)
- 역할: 컬럼 탐색, fallback 계획, 요청 차원 추출 등 분석 보조 기능을 제공합니다.

### [manufacturing_agent/analysis/llm_planner.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/analysis/llm_planner.py)
- 역할: 분석용 LLM 계획을 생성합니다.

### [manufacturing_agent/analysis/safe_executor.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/analysis/safe_executor.py)
- 역할: pandas 코드를 안전하게 검증하고 실행합니다.

### [manufacturing_agent/analysis/engine.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/analysis/engine.py)
- 역할: 분석 엔진 전체를 조립하고 재시도, fallback 까지 담당합니다.

## 12. 데이터 함수

### [manufacturing_agent/data/retrieval.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/data/retrieval.py)

- `get_production_data`
- `get_target_data`
- `get_equipment_status`
- `get_wip_status`
- `get_hold_lot_data`
- `get_lot_trace_data`
  - 역할: mock 제조 데이터를 생성하고 필터링한 결과를 반환합니다.

## 13. 도메인 함수와 요소

### [manufacturing_agent/domain/knowledge.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/domain/knowledge.py)

- `PROCESS_GROUPS`
- `PROCESS_SPECS`
- `MODE_GROUPS`
- `DEN_GROUPS`
- `TECH_GROUPS`
- `PKG_TYPE1_GROUPS`
- `PKG_TYPE2_GROUPS`
  - 역할: 제조 도메인의 기본 규칙과 값 목록을 정의합니다.

- `GROUP_PARAMETER_FIELD_SPECS`
- `CODE_PARAMETER_FIELD_SPECS`
- `SINGLE_VALUE_PARAMETER_FIELD_SPECS`
- `PARAMETER_FIELD_SPECS`
  - 역할: 파라미터 추출 규칙을 “그룹형 / 코드형 / 단일 값” 구조로 선언적으로 정리한 스펙입니다.
  - 사용처: [parameter_service.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/services/parameter_service.py)

- `build_domain_knowledge_prompt()`
  - 역할: 도메인 지식을 LLM 프롬프트용 텍스트로 변환합니다.

### [manufacturing_agent/domain/registry.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/domain/registry.py)

- `expand_registered_values`
  - 역할: 등록된 값 그룹을 실제 값 목록으로 확장합니다.

- `detect_registered_values`
  - 역할: 질문에서 등록된 값 그룹을 탐지합니다.

- `match_registered_analysis_rules`
  - 역할: 질문과 맞는 분석 규칙을 찾습니다.

- `build_registered_domain_prompt`
  - 역할: 사용자 정의 도메인 규칙을 LLM 프롬프트에 넣을 수 있게 정리합니다.

## 14. Langflow 함수와 요소

### [langflow_version/workflow.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/langflow_version/workflow.py)

- 역할: LangGraph 없이도 같은 흐름을 단계별로 실행할 수 있게 만든 워크플로우입니다.

### [langflow_version/components.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/langflow_version/components.py)

- 역할: Langflow 캔버스에서 사용할 컴포넌트를 정의합니다.
