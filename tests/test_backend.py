import math

import pandas as pd
import pytest

import backend
from backend import (
    REQUIRED_COLUMNS,
    filter_analyses,
    get_available_tags,
    parse_tags_column,
    prepare_uploaded_dataframe,
    summarize_photo_dashboard,
    validate_columns,
)


def make_raw_df():
    # 업로드 CSV를 읽은 직후처럼 태그가 다양한 문자열 형식인 원본을 만든다.
    return pd.DataFrame(
        {
            "id": ["a", "b", "c", "d", "e"],
            "final_score": [8.0, "6.5", 9.0, "invalid", 4.0],
            "captured_at": [
                "2026-01-10",
                "2026-01-20T10:00:00",
                "2026-02-05",
                "2026-02-06",
                "not-a-date",
            ],
            "tags": [
                '["자연풍경", "골든아워"]',
                "자연풍경, 인물",
                ["골든아워", " 자연풍경 "],
                "인물",
                None,
            ],
        }
    )


@pytest.fixture
def df_clean():
    return prepare_uploaded_dataframe(make_raw_df())


# ---------- 모듈 제약 ----------


def test_backend_does_not_import_streamlit():
    source = open(backend.__file__, encoding="utf-8").read()
    assert "import streamlit" not in source
    assert "from streamlit" not in source


def test_backend_reuses_existing_functions():
    assert backend.clean_analysis_dataframe.__module__ == (
        "clean_analysis_dataframe.clean_analysis_dataframe"
    )
    assert backend.aggregate_photo_insights.__module__ == (
        "aggregate_photo_insights.photo_analytics"
    )


def test_required_columns_contract():
    assert REQUIRED_COLUMNS == ["id", "final_score", "captured_at", "tags"]


# ---------- validate_columns ----------


def test_validate_columns_all_present():
    assert validate_columns(make_raw_df()) == []


def test_validate_columns_reports_missing_in_order():
    df = pd.DataFrame({"tags": [], "id": []})
    assert validate_columns(df) == ["final_score", "captured_at"]


def test_validate_columns_empty_dataframe():
    assert validate_columns(pd.DataFrame()) == REQUIRED_COLUMNS


# ---------- parse_tags_column ----------


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (["자연풍경", " 골든아워 "], ["자연풍경", "골든아워"]),
        (("자연풍경", "골든아워"), ["자연풍경", "골든아워"]),
        ('["자연풍경", "골든아워"]', ["자연풍경", "골든아워"]),
        ('[" 자연풍경 ", ""]', ["자연풍경"]),
        ("자연풍경, 골든아워", ["자연풍경", "골든아워"]),
        ("자연풍경,,골든아워, ", ["자연풍경", "골든아워"]),
        ("자연풍경", ["자연풍경"]),
        ("[깨진 JSON", ["[깨진 JSON"]),
        ("", []),
        ("   ", []),
        (None, []),
        (float("nan"), []),
        ([], []),
        ("[]", []),
        ('"자연풍경"', ["자연풍경"]),
        ('"자연풍경", "골든아워"', ["자연풍경", "골든아워"]),
        ('" 자연풍경 "', ["자연풍경"]),
        # 배열이 아닌 문자열은 따옴표로 감싸도 쉼표 분리 규칙을 따른다.
        ('"자연풍경, 골든아워"', ["자연풍경", "골든아워"]),
        ('"자연풍경, 골든아워", "인물"', ["자연풍경", "골든아워", "인물"]),
        # 명시적인 JSON 배열의 원소는 쉼표가 있어도 나누지 않는다.
        ('["자연풍경, 골든아워"]', ["자연풍경, 골든아워"]),
        ('"닫히지 않은 따옴표, 골든아워', ['"닫히지 않은 따옴표', "골든아워"]),
    ],
)
def test_parse_tags_column_formats(raw, expected):
    df = pd.DataFrame({"tags": [raw]})
    assert parse_tags_column(df)["tags"].iloc[0] == expected


def test_parse_tags_column_list_with_non_string_items():
    df = pd.DataFrame({"tags": [[1, None, " a "]]})
    assert parse_tags_column(df)["tags"].iloc[0] == ["1", "a"]


@pytest.mark.parametrize(
    "nested",
    [
        '[["자연풍경", "골든아워"], "인물"]',
        '[{"tag": "자연풍경"}]',
        [["자연풍경"], "인물"],
    ],
)
def test_parse_tags_column_nested_value_raises_readable_error(nested):
    df = pd.DataFrame({"tags": ["자연풍경", nested]})
    with pytest.raises(ValueError) as excinfo:
        parse_tags_column(df)
    message = str(excinfo.value)
    # 몇 번째 행인지, 무엇이 문제인지, 어떤 형식이어야 하는지를 모두 알려준다.
    assert "2번째 데이터 행" in message
    assert "중첩" in message
    assert "쉼표로 구분한 문자열" in message


