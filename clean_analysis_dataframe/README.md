# 사진 분석 데이터 정제 함수 — 9주차 개인 담당 모듈

담당자: 박상현 · 팀명: 아트서강 · 갱신일: 2026-11-03

`clean_analysis_dataframe(df_raw: pd.DataFrame) -> pd.DataFrame`는 점수와 촬영 날짜를 정제한 새 표를 반환합니다. 필수 열은 `id`, `final_score`, `captured_at`, `tags`입니다. 유한 점수는 0~10으로 제한하고 무효 점수 행은 제거하며, 잘못된 날짜는 NaT로 유지합니다. 추가 열·태그·행 순서·중복 인덱스를 보존합니다. DB 입출력·LLM 호출·집계는 담당하지 않습니다.

## 확인할 파일

| 파일 | 내용 |
|---|---|
| [report.md](report.md) | 6단계 보고서, 명세·결함·수정·검증·실제 커밋 이력 |
| [구현](clean_analysis_dataframe.py), [테스트](test_clean_analysis_dataframe.py) | 함수와 정상·경계·예외·회귀 테스트 |
| [prompt_log.md](prompt_log.md), [원문 프롬프트](copilot_prompt.txt) | 사용 도구·작업 과정·커밋 시점 구분 |
| [CHECKLIST.md](CHECKLIST.md), [SECURITY_CHECKLIST.md](SECURITY_CHECKLIST.md) | 완료·미완료 사항 및 보안 점검 범위 |
| [증빙 안내](evidence/README.md) | 생성 원본·Copilot 대화·테스트 출력·과거 검증 기록 |

## 실행

Python 3.12 환경에서 이 개인 모듈 폴더를 열고 실행합니다.

```powershell
python -m pip install -r requirements.txt
python -B -X utf8 -m pytest -v --tb=short -p no:cacheprovider
```

저장소 폴더 반영 후 검증은 **33 passed in 0.79s**입니다. [실행 출력](evidence/pytest_repository_check.txt). 증빙 폴더의 과거 테스트 사본만 `evidence/conftest.py`로 수집에서 제외합니다. 팀 전체 통합·성능 검증 결과는 아닙니다.

## 제출 상태

원본 보존 `be8c457`, 수정 반영 `54cc951`의 로컬 커밋 2개를 사용자가 직접 완료했습니다. 11월 2일 작업을 11월 3일 사후 기록했으며 생성 직후 커밋으로 주장하지 않습니다. 현재 문서 커밋과 push·LMS 제출은 대기 중입니다. 팀 통합 테스트 및 전원 보안 교차 확인은 별도입니다.
