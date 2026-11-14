"""analyze_with_gemini.llm_client의 USE_MOCK 분기 및 [MOCK] 로그 검증 테스트."""
import json
import logging

import pytest

from analyze_with_gemini import llm_client


def test_generate_analysis_mock_logs_marker_and_returns_valid_json(monkeypatch, caplog):
    """USE_MOCK 활성화 시 [MOCK] INFO 로그와 유효한 JSON 계약을 반환한다."""
    monkeypatch.setenv("USE_MOCK", "true")
    monkeypatch.setattr(llm_client, "USE_MOCK", True)

    with caplog.at_level(logging.INFO, logger=llm_client.logger.name):
        raw = llm_client.generate_analysis(
            image_bytes=b"fake-image-bytes",
            model="gemini-1.5-flash",
            prompt='{"task": "test"}',
        )

    assert "[MOCK]" in caplog.text
    parsed = json.loads(raw)
    assert parsed["final_score"] == 8.0
    assert parsed["focus_status"] == "판별 불가"
    assert len(parsed["aesthetic_tags"]) == 6


def test_generate_analysis_real_mode_via_env_raises_not_implemented(monkeypatch):
    """USE_MOCK=false 환경 변수 설정 시 실제 API 미구현 예외가 발생한다."""
    monkeypatch.setenv("USE_MOCK", "false")
    monkeypatch.setattr(llm_client, "USE_MOCK", True)

    with pytest.raises(NotImplementedError):
        llm_client.generate_analysis(
            image_bytes=b"fake-image-bytes",
            model="gemini-1.5-flash",
            prompt='{"task": "test"}',
        )


def test_generate_analysis_real_mode_via_module_flag_raises_not_implemented(monkeypatch):
    """모듈 상수 USE_MOCK=False 설정 시에도 실제 API 경계에서 NotImplementedError가 발생한다."""
    monkeypatch.setenv("USE_MOCK", "true")
    monkeypatch.setattr(llm_client, "USE_MOCK", False)

    with pytest.raises(NotImplementedError):
        llm_client.generate_analysis(
            image_bytes=b"fake-image-bytes",
            model="gemini-1.5-flash",
            prompt='{"task": "test"}',
        )


def test_generate_analysis_validates_inputs_before_real_mode(monkeypatch):
    """USE_MOCK=false여도 잘못된 입력에 대해서는 TypeError/ValueError를 먼저 발생시킨다."""
    monkeypatch.setenv("USE_MOCK", "false")

    with pytest.raises(TypeError):
        llm_client.generate_analysis(image_bytes="not-bytes", model="gemini-1.5-flash", prompt="ok")  # type: ignore[arg-type]

    with pytest.raises(ValueError):
        llm_client.generate_analysis(image_bytes=b"ok", model="   ", prompt="ok")
