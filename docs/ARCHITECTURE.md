# Architecture

## 전체 구조

```text
UI
  -> manufacturing_agent.agent.run_agent()
  -> graph/
  -> services/
  -> data/ + domain/
  -> analysis/
  -> response
```

## 1. UI Layer

- [app.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/app.py)
- [manufacturing_agent/app](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/app)

역할:

- Streamlit 화면 구성
- 채팅 입력/출력
- 세션 상태 유지
- 도메인 규칙 관리 화면 제공

## 2. Orchestration Layer

- [manufacturing_agent/graph](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/graph)

역할:

- LangGraph 노드 연결
- 분기 처리
- 상태 전달

원칙:

- 노드는 가능한 얇게 유지
- 복잡한 계산은 `services/` 로 이동

## 3. Service Layer

- [manufacturing_agent/services](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/services)

역할:

- 파라미터 추출
- query mode 판단
- retrieval 계획
- multi-dataset merge
- 실행 총괄
- 응답 생성

이 계층이 사실상 프로젝트의 핵심 비즈니스 로직입니다.

## 4. Domain Layer

- [manufacturing_agent/domain](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/domain)

역할:

- 공정 그룹
- 제품 속성
- dataset 메타 정보
- 사용자 정의 도메인 규칙
- custom join / analysis rule

## 5. Data Layer

- [manufacturing_agent/data](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/data)

역할:

- mock 제조 dataset 생성
- dataset registry 관리
- retrieval 실행

## 6. Analysis Layer

- [manufacturing_agent/analysis](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/analysis)

역할:

- LLM 기반 분석 계획
- pandas 코드 생성/보정
- 안전 실행
- fallback 분석

## 7. Langflow Layer

- [langflow_version](/C:/Users/qkekt/Desktop/agent_langgraph_v2/langflow_version)

역할:

- LangGraph와 같은 코어 로직을 Langflow 컴포넌트로 재사용
- Langflow 없는 환경에서도 import 가능하게 유지

## 8. Legacy Compatibility Layer

- [core](/C:/Users/qkekt/Desktop/agent_langgraph_v2/core)

역할:

- 이전 import 경로 유지
- 과거 구조 참고

권장:

- 새 기능은 `manufacturing_agent/` 와 `langflow_version/` 에 추가
- `core/` 는 가능하면 더 키우지 않음
