# Architecture

## 1. UI

- `app.py`
- `manufacturing_agent/app/`

Streamlit 화면과 세션 상태만 담당합니다.

## 2. Orchestration

- `manufacturing_agent/graph/`

LangGraph 노드와 라우팅만 있습니다.  
노드는 가능한 한 얇게 유지하고, 실제 계산은 `services/`로 내립니다.

## 3. Services

- `parameter_service.py`
- `query_mode.py`
- `retrieval_planner.py`
- `merge_service.py`
- `runtime_service.py`
- `response_service.py`

서비스 계층은 "입력 dict -> 출력 dict" 형태를 최대한 유지합니다.

## 4. Domain / Data

- `manufacturing_agent/domain/`
- `manufacturing_agent/data/`

제조 도메인 의미와 mock 데이터 생성 로직을 유지하는 계층입니다.
