"""명세에서 먼저 작성한 정상·경계·예외 테스트. 모든 입력은 가상 데이터입니다."""

from datetime import date

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from clean_analysis_dataframe import clean_analysis_dataframe


def sample_frame(scores, dates=None):
    size = len(scores)
    return pd.DataFrame(
        {
            "id": list(range(1, size + 1)),
            "final_score": scores,
            "captured_at": dates if dates is not None else ["2026-10-01"] * size,
            "tags": [["대칭"] for _ in range(size)],
        }
    )


def test_normal_values_and_dates():
    raw = sample_frame([8.5, 6], ["2026-10-01", "2026-10-02 14:30:00"])
    result = clean_analysis_dataframe(raw)
    assert result["final_score"].tolist() == [8.5, 6.0]
    assert result["final_score"].dtype == "float64"
    assert result["captured_at"].tolist() == [
        pd.Timestamp("2026-10-01"), pd.Timestamp("2026-10-02 14:30:00")
    ]
    assert pd.api.types.is_datetime64_any_dtype(result["captured_at"])


def test_numeric_strings_and_score_clipping():
    result = clean_analysis_dataframe(sample_frame(["8.5", " 7 ", -2, 12]))
    assert result["final_score"].tolist() == [8.5, 7.0, 0.0, 10.0]


def test_missing_or_unusable_scores_are_removed_not_filled_with_zero():
    raw = sample_frame([None, pd.NA, float("nan"), "", "not-a-score", 0, 7])
    result = clean_analysis_dataframe(raw)
    assert result["id"].tolist() == [6, 7]
    assert result["final_score"].tolist() == [0.0, 7.0]


def test_invalid_or_missing_dates_keep_scored_rows():
    raw = sample_frame([8, 7, 6, 5], ["bad-date", None, "2026-02-30", "2026-10-01"])
    result = clean_analysis_dataframe(raw)
    assert len(result) == 4
    assert result["captured_at"].isna().tolist() == [True, True, True, False]


def test_original_input_extra_columns_tags_and_index_are_preserved():
    raw = sample_frame(["8.5", None, "12"])
    raw.index = [10, 20, 30]
    raw["memo"] = ["A", "B", "C"]
    raw["tags"] = [["대칭", "야경"], [], None]
    before = raw.copy(deep=True)
    result = clean_analysis_dataframe(raw)
    assert_frame_equal(raw, before)
    assert result is not raw
    assert result.index.tolist() == [10, 30]
    assert result.columns.tolist() == raw.columns.tolist()
    assert result["memo"].tolist() == ["A", "C"]
    assert result["tags"].tolist() == [["대칭", "야경"], None]
    assert "year_month" not in result.columns


@pytest.mark.parametrize("scores", [[0], [10], [0, 10]])
def test_inclusive_score_boundaries(scores):
    result = clean_analysis_dataframe(sample_frame(scores))
    assert result["final_score"].tolist() == [float(x) for x in scores]


def test_completely_empty_dataframe_gets_empty_standard_columns():
    raw = pd.DataFrame()
    result = clean_analysis_dataframe(raw)
    assert result.empty
    assert result.columns.tolist() == ["id", "final_score", "captured_at", "tags"]
    assert result["final_score"].dtype == "float64"
    assert pd.api.types.is_datetime64_any_dtype(result["captured_at"])
    assert raw.columns.empty


def test_empty_dataframe_with_schema_keeps_extra_columns():
    raw = sample_frame([])
    raw["memo"] = pd.Series(dtype="object")
    result = clean_analysis_dataframe(raw)
    assert result.empty
    assert result.columns.tolist() == raw.columns.tolist()


def test_all_scores_missing_returns_typed_empty_frame():
    result = clean_analysis_dataframe(sample_frame([None, "invalid"]))
    assert result.empty
    assert result["final_score"].dtype == "float64"
    assert pd.api.types.is_datetime64_any_dtype(result["captured_at"])


@pytest.mark.parametrize("raw", [None, [], {}, "dataframe", 123])
def test_non_dataframe_input_raises_type_error(raw):
    with pytest.raises(TypeError, match="DataFrame"):
        clean_analysis_dataframe(raw)


@pytest.mark.parametrize("column", ["id", "final_score", "captured_at", "tags"])
def test_missing_required_column_raises_value_error(column):
    raw = sample_frame([8]).drop(columns=column)
    with pytest.raises(ValueError, match=column):
        clean_analysis_dataframe(raw)


def test_empty_but_incomplete_schema_is_not_silently_fixed():
    with pytest.raises(ValueError, match="필수 열 누락"):
        clean_analysis_dataframe(pd.DataFrame(columns=["id"]))


def test_row_index_without_columns_raises_missing_columns_error():
    """행 인덱스가 있는 무열 입력은 완전히 빈 입력의 예외에 해당하지 않습니다."""
    raw = pd.DataFrame(index=[101, 102])
    with pytest.raises(ValueError, match="필수 열 누락") as error:
        clean_analysis_dataframe(raw)
    for column in ["id", "final_score", "captured_at", "tags"]:
        assert column in str(error.value)
    assert raw.shape == (2, 0)
    assert raw.index.tolist() == [101, 102]


def test_duplicate_column_names_are_rejected():
    raw = pd.concat([sample_frame([8]), pd.Series([6], name="final_score")], axis=1)
    with pytest.raises(ValueError, match="중복"):
        clean_analysis_dataframe(raw)


def test_boolean_infinite_and_complex_scores_are_not_valid_scores():
    raw = sample_frame(pd.Series([True, False, float("inf"), -float("inf"), 1+2j, 7], dtype="object"))
    result = clean_analysis_dataframe(raw)
    assert result["id"].tolist() == [6]
    assert result["final_score"].tolist() == [7.0]


def test_date_objects_and_timezone_keep_local_capture_month():
    raw = sample_frame([8, 9, 7], [date(2026, 10, 1), "2026-10-01T00:30:00+09:00", pd.Timestamp("2026-10-03")])
    result = clean_analysis_dataframe(raw)
    assert result["captured_at"].tolist() == [
        pd.Timestamp("2026-10-01"), pd.Timestamp("2026-10-01 00:30:00"), pd.Timestamp("2026-10-03")
    ]
    assert result["captured_at"].dt.tz is None


def test_numbers_are_not_inferred_as_unix_nanosecond_dates():
    result = clean_analysis_dataframe(sample_frame([8, 7, 6], [0, 20261001, True]))
    assert result["captured_at"].isna().all()


def test_repeated_cleaning_produces_same_result():
    once = clean_analysis_dataframe(sample_frame(["12", -1, "bad"], ["2026-10-01", None, "bad"]))
    assert_frame_equal(clean_analysis_dataframe(once), once)


def test_duplicate_row_indices_are_preserved():
    raw = sample_frame([None, 8, 12])
    raw.index = [1, 1, 2]
    result = clean_analysis_dataframe(raw)
    assert result.index.tolist() == [1, 2]
    assert result["final_score"].tolist() == [8.0, 10.0]


@pytest.mark.parametrize("value", ["now", "today", "01/02/2026", "3000-01-01", ""])
def test_ambiguous_relative_or_out_of_range_dates_become_nat(value):
    result = clean_analysis_dataframe(sample_frame([8], [value]))
    assert len(result) == 1
    assert pd.isna(result["captured_at"].iloc[0])
