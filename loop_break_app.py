"""Part 4: Loop Break — embedded in Spotify web player UI."""

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

SPOTIFY_LOGO = """
<svg role="img" viewBox="0 0 24 24" width="32" height="32" fill="#1ed760" aria-hidden="true">
  <path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.26-1.26 11.28-1.02 15.721 1.621.539.3.719 1.02.419 1.56-.299.421-1.02.599-1.559.3z"/>
</svg>
"""

SPOTIFY_CSS = """
<style>
    #MainMenu, footer, header {visibility: hidden;}
    .stApp { background: #000; }

    .main .block-container {
        padding-top: 4.25rem !important;
        padding-left: 22rem !important;
        padding-right: 1.5rem !important;
        padding-bottom: 2rem !important;
        max-width: 100% !important;
        margin-left: 0 !important;
        margin-right: 0 !important;
    }

  .main.lb-panel-open .block-container {
        padding-right: 26rem !important;
    }

    section[data-testid="stSidebar"] {
        background: #000 !important;
        border-right: 1px solid #282828;
    }

    .spotify-topbar {
        position: fixed; top: 0; left: 0; right: 0; height: 56px;
        background: #000; z-index: 1000;
        display: flex; align-items: center; gap: 1rem;
        padding: 0 1.25rem; border-bottom: 1px solid #1a1a1a;
    }

    .spotify-topbar .logo { display: flex; align-items: center; flex-shrink: 0; }

    .home-btn {
        width: 48px; height: 48px; background: #1a1a1a; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        color: #b3b3b3; font-size: 1.2rem; flex-shrink: 0;
    }

    .search-pill {
        flex: 1; max-width: 480px; height: 48px; background: #1a1a1a;
        border-radius: 500px; display: flex; align-items: center;
        padding: 0 1rem; gap: 0.65rem; color: #b3b3b3; font-size: 0.9rem;
    }

    .topbar-right {
        margin-left: auto; display: flex; align-items: center;
        gap: 1.25rem; color: #b3b3b3; font-size: 0.82rem; font-weight: 600;
    }

    .topbar-right .premium { color: #fff; }
    .login-pill {
        background: #fff; color: #000; font-weight: 700;
        padding: 0.55rem 1.75rem; border-radius: 500px; font-size: 0.95rem;
    }

    .user-chip {
        background: #282828; color: #fff; font-weight: 600;
        padding: 0.4rem 0.85rem; border-radius: 500px; font-size: 0.82rem;
    }

    .spotify-lib-sidebar {
        position: fixed; top: 56px; left: 0; bottom: 0; width: 21rem;
        background: #000; border-right: 1px solid #1a1a1a;
        z-index: 999; padding: 0.5rem 0.75rem;
        display: flex; flex-direction: column;
    }

    .lib-header {
        display: flex; justify-content: space-between; align-items: center;
        color: #fff; font-weight: 700; font-size: 1rem;
        padding: 0.65rem 0.5rem;
    }

    .lib-card {
        background: #121212; border-radius: 8px; padding: 1rem;
        margin-top: 0.5rem;
    }

    .lib-card h4 { color: #fff; font-size: 0.95rem; margin: 0 0 0.35rem; font-weight: 700; }
    .lib-card p { color: #b3b3b3; font-size: 0.8rem; margin: 0 0 0.75rem; line-height: 1.4; }

    .lib-pill-btn {
        display: inline-block; background: #fff; color: #000;
        font-weight: 700; font-size: 0.85rem; padding: 0.45rem 1rem;
        border-radius: 500px;
    }

    .lib-nav-item {
        display: flex; align-items: center; gap: 0.75rem;
        padding: 0.55rem 0.5rem; border-radius: 4px;
        color: #b3b3b3; font-size: 0.9rem; margin: 0.15rem 0;
    }

    .lib-nav-item.active { background: #282828; color: #fff; }
    .lib-nav-item .dot {
        width: 40px; height: 40px; border-radius: 4px; flex-shrink: 0;
    }
    .lib-nav-item .dot.dw {
        background: linear-gradient(135deg, #1a472a, #2d1b4e);
    }

    .lib-footer {
        margin-top: auto; padding: 1rem 0.5rem;
        font-size: 0.62rem; color: #6a6a6a; line-height: 1.6;
    }

    .loop-panel-fixed {
        position: fixed; top: 56px; right: 0; bottom: 0; width: 25rem;
        background: #121212; border-left: 1px solid #282828;
        z-index: 998; overflow-y: auto; padding: 1.25rem;
    }

    .main-gradient {
        background: linear-gradient(180deg, #1f1f1f 0%, #121212 320px, #121212 100%);
        border-radius: 8px; padding: 1.5rem 1.5rem 2rem;
        min-height: calc(100vh - 5rem);
    }

    .section-head {
        display: flex; justify-content: space-between; align-items: baseline;
        margin-bottom: 1rem;
    }
    .section-head h2 { color: #fff; font-size: 1.5rem; font-weight: 700; margin: 0; }
    .section-head a { color: #b3b3b3; font-size: 0.82rem; font-weight: 600; text-decoration: none; }

    .card-row { display: flex; gap: 1rem; overflow-x: auto; padding-bottom: 0.5rem; }

    .song-card {
        flex: 0 0 180px; background: #181818; border-radius: 8px;
        padding: 1rem; cursor: pointer; transition: background 0.15s;
    }
    .song-card:hover { background: #282828; }
    .song-card .cover {
        width: 100%; aspect-ratio: 1; border-radius: 6px; margin-bottom: 1rem;
        background: linear-gradient(145deg, #1ed760, #509bf5 60%, #8c67ab);
    }
    .song-card .cover.alt { background: linear-gradient(145deg, #e13300, #7358ff); }
    .song-card .title { color: #fff; font-weight: 600; font-size: 0.95rem; margin: 0; }
    .song-card .sub { color: #b3b3b3; font-size: 0.82rem; margin: 0.35rem 0 0; }

    .pl-header {
        display: flex; gap: 1.5rem; align-items: flex-end; margin-bottom: 1.5rem;
    }
    .pl-cover {
        width: 232px; height: 232px; flex-shrink: 0; border-radius: 4px;
        background: linear-gradient(145deg, #1ed760 0%, #1db954 30%, #509bf5 70%, #8c67ab);
        box-shadow: 0 4px 60px rgba(0,0,0,0.5);
    }
    .pl-type { color: #fff; font-size: 0.8rem; font-weight: 600; margin: 0 0 0.5rem; }
    .pl-title { color: #fff; font-size: 3.5rem; font-weight: 900; margin: 0; line-height: 1.05; letter-spacing: -0.04em; }
    .pl-meta { color: #b3b3b3; font-size: 0.85rem; margin-top: 0.75rem; }
    .pl-meta strong { color: #fff; }

    .play-btn {
        width: 56px; height: 56px; background: #1db954; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        color: #000; font-size: 1.5rem; margin-top: 1.25rem;
        box-shadow: 0 8px 24px rgba(29,185,84,0.35);
    }

    .stale-strip {
        background: linear-gradient(90deg, rgba(29,185,84,0.15), rgba(29,185,84,0.05));
        border: 1px solid rgba(29,185,84,0.45);
        border-radius: 8px; padding: 0.85rem 1rem;
        margin-bottom: 1.25rem;
        display: flex; align-items: center; justify-content: space-between; gap: 1rem;
    }
    .stale-strip p { color: #fff; font-size: 0.9rem; font-weight: 600; margin: 0; }
    .stale-strip small { color: #b3b3b3; font-size: 0.78rem; display: block; margin-top: 0.15rem; font-weight: 400; }

    .track-table { width: 100%; border-collapse: collapse; }
    .track-table th {
        color: #b3b3b3; font-size: 0.72rem; font-weight: 400;
        text-align: left; padding: 0.35rem 0.75rem; border-bottom: 1px solid #282828;
    }
    .track-table td {
        padding: 0.55rem 0.75rem; border-bottom: 1px solid rgba(255,255,255,0.06);
        color: #b3b3b3; font-size: 0.88rem;
    }
    .track-table .t-title { color: #fff; }
    .lib-tag {
        display: inline-block; background: #3e3e3e; color: #b3b3b3;
        font-size: 0.62rem; padding: 0.1rem 0.35rem; border-radius: 3px;
        margin-left: 0.4rem; vertical-align: middle;
    }

    .panel-handle {
        width: 40px; height: 4px; background: #535353;
        border-radius: 4px; margin: 0 auto 1rem;
    }
    .panel-title { color: #fff; font-size: 1.15rem; font-weight: 700; margin: 0 0 0.25rem; }
    .panel-sub { color: #b3b3b3; font-size: 0.82rem; margin: 0 0 1rem; line-height: 1.4; }

    .loop-pill {
        display: inline-block; color: #1db954; border: 1px solid #1db954;
        background: rgba(29,185,84,0.1); border-radius: 500px;
        padding: 0.2rem 0.65rem; font-size: 0.72rem; font-weight: 600;
        margin-bottom: 0.5rem;
    }

    .pick-row {
        background: #181818; border-radius: 8px; padding: 0.75rem;
        margin-bottom: 0.5rem;
    }
    .pick-row .t { color: #fff; font-weight: 600; font-size: 0.88rem; margin: 0; }
    .pick-row .a { color: #b3b3b3; font-size: 0.78rem; margin: 0.1rem 0 0.4rem; }
    .pick-row .w { color: #d0d0d0; font-size: 0.74rem; line-height: 1.35; margin: 0.2rem 0; }
    .pick-row .w em { color: #1db954; font-style: normal; font-weight: 600; }

    .breadcrumb { color: #b3b3b3; font-size: 0.8rem; margin-bottom: 0.75rem; }
    .breadcrumb span { color: #1db954; }

    .stButton > button[kind="primary"] {
        background: #1db954 !important; color: #000 !important;
        border: none !important; font-weight: 700 !important;
        border-radius: 500px !important;
    }
    .stButton > button[kind="secondary"] {
        background: transparent !important; color: #fff !important;
        border: 1px solid #535353 !important; border-radius: 500px !important;
    }

    div[data-testid="stVerticalBlock"] > div:has(> div.loop-panel-marker) { display: none; }
</style>
"""

