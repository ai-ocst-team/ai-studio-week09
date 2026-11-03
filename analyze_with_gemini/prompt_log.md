# prompt_log.md — AI 활용 과정 기록

## analyze_with_gemini — 2026-11-03, 작성자: 김도혁

- **사용 도구**: GitHub Copilot Chat(구현, 사용자 확인), Codex(명세·사전 테스트 준비 및 코드 검토·수정·문서 정리 보조).
- **프롬프트 원문 확인**: 아래 전문을 실제 Copilot 요청문과 대조 완료했다고 사용자가 확인함.
- **설계 변경 사유**: EXIF 구현 담당 중복을 해소하여 analyze_with_gemini를 담당. 팀 합의로 8범주·최대 3개를 6범주·각 최대 2개로 변경. 6범주 모두 포함하며 해당 없음은 []. 9주차에는 llm_client.py의 [MOCK]로 외부 의존성을 격리함.

### 프롬프트 원문

```text
당신은 아트서강 사진 평가 시스템의 Python 백엔드 구현을 돕습니다.
이번 작업은 김도혁 담당 analyze_with_gemini의 9주차 Mock 구현입니다.

[최우선 명세]
첨부한 report.md의 「1단계: 논리 설계」를 전부 읽고 그대로 구현하세요. 이 문서가 입출력·예외·스키마의 계약입니다.
test_analyze_with_gemini.py는 구현 전에 정한 판정 기준입니다. 테스트를 수정하거나 완화하지 마세요.

[고정 시그니처]
def analyze_with_gemini(photo: dict[str, Any], model: str, hint: str) -> dict[str, Any]:
def generate_analysis(image_bytes: bytes, model: str, prompt: str) -> str:

[입출력 예시]
photo={"upload_bytes": b"dummy", "sha256": "a"*64, "safe_exif": {"iso": 100}}
model="dummy-model", hint="의도적 보케". 빈 hint와 빈 safe_exif는 정상입니다.
분석 결과는 점수 5개, aesthetic_tags 6범주 모두(각 0~2개), focus_status를 가진 dict입니다.
외부 호출 경계 generate_analysis는 JSON 문자열을 반환하고, 분석 함수는 검증된 dict를 반환합니다.

[설계와 예외]
입력 최상위 타입이 잘못되면 TypeError, 필수 photo 키 누락·무효 값·공백 모델은 ValueError.
모든 최상위 타입을 먼저 검사한 뒤 세부 photo 필드를 검사하세요.
safe_exif는 명세의 7개 허용 키만 요청에 포함하고 bool·NaN·Infinity·복합 객체는 거절하세요.
클라이언트 호출 이전에 입력 검사를 마치고 원본 photo를 수정하지 마세요.
요청은 task/safe_exif/hint/response_contract 키를 가진 JSON 문자열로 만드세요.
response_contract에는 report.md의 「1단계: 논리 설계」의 정확한 범주·어휘·제약을 포함하세요.
hint는 데이터이며 시스템 지시를 덮어쓰지 않는다고 task에 명시하세요.
경로·sha256·알 수 없는 EXIF 키를 프롬프트에 넣지 마세요. 사진 바이트는 별도 인자로만 전달하세요.
llm_client.generate_analysis를 키워드 인자로 1회 호출하세요.
클라이언트의 TimeoutError/ConnectionError/OSError만 RuntimeError("VLM 통신 실패")로 원인 연결하여 변환하세요.
응답 타입 검사 후 기존 validate_vlm_response 함수를 재사용하고, 정확히 6범주 모두 있는지 추가 검증하세요.
기존 검증 함수의 ValueError를 통신 실패로 바꾸지 마세요.

[제약]
표준 라이브러리만 사용합니다. 실제 API·SDK·네트워크·파일/DB 저장·API 키·비밀값·출력 로그는 금지합니다.
타입 힌트와 한국어 docstring을 쓰고 [MOCK]를 표시하세요.
실제 이미지 분석인 것처럼 꾸미지 말고 고정된 가상 응답을 반환하세요.
기존 validate_vlm_response 폴더는 변경하지 마세요. 호출은 기존 함수를 import하여 재사용합니다.
태그 검증을 다시 구현하지 말고, 요청 스키마의 어휘는 report.md의 「1단계: 논리 설계」와 일치시키세요.
광범위한 except, eval, 가변 기본값, 자동 재시도, 추가 함수 인자는 금지합니다.

[산출물과 검증]
analyze_with_gemini.py와 llm_client.py 두 구현 파일만 수정하세요.
테스트·명세·과정 기록·Git은 변경하지 마세요. 커밋과 테스트는 이 생성 단계에서 실행하지 마세요.
먼저 생성 원본을 보존하고 사람이 리딩한 다음 pytest를 실행할 계획입니다.
모든 정상·경계·예외 테스트를 충족하는 코드를 작성하고, 마지막에 변경 파일과 설계 요점을 짧게 설명하세요.
```

