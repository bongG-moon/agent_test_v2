# agent_langgraph_v2

제조 분석 에이전트를 LangGraph 중심으로 다시 정리한 프로젝트입니다.  
핵심 목표는 기존 기능을 유지하면서도, 초보자도 흐름을 따라가기 쉽게 구조를 나누고 Langflow 전환도 가능하도록 만드는 것입니다.

## 핵심 구조

```text
app.py
  -> manufacturing_agent/        # 실제 실행 코어
  -> langflow_version/           # Langflow 전용 래퍼와 컴포넌트
  -> docs/                       # 구조/파일/함수 설명 문서
  -> tests/                      # 기본 동작 검증
```

## 어디부터 보면 좋은가

1. [app.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/app.py)
2. [manufacturing_agent/agent.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/agent.py)
3. [manufacturing_agent/graph/builder.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/manufacturing_agent/graph/builder.py)
4. [docs/START_HERE.md](/C:/Users/qkekt/Desktop/agent_langgraph_v2/docs/START_HERE.md)
5. [docs/ARCHITECTURE.md](/C:/Users/qkekt/Desktop/agent_langgraph_v2/docs/ARCHITECTURE.md)

## 문서

- [docs/README.md](/C:/Users/qkekt/Desktop/agent_langgraph_v2/docs/README.md)
- [docs/START_HERE.md](/C:/Users/qkekt/Desktop/agent_langgraph_v2/docs/START_HERE.md)
- [docs/ARCHITECTURE.md](/C:/Users/qkekt/Desktop/agent_langgraph_v2/docs/ARCHITECTURE.md)
- [docs/PYTHON_FILE_GUIDE.md](/C:/Users/qkekt/Desktop/agent_langgraph_v2/docs/PYTHON_FILE_GUIDE.md)
- [docs/FUNCTION_ROLE_GUIDE.md](/C:/Users/qkekt/Desktop/agent_langgraph_v2/docs/FUNCTION_ROLE_GUIDE.md)
- [docs/BEGINNER_LEARNING_PATH.md](/C:/Users/qkekt/Desktop/agent_langgraph_v2/docs/BEGINNER_LEARNING_PATH.md)
- [docs/LANGFLOW_VERSION.md](/C:/Users/qkekt/Desktop/agent_langgraph_v2/docs/LANGFLOW_VERSION.md)
- [docs/LANGFLOW_CANVAS_EXAMPLE.md](/C:/Users/qkekt/Desktop/agent_langgraph_v2/docs/LANGFLOW_CANVAS_EXAMPLE.md)
- [langflow_components/README.md](/C:/Users/qkekt/Desktop/agent_langgraph_v2/langflow_components/README.md)

## 실행

```powershell
cd C:\Users\qkekt\Desktop\agent_langgraph_v2
pip install -r requirements.txt
copy .env.example .env
streamlit run app.py
```

## 테스트

```powershell
cd C:\Users\qkekt\Desktop\agent_langgraph_v2
pytest -q
```
