import json
import re
from typing import Any

PhotoAnalysis = dict[str, Any]

_TAG_VOCABULARY = {
	"피사체 장르": {"자연풍경", "건축도시", "인물동물", "사물정물", "거리스냅"},
	"빛의 조건": {"안정된 순광", "골든아워", "흐린날 확산광", "극단적 역광", "저조도 야경"},
	"피사체 동세": {"완전 정지", "완만한 흐름", "예측불가 빠른동세", "찰나의 순간"},
	"카메라 앵글": {"아이레벨", "로우 앵글", "하이앵글(탑뷰)", "피사체 눈높이 일치", "틸트사선"},
	"공간 구성": {"단일피사체 집중", "다층 레이어", "프레임인프레임", "대칭패턴", "여백의미"},
	"색채 조화": {"자연스런 뉴트럴", "뚜렷한 보색대비", "차분한 모노톤", "다채로운 색정돈", "절제된 톤다운"},
}
_FOCUS_STATUSES = {"완벽 칼초점", "미세 앞핀", "미세 뒤핀", "초점 이탈", "판별 불가"}
_REQUIRED_FIELDS = {
	"final_score",
	"composition_score",
	"lighting_score",
	"color_score",
	"technique_score",
	"aesthetic_tags",
	"focus_status",
}


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
		raise ValueError("aesthetic_tags는 범주별 태그 객체여야 합니다.")
	for category, tags in aesthetic_tags.items():
		if category not in _TAG_VOCABULARY:
			raise ValueError(f"정의되지 않은 태그 범주입니다: {category}")
		if not isinstance(tags, list):
			raise ValueError(f"{category}의 태그는 리스트여야 합니다.")
		if len(tags) > 2:
			raise ValueError(f"{category}의 태그는 최대 2개까지 허용됩니다.")
		if any(not isinstance(tag, str) or tag not in _TAG_VOCABULARY[category] for tag in tags):
			raise ValueError(f"{category}에 허용되지 않은 태그가 있습니다.")

	if data["focus_status"] not in _FOCUS_STATUSES:
		raise ValueError("focus_status가 허용된 값이 아닙니다.")

	return data
