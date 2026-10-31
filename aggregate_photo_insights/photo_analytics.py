# -*- coding: utf-8 -*-
"""photo_grader - 모듈 3: pandas 기반 통계 및 시계열 분석.

파일명: photo_analytics.py
담당자: 하정윤 (아트서강)
"""
from typing import Any
import pandas as pd


def aggregate_photo_insights(df_analyses: pd.DataFrame) -> dict[str, Any]:
    """VLM 기반 사진 감성·구도 심층 비평 및 스마트 Culling 시스템의 사진 분석 레코드를 정제 및 집계합니다.

    사진의 종합 점수(final_score), 촬영 일시(captured_at), 분석 태그(tags)를 바탕으로
    유효 사진 총 건수, 월별 추이, 신뢰성 필터(count >= 2)가 적용된 상위/하위 태그 통계를 도출합니다.

    Args:
        df_analyses (pd.DataFrame): 사진 분석 레코드가 담긴 원본 데이터프레임.
            - 필수 열: ["id", "final_score", "captured_at", "tags"]
            - tags 열은 문자열 리스트(예: ["3분할_구도", "자연광"]) 형태여야 합니다.

    Returns:
        dict[str, Any]: 다음 구조의 단일 딕셔너리:
            {
                "total_photos": int,
                "monthly_trend": {
                    "YYYY-MM": {"count": int, "avg_score": float}
                },
                "top_tags": [
                    {"tag": str, "avg_score": float, "count": int}
                ],
                "bottom_tags": [
                    {"tag": str, "avg_score": float, "count": int}
                ]
            }

    Raises:
        ValueError: ["id", "final_score", "captured_at", "tags"] 중 누락된 열이 있을 경우 발생.
    """
    empty_contract: dict[str, Any] = {
        "total_photos": 0,
        "monthly_trend": {},
        "top_tags": [],
        "bottom_tags": [],
    }

    # 1. DataFrame None 및 Empty 방어
    if df_analyses is None or df_analyses.empty:
        return empty_contract

    # 2. 필수 열 누락 검증 (KeyError 방지)
    required_columns = ["id", "final_score", "captured_at", "tags"]
    missing_columns = [col for col in required_columns if col not in df_analyses.columns]
    if missing_columns:
        raise ValueError(f"데이터프레임 필수 열 누락: {', '.join(missing_columns)}")

    # 3. 원본 불변성 보장 및 메모리 최적화 (필요 4개 열만 복사)
    df = df_analyses[required_columns].copy()

    # 4. 결측치 및 점수 이상치 정제
    df["final_score"] = pd.to_numeric(df["final_score"], errors="coerce")
    df = df.dropna(subset=["final_score"])

    if df.empty:
        return empty_contract

    # 점수 클리핑 (0.0 ~ 10.0 범위 강제)
    df["final_score"] = df["final_score"].clip(lower=0.0, upper=10.0)
    total_photos = int(len(df))

    # 5. 월별 시계열 집계 (captured_at 파싱 및 명시적 컬럼 분리)
    captured_dt = pd.to_datetime(df["captured_at"], errors="coerce")
    valid_time_mask = captured_dt.notna()

    monthly_trend: dict[str, dict[str, Any]] = {}
    if valid_time_mask.any():
        df_time = df.loc[valid_time_mask].copy()
        df_time["year_month"] = captured_dt.loc[valid_time_mask].dt.strftime("%Y-%m")
        grouped_time = df_time.groupby("year_month")["final_score"].agg(["count", "mean"]).sort_index()

        monthly_trend = {
            str(period): {
                "count": int(row["count"]),
                "avg_score": round(float(row["mean"]), 2),
            }
            for period, row in grouped_time.iterrows()
        }

    # 6. 태그 심층 집계 (explode & 공백 정규화 & 신뢰성 필터링)
    df_tags = df[["final_score", "tags"]].explode("tags").dropna(subset=["tags"])

    # 태그 문자열 정규화: 앞뒤 공백 제거(strip) 및 유효 문자열 필터링
    df_tags["tags"] = df_tags["tags"].astype(str).str.strip()
    df_tags = df_tags[df_tags["tags"] != ""]

    top_tags: list[dict[str, Any]] = []
    bottom_tags: list[dict[str, Any]] = []

    if not df_tags.empty:
        tag_stats = (
            df_tags.groupby("tags")["final_score"]
            .agg(count="count", avg_score="mean")
            .reset_index()
        )

        # 최소 2회 이상 등장한 태그만 선별
        reliable_tags = tag_stats[tag_stats["count"] >= 2]

        if not reliable_tags.empty:
            # 상위 태그 (평균 점수 내림차순, 동점 시 등장 횟수 내림차순 정렬)
            top_records = reliable_tags.sort_values(
                by=["avg_score", "count"], ascending=[False, False]
            ).head(5)

            top_tags = [
                {
                    "tag": str(row["tags"]),
                    "avg_score": round(float(row["avg_score"]), 2),
                    "count": int(row["count"]),
                }
                for _, row in top_records.iterrows()
            ]

            # 하위 태그 (평균 점수 오름차순, 동점 시 등장 횟수 내림차순 정렬)
            bottom_records = reliable_tags.sort_values(
                by=["avg_score", "count"], ascending=[True, False]
            ).head(5)

            bottom_tags = [
                {
                    "tag": str(row["tags"]),
                    "avg_score": round(float(row["avg_score"]), 2),
                    "count": int(row["count"]),
                }
                for _, row in bottom_records.iterrows()
            ]

    return {
        "total_photos": total_photos,
        "monthly_trend": monthly_trend,
        "top_tags": top_tags,
        "bottom_tags": bottom_tags,
    }