def test_prepare_uploaded_dataframe_reports_nested_tags():
    df_raw = make_raw_df()
    df_raw.loc[0, "tags"] = '[["자연풍경"]]'
    with pytest.raises(ValueError, match="1번째 데이터 행"):
        prepare_uploaded_dataframe(df_raw)


def test_parse_tags_column_does_not_mutate_input():
    df = pd.DataFrame({"id": [1], "tags": ["a, b"]})
    result = parse_tags_column(df)
    assert df["tags"].iloc[0] == "a, b"
    assert result["tags"].iloc[0] == ["a", "b"]
    assert result is not df


def test_parse_tags_column_all_elements_are_str_lists():
    result = parse_tags_column(make_raw_df())
    for tags in result["tags"]:
        assert isinstance(tags, list)
        assert all(isinstance(tag, str) for tag in tags)


# ---------- prepare_uploaded_dataframe ----------


def test_prepare_uploaded_dataframe_missing_columns_raises():
    df = pd.DataFrame({"id": [1], "tags": ["a"]})
    with pytest.raises(ValueError, match="필수 컬럼 누락: final_score, captured_at"):
        prepare_uploaded_dataframe(df)


def test_prepare_uploaded_dataframe_cleans_and_parses(df_clean):
    # 점수가 'invalid'인 d 행만 제거된다.
    assert df_clean["id"].tolist() == ["a", "b", "c", "e"]
    assert df_clean["final_score"].tolist() == [8.0, 6.5, 9.0, 4.0]
    assert str(df_clean["captured_at"].dtype) == "datetime64[ns]"
    assert pd.isna(df_clean["captured_at"].iloc[3])
    assert df_clean["tags"].tolist() == [
        ["자연풍경", "골든아워"],
        ["자연풍경", "인물"],
        ["골든아워", "자연풍경"],
        [],
    ]


def test_prepare_uploaded_dataframe_does_not_mutate_input():
    raw = make_raw_df()
    snapshot = raw.copy()
    prepare_uploaded_dataframe(raw)
    pd.testing.assert_frame_equal(raw, snapshot)


def test_prepare_uploaded_dataframe_empty_rows_with_columns():
    raw = pd.DataFrame(columns=REQUIRED_COLUMNS)
    result = prepare_uploaded_dataframe(raw)
    assert result.empty
    assert list(result.columns) == REQUIRED_COLUMNS


# ---------- get_available_tags ----------


def test_get_available_tags_sorted_unique(df_clean):
    assert get_available_tags(df_clean) == ["전체", "골든아워", "인물", "자연풍경"]


def test_get_available_tags_empty_dataframe():
    assert get_available_tags(pd.DataFrame(columns=REQUIRED_COLUMNS)) == ["전체"]


def test_get_available_tags_without_tags_column():
    assert get_available_tags(pd.DataFrame({"id": [1]})) == ["전체"]


def test_get_available_tags_all_rows_without_tags():
    df = pd.DataFrame({"tags": [[], []]})
    assert get_available_tags(df) == ["전체"]


def test_get_available_tags_reserved_label_appears_once():
    # 데이터에 "전체"라는 태그가 있어도 선택지에는 맨 앞에 한 번만 나온다.
    df = pd.DataFrame({"tags": [["전체", "자연풍경"], ["전체"]]})
    assert get_available_tags(df) == ["전체", "자연풍경"]


# ---------- filter_analyses ----------


def test_filter_analyses_defaults_return_all(df_clean):
    result = filter_analyses(df_clean)
    pd.testing.assert_frame_equal(result, df_clean)
    assert result is not df_clean


def test_filter_analyses_min_score_inclusive(df_clean):
    result = filter_analyses(df_clean, min_score=8.0)
    assert result["id"].tolist() == ["a", "c"]


def test_filter_analyses_by_tag(df_clean):
    result = filter_analyses(df_clean, selected_tag="인물")
    assert result["id"].tolist() == ["b"]


def test_filter_analyses_by_score_and_tag(df_clean):
    result = filter_analyses(df_clean, min_score=7.0, selected_tag="자연풍경")
    assert result["id"].tolist() == ["a", "c"]


def test_filter_analyses_unknown_tag_returns_empty(df_clean):
    result = filter_analyses(df_clean, selected_tag="없는태그")
    assert result.empty
    assert list(result.columns) == list(df_clean.columns)


def test_filter_analyses_tag_is_exact_match(df_clean):
    # 부분 문자열("자연")로는 일치하지 않는다.
    assert filter_analyses(df_clean, selected_tag="자연").empty


def test_filter_analyses_does_not_mutate_input(df_clean):
    snapshot = df_clean.copy()
    result = filter_analyses(df_clean, min_score=5.0, selected_tag="골든아워")
    result.loc[result.index[0], "final_score"] = -1.0
    pd.testing.assert_frame_equal(df_clean, snapshot)


