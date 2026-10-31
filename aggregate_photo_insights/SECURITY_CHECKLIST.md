# 3.6 AI·데이터 보안 체크리스트 (이후 모든 제출물에 첨부)

- **과제명**: AI 오케스트레이션 스튜디오 9주차 과제
- **팀명**: 아트서강
- **대상 모듈**: `photo_grader/photo_analytics.py` (`aggregate_photo_insights`)
- **작성자**: 하정윤

---

## 보안 체크리스트 점검표

| 구분 | 번호 | 점검 항목 | 확인 | 점검 및 조치 결과 |
|:---:|:---:|:---|:---:|:---|
| **데이터** | **S1** | 제출물에 실존 인물의 실명·전화번호·이메일 등 PII가 포함되지 않았다 (더미 데이터 사용) | ☑ | 가상 ID 및 통제 어휘 태그 등 비식별화된 데이터셋만 사용 (PII 유출 0건) |
| **데이터** | **S2** | 외부 AI(챗봇·API)에 기업 기밀·타인 코드·PII를 입력하지 않았다 | ☑ | Gemini WebUI 프롬프트에 민감 정보 및 실데이터 입력 원천 배제 |
| **데이터** | **S3** | 외부 데이터 사용 시 출처·라이선스를 확인하고 PII 열을 비식별 처리했다 | ☑ | 사진 메타데이터 중 GPS IFD 및 카메라 시리얼 번호 원천 제거 스키마 준수 |
| **키 관리** | **S4** | API 키·비밀번호가 소스코드에 하드코딩되어 있지 않다 | ☑ | 소스코드 내 API 키, 토큰, 패스워드 등 하드코딩된 비밀값 0건 확인 |
| **키 관리** | **S5** | .env 파일이 .gitignore에 등록되어 있고, git ls-files 확인 결과 추적되지 않는다 | ☑ | 저장소 최상위에 `.gitignore` 적용 완료 (`.env`, `.venv/`, `__pycache__/` 추적 배제) |
| **키 관리** | **S6** | 커밋 히스토리에 키가 노출된 적이 없다 (노출 시 폐기·재발급 완료를 명기) | ☑ | Git 커밋 히스토리 전체 점검 결과 키 노출 이력 없음 확인 |
| **키 관리** | **S7** | 키·비밀 값을 print/log/스크린샷으로 전체 출력하지 않았다 | ☑ | 테스트 코드, 실행 로그, 콘솔 출력에 비밀값 출력 로직 없음 |
| **AI 사용** | **S8** | AI 사용 내역(프롬프트·채택·수정)을 과제 규정에 따라 기록·첨부했다 | ☑ | `prompt_log.md` 및 `report.md`에 프롬프트 원문, 결함, 수정 내역 상세 기록 |
| **AI 사용** | **S9** | (LLM 기능 포함 시) 사용자 입력 검증과 출력 검증(형식 확인)을 적용했다 | ☑ | DataFrame 필수 컬럼 검증, NaN 처리, final_score 클리핑 및 반환 딕셔너리 규격 검증 |
| **AI 사용** | **S10** | (LLM 기능 포함 시) 시스템 프롬프트에 비밀 정보를 포함하지 않았다 | ☑ | 프롬프트에 모듈 역할 및 시그니처 명세만 포함, 비밀 정보 일절 배제 |

---

## 세부 증빙

### 1. `.gitignore` 설정 및 Git 추적 상태 검증 (S5)
저장소 루트에 `.gitignore`가 설정되어 있으며, `.env`, `.venv/`, `__pycache__/` 파일이 정상적으로 Git 추적 대상에서 제외되어 있음을 확인함.

```bash
$ git status
On branch feat/hjy
Untracked files:
	.gitignore
	aggregate_photo_insights/photo_analytics.py
	aggregate_photo_insights/prompt_log.md
	aggregate_photo_insights/report.md
	aggregate_photo_insights/test_photo_analytics.py
	aggregate_photo_insights/SECURITY_CHECKLIST.md
```

### 2. PII 및 시크릿 스캔 검증 (S1, S4, S7)
- 소스 코드(`photo_analytics.py`, `test_photo_analytics.py`) 내에 어떠한 실존 인물 정보(전화번호, 이메일, 주소 등)나 하드코딩된 API 토큰이 존재하지 않음을 전수 스캔 완료함.
