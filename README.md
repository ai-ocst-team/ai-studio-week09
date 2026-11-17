# 사진 평가 AI (아트서강)

사진 폴더를 읽어 VLM으로 구도·빛·색·기술 점수와 감성 태그를 매기고, 그 결과를 pandas로 정제·집계해 월별 추이와 상·하위 태그를 뽑는 파이프라인이다. 현재 VLM 호출은 Mock 응답만 지원한다.

11주차에는 사진 분석 결과 CSV를 올려 점수·촬영 월·태그별 통계를 확인하는 Streamlit 대시보드를 추가했다. CSV 대시보드는 사진을 새로 평가하거나 LLM을 호출하지 않는다. 모듈별 입출력 계약은 [docs/schema.md](docs/schema.md)를 참고한다.

## 11주차 Streamlit 대시보드 실행 및 설계 안내

저장소 루트에서 Python 가상환경을 준비한 뒤 실행한다. 아래는 Windows PowerShell 예시다.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

macOS/Linux에서는 가상환경 활성화 명령을 `source .venv/bin/activate`로 바꾼다. 활성화가 제한된 Windows 환경에서는 `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`와 `.\.venv\Scripts\python.exe -m streamlit run app.py`를 사용할 수 있다. `python app.py`로 실행하지 않는다. 실행 후 브라우저에서 터미널에 표시된 Local URL(기본 `http://localhost:8501`)을 연다.

### 업로드 및 대시보드

필수 컬럼은 `id`, `final_score`, `captured_at`, `tags`다. 점수 범위는 0~10이고 날짜는 ISO 형식을 사용하며, `tags`는 JSON 배열 문자열 또는 쉼표 구분 문자열이다. 날짜 결측은 허용한다.

| 샘플 | 기대 결과 (최소 점수 0, 태그 전체) |
|---|---|
| [UTF-8 정상 CSV](sample_data/sample_photos.csv) | 14장, 평균 7.66점, 유효 촬영일 12건 |
| [CP949 CSV](sample_data/sample_photos_cp949.csv) | UTF-8 실패 후 `seek(0)`·CP949 재시도; 정상 CSV와 같은 값·한글 태그 |
| [필수 컬럼 누락 CSV](sample_data/sample_photos_broken.csv) | `final_score` 누락 안내 후 분석 중단 |

업로드 전에는 안내 메시지와 `st.stop()`으로 분석을 중단한다. 업로드 후 사이드바의 최소 점수·태그 필터를 바꾸면 사진 수·평균 점수·유효 촬영일 지표, 월별 차트, 태그 차트와 상세 표가 즉시 바뀐다. 예를 들어 `건축도시` 태그만 선택하면 3장·평균 7.83점이다. 태그 차트는 2회 이상 등장한 태그 중 상위 **최대 5개**이며, 상세 표는 원본 CSV 그대로가 아닌 정제·필터링된 데이터다. 필터 결과가 0건이면 평균은 `-`로 표시된다.

### UI와 백엔드의 역할

```text
app.py: 업로드 읽기(UTF-8 → CP949), 위젯·상태·오류 안내·화면 출력
  → backend.py: 필수 컬럼 검증, tags 파싱, 점수·태그 필터, KPI·차트 데이터 구성
    → clean_analysis_dataframe: 기존 점수·날짜 정제
    → aggregate_photo_insights: 기존 통계 집계
```

`app.py`의 `pd.read_csv`는 파일 입력 처리이며 `groupby`, `to_datetime`, `clip` 같은 데이터 가공은 포함하지 않는다. `backend.py`는 Streamlit을 import하지 않고 기존 두 백엔드 함수를 호출한다. CSV 경로에는 실제 VLM/API 호출이나 API 키가 필요하지 않으며, 업로드 데이터를 저장하는 앱 코드도 없다(로컬 실행 기준).

### session_state를 사용하는 이유

필터를 조작할 때마다 Streamlit이 스크립트를 다시 실행하므로, 정제된 DataFrame을 `st.session_state.prepared_df`에 보관해 같은 업로드를 반복 파싱·정제하지 않는다. `uploaded_file_sig`에 파일 ID·이름·크기를 저장해 파일 교체를 판별하고, 두 상태 키는 `if ... not in st.session_state`로 최초 한 번 초기화한다. 파일 교체·업로드 해제·입력 오류 때는 관련 데이터와 필터 상태를 초기화하고, 같은 파일의 필터 변경에는 저장된 데이터를 재사용한다.

### 검증 및 기록

```powershell
python -m pytest -q -o addopts=""
```

팀원의 [브라우저 검증 보고서](docs/week11_verification.md)와 [192개 전체 테스트 로그](tests/pytest_week11_log.txt)에 초기 화면·정상·CP949·컬럼 누락 시나리오가 기록돼 있다. 기존 추가 옵션에 의한 테스트 선택 제외를 피하려고 위 명령은 `addopts`를 비운다.

