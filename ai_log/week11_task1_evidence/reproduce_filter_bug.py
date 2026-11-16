"""filter_analyses 열 소실 문제를 재현합니다.

저장소 루트에서 실행:
    python ai_log/week11_task1_evidence/reproduce_filter_bug.py

AI가 처음 생성한 함수(아래 original_filter_analyses)와 현재 backend.filter_analyses를
같은 입력으로 호출해 반환 모양을 나란히 출력합니다.
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import backend  # noqa: E402

ALL_TAGS = "전체"


def original_filter_analyses(df_clean, min_score=0.0, selected_tag=ALL_TAGS):
    """수정 전 코드. 마지막 인덱싱이 result[has_tag]입니다."""
    result = df_clean[df_clean["final_score"] >= min_score]
    if selected_tag != ALL_TAGS:
        has_tag = [
            isinstance(tags, (list, tuple)) and selected_tag in tags
            for tags in result["tags"].tolist()
        ]
        result = result[has_tag]
    return result.copy()


def main() -> int:
    df_clean = backend.prepare_uploaded_dataframe(
        pd.DataFrame(
            {
                "id": ["a", "b", "c"],
                "final_score": [9.0, 5.0, 3.0],
                "captured_at": ["2026-01-01", "2026-02-01", None],
                "tags": ['["자연풍경", "골든아워"]', "자연풍경, 인물", None],
            }
        )
    )
    header_only = backend.prepare_uploaded_dataframe(
        pd.DataFrame(columns=backend.REQUIRED_COLUMNS)
    )

    cases = [
        ("점수 10.0 + 태그 '자연풍경'", df_clean, 10.0, "자연풍경"),
        ("점수 10.0 + '전체'", df_clean, 10.0, ALL_TAGS),
        ("헤더만 있는 입력 + 태그 '자연풍경'", header_only, 0.0, "자연풍경"),
        ("점수 5.0 + 태그 '자연풍경' (결과 있음)", df_clean, 5.0, "자연풍경"),
    ]

    print("1) pandas 동작: 빈 리스트 인덱싱")
    print(f"   df[[]].shape      = {df_clean[[]].shape}   <- 열 0개 선택으로 해석")
    print(f"   df.loc[[]].shape  = {df_clean.loc[[]].shape}   <- 행 0개 선택")
    print()
    print("2) 수정 전 / 수정 후 반환 모양")
    still_broken = False
    for label, frame, min_score, tag in cases:
        before = original_filter_analyses(frame, min_score, tag)
        after = backend.filter_analyses(frame, min_score, tag)
        print(f"   {label}")
        print(f"      수정 전: {before.shape} 열={list(before.columns)}")
        print(f"      수정 후: {after.shape} 열={list(after.columns)}")
        if list(after.columns) != list(frame.columns):
            still_broken = True

    print()
    print("결과:", "현재 코드에도 열 소실이 남아 있음" if still_broken else "현재 코드는 모든 경우에 열을 유지함")
    return 1 if still_broken else 0


if __name__ == "__main__":
    sys.exit(main())
