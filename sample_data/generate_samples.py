"""Generate CSV fixtures for the Streamlit manual-validation scenarios."""

from pathlib import Path

import pandas as pd


OUTPUT_DIR = Path(__file__).resolve().parent
COLUMNS = ["id", "final_score", "captured_at", "tags"]

ROWS = [
    (1, 8.7, "2026-01-05 09:30:00", '["자연풍경", "골든아워"]'),
    (2, 6.4, "2026-01-12", '["건축도시", "아이레벨"]'),
    (3, 7.8, "2026-02-02 16:10:00", '["거리스냅", "흐린날 확산광"]'),
    (4, 9.1, "2026-02-14 17:45:00", '["골든아워", "로우 앵글"]'),
    (5, 5.9, "2026-02-21", '["자연풍경", "단일피사체 집중"]'),
    (6, 8.2, "2026-03-03 11:20:00", '["건축도시", "흐린날 확산광"]'),
    (7, 6.8, "2026-03-09", '["거리스냅", "아이레벨"]'),
    (8, 9.4, "2026-03-18 18:05:00", '["골든아워", "단일피사체 집중"]'),
    (9, 7.1, "2026-04-01", '["자연풍경", "로우 앵글"]'),
    (10, 8.9, "2026-04-11 13:15:00", '["건축도시", "골든아워"]'),
    (11, 6.2, "2026-04-19", '["거리스냅", "흐린날 확산광"]'),
    (12, 7.6, "2026-04-25 07:40:00", '["로우 앵글", "아이레벨"]'),
    (13, 9.7, "", '["단일피사체 집중", "자연풍경"]'),
    (14, 5.5, "", '["거리스냅", "골든아워"]'),
]


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    photos = pd.DataFrame(ROWS, columns=COLUMNS)

    photos.to_csv(OUTPUT_DIR / "sample_photos.csv", encoding="utf-8", index=False)
    photos.to_csv(
        OUTPUT_DIR / "sample_photos_cp949.csv", encoding="cp949", index=False
    )
    photos.drop(columns=["final_score"]).head(4).to_csv(
        OUTPUT_DIR / "sample_photos_broken.csv", encoding="utf-8", index=False
    )


if __name__ == "__main__":
    main()
