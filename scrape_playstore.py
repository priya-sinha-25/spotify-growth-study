"""Scrape Google Play Store reviews for the Spotify app."""

import csv
from pathlib import Path

from google_play_scraper import Sort, reviews

APP_ID = "com.spotify.music"
REVIEW_COUNT = 400
OUTPUT_FILE = Path("playstore.csv")
SOURCE = "PlayStore"
LOW_STAR_RATINGS = {1, 2, 3}


def scrape_reviews(app_id: str, count: int) -> list[dict]:
    result, _ = reviews(
        app_id,
        lang="en",
        country="us",
        sort=Sort.NEWEST,
        count=count,
    )
    return result


def filter_low_star_reviews(reviews_data: list[dict]) -> list[dict]:
    return [
        review
        for review in reviews_data
        if review["score"] in LOW_STAR_RATINGS and review.get("content")
    ]


def save_reviews(reviews_data: list[dict], output_path: Path) -> None:
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["text", "source"])
        writer.writeheader()
        for review in reviews_data:
            writer.writerow({"text": review["content"], "source": SOURCE})


def main() -> None:
    print(f"Scraping {REVIEW_COUNT} reviews for {APP_ID}...")
    reviews_data = scrape_reviews(APP_ID, REVIEW_COUNT)
    low_star_reviews = filter_low_star_reviews(reviews_data)
    save_reviews(low_star_reviews, OUTPUT_FILE)
    print(f"Saved {len(low_star_reviews)} reviews (1–3 stars) to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
