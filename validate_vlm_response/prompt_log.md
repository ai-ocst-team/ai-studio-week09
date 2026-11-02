
## 프롬프트
당신은 Python 백엔드 개발을 돕는 어시스턴트입니다.
사진 평가 시스템에서 VLM 응답의 유효성을 검증하는 함수를 구현해 주세요.

**[함수 시그니처 — 변경 금지]**

```
from typing import Any

PhotoAnalysis = dict[str, Any]

def validate_vlm_response(raw_text: str) -> PhotoAnalysis:
```
**[입출력 명세]**

입력: VLM이 반환한 JSON 문자열

출력: 검증된 PhotoAnalysis 딕셔너리

필수 필드:

- `final_score`, `composition_score`, `lighting_score`, `color_score`, `technique_score`: 각각 0.0~10.0 범위의 숫자
- `aesthetic_tags`: 범주별 태그 리스트(각 최대 2개, 빈 리스트 허용)
- `focus_status`: 5개 초점 상태 중 하나
**범주별 태그 범주 및 허용 어휘**

- 피사체 장르: 자연풍경 / 건축도시 / 인물동물 / 사물정물 / 거리스냅
- 빛의 조건: 안정된 순광 / 골든아워 / 흐린날 확산광 / 극단적 역광 / 저조도 야경
- 피사체 동세: 완전 정지 / 완만한 흐름 / 예측불가 빠른동세 / 찰나의 순간
- 카메라 앵글: 아이레벨 / 로우 앵글 / 하이앵글(탑뷰) / 피사체 눈높이 일치 / 틸트사선
- 공간 구성: 단일피사체 집중 / 다층 레이어 / 프레임인프레임 / 대칭패턴 / 여백의미
- 색채 조화: 자연스런 뉴트럴 / 뚜렷한 보색대비 / 차분한 모노톤 / 다채로운 색정돈 / 절제된 톤다운
**초점 상태 허용값**

완벽 칼초점, 미세 앞핀, 미세 뒤핀, 초점 이탈, 판별 불가

**[예외·경계 방침]**

1. 마크다운 코드 블록(```` ```json ... ``` ````)이 있으면 제거한 뒤 JSON 파싱
2. `json.loads()`로 파싱하고, JSON 구문 오류 발생 시 `ValueError` 발생
3. 필수 필드가 누락되거나 점수가 0.0~10.0 범위를 벗어나면 `ValueError` 발생
4. `aesthetic_tags`에 정의되지 않은 범주나 허용 어휘 목록에 없는 태그가 하나라도 포함되면 `ValueError` 발생
5. 범주별 태그가 3개를 초과하거나 초점 상태가 허용값에 없으면 `ValueError` 발생
6. 잘못된 값은 자동 보정하지 않고, 모든 검증을 통과하면 dict 반환
**[제약 조건]**

- 표준 라이브러리만 사용 (pandas 및 외부 API 사용 금지)
- 함수 시그니처 변경 금지, 타입 힌트와 docstring 필수
- `eval()` 및 광범위한 `except:` 사용 금지
- 오류 발생 시 기본값으로 대체하거나 `None`을 반환하지 말 것
**[통과해야 할 테스트]**

- 정상 JSON → dict 반환
- 마크다운으로 감싼 JSON → 정상 파싱
- 점수가 0.0 또는 10.0 → 정상 처리
- 잘못된 JSON 또는 필수 키 누락 → `ValueError`
- 점수 10.1 → `ValueError`
- 허용 어휘에 없는 태그 포함 → `ValueError`
- 범주별 태그 4개 또는 잘못된 초점 상태 → `ValueError`
위 명세에 맞는 함수 코드만 작성해 주세요.


## pytest



pytest -v validate_vlm_response/validate_vlm_test.py      
========================= test session starts ==========================
platform win32 -- Python 3.13.15, pytest-9.2.0, pluggy-1.7.0 -- C:\Users\sinbi\ai_studio\venv1\Scripts\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\sinbi\ai_studio\ai-studio-week09
collected 7 items                                                       

