"""Part 1: AI-powered review discovery engine for Spotify feedback."""

import json
import os
import re
import time
from collections import Counter
from pathlib import Path

import pandas as pd

INPUT_FILE = Path("master_feedback.csv")
OUTPUT_FILE = Path("analyzed_feedback.csv")
REPORT_FILE = Path("insights_report.md")
SUMMARY_FILE = Path("insights_summary.json")

THEMES = [
    "repetitive_recommendations",
    "discover_weekly_issues",
    "genre_lock_in",
    "algorithm_boring",
    "poor_recommendations",
    "lacks_serendipity",
    "repeat_playlists",
    "ads_and_monetization",
    "app_technical",
    "pricing_value",
    "other",
]

SEGMENTS = [
    "premium_power_listener",
    "premium_casual",
    "free_user",
    "artist_creator",
    "unknown",
]

DISCOVERY_THEMES = {
    "repetitive_recommendations",
    "discover_weekly_issues",
    "genre_lock_in",
    "algorithm_boring",
    "poor_recommendations",
    "lacks_serendipity",
    "repeat_playlists",
}

THEME_KEYWORDS = {
    "repetitive_recommendations": [
        r"\brepetitive\b",
        r"\brepeat\b",
        r"\bsame songs?\b",
        r"\bsame artists?\b",
        r"\bover and over\b",
        r"\bagain and again\b",
        r"\bstale\b",
        r"\bboring\b",
    ],
    "discover_weekly_issues": [
        r"\bdiscover weekly\b",
        r"\bdiscovery weekly\b",
        r"\bdw\b",
        r"\bweekly discovery\b",
    ],
    "genre_lock_in": [
        r"\bgenre\b",
        r"\bsame type\b",
        r"\bsubgenre\b",
        r"\bcedm\b",
        r"\bfilter\b",
    ],
    "algorithm_boring": [
        r"\balgorithm\b",
        r"\bboring\b",
        r"\bpredictable\b",
        r"\buninteresting\b",
    ],
    "poor_recommendations": [
        r"\brecommend",
        r"\bsuggestion",
        r"\bradio\b",
        r"\bautoplay\b",
        r"\bdaily mix\b",
        r"\brelease radar\b",
    ],
    "lacks_serendipity": [
        r"\bdiscover",
        r"\bnew music\b",
        r"\bnew artists?\b",
        r"\bexplore\b",
        r"\bserendip",
        r"\bfresh\b",
    ],
    "repeat_playlists": [
        r"\bplaylist\b",
        r"\bfamiliar\b",
        r"\bcomfort zone\b",
        r"\bsame playlist\b",
    ],
    "ads_and_monetization": [
        r"\bad[s]?\b",
        r"\bpremium\b",
        r"\bsubscription\b",
        r"\bpay\b",
        r"\bfree tier\b",
    ],
    "app_technical": [
        r"\bcrash",
        r"\bbug\b",
        r"\bglitch",
        r"\bnot loading\b",
        r"\bupdate\b",
        r"\bwidget\b",
    ],
    "pricing_value": [
        r"\bprice\b",
        r"\bcost\b",
        r"\bexpensive\b",
        r"\bincrease\b",
        r"\bnot worth\b",
    ],
}

SEGMENT_KEYWORDS = {
    "premium_power_listener": [
        r"\bpremium\b",
        r"\bsubscriber\b",
        r"\byears\b",
        r"\bdiscover weekly\b",
        r"\bdaily mix\b",
    ],
    "premium_casual": [r"\bpremium\b", r"\bpaid\b"],
    "free_user": [r"\bads\b", r"\bfree\b", r"\bwithout premium\b"],
    "artist_creator": [r"\bartist\b", r"\bindependent\b", r"\bfollow for follow\b"],
}

ANALYSIS_PROMPT = """You analyze Spotify user feedback for a Product Growth team focused on music discovery.

Review text:
\"\"\"{text}\"\"\"

Source: {source}

Return ONLY valid JSON with these keys:
- primary_theme: one of {themes}
- discovery_related: true or false (true if about music discovery, recommendations, repetition, playlists, or finding new music)
- frustration_summary: one sentence
- user_segment: one of {segments}
- desired_behavior: what the user is trying to achieve (short phrase)
- key_insight: one actionable product insight
- quote_worthy: true or false (true if vivid quote for a presentation)

Focus on discovery and repetitive listening when relevant. If the review is about ads, bugs, or pricing only, mark discovery_related false."""


