# 증빙 안내

- `copilot_original_2026-11-02/`: 생성 완료 시점의 구현·테스트·프롬프트·완료 화면 사본과 manifest.
- `copilot_chat_original.json`: 실제 Copilot 내보내기 원본. 사용자 경로 및 도구 실행 기록을 포함합니다.
- `pytest_copilot_result.txt`: 최초 32개 테스트 통과 출력.
- `pytest_regression_before_fix.txt`: 새 회귀 테스트가 수정 전 코드에서 실패한 출력.
- `pytest_after_fix.txt`: 로컬 수정 완료 후 33개 테스트 통과 출력.
- `pytest_repository_check.txt`: 팀 저장소 사본의 개인 폴더에서 33개 테스트 통과 출력(2026-11-03 KST).
- `review_fix.diff`, `code_review.txt`: 실제 결함과 검토·수정 기록.
- `copilot_chat_verification.json`, `records_verification.json`: 각 기록 시점의 검증 결과입니다. 현재 Git 상태나 현재 모든 파일의 해시를 검증하는 보고서가 아닙니다.

일부 증빙의 도구 명칭 헤더 및 manifest 설명은 사용자가 이후 수정한 사본을 그대로 옮겼습니다. 원본 대화 JSON과 구분하며, 수정된 헤더를 도구 출처의 독립 증거로 사용하지 않습니다. 이후 문서 및 증빙 헤더 변경으로 과거 검증 JSON의 일부 파일 해시는 현재 파일과 다를 수 있습니다. 과거 JSON은 재작성하지 않았습니다.

개발 지원 도구와 실제 Git 이력의 현재 설명은 상위 `prompt_log.md`와 `report.md`를 기준으로 합니다. 보관 원본 테스트는 `conftest.py`에서 중복 수집 대상에서 제외합니다.
