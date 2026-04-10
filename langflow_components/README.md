# Langflow Components Path

이 폴더는 `LANGFLOW_COMPONENTS_PATH`로 바로 연결해서 사용할 수 있는 실제 Langflow 커스텀 컴포넌트 모음입니다.

설정 예시:

```powershell
setx LANGFLOW_COMPONENTS_PATH "C:\Users\qkekt\Desktop\agent_langgraph_v2\langflow_components"
```

앱을 다시 시작한 뒤 `Blank Flow`에서 `manufacturing`를 검색하면 컴포넌트들이 보입니다.

## 포함된 컴포넌트

### 큰 단위 컴포넌트
- `manufacturing_agent_component`
  - 전체 흐름을 한 번에 실행합니다.
- `resolve_manufacturing_request`
  - 파라미터 추출과 질의 모드 판단을 한 번에 처리합니다.
- `plan_manufacturing_retrieval`
  - 데이터셋 선택과 조회 계획을 한 번에 처리합니다.
- `run_manufacturing_branch`
  - follow-up, 단일 조회, 다중 조회 중 하나를 실행합니다.
- `finish_manufacturing_result`
  - 최종 결과를 정리합니다.

### 잘게 나눈 컴포넌트
- `manufacturing_state_input`
  - Langflow 입력값을 공통 state로 만듭니다.
- `extract_manufacturing_params`
  - 날짜, 공정, 제품, MODE 같은 필터를 추출합니다.
- `decide_manufacturing_query_mode`
  - 새 조회인지 후속 분석인지 판단합니다.
- `plan_manufacturing_datasets`
  - 필요한 dataset 목록을 계획합니다.
- `build_manufacturing_jobs`
  - 실제 조회 job 목록을 만듭니다.
- `execute_manufacturing_jobs`
  - 생성된 job을 실행해 원본 결과를 state에 담습니다.
- `run_manufacturing_followup`
  - 현재 테이블을 활용한 후속 분석만 따로 실행합니다.

## 추천 사용 방식

### 빠른 테스트
1. `manufacturing_agent_component` 하나만 배치
2. `user_input`에 질문 입력
3. `result` 확인

### 확장/수정 중심 테스트
1. `manufacturing_state_input`
2. `extract_manufacturing_params`
3. `decide_manufacturing_query_mode`
4. `plan_manufacturing_datasets`
5. `build_manufacturing_jobs`
6. `execute_manufacturing_jobs`
7. 필요에 따라 `run_manufacturing_followup` 또는 기존 큰 노드와 조합

## 왜 두 종류를 같이 두는가

- 큰 단위 컴포넌트는 빨리 테스트하기 좋습니다.
- 잘게 나눈 컴포넌트는 Langflow에서 재배치하거나 중간 상태를 확인하기 좋습니다.
- 실제 운영에서는 큰 노드로 시작한 뒤, 수정이 잦은 부분만 작은 노드로 교체하는 방식이 가장 편합니다.