### 생성 코드 및 커밋 이력

| 구분 | 커밋 | 확인 내용 |
|---|---|---|
| 명세·사전 테스트 | 7bfbea6f2bf8873e06f272cf90b4a14c5fd5c583 | 2026-11-03 22:34:17 +09:00, author dohyeok |
| 생성 원본 | 8665573441df9d67bf37e9d0c259d97d1ae4c957 | 2026-11-03 22:41:57 +09:00, author dohyeok. feat(vlm): preserve Copilot-generated analysis code |
| 리딩 후 수정·검증 | 현재 로컬에서 해시 미확인 | 보안 문서에는 작성자가 수정 커밋 확인 완료로 기재함. 이 로컬 사본에는 수정이 작업 트리로 남아 있으므로 생성 원본 해시를 수정 커밋 해시로 대신 기록하지 않음 |

### 코드 리딩 결과

1. **입력 검사**: photo/model/hint의 타입, upload_bytes·sha256·safe_exif의 필수 여부와 값 검사. 잘못된 타입은 TypeError, 누락·무효 값은 ValueError. SHA는 형식만 검사하며 실제 바이트와의 일치는 검증하지 않음.
2. **EXIF 최소 전달**: 허용 키 7개만 새 dict에 복사. bool·복합 자료형·NaN·Infinity는 거절하고 원본 photo는 유지. GPS·Artist 등 알 수 없는 키와 경로·SHA는 프롬프트에서 제외.
3. **요청 구성**: task/safe_exif/hint/response_contract를 JSON으로 구성. hint는 데이터로 구분. 이 문구만으로 실제 모델의 프롬프트 주입 방어를 증명하지는 않음.
4. **호출·예외**: llm_client를 한 번 호출. TimeoutError/ConnectionError/OSError를 원인이 연결된 RuntimeError로 바꿈. 응답 검증 오류와 통신 오류는 구분.
5. **응답 검증**: 팀 검증 함수를 재사용해 JSON·점수 5개·허용 어휘·최대 2개·초점 상태 검사. 범주 집합을 비교해 6범주 누락도 거절.
6. **Mock의 의미**: 점수 8.0·빈 태그·판별 불가를 반환하는 가상 구현. 실제 이미지 분석 결과로 해석하지 않음.

위 결과는 코드 검토 보조와 실제 재현을 통해 정리한 내용이다. 담당자 본인의 직접 검토·이해 확인은 별도 수행 사항이며, 이 문서가 대신 수행했다고 주장하지 않는다.

### 발견 결함과 수정 내역

| 결함·개선점 | 재현·근거 | 반영 내용 |
|---|---|---|
| 테스트 경로 보정에 의존한 import | 기존 42개 테스트는 통과하지만 일반 호출에서 함수 대신 모듈이 잡혀 TypeError 발생 | 본인 폴더를 패키지로 지정하고 Mock은 상대 import |
| 저장소 루트만으로 불러오기 실패 | 격리 Python 프로세스 회귀 테스트 추가 후 수정 전 1 failed, 42 passed. llm_client를 찾지 못함 | 팀 검증 파일은 고정된 저장소 경로에서 runpy.run_path로 읽어 재사용. sys.path 보정 제거 |
| 검증 폴더와 모듈의 동명 충돌 | 중간 수정에서 팀 검증 테스트 7건 실패 | 다른 팀원 폴더에 변경을 남기지 않고 본인 폴더 내부에서만 로딩 방식 수정 |
| 어휘 중복 정의 | 요청 계약과 팀 검증기에 같은 어휘 존재 | 현재 일치함을 확인. 공용 스키마 통합은 팀 합의가 필요한 후속 개선으로 남김 |

