# -*- coding: utf-8 -*-
"""13주차 Task 1: llm_service 단위 테스트 (모의 Anthropic SDK 기반, 네트워크 무호출)."""

from __future__ import annotations

import base64
import json
import sys
from datetime import date
from types import ModuleType, SimpleNamespace
from unittest.mock import patch

import anthropic
import pytest

import llm_service

try:
    import httpx2 as _httpx
except ImportError:
    import httpx as _httpx


def _make_response(blocks, *, input_tokens=100, output_tokens=50, model="claude-haiku-4-5"):
    return SimpleNamespace(
        content=blocks,
        usage=SimpleNamespace(input_tokens=input_tokens, output_tokens=output_tokens),
        model=model,
    )


def _text_block(text: str):
    return SimpleNamespace(type="text", text=text)


def _thinking_block(thinking: str = "internal reasoning"):
    return SimpleNamespace(type="thinking", thinking=thinking)


def _make_rate_limit_error():
    req = _httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    resp = _httpx.Response(429, request=req)
    return anthropic.RateLimitError("rate limit", response=resp, body=None)


def _make_timeout_error():
    req = _httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    return anthropic.APITimeoutError(request=req)


def _make_auth_error():
    req = _httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    resp = _httpx.Response(401, request=req)
    return anthropic.AuthenticationError("invalid api key", response=resp, body=None)


@pytest.fixture(autouse=True)
def isolated_env(monkeypatch, tmp_path):
    """로컬 .env 및 프로세스 환경 변수를 테스트마다 안전하게 격리한다."""
    monkeypatch.setattr(llm_service, "_ENV_PATH", tmp_path / "nonexistent.env")
    monkeypatch.setenv("USE_MOCK", "true")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)
    monkeypatch.setattr(
        llm_service,
        "_LAST_VISION_USAGE",
        {"input_tokens": 0, "output_tokens": 0, "model": "mock"},
    )


