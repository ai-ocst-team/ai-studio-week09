
import json
import pytest

from validate_vlm_response import validate_vlm_response


@pytest.fixture
def valid_data():
    return {
        "final_score": 8.5,
        "composition_score": 8.0,
        "lighting_score": 9.0,
        "color_score": 7.5,
        "technique_score": 8.0,
        "aesthetic_tags": {
            "피사체 장르": ["자연풍경"],
            "빛의 조건": ["골든아워"],
            "피사체 동세": [],
            "카메라 앵글": ["아이레벨"],
            "공간 구성": ["대칭패턴"],
            "색채 조화": ["차분한 모노톤"]
        },
        "focus_status": "완벽 칼초점"
    }


# 정상: 올바른 JSON
def test_valid_json(valid_data):
    raw = json.dumps(valid_data, ensure_ascii=False)
    assert validate_vlm_response(raw) == valid_data


# 경계: 마크다운 코드 블록 포함
def test_markdown_json(valid_data):
    raw = json.dumps(valid_data, ensure_ascii=False)
    raw = f"```json\n{raw}\n```"
    assert validate_vlm_response(raw) == valid_data


# 경계: 점수 0.0과 10.0
def test_score_boundary(valid_data):
    valid_data["final_score"] = 0.0
    valid_data["composition_score"] = 10.0
    raw = json.dumps(valid_data, ensure_ascii=False)
    assert validate_vlm_response(raw) == valid_data


# 예외: JSON 구문 오류
def test_invalid_json():
    with pytest.raises(ValueError):
        validate_vlm_response('{"final_score": 8.5,}')


# 예외: 점수 범위 초과
def test_invalid_score(valid_data):
    valid_data["final_score"] = 10.1
    raw = json.dumps(valid_data, ensure_ascii=False)
    with pytest.raises(ValueError):
        validate_vlm_response(raw)


# 예외: 허용되지 않은 태그
def test_invalid_tag(valid_data):
    valid_data["aesthetic_tags"]["피사체 장르"] = ["음식사진"]
    raw = json.dumps(valid_data, ensure_ascii=False)
    with pytest.raises(ValueError):
        validate_vlm_response(raw)


# 예외: 초점 상태 자료형 오류
def test_invalid_focus_type(valid_data):
    valid_data["focus_status"] = []
    raw = json.dumps(valid_data, ensure_ascii=False)
    with pytest.raises(ValueError):
        validate_vlm_response(raw)
