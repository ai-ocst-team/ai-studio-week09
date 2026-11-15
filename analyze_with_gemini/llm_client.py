"""VLM 호출 경계: USE_MOCK 기본값은 true이며 실제 API는 아직 연결하지 않는다."""
import json
import logging
import os

logger = logging.getLogger(__name__)


def _generate_real(image_bytes: bytes, model: str, prompt: str) -> str:
    """13주차 API 구현 교체 지점. 현재는 네트워크 요청 없이 명시적으로 실패한다."""
    raise NotImplementedError("실제 VLM API는 아직 연결되지 않았습니다. USE_MOCK=true를 사용하세요.")


def generate_analysis(image_bytes: bytes, model: str, prompt: str) -> str:
    """[MOCK] 모드에서는 가상 JSON을, 비Mock 모드에서는 실제 API 경계를 사용한다.

    USE_MOCK 환경 변수를 호출 시점마다 읽는다. 미설정 시 true이며
    true/1/yes/on 및 false/0/no/off를 지원한다(대소문자·주변 공백 무시).
    파이프라인은 use_mock 인자를 이 환경 변수에 반영한다.

    Args:
        image_bytes: 비어 있지 않은 이미지 바이트.
        model: 비어 있지 않은 모델명.
        prompt: 비어 있지 않은 요청 문자열.

    Returns:
        점수 5개, 6개 태그 범주, 초점 상태를 갖춘 JSON 문자열.

    Raises:
        TypeError: 인자의 타입이 잘못된 경우.
        ValueError: 인자가 비어 있거나 USE_MOCK 설정이 허용값이 아닌 경우.
        NotImplementedError: 비Mock 모드에서 아직 미구현인 실제 API 경계에 도달한 경우.
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

    # import 시점에 고정하지 않아 파이프라인의 모드 전환이 즉시 반영된다.
    mode = os.getenv("USE_MOCK", "true").strip().lower()
    if mode in {"false", "0", "no", "off"}:
        return _generate_real(image_bytes=image_bytes, model=model, prompt=prompt)
    if mode not in {"true", "1", "yes", "on"}:
        raise ValueError("USE_MOCK은 true/1/yes/on 또는 false/0/no/off여야 합니다.")

    # 이미지·프롬프트·EXIF·사용자 의도 등 입력 내용은 로그에 출력하지 않는다.
    logger.info("[MOCK] 실제 VLM 호출 없이 가상 분석 응답을 반환합니다.")
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