validate_vlm_response/validate_vlm_test.py::test_valid_json PASSED [ 14%]
validate_vlm_response/validate_vlm_test.py::test_markdown_json PASSED [ 28%]
validate_vlm_response/validate_vlm_test.py::test_score_boundary PASSED [42%]
validate_vlm_response/validate_vlm_test.py::test_invalid_json PASSED [ 57%]
validate_vlm_response/validate_vlm_test.py::test_invalid_score PASSED [ 71%]
validate_vlm_response/validate_vlm_test.py::test_invalid_tag PASSED [ 85%]
validate_vlm_response/validate_vlm_test.py::test_invalid_focus_type FAILED [100%]

=============================== FAILURES ===============================
_______________________ test_invalid_focus_type ________________________

valid_data = {'final_score': 8.5, 'composition_score': 8.0, 'lighting_score': 9.0, 'color_score': 7.5, ...}

    def test_invalid_focus_type(valid_data):
        valid_data["focus_status"] = []
        raw = json.dumps(valid_data, ensure_ascii=False)
        with pytest.raises(ValueError):
>           validate_vlm_response(raw)

validate_vlm_response\validate_vlm_test.py:76: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

raw_text = '{"final_score": 8.5, "composition_score": 8.0, "lighting_score": 9.0, "color_score": 7.5, "technique_score": 8.0, "ae..."], "빛의 조건": ["골든아워"], "피사체 동세": [], "카메라 앵글": ["아이레벨"], "공간 구성": ["대칭패턴"], "색채 조화": ["차분한 모노톤"]}, "focus_status": []}'

    def validate_vlm_response(raw_text: str) -> PhotoAnalysis:
        """Parse and validate a VLM photo-analysis JSON response."""
        fenced_match = re.fullmatch(
                r"\s*```(?:json)?\s*(.*?)\s*```\s*", raw_text, flags=re.DOTALL | re.IGNORECASE
        )
        json_text = fenced_match.group(1) if fenced_match else raw_text
    
        try:
                data = json.loads(json_text)
        except json.JSONDecodeError as error:
                raise ValueError("응답이 올바른 JSON 형식이 아닙니다.") from error
    
        if not isinstance(data, dict):
                raise ValueError("JSON 최상위 값은 객체여야 합니다.")
        missing_fields = _REQUIRED_FIELDS - data.keys()
        if missing_fields:
                raise ValueError(f"필수 필드가 누락되었습니다: {', '.join(sorted(missing_fields))}")
    
        score_fields = (
                "final_score",
                "composition_score",
                "lighting_score",
                "color_score",
                "technique_score",
        )
        for field in score_fields:
                score = data[field]
                if isinstance(score, bool) or not isinstance(score, (int, float)) or not 0 <= score <= 10:
                        raise ValueError(f"{field}는 0.0~10.0 범위의 숫자여야 합니다.")
    
        aesthetic_tags = data["aesthetic_tags"]
        if not isinstance(aesthetic_tags, dict):
                raise ValueError("aesthetic_tags는 범주별 태그 객체여야합니다.")
        for category, tags in aesthetic_tags.items():
                if category not in _TAG_VOCABULARY:
                        raise ValueError(f"정의되지 않은 태그 범주입니다: {category}")
                if not isinstance(tags, list):
                        raise ValueError(f"{category}의 태그는 리스트여야 합니다.")
                if len(tags) > 2:
                        raise ValueError(f"{category}의 태그는 최대 2개까지 허용됩니다.")
                if any(not isinstance(tag, str) or tag not in _TAG_VOCABULARY[category] for tag in tags):
                        raise ValueError(f"{category}에 허용되지 않은 태그가 있습니다.")
    
>       if data["focus_status"] not in _FOCUS_STATUSES:
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E    TypeError: unhashable type: 'list'

validate_vlm_response\validate_vlm_response.py:70: TypeError
======================= short test summary info ========================
FAILED validate_vlm_response/validate_vlm_test.py::test_invalid_focus_type - TypeError: unhashable type: 'list'
===================== 1 failed, 6 passed in 0.37s ======================



## 수정

set의 포함여부를 검사하기 전에 자료형을 검사하지 않음.

focus_status = data["focus_status"]

if not isinstance(focus_status, str) or focus_status not in _FOCUS_STATUSES:
    raise ValueError("focus_status가 허용된 값이 아닙니다.")


pytest결과
========================================================= 7 passed in 0.18s =========================================================