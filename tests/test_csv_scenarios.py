import json
from collections import Counter
from io import BytesIO
from pathlib import Path

import pandas as pd
import pytest


SAMPLE_DIR = Path(__file__).resolve().parents[1] / "sample_data"
SAMPLE_CSV = SAMPLE_DIR / "sample_photos.csv"
CP949_CSV = SAMPLE_DIR / "sample_photos_cp949.csv"
BROKEN_CSV = SAMPLE_DIR / "sample_photos_broken.csv"
EXPECTED_COLUMNS = ["id", "final_score", "captured_at", "tags"]


def test_scenario_csv_files_exist():
    assert SAMPLE_CSV.is_file()
    assert CP949_CSV.is_file()
    assert BROKEN_CSV.is_file()


def test_utf8_csv_has_expected_schema_and_values():
    photos = pd.read_csv(SAMPLE_CSV, encoding="utf-8", keep_default_na=False)

    assert photos.columns.tolist() == EXPECTED_COLUMNS
    assert 12 <= len(photos) <= 15
    assert photos["final_score"].between(0.0, 10.0).all()
    assert photos["captured_at"].eq("").sum() in (1, 2)
    months = {
        value[:7]
        for value in photos["captured_at"]
        if value
    }
    assert len(months) >= 3


def test_cp949_csv_fails_utf8_and_restores_korean_tags():
    utf8_photos = pd.read_csv(SAMPLE_CSV, encoding="utf-8", keep_default_na=False)
    buffer = BytesIO(CP949_CSV.read_bytes())

    with pytest.raises(UnicodeDecodeError):
        pd.read_csv(buffer, encoding="utf-8")

    buffer.seek(0)
    cp949_photos = pd.read_csv(buffer, encoding="cp949", keep_default_na=False)

    assert len(cp949_photos) == len(utf8_photos)
    assert cp949_photos["tags"].tolist() == utf8_photos["tags"].tolist()
    assert "자연풍경" in json.loads(cp949_photos.loc[0, "tags"])


def test_broken_csv_omits_final_score():
    broken = pd.read_csv(BROKEN_CSV, encoding="utf-8")

    assert len(broken) in range(3, 6)
    assert broken.columns.tolist() == ["id", "captured_at", "tags"]
    assert "final_score" not in broken.columns


def test_korean_tags_include_repeated_values():
    photos = pd.read_csv(SAMPLE_CSV, encoding="utf-8")
    tag_counts = Counter(
        tag
        for value in photos["tags"]
        for tag in json.loads(value)
    )

    assert sum(count >= 2 for count in tag_counts.values()) >= 2
