"""Part 1: Spotify Review Discovery Engine — Streamlit app."""

import json
import os
from pathlib import Path

import pandas as pd
import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError

from analyze_feedback import (
    THEMES,
    build_summary_json,
    classify_with_groq,
    classify_with_keywords,
)

DATA_DIR = Path(__file__).parent
MASTER_FILE = DATA_DIR / "master_feedback.csv"
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

    result = classify_with_keywords(text)
    result["analysis_method"] = "keyword"
    return result


@st.cache_data
def load_master_data() -> pd.DataFrame:
    if MASTER_FILE.exists():
        return pd.read_csv(MASTER_FILE)
    return pd.DataFrame()


@st.cache_data
def load_analyzed_data() -> pd.DataFrame:
    if ANALYZED_FILE.exists():
        return pd.read_csv(ANALYZED_FILE)
    return pd.DataFrame()


@st.cache_data
def load_summary() -> dict:
    if SUMMARY_FILE.exists():
        return json.loads(SUMMARY_FILE.read_text(encoding="utf-8"))
    return {}


def normalize_upload(df: pd.DataFrame) -> pd.DataFrame:
    """Accept CSV with text/source columns or common aliases."""
    columns = {c.lower(): c for c in df.columns}
    text_col = columns.get("text") or columns.get("original review") or columns.get("review")
    source_col = columns.get("source")
    if not text_col:
        raise ValueError("CSV must include a 'text' column.")
    out = pd.DataFrame(
        {
            "text": df[text_col].astype(str),
            "source": df[source_col].astype(str) if source_col else "Other",
        }
    )
    return out.dropna(subset=["text"])


def show_bulk_summary(df: pd.DataFrame) -> None:
    discovery = df[df["discovery_related"].astype(str).str.lower().isin(["true", "1", "yes"])]
    if discovery.empty and "discovery_related" in df.columns:
        discovery = df[df["discovery_related"] == True]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Reviews analyzed", len(df))
    c2.metric("Discovery-related", len(discovery))
    c3.metric(
        "Top theme",
        discovery["primary_theme"].mode().iloc[0].replace("_", " ").title()
        if not discovery.empty
        else "—",
    )
    methods = df["analysis_method"].value_counts() if "analysis_method" in df.columns else {}
    c4.metric("AI method", methods.index[0] if len(methods) else "keyword")

    if not discovery.empty:
        st.subheader("Theme breakdown (discovery-related)")
        st.bar_chart(discovery["primary_theme"].value_counts())

    st.subheader("Analyzed reviews")
    display_cols = [
        c
        for c in [
            "text",
            "source",
            "primary_theme",
            "discovery_related",
            "user_segment",
            "key_insight",
            "analysis_method",
        ]
        if c in df.columns
    ]
    st.dataframe(df[display_cols], use_container_width=True, hide_index=True)

    st.download_button(
        "Download analyzed CSV",
        df.to_csv(index=False),
        file_name="analyzed_feedback.csv",
        mime="text/csv",
    )