def test_setting_priority_env_then_secrets_then_dotenv_then_default(monkeypatch, tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        'USE_MOCK="false"\nLLM_MODEL="claude-dotenv-model"\nANTHROPIC_API_KEY="sk-dotenv"\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(llm_service, "_ENV_PATH", env_file)
    monkeypatch.delenv("USE_MOCK")

    # 1) .env 적용
    assert llm_service.is_mock_mode() is False
    assert llm_service.get_active_model() == "claude-dotenv-model"

    # 2) st.secrets가 .env보다 우선
    fake_st = ModuleType("streamlit")
    fake_st.secrets = {"USE_MOCK": "true", "LLM_MODEL": "claude-secrets-model"}
    monkeypatch.setitem(sys.modules, "streamlit", fake_st)
    assert llm_service.is_mock_mode() is True
    assert llm_service.get_active_model() == "claude-secrets-model"

    # 3) OS 환경 변수가 st.secrets보다 우선 (빈 문자열 "" 보존 포함)
    monkeypatch.setenv("LLM_MODEL", "claude-env-model")
    assert llm_service.get_active_model() == "claude-env-model"
    monkeypatch.setenv("USE_MOCK", "")
    with pytest.raises(ValueError, match="USE_MOCK"):
        llm_service.is_mock_mode()


def test_missing_api_key_raises_runtime_error(monkeypatch):
    monkeypatch.setenv("USE_MOCK", "false")
    with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
        llm_service.generate_culling_report({"total_photos": 3})


def test_mock_mode_report_chat_and_last_vision_usage():
    report, usage = llm_service.generate_culling_report(
        {
            "session_label": "2026-01-10 ~ 2026-01-11 (4장)",
            "total_photos": 4,
            "avg_score": 8.25,
            "a_cut_count": 2,
            "b_cut_count": 1,
            "c_cut_count": 1,
        }
    )
    assert set(report) == {"headline", "best_shot_summary", "cleanup_advice", "findings", "risk_level"}
    assert report["risk_level"] == "low"
    assert usage == {"input_tokens": 0, "output_tokens": 0, "model": "mock"}

    reply_empty, _ = llm_service.generate_chat_reply([{"role": "user", "content": "  "}])
    assert "질문을 입력" in reply_empty

    reply_tag, chat_usage = llm_service.generate_chat_reply(
        [{"role": "user", "content": "태그 기준 추천"}],
        summary_context={
            "total_photos": 4,
            "avg_score": 8.25,
            "a_cut_count": 2,
            "b_cut_count": 1,
            "top_tags": [{"tag": "골든아워"}],
        },
    )
    assert reply_tag.startswith("[MOCK]")
    assert "사진 4장" in reply_tag and "골든아워" in reply_tag
    assert chat_usage == {"input_tokens": 0, "output_tokens": 0, "model": "mock"}
    assert llm_service.get_last_vision_usage() == {"input_tokens": 0, "output_tokens": 0, "model": "mock"}


def test_real_culling_report_handles_code_fence_and_thinking_block(monkeypatch):
    monkeypatch.setenv("USE_MOCK", "false")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")

    valid_payload = {
        "headline": "겨울 출사 4장 중 2장 대표샷 추천",
        "best_shot_summary": "골든아워 사진 2장이 구도와 빛에서 우수합니다.",
        "cleanup_advice": "보류 1장은 초점 확인 후 정리를 권장합니다.",
        "findings": ["A컷 비율 50%", "상위 태그 골든아워 강세"],
        "risk_level": "low",
    }
    fenced = "```json\n" + json.dumps(valid_payload, ensure_ascii=False) + "\n```"
    fake_resp = _make_response(
        [_thinking_block(), _text_block(fenced)],
        input_tokens=210,
        output_tokens=95,
        model="claude-haiku-4-5",
    )

    fake_client = SimpleNamespace(messages=SimpleNamespace(create=lambda **kw: fake_resp))
    with patch("anthropic.Anthropic", return_value=fake_client):
        report, usage = llm_service.generate_culling_report({"total_photos": 4})

    assert report == valid_payload
    assert usage == {"input_tokens": 210, "output_tokens": 95, "model": "claude-haiku-4-5"}


@pytest.mark.parametrize(
    "bad_text",
    [
        "not json at all",
        '["list", "not", "dict"]',
        json.dumps({"headline": "only one"}),
        json.dumps(
            {
                "headline": "ok",
                "best_shot_summary": "ok",
                "cleanup_advice": "ok",
                "findings": ["ok"],
                "risk_level": "critical",
            }
        ),
        json.dumps(
            {
                "headline": "ok",
                "best_shot_summary": "ok",
                "cleanup_advice": "ok",
                "findings": [],
                "risk_level": "low",
            }
        ),
    ],
)
def test_real_culling_report_rejects_invalid_json_or_schema(monkeypatch, bad_text):
    monkeypatch.setenv("USE_MOCK", "false")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    fake_resp = _make_response([_text_block(bad_text)])
    fake_client = SimpleNamespace(messages=SimpleNamespace(create=lambda **kw: fake_resp))

    with patch("anthropic.Anthropic", return_value=fake_client):
        with pytest.raises(ValueError):
            llm_service.generate_culling_report({"total_photos": 1})


def test_real_chat_reply_strips_leading_assistant_and_injects_context(monkeypatch):
    monkeypatch.setenv("USE_MOCK", "false")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")

    recorded = {}

    def fake_create(**kwargs):
        recorded.update(kwargs)
        return _make_response(
            [_thinking_block(), _text_block("A컷 2장을 우선 유지하세요.")],
            input_tokens=150,
            output_tokens=40,
        )

    fake_client = SimpleNamespace(messages=SimpleNamespace(create=fake_create))
    messages = [
        {"role": "assistant", "content": "안녕하세요! 질문을 입력해 주세요."},
        {"role": "assistant", "content": "두 번째 인사말"},
        {"role": "user", "content": "뭘 남길까요?"},
        {"role": "assistant", "content": "구도를 확인하세요."},
        {"role": "user", "content": "상위 태그도 알려줘"},
    ]
    with patch("anthropic.Anthropic", return_value=fake_client):
        reply, usage = llm_service.generate_chat_reply(messages, summary_context={"total_photos": 5})

    assert reply == "A컷 2장을 우선 유지하세요."
    assert usage == {"input_tokens": 150, "output_tokens": 40, "model": "claude-haiku-4-5"}
    assert recorded["messages"][0]["role"] == "user"
    assert len(recorded["messages"]) == 3
    assert '"total_photos": 5' in recorded["system"]


@pytest.mark.parametrize(
    "raw_bytes,expected_mime",
    [
        (b"\xff\xd8\xff\xe0jpeg-data", "image/jpeg"),
        (b"\x89PNG\r\n\x1a\npng-data", "image/png"),
        (b"RIFF1234WEBPvp8", "image/webp"),
    ],
)
def test_analyze_photo_with_claude_vision_and_model_fallback(monkeypatch, raw_bytes, expected_mime):
    monkeypatch.setenv("USE_MOCK", "false")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")

    vision_json = {
        "final_score": 8.8,
        "composition_score": 9.0,
        "lighting_score": 8.5,
        "color_score": 8.7,
        "technique_score": 8.9,
        "aesthetic_tags": {
            "피사체 장르": ["자연풍경"],
            "빛의 조건": ["골든아워"],
            "피사체 동세": [],
            "카메라 앵글": ["아이레벨"],
            "공간 구성": ["여백의미"],
            "색채 조화": [],
        },
        "focus_status": "완벽 칼초점",
    }
    recorded = {}

    def fake_create(**kwargs):
        recorded.update(kwargs)
        return _make_response(
            [_thinking_block(), _text_block("```json\n" + json.dumps(vision_json, ensure_ascii=False) + "\n```")],
            input_tokens=512,
            output_tokens=88,
            model="claude-haiku-4-5",
        )

    fake_client = SimpleNamespace(messages=SimpleNamespace(create=fake_create))
    with patch("anthropic.Anthropic", return_value=fake_client):
        out_text, usage = llm_service.analyze_photo_with_claude(
            raw_bytes,
            '{"task": "eval"}',
            model="gemini-1.5-flash",
        )

    assert recorded["model"] == "claude-haiku-4-5"
    content_blocks = recorded["messages"][0]["content"]
    assert content_blocks[0]["source"]["media_type"] == expected_mime
    assert content_blocks[0]["source"]["data"] == base64.standard_b64encode(raw_bytes).decode("ascii")
    assert json.loads(out_text)["final_score"] == 8.8
    assert usage == {"input_tokens": 512, "output_tokens": 88, "model": "claude-haiku-4-5"}
    assert llm_service.get_last_vision_usage() == usage


def test_analyze_photo_rejects_non_json(monkeypatch):
    monkeypatch.setenv("USE_MOCK", "false")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    fake_client = SimpleNamespace(
        messages=SimpleNamespace(create=lambda **kw: _make_response([_text_block("not json")]))
    )
    with patch("anthropic.Anthropic", return_value=fake_client):
        with pytest.raises(ValueError, match="JSON"):
            llm_service.analyze_photo_with_claude(b"\xff\xd8\xff", "prompt")


def test_retry_backoff_succeeds_after_transient_rate_limit_and_timeout(monkeypatch):
    monkeypatch.setenv("USE_MOCK", "false")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")

    attempts = {"count": 0}
    sleeps = []

    def flaky_create(**kwargs):
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise _make_rate_limit_error()
        if attempts["count"] == 2:
            raise _make_timeout_error()
        return _make_response([_text_block("성공 응답")], input_tokens=10, output_tokens=5)

    fake_client = SimpleNamespace(messages=SimpleNamespace(create=flaky_create))
    monkeypatch.setattr(llm_service.time, "sleep", sleeps.append)

    with patch("anthropic.Anthropic", return_value=fake_client):
        reply, _ = llm_service.generate_chat_reply([{"role": "user", "content": "안녕"}])

    assert reply == "성공 응답"
    assert attempts["count"] == 3
    assert sleeps == [1, 2]


def test_retry_exhaustion_reraises_and_auth_error_does_not_retry(monkeypatch):
    monkeypatch.setenv("USE_MOCK", "false")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")

    sleeps = []
    monkeypatch.setattr(llm_service.time, "sleep", sleeps.append)

    always_429 = SimpleNamespace(
        messages=SimpleNamespace(create=lambda **kw: (_ for _ in ()).throw(_make_rate_limit_error()))
    )
    with patch("anthropic.Anthropic", return_value=always_429):
        with pytest.raises(anthropic.RateLimitError):
            llm_service.generate_chat_reply([{"role": "user", "content": "재시도"}])
    assert sleeps == [1, 2, 4]

    sleeps.clear()
    auth_calls = {"count": 0}

    def raise_auth(**kwargs):
        auth_calls["count"] += 1
        raise _make_auth_error()

    auth_client = SimpleNamespace(messages=SimpleNamespace(create=raise_auth))
    with patch("anthropic.Anthropic", return_value=auth_client):
        with pytest.raises(anthropic.AuthenticationError):
            llm_service.generate_chat_reply([{"role": "user", "content": "인증오류"}])
    assert auth_calls["count"] == 1
    assert sleeps == []


def test_real_chat_reply_merges_consecutive_same_role_messages(monkeypatch):
    monkeypatch.setenv("USE_MOCK", "false")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")

    recorded = {}

    def fake_create(**kwargs):
        recorded.update(kwargs)
        return _make_response([_text_block("정리 답변")], input_tokens=30, output_tokens=15)

    fake_client = SimpleNamespace(messages=SimpleNamespace(create=fake_create))
    messages = [
        {"role": "assistant", "content": "초기 안내"},
        {"role": "user", "content": "첫 질문"},
        {"role": "user", "content": "두 번째 질문"},
        {"role": "assistant", "content": "첫 답변"},
        {"role": "assistant", "content": "추가 답변"},
        {"role": "user", "content": "마무리 질문"},
    ]
    with patch("anthropic.Anthropic", return_value=fake_client):
        reply, _ = llm_service.generate_chat_reply(messages)

    assert reply == "정리 답변"
    assert recorded["messages"] == [
        {"role": "user", "content": "첫 질문\n\n두 번째 질문"},
        {"role": "assistant", "content": "첫 답변\n\n추가 답변"},
        {"role": "user", "content": "마무리 질문"},
    ]


def test_code_fence_with_prose_and_uppercase_risk_level(monkeypatch):
    monkeypatch.setenv("USE_MOCK", "false")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")

    report_payload = {
        "headline": "세션 요약",
        "best_shot_summary": "A컷 중심 추천",
        "cleanup_advice": "C컷 정리 권장",
        "findings": ["구도 안정적"],
        "risk_level": " LOW ",
    }
    wrapped_report = "분석 결과입니다:\n```json\n" + json.dumps(report_payload, ensure_ascii=False) + "\n```\n참고하세요."
    fake_report_client = SimpleNamespace(
        messages=SimpleNamespace(create=lambda **kw: _make_response([_text_block(wrapped_report)]))
    )
    with patch("anthropic.Anthropic", return_value=fake_report_client):
        report, _ = llm_service.generate_culling_report({"total_photos": 2})

    assert report["risk_level"] == "low"

    vision_payload = {"final_score": 8.4}
    wrapped_vision = "평가 JSON:\n```json\n" + json.dumps(vision_payload) + "\n```\n완료."
    fake_vision_client = SimpleNamespace(
        messages=SimpleNamespace(create=lambda **kw: _make_response([_text_block(wrapped_vision)]))
    )
    with patch("anthropic.Anthropic", return_value=fake_vision_client):
        out_text, _ = llm_service.analyze_photo_with_claude(b"\xff\xd8\xff", "prompt")

    assert json.loads(out_text) == {"final_score": 8.4}


def test_summary_context_sanitizes_nan_date_and_scalar_in_mock_and_real(monkeypatch):
    class _FakeIntScalar:
        def item(self):
            return 7

    class _FakeFloatScalar:
        def item(self):
            return 8.25

    summary_context = {
        "session_label": "제주",
        "total_photos": _FakeIntScalar(),
        "avg_score": float("nan"),
        "captured_date": date(2026, 1, 10),
        "bonus": _FakeFloatScalar(),
        "a_cut_count": 2,
        "b_cut_count": 3,
        "c_cut_count": 2,
    }

    # Mock 모드 검증
    mock_report, _ = llm_service.generate_culling_report(summary_context)
    assert mock_report["risk_level"] == "low"
    assert "총 7장" in mock_report["findings"][0]
    assert "평균 0.00점" in mock_report["headline"]

    mock_chat, _ = llm_service.generate_chat_reply([{"role": "user", "content": "요약"}], summary_context=summary_context)
    assert "사진 7장" in mock_chat
    assert "평균 0.00점" in mock_chat

    # Real 모드 검증
    monkeypatch.setenv("USE_MOCK", "false")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    sent_payloads = []

    def fake_create(**kwargs):
        sent_payloads.append(kwargs)
        if kwargs["messages"][0]["content"] != "질문":
            return _make_response(
                [
                    _text_block(
                        json.dumps(
                            {
                                "headline": "ok",
                                "best_shot_summary": "ok",
                                "cleanup_advice": "ok",
                                "findings": ["ok"],
                                "risk_level": "medium",
                            }
                        )
                    )
                ]
            )
        return _make_response([_text_block("답변")])

    fake_client = SimpleNamespace(messages=SimpleNamespace(create=fake_create))
    with patch("anthropic.Anthropic", return_value=fake_client):
        llm_service.generate_culling_report(summary_context)
        llm_service.generate_chat_reply([{"role": "user", "content": "질문"}], summary_context=summary_context)

    report_sent = json.loads(sent_payloads[0]["messages"][0]["content"])
    assert report_sent["total_photos"] == 7
    assert report_sent["avg_score"] is None
    assert report_sent["captured_date"] == "2026-01-10"
    assert report_sent["bonus"] == 8.25
    assert '"captured_date": "2026-01-10"' in sent_payloads[1]["system"]


def test_boolean_streamlit_secret_use_mock_false(monkeypatch):
    monkeypatch.delenv("USE_MOCK")
    fake_st = ModuleType("streamlit")
    fake_st.secrets = {"USE_MOCK": False}
    monkeypatch.setitem(sys.modules, "streamlit", fake_st)
    assert llm_service.is_mock_mode() is False
