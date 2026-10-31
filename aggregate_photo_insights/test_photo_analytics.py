# -*- coding: utf-8 -*-
"""photo_grader - 모듈 3 단위 테스트.

파일명: test_photo_analytics.py
대응 함수: aggregate_photo_insights (T09, T10, T11, T12 및 리딩 개선점 검증)
"""
import pytest
import pandas as pd
import numpy as np
from photo_analytics import aggregate_photo_insights


def test_t09_normal_case_100_photos():
    """T09 정상: 100건 사진 데이터 집계 및 Top/Bottom 5 태그 도출 검증."""
    np.random.seed(42)
    sample_tags = [["3분할_구도", "자연광"], ["소실점", "역광"], ["의도적_보케", "따뜻한_색조"], ["빛_부족", "흔들림"]]
    
    df_100 = pd.DataFrame({
        "id": range(1, 101),
        "final_score": np.random.uniform(3.0, 9.8, 100),
        "captured_at": pd.date_range("2026-08-01", periods=100, freq="D"),
        "tags": [sample_tags[i % len(sample_tags)] for i in range(100)],
        "heavy_metadata": ["x" * 1000 for _ in range(100)]  # 무거운 메타데이터 컬럼
    })
    
    result = aggregate_photo_insights(df_100)
    
    assert result["total_photos"] == 100
    assert len(result["top_tags"]) <= 5
    assert len(result["bottom_tags"]) <= 5
    for t in result["top_tags"]:
        assert t["count"] >= 2
    assert result["top_tags"][0]["avg_score"] >= result["bottom_tags"][0]["avg_score"]


def test_t10_normal_case_3_months_trend():
    """T10 정상: 2026년 8월~10월 3개월간 월별 시계열 평균 추이 집계 검증."""
    df_3m = pd.DataFrame({
        "id": [1, 2, 3, 4],
        "final_score": [8.0, 9.0, 7.0, 6.0],
        "captured_at": ["2026-08-15 14:00:00", "2026-08-20 10:00:00", "2026-09-10 12:00:00", "2026-10-05 18:00:00"],
        "tags": [["자연광"], ["자연광"], ["역광"], ["역광"]]
    })
    
    result = aggregate_photo_insights(df_3m)
    trend = result["monthly_trend"]
    
    assert "2026-08" in trend
    assert "2026-09" in trend
    assert "2026-10" in trend
    assert trend["2026-08"]["count"] == 2
    assert trend["2026-08"]["avg_score"] == 8.5
    assert trend["2026-09"]["avg_score"] == 7.0
    assert trend["2026-10"]["avg_score"] == 6.0


def test_t11_boundary_empty_and_single():
    """T11 경계: 빈 DataFrame 및 단 1장 입력 시 기본 반환 규격 준수."""
    # 1. 빈 DataFrame
    empty_res = aggregate_photo_insights(pd.DataFrame())
    assert empty_res == {"total_photos": 0, "monthly_trend": {}, "top_tags": [], "bottom_tags": []}

    # 2. None 전달
    assert aggregate_photo_insights(None) == {"total_photos": 0, "monthly_trend": {}, "top_tags": [], "bottom_tags": []}

    # 3. 1장 데이터 (등장 횟수 1회이므로 top/bottom 태그는 빈 리스트여야 함)
    df_single = pd.DataFrame({
        "id": [1],
        "final_score": [8.8],
        "captured_at": ["2026-09-01"],
        "tags": [["희귀_태그"]]
    })
    single_res = aggregate_photo_insights(df_single)
    assert single_res["total_photos"] == 1
    assert single_res["top_tags"] == []
    assert single_res["bottom_tags"] == []


def test_t12_exceptional_missing_column():
    """T12 예외: 필수 열(final_score, tags 등) 누락 시 ValueError 발생."""
    df_missing_score = pd.DataFrame({
        "id": [1, 2],
        "captured_at": ["2026-08-01", "2026-08-02"],
        "tags": [["빛"], ["구도"]]
    })
    with pytest.raises(ValueError, match="데이터프레임 필수 열 누락"):
        aggregate_photo_insights(df_missing_score)


def test_tag_whitespace_normalization():
    """리딩 검증: 태그 앞뒤 공백(strip) 정규화로 인한 카운트 합산 검증."""
    df_ws = pd.DataFrame({
        "id": [1, 2],
        "final_score": [9.0, 9.0],
        "captured_at": ["2026-08-01", "2026-08-02"],
        "tags": [[" 자연광 "], ["자연광"]]  # 공백이 섞인 동일 태그
    })
    result = aggregate_photo_insights(df_ws)
    # 정규화되어 count 2로 합산되므로 Top 5에 정상 진입해야 함
    assert len(result["top_tags"]) == 1
    assert result["top_tags"][0]["tag"] == "자연광"
    assert result["top_tags"][0]["count"] == 2


def test_edge_score_clipping_and_immutability():
    """추가 심화: 원본 불변성 유지 및 점수 이상치(0~10) 클리핑 검증."""
    df_original = pd.DataFrame({
        "id": [1, 2],
        "final_score": [-3.5, 12.0],
        "captured_at": ["2026-08-01", "2026-08-02"],
        "tags": [["태그A"], ["태그A"]]
    })
    df_copy = df_original.copy()

    result = aggregate_photo_insights(df_original)

    # 원본 불변성 검증
    pd.testing.assert_frame_equal(df_original, df_copy)
    # 클리핑 검증: (-3.5 -> 0.0, 12.0 -> 10.0 => 평균 5.0)
    assert result["top_tags"][0]["avg_score"] == 5.0
