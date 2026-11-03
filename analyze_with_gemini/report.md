# 9주차 과제 보고서 — 바이브 코딩 표준 6단계 사이클 적용

- **팀명**: 아트서강
- **대상 함수**: analyze_with_gemini(photo, model, hint)
- **작성자 / 역할**: 김도혁 (VLM 요청 구성 및 분석 응답 검증 연결)
- **현재 상태**: 생성 원본 커밋 보존, Codex 코드 리딩·import 결함 수정 및 전체 pytest 통과. 요청문 대조·보안 점검·팀 확인·GitHub/LMS 제출은 사용자 확인으로 완료. 본인 직접 리딩 확인과 수정 커밋 해시는 로컬에서 미확인.

## 1단계: 논리 설계

# analyze_with_gemini — 논리 설계 및 테스트 기준

담당: 김도혁. 상태: 구현 및 후속 검증 반영. 기준 저장소 main: cf6cfe4d81a60d6db69a1701dff0524936ad49c8.

## 설계 변경

- EXIF 함수는 기존 prepare_photo 담당자의 구현을 재사용하고 본인 담당을 analyze_with_gemini로 변경한다.
- 사용자 합의: 8범주·최대 3개에서 **6범주·각 최대 2개**로 변경한다.
- 6범주 키를 모두 포함하고 해당 태그가 없으면 []를 반환한다.
- 9~12주차는 llm_client.py의 [MOCK]만 사용한다. 실제 API·모델 존재 여부와 품질은 이번 검증 대상이 아니다.
- 아래 예외·공백 모델 정책은 구현 명세에 포함했고, 해당 요청문 대조 완료를 사용자가 확인했다.

## 고정 인터페이스

`analyze_with_gemini(photo: dict[str, Any], model: str, hint: str) -> dict[str, Any]`

입력 photo는 prepare_photo 반환 딕셔너리다. upload_bytes는 비어 있지 않은 bytes, sha256은 64자리 16진수 문자열, safe_exif는 dict여야 한다. 추가 path/width/height/dhash는 전달받을 수 있으나 프롬프트에 포함하지 않는다.

모델명은 문자열이어야 한다. 양끝 공백을 제거하며 빈 문자열이면 ValueError. hint는 문자열이며 빈 값 허용, 촬영 의도로 요청에 반영한다. 타입이 다른 인자는 TypeError, 타입이 맞으나 필수값 누락/무효이면 ValueError.

안전 EXIF 전송 허용 키: aperture, shutter_speed, iso, focal_length, camera_model, lens_model, captured_at. 키가 없으면 생략. 그 외 키는 요청에서 제외한다. 값은 bool을 제외한 int/유한 float/str만 허용한다. 허용 키에 무효 자료형이 있으면 ValueError. 입력을 수정하지 않는다.

## 처리 순서

1. 입력 타입·필수 키·값 검사.
2. EXIF 허용 키만 새 dict로 선별.
3. JSON 요청 문자열 구성: task, safe_exif, hint, response_contract. hint는 JSON 데이터로 구분하며 지시문보다 우선하지 않도록 task에 명시.
4. response_contract에 점수 5필드(0~10), 태그 6범주와 허용 어휘, 최대 2개·범주별 [] 허용, 초점 상태 5개를 명시.
5. llm_client.generate_analysis(image_bytes=..., model=정리한 모델명, prompt=...) 1회 호출.
6. 클라이언트 TimeoutError/ConnectionError/OSError만 RuntimeError("VLM 통신 실패")로 변환하고 원인을 연결. 검증 오류는 통신 오류로 바꾸지 않는다.
7. 반환값이 str이 아니면 ValueError. 기존 validate_vlm_response(raw_text)로 JSON·점수·허용 어휘·초점 검증을 재사용.
8. aesthetic_tags의 키가 정확한 6범주인지 추가 검사. 성공 시 기존 검증 결과 dict 반환.

본인 모듈은 패키지 상대 import로 Mock을 불러온다. 팀 검증 파일은 고정된 저장소 경로에서 runpy.run_path로 읽어 함수를 재사용하며, 테스트의 sys.path 보정과 모듈 이름 충돌을 피한다. __init__.py는 본인 폴더에만 둔다. 다른 팀원 파일은 변경하지 않는다.

## 반환 계약

final_score, composition_score, lighting_score, color_score, technique_score: 0~10 숫자. aesthetic_tags: 아래 6개 키의 문자열 리스트, 각 0~2개. focus_status: 기존 허용값 중 하나.

| 범주 | 허용 어휘 |
|---|---|
| 피사체 장르 | 자연풍경, 건축도시, 인물동물, 사물정물, 거리스냅 |
| 빛의 조건 | 안정된 순광, 골든아워, 흐린날 확산광, 극단적 역광, 저조도 야경 |
| 피사체 동세 | 완전 정지, 완만한 흐름, 예측불가 빠른동세, 찰나의 순간 |
| 카메라 앵글 | 아이레벨, 로우 앵글, 하이앵글(탑뷰), 피사체 눈높이 일치, 틸트사선 |
| 공간 구성 | 단일피사체 집중, 다층 레이어, 프레임인프레임, 대칭패턴, 여백의미 |
| 색채 조화 | 자연스런 뉴트럴, 뚜렷한 보색대비, 차분한 모노톤, 다채로운 색정돈, 절제된 톤다운 |

