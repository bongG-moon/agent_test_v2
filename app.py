import streamlit as st

from manufacturing_agent.agent import run_agent_with_progress
from manufacturing_agent.app.ui_domain_knowledge import render_domain_knowledge_page, render_domain_registry_summary_card
from manufacturing_agent.app.ui_renderer import (
    build_retry_question_suggestions,
    has_active_context,
    init_session_state,
    render_context,
    render_question_guide_and_examples,
    render_retry_question_suggestions,
    render_tool_results,
    reset_chat_session,
    reset_filter_session,
    sync_context,
)
from manufacturing_agent.shared.text_sanitizer import sanitize_markdown_text


st.set_page_config(page_title="Compact Manufacturing Chat", layout="wide")


def _get_saved_chat_history():
    return [{"role": message["role"], "content": message["content"]} for message in st.session_state.messages]


def _render_saved_chat_history() -> None:
    engineer_mode = bool(st.session_state.get("engineer_mode", False))
    for index, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            st.markdown(sanitize_markdown_text(message["content"]))
            if message.get("tool_results"):
                render_tool_results(message["tool_results"], engineer_mode=engineer_mode)
            if message.get("retry_suggestions"):
                selected_retry = render_retry_question_suggestions(
                    message.get("source_user_input", ""),
                    message.get("content", ""),
                    key_prefix=f"saved_retry_{index}",
                    failure_type=message.get("failure_type", ""),
                )
                if selected_retry:
                    st.session_state.queued_user_input = selected_retry
                    st.rerun()


def _run_chat_turn(user_input: str, progress_callback=None):
    result = run_agent_with_progress(
        user_input=user_input,
        chat_history=_get_saved_chat_history(),
        context=st.session_state.context,
        current_data=st.session_state.current_data,
        progress_callback=progress_callback,
    )

    tool_results = result.get("tool_results", [])
    extracted_params = result.get("extracted_params", {})
    if tool_results:
        sync_context(extracted_params)

    st.session_state.current_data = result.get("current_data")
    return result


def _stream_response_text(text: str):
    safe_text = sanitize_markdown_text(text)
    for line in str(safe_text or "").splitlines(keepends=True):
        yield line


def _render_display_options() -> None:
    st.session_state.engineer_mode = st.toggle(
        "ENG'R 모드",
        value=bool(st.session_state.get("engineer_mode", False)),
        help="켜면 pandas 처리 요약과 생성된 코드를 함께 보여줍니다.",
    )


def _render_reset_controls() -> None:
    left_col, right_col = st.columns(2)

    with left_col:
        if st.button(
            "대화 초기화",
            use_container_width=True,
            help="대화 기록, 현재 결과, 기억 중인 조회 조건을 모두 지웁니다.",
        ):
            reset_chat_session(st.session_state)
            st.session_state.chat_reset_notice = "대화를 새로 시작했습니다. 이전 질문, 응답, 현재 데이터와 조회 조건을 모두 비웠습니다."
            st.rerun()

    with right_col:
        if st.button(
            "필터 초기화",
            use_container_width=True,
            disabled=not has_active_context(st.session_state.get("context")),
            help="기억 중인 조회 조건과 현재 결과 테이블만 지우고, 대화 기록은 유지합니다.",
        ):
            reset_filter_session(st.session_state)
            st.session_state.chat_reset_notice = "필터와 현재 결과 테이블을 초기화했습니다. 이전 대화 내용은 그대로 유지됩니다."
            st.rerun()

    st.caption("대화 초기화는 전체 흐름을 새로 시작할 때 사용합니다. 필터 초기화는 이전 질문에서 기억한 날짜/공정/MODE 같은 조건과 현재 결과만 지우고 싶을 때 사용합니다.")


def _render_navigation() -> str:
    with st.sidebar:
        st.markdown("## 메뉴")
        page = st.radio(
            "화면 선택",
            options=["채팅 분석", "도메인 관리"],
            index=0,
            label_visibility="collapsed",
        )
    return page


def _render_chat_page() -> None:
    st.title("제조 데이터 채팅 분석")
    st.caption("첫 질문에서 필요하면 바로 후처리까지 수행하고, 최종 응답과 함께 결과 테이블을 보여줍니다.")
    notice = str(st.session_state.get("chat_reset_notice", "") or "")
    if notice:
        st.success(notice)
        st.session_state.chat_reset_notice = ""
    _render_display_options()
    _render_reset_controls()
    render_domain_registry_summary_card()
    render_context()
    selected_example = render_question_guide_and_examples()
    if selected_example:
        st.session_state.queued_user_input = selected_example
        st.rerun()
    _render_saved_chat_history()

    queued_input = str(st.session_state.get("queued_user_input", "") or "")
    if queued_input:
        st.session_state.queued_user_input = ""

    user_input = st.chat_input("예: 오늘 DA공정에서 DDR5제품의 생산 달성율을 공정별로 알려줘")
    if not user_input and queued_input:
        user_input = queued_input
    if not user_input:
        return

    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(sanitize_markdown_text(user_input))

    with st.chat_message("assistant"):
        with st.status("질문을 분석하고 필요한 데이터를 찾는 중입니다.", expanded=True) as status:
            progress_placeholder = st.empty()
            progress_lines = []

            def _update_progress(title: str, detail: str) -> None:
                progress_lines.append(f"- **{title}**: {detail}")
                progress_placeholder.markdown("\n".join(progress_lines))

            result = _run_chat_turn(user_input, progress_callback=_update_progress)
            response = sanitize_markdown_text(result.get("response", "응답을 생성하지 못했습니다."))
            tool_results = result.get("tool_results", [])
            engineer_mode = bool(st.session_state.get("engineer_mode", False))
            if tool_results:
                st.write("데이터 조회와 후처리를 마쳤습니다.")
            else:
                st.write("응답 생성을 마쳤습니다.")
            status.update(label="처리 완료", state="complete", expanded=False)

        rendered_response = st.write_stream(_stream_response_text(response))
        if tool_results:
            render_tool_results(tool_results, engineer_mode=engineer_mode)
        failure_type = str(result.get("failure_type", "") or "")
        retry_suggestions = build_retry_question_suggestions(user_input, response, failure_type=failure_type)
        should_show_retry = bool(result.get("failure_type")) or any(
            token in response for token in ["찾을 수 없습니다", "병합", "N:M", "날짜", "실패", "없습니다"]
        )
        if should_show_retry:
            selected_retry = render_retry_question_suggestions(
                user_input,
                response,
                key_prefix=f"live_retry_{len(st.session_state.messages)}",
                failure_type=failure_type,
            )
            if selected_retry:
                st.session_state.queued_user_input = selected_retry
                st.rerun()
        else:
            retry_suggestions = []

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": sanitize_markdown_text(rendered_response if isinstance(rendered_response, str) else response),
            "tool_results": tool_results,
            "source_user_input": user_input,
            "failure_type": failure_type,
            "retry_suggestions": retry_suggestions if should_show_retry else [],
        }
    )


def main() -> None:
    init_session_state()
    page = _render_navigation()

    if page == "도메인 관리":
        render_domain_knowledge_page()
        return

    _render_chat_page()


if __name__ == "__main__":
    main()