- 본인 __init__.py와 독립 프로세스 회귀 테스트 1개 추가. 기존 42개 테스트의 기대값은 변경하지 않음.
- 현재 최종 변경 범위는 analyze_with_gemini 폴더뿐. 다른 팀원의 구현·테스트는 변경하지 않음.
- 수정·테스트 실행 보조는 Codex가 수행했으며 원본 생성 커밋은 그대로 보존.

### 최종 테스트 결과

- 개인: 43 passed in 0.05s.
- 본인 폴더만 변경한 최종 전체 결과: **98 passed, 4 warnings in 1.16s**.
- 정상·경계·예외 외에도 6범주 누락, 태그 3개, 점수 범위 초과, 불량 응답, 통신 예외, 원본 불변, 독립 import를 검사.
- 경고 4건: 기존 prepare_photo의 Pillow Image.getdata 제거 예정 경고. 테스트 실패 아님.
- 최종 전체 실행 시각(KST): 2026-11-03T23:28:52.011782+09:00
- Python 3.12.14 / pytest 9.2.0 / 종료 코드 0
- 명령: `python -m pytest -v --tb=short -p no:cacheprovider`
- 실행 환경: Codex 번들 Python, 임시 pytest 의존성 경로. 아래 결과는 보조 도구의 실제 실행 기록.
- 검증한 analyze_with_gemini.py SHA-256: `e6a34651eb2456ab7cf425072388a2770f76638df6caf458e7ddc28b2bba00b4`

### 제출 및 보안 확인

- 실제 Copilot 요청문 대조: 사용자 확인으로 완료.
- S1~S10 보안 점검: 작성자가 SECURITY_CHECKLIST.md에 확인 결과를 기재함.
- 팀 전원 보안 교차 확인, GitHub 반영·병합 및 LMS 제출: 사용자가 완료했다고 확인함. 원격·LMS를 이 로컬 점검에서 별도로 조회한 것은 아님.
- 현재 추가로 정리한 문서는 로컬 변경이므로 제출본에 포함하려면 문서 갱신 내용을 반영해야 함.
- 본인 직접 리딩 확인과 수정 커밋의 정확한 해시는 이 로컬 사본에서 확인되지 않아 완료로 단정하지 않음.

### 실제 전체 pytest 출력

