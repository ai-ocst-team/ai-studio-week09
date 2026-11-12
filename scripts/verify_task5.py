"""Compare aggregation behavior against the reviewed main commit."""
import random
import runpy
import subprocess
import warnings

import pandas as pd

BASELINE = "b2a7d8ba5bbaef68c4951717912359e634b32274"
MODULE = "aggregate_photo_insights/photo_analytics.py"
source = subprocess.check_output(["git", "show", f"{BASELINE}:{MODULE}"], text=True)
namespace = {}
exec(compile(source, f"{BASELINE}:{MODULE}", "exec"), namespace)
before = namespace["aggregate_photo_insights"]
after = runpy.run_path(MODULE)["aggregate_photo_insights"]
rng = random.Random(42)
compared_cases = 0
with warnings.catch_warnings():
    warnings.simplefilter("ignore", UserWarning)
    for case in range(200):
        size = rng.randrange(40)
        frame = pd.DataFrame({
            "id": range(size),
            "final_score": [rng.choice([None, -1, 0, 1.234, 5, 9.999, 12]) for _ in range(size)],
            "captured_at": [rng.choice(["2026-01-01", "2026-02-01", "invalid"]) for _ in range(size)],
            "tags": [rng.sample([" a ", "b", "c", "d", "e", "f", "g", ""], rng.randrange(5)) for _ in range(size)],
        })
        original = frame.copy(deep=True)
        if before(frame) != after(frame):
            raise AssertionError(f"Return mismatch at case {case}")
        compared_cases += 1
        pd.testing.assert_frame_equal(frame, original)
for frame in (None, pd.DataFrame()):
    if before(frame) != after(frame):
        raise AssertionError("Empty-input return mismatch")
for function in (before, after):
    try:
        function(pd.DataFrame({"id": [1]}))
    except ValueError as error:
        if str(error) != "데이터프레임 필수 열 누락: final_score, captured_at, tags":
            raise AssertionError(f"Unexpected missing-column error: {error}")
    else:
        raise AssertionError("Missing-column input did not raise ValueError")
print(f"Baseline: {BASELINE}")
print(f"Seed 42: {compared_cases} complete return dictionaries equal; input frames unchanged.")
print("None, empty input and missing-column exception behavior equal.")
