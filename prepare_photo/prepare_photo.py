from __future__ import annotations
import hashlib, io
from pathlib import Path
from typing import Any
from PIL import Image, ImageOps, UnidentifiedImageError


def _normalize_exif_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (int, float, str)):
        return value
    if isinstance(value, bytes):
        try:
            return value.decode("utf-8")
        except UnicodeDecodeError:
            return value.decode("utf-8", errors="replace")
    if hasattr(value, "numerator") and hasattr(value, "denominator"):
        try:
            return float(value)
        except (TypeError, ValueError):
            pass
    if isinstance(value, (tuple, list)):
        if len(value) == 1:
            return _normalize_exif_value(value[0])
        if len(value) == 2 and all(isinstance(item, (int, float)) for item in value):
            denominator = float(value[1])
            if denominator != 0:
                return float(value[0]) / denominator
    return str(value)


def extract_safe_exif(image: Image.Image) -> dict[str, Any]:
    """입력으로 받은 PIL 이미지에서 안전한 EXIF 메타데이터만 추출한다.

    입력:
        PIL.Image 객체. 이미지의 EXIF 태그를 읽어 보안상 허용된 항목만 검사한다.

    출력:
        조리개, 셔터스피드, ISO, 초점거리, 카메라 모델명, 렌즈 모델명, 촬영 일시를 담은
        딕셔너리. 값이 없거나 EXIF를 읽을 수 없으면 빈 딕셔너리를 반환한다.

    예외:
        EXIF 데이터가 없거나 태그를 읽는 과정에서 오류가 발생하면 빈 dict를 반환한다.
    """
    try:
        exif = image.getexif()
    except (AttributeError, TypeError, ValueError, OSError):
        return {}

    if not exif:
        return {}

    whitelisted = {
        "aperture": (0x829D,),
        "shutter_speed": (0x829A,),
        "iso": (0x8827, 0x8829),
        "focal_length": (0x920A,),
        "camera_model": (0x0110,),
        "lens_model": (0xFDEA,),
        "captured_at": (0x9003,),
    }

    result: dict[str, Any] = {}
    for key, tags in whitelisted.items():
        for tag in tags:
            if tag not in exif:
                continue
            value = _normalize_exif_value(exif.get(tag))
            if value is not None and value != "":
                result[key] = value
                break
    return result


def prepare_photo(image_path: str | Path) -> dict[str, Any]:
    """사진 경로를 받아 VLM 업로드용 JPEG와 메타데이터를 준비한다.

    입력:
        분석할 이미지 파일의 경로. 문자열 또는 pathlib.Path를 받을 수 있다.

    출력:
        경로, SHA-256, 안전 EXIF, 업로드용 JPEG 바이트, dHash, 최종 너비와 높이 정보를 담은
        딕셔너리를 반환한다.

    예외:
        파일이 없으면 FileNotFoundError("사진 파일을 찾을 수 없음")를 발생시키고,
        읽을 수 없는 이미지 형식이면 ValueError("지원하지 않는 이미지 형식")을,
        손상된 이미지이면 ValueError("손상된 이미지 파일")을 발생시킨다.
    """
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError("사진 파일을 찾을 수 없음")

    try:
        with Image.open(path) as image:
            if image.format not in {"JPEG", "PNG", "WEBP", "MPO"}:
                raise ValueError("지원하지 않는 이미지 형식")

            try:
                image.load()
            except (OSError, SyntaxError, ValueError) as exc:
                raise ValueError("손상된 이미지 파일") from exc

            safe_exif = extract_safe_exif(image)
            image = ImageOps.exif_transpose(image)

            if image.mode != "RGB":
                if image.mode in {"RGBA", "LA", "PA", "P", "RGBa", "RGBX", "CMYK", "YCbCr"} or "A" in image.mode:
                    if "A" in image.mode or image.mode == "P":
                        rgba = image.convert("RGBA")
                        white = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
                        image = Image.alpha_composite(white, rgba).convert("RGB")
                    else:
                        image = image.convert("RGB")
                else:
                    image = image.convert("RGB")

            if max(image.size) > 3072:
                scale = 3072 / max(image.size)
                image = image.resize(
                    (
                        max(1, int(round(image.width * scale))),
                        max(1, int(round(image.height * scale))),
                    ),
                    Image.LANCZOS,
                )

            jpeg_buffer = io.BytesIO()
            image.save(jpeg_buffer, format="JPEG", quality=90)
            upload_bytes = jpeg_buffer.getvalue()

            sha256 = hashlib.sha256()
            with path.open("rb") as source_file:
                while True:
                    chunk = source_file.read(1024 * 1024)
                    if not chunk:
                        break
                    sha256.update(chunk)

            upload_image = Image.open(io.BytesIO(upload_bytes))
            try:
                d_hash_image = upload_image.convert("L").resize((9, 8), Image.LANCZOS)
                pixels = list(d_hash_image.getdata())
                hash_value = 0
                for row in range(8):
                    row_offset = row * 9
                    for col in range(8):
                        left = pixels[row_offset + col]
                        right = pixels[row_offset + col + 1]
                        if left < right:
                            hash_value |= 1 << (row * 8 + col)
                dhash = f"{hash_value & ((1 << 64) - 1):016x}"
            finally:
                upload_image.close()

            return {
                "path": str(path),
                "sha256": sha256.hexdigest(),
                "safe_exif": safe_exif,
                "upload_bytes": upload_bytes,
                "dhash": dhash,
                "width": image.width,
                "height": image.height,
            }
    except UnidentifiedImageError as exc:
        raise ValueError("지원하지 않는 이미지 형식") from exc
