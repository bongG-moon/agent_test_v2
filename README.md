# agent_langgraph_v2

초보자도 읽기 쉬운 구조로 다시 정리한 제조 분석 에이전트입니다.  
기존 프로젝트의 도메인 지식, mock 데이터, 사용자 도메인 레지스트리 개념은 유지하고, LangGraph 오케스트레이션을 `graph / services / domain / data` 계층으로 나눴습니다.

## 핵심 목표

- `core/agent.py` 같은 거대한 파일 대신 기능별 모듈로 분리
- LangGraph는 흐름만 담당
- 실제 비즈니스 로직은 순수 함수 서비스로 분리
- 나중에 Langflow custom node로 옮기기 쉬운 입력/출력 계약 유지
- 기존 제조 도메인/데이터 의미 유지

## 폴더 구조

```text
agent_langgraph_v2/
  app.py
  manufacturing_agent/
    agent.py
    graph/
      state.py
      routes.py
      builder.py
      nodes/
    services/
      request_context.py
      parameter_service.py
      query_mode.py
      retrieval_planner.py
      merge_service.py
      response_service.py
      runtime_service.py
    analysis/
    data/
    domain/
    adapters/
      langflow_nodes.py
    app/
      ui_renderer.py
      ui_domain_knowledge.py
  docs/
  tests/
```

## 실행

```bash
cd C:\Users\qkekt\Desktop\agent_langgraph_v2
pip install -r requirements.txt
copy .env.example .env
streamlit run app.py
```

## 읽는 순서

1. `manufacturing_agent/agent.py`
2. `manufacturing_agent/graph/builder.py`
3. `manufacturing_agent/graph/nodes/`
4. `manufacturing_agent/services/`
5. `manufacturing_agent/domain/` 와 `manufacturing_agent/data/`

## 구조 설명

- `graph/`
  - LangGraph 노드와 라우팅만 담당합니다.
- `services/`
  - 파라미터 추출, retrieval 계획, 병합, 응답 생성 같은 실제 로직이 있습니다.
- `domain/`
  - 공정 그룹, 제품 alias, 사용자 등록 규칙을 관리합니다.
- `data/`
  - 제조 mock 데이터 생성과 데이터셋 카탈로그를 관리합니다.
- `adapters/langflow_nodes.py`
  - Langflow로 옮길 때 재사용할 수 있는 dict 기반 wrapper입니다.

## Langflow 전환 포인트

각 컴포넌트는 가능하면 `dict -> dict` 형태로 작성했습니다.

- `extract_params_component`
- `decide_query_mode_component`
- `plan_retrieval_component`
- `retrieval_component`
- `multi_retrieval_component`
- `followup_analysis_component`

이 함수들은 LangGraph 노드에서 사용하는 서비스와 같은 코어 로직을 호출합니다.

## 테스트

```bash
pytest -q
```

현재 테스트는 v2 구조 기준 smoke/contract 테스트로 정리되어 있습니다.
