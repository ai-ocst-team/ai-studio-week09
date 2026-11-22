"""11주차 Streamlit 대시보드용 백엔드 어댑터.

Streamlit에 의존하지 않는 순수 pandas 함수만 제공합니다.
데이터 정제와 통계 집계는 기존 모듈 함수를 그대로 호출합니다.
"""

from __future__ import annotations

import json
from numbers import Real
from typing import Any

import pandas as pd

from aggregate_photo_insights.photo_analytics import aggregate_photo_insights
from clean_analysis_dataframe.clean_analysis_dataframe import clean_analysis_dataframe

REQUIRED_COLUMNS = ["id", "final_score", "captured_at", "tags"]
ALL_TAGS = "전체"

MONTHLY_COLUMNS = ["year_month", "count", "avg_score"]
TAG_COLUMNS = ["tag", "avg_score", "count"]

TAG_GLOSSARY: dict[str, str] = {
    "자연풍경": "산, 바다, 숲처럼 자연 환경을 주제로 담은 사진입니다.",
    "건축도시": "건물이나 도시 공간의 형태와 구조를 중심으로 담은 사진입니다.",
    "인물동물": "사람이나 동물의 표정, 자세, 행동이 중심인 사진입니다.",
    "사물정물": "움직임이 적은 물건을 빛과 배치로 표현한 사진입니다.",
    "거리스냅": "거리에서 마주친 일상적인 장면이나 순간을 담은 사진입니다.",
    "안정된 순광": "카메라 뒤쪽의 빛이 피사체 앞면을 고르게 비추는 조건입니다.",
    "골든아워": "해가 뜬 직후나 지기 직전 따뜻하고 낮은 각도의 빛이 드는 시간대입니다.",
    "흐린날 확산광": "구름이 햇빛을 퍼뜨려 그림자 경계가 부드러워지는 조건입니다.",
    "극단적 역광": "피사체 뒤의 빛이 강해 윤곽이나 실루엣이 특히 두드러지는 조건입니다.",
    "저조도 야경": "빛이 적은 밤에 가로등이나 건물 조명처럼 제한된 광원을 활용한 장면입니다.",
    "완전 정지": "촬영 시점에 피사체의 움직임이 거의 드러나지 않는 상태입니다.",
    "완만한 흐름": "물결이나 천천히 걷는 사람처럼 느린 움직임이 느껴지는 장면입니다.",
    "예측불가 빠른동세": "빠르게 움직이면서 방향이나 타이밍을 예상하기 어려운 장면입니다.",
    "찰나의 순간": "표정이나 몸짓이 짧은 순간에만 나타나 촬영 타이밍이 중요한 장면입니다.",
    "아이레벨": "촬영자가 눈높이에서 수평에 가깝게 바라본 구도입니다.",
    "로우 앵글": "카메라를 낮게 두고 피사체를 올려다본 구도입니다.",
    "하이앵글(탑뷰)": "카메라를 피사체보다 높게 두고 아래로 내려다본 구도입니다.",
    "피사체 눈높이 일치": "카메라 높이를 사람이나 동물의 눈높이에 맞춘 구도입니다.",
    "틸트사선": "카메라를 기울여 화면의 수평이나 수직을 사선으로 표현한 구도입니다.",
    "단일피사체 집중": "주변 요소를 줄여 하나의 피사체에 시선이 모이도록 한 구도입니다.",
    "다층 레이어": "전경, 중경, 배경이 겹치며 깊이감을 만드는 구도입니다.",
    "프레임인프레임": "창이나 문틀 같은 화면 속 테두리로 피사체를 감싸 강조한 구도입니다.",
    "대칭패턴": "중심축을 기준으로 비슷한 형태가 반복되거나 대칭으로 배치된 구도입니다.",
    "여백의미": "빈 공간을 활용해 피사체를 강조하거나 장면에 여유를 주는 구도입니다.",
    "자연스런 뉴트럴": "특정 색이 과하게 두드러지지 않고 자연스러운 균형을 이루는 색감입니다.",
    "뚜렷한 보색대비": "파랑과 주황처럼 색상환에서 반대에 가까운 색의 대비가 두드러지는 표현입니다.",
    "차분한 모노톤": "하나의 색 계열이나 무채색을 중심으로 차분하게 구성한 색감입니다.",
    "다채로운 색정돈": "여러 색이 등장하면서도 배치와 비중이 조화를 이루는 표현입니다.",
    "절제된 톤다운": "채도를 낮춰 색을 부드럽고 절제된 느낌으로 표현한 사진입니다.",
}


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