def test_filter_analyses_empty_dataframe():
    empty = prepare_uploaded_dataframe(pd.DataFrame(columns=REQUIRED_COLUMNS))
    result = filter_analyses(empty, min_score=5.0, selected_tag="인물")
    assert result.empty
    # (0, 0)도 .empty가 참이므로 열과 자료형이 남아 있는지 따로 확인한다.
    assert list(result.columns) == list(empty.columns)
    assert result.dtypes.tolist() == empty.dtypes.tolist()


def test_filter_analyses_keeps_columns_when_score_removes_all_rows(df_clean):
    # 점수 조건에서 0행이 된 뒤 태그 조건을 적용해도 열이 사라지면 안 된다.
    result = filter_analyses(df_clean, min_score=10.0, selected_tag="자연풍경")
    assert result.shape == (0, len(df_clean.columns))
    assert list(result.columns) == list(df_clean.columns)
    assert result.dtypes.tolist() == df_clean.dtypes.tolist()


def test_filter_analyses_empty_result_shape_is_same_for_all_and_tag(df_clean):
    by_all = filter_analyses(df_clean, min_score=10.0)
    by_tag = filter_analyses(df_clean, min_score=10.0, selected_tag="자연풍경")
    pd.testing.assert_frame_equal(by_all, by_tag)


# ---------- summarize_photo_dashboard ----------


def test_summarize_photo_dashboard_keys_and_types(df_clean):
    summary = summarize_photo_dashboard(df_clean)
    assert set(summary) == {
        "total_photos",
        "avg_score",
        "valid_date_count",
        "monthly_df",
        "tags_df",
        "insights",
    }
    assert isinstance(summary["total_photos"], int)
    assert isinstance(summary["avg_score"], float)
    assert isinstance(summary["valid_date_count"], int)
    assert isinstance(summary["monthly_df"], pd.DataFrame)
    assert isinstance(summary["tags_df"], pd.DataFrame)
    assert isinstance(summary["insights"], dict)


def test_summarize_photo_dashboard_values(df_clean):
    summary = summarize_photo_dashboard(df_clean)
    assert summary["total_photos"] == 4
    assert math.isclose(summary["avg_score"], round((8.0 + 6.5 + 9.0 + 4.0) / 4, 2))
    assert summary["valid_date_count"] == 3

    monthly_df = summary["monthly_df"]
    assert list(monthly_df.columns) == ["year_month", "count", "avg_score"]
    assert monthly_df["year_month"].tolist() == ["2026-01", "2026-02"]
    assert monthly_df["count"].tolist() == [2, 1]
    assert monthly_df["avg_score"].tolist() == [7.25, 9.0]


def test_summarize_photo_dashboard_tags_use_reliable_top_tags(df_clean):
    summary = summarize_photo_dashboard(df_clean)
    tags_df = summary["tags_df"]
    assert list(tags_df.columns) == ["tag", "avg_score", "count"]
    # 인물(1회)은 count >= 2 필터로 제외된다.
    assert tags_df["tag"].tolist() == ["골든아워", "자연풍경"]
    assert tags_df["count"].tolist() == [2, 3]
    assert tags_df["avg_score"].tolist() == [8.5, round((8.0 + 6.5 + 9.0) / 3, 2)]
    assert tags_df.to_dict("records") == summary["insights"]["top_tags"]


def test_summarize_photo_dashboard_insights_is_original(df_clean):
    summary = summarize_photo_dashboard(df_clean)
    assert set(summary["insights"]) == {
        "total_photos",
        "monthly_trend",
        "top_tags",
        "bottom_tags",
    }


def test_summarize_photo_dashboard_empty_dataframe():
    empty = prepare_uploaded_dataframe(pd.DataFrame(columns=REQUIRED_COLUMNS))
    summary = summarize_photo_dashboard(empty)
    assert summary["total_photos"] == 0
    assert summary["avg_score"] == 0.0
    assert summary["valid_date_count"] == 0
    assert summary["monthly_df"].empty
    assert list(summary["monthly_df"].columns) == ["year_month", "count", "avg_score"]
    assert summary["tags_df"].empty
    assert list(summary["tags_df"].columns) == ["tag", "avg_score", "count"]


def test_summarize_photo_dashboard_no_valid_dates_or_tags():
    df = prepare_uploaded_dataframe(
        pd.DataFrame(
            {
                "id": [1, 2],
                "final_score": [5.0, 7.0],
                "captured_at": [None, "bad"],
                "tags": ["", None],
            }
        )
    )
    summary = summarize_photo_dashboard(df)
    assert summary["total_photos"] == 2
    assert summary["avg_score"] == 6.0
    assert summary["valid_date_count"] == 0
    assert summary["monthly_df"].empty
    assert summary["tags_df"].empty


def test_summarize_after_filter_reflects_subset(df_clean):
    summary = summarize_photo_dashboard(
        filter_analyses(df_clean, selected_tag="골든아워")
    )
    assert summary["total_photos"] == 2
    assert summary["avg_score"] == 8.5
