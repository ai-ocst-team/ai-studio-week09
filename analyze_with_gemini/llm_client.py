"""[MOCK] 외부 VLM 의존성의 경계. 실제 API 호출과 키 사용은 하지 않는다."""


def generate_analysis(image_bytes: bytes, model: str, prompt: str) -> str:
    """[MOCK] 사전 정의한 가상 분석 JSON 문자열을 반환한다. Copilot 구현 예정."""
    raise NotImplementedError("Copilot으로 구현할 단계입니다.")
