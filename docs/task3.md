# Task 3 진행 및 제출 증빙 — 박상현

기준: `5795dad` / 브랜치: `psh-task3-mock`. 팀원의 임시 Task 3 이후 커밋은 포함하지 않은 상태에서 진행합니다.

| 요구사항 | 현재 상태 | 파일 |
|---|---|---|
| USE_MOCK 스위치 | 환경 변수 단일 기준, 기본 true, 잘못된 값 거부 | `analyze_with_gemini/llm_client.py` |
| 실행 시 [MOCK] 표식 | INFO 로그, 사용자 입력 내용 출력 안 함 | 동일 |
| 실제 API 교체 경계 | 동일 인자·str 반환 계약, 현재 NotImplementedError | `_generate_real` |
| prompts/ 템플릿 | 기존 지시문을 분리하고 실제 요청에 연결 | `prompts/photo_analysis_prompt.txt` |
| 입력·반환 문서 | 함수 타입 힌트·docstring, 요청·반환 규격 안내 | `prompts/README.md` |
| 테스트 | 전체 126개 통과, 신규 Task 3 테스트 23개 | `tests/test_llm_client.py` |
| AI 기록 2건 | 기록 1 준비, 후속 리팩터링 기록 미완료 | `ai_log/10주차_박상현.md` |
| 커밋 | 사용자 검토 후 직접 실행 예정 | 현재 미커밋 |

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

## 범위와 후속 작업

실제 Gemini API·키·네트워크를 사용하지 않습니다. 테스트는 가상 바이트와 합성 이미지로 실행합니다. 실제 모델 품질이나 이미지 내 개인정보 제거를 검증한 작업은 아닙니다. 기존 전처리의 업로드 바이트·지원 확장자 정책은 별도 담당 범위로 유지했습니다.

기존 파이프라인은 use_mock 값을 프로세스 환경 변수에 반영하며 호출 후 복원하지 않습니다. 병렬 실행 시 모드 격리 및 CLI의 비Mock 선택 옵션은 Task 1과 협의할 사항입니다. 이번 테스트의 monkeypatch는 테스트 사이 환경을 복원합니다.

현재 main에는 팀원의 임시 Task 3 파일이 있으므로 PR에서 `llm_client.py`, `prompts/photo_analysis_prompt.txt`, `tests/test_llm_client.py`의 충돌이 생길 수 있습니다. 통합 시 설정 정책과 프롬프트 파일의 의미를 비교하여 하나의 구현으로 정리하고 전체 테스트를 재실행해야 합니다.

이번 단계는 기능 구현입니다. 사용자의 기능 커밋 후 별도 리팩터링을 진행하고, 실제 해시와 두 번째 AI 기록을 추가합니다. 기존 공통 README·보안 체크리스트·다른 팀원의 AI 기록은 수정하지 않았습니다.
