"""Part 4: Loop Break — diagnostic engine and recommendation logic."""

import json
import re
from urllib.parse import quote_plus

LOOP_TYPES = [
    "library_leak",
    "genre_lock",
    "context_pollution",
    "comfort_spiral",
]

LOOP_LABELS = {
    "library_leak": "Library Leak",
    "genre_lock": "Genre Lock",
    "context_pollution": "Context Pollution",
    "comfort_spiral": "Comfort Spiral",
}

LOOP_DESCRIPTIONS = {
    "library_leak": (
        "Discover Weekly is pulling from songs you already know — saved, liked, or heard recently — "
        "so the playlist feels like a library replay instead of discovery."
    ),
    "genre_lock": (
        "Recommendations are stuck in one genre or mood week after week. "
        "The algorithm is playing it safe inside your usual lane."
    ),
    "context_pollution": (
        "Listening in one context (workout, sleep, focus) is skewing your Made For You picks. "
        "Discover Weekly inherited the wrong session signal."
    ),
    "comfort_spiral": (
        "You are retreating to the same saved playlists when DW disappoints. "
        "Familiarity is winning over serendipity."
    ),
}

INTERVENTIONS = {
    "library_leak": "Hard exclude library overlap — prioritize unheard artists with adjacent taste fit.",
    "genre_lock": "Cross-genre bridge tracks — same emotional tone, different sonic lane.",
    "context_pollution": "Session-scoped reset — ignore off-context listening for this week's picks.",
    "comfort_spiral": "High-serendipity mode — deliberate picks outside your comfort spiral.",
}

CLASSIFY_PROMPT = """You are Loop Break, an in-product Spotify discovery diagnostic (fellowship prototype).

A user opened Discover Weekly but it felt stale. Classify their loop type using this taxonomy from 271 user reviews:

1. library_leak — saved/heard/liked songs appearing in DW; "already in my library"
2. genre_lock — same genre/mood weeks in a row; boring/predictable; echo chamber
3. context_pollution — workout/sleep/focus listening skewing recommendations
4. comfort_spiral — replaying same playlists; retreating to saved music when DW fails

User frustration:
\"\"\"{frustration}\"\"\"

Return JSON only:
{{
  "loop_type": "library_leak|genre_lock|context_pollution|comfort_spiral",
  "confidence": "high|medium|low",
  "diagnosis_summary": "2 sentences in second person (you...) explaining what loop they are in",
  "intervention_preview": "1 sentence on what Loop Break will do differently than generic recs"
}}"""

RECOMMEND_PROMPT = """You are Loop Break inside Spotify — a post-Discover-Weekly reset feature.

Loop type: {loop_label}
Intervention: {intervention}
User frustration: \"\"\"{frustration}\"\"\"
Current mood: {mood}
Openness to novelty: {openness}

Survey-backed rules:
- Return EXACTLY 3 real tracks (artist + song title)
- Each track needs why_fit (why it matches their taste) and novelty_rationale (why it differs from a stale DW)
- Prioritize artists they likely have NOT heard; do not suggest obvious mega-hits they already know
- Tone: warm, concise, Spotify-native (not robotic)

Return JSON only:
{{
  "intervention_headline": "short action title e.g. Cross-genre bridge reset",
  "loop_break_message": "1-2 sentences setting up the 3 picks",
  "tracks": [
    {{"artist": "", "song": "", "why_fit": "", "novelty_rationale": ""}},
    {{"artist": "", "song": "", "why_fit": "", "novelty_rationale": ""}},
    {{"artist": "", "song": "", "why_fit": "", "novelty_rationale": ""}}
  ]
}}"""

KEYWORD_PATTERNS = {
    "library_leak": [
        r"\blibrary\b",
        r"\bsaved\b",
        r"\balready heard\b",
        r"\balready know\b",
        r"\bliked\b",
        r"\bheard before\b",
        r"\bin my playlist\b",
    ],
    "genre_lock": [
        r"\bgenre\b",
        r"\bsame mood\b",
        r"\bstuck\b",
        r"\becho chamber\b",
        r"\bpredictable\b",
        r"\bboring\b",
        r"\bsame artists?\b",
        r"\brepetitive\b",
    ],
    "context_pollution": [
        r"\bworkout\b",
        r"\bgym\b",
        r"\bsleep\b",
        r"\bfocus\b",
        r"\bwork\b",
        r"\bcommute\b",
        r"\bstudying\b",
    ],
    "comfort_spiral": [
        r"\bcomfort\b",
        r"\bsame playlist\b",
        r"\breplay\b",
        r"\boverplaying\b",
        r"\bsaved playlist\b",
        r"\bfamiliar\b",
        r"\bgo back to\b",
    ],
}

