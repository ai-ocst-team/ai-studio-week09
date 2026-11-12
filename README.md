# 사진 평가 AI · 10주차 Task 5

담당: 김도혁. 검토 기준: `main`의 `b2a7d8b`, 2026-11-09. 작업 브랜치는 `refactor/code-quality-and-audit`다. Task 1~4의 통합 구현은 이 작업에 포함하지 않았다.

## 리팩터링과 검증

`aggregate_photo_insights/photo_analytics.py`의 상·하위 태그 결과 변환을 `_tag_records()`로 추출했다. 중복된 문자열·숫자 변환과 반올림 규칙을 한 곳에서 관리한다. 정렬, 동점 처리, 5개 제한, 예외와 반환 계약을 유지했다. 성능 향상을 측정하거나 주장하지 않는다.

AI 생성 근거는 `aggregate_photo_insights/prompt_log.md`와 생성 커밋 `e793d3a`, 이후 수정 커밋 `5f7b32a`다. 과거 문서에 적힌 수정 해시 `e2f5a7c`와 실제 파일 이력은 달라 이번 기록에는 확인한 해시를 사용한다.

- 기준 커밋을 임시 디렉터리에 풀어 기존 테스트 실행: 98 passed, 4 warnings.
- 변경 후 `.venv/bin/python -m pytest -q`: 98 passed, 4 warnings.
- `.venv/bin/python scripts/verify_task5.py`: 합성 입력 200건의 전체 반환값과 원본 불변성 확인. None·빈 입력·필수 열 누락 예외도 비교.
- 경고는 기존 `Image.getdata()` 사용에 대한 Pillow 폐기 예고다. 이 리팩터링에서 수정하지 않았다.
- 증거: [수정 전](evidence/task5/pytest_before.txt), [수정 후](evidence/task5/pytest_after.txt), [동작 비교](evidence/task5/parity.txt).
- 리팩터링 커밋: [`0b3a326`](https://github.com/ai-ocst-team/ai-studio-week09/commit/0b3a326), `refactor: extract shared tag result conversion`.

## 코드 리뷰 및 팀 작업 접점

아래 내용은 AI 사전 검토다. 실제 교차 리뷰 코멘트로 계산하지 않는다.

| 위치·재현 조건 | 관찰과 영향 | 판단·제안 |
|---|---|---|
| 집계 함수의 top/bottom 결과 생성 | 동일한 변환이 두 곳에 있어 수정 시 불일치 가능 | 작은 함수로 추출. 정렬 로직은 각 위치에 유지 |
| 분석 모듈과 응답 검증기의 `_TAG_VOCABULARY`, `_FOCUS_STATUSES` | 현재 허용값은 같지만 별도로 정의됨 | Task 2와 공통 규칙 소유권 협의 필요. 이번에는 변경 안 함 |
| 분석 반환 `aesthetic_tags`와 정제·집계 입력 `tags` | 초기 기준 b2a7d8b에서는 범주별 dict와 문자열 리스트 계약이 다르고 루트 파이프라인이 없었음 | 최신 main의 pipeline.py에 평탄화·중복 제거 구현됨. 아래 통합 검증 결과 참조 |
| `analyze_with_gemini/llm_client.py` 정상 호출 | 고정 Mock JSON 반환. docstring에만 `[MOCK]`, 실행 로그와 `USE_MOCK` 스위치 없음 | Task 3 구현 대상. 이번 리팩터링과 분리 |
| `prepare_photo/prepare_photo.py` 입력 경로 | 로컬 파일을 직접 읽음. 웹 업로드 서비스용 경로 제한은 없음 | 향후 서비스 경계에서 허용 경로·용량 정책 필요. 현재 로컬 함수의 계약 변경 보류 |

좋은 점은 집계 입력의 필요한 열만 복사하는 방식, 점수 정제, VLM 입력의 EXIF 화이트리스트와 응답 검증이다. 고정 경로의 `run_path()`는 로컬 검증 모듈을 실행하며 사용자 문자열을 실행하는 구조는 아니다. 사용자 hint를 데이터로 구분하는 프롬프트가 있지만 실제 모델의 프롬프트 주입 저항성을 검증한 것은 아니다.

## 실제 교차 리뷰 반영 · 대기

실제로 받은 코멘트가 제공되지 않았다. 아래 두 행은 요구사항 추적용 빈 자리이며 완료 건수가 아니다.

| 항목 | 받은 코멘트·출처 | 수용/보류 판단 | 이유·추적 | 관련 커밋 |
|---|---|---|---|---|
| 1 | 대기 | 미판단 | 실제 원문 또는 정확한 요지와 리뷰어·PR 필요 | 없음 |
| 2 | 대기 | 미판단 | 실제 원문 또는 정확한 요지와 리뷰어·PR 필요 | 없음 |

## 보안·AI 기록 상태

[보안 점검](SECURITY_CHECKLIST.md)과 [김도혁 AI 협업 기록](ai_log/10주차_김도혁.md)을 참조한다. `.env` 경로는 현재 추적 목록과 로컬 ref 이력에서 발견되지 않았다. 모든 과거 비밀값 노출이 없었다는 판정은 아니다.

AI 협업 기록 2건은 리팩터링과 증거·검증 코드 보완으로 구성했다. 2026-11-11 김도혁이 문서에서 리팩터링 수용과 직접 판단 완료를 확인했다. 외부 사진·데이터 미사용은 2026-11-11 사용자 확인으로 반영했다. 5주차 원본 체크리스트는 2026-11-11 사용자 제공 원문과 대조 완료했다. S6는 이후 사용자가 다른 파일의 이력까지 확인했다고 문서에 기재했다. 실제 교차 리뷰 요건은 남았다. PR 생성·push·원격 main 병합·최종 제출은 수행하지 않았다.

## Claude AI 리뷰 후속 검증 · 2026-11-10

로컬에 제공된 `evidence/task5/claude_review_findings.md`를 근거로 검증했다. 이 문서는 별도 Claude AI 리뷰 기록이며, 이전 CLI 호출 실패 JSON이 성공했다는 뜻은 아니다. 사람 교차 리뷰 2건에는 계산하지 않는다.

| 리뷰 항목 | 판단 | 반영·검증 |
|---|---|---|
| 2. 증거 명령 인용 부호 누락 | 수용 | `scripts/audit_task5.py`가 셸 인용을 보존하고 실제 zsh 실행 결과를 저장. 이력 조회·추적 파일 필터·검색 명령 재실행 성공 |
| 3. 검색 범위가 문구보다 좁음 | 수용 | 검색 대상에 `scripts` 포함, 보안 문서에 대상 경로 명시 |
| 4. 최적화 실행에서 비교 생략 | 수용 | 검증용 assert를 명시적 비교·예외로 변경. 정상 코드 일반·`-O` 실행 성공, 의도적으로 잘못된 total_photos를 반환하면 두 모드 모두 실패 |

재현 명령은 `.venv/bin/python scripts/audit_task5.py`, `.venv/bin/python scripts/verify_task5.py`, `.venv/bin/python -O scripts/verify_task5.py`다. `evidence/task5/optimization_check.txt`에 변경 전후 오류 주입 결과를 저장했다. 과거 98개 테스트 결과는 기준 `b2a7d8b`와 현재 Task 5 브랜치의 결과다. 원격 main `5ea3e8c`에는 파이프라인이 추가됐으며, 앞선 임시 디렉터리 검증에서 전체 테스트 import 충돌이 확인됐다. 해당 검증 시점에는 최신 main 통합 전이었으며, 이후 아래 통합 기록에서 완료했다.

후속 수정 커밋: `8868455` (`fix: preserve audit commands and verification under optimization`).

## 최신 main 통합 · 2026-11-10

`origin/main`의 `5ea3e8c`를 작업 브랜치에 병합했다. 병합 커밋은 `f63076e`이며 충돌은 없었다. 파이프라인·CLI·통합 테스트 5건이 포함됐다.

병합 직후 전체 pytest는 수집 단계에서 실패했다. 기존 단위 테스트는 `prepare_photo`, `clean_analysis_dataframe`을 단일 모듈로 import하지만 파이프라인은 같은 이름을 패키지로 import해 충돌했다. 두 디렉터리에 공개 함수를 내보내는 `__init__.py`를 추가했다. 함수 본문과 호출 계약은 변경하지 않았다. 수정 커밋은 `df1f249`다.

- `.venv/bin/python -m pytest -q`: **103 passed, 9 warnings**. [전체 로그](evidence/task5/pytest_integrated.txt).
- `.venv/bin/python main.py --help`: exit 0.
- `.venv/bin/python scripts/verify_task5.py`: 합성 입력 200건 동작 비교 통과.
- 경고는 기존 Pillow getdata 폐기 예고이며 통합 테스트에서도 발생해 총 9개다.

Task 5 구현과 팀 main 통합 검증은 완료했다. 사람의 직접 판단은 2026-11-11 사용자 문서 확인으로 반영했다. 실제 교차 리뷰 인정 여부·보안 미확인 항목은 대기 상태를 유지한다. push·PR·merge는 아직 수행하지 않았다.

## analyze_with_gemini AI 보조 자체 코드 리뷰

[AI 보조 자체 코드 리뷰](docs/reviews/analyze_with_gemini_review.md)를 작성했다. 모듈 테스트 43개, 전체 103개가 통과했다. 별도 재현에서 비Mock 요청에도 고정 Mock이 반환되는 점과 통신 실패 시 다음 사진 처리가 중단되는 점을 확인했다. Task 1·3와 정책·구현 범위를 맞추기 위해 제품 코드 수정은 보류했다. 이 리뷰는 팀 간 교차 리뷰로 계산하지 않는다.

## 진행상황 · 2026-11-11 문서 점검

- 리팩터링 수용 및 AI 협업 직접 검토: 사용자 문서 확인 반영 완료.
- AI 기록 2건: 집계 리팩터링, 증거·검증 코드 보완. 삭제된 보안 협업 기록은 복원하지 않았다.
- 코드 검증: 최근 전체 103 passed, 9 warnings. 이번 변경은 문서만 수정해 테스트를 재실행하지 않았다.
- 보안: S1·S2 등은 사용자 확인과 도구 검증 범위를 구분했다. S3는 사용자 확인에 따라 외부 사진·데이터 미사용으로 정리했다. 5주차 원본 S1~S10 대조는 완료했다. S6의 `.env*` 경로 이력 0건은 전체 비밀값 감사와 구분한다.
- 다음 작업: 남은 제출 요건 확인 후 브랜치 push·PR 생성·팀 리뷰. 팀 간 교차 리뷰 요건은 자체 리뷰로 완료 처리하지 않는다.

## 5주차 원본 체크리스트 반영 · 2026-11-11

사용자가 제공한 S1~S10 원문을 보안 문서의 점검 항목으로 반영하고 전 항목 대응을 확인했다. 외부 사진·데이터 미사용인 S3는 미해당으로 표시했다. 원본 대조는 완료했지만 S6는 이후 사용자 점검 완료를 반영하되 도구의 파일명 검사와 구분했다. 실제 팀 간 교차 리뷰 또는 대체 인정 확인과 push·PR은 아직 남아 있다.

## PR 제출 준비 · 2026-11-11

사용자가 S6의 다른 이름 파일 이력 점검도 완료했다고 문서에 확인했다. 사용자 점검과 도구의 자동 검사 범위를 구분해 반영했다. 팀 간 교차 리뷰 또는 대체 인정 확인은 계속 대기다.
