"""[MOCK] 외부 VLM 의존성의 경계. 실제 API 호출과 키 사용은 하지 않는다."""
import json


def generate_analysis(image_bytes: bytes, model: str, prompt: str) -> str:
    """[MOCK] 고정된 가상 분석을 JSON 문자열로 반환하며 실제 이미지를 분석하지 않는다.

    Args:
        image_bytes: 비어 있지 않은 이미지 바이트.
        model: 비어 있지 않은 모델명.
        prompt: 비어 있지 않은 요청 문자열.

    Returns:
        점수 5개, 6개 태그 범주, 초점 상태를 갖춘 가상 JSON 문자열.

    Raises:
        TypeError: 인자의 타입이 잘못된 경우.
        ValueError: 인자가 비어 있거나 공백뿐인 경우.
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