초점: 완벽 칼초점, 미세 앞핀, 미세 뒤핀, 초점 이탈, 판별 불가.

## Mock 경계

`llm_client.generate_analysis(image_bytes: bytes, model: str, prompt: str) -> str`

docstring에 [MOCK] 표시. 사전 정의한 정상 JSON을 매번 새 문자열로 반환. 모든 범주 [] 허용, focus_status='판별 불가'. 입력 의도에 따라 실제 이미지를 분석한 것처럼 점수·비평을 생성하지 않는다. 함수 자체도 타입과 비어 있는 인자를 검사한다. 네트워크·SDK·API 키·파일 저장·로그 출력 없음.

## 비목표

이미지 재전처리, EXIF 재추출, DB 저장, 집계, UI, 자동 재시도, 실제 모델 연동, 태그 검증 재구현은 하지 않는다. 문자열 값이나 hint에 담긴 개인정보를 의미적으로 자동 검출하는 기능은 없다. 테스트에는 더미 값만 사용하고 실제 프롬프트 내용은 사람이 확인한다.

### 선행 테스트 기준

| 범주 | 입력 조건 | 기대 결과 |
|---|---|---|
| 정상 | 전처리 사진·모델·촬영 의도 | 요청 1회, 검증된 분석 dict, 원본 불변 |
| 정상 | 코드블록으로 감싼 응답 | 기존 검증 함수를 통해 정상 파싱 |
| 경계 | 빈 hint·빈 safe_exif·태그 [] | 정상 처리, 6범주 유지 |
| 경계 | 점수 0/10·허용 태그 2개 | 정상 처리 |
| 예외 | 필수 입력 누락·공백 모델·비정상 EXIF | 명세의 TypeError 또는 ValueError |
| 예외 | 누락 범주·태그 3개·점수 범위 초과·깨진 응답 | ValueError |
| 예외 | Mock 경계의 통신 실패 예외 | 원인을 연결한 RuntimeError |

테스트 파일: test_analyze_with_gemini.py. 사전 42개에 독립 import 회귀 검사 1개를 추가해 최종 43개가 통과했다.

## 2단계: 정밀 프롬프트 작성

역할·맥락, 시그니처, 입출력, 예외·경계, 제약, 테스트 기준을 포함한 전문은 prompt_log.md에 있다. 사용자가 실제 Copilot 요청문 대조를 완료했다고 확인했다.

## 3단계: AI 코드 생성

사용자가 생성 구현을 저장하고 원본 커밋 `8665573441df9d67bf37e9d0c259d97d1ae4c957`을 남겼다. 준비 명세 커밋은 `7bfbea6f2bf8873e06f272cf90b4a14c5fd5c583`이다. 실제 Copilot 요청문 대조는 사용자 확인으로 완료했다.

## 4단계: 코드 리딩·검증

사용자 요청으로 Codex가 코드 흐름을 검토하고 테스트 경로 보정이 import 결함을 가리는 문제를 재현했다. 본인 패키지 import와 팀 검증 파일을 읽는 방식을 수정하고 새 프로세스 회귀 테스트를 추가했다. 사용자 본인의 이해 확인은 별도다. 상세 실패→수정→통과 기록은 prompt_log.md에 있다.

## 5단계: 테스트

개인 43개 통과. 최종 저장소 전체 **98 passed, 4 warnings in 1.16s**. 실제 출력·환경·코드 해시는 prompt_log.md에 보존했다. 기존 42개 테스트는 기대값을 변경하지 않았다. 경고는 기존 prepare_photo의 Pillow 제거 예정 기능 사용이다.

```bash
python -m pytest analyze_with_gemini -v --tb=short -p no:cacheprovider
python -m pytest -v --tb=short -p no:cacheprovider
```

## 6단계: Git 커밋 및 과정 기록

브랜치: feat/kdh-analyze-with-gemini. 준비 및 생성 원본 커밋은 prompt_log.md에 기록했다. 요청문 대조, 보안 점검, 전원 교차 확인과 GitHub 반영·병합·LMS 제출은 사용자 확인으로 완료했다.

현재 로컬에는 후속 수정이 작업 트리로 남아 있고 정확한 수정 커밋 해시는 확인되지 않았다. 원격에서 완료한 작업과 로컬 상태를 동일하다고 단정하지 않는다. 이번 문서 갱신분도 제출본에 반영해야 한다. 본인의 직접 코드 리딩 확인은 별도이며 AI 보조 검토를 독립 수행으로 바꿔 기록하지 않는다.

## 참고

정윤님 aggregate_photo_insights 폴더의 문서 구성과 6단계 보고 형식을 참고했다. 팀 검증 코드 기준 SHA: cf6cfe4d81a60d6db69a1701dff0524936ad49c8. 기존 팀원 파일은 수정하지 않았다. 강의 10~11·13·35~36·44~52쪽과 5주차 S1~S10을 기준으로 준비했다.
