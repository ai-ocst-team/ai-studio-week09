# 4. 제출 체크리스트

> AI 오케스트레이션 스튜디오 제9주차 과제 — 바이브 코딩 표준 6단계 사이클 적용  
> 팀명: **아트서강** | 담당자: **하정윤** | 대상 함수: **`aggregate_photo_insights`** (`photo_analytics.py`) | 브랜치: **`feat/hjy`**

---

## 팀원별 담당 함수 가이드

| 이름 | 맡은 함수 | 비고 (진행 현황) |
|:---:|:---|:---:|
| **하정윤** | `aggregate_photo_insights` | **제출 완료 (6단계 사이클 완주)** |
| **박상현** | *(미정)* | 브랜치 작업 진행 중 |
| **류시향** | `prepare_photo` | 브랜치 작업 진행 중 |
| **김도혁** | `extract_safe_exif(image)` | 브랜치 작업 진행 중 |
| **신비** | `validate_vlm_response` | 브랜치 작업 진행 중 |

---

## 4.1 제출 체크리스트 점검표

| 번호 | 확인 항목 | 확인 | 세부 확인 및 이행 내용 |
|:---:|:---|:---:|:---|
| **1** | **팀원 1인당 최소 1개 함수, 사이클 6단계 완주** | **진행 중<br>(하정윤 완료)** | • **하정윤(본인)**: 모듈 3 핵심 함수 `aggregate_photo_insights` 6단계 사이클 완주 및 제출 완료<br>• **타 팀원**: 각자 브랜치에서 작업 진행 중 (최종 main 브랜치 통합 시 팀 전원 완주 여부 확인 예정) |
| **2** | **함수당 테스트 3개 이상(정상·경계·예외), pytest 전체 통과** | **☑** | 정상 2건(T09, T10), 경계 1건(T11), 예외 1건(T12), 공백 정규화, 불변성 검증 등 총 6개 테스트 작성 및 pytest 6/6 (100%) 전체 통과 |
| **3** | **prompt_log.md: 프롬프트 원문 + 발견 결함 + 수정 내역 + 커밋 해시** | **☑** | Gemini WebUI 프롬프트 원문, 코드 리딩에서 적발한 4대 결함(공백 미정규화, 메모리 오버헤드 등), 수정 내역 및 커밋 해시를 표준 서식으로 작성 완료 |
| **4** | **함수당 2커밋 이상, 의미 있는 커밋 메시지** | **☑** | `feat: initial AI-generated draft...` (AI 1차 생성 원본) 및 `fix(analytics): normalize tag whitespace...` (리딩 수정/테스트)로 커밋 히스토리 분리 완료 |
| **5** | **.gitignore(.env, .venv/, __pycache__/) 및 보안 체크리스트 포함** | **☑** | 저장소 최상위 `.gitignore` 등록 및 3.6 AI·데이터 보안 체크리스트(S1~S10) 전수 마킹 완료 (`SECURITY_CHECKLIST.md` 첨부) |
| **6** | **LLM 의존 기능의 Mock 격리 및 [MOCK] 표시 (해당 시)** | **☑** | 본 담당 함수는 pandas 기반 순수 집계 함수로 LLM 외부 호출이 없음 (전체 파이프라인의 VLM 의존 모듈은 7주차 설계에 따라 Mock 격리 스키마 준수) |
| **7** | **저장소에 PII·실데이터·API 키가 없음을 전원 교차 확인** | **진행 중<br>(하정윤 검증)** | 현재 제출된 하정윤 담당 모듈 기준 PII·실데이터·API 키 0건 검증 완료 (팀원 전체 모듈 통합 및 main 병합 시 최종 교차 확인 예정) |

---

## 4.2 항목별 상세 증빙 요약

### [항목 1] 표준 6단계 사이클 산출물 구성 (하정윤 담당 완료)
- **현재 진행 상황**: 팀원별 개인 브랜치 작업 중이며, 본 브랜치(`feat/hjy`) 기준 담당자(하정윤) 분량은 6단계 사이클을 100% 완주함.
  - **① 논리 설계**: 함수 시그니처(`aggregate_photo_insights: pd.DataFrame -> dict`), 입출력 계약 및 4대 테스트 케이스(T09~T12) 선행 확정
  - **② 정밀 프롬프트**: 역할, 시그니처, 입출력 명세, 부정 제약("~금지")을 포함한 6대 구성 요소 작성
  - **③ AI 코드 생성**: Google Gemini WebUI를 통해 1차 생성 코드 도출
  - **④ 코드 리딩·검증**: 태그 공백 미정규화(`strip` 누락), 전체 복사로 인한 메모리 오버헤드, 미사용 import(`numpy`) 등 4개 결함 적발 및 수정
  - **⑤ 테스트**: `test_photo_analytics.py` 단위 테스트 스위트 구동 (6 passed)
  - **⑥ Git 커밋**: 단계별 의미 단위 분리 커밋 및 `prompt_log.md` 갱신

### [항목 2] pytest 테스트 실행 결과 (6 passed)
```bash
$ pytest -v aggregate_photo_insights/test_photo_analytics.py
============================= test session starts =============================
collected 6 items

aggregate_photo_insights/test_photo_analytics.py::test_t09_normal_case_100_photos PASSED          [ 16%]
aggregate_photo_insights/test_photo_analytics.py::test_t10_normal_case_3_months_trend PASSED      [ 33%]
aggregate_photo_insights/test_photo_analytics.py::test_t11_boundary_empty_and_single PASSED       [ 50%]
aggregate_photo_insights/test_photo_analytics.py::test_t12_exceptional_missing_column PASSED     [ 66%]
aggregate_photo_insights/test_photo_analytics.py::test_tag_whitespace_normalization PASSED       [ 83%]
aggregate_photo_insights/test_photo_analytics.py::test_edge_score_clipping_and_immutability PASSED [100%]

============================== 6 passed in 0.45s ==============================
```

### [항목 5] `.gitignore` 설정 상태
```text
__pycache__/
*.py[cod]
.venv/
.env
.pytest_cache/
*.bak
```
