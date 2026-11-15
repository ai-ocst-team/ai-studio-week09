# Task 3 진행 및 제출 증빙 — 박상현

기준: `5795dad` / 브랜치: `psh-task3-mock`. 개인 구현·리팩터링 후 최신 `origin/main` (`8b1622f`)을 로컬 병합했습니다. 로컬 통합 커밋 `b3c0a18` 생성·push 후 [PR #10](https://github.com/ai-ocst-team/ai-studio-week09/pull/10)을 통해 팀 main에 반영했습니다(PR 병합 커밋 `5d4c617`).

| 요구사항 | 현재 상태 | 파일 |
|---|---|---|
| USE_MOCK 스위치 | 환경 변수 단일 기준, 기본 true, 잘못된 값 거부 | `analyze_with_gemini/llm_client.py` |
| 실행 시 [MOCK] 표식 | INFO 로그, 사용자 입력 내용 출력 안 함 | 동일 |
| 실제 API 교체 경계 | 동일 인자·str 반환 계약, 현재 NotImplementedError | `_generate_real` |
| prompts/ 템플릿 | 기존 지시문을 분리하고 실제 요청에 연결 | `prompts/photo_analysis_prompt.txt` |
| 입력·반환 문서 | 함수 타입 힌트·docstring, 요청·반환 규격 안내 | `prompts/README.md` |
| 테스트 | 전체 126개 통과, 신규 Task 3 테스트 23개 | `tests/test_llm_client.py` |
| AI 기록 2건 | 기능 구현 및 책임 분리 리팩터링 기록·실제 해시 반영 | `ai_log/10주차_박상현.md` |
| 커밋 | 기능·별도 refactor·로컬 통합 및 PR 병합 완료 | `8b34747`, `f65dfc2`, `b3c0a18`, `5d4c617` |

## 재현

Python 환경에 pandas, Pillow, pytest가 필요합니다. 저장소 루트에서 실행합니다.

```powershell
python -B -X utf8 -m pytest -q --tb=short -p no:cacheprovider
```

검증 환경의 임시 경로 문제로 실제 실행은 별도의 `--basetemp`를 지정했습니다. 로그 머리말에 실행 명령과 시각을 기록했습니다. pytest는 basetemp를 정리하므로 사용자 데이터가 있는 폴더를 지정하지 않습니다.

- [최초 기준 실행: 임시 경로 오류](../ai_log/task3_evidence/pytest_baseline.txt)
- [기준 재실행: 103 passed](../ai_log/task3_evidence/pytest_baseline_retry.txt)
- [구현 전 새 요구사항 테스트: 14 failed, 9 passed](../ai_log/task3_evidence/pytest_task3_before.txt)
- [기능 반영 후 전체: 126 passed](../ai_log/task3_evidence/pytest_feature.txt)
- [리팩터링 후 전체: 126 passed](../ai_log/task3_evidence/pytest_refactor.txt)
- [최신 main 통합 후 전체 테스트](../ai_log/task3_evidence/pytest_merge.txt)
- [변경 전후 168건 동작 비교](../ai_log/task3_evidence/refactor_parity.txt)

## 리팩터링 검토

`generate_analysis`의 입력 검사·설정 해석·가상 응답 생성을 각각 `_validate_request`, `_is_mock_enabled`, `_generate_mock`로 옮겼습니다. 공개 함수는 세 역할을 연결하는 분기만 남깁니다. 반환값·예외·로그·시그니처를 보존했으며 성능 개선을 주장하지 않습니다.

기능 커밋 `8b347476d41efcea4c9fa6805dab38fcf9f7405b`는 사용자가 2026-11-15 10:33:35 KST에 직접 실행했습니다. 이후 리팩터링 커밋 `f65dfc26cdb6db4f113cf8a31fea39c35a5f13ca`를 2026-11-15 10:37:29 KST에 직접 실행했습니다.

## 범위와 후속 작업

실제 Gemini API·키·네트워크를 사용하지 않습니다. 테스트는 가상 바이트와 합성 이미지로 실행합니다. 실제 모델 품질이나 이미지 내 개인정보 제거를 검증한 작업은 아닙니다. 기존 전처리의 업로드 바이트·지원 확장자 정책은 별도 담당 범위로 유지했습니다.

기존 파이프라인은 use_mock 값을 프로세스 환경 변수에 반영하며 호출 후 복원하지 않습니다. 병렬 실행 시 모드 격리 및 CLI의 비Mock 선택 옵션은 Task 1과 협의할 사항입니다. 이번 테스트의 monkeypatch는 테스트 사이 환경을 복원합니다.

최신 main `8b1622f`를 자동 커밋 없이 병합하면서 겹친 세 파일을 정리했습니다. LLM 클라이언트·프롬프트·테스트는 `f65dfc2`의 구현을 유지하고, 팀 스키마 문서는 환경 변수 하나로 전환하는 정책과 실제 프롬프트 파일 로딩 방식에 맞췄습니다. 팀원의 집계 보고서 변경은 그대로 반영했습니다. 통합 후 전체 pytest는 **126 passed, 12 warnings in 3.39s**로 통과했습니다. 경고는 기존 Pillow getdata 폐기 예고입니다.

Task 3 코드의 커밋·push·PR 병합과 로컬 main 동기화를 완료했습니다. LMS 제출 및 팀 전체 체크리스트 충족 여부는 별도 확인 사항입니다. 이번 완료 상태 갱신은 문서만 수정했으므로 테스트를 재실행하지 않았으며, 위 테스트 결과는 통합 시점의 실행 기록입니다. 기존 보안 체크리스트·다른 팀원의 AI 기록은 수정하지 않았습니다.