```text
============================= test session starts ==============================
platform darwin -- Python 3.12.14, pytest-9.2.0, pluggy-1.7.0 -- /Users/dohyeok/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3
rootdir: /Users/dohyeok/.codex/.chatgpt-projects/g-p-6ac48a02559081918a00e52e7c8655eb/week09/connected/ai-studio-week09
collecting ... collected 98 items

aggregate_photo_insights/test_photo_analytics.py::test_t09_normal_case_100_photos PASSED [  1%]
aggregate_photo_insights/test_photo_analytics.py::test_t10_normal_case_3_months_trend PASSED [  2%]
aggregate_photo_insights/test_photo_analytics.py::test_t11_boundary_empty_and_single PASSED [  3%]
aggregate_photo_insights/test_photo_analytics.py::test_t12_exceptional_missing_column PASSED [  4%]
aggregate_photo_insights/test_photo_analytics.py::test_tag_whitespace_normalization PASSED [  5%]
aggregate_photo_insights/test_photo_analytics.py::test_edge_score_clipping_and_immutability PASSED [  6%]
analyze_with_gemini/test_analyze_with_gemini.py::test_normal_request_and_input_unchanged PASSED [  7%]
analyze_with_gemini/test_analyze_with_gemini.py::test_boundary_empty_hint_and_exif PASSED [  8%]
analyze_with_gemini/test_analyze_with_gemini.py::test_boundary_two_tags_and_score_limits PASSED [  9%]
analyze_with_gemini/test_analyze_with_gemini.py::test_markdown_response_reuses_validator PASSED [ 10%]
analyze_with_gemini/test_analyze_with_gemini.py::test_missing_photo_field[upload_bytes] PASSED [ 11%]
analyze_with_gemini/test_analyze_with_gemini.py::test_missing_photo_field[sha256] PASSED [ 12%]
analyze_with_gemini/test_analyze_with_gemini.py::test_missing_photo_field[safe_exif] PASSED [ 13%]
analyze_with_gemini/test_analyze_with_gemini.py::test_invalid_photo_value[upload_bytes-] PASSED [ 14%]
analyze_with_gemini/test_analyze_with_gemini.py::test_invalid_photo_value[upload_bytes-string] PASSED [ 15%]
analyze_with_gemini/test_analyze_with_gemini.py::test_invalid_photo_value[sha256-invalid] PASSED [ 16%]
analyze_with_gemini/test_analyze_with_gemini.py::test_invalid_photo_value[sha256-gggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggg] PASSED [ 17%]
analyze_with_gemini/test_analyze_with_gemini.py::test_invalid_photo_value[safe_exif-value4] PASSED [ 18%]
analyze_with_gemini/test_analyze_with_gemini.py::test_argument_types[args0] PASSED [ 19%]
analyze_with_gemini/test_analyze_with_gemini.py::test_argument_types[args1] PASSED [ 20%]
analyze_with_gemini/test_analyze_with_gemini.py::test_argument_types[args2] PASSED [ 21%]
analyze_with_gemini/test_analyze_with_gemini.py::test_empty_model PASSED [ 22%]
analyze_with_gemini/test_analyze_with_gemini.py::test_invalid_allowed_exif_value[True] PASSED [ 23%]
analyze_with_gemini/test_analyze_with_gemini.py::test_invalid_allowed_exif_value[nan] PASSED [ 24%]
analyze_with_gemini/test_analyze_with_gemini.py::test_invalid_allowed_exif_value[inf] PASSED [ 25%]
analyze_with_gemini/test_analyze_with_gemini.py::test_invalid_allowed_exif_value[value3] PASSED [ 26%]
analyze_with_gemini/test_analyze_with_gemini.py::test_invalid_allowed_exif_value[value4] PASSED [ 27%]
analyze_with_gemini/test_analyze_with_gemini.py::test_missing_category_rejected[\ud53c\uc0ac\uccb4 \uc7a5\ub974] PASSED [ 28%]
analyze_with_gemini/test_analyze_with_gemini.py::test_missing_category_rejected[\ube5b\uc758 \uc870\uac74] PASSED [ 29%]
analyze_with_gemini/test_analyze_with_gemini.py::test_missing_category_rejected[\ud53c\uc0ac\uccb4 \ub3d9\uc138] PASSED [ 30%]
analyze_with_gemini/test_analyze_with_gemini.py::test_missing_category_rejected[\uce74\uba54\ub77c \uc575\uae00] PASSED [ 31%]
analyze_with_gemini/test_analyze_with_gemini.py::test_missing_category_rejected[\uacf5\uac04 \uad6c\uc131] PASSED [ 32%]
analyze_with_gemini/test_analyze_with_gemini.py::test_missing_category_rejected[\uc0c9\ucc44 \uc870\ud654] PASSED [ 33%]
analyze_with_gemini/test_analyze_with_gemini.py::test_three_tags_rejected PASSED [ 34%]
analyze_with_gemini/test_analyze_with_gemini.py::test_out_of_range_score[final_score] PASSED [ 35%]
analyze_with_gemini/test_analyze_with_gemini.py::test_out_of_range_score[composition_score] PASSED [ 36%]
analyze_with_gemini/test_analyze_with_gemini.py::test_out_of_range_score[lighting_score] PASSED [ 37%]
analyze_with_gemini/test_analyze_with_gemini.py::test_out_of_range_score[color_score] PASSED [ 38%]
analyze_with_gemini/test_analyze_with_gemini.py::test_out_of_range_score[technique_score] PASSED [ 39%]
analyze_with_gemini/test_analyze_with_gemini.py::test_invalid_response[{"broken":] PASSED [ 40%]
analyze_with_gemini/test_analyze_with_gemini.py::test_invalid_response[[]] PASSED [ 41%]
analyze_with_gemini/test_analyze_with_gemini.py::test_invalid_response[None] PASSED [ 42%]
analyze_with_gemini/test_analyze_with_gemini.py::test_invalid_response[raw3] PASSED [ 43%]
analyze_with_gemini/test_analyze_with_gemini.py::test_client_error_converted_with_cause[TimeoutError] PASSED [ 44%]
analyze_with_gemini/test_analyze_with_gemini.py::test_client_error_converted_with_cause[ConnectionError] PASSED [ 45%]
analyze_with_gemini/test_analyze_with_gemini.py::test_client_error_converted_with_cause[OSError] PASSED [ 46%]
analyze_with_gemini/test_analyze_with_gemini.py::test_mock_end_to_end_and_no_shared_result PASSED [ 47%]
analyze_with_gemini/test_analyze_with_gemini.py::test_mock_docstring_and_json_contract PASSED [ 48%]
analyze_with_gemini/test_analyze_with_gemini.py::test_repository_import_without_test_path_setup PASSED [ 50%]
clean_analysis_dataframe/test_clean_analysis_dataframe.py::test_normal_values_and_dates PASSED [ 51%]
clean_analysis_dataframe/test_clean_analysis_dataframe.py::test_numeric_strings_and_score_clipping PASSED [ 52%]
clean_analysis_dataframe/test_clean_analysis_dataframe.py::test_missing_or_unusable_scores_are_removed_not_filled_with_zero PASSED [ 53%]
clean_analysis_dataframe/test_clean_analysis_dataframe.py::test_invalid_or_missing_dates_keep_scored_rows PASSED [ 54%]
clean_analysis_dataframe/test_clean_analysis_dataframe.py::test_original_input_extra_columns_tags_and_index_are_preserved PASSED [ 55%]
clean_analysis_dataframe/test_clean_analysis_dataframe.py::test_inclusive_score_boundaries[scores0] PASSED [ 56%]
clean_analysis_dataframe/test_clean_analysis_dataframe.py::test_inclusive_score_boundaries[scores1] PASSED [ 57%]
clean_analysis_dataframe/test_clean_analysis_dataframe.py::test_inclusive_score_boundaries[scores2] PASSED [ 58%]
clean_analysis_dataframe/test_clean_analysis_dataframe.py::test_completely_empty_dataframe_gets_empty_standard_columns PASSED [ 59%]
clean_analysis_dataframe/test_clean_analysis_dataframe.py::test_empty_dataframe_with_schema_keeps_extra_columns PASSED [ 60%]
clean_analysis_dataframe/test_clean_analysis_dataframe.py::test_all_scores_missing_returns_typed_empty_frame PASSED [ 61%]
clean_analysis_dataframe/test_clean_analysis_dataframe.py::test_non_dataframe_input_raises_type_error[None] PASSED [ 62%]
clean_analysis_dataframe/test_clean_analysis_dataframe.py::test_non_dataframe_input_raises_type_error[raw1] PASSED [ 63%]
clean_analysis_dataframe/test_clean_analysis_dataframe.py::test_non_dataframe_input_raises_type_error[raw2] PASSED [ 64%]
clean_analysis_dataframe/test_clean_analysis_dataframe.py::test_non_dataframe_input_raises_type_error[dataframe] PASSED [ 65%]
clean_analysis_dataframe/test_clean_analysis_dataframe.py::test_non_dataframe_input_raises_type_error[123] PASSED [ 66%]
clean_analysis_dataframe/test_clean_analysis_dataframe.py::test_missing_required_column_raises_value_error[id] PASSED [ 67%]
clean_analysis_dataframe/test_clean_analysis_dataframe.py::test_missing_required_column_raises_value_error[final_score] PASSED [ 68%]
clean_analysis_dataframe/test_clean_analysis_dataframe.py::test_missing_required_column_raises_value_error[captured_at] PASSED [ 69%]
clean_analysis_dataframe/test_clean_analysis_dataframe.py::test_missing_required_column_raises_value_error[tags] PASSED [ 70%]
clean_analysis_dataframe/test_clean_analysis_dataframe.py::test_empty_but_incomplete_schema_is_not_silently_fixed PASSED [ 71%]
clean_analysis_dataframe/test_clean_analysis_dataframe.py::test_row_index_without_columns_raises_missing_columns_error PASSED [ 72%]
clean_analysis_dataframe/test_clean_analysis_dataframe.py::test_duplicate_column_names_are_rejected PASSED [ 73%]
clean_analysis_dataframe/test_clean_analysis_dataframe.py::test_boolean_infinite_and_complex_scores_are_not_valid_scores PASSED [ 74%]
clean_analysis_dataframe/test_clean_analysis_dataframe.py::test_date_objects_and_timezone_keep_local_capture_month PASSED [ 75%]
clean_analysis_dataframe/test_clean_analysis_dataframe.py::test_numbers_are_not_inferred_as_unix_nanosecond_dates PASSED [ 76%]
clean_analysis_dataframe/test_clean_analysis_dataframe.py::test_repeated_cleaning_produces_same_result PASSED [ 77%]
clean_analysis_dataframe/test_clean_analysis_dataframe.py::test_duplicate_row_indices_are_preserved PASSED [ 78%]
clean_analysis_dataframe/test_clean_analysis_dataframe.py::test_ambiguous_relative_or_out_of_range_dates_become_nat[now] PASSED [ 79%]
clean_analysis_dataframe/test_clean_analysis_dataframe.py::test_ambiguous_relative_or_out_of_range_dates_become_nat[today] PASSED [ 80%]
clean_analysis_dataframe/test_clean_analysis_dataframe.py::test_ambiguous_relative_or_out_of_range_dates_become_nat[01/02/2026] PASSED [ 81%]
clean_analysis_dataframe/test_clean_analysis_dataframe.py::test_ambiguous_relative_or_out_of_range_dates_become_nat[3000-01-01] PASSED [ 82%]
clean_analysis_dataframe/test_clean_analysis_dataframe.py::test_ambiguous_relative_or_out_of_range_dates_become_nat[] PASSED [ 83%]
prepare_photo/test_prepare_photo.py::test_t01_jpeg_with_exif PASSED      [ 84%]
prepare_photo/test_prepare_photo.py::test_t02_png_without_exif PASSED    [ 85%]
prepare_photo/test_prepare_photo.py::test_t03_huge_image PASSED          [ 86%]
prepare_photo/test_prepare_photo.py::test_t04_missing_file PASSED        [ 87%]
prepare_photo/test_prepare_photo.py::test_t04_text_file PASSED           [ 88%]
prepare_photo/test_prepare_photo.py::test_directory_path_is_not_file PASSED [ 89%]
prepare_photo/test_prepare_photo.py::test_truncated_jpeg PASSED          [ 90%]
prepare_photo/test_prepare_photo.py::test_no_upscale_small_image PASSED  [ 91%]
prepare_photo/test_prepare_photo.py::test_extract_safe_exif_without_exif PASSED [ 92%]
validate_vlm_response/validate_vlm_test.py::test_valid_json PASSED       [ 93%]
validate_vlm_response/validate_vlm_test.py::test_markdown_json PASSED    [ 94%]
validate_vlm_response/validate_vlm_test.py::test_score_boundary PASSED   [ 95%]
validate_vlm_response/validate_vlm_test.py::test_invalid_json PASSED     [ 96%]
validate_vlm_response/validate_vlm_test.py::test_invalid_score PASSED    [ 97%]
validate_vlm_response/validate_vlm_test.py::test_invalid_tag PASSED      [ 98%]
validate_vlm_response/validate_vlm_test.py::test_invalid_focus_type PASSED [100%]

=============================== warnings summary ===============================
prepare_photo/test_prepare_photo.py::test_t01_jpeg_with_exif
prepare_photo/test_prepare_photo.py::test_t02_png_without_exif
prepare_photo/test_prepare_photo.py::test_t03_huge_image
prepare_photo/test_prepare_photo.py::test_no_upscale_small_image
  /Users/dohyeok/.codex/.chatgpt-projects/g-p-6ac48a02559081918a00e52e7c8655eb/week09/connected/ai-studio-week09/prepare_photo/prepare_photo.py:69: DeprecationWarning: Image.Image.getdata is deprecated and will be removed in Pillow 14 (2027-10-15). Use get_flattened_data instead.
    pixels = list(small.getdata())

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================== 98 passed, 4 warnings in 1.16s ========================

```
