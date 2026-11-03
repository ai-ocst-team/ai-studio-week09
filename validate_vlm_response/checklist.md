# 4. 9주차 과제 제출 체크리스트

20240782 신비

| 번호 | 확인 항목 | 확인 | 점검 및 조치 결과 |
|:---:|---|:---:|---|
| 1 | **팀원 1인당 최소 1개 함수, 사이클 6단계 완주** | ☑ | **개인 작업 완료:** `validate_vlm_response(raw_text: str) -> PhotoAnalysis` 구현, AI 생성·코드 리딩·수정·테스트·커밋·Push 완료.|
| 2 | **함수당 테스트 3개 이상(정상·경계·예외), pytest 전체 통과** | ☑ | **개인 작업 완료:** 정상 JSON·마크다운·점수 경계·잘못된 JSON·점수 초과·허용되지 않은 태그·잘못된 초점 자료형에 대한 **7개 테스트 전체 통과**. 전체 팀 함수의 테스트 결과 및 README/로그의 통과 출력 첨부는 확인 필요. |
| 3 | **`prompt_log.md`: 프롬프트 원문 + 발견 결함 + 수정 내역 + 커밋 해시** | ☑ | `prompt_log.md` 작성 및 Push. `focus_status=[]`에서 발생한 `TypeError`를 `ValueError`로 처리하도록 수정한 이력 확인. 
| 4 | **함수당 2커밋 이상, 의미 있는 커밋 메시지** | ☑ | `d739731` — `feat: add AI-generated VLM response validator` (생성 원본), `aa5dea9` — `fix: validate focus status and add pytest tests` (수정·테스트). |
| 5 | **`.gitignore`(`.env`, `.venv/`, `__pycache__/`) 및 보안 체크리스트 포함** | ☑ | 프로젝트 최상위 폴더에서 실행. |
| 6 | **LLM 의존 기능의 Mock 격리 및 `[MOCK]` 표시 (해당 시)** | ☑ | 해당없음 |
| 7 | **저장소에 PII·실데이터·API 키가 없음을 전원 교차 확인** | ☑ | 해당없음 |

## 개인 담당 함수 완료 기록

| 항목 | 확인 | 근거 |
|---|:---:|---|
| `validate_vlm_response` 구현 | ☑ | VLM 응답 유효성 검사 함수 작성 및 Push 완료 |
| Copilot 생성 원본 커밋 | ☑ | `d739731` |
| 코드 리딩과 결함 수정 | ☑ | `focus_status`에 리스트가 들어올 때 `TypeError`가 발생하던 문제 수정 |
| 수정·테스트 커밋 | ☑ | `aa5dea9` |
| pytest 전체 통과 | ☑ | 개인 함수 대상 7개 테스트 통과 `prompt_log.md` |
| `prompt_log.md` 작성 및 Push | ☑ | |
| 작업 브랜치 원격 Push | ☑ | `feature/validate_vlm_response` |
| PR 생성·병합 및 팀 저장소 전체 확인 | ☑ | |
