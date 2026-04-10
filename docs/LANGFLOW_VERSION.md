# Langflow Version Guide

이 문서는 [langflow_version](/C:/Users/qkekt/Desktop/agent_langgraph_v2/langflow_version) 폴더가 왜 존재하는지와 어떻게 사용하는지 설명합니다.

## 왜 별도 폴더로 분리했는가

- LangGraph 버전은 [manufacturing_agent/graph](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/graph)를 중심으로 동작합니다.
- Langflow 버전은 컴포넌트와 데이터 입출력 형식이 따로 필요합니다.
- 하지만 도메인 로직과 데이터 로직을 복제하면 유지보수가 어려워집니다.

그래서 구조를 이렇게 잡았습니다.

- [manufacturing_agent](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent)
  - 공통 코어 로직
- [langflow_version](/C:/Users/qkekt/Desktop/agent_langgraph_v2/langflow_version)
  - Langflow 입출력과 컴포넌트 래퍼

즉, Langflow 버전은 새 비즈니스 로직이 아니라 공통 코어를 다른 실행 방식으로 감싸는 레이어입니다.

## 구성 파일

### [langflow_version/component_base.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/langflow_version/component_base.py)
- 역할: Langflow 설치 여부와 관계없이 import/test가 가능하도록 하는 호환층

### [langflow_version/workflow.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/langflow_version/workflow.py)
- 역할: LangGraph 없이도 같은 순서로 단계를 실행하는 워크플로우 함수 모음
- 특징: [manufacturing_agent/graph/builder.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/graph/builder.py)의 분기 함수와 같은 기준을 재사용합니다.

### [langflow_version/components.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/langflow_version/components.py)
- 역할: Langflow custom component 클래스 정의

## 제공 컴포넌트

### `ManufacturingStateComponent`
- 입력: `user_input`, `chat_history`, `context`, `current_data`
- 출력: `state`

### `ResolveRequestComponent`
- 입력: `state`
- 출력: `state`

### `PlanRetrievalComponent`
- 입력: `state`
- 출력: `state`

### `RunWorkflowBranchComponent`
- 입력: `state`
- 출력: `state`

### `FinishManufacturingResultComponent`
- 입력: `state`
- 출력: `state`, `result`

### `ManufacturingAgentComponent`
- 입력: `user_input`, `chat_history`, `context`, `current_data`
- 출력: `result`

## 공통 state

LangGraph와 Langflow는 가능한 한 같은 상태 구조를 사용합니다.

- `user_input`
- `chat_history`
- `context`
- `current_data`
- `extracted_params`
- `query_mode`
- `retrieval_plan`
- `retrieval_jobs`
- `result`

## 구현 원칙

- 도메인 로직은 [manufacturing_agent/domain](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/domain)에만 둡니다.
- 데이터 조회 로직은 [manufacturing_agent/data/retrieval.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/data/retrieval.py)에만 둡니다.
- Langflow 쪽은 입력을 state로 만들고, state를 결과로 바꾸는 역할만 담당합니다.

## 참고 자료

- [LANGFLOW_CANVAS_EXAMPLE.md](/C:/Users/qkekt/Desktop/agent_langgraph_v2/docs/LANGFLOW_CANVAS_EXAMPLE.md)
- [components.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/langflow_version/components.py)
- [workflow.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/langflow_version/workflow.py)
- [Langflow custom components docs](https://docs.langflow.org/components-custom-components)

## LANGFLOW_COMPONENTS_PATH 설정

Langflow에서 바로 커스텀 컴포넌트를 읽어오려면 아래 경로를 `LANGFLOW_COMPONENTS_PATH` 로 잡으면 됩니다.

```powershell
$env:LANGFLOW_COMPONENTS_PATH="C:\Users\qkekt\Desktop\agent_langgraph_v2\langflow_components"
```

실제 Langflow 로딩용 폴더:

- [langflow_components](/C:/Users/qkekt/Desktop/agent_langgraph_v2/langflow_components)
- [manufacturing_components.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/langflow_components/manufacturing_agent/manufacturing_components.py)

이 로딩용 폴더는 Langflow가 요구하는 폴더 구조만 담당하고,
실제 구현은 아래 공통 모듈을 그대로 재사용합니다.

- [components.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/langflow_version/components.py)
- [workflow.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/langflow_version/workflow.py)
- [manufacturing_agent](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent)
