# 사진 평가 AI (아트서강)

사진 폴더를 읽어 VLM으로 구도·빛·색·기술 점수와 감성 태그를 매기고, 그 결과를 pandas로 정제·집계해 월별 추이와 상·하위 태그를 뽑는 파이프라인이다. 현재 VLM 호출은 Mock 응답만 지원한다.

모듈별 입출력 타입, 예외, 허용 어휘의 기준 문서는 [docs/schema.md](docs/schema.md)다. 이 README는 저장소의 지도 역할만 한다.

## 실행

```bash
python -m venv .venv && source .venv/bin/activate
pip install pandas pillow pytest

python main.py --image-dir <사진 폴더> --hint "배경 위주 풍경" --output results/summary.json
python -m pytest -q
```

- 루트 `requirements.txt`는 아직 없다. 11주차 Task 1에서 추가할 예정이다.
- `--image-dir` 기본값은 `sample_images`인데 이 폴더는 저장소에 없으므로 경로를 직접 넘겨야 한다.
- CLI의 `--use-mock`은 항상 켜져 있고 끄는 옵션이 없다. Mock을 끄면(`USE_MOCK=false`) 실제 API 경로는 `NotImplementedError`를 낸다.
- 테스트는 2026-11-16 로컬(Python 3.14.6)에서 126개가 통과했다. Pillow의 `getdata()` 폐기 예고 경고 12건이 함께 나온다.

## 파이프라인 흐름

```text
사진 폴더
  └─[1] prepare_photo            이미지 전처리, 허용된 EXIF만 추출
  └─[2] analyze_with_gemini      VLM 요청 구성 → llm_client 호출(Mock)
        └─[3] validate_vlm_response  응답 JSON 검증
  └─    pipeline.py              태그 평탄화, id/captured_at 붙여 DataFrame 구성
  └─[4] clean_analysis_dataframe 점수 클리핑, 날짜 정규화
  └─[5] aggregate_photo_insights 총 건수, 월별 추이, 상·하위 태그
  └─    run_pipeline 반환        집계 결과 + hint, 처리·실패 건수
```

| 단계 | 폴더 | 공개 함수 | 9주차 담당 |
|---|---|---|---|
| 1 | `prepare_photo/` | `prepare_photo(image_path)`, `extract_safe_exif(image)` | 류시향, 김도혁 |
| 2 | `analyze_with_gemini/` | `analyze_with_gemini(photo, model, hint)`, `llm_client.generate_analysis(...)` | [9주차 체크리스트](9주차_체크리스트.md)에 없음 |
| 3 | `validate_vlm_response/` | `validate_vlm_response(raw_text)` | 신비 |
| 4 | `clean_analysis_dataframe/` | `clean_analysis_dataframe(df_raw)` | 박상현 |
| 5 | `aggregate_photo_insights/` | `aggregate_photo_insights(df_analyses)` | 하정윤 |
| 통합 | `pipeline.py`, `main.py` | `run_pipeline(image_dir, hint, model, use_mock)` | 하정윤 (10주차) |

4·5단계가 요구하는 필수 열은 `id`, `final_score`, `captured_at`, `tags`이고, `tags`는 문자열 리스트여야 한다. 상·하위 태그는 2회 이상 등장한 태그만 집계한다.

## 폴더 구조

```text
.
├── main.py                      CLI 진입점
├── pipeline.py                  1~5단계를 잇는 run_pipeline
│
├── prepare_photo/               [1] 전처리 모듈
├── analyze_with_gemini/         [2] VLM 요청 모듈
│   ├── analyze_with_gemini.py
│   └── llm_client.py            USE_MOCK 환경 변수로 Mock/Real 전환
├── validate_vlm_response/       [3] 응답 검증 모듈
├── clean_analysis_dataframe/    [4] 정제 모듈
├── aggregate_photo_insights/    [5] 집계 모듈 (구현 파일은 photo_analytics.py)
│
├── prompts/                     VLM 지시문 템플릿과 요청·반환 규격 안내
├── tests/                       모듈을 가로지르는 테스트
│   ├── test_integration.py      파이프라인 통합 테스트
│   ├── test_llm_client.py       Mock 전환·로그 테스트
│   └── pytest_log.txt           10주차 전체 실행 로그
│
├── docs/
│   ├── schema.md                모듈 간 입출력 계약 (기준 문서)
│   ├── task3.md                 10주차 Task 3 기록 (박상현)
│   └── week10_task5.md          10주차 Task 5 기록 (김도혁)
├── ai_log/                      주차별·팀원별 AI 협업 기록
│   ├── 10주차_<이름>.md
│   ├── task3_evidence/          Task 3 pytest 로그, 검증 스크립트
│   └── task5_evidence/          Task 5 pytest 로그, 감사·검증 스크립트, 리뷰
│
├── 9주차_체크리스트.md           9주차 제출 체크리스트
├── 10주차_체크리스트.md          10주차 제출 체크리스트
└── SECURITY_CHECKLIST.md        저장소 전체 보안 점검 (5주차 S1~S10 기준)
```

