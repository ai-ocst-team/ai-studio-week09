"""사전 테스트 기준: 정상·경계·예외 및 기존 검증 함수와의 연결."""
import copy
import sys
from pathlib import Path

# 기존 팀 검증 모듈을 재사용한다.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "validate_vlm_response"))
import json

import pytest

import llm_client
from analyze_with_gemini import analyze_with_gemini

CATEGORIES = (
    "피사체 장르", "빛의 조건", "피사체 동세", "카메라 앵글", "공간 구성", "색채 조화"
)
SCORES = (
    "final_score", "composition_score", "lighting_score", "color_score", "technique_score"
)


@pytest.fixture
def photo():
    return {
        "upload_bytes": b"synthetic-image-bytes",
        "sha256": "a" * 64,
        "safe_exif": {"iso": 100, "camera_model": "DummyCam"},
        "path": "/dummy/private.jpg",
    }


@pytest.fixture
def analysis():
    return {
        **dict.fromkeys(SCORES, 8.0),
        "aesthetic_tags": dict((category, []) for category in CATEGORIES),
        "focus_status": "판별 불가",
    }


def stub(monkeypatch, analysis, capture=None):
    def generate_analysis(*, image_bytes, model, prompt):
        if capture is not None:
            capture.append({"image_bytes": image_bytes, "model": model, "prompt": prompt})
        return json.dumps(analysis, ensure_ascii=False)
    monkeypatch.setattr(llm_client, "generate_analysis", generate_analysis)


def test_normal_request_and_input_unchanged(photo, analysis, monkeypatch):
    calls = []
    photo["safe_exif"].update(GPSInfo="SENSITIVE_DUMMY", Artist="PRIVATE_DUMMY")
    before = copy.deepcopy(photo)
    stub(monkeypatch, analysis, calls)
    hint = '감성 보케: "따뜻한 빛"\n관찰 요청'
    result = analyze_with_gemini(photo, " dummy-model ", hint)
    assert result == analysis
    assert photo == before
    assert len(calls) == 1
    assert calls[0]["image_bytes"] == photo["upload_bytes"]
    assert calls[0]["model"] == "dummy-model"
    request = json.loads(calls[0]["prompt"])
    assert request["hint"] == hint
    assert request["safe_exif"] == {"iso": 100, "camera_model": "DummyCam"}
    assert request["task"] and request["response_contract"]
    for category in CATEGORIES:
        assert category in calls[0]["prompt"]
    assert "SENSITIVE_DUMMY" not in calls[0]["prompt"]
    assert "PRIVATE_DUMMY" not in calls[0]["prompt"]
    assert photo["path"] not in calls[0]["prompt"]
    assert photo["sha256"] not in calls[0]["prompt"]


def test_boundary_empty_hint_and_exif(photo, analysis, monkeypatch):
    photo["safe_exif"] = {}
    stub(monkeypatch, analysis)
    assert analyze_with_gemini(photo, "dummy", "") == analysis


def test_boundary_two_tags_and_score_limits(photo, analysis, monkeypatch):
    analysis["aesthetic_tags"]["피사체 장르"] = ["자연풍경", "건축도시"]
    analysis["final_score"], analysis["color_score"] = 0, 10
    stub(monkeypatch, analysis)
    assert analyze_with_gemini(photo, "dummy", "") == analysis


def test_markdown_response_reuses_validator(photo, analysis, monkeypatch):
    monkeypatch.setattr(llm_client, "generate_analysis", lambda **kw: '```json\n' + json.dumps(analysis) + '\n```')
    assert analyze_with_gemini(photo, "dummy", "") == analysis


@pytest.mark.parametrize("field", ["upload_bytes", "sha256", "safe_exif"])
def test_missing_photo_field(photo, field, monkeypatch):
    del photo[field]
    def unexpected(**kw):
        pytest.fail("무효 입력에서 클라이언트를 호출했습니다.")
    monkeypatch.setattr(llm_client, "generate_analysis", unexpected)
    with pytest.raises(ValueError):
        analyze_with_gemini(photo, "dummy", "")


