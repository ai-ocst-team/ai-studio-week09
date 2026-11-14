"""[MOCK] 외부 VLM 의존성의 경계. USE_MOCK 전환을 통해 Mock/실제 API 분기를 제공한다."""
import json
import logging
import os

logger = logging.getLogger(__name__)

USE_MOCK = True
_MOCK_TRUE_VALUES = frozenset({"true", "1", "yes", "on"})


def _is_mock_enabled() -> bool:
    """모듈 상수 USE_MOCK 및 환경 변수 USE_MOCK을 기준으로 Mock 모드 여부를 반환한다."""
    env_flag = os.getenv("USE_MOCK", "true").strip().lower()
    return bool(USE_MOCK) and env_flag in _MOCK_TRUE_VALUES


def _generate_mock(model: str) -> str:
    """[MOCK] 고정된 가상 분석 JSON 문자열을 반환한다."""
    logger.info("[MOCK] 실제 VLM API를 호출하지 않고 가상 응답을 반환합니다. (model=%s)", model)
    response = {
        "final_score": 8.0,
        "composition_score": 8.0,
        "lighting_score": 8.0,
        "color_score": 8.0,
        "technique_score": 8.0,
        "aesthetic_tags": {
            "피사체 장르": [],
            "빛의 조건": [],
            "피사체 동세": [],
            "카메라 앵글": [],
            "공간 구성": [],
            "색채 조화": [],
        },
        "focus_status": "판별 불가",
    }
    return json.dumps(response, ensure_ascii=False, allow_nan=False)


def _generate_real(image_bytes: bytes, model: str, prompt: str) -> str:
    """실제 Gemini VLM API 호출 경계 (13주차 API 키 연동 후 구현 예정)."""
    raise NotImplementedError(
        "실제 Gemini API 연동은 13주차 API 키 연결 이후 구현됩니다. USE_MOCK=true 모드를 사용하세요."
    )


def generate_analysis(image_bytes: bytes, model: str, prompt: str) -> str:
    """[MOCK] USE_MOCK 설정에 따라 가상 분석 JSON을 반환하거나 실제 API 경계를 호출한다.

    Args:
        image_bytes: 비어 있지 않은 이미지 바이트.
        model: 비어 있지 않은 모델명.
        prompt: 비어 있지 않은 요청 문자열.

    Returns:
        점수 5개, 6개 태그 범주, 초점 상태를 갖춘 JSON 문자열.

    Raises:
        TypeError: 인자의 타입이 잘못된 경우.
        ValueError: 인자가 비어 있거나 공백뿐인 경우.
        NotImplementedError: USE_MOCK이 비활성화된 상태에서 실제 API 호출을 시도한 경우.
    """
    if not isinstance(image_bytes, bytes):
        raise TypeError("image_bytes는 bytes여야 합니다.")
    if not isinstance(model, str):
        raise TypeError("model은 str이어야 합니다.")
    if not isinstance(prompt, str):
        raise TypeError("prompt는 str이어야 합니다.")
    if not image_bytes:
        raise ValueError("image_bytes는 비어 있을 수 없습니다.")
    if not model.strip():
        raise ValueError("model은 공백일 수 없습니다.")
    if not prompt.strip():
        raise ValueError("prompt는 공백일 수 없습니다.")

    if _is_mock_enabled():
        return _generate_mock(model=model)
    return _generate_real(image_bytes=image_bytes, model=model, prompt=prompt)
