"""Part 4: Loop Break — embedded in a Spotify app UI prototype."""

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
    #MainMenu, footer, header {visibility: hidden;}

    .stApp { background: #000; }

    .block-container {
        max-width: 390px;
        padding-top: 3.2rem;
        padding-bottom: 8.5rem;
        background: #121212;
        min-height: 100vh;
        margin: 0 auto;
        border-left: 1px solid #282828;
        border-right: 1px solid #282828;
    }

    .chrome-top {
        position: fixed;
        top: 0;
        left: 50%;
        transform: translateX(-50%);
        width: 390px;
        max-width: 100%;
        background: #121212;
        z-index: 999;
        border-bottom: 1px solid #282828;
    }

    .chrome-status {
        display: flex;
        justify-content: space-between;
        padding: 0.35rem 1rem 0;
        font-size: 0.62rem;
        color: #fff;
    }

    .chrome-bar {
        display: flex;
        align-items: center;
        padding: 0.55rem 1rem 0.65rem;
        gap: 0.5rem;
    }

    .chrome-bar .title {
        flex: 1;
        text-align: center;
        color: #fff;
        font-weight: 700;
        font-size: 0.95rem;
    }

    .chrome-bar .ico { color: #fff; width: 1.5rem; }

    .chrome-bottom {
        position: fixed;
        bottom: 0;
        left: 50%;
        transform: translateX(-50%);
        width: 390px;
        max-width: 100%;
        z-index: 999;
    }

    .mini-player {
        background: #282828;
        margin: 0 0.5rem 0.35rem;
        border-radius: 6px;
        padding: 0.45rem 0.65rem;
        display: flex;
        align-items: center;
        gap: 0.55rem;
    }

    .mini-player .thumb {
        width: 36px; height: 36px; border-radius: 3px;
        background: linear-gradient(135deg, #1db954, #509bf5);
    }

    .mini-player .song { color: #fff; font-size: 0.78rem; font-weight: 600; margin: 0; }
    .mini-player .artist { color: #b3b3b3; font-size: 0.68rem; margin: 0; }

    .bottom-nav {
        background: #121212;
        border-top: 1px solid #282828;
        display: flex;
        justify-content: space-around;
        padding: 0.5rem 0 0.65rem;
    }

    .nav-item { text-align: center; color: #b3b3b3; font-size: 0.6rem; font-weight: 600; }
    .nav-item.active { color: #fff; }
    .nav-item .ico { font-size: 1.1rem; display: block; margin-bottom: 0.1rem; }

    .greeting { color: #fff; font-size: 1.4rem; font-weight: 700; margin: 0 0 1rem; }
    .section-label { color: #fff; font-size: 1rem; font-weight: 700; margin: 0.75rem 0 0.55rem; }

    .mfy-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.6rem; }
    .mfy-card {
        border-radius: 6px; padding: 0.7rem; min-height: 64px;
        background: #282828; position: relative;
    }
    .mfy-card.dw { background: linear-gradient(135deg, #1a472a 0%, #2d1b4e 100%); }
    .mfy-card h4 { color: #fff; font-size: 0.8rem; font-weight: 700; margin: 0; }
    .mfy-card .sub { color: rgba(255,255,255,0.75); font-size: 0.66rem; margin-top: 0.2rem; }

    .dw-cover {
        width: 160px; height: 160px; margin: 0 auto 0.75rem;
        border-radius: 4px;
        background: linear-gradient(145deg, #1ed760, #1db954 25%, #509bf5 70%, #8c67ab);
        box-shadow: 0 8px 24px rgba(0,0,0,0.4);
    }

    .dw-title { color: #fff; font-size: 1.3rem; font-weight: 700; text-align: center; margin: 0; }
    .dw-meta { color: #b3b3b3; font-size: 0.76rem; text-align: center; margin: 0.2rem 0 0.65rem; }

    .stale-banner {
        background: linear-gradient(90deg, #1a472a, #1f1f1f);
        border: 1px solid #1db954;
        border-radius: 8px;
        padding: 0.7rem 0.8rem;
        margin: 0.75rem 0;
    }
    .stale-banner p { color: #fff; font-size: 0.8rem; font-weight: 600; margin: 0 0 0.1rem; }
    .stale-banner small { color: #b3b3b3; font-size: 0.7rem; }

    .track-row {
        display: flex; align-items: center; gap: 0.6rem;
        padding: 0.4rem 0; border-bottom: 1px solid #282828;
    }
    .track-row .num { color: #b3b3b3; font-size: 0.78rem; width: 1rem; text-align: center; }
    .track-row .thumb { width: 38px; height: 38px; border-radius: 3px; background: #333; }
    .track-row .song { color: #fff; font-size: 0.84rem; margin: 0; font-weight: 500; }
    .track-row .artist { color: #b3b3b3; font-size: 0.74rem; margin: 0.1rem 0 0; }
    .lib-badge {
        display: inline-block; background: #535353; color: #fff;
        font-size: 0.55rem; font-weight: 600; padding: 0.1rem 0.3rem;
        border-radius: 3px; margin-left: 0.3rem; vertical-align: middle;
    }

    .loop-sheet {
        background: #181818; border-radius: 12px;
        border: 1px solid #282828; padding: 0.85rem; margin-bottom: 0.75rem;
    }
    .sheet-handle {
        width: 32px; height: 4px; background: #535353;
        border-radius: 4px; margin: 0 auto 0.65rem;
    }
    .loop-sheet h3 { color: #fff; font-size: 1rem; margin: 0 0 0.3rem; }
    .loop-sheet p { color: #b3b3b3; font-size: 0.8rem; line-height: 1.4; margin: 0 0 0.5rem; }

    .loop-type-pill {
        display: inline-block; background: #282828; color: #1db954;
        border: 1px solid #1db954; border-radius: 500px;
        padding: 0.18rem 0.6rem; font-size: 0.7rem; font-weight: 600;
        margin-bottom: 0.35rem;
    }

    .pick-card {
        background: #282828; border-radius: 8px;
        padding: 0.7rem; margin-bottom: 0.45rem;
    }
    .pick-card .song { color: #fff; font-weight: 600; font-size: 0.88rem; margin: 0; }
    .pick-card .artist { color: #b3b3b3; font-size: 0.76rem; margin: 0.08rem 0 0.4rem; }
    .pick-card .why { color: #d0d0d0; font-size: 0.73rem; line-height: 1.35; margin: 0.15rem 0; }
    .pick-card .why em { color: #1db954; font-style: normal; font-weight: 600; }

    .prototype-banner {
        text-align: center; color: #535353; font-size: 0.68rem;
        margin-top: 0.5rem;
    }

    .stButton > button[kind="primary"] {
        background-color: #1db954 !important; color: #000 !important;
        border: none !important; font-weight: 700 !important; border-radius: 500px !important;
    }
    .stButton > button[kind="secondary"] {
        background-color: #282828 !important; color: #fff !important;
        border: 1px solid #535353 !important; border-radius: 500px !important;
    }

    div[data-testid="stSidebar"] { background-color: #000; }
</style>
"""

DW_TRACKS = [
    ("Blinding Lights", "The Weeknd", True),
    ("As It Was", "Harry Styles", False),
    ("Flowers", "Miley Cyrus", True),
    ("Cruel Summer", "Taylor Swift", False),
    ("Save Your Tears", "The Weeknd", True),
    ("Espresso", "Sabrina Carpenter", False),
]

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
        "lb_screen": "home",
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


def render_chrome_top(title: str) -> None:
    st.markdown(
        f"""
        <div class="chrome-top">
          <div class="chrome-status"><span>9:41</span><span>●●●</span></div>
          <div class="chrome-bar">
            <span class="ico">☰</span>
            <span class="title">{title}</span>
            <span class="ico">👤</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_chrome_bottom() -> None:
    st.markdown(
        """
        <div class="chrome-bottom">
          <div class="mini-player">
            <div class="thumb"></div>
            <div>
              <p class="song">Discover Weekly</p>
              <p class="artist">Made For You · Spotify</p>
            </div>
          </div>
          <div class="bottom-nav">
            <div class="nav-item active"><span class="ico">🏠</span>Home</div>
            <div class="nav-item"><span class="ico">🔍</span>Search</div>
            <div class="nav-item"><span class="ico">📚</span>Your Library</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def nav_back() -> bool:
    return st.button("← Back", type="secondary", use_container_width=True)


def go_back() -> None:
    screen = st.session_state["lb_screen"]
    step = st.session_state["lb_step"]
    if screen == "loop_break" and step in ("diagnostic", "results"):
        st.session_state["lb_step"] = "diagnostic" if step == "results" else "entry"
    elif screen == "loop_break":
        st.session_state["lb_screen"] = "dw"
        st.session_state["lb_step"] = "entry"
    elif screen == "dw":
        st.session_state["lb_screen"] = "home"


def render_home() -> None:
    render_chrome_top("Good evening")
    st.markdown(
        """
        <p class="greeting">Good evening</p>
        <p class="section-label">Made For You</p>
        <div class="mfy-grid">
          <div class="mfy-card dw">
            <h4>Discover Weekly</h4>
            <div class="sub">Your weekly mixtape · Updated today</div>
          </div>
          <div class="mfy-card"><h4>Release Radar</h4><div class="sub">New from artists you follow</div></div>
          <div class="mfy-card"><h4>Daily Mix 1</h4><div class="sub">Indie · Alt</div></div>
          <div class="mfy-card"><h4>On Repeat</h4><div class="sub">Songs you love right now</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Open Discover Weekly", type="primary", use_container_width=True):
        st.session_state["lb_screen"] = "dw"
        st.rerun()
    render_chrome_bottom()


def render_dw_playlist() -> None:
    render_chrome_top("Discover Weekly")

    rows = ""
    for i, (song, artist, in_lib) in enumerate(DW_TRACKS, start=1):
        badge = '<span class="lib-badge">In your library</span>' if in_lib else ""
        rows += f"""
        <div class="track-row">
          <span class="num">{i}</span><div class="thumb"></div>
          <div><p class="song">{song}{badge}</p><p class="artist">{artist}</p></div>
        </div>"""

    st.markdown(
        f"""
        <div class="dw-cover"></div>
        <p class="dw-title">Discover Weekly</p>
        <p class="dw-meta">Made For You · 30 songs · Updated Monday</p>
        <div class="stale-banner">
          <p>This week feels familiar?</p>
          <small>3 songs already in your library — Loop Break can diagnose why.</small>
        </div>
        {rows}
        """,
        unsafe_allow_html=True,
    )

    if st.button("Break the loop", type="primary", use_container_width=True):
        st.session_state["lb_screen"] = "loop_break"
        st.session_state["lb_step"] = "entry"
        st.rerun()
    if nav_back():
        go_back()
        st.rerun()
    render_chrome_bottom()


def render_loop_entry() -> None:
    render_chrome_top("Loop Break")
    st.markdown(
        """
        <div class="loop-sheet">
          <div class="sheet-handle"></div>
          <h3>Loop Break</h3>
          <p>In-product reset when Discover Weekly stops feeling new.
          Describe what went wrong — we'll diagnose your loop type.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    frustration = st.text_area(
        "Frustration",
        value=st.session_state["lb_frustration"],
        height=96,
        placeholder="e.g. Half the songs were already in my library…",
        label_visibility="collapsed",
    )

    st.caption("Examples:")
    c1, c2 = st.columns(2)
    for i, example in enumerate(EXAMPLE_PROMPTS):
        col = c1 if i % 2 == 0 else c2
        with col:
            if st.button(example[:38] + "…", key=f"ex_{i}"):
                st.session_state["lb_frustration"] = example
                st.rerun()

    if st.button("Run Loop Diagnostic", type="primary", use_container_width=True):
        if not frustration or len(frustration.strip()) < 15:
            st.error("Please enter at least 15 characters.")
            return
        st.session_state["lb_frustration"] = frustration.strip()
        api_key = get_secret("GROQ_API_KEY")
        with st.spinner("Diagnosing your loop…"):
            try:
                diagnosis = (
                    classify_loop_groq(frustration.strip(), api_key)
                    if api_key
                    else classify_loop_keyword(frustration.strip())
                )
            except Exception as exc:
                st.warning(f"AI failed ({exc}). Using keyword fallback.")
                diagnosis = classify_loop_keyword(frustration.strip())
        st.session_state["lb_diagnosis"] = diagnosis
        st.session_state["lb_step"] = "diagnostic"
        st.rerun()

    if nav_back():
        go_back()
        st.rerun()
    render_chrome_bottom()


def render_loop_diagnostic() -> None:
    diagnosis = st.session_state["lb_diagnosis"]
    loop_type = diagnosis["loop_type"]
    label = LOOP_LABELS[loop_type]

    render_chrome_top("Loop Diagnostic")
    st.markdown(
        f"""
        <div class="loop-sheet">
          <div class="sheet-handle"></div>
          <div class="loop-type-pill">{label}</div>
          <h3>Your loop type</h3>
          <p>{diagnosis.get("diagnosis_summary", LOOP_DESCRIPTIONS[loop_type])}</p>
          <p><strong style="color:#1db954">Next:</strong>
          {diagnosis.get("intervention_preview", INTERVENTIONS[loop_type])}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.caption("How are you feeling?")
    mood = st.selectbox(
        "Mood",
        ["Calm / low energy", "Energetic", "Melancholy", "Focused", "Open to anything"],
        index=4,
        label_visibility="collapsed",
    )
    st.caption("How far should we push novelty?")
    openness = st.select_slider(
        "Novelty",
        options=[
            "Stay close to my taste",
            "Nudge me slightly outside my comfort zone",
            "Surprise me — break the loop completely",
        ],
        value=st.session_state["lb_openness"],
        label_visibility="collapsed",
    )

    if st.button("Get 3 Loop Break picks", type="primary", use_container_width=True):
        st.session_state["lb_mood"] = mood
        st.session_state["lb_openness"] = openness
        api_key = get_secret("GROQ_API_KEY")
        with st.spinner("Building your reset…"):
            try:
                recs = (
                    generate_loop_break_groq(
                        loop_type, st.session_state["lb_frustration"], mood, openness, api_key
                    )
                    if api_key
                    else generate_loop_break_keyword(
                        loop_type, st.session_state["lb_frustration"], mood, openness
                    )
                )
            except Exception as exc:
                st.warning(f"AI failed ({exc}). Using fallback picks.")
                recs = generate_loop_break_keyword(
                    loop_type, st.session_state["lb_frustration"], mood, openness
                )
        st.session_state["lb_recommendations"] = recs
        st.session_state["lb_step"] = "results"
        st.rerun()

    if nav_back():
        go_back()
        st.rerun()
    render_chrome_bottom()


def render_loop_results() -> None:
    diagnosis = st.session_state["lb_diagnosis"]
    recs = st.session_state["lb_recommendations"]
    label = LOOP_LABELS[diagnosis["loop_type"]]

    render_chrome_top("Your Loop Break")

    picks = ""
    for i, track in enumerate(recs.get("tracks", [])[:3], start=1):
        picks += f"""
        <div class="pick-card">
          <p class="song">{i}. {track.get("song", "")}</p>
          <p class="artist">{track.get("artist", "")}</p>
          <p class="why"><em>Why it fits:</em> {track.get("why_fit", "")}</p>
          <p class="why"><em>Not last week's DW:</em> {track.get("novelty_rationale", "")}</p>
        </div>"""

    st.markdown(
        f"""
        <div class="loop-sheet">
          <div class="loop-type-pill">{label} reset</div>
          <h3>{recs.get("intervention_headline", "Your Loop Break")}</h3>
          <p>{recs.get("loop_break_message", "")}</p>
        </div>
        {picks}
        """,
        unsafe_allow_html=True,
    )

    for track in recs.get("tracks", [])[:3]:
        artist = track.get("artist", "")
        song = track.get("song", "")
        st.link_button(f"▶  {song} — {artist}", spotify_search_url(artist, song), use_container_width=True)

    st.caption("Trust this more than your last Discover Weekly?")
    trust = st.slider("Trust", 1, 5, 4, label_visibility="collapsed")
    st.caption(f"**{trust}/5**")

    if st.button("Done — back to Home", type="primary", use_container_width=True):
        st.session_state["lb_trust_score"] = trust
        st.session_state["lb_screen"] = "home"
        st.session_state["lb_step"] = "entry"
        st.session_state["lb_frustration"] = ""
        st.session_state["lb_diagnosis"] = None
        st.session_state["lb_recommendations"] = None
        st.rerun()

    if nav_back():
        go_back()
        st.rerun()
    render_chrome_bottom()


def render_grader_sidebar() -> None:
    with st.sidebar:
        st.markdown("### Demo controls")
        st.caption("Loop Break embedded in Spotify mobile UI")
        st.markdown("**Path:** Home → DW playlist → Break the loop")
        if get_secret("GROQ_API_KEY"):
            st.success("Groq connected")
        else:
            st.warning("No API key")
        with st.expander("Why AI?"):
            st.caption(
                "Recsys scores plays, not why DW failed. AI diagnoses loop type, "
                "matches intervention, explains 3 picks. UX: passive dump → guided reset."
            )
        if st.session_state.get("lb_trust_score"):
            st.metric("Last trust score", f"{st.session_state['lb_trust_score']}/5")
        if st.button("Reset to Home"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()


def main() -> None:
    st.set_page_config(
        page_title="Spotify",
        page_icon="🎵",
        layout="centered",
        initial_sidebar_state="collapsed",
    )
    st.markdown(SPOTIFY_CSS, unsafe_allow_html=True)
    init_session()
    render_grader_sidebar()

    screen = st.session_state["lb_screen"]
    step = st.session_state["lb_step"]

    if screen == "home":
        render_home()
    elif screen == "dw":
        render_dw_playlist()
    elif screen == "loop_break":
        if step == "entry":
            render_loop_entry()
        elif step == "diagnostic":
            render_loop_diagnostic()
        else:
            render_loop_results()

    st.markdown(
        '<p class="prototype-banner">Fellowship prototype — not affiliated with Spotify AB</p>',
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
