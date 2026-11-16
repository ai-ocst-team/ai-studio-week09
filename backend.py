"""11주차 Streamlit 대시보드용 백엔드 어댑터.

Streamlit에 의존하지 않는 순수 pandas 함수만 제공합니다.
데이터 정제와 통계 집계는 기존 모듈 함수를 그대로 호출합니다.
"""

from __future__ import annotations

import json
from typing import Any

import pandas as pd

from aggregate_photo_insights.photo_analytics import aggregate_photo_insights
from clean_analysis_dataframe.clean_analysis_dataframe import clean_analysis_dataframe

REQUIRED_COLUMNS = ["id", "final_score", "captured_at", "tags"]
ALL_TAGS = "전체"

MONTHLY_COLUMNS = ["year_month", "count", "avg_score"]
TAG_COLUMNS = ["tag", "avg_score", "count"]


def validate_columns(df: pd.DataFrame) -> list[str]:
    """REQUIRED_COLUMNS 중 df에 없는 열 이름을 순서대로 반환합니다."""
    return [column for column in REQUIRED_COLUMNS if column not in df.columns]


def _clean_tag_items(items: Any) -> list[str]:
    """반복 가능한 태그 묶음을 공백 제거된 비어 있지 않은 문자열 리스트로 바꿉니다."""
    result: list[str] = []
    for item in items:
        if item is None:
            continue
        if isinstance(item, (list, tuple, set, dict)):
            # 태그 하나가 들어갈 자리에 묶음이 있으면 어느 태그인지 정할 수 없습니다.
            raise ValueError(
                f"태그 자리에 배열이나 객체가 중첩되어 있습니다({item!r}). "
                '태그는 ["자연풍경", "골든아워"]처럼 한 단계 배열이거나 '
                "쉼표로 구분한 문자열이어야 합니다."
            )
        if not isinstance(item, str) and pd.isna(item):
            continue
        text = str(item).strip()
        if text:
            result.append(text)
    return result


def _parse_json_tags(text: str) -> list | None:
    """JSON 배열로 읽을 수 있는 문자열이면 리스트를, 아니면 None을 반환합니다."""
    is_array = text.startswith("[")
    if is_array:
        candidate = text
    elif text.startswith('"'):
        # '"자연풍경"', '"자연풍경", "골든아워"'처럼 따옴표로 감싼 값은
        # 대괄호를 씌워 JSON 배열로 읽어야 따옴표가 태그에 남지 않습니다.
        candidate = f"[{text}]"
    else:
        return None
    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError:
        return None
    if not isinstance(parsed, list):
        return None
    if is_array:
        return parsed

    # 배열이 아닌 문자열은 쉼표로 나누는 규칙이므로, 따옴표만 벗긴 뒤에도
    # '"자연풍경, 골든아워"' 안의 쉼표는 태그 구분자로 봅니다.
    items: list = []
    for item in parsed:
        items.extend(item.split(",") if isinstance(item, str) else [item])
    return items


def _normalize_tags(value: Any) -> list[str]:
    """tags 셀 하나를 list[str]로 정규화합니다."""
    if isinstance(value, (list, tuple)):
        return _clean_tag_items(value)
    if value is None:
        return []
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return []
        parsed = _parse_json_tags(text)
        if parsed is not None:
            return _clean_tag_items(parsed)
        return _clean_tag_items(text.split(","))
    if pd.isna(value):
        return []
    return _clean_tag_items([value])


def parse_tags_column(df: pd.DataFrame) -> pd.DataFrame:
    """df를 복사한 뒤 tags 열의 각 원소를 list[str]로 정규화해 반환합니다."""
    result = df.copy()
    parsed: list[list[str]] = []
    for row_number, value in enumerate(result["tags"].tolist(), start=1):
        try:
            parsed.append(_normalize_tags(value))
        except ValueError as exc:
            raise ValueError(
                f"tags 열의 {row_number}번째 데이터 행을 읽을 수 없습니다: {exc}"
            ) from exc
    result["tags"] = parsed
    return result


def prepare_uploaded_dataframe(df_raw: pd.DataFrame) -> pd.DataFrame:
    """업로드된 원본 DataFrame을 검증·태그 파싱·정제해 반환합니다."""
    missing = validate_columns(df_raw)
    if missing:
        raise ValueError(f"필수 컬럼 누락: {', '.join(missing)}")
    return clean_analysis_dataframe(parse_tags_column(df_raw))


def get_available_tags(df_clean: pd.DataFrame) -> list[str]:
    """선택 가능한 태그 목록을 "전체" + 가나다순 고유 태그로 반환합니다."""
    if df_clean.empty or "tags" not in df_clean.columns:
        return [ALL_TAGS]
    unique_tags = {
        tag
        for tags in df_clean["tags"].tolist()
        if isinstance(tags, (list, tuple))
        for tag in tags
        if isinstance(tag, str) and tag
    }
    # "전체"는 필터 해제를 뜻하는 예약어이므로 실제 태그와 겹쳐도 한 번만 넣습니다.
    unique_tags.discard(ALL_TAGS)
    return [ALL_TAGS, *sorted(unique_tags)]


def filter_analyses(
    df_clean: pd.DataFrame,
    min_score: float = 0.0,
    selected_tag: str = ALL_TAGS,
) -> pd.DataFrame:
    """최소 점수와 선택 태그 조건을 만족하는 행만 복사해 반환합니다."""
    result = df_clean[df_clean["final_score"] >= min_score]
    if selected_tag != ALL_TAGS:
        has_tag = [
            isinstance(tags, (list, tuple)) and selected_tag in tags
            for tags in result["tags"].tolist()
        ]
        # result[has_tag]는 빈 리스트를 "열 0개 선택"으로 해석하므로 행 선택임을 명시합니다.
        result = result.loc[has_tag]
    return result.copy()


def summarize_photo_dashboard(df_clean: pd.DataFrame) -> dict[str, Any]:
    """대시보드 지표와 표용 DataFrame을 고정 키 딕셔너리로 반환합니다."""
    insights = aggregate_photo_insights(df_clean)

    if df_clean.empty:
        avg_score = 0.0
        valid_date_count = 0
    else:
        avg_score = round(float(df_clean["final_score"].mean()), 2)
        valid_date_count = int(df_clean["captured_at"].notna().sum())

    monthly_rows = [
        {"year_month": year_month, "count": stats["count"], "avg_score": stats["avg_score"]}
        for year_month, stats in insights["monthly_trend"].items()
    ]
    monthly_df = pd.DataFrame(monthly_rows, columns=MONTHLY_COLUMNS)
    tags_df = pd.DataFrame(insights["top_tags"], columns=TAG_COLUMNS)

    return {
        "total_photos": int(insights["total_photos"]),
        "avg_score": avg_score,
        "valid_date_count": valid_date_count,
        "monthly_df": monthly_df,
        "tags_df": tags_df,
        "insights": insights,
    }
