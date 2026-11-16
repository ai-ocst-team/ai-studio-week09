# -*- coding: utf-8 -*-
"""11주차 사진 평가 AI 대시보드 (Streamlit UI 전담 모듈).

실행:
    streamlit run app.py
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from backend import (
    REQUIRED_COLUMNS,
    filter_analyses,
    get_available_tags,
    prepare_uploaded_dataframe,
    summarize_photo_dashboard,
    validate_columns,
)


def _read_csv_with_cp949_fallback(uploaded_file) -> pd.DataFrame:
    """UTF-8로 CSV를 읽고 실패 시 파일 포인터를 되돌려 CP949로 재시도한다."""
    uploaded_file.seek(0)
    try:
        return pd.read_csv(uploaded_file)
    except UnicodeDecodeError:
        uploaded_file.seek(0)
        return pd.read_csv(uploaded_file, encoding="cp949")


def _reset_session_data() -> None:
    """오류 발생 또는 업로드 해제 시 보관된 분석 상태를 초기화한다."""
    st.session_state.prepared_df = None
    st.session_state.uploaded_file_sig = None
    st.session_state.pop("min_score_filter", None)
    st.session_state.pop("tag_filter", None)


def main() -> None:
    st.set_page_config(page_title="사진 평가 AI 대시보드", layout="wide")
    st.title("사진 평가 AI 분석 대시보드")
    st.caption("업로드된 사진 분석 CSV를 바탕으로 점수 추이·태그별 인사이트를 시각화합니다.")

    # [session_state 1단계: 초기화] Rerun 간 유지할 상태 키를 최초 1회만 준비
    if "prepared_df" not in st.session_state:
        st.session_state.prepared_df = None
    if "uploaded_file_sig" not in st.session_state:
        st.session_state.uploaded_file_sig = None

    # 1. 입력: CSV 드래그 앤 드롭 업로드 (미업로드 시 st.stop()으로 중단)
    uploaded = st.file_uploader("사진 분석 CSV 파일을 드래그 앤 드롭하세요", type=["csv"])
    if uploaded is None:
        _reset_session_data()
        st.info("CSV 파일을 업로드하면 사진 평가 대시보드 분석이 시작됩니다.")
        st.stop()

    # 2. 처리 및 session_state 3단계(쓰기): 동일 파일 Rerun 시 재파싱·재정제 생략
    file_sig = (getattr(uploaded, "file_id", None), uploaded.name, uploaded.size)
    if st.session_state.uploaded_file_sig != file_sig or st.session_state.prepared_df is None:
        try:
            df_raw = _read_csv_with_cp949_fallback(uploaded)
        except (UnicodeDecodeError, pd.errors.EmptyDataError, pd.errors.ParserError, ValueError, OSError) as exc:
            _reset_session_data()
            st.error(f"CSV 파일을 읽을 수 없습니다: {exc}")
            st.stop()

        missing = validate_columns(df_raw)
        if missing:
            _reset_session_data()
            st.error(f"필수 컬럼이 없습니다: {missing}. 필요 컬럼: {REQUIRED_COLUMNS}")
            st.stop()

        try:
            st.session_state.prepared_df = prepare_uploaded_dataframe(df_raw)
        except (TypeError, ValueError) as exc:
            _reset_session_data()
            st.error(f"데이터 정제 중 오류가 발생했습니다: {exc}")
            st.stop()

        st.session_state.uploaded_file_sig = file_sig
        st.session_state.pop("min_score_filter", None)
        st.session_state.pop("tag_filter", None)

    # [session_state 2단계: 읽기] Rerun 시 보관된 정제 DataFrame 재사용
    df_clean = st.session_state.prepared_df
    if df_clean is None:
        st.stop()

    if df_clean.empty:
        st.warning("유효한 점수 데이터가 포함된 행이 없습니다.")

    # 3. 사이드바 필터 (조작 시 즉시 Rerun 반영)
    st.sidebar.header("분석 필터")
    available_tags = get_available_tags(df_clean)
    if "tag_filter" in st.session_state and st.session_state.tag_filter not in available_tags:
        st.session_state.tag_filter = "전체"

    min_score = st.sidebar.slider(
        "최소 종합 점수",
        min_value=0.0,
        max_value=10.0,
        value=0.0,
        step=0.5,
        key="min_score_filter",
    )
    selected_tag = st.sidebar.selectbox(
        "감성 태그 선택",
        options=available_tags,
        key="tag_filter",
    )

    df_filtered = filter_analyses(df_clean, min_score=min_score, selected_tag=selected_tag)
    summary = summarize_photo_dashboard(df_filtered)

    # 4. 출력: KPI -> 차트 -> 상세 표
    col1, col2, col3 = st.columns(3)
    col1.metric("필터링된 사진 수", f"{summary['total_photos']:,}장")
    col2.metric(
        "평균 종합 점수",
        "-" if summary["total_photos"] == 0 else f"{summary['avg_score']:.2f}점",
    )
    col3.metric("촬영일 유효 건수", f"{summary['valid_date_count']:,}건")

    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        st.subheader("월별 평균 점수 추이")
        monthly_df = summary["monthly_df"]
        if monthly_df.empty:
            st.info("표시할 월별 추이 데이터가 없습니다.")
        else:
            st.line_chart(monthly_df, x="year_month", y="avg_score")

    with chart_col2:
        st.subheader("상위 감성 태그 평균 점수 (최대 5개, 2회 이상)")
        tags_df = summary["tags_df"]
        if tags_df.empty:
            st.info("2회 이상 등장한 태그가 없습니다.")
        else:
            st.bar_chart(tags_df, x="tag", y="avg_score")

    st.subheader("상세 분석 목록")
    st.dataframe(df_filtered)


if __name__ == "__main__":
    main()
