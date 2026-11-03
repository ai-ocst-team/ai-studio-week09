from __future__ import annotations
import hashlib, io, math
from pathlib import Path
from typing import Any
from PIL import Image, ImageOps, UnidentifiedImageError

EXIF_IFD_POINTER = 0x8769
# 카메라 모델은 기본 IFD, 나머지는 Exif 서브 IFD에서 조회한다.
BASE_TAGS = {"camera_model": (0x0110,)}
SUB_TAGS = {
    "aperture": (0x829D,),
    "shutter_speed": (0x829A,),
    "iso": (0x8827,),
    "focal_length": (0x920A,),
    "lens_model": (0xA434,),
    "captured_at": (0x9003,),
}


def _normalize_exif_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="replace")
    if isinstance(value, str):
        value = value.strip("\x00 ")
        return value or None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return value if math.isfinite(value) else None
    if hasattr(value, "numerator") and hasattr(value, "denominator"):
        try:
            number = float(value)
        except (TypeError, ValueError, ZeroDivisionError):
            return None
        return number if math.isfinite(number) else None
    if isinstance(value, (tuple, list)) and len(value) == 1:
        return _normalize_exif_value(value[0])
    return None


def extract_safe_exif(image: Image.Image) -> dict[str, Any]:
    """안전한 EXIF(화이트리스트 7개)만 추출한다. 없거나 실패하면 {}."""
    try:
        base = image.getexif()
        if not base:
            return {}
        sub = base.get_ifd(EXIF_IFD_POINTER)
    except (AttributeError, TypeError, ValueError, OSError, SyntaxError):
        return {}

    result: dict[str, Any] = {}
    for source, table in ((base, BASE_TAGS), (sub, SUB_TAGS)):
        for key, tags in table.items():
            for tag in tags:
                if tag not in source:
                    continue
                value = _normalize_exif_value(source.get(tag))
                if value is not None:
                    result[key] = value
                    break
    return result


def _dhash(upload_bytes: bytes) -> str:
    with Image.open(io.BytesIO(upload_bytes)) as img:
        small = img.convert("L").resize((9, 8), Image.Resampling.LANCZOS)
        pixels = list(small.getdata())
    value = 0
    for row in range(8):
        for col in range(8):
            if pixels[row * 9 + col] < pixels[row * 9 + col + 1]:
                value |= 1 << (row * 8 + col)
    return f"{value:016x}"


def prepare_photo(image_path: str | Path) -> dict[str, Any]:
    """사진 경로를 받아 VLM 업로드용 JPEG와 메타데이터를 준비한다.

    예외: FileNotFoundError("사진 파일을 찾을 수 없음"),
    ValueError("지원하지 않는 이미지 형식"), ValueError("손상된 이미지 파일")
    """
    path = Path(image_path)
    if not path.is_file():
        raise FileNotFoundError("사진 파일을 찾을 수 없음")

    try:
        with Image.open(path) as opened:
            if opened.format not in {"JPEG", "PNG", "WEBP", "MPO"}:
                raise ValueError("지원하지 않는 이미지 형식")
            opened.load()
            safe_exif = extract_safe_exif(opened)
            image = ImageOps.exif_transpose(opened)

            if image.mode in ("RGBA", "LA", "P"):
                rgba = image.convert("RGBA")
                bg = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
                image = Image.alpha_composite(bg, rgba).convert("RGB")
            elif image.mode != "RGB":
                image = image.convert("RGB")

            if max(image.size) > 3072:
                scale = 3072 / max(image.size)
                image = image.resize(
                    (max(1, round(image.width * scale)), max(1, round(image.height * scale))),
                    Image.Resampling.LANCZOS,
                )

            buf = io.BytesIO()
            image.save(buf, format="JPEG", quality=90)
            upload_bytes = buf.getvalue()
            width, height = image.width, image.height
    except UnidentifiedImageError as exc:
        raise ValueError("지원하지 않는 이미지 형식") from exc
    except (OSError, SyntaxError) as exc:
        raise ValueError("손상된 이미지 파일") from exc

    sha = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            sha.update(chunk)

    return {
        "path": str(path),
        "sha256": sha.hexdigest(),
        "safe_exif": safe_exif,
        "upload_bytes": upload_bytes,
        "dhash": _dhash(upload_bytes),
        "width": width,
        "height": height,
    }
