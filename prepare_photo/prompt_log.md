# prompt_log.md — AI 활용 과정 기록

## prepare_photo — 2026-11-03, 작성자: 류시향
- **사용 도구**: VS Code GitHub Copilot (코드 생성)
- **보조 도구**: Claude Sonnet 5.5 (프롬프트 초안 정리, 코드 리딩 보조)
- **프롬프트 위치**: 커밋 `af86e35` (`prepare_photo/copilot_prompt.txt`, 2단계)
- **프롬프트 원문**:
  ````markdown
  당신은 파이썬 이미지 처리 및 백엔드 모듈 개발을 돕는 전문 어시스턴트입니다.
  'VLM 기반 사진 감성·구도 심층 비평 및 스마트 Culling 시스템(아트서강)'의 사진 적재·전처리 모듈(photo_analyzer.py)에 들어갈 함수 2개를 구현해 주세요.

  [함수 시그니처 — 변경 금지]
  def prepare_photo(image_path: str | Path) -> dict[str, Any]:
  def extract_safe_exif(image: Image.Image) -> dict[str, Any]:

  [파일 상단 import]
  from __future__ import annotations
  import hashlib, io
  from pathlib import Path
  from typing import Any
  from PIL import Image, ImageOps, UnidentifiedImageError

  [extract_safe_exif 명세]
  - 입력: PIL.Image 객체. 출력: 화이트리스트 키만 담은 dict.
  - 화이트리스트(7개)만 추출한다. 값이 없는 키는 결과에 넣지 않는다.
    1. aperture (조리개, FNumber)
    2. shutter_speed (셔터스피드, ExposureTime)
    3. iso (ISOSpeedRatings / PhotographicSensitivity)
    4. focal_length (초점거리, FocalLength)
    5. camera_model (카메라 모델명, Model)
    6. lens_model (렌즈 모델명, LensModel)
    7. captured_at (촬영 일시, DateTimeOriginal)
  - GPS IFD, 기기 일련번호(BodySerialNumber, LensSerialNumber, CameraOwnerName, Artist 등)는 절대 포함하지 않는다.
  - 값은 JSON/SQLite에 저장 가능한 기본 타입(int, float, str)으로 변환한다. IFDRational은 float로 바꾼다.
  - EXIF가 없거나 읽기 실패 시 빈 dict {}를 반환한다.

  [prepare_photo 입력 명세]
  image_path: 분석할 사진 파일의 경로(str 또는 Path).
  지원 포맷: JPEG, PNG, WEBP, MPO. (ARW는 Pillow가 직접 열지 못할 수 있으므로 이번 구현에서는 지원하지 않고, 열 수 없으면 아래 예외 규칙에 따른다.)

  [prepare_photo 출력 명세 — 딕셔너리 계약]
  {
      "path": 입력 파일 경로(str),
      "sha256": 원본 파일 바이트의 SHA-256 hex 문자열(str, 64자),
      "safe_exif": extract_safe_exif 결과(dict),
      "upload_bytes": VLM 업로드용 JPEG 바이트(bytes),
      "dhash": upload_bytes 기준 64비트 dHash를 16자리 hex 문자열로 표현한 값(str),
      "width": 최종 이미지 너비(int),
      "height": 최종 이미지 높이(int)
  }

  [처리 순서 — 반드시 이 순서를 지킬 것]
  1. 경로를 Path로 변환. 파일이 존재하지 않으면 FileNotFoundError("사진 파일을 찾을 수 없음") 발생.
  2. Image.open으로 열기. PIL.UnidentifiedImageError가 나면 ValueError("지원하지 않는 이미지 형식") 발생. (예: 텍스트 파일)
  3. 열린 이미지의 실제 포맷(image.format)이 JPEG, PNG, WEBP, MPO 중 하나가 아니면 ValueError("지원하지 않는 이미지 형식") 발생. 확장자가 아니라 실제 포맷으로 판단한다.
  4. 이미지 데이터를 끝까지 읽어 검증(image.load()). 읽기 중 OSError, SyntaxError, ValueError 등이 나면 ValueError("손상된 이미지 파일") 발생.
  5. extract_safe_exif(image)로 안전 EXIF 추출. (방향 보정 전에 수행)
  6. ImageOps.exif_transpose로 EXIF 회전 정보에 따라 방향 보정.
  7. 색상 모드가 RGB가 아니면 RGB로 변환. (RGBA·P 모드는 흰 배경에 합성하여 평탄화)
  8. 긴 변이 3072px를 초과(>)하면 비율을 유지하여 긴 변을 3072px로 축소(Image.LANCZOS). 3072px 이하이면 축소하지 않는다.
  9. JPEG(quality=90)로 io.BytesIO에 인코딩하여 upload_bytes 생성. 이때 EXIF 등 메타데이터를 다시 붙이지 않는다.
  10. 원본 파일을 청크(1MB 단위)로 읽어 SHA-256 계산. 파일 전체를 한 번에 메모리에 올리지 않는다.
  11. upload_bytes를 다시 열어 9x8 그레이스케일로 축소(LANCZOS)한 뒤, 각 행에서 인접 픽셀 비교(왼쪽 < 오른쪽)로 64비트 dHash를 계산하고 16자리 hex 문자열로 변환.
  12. 위 출력 명세의 dict를 반환. width/height는 축소 후 최종 크기.

  [예외 요약]
  - 파일 없음 → FileNotFoundError
  - 식별 불가 또는 비지원 포맷 → ValueError("지원하지 않는 이미지 형식")
  - 손상된 파일 → ValueError("손상된 이미지 파일")

  [제약 조건]
  - Pillow와 표준 라이브러리만 사용할 것. (numpy 등 추가 라이브러리 금지)
  - 원본 파일을 수정하거나 덮어쓰지 말 것.
  - GPS, 기기 일련번호 등 개인식별정보(PII)는 반환값 어디에도 포함 금지.
  - 이미지 파일 핸들은 with 문으로 반드시 해제할 것.
  - 광범위한 `except:` 또는 `except Exception:`으로 예외를 삼키지 말 것. 구체적인 예외 타입만 잡을 것.
  - 함수에 한국어 docstring(입력, 출력, 예외)을 작성할 것.
  - 미사용 import를 남기지 말 것.
  - 함수 시그니처에 매개변수를 추가하거나 이름을 바꾸지 말 것.
  - 코드만 출력하고, 짧은 설명은 코드 아래에 3줄 이내로 적을 것.
  ````
