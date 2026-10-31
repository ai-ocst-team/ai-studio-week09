# prompt_log.md — AI 활용 과정 기록

> 사이클 1회전(함수 하나)마다 아래 형식으로 1항목을 추가한다.
> 이 파일은 10주차 아카이빙 중간 점검과 16주차 발표에서 그대로 사용된다.

## [모듈 3] aggregate_photo_insights — 2026-10-31, 작성자: 하정윤
- **사용 도구**: Google Gemini WebUI
- **프롬프트 원문**:
  ```markdown
  당신은 파이썬 백엔드 및 데이터 분석 모듈 개발을 돕는 전문 어시스턴트입니다.
  'VLM 기반 사진 감성·구도 심층 비평 및 스마트 Culling 시스템(아트서강)'의 데이터 분석 모듈(photo_analytics.py)에 들어갈 집계 함수를 구현해 주세요.

  [함수 시그니처 — 변경 금지]
  def aggregate_photo_insights(df_analyses: pd.DataFrame) -> dict[str, Any]:

  [입력 명세]
  df_analyses: 사진 분석 레코드가 담긴 pandas DataFrame.
  - 필수 포함 컬럼: ["id", "final_score", "captured_at", "tags"]
  - tags 컬럼의 각 행은 문자열 리스트(예: ["3분할_구도", "자연광"]) 형태임.

  [출력 명세 — 딕셔너리 계약]
  {
      "total_photos": 정제 후 유효 사진 총 건수(int),
      "monthly_trend": {"YYYY-MM": {"count": int, "avg_score": float}},
      "top_tags": [{"tag": str, "avg_score": float, "count": int}],
      "bottom_tags": [{"tag": str, "avg_score": float, "count": int}]
  }

  [예외·경계 방침]
  1. df_analyses가 빈 경우 기본 딕셔너리 즉시 반환.
  2. 필수 열 누락 시 ValueError 발생.
  3. final_score NaN 제거 및 0.0~10.0 클리핑.

  [제약 조건]
  - 표준 라이브러리와 pandas만 주로 사용할 것.
  - 원본 DataFrame 직접 수정 금지(inplace 금지, .copy() 사용 필수).
  - 최소 2회 이상 등장한 태그만 top/bottom에 선별.
  ```
- **생성 코드 위치**: 커밋 `e793d3a` (Gemini WebUI 생성 원본)
- **코드 리딩에서 발견한 결함 및 실무 개선점**:
  1. **태그 문자열 미정규화(`strip` 누락)**: `df_tags["tags"].apply(lambda t: isinstance(t, str) and bool(t.strip()))`으로 공백 전용 문자열만 필터링하고 실제 앞뒤 공백을 자르지 않아, `" 자연광 "`과 `"자연광"`이 별개 태그로 분리되어 신뢰성 필터(`count >= 2`)에서 둘 다 누락되는 심각한 데이터 정제 결함 발견.
  2. **대용량 배치 시 메모리 낭비**: `df = df_analyses.copy()`로 인해 VLM 심층 비평문 텍스트, 바이너리 썸네일 등 수십~수백 MB의 불필요한 메타데이터 컬럼까지 딥카피되는 비효율 발견.
  3. **미사용 import (`import numpy as np`)**: 본문에서 전혀 쓰이지 않는 라이브러리가 포함되어 린터(Flake8/Ruff F401) 경고 발생.
  4. **`apply(lambda)` 행 단위 순회 병목**: 태그 필터링을 파이썬 인터프리터 수준에서 순회하여 대량 데이터 집계 시 성능 저하 유발.
- **수정 내역 (커밋 `e2f5a7c`)**:
  - `df_tags["tags"] = df_tags["tags"].astype(str).str.strip()` 적용으로 태그 공백을 완전히 정규화하고 벡터화 연산으로 전환.
  - `df = df_analyses[required_columns].copy()`로 필요한 4개 컬럼만 프로젝션 복사하여 메모리 최적화 완료.
  - 미사용 import 제거 및 datetime 명시적 파생 컬럼 처리.
- **최종 테스트 결과**:
  - `pytest -v test_photo_analytics.py` 실행 완료 (6 passed, 0 failed, 100% 통과).
