"""Compare committed feature behavior with current client, without network access."""
from contextlib import contextmanager
import importlib.util
import inspect
import logging
import os
from pathlib import Path
import subprocess
import tempfile


BASELINE = "8b347476d41efcea4c9fa6805dab38fcf9f7405b"
ROOT = Path(__file__).resolve().parents[3]
CLIENT = "analyze_with_gemini/llm_client.py"


def load_module(name: str, path: Path):
    """Load an explicitly selected local client version for comparison."""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@contextmanager
def mode(value):
    """Restore the caller's USE_MOCK value even if comparison fails."""
    original = os.environ.get("USE_MOCK")
    try:
        if value is None:
            os.environ.pop("USE_MOCK", None)
        else:
            os.environ["USE_MOCK"] = value
        yield
    finally:
        if original is None:
            os.environ.pop("USE_MOCK", None)
        else:
            os.environ["USE_MOCK"] = original


def outcome(module, args):
    """Record return bytes/text, exception class/message, and safe log messages."""
    logs = []

    class Capture(logging.Handler):
        def emit(self, record):
            logs.append((record.levelname, record.getMessage()))

    handler = Capture()
    logger = module.logger
    old_level = logger.level
    old_propagate = logger.propagate
    logger.setLevel(logging.INFO)
    logger.propagate = False
    logger.addHandler(handler)
    try:
        try:
            value = module.generate_analysis(*args)
            result = ("return", type(value).__name__, value)
        except (TypeError, ValueError, NotImplementedError) as error:
            result = ("raise", type(error).__name__, str(error))
        return result, logs
    finally:
        logger.removeHandler(handler)
        logger.setLevel(old_level)
        logger.propagate = old_propagate


def main() -> None:
    """Check a fixed cross-product of modes and valid/invalid arguments."""
    before_source = subprocess.check_output(["git", "show", f"{BASELINE}:{CLIENT}"], cwd=ROOT)
    # New dedicated directory: no existing user files are removed.
    with tempfile.TemporaryDirectory(prefix="task3_parity_") as temp:
        original = Path(temp) / "llm_before.py"
        original.write_bytes(before_source)
        before = load_module("task3_before", original)
        after = load_module("task3_after", ROOT / CLIENT)
        if inspect.signature(before.generate_analysis) != inspect.signature(after.generate_analysis):
            raise RuntimeError("Public signature changed")
        modes = [None, "true", " TRUE ", "1", "yes", "on", "false", " FALSE ", "0", "no", "off", "", "flase", "2"]
        requests = [
            (b"dummy", "dummy", "dummy"), (b"dummy", " model ", " prompt "),
            ("wrong", "dummy", "dummy"), (None, "dummy", "dummy"),
            (b"", "dummy", "dummy"), (b"dummy", None, "dummy"),
            (b"dummy", "", "dummy"), (b"dummy", "  ", "dummy"),
            (b"dummy", "dummy", None), (b"dummy", "dummy", ""),
            (b"dummy", "dummy", "  "), (None, None, None),
        ]
        comparisons = 0
        for flag in modes:
            with mode(flag):
                for args in requests:
                    if outcome(before, args) != outcome(after, args):
                        raise RuntimeError(f"Behavior differs at comparison {comparisons + 1}")
                    comparisons += 1
    print(f"baseline={BASELINE}")
    print(f"PASS: {comparisons} behavior comparisons; identical signature, JSON text, exceptions and logs")


if __name__ == "__main__":
    main()
