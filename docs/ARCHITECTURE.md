# Architecture

## 전체 구조

```text
UI
  -> manufacturing_agent.agent.run_agent()
  -> graph/builder.py
  -> graph/nodes/*
  -> services/*
  -> data/ + domain/ + analysis/
  -> response

Langflow
  -> langflow_version/components.py
  -> langflow_version/workflow.py
  -> manufacturing_agent/* 공통 로직 재사용
```

## 1. UI 레이어

- [app.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/app.py)
- [manufacturing_agent/app](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/app)

역할:

- Streamlit 화면 구성
- 채팅 입력/출력 관리
- 세션 상태 관리
- 결과 표 렌더링

## 2. 에이전트 진입 레이어

- [manufacturing_agent/agent.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/agent.py)

역할:

- LangGraph 실행 진입점 제공
- Langflow나 외부 시스템에서 바로 쓸 수 있는 래퍼 함수 제공
- 외부 시스템 연동용 얇은 래퍼 역할도 이 파일에서 함께 담당

## 3. 그래프 레이어

- [manufacturing_agent/graph/builder.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/graph/builder.py)
- [manufacturing_agent/graph/state.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/graph/state.py)
- [manufacturing_agent/graph/nodes](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/graph/nodes)

역할:

- LangGraph 노드 연결
- 상태 전달
- 분기 규칙 관리

구조 포인트:

- 노드는 파일별로 분리되어 읽기 쉽습니다.
- 별도 분기 전용 파일을 두지 않고, `builder.py` 안에서 분기 함수를 같이 관리합니다.
- 그래서 그래프 구조와 분기 규칙을 한 파일에서 같이 볼 수 있습니다.

## 4. 서비스 레이어

- [manufacturing_agent/services](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/services)

역할:

- 파라미터 추출
- query mode 판단
- retrieval 계획
- 다중 dataset 병합
- 실행 조율
- 응답 생성

핵심 포인트:

- 이 프로젝트의 실질적인 비즈니스 로직은 대부분 여기 있습니다.
- 그래프 노드는 가능한 얇게 유지하고, 계산과 판단은 서비스 함수로 분리했습니다.

## 5. 도메인 레이어

- [manufacturing_agent/domain](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/domain)

역할:

- 공정 그룹 관리
- 제품/기술/라인 지식 관리
- dataset 메타데이터 관리
- 사용자 정의 도메인 규칙 저장
- custom join 및 analysis rule 관리

## 6. 데이터 레이어

- [manufacturing_agent/data](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/data)

역할:

- mock 제조 데이터 생성
- dataset registry 관리
- dataset 조회 실행

## 7. 분석 레이어

- [manufacturing_agent/analysis](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/analysis)

역할:

- LLM 기반 분석 계획 생성
- pandas 코드 생성/보정
- 안전한 실행
- fallback 분석

## 8. Langflow 레이어

- [langflow_version](/C:/Users/qkekt/Desktop/agent_langgraph_v2/langflow_version)

역할:

- LangGraph 없이도 같은 흐름을 단계별로 실행
- Langflow 컴포넌트 형태로 코어 로직 감싸기
- Langflow 미설치 환경에서도 import/test 가능하도록 호환층 제공

핵심 포인트:

- Langflow 전용 새 비즈니스 로직을 만드는 구조가 아닙니다.
- `manufacturing_agent/`의 공통 코어를 재사용하기 위한 래퍼 레이어입니다.