Task 5에서는 2026-11-17 기준 코드 `d09e75b`를 점검해 **192 passed, 12 warnings**를 재확인했다(Python 3.12.14, pandas 3.0.1, Pillow 13.0.0, pytest 9.1.1). 경고는 기존 Pillow `getdata()` 폐기 예고다. [Task 5 실행 증빙](ai_log/week11_task5_evidence/audit_result.txt), [재현 스크립트](ai_log/week11_task5_evidence/audit.py), [박상현 AI 과정 기록](ai_log/11주차_박상현.md)을 참조한다. 재현 스크립트는 저장소 루트에서 `python -B ai_log/week11_task5_evidence/audit.py`로 실행한다.

이번 Task 5는 코드 검수·CSV 함수 실행·pytest 검증이다. 별도 Streamlit 설치나 브라우저 수동 검증을 새로 수행하지 않았으며, 브라우저 실행 증빙은 Task 4 담당자의 기록과 구분한다. 보안 검사 범위와 확인 한계는 [11주차 보안 재점검](SECURITY_CHECKLIST.md#11주차-보안-재점검--2026-11-17)에 적었다.

## 기존 사진 폴더 CLI 실행 (9~10주차)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python main.py --image-dir <사진 폴더> --hint "배경 위주 풍경" --output results/summary.json
python -m pytest -q
```

- `--image-dir` 기본값은 `sample_images`인데 이 폴더는 저장소에 없으므로 경로를 직접 넘겨야 한다.
- CLI의 `--use-mock`은 항상 켜져 있고 끄는 옵션이 없다. 파이프라인은 `use_mock` 인자로 환경 변수를 덮어쓰므로 환경 변수만 false로 설정해도 이 CLI에서는 Mock이 유지된다. Python에서 `run_pipeline(..., use_mock=False)`로 유효 이미지를 처리하면 미구현 API 경계의 `NotImplementedError`가 발생한다.
- 기존 10주차 테스트 기록: 2026-11-16 로컬(Python 3.14.6)에서 126개가 통과했다. Pillow의 `getdata()` 폐기 예고 경고 12건이 함께 나온다.

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
├── app.py                       11주차 Streamlit UI
├── backend.py                   CSV 대시보드 어댑터
├── requirements.txt             의존성 목록
├── sample_data/                 CSV 샘플 3종 및 생성 스크립트
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
│   ├── test_backend.py          대시보드 백엔드 테스트
│   ├── test_csv_scenarios.py     CSV 시나리오 테스트
│   ├── pytest_week11_log.txt     11주차 전체 테스트 로그
│   └── pytest_log.txt           10주차 통합 테스트 5개 로그
│
├── docs/
│   ├── schema.md                모듈 간 입출력 계약 (기준 문서)
│   ├── task3.md                 10주차 Task 3 기록 (박상현)
│   ├── week11_verification.md   브라우저 검증 보고서
│   ├── screenshots/             검증 캡처
│   └── week10_task5.md          10주차 Task 5 기록 (김도혁)
├── ai_log/                      주차별·팀원별 AI 협업 기록
│   ├── 10주차_<이름>.md
│   ├── 11주차_<이름>.md
│   ├── week11_task5_evidence/    박상현 검수 스크립트·실행 결과
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
| 11주차 | Streamlit 대시보드 | 아래 파일 표, [수동 검증](docs/week11_verification.md), `ai_log/11주차_<이름>.md` |

10주차 Task 5(타 모듈 리팩터링, 코드 리뷰, 보안 감사)의 상세 기록은 이전에 이 README에 있었고, 지금은 [docs/week10_task5.md](docs/week10_task5.md)로 옮겼다. 보안 점검 결과는 [SECURITY_CHECKLIST.md](SECURITY_CHECKLIST.md)에 있다.

### 11주차 파일

4·5단계 모듈 위에 CSV 업로드 대시보드를 연결했다. 아래 파일은 main에 병합돼 있다. Task 5의 문서·감사 변경은 별도 개인 브랜치에서 검토 후 PR로 반영한다.

| 파일 | 역할 |
|---|---|
| `app.py` | Streamlit UI. 입출력만 담당 |
| `backend.py` | Streamlit에 의존하지 않는 어댑터. 4·5단계 함수를 호출 |
| `requirements.txt` | 루트 의존성 목록 |
| `sample_data/` | 정상 / CP949 / 컬럼 누락 샘플 CSV 3종 |
| `tests/test_backend.py`, `tests/test_csv_scenarios.py` | 백엔드와 CSV 시나리오 테스트 |
| `docs/week11_verification.md` | 수동 검증 기록 |
