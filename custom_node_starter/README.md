# Custom Node Starter

이 폴더는 Langflow에서 커스텀 노드를 새로 만들 때 바로 참고할 수 있는 시작점입니다.

## 이 폴더를 왜 만들었는가

지금 프로젝트에는 이미 [langflow_components](/C:/Users/qkekt/Desktop/agent_langgraph_v2/langflow_components)가 있습니다.
그 폴더는 "실제로 로드되는 제조 노드"를 담는 운영용 폴더입니다.

반면 이 폴더는 아래 목적에 맞춘 안내용/템플릿용 폴더입니다.

- 처음 custom node를 만들 때 어떤 구조로 시작해야 하는지 보기
- Langflow UI에서 직접 만드는 방식과 파일 기반 방식을 비교하기
- 어떤 단위로 노드를 쪼개면 좋은지 감 잡기
- 나중에 새 커스텀 노드를 추가할 때 복붙 출발점으로 쓰기

## 추천 분리 기준

커스텀 노드는 "한 파일이 하나의 판단 또는 하나의 실행만 담당"하게 두는 편이 좋습니다.

추천 단위:

- 입력값을 state로 만드는 노드
- 질문에서 파라미터를 추출하는 노드
- 질의 모드를 판단하는 노드
- 필요한 dataset을 계획하는 노드
- 조회 job을 만드는 노드
- 조회 job을 실행하는 노드
- 현재 테이블을 후속 분석하는 노드
- 최종 응답을 정리하는 노드

좋은 예:

- `Extract Params`
- `Decide Query Mode`
- `Build Retrieval Jobs`
- `Execute Jobs`

너무 큰 예:

- `질문 해석 + 계획 + 실행 + 응답 생성`을 한 파일에 다 넣는 것

## 방법 1. Langflow UI에서 직접 만들기

공식 문서 기준으로 Langflow에서는 `New Custom Component`를 눌러 코드 창에 Python을 넣어 커스텀 컴포넌트를 만들 수 있습니다.

대략 순서:

1. Langflow에서 `Blank Flow` 열기
2. `Core components` 또는 `Bundles` 메뉴에서 `New Custom Component` 클릭
3. 코드 창에 Python 코드 붙여넣기
4. 저장
5. 캔버스에서 새 노드 확인

UI에서 바로 시작할 때는 아래 파일을 먼저 복붙하는 것이 가장 쉽습니다.

- [minimal_custom_component.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/custom_node_starter/ui_templates/minimal_custom_component.py)
- [manufacturing_param_summary.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/custom_node_starter/ui_templates/manufacturing_param_summary.py)

## 방법 2. 파일 기반으로 관리하기

프로젝트처럼 커스텀 노드를 관리하려면 파일 기반이 더 안정적입니다.

장점:

- Git으로 관리 가능
- 리뷰와 재사용이 쉬움
- 여러 노드를 묶어서 운영하기 좋음
- 팀 단위 유지보수에 유리함

기본 구조:

```text
LANGFLOW_COMPONENTS_PATH/
└── category_name/
    ├── __init__.py
    └── my_component.py
```

이 폴더 안에는 파일 기반 예시도 넣어뒀습니다.

- [file_templates/manufacturing_custom/__init__.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/custom_node_starter/file_templates/manufacturing_custom/__init__.py)
- [file_templates/manufacturing_custom/manufacturing_param_summary.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/custom_node_starter/file_templates/manufacturing_custom/manufacturing_param_summary.py)

## 커스텀 노드 만들 때 꼭 지켜야 할 것

### 1. 클래스는 파일 안에 직접 정의

Langflow 로더는 Python 파일을 직접 파싱합니다.
그래서 "다른 파일에서 import한 클래스를 다시 export만 하는 형태"는 잘 안 읽히는 경우가 있습니다.

안전한 방식:

- 한 `.py` 파일 안에 `class MyComponent(Component): ...`를 직접 적기

### 2. 입력 이름과 출력 이름을 겹치지 않기

예:

- 입력 `state`
- 출력 `state_with_params`

겹치면 Langflow가 컴포넌트를 로드하지 않을 수 있습니다.

### 3. 처음에는 노드를 아주 작게 만들기

처음부터 큰 노드를 만들기보다:

- 입력 확인용
- state 확인용
- 파라미터 추출용

이렇게 작게 시작한 뒤 나중에 합치는 편이 쉽습니다.

### 4. 설명 문구를 구체적으로 쓰기

- `display_name`
- `description`
- `name`

이 세 값은 Langflow 안에서 노드를 찾을 때 정말 중요합니다.

## 처음 시작할 때 추천 순서

1. UI에서 [minimal_custom_component.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/custom_node_starter/ui_templates/minimal_custom_component.py)로 테스트
2. 그 다음 [manufacturing_param_summary.py](/C:/Users/qkekt/Desktop/agent_langgraph_v2/custom_node_starter/ui_templates/manufacturing_param_summary.py)로 state 입력형 노드 테스트
3. 잘 되면 파일 기반 템플릿으로 옮겨 프로젝트 폴더에서 관리

## 공식 참고 자료

- [Create custom Python components](https://docs.langflow.org/components-custom-components)
- [Configure tools for agents](https://docs.langflow.org/agents-tools)