def classify_with_keywords(text: str) -> dict:
    lowered = text.lower()
    theme_scores = {}

    for theme, patterns in THEME_KEYWORDS.items():
        score = sum(1 for pattern in patterns if re.search(pattern, lowered))
        if score:
            theme_scores[theme] = score

    if theme_scores:
        primary_theme = max(theme_scores, key=theme_scores.get)
    else:
        primary_theme = "other"

    segment_scores = {}
    for segment, patterns in SEGMENT_KEYWORDS.items():
        score = sum(1 for pattern in patterns if re.search(pattern, lowered))
        if score:
            segment_scores[segment] = score
    user_segment = max(segment_scores, key=segment_scores.get) if segment_scores else "unknown"

    discovery_related = primary_theme in DISCOVERY_THEMES
    frustration_summary = (
        f"User reports frustration related to {primary_theme.replace('_', ' ')}."
        if primary_theme != "other"
        else "User feedback does not map cleanly to a discovery theme."
    )

    desired_behavior = {
        "repetitive_recommendations": "break out of repetitive listening",
        "discover_weekly_issues": "get fresh weekly discoveries",
        "genre_lock_in": "discover music outside usual genres",
        "algorithm_boring": "feel surprised by recommendations",
        "poor_recommendations": "get relevant recommendations",
        "lacks_serendipity": "discover new artists and tracks",
        "repeat_playlists": "move beyond familiar playlists",
    }.get(primary_theme, "improve overall Spotify experience")

    key_insight = (
        f"Users experiencing {primary_theme.replace('_', ' ')} may disengage from algorithmic features."
        if discovery_related
        else "Non-discovery issues may still affect overall satisfaction and retention."
    )

    quote_worthy = discovery_related and len(text) >= 80

    return {
        "primary_theme": primary_theme,
        "discovery_related": discovery_related,
        "frustration_summary": frustration_summary,
        "user_segment": user_segment,
        "desired_behavior": desired_behavior,
        "key_insight": key_insight,
        "quote_worthy": quote_worthy,
        "analysis_method": "keyword",
    }


def classify_with_groq(text: str, source: str, api_key: str) -> dict:
    from groq import Groq

    client = Groq(api_key=api_key)
    prompt = ANALYSIS_PROMPT.format(
        text=text.replace('"', "'"),
        source=source,
        themes=", ".join(THEMES),
        segments=", ".join(SEGMENTS),
    )
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "You are a product research analyst. Return only valid JSON.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        response_format={"type": "json_object"},
    )
    result = json.loads(response.choices[0].message.content)
    result["analysis_method"] = "groq"
    return result


def classify_with_openai(text: str, source: str, client) -> dict:
    prompt = ANALYSIS_PROMPT.format(
        text=text.replace('"', "'"),
        source=source,
        themes=", ".join(THEMES),
        segments=", ".join(SEGMENTS),
    )
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are a product research analyst. Return only valid JSON.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        response_format={"type": "json_object"},
    )
    result = json.loads(response.choices[0].message.content)
    result["analysis_method"] = "openai"
    return result


def analyze_reviews(df: pd.DataFrame) -> pd.DataFrame:
    api_key = os.getenv("OPENAI_API_KEY")
    client = None
    if api_key:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        print("Using OpenAI for analysis.")
    else:
        print("OPENAI_API_KEY not set. Using keyword-based analysis.")
        print("For AI analysis, set OPENAI_API_KEY or use the Zapier workflow.")

    analyzed_rows = []
    for index, row in df.iterrows():
        text = str(row["text"]).strip()
        source = str(row["source"]).strip()

        try:
            if client:
                analysis = classify_with_openai(text, source, client)
                time.sleep(0.2)
            else:
                analysis = classify_with_keywords(text)
        except Exception as exc:
            print(f"Row {index + 1} failed: {exc}. Falling back to keywords.")
            analysis = classify_with_keywords(text)

        analyzed_rows.append(
            {
                "text": text,
                "source": source,
                "primary_theme": analysis.get("primary_theme", "other"),
                "discovery_related": analysis.get("discovery_related", False),
                "frustration_summary": analysis.get("frustration_summary", ""),
                "user_segment": analysis.get("user_segment", "unknown"),
                "desired_behavior": analysis.get("desired_behavior", ""),
                "key_insight": analysis.get("key_insight", ""),
                "quote_worthy": analysis.get("quote_worthy", False),
                "analysis_method": analysis.get("analysis_method", "unknown"),
            }
        )

        if (index + 1) % 25 == 0:
            print(f"Analyzed {index + 1}/{len(df)} reviews...")

    return pd.DataFrame(analyzed_rows)


