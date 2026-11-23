# -*- coding: utf-8 -*-
"""12주차 사진 평가 AI 대시보드 (Streamlit UI · 상태 관리 · Mock 챗봇 전담 모듈).

실행:
    streamlit run app.py
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from backend import (
    ALL_TAGS,
    REQUIRED_COLUMNS,
    TAG_GLOSSARY,
    assign_cut_grades,
    count_dropped_rows,
    filter_analyses,
    get_ai_reply,
    get_available_tags,
    prepare_uploaded_dataframe,
    summarize_cut_counts,
    summarize_photo_dashboard,
    validate_columns,
)

DEFAULT_A_CUTOFF = 8.0
DEFAULT_B_CUTOFF = 6.0
INITIAL_ASSISTANT_MESSAGE = (
    "안녕하세요! 업로드된 사진 분석 요약(A컷/B컷 현황, 평균 점수, 감성 태그)을 바탕으로 "
    "선별 기준이나 아쉬운 컷 정리 방법을 질문해 주세요."
)


def _read_csv_with_cp949_fallback(uploaded_file) -> tuple[pd.DataFrame, str]:
    """UTF-8로 CSV를 읽고 실패 시 파일 포인터를 되돌려 CP949로 재시도한다."""
    uploaded_file.seek(0)
    try:
        return pd.read_csv(uploaded_file), "utf-8"
    except UnicodeDecodeError:
        uploaded_file.seek(0)
        return pd.read_csv(uploaded_file, encoding="cp949"), "cp949"


def _reset_session_data() -> None:
    """오류 발생 또는 업로드 해제 시 보관된 분석·필터 상태를 초기화한다."""
    st.session_state.prepared_df = None
    st.session_state.uploaded_file_sig = None
    st.session_state.dropped_row_count = 0
    st.session_state.encoding_used = "utf-8"
    st.session_state.pop("min_score_filter", None)
    st.session_state.pop("tag_filter", None)
    st.session_state.pop("a_cutoff_filter", None)
    st.session_state.pop("b_cutoff_filter", None)


def _init_session_state() -> None:
    """Rerun 간 유지할 모든 session_state 키를 최초 1회만 초기화한다."""
    if "prepared_df" not in st.session_state:
        st.session_state.prepared_df = None
    if "uploaded_file_sig" not in st.session_state:
        st.session_state.uploaded_file_sig = None
    if "dropped_row_count" not in st.session_state:
        st.session_state.dropped_row_count = 0
    if "encoding_used" not in st.session_state:
        st.session_state.encoding_used = "utf-8"
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": INITIAL_ASSISTANT_MESSAGE}
        ]


def _reset_chat_messages() -> None:
    """대화 내역만 초기 인사말 상태로 되돌린다."""
    st.session_state.messages = [
        {"role": "assistant", "content": INITIAL_ASSISTANT_MESSAGE}
    ]


def main() -> None:
    st.set_page_config(page_title="사진 평가 AI 대시보드", layout="wide")
    st.title("사진 평가 AI 분석 대시보드")
    st.caption(
        "업로드된 사진 분석 CSV를 바탕으로 A컷/B컷 선별, 점수 추이, 감성 태그 인사이트를 제공합니다."
    )

    # [session_state 1단계: 초기화]
    _init_session_state()

    # 1. 입력: CSV 드래그 앤 드롭 업로드 (미업로드 시 st.stop()으로 안전 대기)
    uploaded = st.file_uploader("사진 분석 CSV 파일을 드래그 앤 드롭하세요", type=["csv"])
    if uploaded is None:
        _reset_session_data()
        st.info("CSV 파일을 업로드하면 사진 평가 대시보드와 AI Culling Q&A가 시작됩니다.")
        st.stop()

    # 2. 처리 및 session_state 쓰기: 파일이 변경된 경우에만 읽기/정제 수행
    file_sig = (getattr(uploaded, "file_id", None), uploaded.name, uploaded.size)
    if st.session_state.uploaded_file_sig != file_sig or st.session_state.prepared_df is None:
        try:
            df_raw, encoding_used = _read_csv_with_cp949_fallback(uploaded)
        except (UnicodeDecodeError, pd.errors.EmptyDataError, pd.errors.ParserError, ValueError, OSError) as exc:
            _reset_session_data()
            st.error(
                f"CSV 파일을 읽을 수 없습니다: {exc}. "
                "비어 있지 않은 UTF-8 또는 CP949 형식의 CSV 파일인지 확인해 주세요."
            )
            st.stop()

        missing = validate_columns(df_raw)
        if missing:
            _reset_session_data()
            st.error(
                f"필수 컬럼이 없습니다: {missing}. "
                f"다음 컬럼을 모두 포함한 CSV를 업로드해 주세요: {REQUIRED_COLUMNS}"
            )
            st.stop()

        try:
            df_cleaned = prepare_uploaded_dataframe(df_raw)
        except (TypeError, ValueError) as exc:
            _reset_session_data()
            st.error(f"데이터 정제 중 오류가 발생했습니다: {exc}")
            st.stop()

        st.session_state.prepared_df = df_cleaned
        st.session_state.uploaded_file_sig = file_sig
        st.session_state.dropped_row_count = count_dropped_rows(df_raw, df_cleaned)
        st.session_state.encoding_used = encoding_used
        st.session_state.pop("min_score_filter", None)
        st.session_state.pop("tag_filter", None)
        st.session_state.pop("a_cutoff_filter", None)
        st.session_state.pop("b_cutoff_filter", None)
        _reset_chat_messages()

    # [session_state 2단계: 읽기] Rerun 시 보관된 정제 DataFrame 재사용
    df_clean = st.session_state.prepared_df
    if df_clean is None:
        st.stop()

    # 방어적 UX 경고 배너
    if st.session_state.encoding_used == "cp949":
        st.warning("CP949 인코딩으로 감지하여 읽었습니다. (UTF-8 저장을 권장합니다)")
    if st.session_state.dropped_row_count > 0:
        st.warning(
            f"점수 누락·형식 오류 행 {st.session_state.dropped_row_count}건을 제외하고 분석했습니다."
        )
    if df_clean.empty:
        st.warning("유효한 점수 데이터가 포함된 행이 없습니다. CSV의 final_score 값을 확인해 주세요.")

    # 3. 사이드바 필터 (A/B컷 기준, 최소 점수, 1클릭 태그 pills)
    st.sidebar.header("A컷/B컷 선별 기준")
    raw_a_cutoff = st.sidebar.slider(
        "A컷 기준 점수 (이상)",
        min_value=0.0,
        max_value=10.0,
        value=DEFAULT_A_CUTOFF,
        step=0.5,
        key="a_cutoff_filter",
    )
    raw_b_cutoff = st.sidebar.slider(
        "B컷 기준 점수 (이상)",
        min_value=0.0,
        max_value=10.0,
        value=DEFAULT_B_CUTOFF,
        step=0.5,
        key="b_cutoff_filter",
    )

    if raw_a_cutoff <= raw_b_cutoff:
        st.sidebar.warning(
            "A컷 기준은 B컷 기준보다 높아야 합니다. 기본값(8.0 / 6.0)으로 적용합니다."
        )
        a_cutoff, b_cutoff = DEFAULT_A_CUTOFF, DEFAULT_B_CUTOFF
    else:
        a_cutoff, b_cutoff = raw_a_cutoff, raw_b_cutoff

    st.sidebar.divider()
    st.sidebar.header("분석 필터")
    available_tags = get_available_tags(df_clean)
    if (
        "tag_filter" in st.session_state
        and st.session_state.tag_filter is not None
        and st.session_state.tag_filter not in available_tags
    ):
        st.session_state.tag_filter = ALL_TAGS

    min_score = st.sidebar.slider(
        "최소 종합 점수",
        min_value=0.0,
        max_value=10.0,
        value=0.0,
        step=0.5,
        key="min_score_filter",
    )
    picked_tag = st.sidebar.pills(
        "감성 태그 선택",
        options=available_tags,
        default=ALL_TAGS,
        selection_mode="single",
        key="tag_filter",
    )
    selected_tag = picked_tag or ALL_TAGS

    if selected_tag != ALL_TAGS and selected_tag in TAG_GLOSSARY:
        st.sidebar.caption(f"선택 태그 의미: {TAG_GLOSSARY[selected_tag]}")

    # 4. 백엔드 호출: 필터링 → A/B컷 등급 부여 → KPI/차트 집계
    df_filtered = filter_analyses(df_clean, min_score=min_score, selected_tag=selected_tag)
    df_graded = assign_cut_grades(df_filtered, a_cutoff=a_cutoff, b_cutoff=b_cutoff)
    cut_counts = summarize_cut_counts(df_graded)
    summary = summarize_photo_dashboard(df_filtered)

    tab_dashboard, tab_chat = st.tabs(["📊 대시보드 분석", "💬 AI Culling Q&A"])

    with tab_dashboard:
        st.caption(
            f"현재 선별 기준 — A컷: {a_cutoff:.1f}점 이상 | "
            f"B컷: {b_cutoff:.1f}점 ~ {a_cutoff:.1f}점 미만 | "
            f"보류: {b_cutoff:.1f}점 미만"
        )

        col1, col2, col3, col4, col5, col6 = st.columns(6)
        col1.metric("필터링된 사진 수", f"{summary['total_photos']:,}장")
        col2.metric(
            "평균 종합 점수",
            "-" if summary["total_photos"] == 0 else f"{summary['avg_score']:.2f}점",
        )
        col3.metric("A컷 수", f"{cut_counts['A컷']:,}장")
        col4.metric("B컷 수", f"{cut_counts['B컷']:,}장")
        col5.metric("보류 수", f"{cut_counts['보류']:,}장")
        col6.metric("촬영일 유효 건수", f"{summary['valid_date_count']:,}건")

        chart_col1, chart_col2 = st.columns(2)
        with chart_col1:
            st.subheader("월별 평균 점수 추이")
            monthly_df = summary["monthly_df"]
            if monthly_df.empty:
                st.info("표시할 월별 추이 데이터가 없습니다.")
            else:
                st.line_chart(monthly_df, x="year_month", y="avg_score")

        with chart_col2:
            st.subheader(
                "상위 감성 태그 평균 점수 (최대 5개, 2회 이상)",
                help="나의 강점 분석용 차트로, 최소 2회 이상 등장한 태그의 평균 점수를 보여줍니다.",
            )
            tags_df = summary["tags_df"]
            if tags_df.empty:
                st.info("2회 이상 등장한 태그가 없습니다.")
            else:
                st.bar_chart(tags_df, x="tag", y="avg_score")
            st.caption(
                "나의 강점 분석 — 최소 2회 이상 등장한 감성 태그의 평균 점수 TOP 5입니다."
            )

        with st.expander("감성 태그 의미 가이드"):
            if selected_tag != ALL_TAGS and selected_tag in TAG_GLOSSARY:
                st.info(f"**{selected_tag}**: {TAG_GLOSSARY[selected_tag]}")
            for tag_name, description in TAG_GLOSSARY.items():
                st.markdown(f"- **{tag_name}**: {description}")

        st.subheader("상세 분석 및 A/B컷 판정 목록")
        st.dataframe(df_graded)

    with tab_chat:
        chat_header_col, chat_reset_col = st.columns([5, 1])
        with chat_header_col:
            st.subheader("AI Culling Q&A 어시스턴트 (Mock)")
            st.caption(
                "현재 필터링된 사진 집계를 바탕으로 질의응답을 제공합니다. "
                "(12주차 Mock 모드 · 13주차 실제 LLM API 연동 지점)"
            )
        with chat_reset_col:
            st.button("대화 초기화", on_click=_reset_chat_messages)

        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

        if prompt := st.chat_input("A컷 선별 기준이나 감성 태그에 대해 질문해 보세요"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.write(prompt)

            summary_context = {
                "total_photos": summary["total_photos"],
                "avg_score": summary["avg_score"],
                "a_cut_count": cut_counts["A컷"],
                "b_cut_count": cut_counts["B컷"],
                "top_tags": summary["insights"].get("top_tags", []),
            }
            reply = get_ai_reply(
                st.session_state.messages,
                summary_context=summary_context,
            )
            st.session_state.messages.append({"role": "assistant", "content": reply})
            with st.chat_message("assistant"):
                st.write(reply)


if __name__ == "__main__":
    main()
