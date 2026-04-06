# agent_langgraph_v2

제조 분석 에이전트를 초보자도 따라가기 쉬운 구조로 다시 정리한 프로젝트입니다.

핵심 방향:

- 실제 실행 코드는 `manufacturing_agent/` 에 모읍니다.
- LangGraph 버전과 Langflow 버전이 같은 코어 로직을 공유합니다.
- 도메인/데이터 의미는 기존 프로젝트를 유지합니다.

## 폴더 요약

```text
agent_langgraph_v2/
  app.py
  manufacturing_agent/   # 실제 v2 코어
  langflow_version/      # Langflow 전용 레이어
  docs/                  # 이해용 문서
  tests/                 # 기본 검증
```

## 어디부터 읽으면 좋은가

1. [app.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/app.py)
2. [manufacturing_agent/agent.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/agent.py)
3. [manufacturing_agent/graph/builder.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/graph/builder.py)
4. [docs/README.md](/C:/Users/qkekt/Desktop/agent_langgraph_v2/docs/README.md)
5. [docs/PYTHON_FILE_GUIDE.md](/C:/Users/qkekt/Desktop/agent_langgraph_v2/docs/PYTHON_FILE_GUIDE.md)

## 문서

- [docs/README.md](/C:/Users/qkekt/Desktop/agent_langgraph_v2/docs/README.md)
- [docs/START_HERE.md](/C:/Users/qkekt/Desktop/agent_langgraph_v2/docs/START_HERE.md)
- [docs/ARCHITECTURE.md](/C:/Users/qkekt/Desktop/agent_langgraph_v2/docs/ARCHITECTURE.md)
- [docs/PYTHON_FILE_GUIDE.md](/C:/Users/qkekt/Desktop/agent_langgraph_v2/docs/PYTHON_FILE_GUIDE.md)
- [docs/FUNCTION_ROLE_GUIDE.md](/C:/Users/qkekt/Desktop/agent_langgraph_v2/docs/FUNCTION_ROLE_GUIDE.md)
- [docs/BEGINNER_LEARNING_PATH.md](/C:/Users/qkekt/Desktop/agent_langgraph_v2/docs/BEGINNER_LEARNING_PATH.md)
- [docs/LANGFLOW_VERSION.md](/C:/Users/qkekt/Desktop/agent_langgraph_v2/docs/LANGFLOW_VERSION.md)
- [docs/LANGFLOW_CANVAS_EXAMPLE.md](/C:/Users/qkekt/Desktop/agent_langgraph_v2/docs/LANGFLOW_CANVAS_EXAMPLE.md)

## 실행

```bash
cd C:\Users\qkekt\Desktop\agent_langgraph_v2
pip install -r requirements.txt
copy .env.example .env
streamlit run app.py
```

## 테스트

```bash
pytest -q
```
