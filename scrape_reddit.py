"""Scrape r/Spotify posts matching discovery-related keywords."""

import csv
import os
import time
from pathlib import Path

import requests

# PRAW credentials — set these or use environment variables
client_id = os.getenv("REDDIT_CLIENT_ID", "YOUR_CLIENT_ID")
client_secret = os.getenv("REDDIT_CLIENT_SECRET", "YOUR_CLIENT_SECRET")
user_agent = os.getenv("REDDIT_USER_AGENT", "SpotifyResearch/1.0")

SUBREDDIT = "Spotify"
KEYWORDS = [
    "algorithm boring",
    "repetitive",
    "discovery weekly",
    "recommendation",
]
POST_LIMIT = 100
OUTPUT_FILE = Path("reddit.csv")
SOURCE = "Reddit"

PUBLIC_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
}
PULLPUSH_URL = "https://api.pullpush.io/reddit/search/submission/"


def credentials_configured() -> bool:
    return (
        client_id not in ("", "YOUR_CLIENT_ID")
        and client_secret not in ("", "YOUR_CLIENT_SECRET")
    )


def combine_post_text(title: str, body: str) -> str:
    title = title.strip()
    body = (body or "").strip()
    if title and body:
        return f"{title} {body}"
    return title or body


def search_with_praw() -> list[dict]:
    import praw

    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent,
    )

    seen_ids: set[str] = set()
    posts: list[dict] = []
    subreddit = reddit.subreddit(SUBREDDIT)

    for keyword in KEYWORDS:
        for submission in subreddit.search(
            keyword,
            sort="top",
            time_filter="all",
            limit=POST_LIMIT,
        ):
            if submission.id in seen_ids:
                continue
            seen_ids.add(submission.id)
            posts.append(
                {
                    "id": submission.id,
                    "score": submission.score,
                    "text": combine_post_text(submission.title, submission.selftext),
                }
            )

    posts.sort(key=lambda post: post["score"], reverse=True)
    return posts[:POST_LIMIT]


def search_with_public_api() -> list[dict]:
    """Fallback using Reddit's public JSON search when PRAW credentials are missing."""
    seen_ids: set[str] = set()
    posts: list[dict] = []

    for keyword in KEYWORDS:
        params = {
            "q": keyword,
            "restrict_sr": "on",
            "sort": "top",
            "t": "all",
            "limit": 100,
        }
        after = None

        while len(posts) < POST_LIMIT:
            if after:
                params["after"] = after

            response = requests.get(
                f"https://www.reddit.com/r/{SUBREDDIT}/search.json",
                headers=PUBLIC_HEADERS,
                params=params,
                timeout=30,
            )
            if response.status_code != 200:
                print(f"Reddit API returned {response.status_code} for '{keyword}'.")
                break

            payload = response.json()
            children = payload.get("data", {}).get("children", [])
            if not children:
                break

            for child in children:
                data = child.get("data", {})
                post_id = data.get("id")
                if not post_id or post_id in seen_ids:
                    continue
                seen_ids.add(post_id)
                posts.append(
                    {
                        "id": post_id,
                        "score": data.get("score", 0),
                        "text": combine_post_text(
                            data.get("title", ""),
                            data.get("selftext", ""),
                        ),
                    }
                )
                if len(posts) >= POST_LIMIT:
                    break

            after = payload.get("data", {}).get("after")
            if not after or len(posts) >= POST_LIMIT:
                break

            time.sleep(1)

        time.sleep(1)

    posts.sort(key=lambda post: post["score"], reverse=True)
    return posts[:POST_LIMIT]


def search_with_pullpush() -> list[dict]:
    """Archive fallback when Reddit blocks direct API access."""
    seen_ids: set[str] = set()
    posts: list[dict] = []

    for keyword in KEYWORDS:
        try:
            response = requests.get(
                PULLPUSH_URL,
                params={
                    "subreddit": SUBREDDIT,
                    "q": keyword,
                    "size": 100,
                    "sort": "desc",
                    "sort_type": "score",
                },
                timeout=30,
            )
        except requests.RequestException as exc:
            print(f"PullPush request failed for '{keyword}': {exc}")
            continue

        if response.status_code != 200:
            print(f"PullPush returned {response.status_code} for '{keyword}'.")
            continue

        for item in response.json().get("data", []):
            post_id = item.get("id")
            if not post_id or post_id in seen_ids:
                continue
            seen_ids.add(post_id)
            posts.append(
                {
                    "id": post_id,
                    "score": item.get("score", 0),
                    "text": combine_post_text(
                        item.get("title", ""),
                        item.get("selftext", ""),
                    ),
                }
            )

        time.sleep(1)

    posts.sort(key=lambda post: post["score"], reverse=True)
    return posts[:POST_LIMIT]


def scrape_posts() -> list[dict]:
    if credentials_configured():
        print("Scraping with PRAW...")
        return search_with_praw()

    print("PRAW credentials not set. Trying Reddit public JSON API...")
    posts = search_with_public_api()
    if posts:
        return posts

    print("Reddit API blocked. Using PullPush archive fallback...")
    return search_with_pullpush()


def save_posts(posts: list[dict], output_path: Path) -> None:
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["text", "source"])
        writer.writeheader()
        for post in posts:
            if post["text"]:
                writer.writerow({"text": post["text"], "source": SOURCE})


def main() -> None:
    print(f"Searching r/{SUBREDDIT} for up to {POST_LIMIT} posts...")
    posts = scrape_posts()
    save_posts(posts, OUTPUT_FILE)
    print(f"Collected {len(posts)} Reddit posts.")
    print(f"Saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
