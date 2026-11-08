# -*- coding: utf-8 -*-
"""[Task 1] 전체 사진 평가 AI 오케스트레이션 통합 파이프라인.

사진 전처리 -> VLM 분석(Mock) -> 이상치 정제 -> 통계 집계의 전 과정을
하나의 워크플로우로 잇는 백엔드 통합 모듈입니다.
모듈 경계 간 데이터 계약과 타입 변환(어댑터)을 보장합니다.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import pandas as pd

from prepare_photo.prepare_photo import prepare_photo
from analyze_with_gemini.analyze_with_gemini import analyze_with_gemini
from clean_analysis_dataframe.clean_analysis_dataframe import clean_analysis_dataframe
from aggregate_photo_insights.photo_analytics import aggregate_photo_insights

def run_pipeline(image_dir: str, use_mock: bool = True) -> dict:
    # 나중에 채울 예정
    return {"total_photos": 0, "monthly_trend": {}, "top_tags": [], "bottom_tags": []}