- **생성 코드 위치**: 커밋 `348eee4` (GitHub Copilot 생성 원본, `prepare_photo/prepare_photo.py`, 3단계)
- **코드 리딩에서 발견한 결함 및 실무 개선점**:
  1. **서브 IFD 미조회로 실제 카메라 EXIF 대부분 누락**: `image.getexif()`의 기본 영역만 조회하여, 서브 IFD(`0x8769`)에 저장되는 조리개·셔터스피드·ISO·초점거리·렌즈 모델·촬영 일시를 실제 카메라 사진에서 읽지 못하고 `camera_model`만 남을 가능성이 높음. Copilot 자체 시험은 가짜 EXIF를 기본 영역에 직접 넣어 통과했기 때문에 이 결함이 가려져 있었으며, 정량 메타데이터 결합이라는 설계 목적(설계문서 문제 정의서 ③)을 무너뜨리는 심각한 결함.
  2. **잘못된 EXIF 태그 번호**: 렌즈 모델에 `0xFDEA`를 사용했으나 Pillow `ExifTags`에 존재하지 않는 번호이고(`TAGS.get(0xFDEA)` → `None`), 표준 LensModel은 `0xA434`임. ISO 보조 후보 `0x8829`는 ISO가 아니라 `Interlace` 태그(`TAGS.get(0x8829)` → `Interlace`)여서 엉뚱한 값이 `iso`로 저장될 위험이 있음.
  3. **손상 파일·비파일 경로 예외 누락**: `Image.open` 단계에서 발생하는 `OSError`/`SyntaxError`는 `UnidentifiedImageError`가 아니므로 `ValueError("손상된 이미지 파일")`로 변환되지 않고 그대로 노출됨. 또한 `path.exists()`는 폴더도 통과시켜 `IsADirectoryError`·`PermissionError`가 명세 밖 예외로 발생함.
  4. **RGB 변환 분기 중복 및 가독성 저하**: 동일한 모드 조건을 3중으로 검사하고 도달하지 않는 분기가 있어, 동작은 맞지만 모든 줄을 설명할 수 있어야 한다는 리딩 기준에 부합하지 않음.
  5. **EXIF 값 정규화 허술**: 분모가 0인 분수가 `nan`/`inf`로 변환되어 SQLite·JSON 저장 시 문제가 되고, 문자열 끝의 `\x00`이 제거되지 않으며, 길이 2 튜플을 무조건 분수로 해석함.
  6. **dHash 비트 순서 미문서화**: 첫 비교 결과가 최하위 비트에 들어가 `imagehash` 등 외부 라이브러리 해시와 값이 달라질 수 있음. 내부 비교용으로는 무방하므로 README에 규칙을 명시하는 개선점으로 분류.
