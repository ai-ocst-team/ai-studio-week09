# prompt_log.md — AI 활용 과정 기록

## analyze_with_gemini — 2026-11-03, 작성자: 김도혁

- **현재 준비 도구**: Codex (명세·사전 테스트·프롬프트·골격·문서 정리)
- **구현에 사용할 도구**: GitHub Copilot Chat — 아직 실제 전송·생성하지 않음
- **설계 변경 사유**: EXIF 담당 중복을 해소하고 analyze_with_gemini로 변경. 사용자 합의에 따라 6범주 모두 포함·각 최대 2개·해당 없음 [] 적용. 실제 API 대신 llm_client.py의 [MOCK] 사용.
- **프롬프트 원문 초안**: 아래 내용은 아직 전송 전이다. 실제 요청이 달라지면 실제 전문으로 갱신한다.

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

- **생성 코드 위치**: 미수행. 실제 생성 직후 커밋 해시 기록 예정.
- **코드 리딩에서 발견한 결함 및 개선점**: 미수행. 실제 코드의 파일·줄·문제·근거를 작성할 것.
- **수정 내역**: 미수행. 실제 변경 내용·사유·수정 커밋 해시를 기록할 것.
- **최종 테스트 결과**: 미수행. pytest 실제 출력 전체·환경·시각·대상 커밋을 아래에 보존할 것.

## 최종 pytest 출력

아직 실행하지 않음. 사전 테스트 수집 결과를 구현 통과로 기록하지 않는다.
