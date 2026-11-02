"""사진 분석 데이터 정제 함수입니다."""

from datetime import date, datetime
from decimal import Decimal
import math
import numbers
import re

import pandas as pd


def _clean_score(value: object) -> float | None:
    """유한한 점수만 0~10 범위의 float로 변환합니다."""
    if pd.api.types.is_bool(value):
        return None
    if isinstance(value, numbers.Complex) and not isinstance(value, numbers.Real):
        return None

    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None
    elif not isinstance(value, (numbers.Number, Decimal)):
        return None

    try:
        score = float(value)
    except (TypeError, ValueError, OverflowError):
        return None

    if not math.isfinite(score):
        return None
    return min(10.0, max(0.0, score))


def _clean_captured_at(value: object) -> pd.Timestamp | None:
    """허용된 날짜 입력을 시간대 없는 datetime64[ns] 범위로 변환합니다."""
    if isinstance(value, str):
        text = value.strip()
        is_date = re.fullmatch(r"\d{4}-\d{2}-\d{2}", text) is not None
        is_datetime = re.fullmatch(
            r"\d{4}-\d{2}-\d{2}[Tt ]\d{2}:\d{2}.*", text
        ) is not None
        if not (is_date or is_datetime):
            return None
    elif not isinstance(value, (date, datetime, pd.Timestamp)):
        return None
    else:
        text = value

    try:
        timestamp = pd.Timestamp(text)
        if pd.isna(timestamp):
            return None
        if timestamp.tz is not None:
            # 시간대만 제거해 현지 촬영 시각을 유지합니다.
            timestamp = timestamp.tz_localize(None)
        return timestamp.as_unit("ns", round_ok=False)
    except (TypeError, ValueError, OverflowError):
        return None


def clean_analysis_dataframe(df_raw: pd.DataFrame) -> pd.DataFrame:
    """사진 분석 DataFrame의 점수와 촬영 시각을 정제해 반환합니다.

    원본의 행 순서, 인덱스, 열 순서와 태그 및 추가 열을 보존합니다.
    점수가 유효하지 않은 행만 제거하며, 날짜 오류는 NaT로 남깁니다.
    """
    if not isinstance(df_raw, pd.DataFrame):
        raise TypeError("입력은 pandas DataFrame이어야 합니다.")

    if df_raw.columns.has_duplicates:
        raise ValueError("중복 열 이름은 허용되지 않습니다.")

    required_columns = ["id", "final_score", "captured_at", "tags"]
    # empty는 한 축만 비어도 참이므로, 행과 열이 모두 없는 경우만 허용합니다.
    if df_raw.shape == (0, 0):
        return pd.DataFrame(
            {
                "id": pd.Series(dtype="object"),
                "final_score": pd.Series(dtype="float64"),
                "captured_at": pd.Series(dtype="datetime64[ns]"),
                "tags": pd.Series(dtype="object"),
            }
        )

    missing_columns = [
        column for column in required_columns if column not in df_raw.columns
    ]
    if missing_columns:
        missing = ", ".join(missing_columns)
        raise ValueError(f"필수 열 누락: {missing}")

    cleaned_scores = [_clean_score(value) for value in df_raw["final_score"].tolist()]
    valid_positions = [
        position for position, score in enumerate(cleaned_scores) if score is not None
    ]

    # 위치 기반 선택은 중복 인덱스가 있어도 행 대응을 바꾸지 않습니다.
    result = df_raw.iloc[valid_positions].copy(deep=True)
    result["final_score"] = pd.array(
        [cleaned_scores[position] for position in valid_positions],
        dtype="float64",
    )
    result["captured_at"] = pd.array(
        [
            _clean_captured_at(value)
            for value in result["captured_at"].tolist()
        ],
        dtype="datetime64[ns]",
    )
    return result