@pytest.mark.parametrize("field,value", [
    ("upload_bytes", b""), ("upload_bytes", "string"),
    ("sha256", "invalid"), ("sha256", "g" * 64), ("safe_exif", []),
])
def test_invalid_photo_value(photo, field, value):
    photo[field] = value
    with pytest.raises(ValueError):
        analyze_with_gemini(photo, "dummy", "")


@pytest.mark.parametrize("args", [(None, "dummy", ""), ({}, None, ""), ({}, "dummy", None)])
def test_argument_types(args):
    with pytest.raises(TypeError):
        analyze_with_gemini(*args)


def test_empty_model(photo):
    with pytest.raises(ValueError):
        analyze_with_gemini(photo, "  ", "")


@pytest.mark.parametrize("value", [True, float("nan"), float("inf"), [], {}])
def test_invalid_allowed_exif_value(photo, value):
    photo["safe_exif"]["iso"] = value
    with pytest.raises(ValueError):
        analyze_with_gemini(photo, "dummy", "")


@pytest.mark.parametrize("category", CATEGORIES)
def test_missing_category_rejected(photo, analysis, monkeypatch, category):
    del analysis["aesthetic_tags"][category]
    stub(monkeypatch, analysis)
    with pytest.raises(ValueError):
        analyze_with_gemini(photo, "dummy", "")


def test_three_tags_rejected(photo, analysis, monkeypatch):
    # 세 태그 모두 허용 어휘로 두어 개수 제한 자체를 검증한다.
    analysis["aesthetic_tags"]["피사체 장르"] = ["자연풍경", "건축도시", "인물동물"]
    stub(monkeypatch, analysis)
    with pytest.raises(ValueError):
        analyze_with_gemini(photo, "dummy", "")


@pytest.mark.parametrize("field", SCORES)
def test_out_of_range_score(photo, analysis, monkeypatch, field):
    analysis[field] = 10.1
    stub(monkeypatch, analysis)
    with pytest.raises(ValueError):
        analyze_with_gemini(photo, "dummy", "")


@pytest.mark.parametrize("raw", ['{"broken":', "[]", None, {}])
def test_invalid_response(photo, monkeypatch, raw):
    monkeypatch.setattr(llm_client, "generate_analysis", lambda **kw: raw)
    with pytest.raises(ValueError):
        analyze_with_gemini(photo, "dummy", "")


@pytest.mark.parametrize("error_type", [TimeoutError, ConnectionError, OSError])
def test_client_error_converted_with_cause(photo, monkeypatch, error_type):
    cause = error_type("dummy failure")
    def fail(**kw):
        raise cause
    monkeypatch.setattr(llm_client, "generate_analysis", fail)
    with pytest.raises(RuntimeError, match="VLM 통신 실패") as exc:
        analyze_with_gemini(photo, "dummy", "")
    assert exc.value.__cause__ is cause


def test_mock_end_to_end_and_no_shared_result(photo):
    first = analyze_with_gemini(photo, "dummy", "")
    assert set(first["aesthetic_tags"]) == set(CATEGORIES)
    assert all(tags == [] for tags in first["aesthetic_tags"].values())
    assert first["focus_status"] == "판별 불가"
    first["aesthetic_tags"]["피사체 장르"].append("자연풍경")
    assert analyze_with_gemini(photo, "dummy", "")["aesthetic_tags"]["피사체 장르"] == []


def test_mock_docstring_and_json_contract():
    assert "[MOCK]" in (llm_client.generate_analysis.__doc__ or "")
    result = json.loads(llm_client.generate_analysis(b"dummy", "dummy", "dummy"))
    assert set(result["aesthetic_tags"]) == set(CATEGORIES)
    assert all(0 <= result[field] <= 10 for field in SCORES)
