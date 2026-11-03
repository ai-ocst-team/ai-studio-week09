# 9주차 과제 보고서 — 바이브 코딩 표준 6단계 사이클 적용

- **팀명**: 아트서강
- **대상 함수**: analyze_with_gemini(photo, model, hint)
- **작성자 / 역할**: 김도혁 (VLM 요청 구성 및 분석 응답 검증 연결)
- **현재 상태**: 명세·사전 테스트·프롬프트 준비. Copilot 생성 전 골격.

## 1단계: 논리 설계

# analyze_with_gemini — 논리 설계 및 테스트 기준

담당: 김도혁. 상태: 구현 전 검토용. 기준 저장소 main: cf6cfe4d81a60d6db69a1701dff0524936ad49c8.

## 설계 변경

- EXIF 함수는 기존 prepare_photo 담당자의 구현을 재사용하고 본인 담당을 analyze_with_gemini로 변경한다.
- 사용자 합의: 8범주·최대 3개에서 **6범주·각 최대 2개**로 변경한다.
- 6범주 키를 모두 포함하고 해당 태그가 없으면 []를 반환한다.
- 9~12주차는 llm_client.py의 [MOCK]만 사용한다. 실제 API·모델 존재 여부와 품질은 이번 검증 대상이 아니다.
- 아래의 예외·공백 모델 정책은 이번 준비안의 구체화 사항이다. 본인이 검토하고 실제 Copilot 입력 전에 확정한다.

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

기존 검증 모듈은 `from validate_vlm_response import validate_vlm_response`로 재사용한다. 해당 폴더를 Python 검색 경로에 두며 테스트는 테스트 파일이 설정한다. 기존 파일은 수정하지 않는다.

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

테스트 파일: test_analyze_with_gemini.py. 매개변수별 검사 포함 42개 수집 확인.

## 2단계: 정밀 프롬프트 작성

역할·맥락, 시그니처, 입출력, 예외·경계, 제약, 테스트 기준을 포함한 전문은 prompt_log.md에 있다. 실제 전송 전 본인이 명세와 테스트를 검토한다.

## 3단계: AI 코드 생성

미수행. Copilot에 report.md·테스트·기존 검증 코드를 첨부하고 prompt_log.md의 프롬프트를 전달한다. 생성 대상은 analyze_with_gemini.py와 llm_client.py 두 파일이다. 수정 전에 생성 원본을 커밋하고 실제 해시를 과정 기록에 남긴다.

## 4단계: 코드 리딩·검증

미수행. 본인이 입력 검사, EXIF 필터, hint 전달, 기존 검증 재사용, 6범주 필수 검사, 통신/검증 예외 구분, 원본 불변, [MOCK] 및 비밀값 부재를 확인한다. 실제 발견한 결함·개선점과 수정 이유를 prompt_log.md에 기록한다.

## 5단계: 테스트

저장소 최상위에서 개인 테스트 후 전체 테스트를 실행한다. 실패하면 4단계로 복귀한다.

```bash
python -m pytest analyze_with_gemini -v --tb=short -p no:cacheprovider
python -m pytest -v --tb=short -p no:cacheprovider
```

현재 확인한 것은 42개 사전 테스트의 수집이며 최종 구현 통과가 아니다. 골격은 NotImplementedError 상태다. 앞서 기존 팀 코드 사본의 55 passed, 4 warnings를 확인했지만 본인 함수의 실적으로 사용하지 않는다. 실제 전체 출력은 prompt_log.md에 첨부한다.

## 6단계: Git 커밋 및 과정 기록

현재 브랜치: feat/kdh-analyze-with-gemini. 본인 함수 관련 커밋·push는 아직 하지 않았다.

1. 실제 author 확인 및 설계·사전 테스트 보존.
2. Copilot 생성 직후 원본 커밋.
3. 본인 리딩·수정 및 pytest 전체 통과 후 두 번째 수정·검증 커밋.
4. prompt_log.md의 실제 해시·출력 갱신, 팀 공용 CHECKLIST.md 담당 변경 및 루트 과정 기록 반영.
5. 전원 보안 교차 확인 후 본인 브랜치 push·팀 병합·LMS 링크 제출.

사후 커밋을 생성 당시 커밋처럼 기록하지 않는다. 수정할 결함이 없었다면 사실대로 기록하고 검토 근거와 검증 커밋을 남긴다.

## 참고

정윤님 aggregate_photo_insights 폴더의 문서 구성과 6단계 보고 형식을 참고했다. 팀 검증 코드 기준 SHA: cf6cfe4d81a60d6db69a1701dff0524936ad49c8. 기존 팀원 파일은 수정하지 않았다. 강의 10~11·13·35~36·44~52쪽과 5주차 S1~S10을 기준으로 준비했다.
