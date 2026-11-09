# -*- coding: utf-8 -*-
"""[Task 1] 전체 사진 평가 AI 오케스트레이션 통합 파이프라인.

사진 전처리 -> VLM 분석(Mock) -> 이상치 정제 -> 통계 집계의 전 과정을
하나의 워크플로우로 잇는 백엔드 통합 모듈입니다.
모듈 경계 간 데이터 계약과 타입 변환(어댑터)을 보장합니다.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import pandas as pd
from PIL import UnidentifiedImageError

from prepare_photo.prepare_photo import prepare_photo
from analyze_with_gemini.analyze_with_gemini import analyze_with_gemini
from clean_analysis_dataframe.clean_analysis_dataframe import clean_analysis_dataframe
from aggregate_photo_insights.photo_analytics import aggregate_photo_insights

logger = logging.getLogger("photo_pipeline")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def run_pipeline(
    image_dir: str | Path,
    hint: str = "",
    model: str = "gemini-1.5-flash",
    use_mock: bool = True,
) -> dict[str, Any]:
    """사진 디렉토리를 순회 처리하여 종합 인사이트 및 통계를 산출합니다.

    Args:
        image_dir (str | Path): 분석 대상 사진들이 위치한 디렉토리 경로.
        hint (str, optional): 사용자가 입력한 촬영 의도(예: '배경 위주', '인물 표정 중시').
            VLM 분석 시 가중치 반영을 위해 주입됩니다. 기본값은 "".
        model (str, optional): 사용할 VLM 모델 식별자. 기본값은 'gemini-1.5-flash'.
        use_mock (bool, optional): Mock 모드 동작 여부. 기본값은 True.

    Returns:
        dict[str, Any]: 다음 구조의 최종 집계 리포트 (Streamlit 연동 규격):
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
                ],
                "user_intent_hint": str,
                "processed_count": int,
                "failed_count": int,
            }

    Raises:
        ValueError: image_dir 경로가 존재하지 않거나 디렉토리가 아닌 경우.
    """
    dir_path = Path(image_dir)
    if not dir_path.exists():
        raise ValueError(f"지정된 이미지 경로가 존재하지 않습니다: {image_dir}")
    if not dir_path.is_dir():
        raise ValueError(f"지정된 경로는 디렉토리가 아닙니다: {image_dir}")

    # =========================================================================
    # [수정 1: 환경변수/Mock 스위치 동기화]
    # AI 초기 코드 결함: use_mock 인자가 선언되었으나 VLM 호출부에 전달되지 않았음
    # 해결: 환경변수 USE_MOCK을 동기화하여 하위 LLM 클라이언트가 Mock/Real 모드를 정확히 감지하도록 개선.
    # =========================================================================
    os.environ["USE_MOCK"] = "true" if use_mock else "false"

    # 지원되는 이미지 파일 검색 (대소문자 무관)
    image_files = sorted(
        [p for p in dir_path.iterdir() if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS]
    )

    records: list[dict[str, Any]] = []
    failed_count = 0

    for img_path in image_files:
        try:
            # 1. 사진 전처리 (크기 조정, 해시 계산, 안전 EXIF 추출)
            photo_data = prepare_photo(img_path)

            # [보안 격리 계약] 외부 VLM에는 PII(GPS 등)가 배제된 안전 페이로드만 전송
            vlm_payload = {
                "upload_bytes": photo_data["upload_bytes"],
                "sha256": photo_data["sha256"],
                "safe_exif": photo_data.get("safe_exif", {}),
            }

            # 2. VLM 분석 및 응답 검증 (Mock 지원 및 사용자 의도 주입)
            analysis = analyze_with_gemini(
                photo=vlm_payload,
                model=model,
                hint=hint,
            )

            # -----------------------------------------------------------------
            # [수정 2]: 태그 중복 제거 및 데이터 무결성 보장]
            # AI 초기 코드 결함: VLM 태그(Dict)를 평탄화 하는 과정에서 중복 체크가 누락됨
            # 해결: 1차원 평탄화 후 dict.fromkeys()를 적용하여 입력순서를 유지하면서 중복제거함
            # -----------------------------------------------------------------
            raw_tags_dict = analysis.get("aesthetic_tags", {})
            flat_tags: list[str] = [
                tag
                for tag_list in raw_tags_dict.values()
                if isinstance(tag_list, list)
                for tag in tag_list
            ]
            unique_tags = list(dict.fromkeys(flat_tags))  # [수정 3] 순서 보존 중복 제거

            # [어댑터] clean_analysis_dataframe 및 내부 보관 규격으로 레코드 조립
            # 내부 시스템에는 11주차 위치 검색을 위해 internal_gps(있을 경우)를 보존
            record = {
                "id": photo_data["sha256"],
                "final_score": analysis.get("final_score"),
                "captured_at": photo_data.get("safe_exif", {}).get("captured_at"),
                "tags": unique_tags,
                "gps": photo_data.get("internal_gps"),
            }
            records.append(record)

        except (UnidentifiedImageError, OSError, ValueError) as exc:
            # =================================================================
            # [수정 2: 예외 처리 범위 한정 및 무차별 넘기기 방지]
            # AI 초기 코드 결함: except Exception으로 포괄 처리하여 어떠한 오류인지 디버깅 할 수 없는 치명적 문제
            # 해결: 손상된 파일이나 파싱 불가 데이터만 선별적으로 스킵하고, 치명적 오류는 조기 감지.
            # =================================================================
            failed_count += 1
            logger.warning(f"이미지 처리 건너뜀 ({img_path.name}): {exc}")
            continue

    # 3. 데이터프레임 조립 및 이상치 정제
    if not records:
        df_raw = pd.DataFrame(columns=["id", "final_score", "captured_at", "tags"])
    else:
        df_raw = pd.DataFrame(records)

    # 필수 4개 열 기반 정제 (점수 클리핑, 날짜 정규화)
    df_cleaned = clean_analysis_dataframe(df_raw)

    # 4. 최종 인사이트 통계 산출 (구조화된 dict 반환)
    insights = aggregate_photo_insights(df_cleaned)

    # 파이프라인 메타정보 병합
    insights["user_intent_hint"] = hint
    insights["processed_count"] = len(records)
    insights["failed_count"] = failed_count

    return insights
