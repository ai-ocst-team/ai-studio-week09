# Claude AI 독립 사전 리뷰 결과

- 리뷰어: Claude AI (Claude Code, Opus 5). 사람 교차 리뷰가 아니다. 이 문서를 실제 교차 리뷰 2건으로 계산하지 않는다.
- 리뷰일: 2026-11-10
- 대상: 브랜치 `refactor/code-quality-and-audit`, 리팩터링 커밋 `0b3a326`, 기준 커밋 `b2a7d8b`
- 대상 파일: `aggregate_photo_insights/photo_analytics.py`, `scripts/verify_task5.py`, `README.md`, `SECURITY_CHECKLIST.md`, `evidence/task5/*`
- 프롬프트: `claude_review_prompt.txt`. 그 프롬프트는 제공 자료만 검토하도록 도구를 막은 샌드박스 호출용이었다. 이번 리뷰는 저장소에서 직접 읽은 자료를 포함한다. 아래 각 항목에 확인 수단을 적었다.
- 테스트: 제공된 `pytest_before.txt`, `pytest_after.txt`, `parity.txt`를 읽었다. pytest와 `verify_task5.py`를 직접 실행하지 않았다.
- 입증 가능한 항목만 적었다. 건수를 맞추기 위해 만든 지적은 없다.

## 1. 리팩터링 동작 보존: 지적 사항 없음

`_tag_records()`의 본문은 삭제된 두 리스트 컴프리헨션과 토큰 단위로 동일하다. 정렬, 동점 처리, `head(5)`, `round(_, 2)`, 예외와 반환 계약은 호출부에 그대로 남아 있다. 이 변경만으로 동작이 달라질 경로는 없다. README가 성능 향상을 주장하지 않는 것도 근거 범위와 맞다.

문서에 인용된 커밋 해시를 `git log -1`로 조회했다. `e793d3a`, `5f7b32a`, `b2a7d8b`, `0b3a326`은 실존하고 `e2f5a7c`는 존재하지 않는다. README의 설명과 일치한다. 다만 `b2a7d8b`의 커밋 날짜는 2026-11-08이고 README는 "`b2a7d8b`, 2026-11-09"로 적었다. 2026-11-09가 점검일이라면 그렇게 표기해야 오해가 없다.

## 2. [중] 증거 파일에 기록된 명령이 실제 실행 명령이 아니다

- 위치: `evidence/task5/env_audit.txt`, `evidence/task5/source_scan.txt`. 주장 위치는 `SECURITY_CHECKLIST.md`의 "실제 명령·표준 출력·종료 코드는 env_audit.txt에 저장했다".
- 재현 조건: 기록된 명령 줄을 그대로 zsh에 붙여 실행한다.
  - `git log --all --full-history --format=%h %s -- **/.env* .env*` : `%s`가 별도 인자로 분리되고 `**/.env*`가 따옴표 없이 노출된다.
  - `rg -n print\(|logging|requests|... --glob *.py ...` : `|`가 이스케이프되지 않아 셸 파이프라인으로 해석된다.
  - `git ls-files --cached (filter basename starts with .env)` : 명령이 아니라 주석이 섞인 문장이다.
- 영향: S5와 S6의 근거가 재현 가능한 명령으로 성립하지 않는다. 검증자가 같은 결론에 도달하지 못하거나 다른 결과를 본다. 결론 자체(`.env*` 경로 이력 0건, 추적 목록에 `.env*` 없음)는 이번 확인 범위에서 반증되지 않았으나, 문서의 "실제 명령" 문구는 현재 파일 내용과 일치하지 않는다.
- 최소 수정안: 재실행 시 `set -x`를 쓰거나 `printf '$ %q ' "$@"` 형태로 인용 부호를 보존해 기록한다. 또는 기록 줄을 요약 표기임을 명시하고, 재현용 명령 블록을 따옴표 포함으로 따로 둔다.
- 검증 방법: 기록된 각 줄을 복사해 실행했을 때 exit 0과 기록된 stdout이 그대로 재현되는지 확인한다.

## 3. [하] S4·S7 문구가 실제 스캔 범위보다 넓게 읽힌다

- 위치: `SECURITY_CHECKLIST.md` S4 "현재 Python 코드에서 ... 검색하고 실행 모듈 검토", S7 "현재 실행 모듈에 비밀값 출력 코드 미발견".
- 재현 조건: `source_scan.txt`의 스캔 대상은 `prepare_photo`, `analyze_with_gemini`, `validate_vlm_response`, `clean_analysis_dataframe`, `aggregate_photo_insights` 5개 디렉터리뿐이다. `git ls-files '*.py'`로 확인하면 그 밖에 있는 추적 파일은 `scripts/verify_task5.py` 하나이고, 이 파일이 `subprocess`, `exec(`, `print`를 쓰는 유일한 파일인데 스캔에서 빠져 있다.
- 영향: 과장으로 단정할 정도는 아니지만, 가장 관련 있는 파일이 근거에서 제외돼 범위 표기가 실제보다 넓게 읽힌다.
- 최소 수정안: 표의 근거 칸에 스캔한 경로를 명시하거나, `scripts`를 포함해 재실행한다.
- 검증 방법: 재실행 결과에 `scripts/verify_task5.py`의 `exec(`, `subprocess` 히트가 나타나는지 확인하고, 그것이 의도된 로컬 검증 코드임을 한 줄로 설명한다.

