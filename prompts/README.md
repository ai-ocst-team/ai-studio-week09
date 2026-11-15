# Task 3 — 사진 평가 프롬프트 초안

`photo_analysis_prompt.txt`는 `analyze_with_gemini()`가 UTF-8로 읽어 실제 요청의 `task`에 넣는 지시문입니다. 기존 9주차 지시문을 그대로 분리하여 내용은 유지했습니다. 실행 위치에 관계없이 모듈 위치 기준으로 읽고, 누락·빈 파일·읽기 오류는 ValueError로 알립니다.

## 요청 계약

| JSON 키 | 내용 |
|---|---|
| task | 외부 파일에서 읽은 지시문 |
| safe_exif | 허용된 촬영 정보만 추출한 객체 |
| hint | 사용자 촬영 의도 문자열(빈 문자열 허용) |
| response_contract | 필수 필드·점수 범위·태그 어휘·초점 상태 계약 |

태그 어휘와 응답 계약은 기존 `analyze_with_gemini.py`의 정의를 사용합니다. 파일에 중복 정의하지 않습니다. hint는 문자열 치환으로 지시문에 삽입하지 않고 별도 JSON 값으로 직렬화합니다. 이것만으로 실제 모델의 프롬프트 주입 방어가 검증된 것은 아닙니다.

## 반환 계약

`llm_client.generate_analysis(image_bytes: bytes, model: str, prompt: str) -> str`의 반환은 JSON 문자열입니다. `analyze_with_gemini`가 검증 후 dict로 변환하며, 최종 `run_pipeline`도 dict를 반환합니다.

- 점수: final_score, composition_score, lighting_score, color_score, technique_score (0~10).
- aesthetic_tags: 피사체 장르·빛의 조건·피사체 동세·카메라 앵글·공간 구성·색채 조화의 6개 범주, 각각 최대 2개.
- focus_status: 기존 검증기의 허용값 사용. Mock 값은 `판별 불가`입니다.

## Mock 설정

- 단일 설정: 환경 변수 `USE_MOCK`. 미설정은 true, true/1/yes/on과 false/0/no/off를 지원하며 다른 값은 오류입니다.
- 기존 `run_pipeline(..., use_mock=True/False)`는 환경 변수를 설정하므로 해당 인자가 우선합니다. 파이프라인은 기존처럼 환경을 복원하지 않습니다. 병렬 실행 시 모드 격리는 Task 1과 별도 협의할 항목입니다.
- Mock은 고정된 가상 값을 반환하고 INFO 수준의 `[MOCK]` 표식을 기록합니다. 단독 사용 시 INFO 로깅을 활성화해야 화면에 보입니다.
- false는 `_generate_real`로 전달되며 아직 NotImplementedError를 발생시킵니다. API 키·SDK·네트워크 호출은 사용하지 않습니다.
- CLI의 `--use-mock`는 현재 True만 선택할 수 있는 기존 Task 1 설정입니다. 비Mock 분기는 Python의 run_pipeline 인자 또는 클라이언트 직접 호출로 검증합니다.