### 모듈 폴더 안의 공통 파일

각 모듈 폴더는 9주차의 "설계 → 프롬프트 → 생성 → 리딩 → 테스트 → 커밋" 사이클 산출물을 함께 담고 있다.

| 파일 | 내용 |
|---|---|
| `<모듈>.py` | 구현 |
| `test_*.py` 또는 `*_test.py` | 해당 모듈 단위 테스트 (루트에서 `pytest`를 돌리면 함께 수집됨) |
| `prompt_log.md`, `copilot_prompt.txt` | AI에 준 프롬프트와 수정 이력 |
| `report.md` | 설계와 검증 보고 |
| `CHECKLIST.md`, `SECURITY_CHECKLIST.md` | 모듈 단위 제출·보안 점검 |
| `evidence/` | 테스트 로그, AI 원본 코드 등 근거 자료 (있는 모듈만) |

### 헷갈리기 쉬운 곳

- `validate_vlm_response/`에는 `validate_vlm_response.py`와 `validate_vlm.py`가 둘 다 있다. 파이프라인이 불러오는 것은 `validate_vlm_response.py`이고, `validate_vlm.py`는 빈 줄 하나만 다른 사본으로 어디서도 쓰이지 않는다.
- `analyze_with_gemini`는 검증기를 import하지 않고 `run_path()`로 파일 경로에서 직접 읽는다. `validate_vlm_response/`에는 `__init__.py`가 없다.
- `aggregate_photo_insights/`에도 `__init__.py`가 없어서 `from aggregate_photo_insights.photo_analytics import ...`는 루트에서 실행할 때만 동작한다.
- 단위 테스트는 모듈 폴더 안에, 통합 테스트는 `tests/`에 있다.

## 주차별 기록

| 주차 | 내용 | 기록 위치 |
|---|---|---|
| 9주차 | 함수 5개를 팀원별로 구현 | [9주차_체크리스트.md](9주차_체크리스트.md), 각 모듈 폴더 |
| 10주차 | 파이프라인 통합, Mock 전환, 통합 테스트, 리팩터링·보안 감사 | [10주차_체크리스트.md](10주차_체크리스트.md), [docs/task3.md](docs/task3.md), [docs/week10_task5.md](docs/week10_task5.md), `ai_log/` |
| 11주차 | Streamlit 대시보드 (진행 중) | 아래 참고 |

10주차 Task 5(타 모듈 리팩터링, 코드 리뷰, 보안 감사)의 상세 기록은 이전에 이 README에 있었고, 지금은 [docs/week10_task5.md](docs/week10_task5.md)로 옮겼다. 보안 점검 결과는 [SECURITY_CHECKLIST.md](SECURITY_CHECKLIST.md)에 있다.

### 11주차에 추가될 파일

4·5단계 모듈 위에 CSV 업로드 대시보드를 얹는다. 아래 파일은 아직 저장소에 없다.

| 파일 | 역할 |
|---|---|
| `app.py` | Streamlit UI. 입출력만 담당 |
| `backend.py` | Streamlit에 의존하지 않는 어댑터. 4·5단계 함수를 호출 |
| `requirements.txt` | 루트 의존성 목록 |
| `sample_data/` | 정상 / CP949 / 컬럼 누락 샘플 CSV 3종 |
| `tests/test_backend.py`, `tests/test_csv_scenarios.py` | 백엔드와 CSV 시나리오 테스트 |
| `docs/week11_verification.md` | 수동 검증 기록 |
