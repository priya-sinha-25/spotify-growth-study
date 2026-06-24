"""Merge Play Store, Spotify Community, and Reddit feedback into one dataset."""

from pathlib import Path

import pandas as pd

PLAYSTORE_FILE = Path("playstore.csv")
COMMUNITY_FILE = Path("community.csv")
REDDIT_FILE = Path("reddit.csv")
OUTPUT_FILE = Path("master_feedback.csv")
MIN_TEXT_LENGTH = 20


def load_feedback() -> pd.DataFrame:
    frames = [
        pd.read_csv(PLAYSTORE_FILE),
        pd.read_csv(COMMUNITY_FILE),
    ]

    if REDDIT_FILE.exists():
        frames.append(pd.read_csv(REDDIT_FILE))
    else:
        print(f"Warning: {REDDIT_FILE} not found. Run scrape_reddit.py first.")

    combined = pd.concat(frames, ignore_index=True)
    combined = combined.drop_duplicates(subset=["text"], keep="first")
    return combined


def filter_short_text(df: pd.DataFrame, min_length: int) -> pd.DataFrame:
    text = df["text"].fillna("").astype(str).str.strip()
    return df[text.str.len() >= min_length].copy()


def print_summary(df: pd.DataFrame) -> None:
    counts = df["source"].value_counts()
    print(f"PlayStore: {counts.get('PlayStore', 0)}")
    print(f"SpotifyCommunity: {counts.get('SpotifyCommunity', 0)}")
    print(f"Reddit: {counts.get('Reddit', 0)}")
    print(f"Total: {len(df)}")


def main() -> None:
    df = load_feedback()
    df = filter_short_text(df, MIN_TEXT_LENGTH)
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"Saved {len(df)} rows to {OUTPUT_FILE}\n")
    print("Summary by source:")
    print_summary(df)


if __name__ == "__main__":
    main()