DW_TRACKS = [
    ("Blinding Lights", "The Weeknd", "After Hours", "3:20", True),
    ("As It Was", "Harry Styles", "Harry's House", "2:47", False),
    ("Flowers", "Miley Cyrus", "Endless Summer Vacation", "3:20", True),
    ("Cruel Summer", "Taylor Swift", "Lover", "2:58", False),
    ("Save Your Tears", "The Weeknd", "After Hours", "3:35", True),
    ("Espresso", "Sabrina Carpenter", "Espresso", "2:55", False),
    ("Starboy", "The Weeknd", "Starboy", "3:50", True),
    ("Die For You", "The Weeknd", "Starboy", "4:20", False),
]

TRENDING = [
    ("Ban Ja Tu", "Charan Preet, Badshah", "alt"),
    ("Die With A Smile", "Lady Gaga, Bruno Mars", ""),
    ("Ordinary", "Alex Warren", "alt"),
    ("Show Me Love", "WizTheMc, bees & honey", ""),
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
        "lb_panel": False,
        "lb_step": "entry",
        "lb_frustration": "",
        "lb_diagnosis": None,
        "lb_openness": "Nudge me slightly outside my comfort zone",
        "lb_recommendations": None,
        "lb_trust_score": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def render_chrome(screen: str) -> None:
    home_active = screen == "home"
    dw_active = screen == "dw"

    st.markdown(
        f"""
        <div class="spotify-topbar">
          <div class="logo">{SPOTIFY_LOGO}</div>
          <div class="home-btn">⌂</div>
          <div class="search-pill">🔍 &nbsp; What do you want to play?</div>
          <div class="topbar-right">
            <span class="premium">Premium</span>
            <span>Support</span>
            <span>Download</span>
            <span>Install App</span>
            <span class="user-chip">● Demo User</span>
          </div>
        </div>
        <div class="spotify-lib-sidebar">
          <div class="lib-header">Your Library <span style="color:#b3b3b3">+</span></div>
          <div class="lib-nav-item {"active" if home_active else ""}">
            <span>⌂</span> Home
          </div>
          <div class="lib-nav-item {"active" if dw_active else ""}">
            <div class="dot dw"></div>
            <div><div style="color:#fff;font-weight:600">Discover Weekly</div>
            <div style="font-size:0.75rem">Playlist · Spotify</div></div>
          </div>
          <div class="lib-card">
            <h4>Made For You</h4>
            <p>Loop Break lives here — when Discover Weekly feels like a rerun, open the playlist and break the loop.</p>
            <span class="lib-pill-btn">Growth prototype</span>
          </div>
          <div class="lib-footer">
            Legal · Privacy · Cookies · About Ads<br>
            🌐 English
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_home() -> None:
    trending = ""
    for title, artist, alt in TRENDING:
        trending += f"""
        <div class="song-card">
          <div class="cover {alt}"></div>
          <p class="title">{title}</p>
          <p class="sub">{artist}</p>
        </div>"""

    st.markdown(
        f"""
        <div class="main-gradient">
          <div class="section-head"><h2>Made For You</h2><a href="#">Show all</a></div>
          <div class="card-row">
            <div class="song-card">
              <div class="cover"></div>
              <p class="title">Discover Weekly</p>
              <p class="sub">Your weekly mixtape of fresh music</p>
            </div>
            <div class="song-card">
              <div class="cover alt"></div>
              <p class="title">Release Radar</p>
              <p class="sub">Catch all the latest from artists you follow</p>
            </div>
            <div class="song-card">
              <div class="cover"></div>
              <p class="title">Daily Mix 1</p>
              <p class="sub">Indie · Alt · The Strokes and more</p>
            </div>
          </div>
          <div class="section-head" style="margin-top:2rem"><h2>Trending songs</h2><a href="#">Show all</a></div>
          <div class="card-row">{trending}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Open Discover Weekly", type="primary", key="open_dw"):
        st.session_state["lb_screen"] = "dw"
        st.rerun()


def render_dw_playlist() -> None:
    rows = ""
    for i, (song, artist, album, dur, in_lib) in enumerate(DW_TRACKS, start=1):
        tag = '<span class="lib-tag">In your library</span>' if in_lib else ""
        rows += f"""
        <tr>
          <td>{i}</td>
          <td class="t-title">{song}{tag}<br><span style="color:#b3b3b3;font-size:0.8rem">{artist}</span></td>
          <td>{album}</td>
          <td>{dur}</td>
        </tr>"""

    st.markdown(
        f"""
        <div class="main-gradient">
          <div class="breadcrumb">Home / Made For You / <span>Discover Weekly</span></div>
          <div class="pl-header">
            <div class="pl-cover"></div>
            <div>
              <p class="pl-type">Playlist</p>
              <h1 class="pl-title">Discover Weekly</h1>
              <p class="pl-meta"><strong>Spotify</strong> · 30 songs · about 1 hr 45 min · Updated Monday</p>
              <div class="play-btn">▶</div>
            </div>
          </div>
          <div class="stale-strip">
            <div>
              <p>This week feels familiar</p>
              <small>3 songs already in your library · Loop Break can diagnose why and reset your discovery.</small>
            </div>
          </div>
          <table class="track-table">
            <thead><tr><th>#</th><th>Title</th><th>Album</th><th>⏱</th></tr></thead>
            <tbody>{rows}</tbody>
          </table>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not st.session_state["lb_panel"]:
        if st.button("Break the loop", type="primary", key="break_loop_btn"):
            st.session_state["lb_panel"] = True
            st.session_state["lb_step"] = "entry"
            st.rerun()
    if st.button("← Back to Home", type="secondary", key="dw_back_home"):
        st.session_state["lb_screen"] = "home"
        st.session_state["lb_panel"] = False
        st.rerun()


def render_panel_entry() -> None:
    st.markdown(
        """
        <div class="panel-handle"></div>
        <p class="panel-title">Loop Break</p>
        <p class="panel-sub">In-product AI reset when Discover Weekly stops feeling new.
        Describe what went wrong — we diagnose your loop type.</p>
        """,
        unsafe_allow_html=True,
    )
    frustration = st.text_area(
        "f",
        value=st.session_state["lb_frustration"],
        height=88,
        placeholder="What felt off about this week's Discover Weekly?",
        label_visibility="collapsed",
    )
    for i, ex in enumerate(EXAMPLE_PROMPTS[:2]):
        if st.button(ex[:44] + "…", key=f"pex_{i}"):
            st.session_state["lb_frustration"] = ex
            st.rerun()
    if st.button("Run Loop Diagnostic", type="primary", use_container_width=True):
        if not frustration or len(frustration.strip()) < 15:
            st.error("Enter at least 15 characters.")
            return
        st.session_state["lb_frustration"] = frustration.strip()
        api_key = get_secret("GROQ_API_KEY")
        with st.spinner("Diagnosing…"):
            try:
                d = (
                    classify_loop_groq(frustration.strip(), api_key)
                    if api_key
                    else classify_loop_keyword(frustration.strip())
                )
            except Exception as exc:
                st.warning(f"Fallback: {exc}")
                d = classify_loop_keyword(frustration.strip())
        st.session_state["lb_diagnosis"] = d
        st.session_state["lb_step"] = "diagnostic"
        st.rerun()
    if st.button("Close", type="secondary", use_container_width=True):
        st.session_state["lb_panel"] = False
        st.session_state["lb_step"] = "entry"
        st.rerun()


def render_panel_diagnostic() -> None:
    d = st.session_state["lb_diagnosis"]
    lt = d["loop_type"]
    label = LOOP_LABELS[lt]
    st.markdown(
        f"""
        <div class="loop-pill">{label}</div>
        <p class="panel-title">Loop Diagnostic</p>
        <p class="panel-sub">{d.get("diagnosis_summary", LOOP_DESCRIPTIONS[lt])}</p>
        <p class="panel-sub"><strong style="color:#1db954">Intervention:</strong>
        {d.get("intervention_preview", INTERVENTIONS[lt])}</p>
        """,
        unsafe_allow_html=True,
    )
    mood = st.selectbox(
        "Mood",
        ["Calm / low energy", "Energetic", "Melancholy", "Focused", "Open to anything"],
        index=4,
        label_visibility="collapsed",
    )
    openness = st.select_slider(
        "Novelty",
        [
            "Stay close to my taste",
            "Nudge me slightly outside my comfort zone",
            "Surprise me — break the loop completely",
        ],
        value=st.session_state["lb_openness"],
        label_visibility="collapsed",
    )
    if st.button("Get 3 Loop Break picks", type="primary", use_container_width=True):
        st.session_state["lb_openness"] = openness
        api_key = get_secret("GROQ_API_KEY")
        with st.spinner("Building picks…"):
            try:
                recs = (
                    generate_loop_break_groq(lt, st.session_state["lb_frustration"], mood, openness, api_key)
                    if api_key
                    else generate_loop_break_keyword(lt, st.session_state["lb_frustration"], mood, openness)
                )
            except Exception as exc:
                st.warning(f"Fallback: {exc}")
                recs = generate_loop_break_keyword(lt, st.session_state["lb_frustration"], mood, openness)
        st.session_state["lb_recommendations"] = recs
        st.session_state["lb_step"] = "results"
        st.rerun()
    if st.button("← Back", type="secondary", use_container_width=True):
        st.session_state["lb_step"] = "entry"
        st.rerun()


def render_panel_results() -> None:
    d = st.session_state["lb_diagnosis"]
    recs = st.session_state["lb_recommendations"]
    label = LOOP_LABELS[d["loop_type"]]
    picks = ""
    for i, t in enumerate(recs.get("tracks", [])[:3], 1):
        picks += f"""
        <div class="pick-row">
          <p class="t">{i}. {t.get("song","")}</p>
          <p class="a">{t.get("artist","")}</p>
          <p class="w"><em>Why it fits:</em> {t.get("why_fit","")}</p>
          <p class="w"><em>Not last DW:</em> {t.get("novelty_rationale","")}</p>
        </div>"""
    st.markdown(
        f"""
        <div class="loop-pill">{label} reset</div>
        <p class="panel-title">{recs.get("intervention_headline", "Your Loop Break")}</p>
        <p class="panel-sub">{recs.get("loop_break_message", "")}</p>
        {picks}
        """,
        unsafe_allow_html=True,
    )
    for t in recs.get("tracks", [])[:3]:
        st.link_button(
            f"▶  {t.get('song','')} — {t.get('artist','')}",
            spotify_search_url(t.get("artist", ""), t.get("song", "")),
            use_container_width=True,
        )
    trust = st.slider("Trust vs last DW", 1, 5, 4, label_visibility="collapsed")
    st.caption(f"Trust score: **{trust}/5**")
    if st.button("Done", type="primary", use_container_width=True):
        st.session_state["lb_trust_score"] = trust
        st.session_state["lb_panel"] = False
        st.session_state["lb_step"] = "entry"
        st.session_state["lb_frustration"] = ""
        st.session_state["lb_diagnosis"] = None
        st.session_state["lb_recommendations"] = None
        st.rerun()


def render_grader_sidebar() -> None:
    with st.sidebar:
        st.markdown("### Demo")
        st.caption("Spotify web UI · Loop Break in right panel")
        if get_secret("GROQ_API_KEY"):
            st.success("Groq connected")
        else:
            st.warning("No API key")
        with st.expander("Why AI?"):
            st.caption(
                "Recsys can't diagnose why DW failed. AI classifies loop type, "
                "matches intervention, explains 3 picks. Same UI — new in-product moment."
            )
        if st.session_state.get("lb_trust_score"):
            st.metric("Trust", f"{st.session_state['lb_trust_score']}/5")
        if st.button("Reset demo"):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()


def main() -> None:
    st.set_page_config(page_title="Spotify", page_icon="🎵", layout="wide", initial_sidebar_state="collapsed")
    st.markdown(SPOTIFY_CSS, unsafe_allow_html=True)
    init_session()
    render_grader_sidebar()

    screen = st.session_state["lb_screen"]
    panel = st.session_state["lb_panel"]
    render_chrome(screen)

    if panel:
        st.markdown(
            """
            <style>
            .main .block-container { padding-right: 26rem !important; }
            div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:last-child {
                position: fixed !important;
                top: 56px !important;
                right: 0 !important;
                width: 25rem !important;
                max-width: 34vw !important;
                height: calc(100vh - 56px) !important;
                background: #121212 !important;
                border-left: 1px solid #282828 !important;
                padding: 1.25rem 1.25rem 2rem !important;
                overflow-y: auto !important;
                z-index: 997 !important;
            }
            div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:last-child > div {
                background: transparent !important;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
        left, right = st.columns([1.6, 1], gap="medium")
        with left:
            render_dw_playlist()
        with right:
            step = st.session_state["lb_step"]
            if step == "entry":
                render_panel_entry()
            elif step == "diagnostic":
                render_panel_diagnostic()
            else:
                render_panel_results()
    else:
        if screen == "home":
            render_home()
        else:
            render_dw_playlist()

    st.markdown(
        '<p style="text-align:center;color:#535353;font-size:0.68rem;margin-top:1rem">'
        "Fellowship prototype — not affiliated with Spotify AB</p>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
