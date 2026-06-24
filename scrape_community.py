"""Scrape post titles from the Spotify Community Music Discovery board."""

import csv
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from requests.exceptions import RequestException

BOARD_URL = "https://community.spotify.com/t5/Discovery-Promo/bd-p/discovery_and_promo"
POST_LIMIT = 50
OUTPUT_FILE = Path("community.csv")
SOURCE = "SpotifyCommunity"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

BLOCKED_MARKERS = (
    "request blocked",
    "could not be satisfied",
    "access denied",
    "node was not found",
    "enable javascript",
)


def page_url(page_number: int) -> str:
    if page_number <= 1:
        return BOARD_URL
    return f"{BOARD_URL}/page/{page_number}"


def is_blocked_page(html: str, status_code: int) -> bool:
    if status_code >= 400:
        return True

    lowered = html.lower()
    if any(marker in lowered for marker in BLOCKED_MARKERS):
        return True

    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.string.strip().lower() if soup.title and soup.title.string else ""
    return "node was not found" in title


def fetch_page(url: str) -> str | None:
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
    except RequestException as exc:
        print(f"Request failed for {url}: {exc}")
        return None

    if is_blocked_page(response.text, response.status_code):
        print(
            f"Skipping protected or unavailable page "
            f"(status {response.status_code}): {url}"
        )
        return None

    return response.text


def extract_titles(html: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    titles: list[str] = []
    seen: set[str] = set()

    for link in soup.select("article h2 a"):
        title = link.get_text(strip=True)
        if not title or title in seen:
            continue
        seen.add(title)
        titles.append(title)

    return titles


def scrape_post_titles(limit: int) -> list[str]:
    collected: list[str] = []
    seen: set[str] = set()
    page_number = 1

    while len(collected) < limit:
        html = fetch_page(page_url(page_number))
        if html is None:
            break

        page_titles = extract_titles(html)
        if not page_titles:
            print(f"No post titles found on page {page_number}.")
            break

        for title in page_titles:
            if title in seen:
                continue
            seen.add(title)
            collected.append(title)
            if len(collected) >= limit:
                break

        page_number += 1

    return collected[:limit]


def save_titles(titles: list[str], output_path: Path) -> None:
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["text", "source"])
        writer.writeheader()
        for title in titles:
            writer.writerow({"text": title, "source": SOURCE})


def main() -> None:
    print(f"Scraping up to {POST_LIMIT} posts from {BOARD_URL}...")
    titles = scrape_post_titles(POST_LIMIT)
    save_titles(titles, OUTPUT_FILE)
    print(f"Collected {len(titles)} post titles.")
    print(f"Saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
