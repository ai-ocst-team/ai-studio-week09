from PIL import Image
from pipeline import run_pipeline


REQUIRED_KEYS = {
    "total_photos",
    "monthly_trend",
    "top_tags",
    "bottom_tags",
    "user_intent_hint",
    "processed_count",
    "failed_count",
}


def create_image(folder, filename, color=(100, 150, 200)):
    # EXIF가 포함되지 않은 정상 테스트 이미지를 생성한다.
    image_path = folder / filename
    Image.new("RGB", (32, 32), color).save(image_path)
    return image_path


def check_result_contract(result):
    # 최종 반환값에 필수 항목이 있고 자료형이 올바른지 확인한다.
    assert isinstance(result, dict)
    assert REQUIRED_KEYS <= result.keys()
    assert isinstance(result["total_photos"], int)
    assert isinstance(result["monthly_trend"], dict)
    assert isinstance(result["top_tags"], list)
    assert isinstance(result["bottom_tags"], list)
    assert isinstance(result["user_intent_hint"], str)
    assert isinstance(result["processed_count"], int)
    assert isinstance(result["failed_count"], int)

    # 태그 통계가 존재한다면 각 항목의 기본 구조도 확인한다.
    for item in result["top_tags"] + result["bottom_tags"]:
        assert {"tag", "avg_score", "count"} <= item.keys()

def check_empty_contract(result, failed_count):
    # 빈 데이터의 반환 계약을 공통으로 검증한다.
    check_result_contract(result)
    assert result["total_photos"] == 0
    assert result["processed_count"] == 0
    assert result["failed_count"] == failed_count
    assert result["monthly_trend"] == {}
    assert result["top_tags"] == []
    assert result["bottom_tags"] == []

def test_happy_path(tmp_path):
    # 정상 이미지 두 장이 전체 파이프라인을 통과하는지 확인한다.
    create_image(tmp_path, "photo1.jpg")
    create_image(tmp_path, "photo2.png", (200, 100, 50))

    result = run_pipeline(tmp_path, hint="풍경 중심", use_mock=True)

    check_result_contract(result)
    assert result["total_photos"] == 2
    assert result["total_photos"] > 0
    assert result["processed_count"] == 2
    assert result["failed_count"] == 0
    assert result["user_intent_hint"] == "풍경 중심"


def test_empty_folder(tmp_path):
    # 빈 폴더를 입력해도 오류 없이 빈 집계 결과를 반환하는지 확인한다.
    result = run_pipeline(tmp_path, use_mock=True)

    check_empty_contract(result, failed_count=0)


def test_corrupted_image(tmp_path):
    # 0바이트 이미지가 실패로 집계되고 전체 실행은 끝나는지 확인한다.
    (tmp_path / "broken.jpg").write_bytes(b"")

    result = run_pipeline(tmp_path, use_mock=True)

    check_empty_contract(result, failed_count=1)


def test_missing_exif(tmp_path):
    # 촬영 날짜 등 EXIF 정보가 없는 이미지도 정상 처리되는지 확인한다.
    image_path = create_image(tmp_path, "no_exif.jpg")
    with Image.open(image_path) as image:
        assert not image.getexif()

    result = run_pipeline(tmp_path, use_mock=True)

    check_result_contract(result)
    assert result["total_photos"] == 1
    assert result["processed_count"] == 1
    assert result["failed_count"] == 0
    assert result["monthly_trend"] == {}


def test_continues_after_image_error(tmp_path):
    # 정상 이미지 사이에 손상된 이미지를 넣어 나머지도 처리되는지 확인한다.
    create_image(tmp_path, "01_valid.jpg")
    (tmp_path / "02_broken.jpg").write_bytes(b"")
    create_image(tmp_path, "03_valid.png", (20, 40, 60))

    result = run_pipeline(tmp_path, use_mock=True)

    check_result_contract(result)
    assert result["total_photos"] == 2
    assert result["processed_count"] == 2
    assert result["failed_count"] == 1
