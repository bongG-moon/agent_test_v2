# Langflow Version Guide

이 문서는 `langflow_version/` 폴더가 어떤 의도로 만들어졌고 어떻게 쓰면 되는지 설명합니다.

## 왜 별도 폴더로 분리했는가

- LangGraph 버전은 `manufacturing_agent/graph/*` 중심으로 동작합니다.
- Langflow 버전은 custom component 형태로 배포/연결하기 쉬워야 합니다.
- 두 버전이 도메인 로직과 데이터 로직을 따로 복제하면 유지보수가 어려워집니다.

그래서 현재 구조는 이렇게 잡았습니다.

- `manufacturing_agent/`: 공통 코어 로직
- `langflow_version/`: Langflow 입출력과 실행 방식을 감싼 전용 레이어

즉, Langflow 버전은 “새 비즈니스 로직”이 아니라 “같은 코어를 다른 실행기에서 쓰기 위한 껍데기”입니다.

## 폴더 구성

### [langflow_version/component_base.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/langflow_version/component_base.py)
- 역할: Langflow 설치 유무를 흡수하는 호환 계층
- 이유: 로컬 테스트 환경에는 Langflow가 없을 수 있기 때문

### [langflow_version/workflow.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/langflow_version/workflow.py)
- 역할: LangGraph 없이도 같은 순서를 따르는 실행 함수 모음
- 이유: Langflow 컴포넌트가 공통으로 재사용할 단일 실행 코어가 필요하기 때문

### [langflow_version/components.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/langflow_version/components.py)
- 역할: 실제 Langflow custom component 클래스들
- 이유: Langflow UI 에 노드처럼 꽂을 수 있게 하기 위해서

## 제공하는 컴포넌트

### `ManufacturingStateComponent`
- 입력: `user_input`, `chat_history`, `context`, `current_data`
- 출력: `state`
- 사용 목적: Langflow 캔버스의 입력 정규화

### `ResolveRequestComponent`
- 입력: `state`
- 출력: `state`
- 사용 목적: 파라미터 추출과 query mode 판단

### `PlanRetrievalComponent`
- 입력: `state`
- 출력: `state`
- 사용 목적: retrieval plan 과 job 생성

### `RunWorkflowBranchComponent`
- 입력: `state`
- 출력: `state`
- 사용 목적: 현재 상태에 맞는 다음 branch 실행

### `FinishManufacturingResultComponent`
- 입력: `state`
- 출력: `state`, `result`
- 사용 목적: 최종 결과 정리 및 외부 노드 전달

### `ManufacturingAgentComponent`
- 입력: `user_input`, `chat_history`, `context`, `current_data`
- 출력: `result`
- 사용 목적: 가장 간단한 전체 실행용 단일 노드

## 권장 사용 방식

### 가장 쉬운 방식

- `Manufacturing Agent` 단일 컴포넌트만 사용
- 장점: 연결이 가장 단순함
- 대상: 처음 Langflow 에 붙여보는 경우

### 단계별 제어 방식

1. `Manufacturing State Input`
2. `Resolve Manufacturing Request`
3. `Run Manufacturing Branch`
4. `Finish Manufacturing Result`

장점:

- 중간 state 를 볼 수 있음
- 디버깅이 쉬움
- 추후 custom node 를 더 세분화하기 쉬움

## 공통 상태 키

LangGraph 와 Langflow 버전이 같은 키를 쓰도록 맞췄습니다.

- `user_input`
- `chat_history`
- `context`
- `current_data`
- `extracted_params`
- `query_mode`
- `retrieval_plan`
- `retrieval_keys`
- `retrieval_jobs`
- `result`

이렇게 해두면:

- LangGraph 노드를 Langflow 로 옮길 때 개념이 거의 같습니다.
- 디버깅 시 “어느 단계에서 어떤 값이 생겼는지” 추적하기 쉽습니다.

## 구현 원칙

- 도메인/데이터 로직은 `manufacturing_agent` 에만 둡니다.
- Langflow 레이어는 state 입출력과 컴포넌트 클래스만 다룹니다.
- DataFrame 을 Langflow 밖으로 직접 많이 노출하지 않고, 가능하면 `dict`/`list[dict]` 기반 payload 를 사용합니다.
- 전체 기능은 유지하되, Langflow 레이어는 최대한 얇게 유지합니다.

## 실제 Langflow 환경에서 쓸 때

공식 문서 기준으로 Langflow 커스텀 컴포넌트는 `Component` 클래스를 상속하고, `inputs`, `outputs`, output method 를 정의하면 됩니다. 현재 구현도 그 형태를 따르도록 작성했습니다.

참고 자료:

- [Langflow custom components docs](https://docs.langflow.org/components-custom-components)

## 한계와 다음 확장 포인트

현재 버전은 “Langflow 전환 가능한 코드”와 “바로 쓸 수 있는 컴포넌트 클래스”를 제공하지만, Langflow 캔버스 JSON 프로젝트 파일까지 자동 생성하지는 않습니다.

다음 단계에서 확장 가능한 부분:

- 컴포넌트를 파일별로 더 잘게 분리
- 캔버스에서 분기 라우터 전용 컴포넌트 추가
- Langflow 프로젝트 템플릿 JSON 예시 추가
- 각 컴포넌트별 샘플 입출력 payload 문서화