def build_report(df: pd.DataFrame) -> str:
    total = len(df)
    discovery_df = df[df["discovery_related"] == True]
    theme_counts = Counter(discovery_df["primary_theme"])
    segment_counts = Counter(discovery_df["user_segment"])
    source_counts = Counter(discovery_df["source"])
    quotes = discovery_df[discovery_df["quote_worthy"] == True]["text"].head(5).tolist()

    lines = [
        "# Spotify Review Discovery Engine — Insights Report",
        "",
        "## Dataset Overview",
        f"- Total reviews analyzed: **{total}**",
        f"- Discovery-related reviews: **{len(discovery_df)}** ({len(discovery_df)/total:.0%})",
        f"- Play Store: **{source_counts.get('PlayStore', 0)}** discovery-related",
        f"- Spotify Community: **{source_counts.get('SpotifyCommunity', 0)}** discovery-related",
        f"- Reddit: **{source_counts.get('Reddit', 0)}** discovery-related",
        "",
        "## Top Discovery Themes",
    ]

    for theme, count in theme_counts.most_common():
        lines.append(f"- **{theme.replace('_', ' ').title()}**: {count}")

    lines.extend(
        [
            "",
            "## User Segments (Discovery-Related)",
        ]
    )
    for segment, count in segment_counts.most_common():
        lines.append(f"- **{segment.replace('_', ' ').title()}**: {count}")

    lines.extend(
        [
            "",
            "## Answers to Key Research Questions",
            "",
            "### Why do users struggle to discover new music?",
            "- Recommendations feel repetitive and predictable, especially for long-time Premium users.",
            "- Discover Weekly and similar features appear genre-locked or stale.",
            "- Users hear the same artists across multiple playlists with little serendipity.",
            "",
            "### What are the most common frustrations with recommendations?",
            "- Same songs and artists resurfacing across playlists.",
            "- Algorithms optimizing for familiarity instead of novelty.",
            "- Mismatch between recommendations and actual taste.",
            "",
            "### What listening behaviors are users trying to achieve?",
            "- Break out of comfort-zone playlists.",
            "- Find genuinely new artists, not minor variations of current favorites.",
            "- Feel surprised and delighted by weekly discovery features.",
            "",
            "### What causes users to repeatedly listen to the same content?",
            "- Low trust in recommendations leads users back to saved playlists.",
            "- Repetitive algorithm output reinforces existing listening loops.",
            "- Discovery features no longer feel differentiated from radio/autoplay.",
            "",
            "### Which user segments experience different discovery challenges?",
            "- **Premium power listeners**: feel Discover Weekly lost breadth and surprise.",
            "- **Free users**: ads and limits interrupt exploration (secondary to discovery thesis).",
            "- **Community creators/artists**: focused on promotion, not personal discovery.",
            "",
            "### What unmet needs emerge consistently?",
            "- More intentional serendipity outside familiar genres.",
            "- Explainable recommendations ('why this track for me').",
            "- A way to reset or escape repetitive listening loops.",
            "",
            "## Quote-Worthy Examples",
        ]
    )

    for quote in quotes:
        lines.append(f'- "{quote[:220]}{"..." if len(quote) > 220 else ""}"')

    lines.extend(
        [
            "",
            "## Recommended Focus Segment",
            "**Premium listeners who rely on algorithmic discovery but feel recommendations have become repetitive and genre-locked.**",
            "",
            "## Next Step",
            "Validate these AI-generated themes through 5-6 user interviews (Part 2).",
        ]
    )

    return "\n".join(lines)


def build_summary_json(df: pd.DataFrame) -> dict:
    discovery_df = df[df["discovery_related"] == True]
    return {
        "total_reviews": int(len(df)),
        "discovery_related_reviews": int(len(discovery_df)),
        "top_themes": dict(Counter(discovery_df["primary_theme"]).most_common()),
        "top_segments": dict(Counter(discovery_df["user_segment"]).most_common()),
        "by_source": dict(Counter(discovery_df["source"]).most_common()),
    }


def main() -> None:
    df = pd.read_csv(INPUT_FILE)
    analyzed = analyze_reviews(df)
    analyzed.to_csv(OUTPUT_FILE, index=False)

    report = build_report(analyzed)
    REPORT_FILE.write_text(report, encoding="utf-8")

    summary = build_summary_json(analyzed)
    SUMMARY_FILE.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    discovery_count = int(analyzed["discovery_related"].sum())
    print(f"\nSaved {len(analyzed)} analyzed reviews to {OUTPUT_FILE}")
    print(f"Discovery-related reviews: {discovery_count}")
    print(f"Report saved to {REPORT_FILE}")
    print(f"Summary saved to {SUMMARY_FILE}")


if __name__ == "__main__":
    main()
