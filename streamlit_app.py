"""Part 1: Spotify Review Discovery Engine — Streamlit app."""

import os
from pathlib import Path

import pandas as pd
import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError

from analyze_feedback import (
    THEMES,
    classify_with_groq,
    classify_with_keywords,
)

DATA_DIR = Path(__file__).parent
ANALYZED_FILE = DATA_DIR / "analyzed_feedback.csv"
SUMMARY_FILE = DATA_DIR / "insights_summary.json"

SOURCE_OPTIONS = ["PlayStore", "Reddit", "SpotifyCommunity", "Other"]


def get_secret(key: str) -> str | None:
    """Read a secret from Streamlit secrets or environment variables."""
    try:
        value = st.secrets.get(key)
        if value:
            return value
    except StreamlitSecretNotFoundError:
        pass
    return os.getenv(key)


def get_api_key() -> str | None:
    return get_secret("GROQ_API_KEY") or get_secret("OPENAI_API_KEY")


def analyze_text(text: str, source: str) -> dict:
    groq_key = get_secret("GROQ_API_KEY")
    if groq_key:
        try:
            return classify_with_groq(text, source, groq_key)
        except Exception as exc:
            st.warning(f"Groq analysis failed ({exc}). Using keyword fallback.")

    openai_key = get_secret("OPENAI_API_KEY")
    if openai_key:
        try:
            from openai import OpenAI

            from analyze_feedback import classify_with_openai

            client = OpenAI(api_key=openai_key)
            return classify_with_openai(text, source, client)
        except Exception as exc:
            st.warning(f"OpenAI analysis failed ({exc}). Using keyword fallback.")

    return classify_with_keywords(text)


@st.cache_data
def load_analyzed_data() -> pd.DataFrame:
    if ANALYZED_FILE.exists():
        return pd.read_csv(ANALYZED_FILE)
    return pd.DataFrame()


@st.cache_data
def load_summary() -> dict:
    if SUMMARY_FILE.exists():
        import json

        return json.loads(SUMMARY_FILE.read_text(encoding="utf-8"))
    return {}


def page_analyze() -> None:
    st.header("Analyze a Review")
    st.write(
        "Paste any Spotify user review or forum post. AI extracts themes, "
        "user segment, and product insights for the Growth team."
    )

    source = st.selectbox("Source", SOURCE_OPTIONS)
    text = st.text_area("Review text", height=150, placeholder="Paste user feedback here...")

    if st.button("Analyze", type="primary"):
        if not text or len(text.strip()) < 10:
            st.error("Please enter at least 10 characters of review text.")
            return

        with st.spinner("Analyzing..."):
            result = analyze_text(text.strip(), source)

        method = result.get("analysis_method", "keyword")
        st.success(f"Analysis complete ({method})")

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Primary Theme", result.get("primary_theme", "").replace("_", " ").title())
            st.metric("Discovery Related", str(result.get("discovery_related", False)))
            st.metric("User Segment", result.get("user_segment", "").replace("_", " ").title())
        with col2:
            st.metric("Quote Worthy", str(result.get("quote_worthy", False)))
            st.metric("Desired Behavior", result.get("desired_behavior", ""))

        st.subheader("Frustration Summary")
        st.write(result.get("frustration_summary", ""))

        st.subheader("Key Product Insight")
        st.info(result.get("key_insight", ""))


def page_dashboard() -> None:
    st.header("Insights Dashboard")
    summary = load_summary()
    df = load_analyzed_data()

    if summary:
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Reviews", summary.get("total_reviews", 0))
        c2.metric("Discovery-Related", summary.get("discovery_related_reviews", 0))
        c3.metric("Sources", len(summary.get("by_source", {})))

    if df.empty:
        st.warning("No analyzed data found. Run analyze_feedback.py locally first.")
        return

    st.subheader("Top Discovery Themes")
    discovery = df[df["discovery_related"] == True]
    if not discovery.empty:
        theme_counts = discovery["primary_theme"].value_counts()
        st.bar_chart(theme_counts)

    st.subheader("Reviews by Source")
    st.bar_chart(df["source"].value_counts())

    st.subheader("Sample Discovery-Related Reviews")
    theme_filter = st.selectbox(
        "Filter by theme",
        ["All"] + [t.replace("_", " ").title() for t in THEMES],
    )
    filtered = discovery
    if theme_filter != "All":
        theme_key = theme_filter.lower().replace(" ", "_")
        filtered = discovery[discovery["primary_theme"] == theme_key]

    display_cols = ["text", "source", "primary_theme", "key_insight"]
    st.dataframe(
        filtered[display_cols].head(20),
        use_container_width=True,
        hide_index=True,
    )


def page_workflow() -> None:
    st.header("How This Workflow Works")
    st.markdown(
        """
### Pipeline

```
Play Store + Reddit + Community
            ↓
     master_feedback.csv (271 reviews)
            ↓
     AI Analysis (Groq / keyword fallback)
            ↓
  Themes · Segments · Insights · Quotes
            ↓
     Product decisions & MVP design
```

### Data sources
- **Play Store** — 1–3 star reviews (complaints)
- **Reddit** — r/Spotify posts (algorithm, Discover Weekly, repetition)
- **Spotify Community** — Discovery & Promo board

### What AI answers
- Why do users struggle to discover new music?
- What frustrates them about recommendations?
- Which segments are affected?
- What unmet needs appear consistently?

### Top finding
**Premium listeners feel recommendations have become repetitive and genre-locked.**
        """
    )

    if st.button("Download full analyzed dataset"):
        df = load_analyzed_data()
        if not df.empty:
            st.download_button(
                "Download CSV",
                df.to_csv(index=False),
                file_name="analyzed_feedback.csv",
                mime="text/csv",
            )


def main() -> None:
    st.set_page_config(
        page_title="Spotify Review Discovery Engine",
        page_icon="🎵",
        layout="wide",
    )

    st.title("Spotify Review Discovery Engine")
    st.caption("Part 1 — AI-powered analysis of user feedback at scale")

    tab1, tab2, tab3 = st.tabs(["Analyze Review", "Insights Dashboard", "Workflow"])

    with tab1:
        page_analyze()
    with tab2:
        page_dashboard()
    with tab3:
        page_workflow()

    api_key = get_api_key()
    if api_key:
        st.sidebar.success("AI API connected")
    else:
        st.sidebar.info("No API key in secrets — using keyword analysis for demo.")


if __name__ == "__main__":
    main()