## 4. [하] `verify_task5.py`는 `-O` 실행 시 아무것도 검증하지 않는다

- 위치: `scripts/verify_task5.py`, 반복 비교와 예외 비교 구간(모든 검증이 `assert`).
- 재현 조건: `python -O scripts/verify_task5.py`. `-O`는 `assert` 문을 전부 제거한다. 이는 Python 언어 사양에 근거한 판단이며 직접 실행해 확인한 것은 아니다. 그 경우 비교 없이 성공 메시지 3줄이 출력되고 exit 0이 된다.
- 영향: `parity.txt`의 출력만으로는 실제 비교가 수행됐는지 구분할 수 없다. 증거 신뢰도 문제다.
- 최소 수정안: `assert before(frame) == after(frame), case`를 `if before(frame) != after(frame): raise SystemExit(f"mismatch at {case}")` 형태로 바꾸고, 성공 메시지에 실제 비교 횟수 카운터를 함께 출력한다. 누락 열 예외 비교의 `assert str(error) == ...`도 같이 바꾼다.
- 검증 방법: `-O`로 실행해도 비교가 수행되는지 확인하고, `after`를 의도적으로 깨뜨렸을 때 비영 exit 코드가 나오는지 확인한다.

## 5. [하] 파리티 비교가 같은 프레임 객체를 두 함수에 순차 전달한다

- 위치: `scripts/verify_task5.py`의 `assert before(frame) == after(frame)` 줄.
- 재현 조건: `before(frame)`가 먼저 호출되므로 `before`가 입력을 변형하면 `after`는 변형된 입력을 받는다.
- 영향: 실제로는 직후의 `pd.testing.assert_frame_equal(frame, original)`이 순 변형을 잡아내므로 구멍은 거의 닫혀 있다. 다만 동작 비교 결론이 두 번째 단정에 의존하는 구조여서 독립적이지 않다.
- 최소 수정안: `before(frame.copy(deep=True)) == after(frame.copy(deep=True))`로 각각 별도 복사본을 전달한다.
- 검증 방법: 같은 시드로 재실행해 출력이 동일한지 확인한다.

## 6. 과장이 아니라고 판단한 부분

- S5의 "`.gitignore`가 루트·하위 `.env` 제외, `.env.production`은 미제외"는 정확하다. `.gitignore`를 읽어 확인했다. 슬래시 없는 `.env` 패턴만 있어 모든 깊이에 적용되고 `.env.*`는 매칭되지 않는다. `env_audit.txt`의 `check-ignore` 출력과도 일치한다.
- "파일명 기준 검사이며 전체 이력의 키 문자열 감사가 아니다", "확인된 비밀값 노출은 없으며 폐기·재발급을 수행했다고 주장하지 않는다", S2의 미확인 표기, S8의 부분 완료 표기는 모두 근거 범위와 일치한다.
- `pytest_before.txt`와 `pytest_after.txt`는 98 passed, 4 warnings로 일치한다. 경고는 양쪽 모두 `prepare_photo.py:69`의 Pillow `getdata()` 폐기 예고다. before 로그의 경로가 임시 디렉터리(`task5-baseline-*`)로 찍혀 있어 README의 "기준 커밋을 임시 디렉터리에 풀어 실행"과 들어맞는다.

## 7. 코드 외 관찰

- `evidence/task5/claude_review_prompt.txt`, `claude_review_result.json`, `claude_review_status.md`, 이 문서, `TEAM_TASK_GUIDE.md`, `WEEK10_TASK5_AGENT_BRIEF.md`가 모두 untracked 상태다. 커밋 기준으로 제출한다면 포함 여부를 결정해야 한다.
- `claude_review_status.md`는 이전 샌드박스 호출이 응답 없이 중단된 상태를 기록한 문서다. 이 리뷰가 생긴 뒤에도 "리뷰 완료 건수 0건"이라는 서술이 남아 있으면 현재 상태와 어긋난다. 단, 이 문서는 AI 리뷰이므로 "실제 교차 리뷰 2건 대기"라는 README의 상태는 그대로 유지하는 것이 맞다.

## 권장 처리 순서

2번과 4번을 먼저 고치면 증거의 재현성이 가장 크게 올라간다. 이어서 3번, 5번, 7번을 처리한다. 1번은 수정 대상이 없고 날짜 표기만 다듬으면 된다.