FALLBACK_TRACKS = {
    "library_leak": [
        {
            "artist": "Mdou Moctar",
            "song": "Afrique Victime",
            "why_fit": "Psychedelic rock energy that can sit next to indie playlists without feeling recycled.",
            "novelty_rationale": "Unlikely to be in your saved library — built for a hard novelty reset.",
        },
        {
            "artist": "Yaeji",
            "song": "Raingurl",
            "why_fit": "Hook-forward and moody — bridges electronic and left-field pop.",
            "novelty_rationale": "A left-field pick DW rarely surfaces when it over-indexes on safe favorites.",
        },
        {
            "artist": "Black Country, New Road",
            "song": "Sunglasses",
            "why_fit": "Art-rock with emotional weight for listeners who want substance, not filler.",
            "novelty_rationale": "Deliberately outside algorithmic comfort picks.",
        },
    ],
    "genre_lock": [
        {
            "artist": "Khruangbin",
            "song": "Time (You and I)",
            "why_fit": "Funk-groove warmth that translates across genres without locking you in one lane.",
            "novelty_rationale": "Cross-genre bridge — same vibe, different sonic neighborhood.",
        },
        {
            "artist": "Rosalía",
            "song": "DESPECHÁ",
            "why_fit": "High-energy pivot if you have been stuck in one mood for weeks.",
            "novelty_rationale": "Breaks genre lock while keeping emotional momentum.",
        },
        {
            "artist": "Fleet Foxes",
            "song": "Can I Believe You",
            "why_fit": "Melodic and expansive for indie-leaning listeners seeking a lateral move.",
            "novelty_rationale": "Adjacent taste, not the same subgenre DW keeps serving.",
        },
    ],
    "context_pollution": [
        {
            "artist": "Nils Frahm",
            "song": "Says",
            "why_fit": "Calm build for resetting away from high-BPM workout skew.",
            "novelty_rationale": "Session reset — ignores gym-mode signals for this week's discovery.",
        },
        {
            "artist": "Mild High Club",
            "song": "Homage",
            "why_fit": "Laid-back groove that works for focus without sleep-playlist baggage.",
            "novelty_rationale": "Context-scoped pick — not trained on your last workout block.",
        },
        {
            "artist": "Caribou",
            "song": "Can't Do Without You",
            "why_fit": "Uplifting but not aggressive — good middle ground after context pollution.",
            "novelty_rationale": "Different session signal than your polluted DW week.",
        },
    ],
    "comfort_spiral": [
        {
            "artist": "Big Thief",
            "song": "Simulation Swarm",
            "why_fit": "Emotionally direct indie for listeners stuck replaying 2019 comfort picks.",
            "novelty_rationale": "High-serendipity — outside your saved playlist spiral.",
        },
        {
            "artist": "JPEGMAFIA",
            "song": "HAZARD DUTY PAY!",
            "why_fit": "Bold energy if you need a jolt out of repetitive listening.",
            "novelty_rationale": "Comfort-zone breaker with clear novelty rationale.",
        },
        {
            "artist": "Sampa the Great",
            "song": "Energy",
            "why_fit": "Confident, fresh hip-hop for resetting algorithmic trust.",
            "novelty_rationale": "Picked to feel nothing like last week's DW rerun.",
        },
    ],
}


def spotify_search_url(artist: str, song: str) -> str:
    query = quote_plus(f"{artist} {song}")
    return f"https://open.spotify.com/search/{query}"


def _score_keywords(text: str) -> str:
    lowered = text.lower()
    scores = {}
    for loop_type, patterns in KEYWORD_PATTERNS.items():
        score = sum(1 for pattern in patterns if re.search(pattern, lowered))
        if score:
            scores[loop_type] = score
    if not scores:
        return "genre_lock"
    return max(scores, key=scores.get)


def classify_loop_keyword(frustration: str) -> dict:
    loop_type = _score_keywords(frustration)
    return {
        "loop_type": loop_type,
        "confidence": "medium",
        "diagnosis_summary": LOOP_DESCRIPTIONS[loop_type],
        "intervention_preview": INTERVENTIONS[loop_type],
        "analysis_method": "keyword",
    }


def classify_loop_groq(frustration: str, api_key: str) -> dict:
    from groq import Groq

    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "You are a Spotify product AI. Return only valid JSON.",
            },
            {
                "role": "user",
                "content": CLASSIFY_PROMPT.format(frustration=frustration.replace('"', "'")),
            },
        ],
        temperature=0.2,
        response_format={"type": "json_object"},
    )
    result = json.loads(response.choices[0].message.content)
    loop_type = result.get("loop_type", "genre_lock")
    if loop_type not in LOOP_TYPES:
        loop_type = _score_keywords(frustration)
    result["loop_type"] = loop_type
    result["analysis_method"] = "groq"
    return result


def generate_loop_break_keyword(
    loop_type: str,
    frustration: str,
    mood: str,
    openness: str,
) -> dict:
    loop_type = loop_type if loop_type in LOOP_TYPES else "genre_lock"
    tracks = FALLBACK_TRACKS[loop_type]
    return {
        "intervention_headline": INTERVENTIONS[loop_type].split("—")[0].strip(),
        "loop_break_message": (
            f"Based on your {LOOP_LABELS[loop_type]} and mood ({mood}), "
            f"here are 3 picks tuned for {openness.lower()} novelty."
        ),
        "tracks": tracks,
        "analysis_method": "keyword",
    }


def generate_loop_break_groq(
    loop_type: str,
    frustration: str,
    mood: str,
    openness: str,
    api_key: str,
) -> dict:
    from groq import Groq

    loop_type = loop_type if loop_type in LOOP_TYPES else "genre_lock"
    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "You are Loop Break inside Spotify. Return only valid JSON.",
            },
            {
                "role": "user",
                "content": RECOMMEND_PROMPT.format(
                    loop_label=LOOP_LABELS[loop_type],
                    intervention=INTERVENTIONS[loop_type],
                    frustration=frustration.replace('"', "'"),
                    mood=mood,
                    openness=openness,
                ),
            },
        ],
        temperature=0.6,
        response_format={"type": "json_object"},
    )
    result = json.loads(response.choices[0].message.content)
    tracks = result.get("tracks", [])
    if len(tracks) < 3:
        fallback = FALLBACK_TRACKS[loop_type]
        result["tracks"] = (tracks + fallback)[:3]
    result["analysis_method"] = "groq"
    return result