def count_dropped_rows(df_raw: pd.DataFrame, df_clean: pd.DataFrame) -> int:
    """정제 전후의 행 수 차이를 0 이상의 정수로 반환합니다."""
    return max(0, len(df_raw) - len(df_clean))


def assign_cut_grades(
    df_clean: pd.DataFrame,
    a_cutoff: float = 8.0,
    b_cutoff: float = 6.0,
) -> pd.DataFrame:
    """점수 기준으로 선별 등급을 추가한 복사본을 반환합니다."""
    for cutoff in (a_cutoff, b_cutoff):
        if isinstance(cutoff, bool) or not isinstance(cutoff, Real) or not 0 <= cutoff <= 10:
            raise ValueError("컷 기준 점수는 0점 이상 10점 이하의 숫자여야 합니다.")
    if a_cutoff <= b_cutoff:
        raise ValueError("A컷 기준 점수는 B컷 기준 점수보다 커야 합니다.")

    graded = df_clean.copy()
    graded["cut_grade"] = pd.Series("보류", index=graded.index, dtype="string")
    if not graded.empty:
        scores = graded["final_score"]
        graded.loc[scores >= b_cutoff, "cut_grade"] = "B컷"
        graded.loc[scores >= a_cutoff, "cut_grade"] = "A컷"
    return graded


def summarize_cut_counts(df_graded: pd.DataFrame) -> dict[str, int]:
    """A컷, B컷, 보류 건수를 세며 없는 등급은 0으로 반환합니다."""
    counts = df_graded["cut_grade"].value_counts()
    return {grade: int(counts.get(grade, 0)) for grade in ("A컷", "B컷", "보류")}


def get_ai_reply(
    messages: list[dict[str, str]],
    summary_context: dict[str, Any] | None = None,
) -> str:
    """[12주차] Mock 응답 / [13주차] 시그니처를 유지하고 함수 내부만 LLM API로 교체."""
    question = messages[-1].get("content", "").strip() if messages else ""
    if not question:
        return "[MOCK] 사진 선별이나 감성 태그에 대해 질문을 입력해 주세요."

    if "태그" in question:
        advice = "상위 태그의 공통점을 살펴보고, 각 태그가 잘 드러나는 사진을 대표 컷으로 골라보세요."
    elif "B컷" in question or "보류" in question:
        advice = "B컷과 보류 사진은 비슷한 A컷과 비교해 초점과 구도를 확인하고, 고유한 순간은 남겨보세요."
    else:
        advice = "A컷을 먼저 비교하고, 비슷한 구도에서는 초점과 촬영 의도가 가장 잘 드러나는 사진을 골라보세요."

    context = summary_context or {}
    facts = []
    if "total_photos" in context:
        facts.append(f"사진 {context['total_photos']}장")
    if "avg_score" in context:
        facts.append(f"평균 {context['avg_score']:.2f}점")
    for key, grade in (("a_cut_count", "A컷"), ("b_cut_count", "B컷")):
        if key in context:
            facts.append(f"{grade} {context[key]}장")

    tags = []
    for item in context.get("top_tags") or ():
        tag = item.get("tag") if isinstance(item, dict) else item
        if isinstance(tag, str) and tag.strip():
            tags.append(tag.strip())
    if tags:
        facts.append(f"상위 태그 {', '.join(tags[:3])}")
    stats = f"현재 집계는 {', '.join(facts)}입니다. " if facts else ""
    if context.get("total_photos") == 0:
        advice = "필터 범위를 넓혀 사진이 표시된 뒤 다시 비교해 보세요."
    return f"[MOCK] {stats}{advice}"
