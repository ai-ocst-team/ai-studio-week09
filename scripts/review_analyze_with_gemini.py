"""Reproduce VLM integration observations without external API calls."""
import contextlib
import io
import logging
import os
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from PIL import Image
from analyze_with_gemini import llm_client
from analyze_with_gemini.analyze_with_gemini import analyze_with_gemini
from pipeline import run_pipeline

photo = {"upload_bytes": b"synthetic", "sha256": "a" * 64, "safe_exif": {}}
output = io.StringIO()
handler = logging.StreamHandler(output)
logging.getLogger().addHandler(handler)
try:
    with patch.dict(os.environ, {"USE_MOCK": "false"}):
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            result = analyze_with_gemini(photo, "dummy", "")
    if result["final_score"] != 8.0:
        raise RuntimeError("Mock observation changed")
    if "[MOCK]" in output.getvalue():
        raise RuntimeError("Mock marker observation changed")
finally:
    logging.getLogger().removeHandler(handler)
print("R1: USE_MOCK=false still returns fixed Mock score 8.0; no [MOCK] output captured.")

with tempfile.TemporaryDirectory(prefix="analyze-review-") as folder:
    for name in ("01.jpg", "02.jpg"):
        Image.new("RGB", (8, 8)).save(Path(folder, name))
    real_generate = llm_client.generate_analysis
    calls = []
    def fail_first(**kwargs):
        calls.append(1)
        if len(calls) == 1:
            raise TimeoutError("synthetic timeout")
        return real_generate(**kwargs)
    with patch.dict(os.environ):
        with patch.object(llm_client, "generate_analysis", fail_first):
            try:
                run_pipeline(folder)
            except RuntimeError as error:
                if str(error) != "VLM 통신 실패" or not isinstance(error.__cause__, TimeoutError):
                    raise
            else:
                raise RuntimeError("Pipeline failure observation changed")
    if len(calls) != 1:
        raise RuntimeError("Pipeline continuation observation changed")
print("R2: first-image timeout escapes as RuntimeError; second image not analyzed (client calls=1).")

import importlib
module = importlib.import_module("analyze_with_gemini.analyze_with_gemini")
validator = module.validate_vlm_response.__globals__
if {key: set(value) for key, value in module._TAG_VOCABULARY.items()} != validator["_TAG_VOCABULARY"]:
    raise RuntimeError("Tag vocabularies already differ")
if set(module._FOCUS_STATUSES) != validator["_FOCUS_STATUSES"]:
    raise RuntimeError("Focus statuses already differ")
print("C1: duplicated tag/focus rules currently match; no current value mismatch found.")
