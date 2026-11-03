"""prepare_photo 테스트 (T01~T04 + 보강). 실행: pytest -v test_prepare_photo.py

import 경로: 이 파일을 prepare_photo/ 폴더 안에 두고, 같은 폴더의 prepare_photo.py를 불러온다.
"""
import io
import random

import pytest
from PIL import Image

from prepare_photo import prepare_photo, extract_safe_exif

EXIF_SUB = 0x8769


def _make_exif(with_gps: bool = True) -> Image.Exif:
    exif = Image.Exif()
    exif[0x0110] = "TestCam"
    sub = exif.get_ifd(EXIF_SUB)
    sub[0x829A] = 1 / 200
    sub[0x829D] = 2.8
    sub[0x8827] = 100
    sub[0x920A] = 50.0
    sub[0xA434] = "TestLens"
    sub[0x9003] = "2024:01:02 03:04:05"
    sub[0xA431] = "SERIAL-1234"          # BodySerialNumber (PII)
    if with_gps:
        exif[0x013B] = "Secret Artist"   # Artist (PII)
        exif.get_ifd(0x8825)[0x0002] = (37.0, 30.0, 0.0)  # GPS
    return exif


@pytest.fixture
def sample_jpg(tmp_path):
    p = tmp_path / "sample.jpg"
    Image.new("RGB", (4000, 2000), (200, 30, 30)).save(p, "JPEG", exif=_make_exif())
    return p


# T01 정상: EXIF가 있는 JPEG
def test_t01_jpeg_with_exif(sample_jpg):
    r = prepare_photo(sample_jpg)
    assert len(r["sha256"]) == 64
    assert max(r["width"], r["height"]) <= 3072
    assert r["safe_exif"]["camera_model"] == "TestCam"
    assert r["safe_exif"]["lens_model"] == "TestLens"
    assert r["safe_exif"]["iso"] == 100
    assert r["safe_exif"]["shutter_speed"] == pytest.approx(0.005)
    assert len(r["safe_exif"]) == 7
    # PII 배제 (성공 기준 ①)
    assert "SERIAL-1234" not in str(r["safe_exif"])
    assert "Secret Artist" not in str(r["safe_exif"])
    assert not any("gps" in k.lower() for k in r["safe_exif"])
    # 업로드 바이트에도 EXIF가 남지 않아야 함
    with Image.open(io.BytesIO(r["upload_bytes"])) as up:
        assert len(up.getexif()) == 0
    assert len(r["dhash"]) == 16


# T02 정상: EXIF 없는 PNG
def test_t02_png_without_exif(tmp_path):
    p = tmp_path / "nature.png"
    Image.new("RGBA", (800, 600), (0, 128, 0, 128)).save(p, "PNG")
    r = prepare_photo(p)
    assert r["safe_exif"] == {}
    with Image.open(io.BytesIO(r["upload_bytes"])) as up:
        assert up.format == "JPEG"
        assert up.mode == "RGB"


# T03 경계: 대형 이미지 (8000x6000, 노이즈)
def test_t03_huge_image(tmp_path):
    p = tmp_path / "huge_photo.jpg"
    rnd = random.Random(0)
    small = Image.new("RGB", (80, 60))
    small.putdata([(rnd.randrange(256), rnd.randrange(256), rnd.randrange(256)) for _ in range(80 * 60)])
    small.resize((8000, 6000), Image.Resampling.BICUBIC).save(p, "JPEG", quality=95)
    r = prepare_photo(p)
    assert max(r["width"], r["height"]) <= 3072
    assert len(r["upload_bytes"]) <= 4 * 1024 * 1024


# T04 예외
def test_t04_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        prepare_photo(tmp_path / "ghost.jpg")


def test_t04_text_file(tmp_path):
    p = tmp_path / "invalid.txt"
    p.write_text("not an image")
    with pytest.raises(ValueError, match="지원하지 않는 이미지 형식"):
        prepare_photo(p)


# 보강 케이스 (수정한 결함의 회귀 테스트)
def test_directory_path_is_not_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        prepare_photo(tmp_path)


def test_truncated_jpeg(sample_jpg, tmp_path):
    bad = tmp_path / "bad.jpg"
    bad.write_bytes(sample_jpg.read_bytes()[:3000])
    with pytest.raises(ValueError, match="손상된 이미지 파일"):
        prepare_photo(bad)


def test_no_upscale_small_image(tmp_path):
    p = tmp_path / "small.jpg"
    Image.new("RGB", (3072, 1000)).save(p, "JPEG")
    r = prepare_photo(p)
    assert (r["width"], r["height"]) == (3072, 1000)


def test_extract_safe_exif_without_exif():
    assert extract_safe_exif(Image.new("RGB", (10, 10))) == {}