- **수정 내역 (커밋 `f256c6e`)**: `prepare_photo/prepare_photo.py` 원본을 직접 수정 (원본은 커밋 `348eee4`에 보존)
  - **서브 IFD 조회 추가**: `base = image.getexif()`와 `base.get_ifd(0x8769)`를 함께 사용하여, 카메라 모델(`0x0110`)은 기본 IFD에서, 조리개·셔터스피드·ISO·초점거리·렌즈 모델·촬영 일시는 Exif 서브 IFD에서 조회하도록 변경.
  - **태그 번호 교정**: 렌즈 모델 `0xFDEA` → `0xA434`(LensModel)로 교체, ISO 후보에서 `Interlace` 태그인 `0x8829`를 제거하고 `0x8827`(ISOSpeedRatings)만 사용.
  - **예외 처리 보강**: `path.exists()` → `path.is_file()`로 변경하여 폴더 경로도 `FileNotFoundError`로 처리. `Image.open`/`load` 구간의 `OSError`·`SyntaxError`를 `ValueError("손상된 이미지 파일")`로 변환(바깥 `try`에서 일괄 처리).
  - **RGB 변환 단순화**: 3중 분기를 `RGBA/LA/P` 알파 합성 분기와 `!= "RGB"` 단순 변환 분기 두 개로 정리.
  - **EXIF 값 정규화 강화**: 문자열 `strip("\x00 ")` 적용, `nan`/`inf` 및 분모 0 값은 키에서 제외, 2개짜리 튜플의 임의 분수 해석 제거, `bytes`는 디코딩 후 동일 규칙 적용.
  - **dHash 분리**: 해시 계산을 `_dhash()` 함수로 분리하고 `with`로 핸들 해제. (비트 순서 규칙 README 기록은 결함 6의 후속 과제)
  - **부수 개선**: `Image.LANCZOS` → `Image.Resampling.LANCZOS`, 미사용 비트 마스크 제거.
- **테스트 커밋**: `8d15303` (`prepare_photo/test_prepare_photo.py`, 5단계)
  - 테스트 구성: T01(EXIF JPEG), T02(EXIF 없는 PNG), T03(8000×6000 대용량), T04(없는 파일·텍스트 파일 예외) + 보강 테스트(폴더 경로, 손상 JPEG, 소형 이미지 확대 금지, EXIF 없는 이미지의 `extract_safe_exif`)
- **최종 테스트 결과**:
  - `pytest -v test_prepare_photo.py` 실행 결과: 9 passed, 0 failed
  - 증거: `evidence/pytest_result.txt`
- **설계문서와 달라진 점**:
  - ARW 포맷은 이번 구현에서 제외 (JPEG, PNG, WEBP, MPO만 지원)
  - EXIF 7번째 항목을 `captured_at`(DateTimeOriginal)으로 지정 (설계문서에 명시 없음)
  - `dhash`는 64비트 값을 16자리 hex 문자열(`str`)로 반환
- **남은 과제**: 실제 카메라·스마트폰 JPEG로 `safe_exif` 검증
