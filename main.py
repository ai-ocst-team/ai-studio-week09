# -*- coding: utf-8 -*-
"""[Task 1] 전체 사진 평가 AI 오케스트레이션 CLI 진입점.

사용법 예시:
    python main.py --image-dir sample_images/ --hint "배경 위주 풍경"
    python main.py --image-dir sample_images/ --output results/summary.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Windows cp949 인코딩 호환성 처리
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

from pipeline import run_pipeline



def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    """CLI 인자 파서 정의."""
    parser = argparse.ArgumentParser(
        description="아트서강 - 전체 사진 평가 AI 오케스트레이션 파이프라인 CLI",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--image-dir",
        type=str,
        default="sample_images",
        help="분석 대상 사진이 모여 있는 디렉토리 경로",
    )
    parser.add_argument(
        "--hint",
        type=str,
        default="",
        help="사용자 촬영 의도 힌트 (예: '인물 중심', '배경 색감 강조')",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="gemini-1.5-flash",
        help="VLM 분석 모델 식별자",
    )
    parser.add_argument(
        "--use-mock",
        action="store_true",
        default=True,
        help="[MOCK] 가상 VLM 응답 모드 활성화 (기본값: True)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="",
        help="결과 JSON을 저장할 파일 경로 (선택 사항)",
    )
    return parser.parse_args(args)


def main() -> int:
    """CLI 메인 실행 함수."""
    args = parse_args()

    image_dir = Path(args.image_dir)
    print("=" * 60)
    print("[아트서강] 사진 평가 AI 오케스트레이션 파이프라인 가동")
    print(f">> 대상 디렉토리: {image_dir.resolve()}")
    if args.hint:
        print(f">> 사용자 촬영 의도: '{args.hint}'")
    print(f">> VLM 모드: {'[MOCK] 모드' if args.use_mock else '실제 API 모드'} ({args.model})")
    print("=" * 60)

    try:
        results = run_pipeline(
            image_dir=image_dir,
            hint=args.hint,
            model=args.model,
            use_mock=args.use_mock,
        )
    except Exception as exc:
        print(f"[ERROR] 파이프라인 실행 실패: {exc}", file=sys.stderr)
        return 1

    print("\n[SUCCESS] 파이프라인 실행 완료 - 최종 집계 리포트:")
    formatted_json = json.dumps(results, ensure_ascii=False, indent=2)
    print(formatted_json)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(formatted_json, encoding="utf-8")
        print(f"\n[INFO] 결과 파일 저장 완료: {output_path.resolve()}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
