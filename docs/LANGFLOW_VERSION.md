# Langflow Version Guide

이 문서는 Langflow용 구현이 어떤 구조로 되어 있는지 설명합니다.

## 핵심 원칙

- 실제 비즈니스 로직은 [manufacturing_agent](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent)에 둡니다.
- Langflow 쪽은 그 로직을 노드형으로 감싸는 얇은 레이어만 둡니다.
- 처음에는 큰 노드로 빠르게 테스트하고, 이후에는 작은 노드로 쪼개서 수정/확장합니다.

## 폴더 역할

- [manufacturing_agent](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent)
  - 공통 코어 로직
- [langflow_version](/C:/Users/qkekt/Desktop/agent_langgraph_v2/langflow_version)
  - Langflow에서 재사용하는 workflow/helper
- [langflow_components](/C:/Users/qkekt/Desktop/agent_langgraph_v2/langflow_components)
  - Langflow가 직접 읽는 커스텀 컴포넌트 폴더

## 컴포넌트 구성

### 큰 단위 컴포넌트
- [manufacturing_agent_component.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/langflow_components/manufacturing_agent/manufacturing_agent_component.py)
- [resolve_manufacturing_request.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/langflow_components/manufacturing_agent/resolve_manufacturing_request.py)
- [plan_manufacturing_retrieval.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/langflow_components/manufacturing_agent/plan_manufacturing_retrieval.py)
- [run_manufacturing_branch.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/langflow_components/manufacturing_agent/run_manufacturing_branch.py)
- [finish_manufacturing_result.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/langflow_components/manufacturing_agent/finish_manufacturing_result.py)

### 더 잘게 나눈 컴포넌트
- [manufacturing_state_input.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/langflow_components/manufacturing_agent/manufacturing_state_input.py)
- [extract_manufacturing_params.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/langflow_components/manufacturing_agent/extract_manufacturing_params.py)
- [decide_manufacturing_query_mode.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/langflow_components/manufacturing_agent/decide_manufacturing_query_mode.py)
- [plan_manufacturing_datasets.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/langflow_components/manufacturing_agent/plan_manufacturing_datasets.py)
- [build_manufacturing_jobs.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/langflow_components/manufacturing_agent/build_manufacturing_jobs.py)
- [execute_manufacturing_jobs.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/langflow_components/manufacturing_agent/execute_manufacturing_jobs.py)
- [run_manufacturing_followup.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/langflow_components/manufacturing_agent/run_manufacturing_followup.py)

## 추천 전략

### 1. 빠른 확인
- `manufacturing_agent_component` 하나만 사용

### 2. 확장 중심 설계
- `manufacturing_state_input`
- `extract_manufacturing_params`
- `decide_manufacturing_query_mode`
- `plan_manufacturing_datasets`
- `build_manufacturing_jobs`
- `execute_manufacturing_jobs`

필요하면 이 뒤에 큰 단위 노드를 섞어서 사용합니다.

## 커스텀 컴포넌트 추가 방식

Langflow는 Python 파일에 `Component` 클래스를 직접 정의한 커스텀 컴포넌트를 읽습니다.
그래서 프로젝트 관리 관점에서는 지금처럼 파일 기반으로 관리하는 방식이 가장 안정적입니다.
