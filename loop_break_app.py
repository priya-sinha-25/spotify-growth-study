"""Part 4: Loop Break — in-product Spotify discovery reset (fellowship prototype)."""

import os

import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError

from loop_break import (
    INTERVENTIONS,
    LOOP_DESCRIPTIONS,
    LOOP_LABELS,
    classify_loop_groq,
    classify_loop_keyword,
    generate_loop_break_groq,
    generate_loop_break_keyword,
    spotify_search_url,
)

SPOTIFY_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Circular+Std:wght@400;700&display=swap');

    .stApp {
        background: linear-gradient(180deg, #121212 0%, #0a0a0a 100%);
    }

    .spotify-hero {
        background: linear-gradient(135deg, #1a472a 0%, #121212 55%, #1a1a2e 100%);
        border-radius: 12px;
        padding: 1.5rem 1.75rem;
        margin-bottom: 1rem;
        border: 1px solid #282828;
    }

    .spotify-hero h1 {
        color: #fff;
        font-size: 1.75rem;
        font-weight: 700;
        margin: 0 0 0.35rem 0;
        letter-spacing: -0.02em;
    }

    .spotify-hero p {
        color: #b3b3b3;
        margin: 0;
        font-size: 0.95rem;
        line-height: 1.45;
    }

    .spotify-badge {
        display: inline-block;
        background: #1DB954;
        color: #000;
        font-size: 0.7rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        padding: 0.2rem 0.55rem;
        border-radius: 4px;
        margin-bottom: 0.6rem;
    }

    .product-context {
        background: #181818;
        border: 1px solid #282828;
        border-radius: 8px;
        padding: 0.85rem 1rem;
        margin: 0.75rem 0 1.25rem 0;
        font-size: 0.82rem;
        color: #a7a7a7;
        line-height: 1.5;
    }

    .product-context strong {
        color: #1DB954;
    }

    .dw-card {
        background: #181818;
        border-radius: 8px;
        padding: 1rem 1.1rem;
        border-left: 4px solid #1DB954;
        margin: 1rem 0;
    }

    .dw-card h3 {
        color: #fff;
        font-size: 1rem;
        margin: 0 0 0.35rem 0;
    }

    .dw-card p {
        color: #b3b3b3;
        font-size: 0.88rem;
        margin: 0;
    }

    .loop-type-pill {
        display: inline-block;
        background: #282828;
        color: #1DB954;
        border: 1px solid #1DB954;
        border-radius: 500px;
        padding: 0.25rem 0.75rem;
        font-size: 0.8rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }

    .track-card {
        background: #181818;
        border-radius: 8px;
        padding: 1rem 1.1rem;
        margin-bottom: 0.65rem;
        border: 1px solid #282828;
        transition: background 0.15s;
    }

    .track-card:hover {
        background: #282828;
    }

    .track-num {
        color: #1DB954;
        font-weight: 700;
        font-size: 0.85rem;
        margin-right: 0.5rem;
    }

    .track-title {
        color: #fff;
        font-weight: 600;
        font-size: 1rem;
        margin: 0;
    }

    .track-artist {
        color: #b3b3b3;
        font-size: 0.88rem;
        margin: 0.15rem 0 0.6rem 0;
    }

    .track-why {
        color: #d0d0d0;
        font-size: 0.82rem;
        margin: 0.35rem 0;
        line-height: 1.4;
    }

    .track-why em {
        color: #1DB954;
        font-style: normal;
        font-weight: 600;
    }

    .prototype-footer {
        color: #535353;
        font-size: 0.75rem;
        text-align: center;
        margin-top: 2rem;
        padding-top: 1rem;
        border-top: 1px solid #282828;
    }

    div[data-testid="stSidebar"] {
        background-color: #000;
    }

  .stButton > button[kind="primary"] {
        background-color: #1DB954 !important;
        color: #000 !important;
        border: none !important;
        font-weight: 700 !important;
        border-radius: 500px !important;
        padding: 0.5rem 1.5rem !important;
    }

    .stButton > button[kind="secondary"] {
        background-color: transparent !important;
        color: #fff !important;
        border: 1px solid #535353 !important;
        border-radius: 500px !important;
    }
</style>
"""

EXAMPLE_PROMPTS = [
    "Discover Weekly had songs I already saved — feels like my library again.",
    "Same indie mood every Monday. I want something new but still 'me'.",
    "I only listen at the gym and now everything sounds like workout EDM.",
    "When DW fails I go back to my 2019 playlist. I'm stuck in a loop.",
]


def get_secret(key: str) -> str | None:
    try:
        value = st.secrets.get(key)
        if value:
            return value
    except StreamlitSecretNotFoundError:
        pass
    return os.getenv(key)


def init_session() -> None:
    defaults = {
        "lb_step": "entry",
        "lb_frustration": "",
        "lb_diagnosis": None,
        "lb_mood": "Open to anything",
        "lb_openness": "Nudge me slightly outside my comfort zone",
        "lb_recommendations": None,
        "lb_trust_score": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def render_hero() -> None:
    st.markdown(
        """
        <div class="spotify-hero">
            <div class="spotify-badge">Made For You · Prototype</div>
            <h1>Loop Break</h1>
            <p>When Discover Weekly feels like a rerun, diagnose why — then get 3 explained picks
            to reset your discovery loop.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="product-context">
            <strong>In-product moment:</strong> Home → Made For You → Discover Weekly →
            <em>"This week feels familiar"</em> → <strong>Loop Break</strong>
            <br><br>
            White space vs AI DJ (session DJ) and Prompted Playlists (new playlist):
            Loop Break owns the <strong>post-DW failure</strong> diagnostic reset.
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_entry() -> None:
    st.markdown(
        """
        <div class="dw-card">
            <h3>Discover Weekly · This week</h3>
            <p>Not feeling fresh? Tell us what went wrong — we'll run a Loop Diagnostic.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    frustration = st.text_area(
        "What felt off about this week's Discover Weekly?",
        value=st.session_state["lb_frustration"],
        height=120,
        placeholder="e.g. Half the songs were already in my library...",
        label_visibility="collapsed",
    )

    st.caption("Try an example:")
    cols = st.columns(2)
    for i, example in enumerate(EXAMPLE_PROMPTS):
        with cols[i % 2]:
            if st.button(example[:52] + "…", key=f"example_{i}"):
                st.session_state["lb_frustration"] = example
                st.rerun()

    if st.button("Run Loop Diagnostic", type="primary", use_container_width=True):
        if not frustration or len(frustration.strip()) < 15:
            st.error("Please describe your DW frustration in at least 15 characters.")
            return

        st.session_state["lb_frustration"] = frustration.strip()
        api_key = get_secret("GROQ_API_KEY")

        with st.spinner("Diagnosing your loop type…"):
            try:
                if api_key:
                    diagnosis = classify_loop_groq(frustration.strip(), api_key)
                else:
                    diagnosis = classify_loop_keyword(frustration.strip())
            except Exception as exc:
                st.warning(f"AI diagnostic failed ({exc}). Using keyword fallback.")
                diagnosis = classify_loop_keyword(frustration.strip())

        st.session_state["lb_diagnosis"] = diagnosis
        st.session_state["lb_step"] = "diagnostic"
        st.rerun()


def render_diagnostic() -> None:
    diagnosis = st.session_state["lb_diagnosis"]
    loop_type = diagnosis["loop_type"]
    label = LOOP_LABELS[loop_type]

    st.markdown(f'<div class="loop-type-pill">{label}</div>', unsafe_allow_html=True)
    st.subheader("Loop Diagnostic")
    st.write(diagnosis.get("diagnosis_summary", LOOP_DESCRIPTIONS[loop_type]))

    st.info(f"**Intervention:** {diagnosis.get('intervention_preview', INTERVENTIONS[loop_type])}")

    col1, col2 = st.columns(2)
    with col1:
        mood = st.selectbox(
            "How are you feeling right now?",
            ["Calm / low energy", "Energetic", "Melancholy", "Focused", "Open to anything"],
            index=4,
        )
    with col2:
        openness = st.select_slider(
            "How far should we push novelty?",
            options=[
                "Stay close to my taste",
                "Nudge me slightly outside my comfort zone",
                "Surprise me — break the loop completely",
            ],
            value=st.session_state["lb_openness"],
        )

    c1, c2 = st.columns([1, 1])
    with c1:
        if st.button("← Back", type="secondary"):
            st.session_state["lb_step"] = "entry"
            st.rerun()
    with c2:
        if st.button("Get my 3 Loop Break picks", type="primary", use_container_width=True):
            st.session_state["lb_mood"] = mood
            st.session_state["lb_openness"] = openness
            api_key = get_secret("GROQ_API_KEY")

            with st.spinner("Building your Loop Break…"):
                try:
                    if api_key:
                        recs = generate_loop_break_groq(
                            loop_type,
                            st.session_state["lb_frustration"],
                            mood,
                            openness,
                            api_key,
                        )
                    else:
                        recs = generate_loop_break_keyword(
                            loop_type,
                            st.session_state["lb_frustration"],
                            mood,
                            openness,
                        )
                except Exception as exc:
                    st.warning(f"AI recommendations failed ({exc}). Using curated fallback picks.")
                    recs = generate_loop_break_keyword(
                        loop_type,
                        st.session_state["lb_frustration"],
                        mood,
                        openness,
                    )

            st.session_state["lb_recommendations"] = recs
            st.session_state["lb_step"] = "results"
            st.rerun()


def render_track_card(index: int, track: dict) -> None:
    artist = track.get("artist", "Unknown")
    song = track.get("song", "Unknown")
    why_fit = track.get("why_fit", "")
    novelty = track.get("novelty_rationale", "")
    url = spotify_search_url(artist, song)

    st.markdown(
        f"""
        <div class="track-card">
            <p class="track-title"><span class="track-num">{index}.</span>{song}</p>
            <p class="track-artist">{artist}</p>
            <p class="track-why"><em>Why it fits:</em> {why_fit}</p>
            <p class="track-why"><em>Why it's not last week's DW:</em> {novelty}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.link_button(f"Open in Spotify — {artist}", url, use_container_width=True)


def render_results() -> None:
    diagnosis = st.session_state["lb_diagnosis"]
    recs = st.session_state["lb_recommendations"]
    loop_type = diagnosis["loop_type"]
    label = LOOP_LABELS[loop_type]

    st.markdown(f'<div class="loop-type-pill">{label} reset</div>', unsafe_allow_html=True)
    st.subheader(recs.get("intervention_headline", "Your Loop Break"))
    st.write(recs.get("loop_break_message", ""))

    method = recs.get("analysis_method", "keyword")
    st.caption(f"Powered by {method} · 3 tracks only (survey-backed format)")

    for i, track in enumerate(recs.get("tracks", [])[:3], start=1):
        render_track_card(i, track)

    st.divider()
    st.subheader("Would you trust this more than your last Discover Weekly?")
    trust = st.slider(
        "Trust score",
        min_value=1,
        max_value=5,
        value=4,
        help="1 = no trust, 5 = would use instead of saved playlists",
        label_visibility="collapsed",
    )
    st.caption(f"Your score: **{trust}/5** — demo metric for Loop Break completion")

    if st.button("Save feedback & start over", type="primary"):
        st.session_state["lb_trust_score"] = trust
        st.session_state["lb_step"] = "entry"
        st.session_state["lb_frustration"] = ""
        st.session_state["lb_diagnosis"] = None
        st.session_state["lb_recommendations"] = None
        st.success(f"Thanks — trust score {trust}/5 recorded for demo.")
        st.rerun()

    if st.button("← Run another diagnostic", type="secondary"):
        st.session_state["lb_step"] = "diagnostic"
        st.rerun()


def main() -> None:
    st.set_page_config(
        page_title="Loop Break | Spotify",
        page_icon="🔄",
        layout="centered",
        initial_sidebar_state="expanded",
    )

    st.markdown(SPOTIFY_CSS, unsafe_allow_html=True)
    init_session()

    with st.sidebar:
        st.markdown("### Loop Break")
        st.caption("Part 4 MVP · Growth fellowship prototype")
        st.markdown("---")
        st.markdown("**Where this lives in Spotify**")
        st.markdown(
            """
            1. User opens **Discover Weekly**
            2. Playlist feels stale
            3. **Loop Break** surfaces (this screen)
            4. Diagnostic → 3 explained picks
            """
        )
        api_key = get_secret("GROQ_API_KEY")
        if api_key:
            st.success("Groq AI connected")
        else:
            st.warning("No API key — keyword + curated fallbacks")

        st.markdown("---")
        with st.expander("Why AI?", expanded=False):
            st.markdown("**Why traditional recsys isn't enough**")
            st.caption(
                "Collaborative filtering scores what you might play — not why DW failed. "
                "It optimizes familiarity, so library overlap and repetition persist "
                "(86% survey; 57% playlist fallback). No diagnosis, no explanation, "
                "no intervention when trust breaks."
            )
            st.markdown("**What AI unlocks**")
            st.caption(
                "• NL frustration → loop type (taxonomy from 271 reviews)\n"
                "• Matched intervention per loop — not one-size-fits-all DW\n"
                "• Explainable 3-track reset (57% need 'explains why')\n"
                "• Mood + novelty dialogue + trust feedback"
            )
            st.markdown("**How UX changes**")
            st.caption(
                "Before: passive 30-track dump → saved playlists.\n"
                "After: diagnose → 3 explained picks → rebuild trust."
            )

        st.markdown("---")
        st.markdown("**Not in MVP**")
        st.caption("Real library overlap detection (Spotify API) · Native DW UI integration")

        if st.session_state.get("lb_trust_score"):
            st.metric("Last trust score", f"{st.session_state['lb_trust_score']}/5")

    render_hero()

    step = st.session_state["lb_step"]
    if step == "entry":
        render_entry()
    elif step == "diagnostic":
        render_diagnostic()
    elif step == "results":
        render_results()

    st.markdown(
        """
        <div class="prototype-footer">
            Fellowship product prototype — not affiliated with Spotify AB.
            Loop taxonomy derived from 271-review discovery corpus + N=14 survey.
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