def page_bulk_analyze() -> None:
    st.header("Bulk Analyze at Scale")
    st.write(
        "Run AI analysis across **hundreds of reviews** in one pass — "
        "the core of the Review Discovery Engine. "
        "Use the bundled dataset (271 reviews from Play Store, Reddit, and Community) "
        "or upload your own CSV with `text` and `source` columns."
    )

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("Load pre-analyzed dataset (271 reviews)", type="primary"):
            df = load_analyzed_data()
            if df.empty:
                st.error("Pre-analyzed file not found.")
            else:
                st.session_state["bulk_results"] = df
                st.success(f"Loaded {len(df)} pre-analyzed reviews.")

    with col_b:
        use_bundled = st.checkbox("Use bundled master_feedback.csv", value=True)

    uploaded = None if use_bundled else st.file_uploader("Upload CSV", type=["csv"])

    max_rows = st.select_slider(
        "Rows to analyze in this run",
        options=[10, 25, 50, 100, 271],
        value=50,
        help="Smaller batches are faster on Streamlit Cloud when using Groq AI.",
    )

    if st.button("Run bulk analysis", type="secondary"):
        try:
            if use_bundled:
                raw = load_master_data()
                if raw.empty:
                    st.error("master_feedback.csv not found.")
                    return
                df_in = raw.head(max_rows)
            else:
                if uploaded is None:
                    st.error("Upload a CSV or enable the bundled dataset.")
                    return
                df_in = normalize_upload(pd.read_csv(uploaded)).head(max_rows)
        except ValueError as exc:
            st.error(str(exc))
            return

        st.info(f"Analyzing **{len(df_in)}** reviews...")
        progress = st.progress(0)
        status = st.empty()
        rows = []
        total = len(df_in)

        for i, row in df_in.iterrows():
            text = str(row["text"]).strip()
            source = str(row.get("source", "Other")).strip()
            result = analyze_text(text, source)
            rows.append(
                {
                    "text": text,
                    "source": source,
                    "primary_theme": result.get("primary_theme", "other"),
                    "discovery_related": result.get("discovery_related", False),
                    "frustration_summary": result.get("frustration_summary", ""),
                    "user_segment": result.get("user_segment", "unknown"),
                    "desired_behavior": result.get("desired_behavior", ""),
                    "key_insight": result.get("key_insight", ""),
                    "quote_worthy": result.get("quote_worthy", False),
                    "analysis_method": result.get("analysis_method", "keyword"),
                }
            )
            idx = len(rows)
            progress.progress(idx / total)
            status.caption(f"Analyzed {idx}/{total} — {result.get('analysis_method', 'keyword')}")

        analyzed = pd.DataFrame(rows)
        st.session_state["bulk_results"] = analyzed
        summary = build_summary_json(analyzed)
        st.session_state["bulk_summary"] = summary
        progress.empty()
        status.empty()
        st.success(f"Bulk analysis complete — {len(analyzed)} reviews processed.")

    if "bulk_results" in st.session_state:
        show_bulk_summary(st.session_state["bulk_results"])


def page_analyze() -> None:
    st.header("Analyze a Single Review")
    st.caption("Demo: try the AI on one review. For scale analysis, use the Bulk Analyze tab.")
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
    summary = st.session_state.get("bulk_summary") or load_summary()
    df = st.session_state.get("bulk_results")
    if df is None or (isinstance(df, pd.DataFrame) and df.empty):
        df = load_analyzed_data()

    if summary:
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Reviews", summary.get("total_reviews", len(df)))
        c2.metric("Discovery-Related", summary.get("discovery_related_reviews", 0))
        c3.metric("Sources", len(summary.get("by_source", {})))

    if df.empty:
        st.warning("No analyzed data found. Use **Bulk Analyze** or run analyze_feedback.py locally.")
        return

    st.subheader("Top Discovery Themes")
    discovery = df[df["discovery_related"].astype(str).str.lower().isin(["true", "1", "yes"])]
    if discovery.empty:
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
Play Store + Reddit + Community  (scrape_*.py)
            ↓
     master_feedback.csv (271 reviews)
            ↓
     Bulk Analyze tab  (AI across all rows)
            ↓
  Themes · Segments · Insights · Quotes
            ↓
     Insights Dashboard → Part 2 & Part 3
```

### Data sources
- **Play Store** — 1–3 star reviews (complaints)
- **Reddit** — r/Spotify posts (algorithm, Discover Weekly, repetition)
- **Spotify Community** — Discovery & Promo board

### What AI answers (at scale)
- Why do users struggle to discover new music?
- What frustrates them about recommendations?
- Which segments are affected?
- What unmet needs appear consistently?

### Top finding
**Discover Weekly staleness traps listeners in repetition loops.**
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

    tab_bulk, tab_single, tab_dash, tab_flow = st.tabs(
        ["Bulk Analyze", "Analyze One Review", "Insights Dashboard", "Workflow"]
    )

    with tab_bulk:
        page_bulk_analyze()
    with tab_single:
        page_analyze()
    with tab_dash:
        page_dashboard()
    with tab_flow:
        page_workflow()

    api_key = get_api_key()
    if api_key:
        st.sidebar.success("AI API connected")
    else:
        st.sidebar.info("No API key — bulk analysis uses keyword fallback.")


if __name__ == "__main__":
    main()
