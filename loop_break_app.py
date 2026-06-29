"""Part 4: Loop Break inside Spotify web player (screenshot-accurate layout)."""

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
<svg viewBox="0 0 24 24" width="32" height="32" fill="#1ed760">
  <path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.26-1.26 11.28-1.02 15.721 1.621.539.3.719 1.02.419 1.56-.299.421-1.02.599-1.559.3z"/>
</svg>
"""

CSS = """
<style>
    #MainMenu, footer, header {visibility: hidden;}
    section[data-testid="stSidebar"] {display: none !important;}
    .stApp {background: #121212;}

    .main .block-container {
        padding: 64px 24px 100px 362px !important;
        max-width: 100% !important;
        margin: 0 !important;
    }

    .ui-top {
        position: fixed; top: 0; left: 0; right: 0; height: 64px;
        background: #000; z-index: 200; display: flex; align-items: center;
        gap: 16px; padding: 0 24px; pointer-events: none;
    }
    .ui-home {
        width: 48px; height: 48px; background: #1f1f1f; border-radius: 50%;
        display: flex; align-items: center; justify-content: center; color: #fff;
    }
    .ui-search {
        flex: 0 1 480px; height: 48px; background: #1f1f1f; border-radius: 500px;
        display: flex; align-items: center; padding: 0 16px; gap: 12px;
        color: #b3b3b3; font-size: 14px;
    }
    .ui-search .lib {margin-left: auto; opacity: 0.8;}
    .ui-top-links {
        margin-left: auto; display: flex; align-items: center; gap: 28px;
        color: #b3b3b3; font-size: 14px; font-weight: 600;
    }
    .ui-top-links .sep {width: 1px; height: 24px; background: #282828;}
    .ui-login {
        background: #fff; color: #000; font-weight: 700; padding: 12px 32px;
        border-radius: 500px; font-size: 16px;
    }

    .ui-left {
        position: fixed; top: 0; left: 0; width: 350px; bottom: 0;
        background: #000; z-index: 150; padding: 8px; pointer-events: none;
        display: flex; flex-direction: column;
    }
    .ui-lib-box {
        background: #121212; border-radius: 8px; flex: 1;
        display: flex; flex-direction: column; padding: 4px 0;
    }
    .ui-lib-head {
        display: flex; justify-content: space-between; align-items: center;
        padding: 12px 16px; color: #fff; font-weight: 700; font-size: 16px;
    }
    .ui-podcast {
        margin: 8px; background: #181818; border-radius: 8px; padding: 16px;
    }
    .ui-podcast h4 {color: #fff; font-size: 14px; margin: 0 0 8px; font-weight: 700;}
    .ui-podcast p {color: #b3b3b3; font-size: 13px; margin: 0 0 16px; line-height: 1.4;}
    .ui-podcast-btn {
        display: inline-block; background: #fff; color: #000; font-weight: 700;
        font-size: 14px; padding: 8px 16px; border-radius: 500px;
    }
    .ui-left-foot {
        padding: 16px; font-size: 10px; color: #6a6a6a; line-height: 1.8;
    }
    .ui-lang {
        display: inline-flex; align-items: center; gap: 6px;
        border: 1px solid #6a6a6a; border-radius: 500px; padding: 6px 12px;
        color: #fff; font-size: 12px; margin-top: 12px;
    }

    .ui-player {
        position: fixed; bottom: 0; left: 0; right: 0; height: 72px;
        background: linear-gradient(90deg, #5038a0, #1e3264);
        z-index: 200; pointer-events: none;
        display: flex; align-items: center; padding: 0 24px; color: #fff; font-size: 13px;
    }

    .main-view {min-height: 70vh;}
    .row-head {
        display: flex; justify-content: space-between; align-items: center;
        margin: 24px 0 16px;
    }
    .row-head h2 {color: #fff; font-size: 24px; font-weight: 700; margin: 0;}
    .row-head a {color: #b3b3b3; font-size: 13px; font-weight: 600; text-decoration: none;}

    .h-scroll {display: flex; gap: 24px; overflow-x: auto; padding-bottom: 8px;}
    .t-card {flex: 0 0 180px;}
    .t-cover {
        width: 180px; height: 180px; border-radius: 6px; margin-bottom: 16px;
        background-size: cover; background-position: center;
        box-shadow: 0 4px 16px rgba(0,0,0,0.4);
    }
    .t-title {color: #fff; font-size: 16px; font-weight: 600; margin: 0;}
    .t-artist {color: #b3b3b3; font-size: 14px; margin: 4px 0 0;}

    .a-card {flex: 0 0 180px; text-align: center;}
    .a-img {
        width: 180px; height: 180px; border-radius: 50%; margin-bottom: 16px;
        background-size: cover; background-position: center;
    }

    .step-hint {
        background: #282828; border-left: 3px solid #1db954;
        padding: 10px 14px; margin-bottom: 16px; border-radius: 4px;
        color: #fff; font-size: 13px;
    }

    .pl-hero {display: flex; gap: 24px; align-items: flex-end; margin-bottom: 24px;}
    .pl-cover {
        width: 232px; height: 232px; border-radius: 4px; flex-shrink: 0;
        background: linear-gradient(145deg, #1ed760, #509bf5 55%, #8c67ab);
        box-shadow: 0 4px 60px rgba(0,0,0,0.5);
    }
    .pl-kicker {color: #fff; font-size: 14px; font-weight: 600; margin: 0;}
    .pl-name {color: #fff; font-size: clamp(48px,6vw,96px); font-weight: 900; margin: 8px 0 0; line-height: 1;}
    .pl-meta {color: #b3b3b3; font-size: 14px; margin-top: 16px;}

    .banner {
        background: #1a2e1a; border: 1px solid #1db954; border-radius: 8px;
        padding: 16px 20px; margin-bottom: 20px;
    }
    .banner strong {color: #fff; font-size: 15px;}
    .banner p {color: #b3b3b3; font-size: 13px; margin: 6px 0 0;}

    .tracks {width: 100%; border-collapse: collapse;}
    .tracks th {color: #b3b3b3; font-weight: 400; font-size: 12px; text-align: left; padding: 8px 16px; border-bottom: 1px solid #282828;}
    .tracks td {padding: 10px 16px; border-bottom: 1px solid rgba(255,255,255,0.06); color: #b3b3b3; font-size: 14px;}
    .tracks .name {color: #fff;}
    .tag {background: #3e3e3e; color: #b3b3b3; font-size: 10px; padding: 2px 6px; border-radius: 3px; margin-left: 6px;}

    .loop-box {
        background: #181818; border-radius: 8px; padding: 24px; max-width: 640px;
    }
    .loop-box h2 {color: #fff; font-size: 28px; margin: 0 0 8px;}
    .loop-box p {color: #b3b3b3; font-size: 14px; line-height: 1.5;}
    .pill {
        display: inline-block; color: #1db954; border: 1px solid #1db954;
        border-radius: 500px; padding: 4px 12px; font-size: 12px; font-weight: 600;
        margin-bottom: 12px;
    }
    .pick {
        background: #282828; border-radius: 8px; padding: 14px; margin: 10px 0;
    }
    .pick .s {color: #fff; font-weight: 600; margin: 0;}
    .pick .ar {color: #b3b3b3; font-size: 13px; margin: 2px 0 8px;}
    .pick .w {color: #ccc; font-size: 12px; margin: 4px 0;}
    .pick em {color: #1db954; font-style: normal; font-weight: 600;}

    .nav-row {display: flex; gap: 12px; margin-bottom: 16px; flex-wrap: wrap;}

    .stButton > button[kind="primary"] {
        background: #1db954 !important; color: #000 !important;
        border: none !important; font-weight: 700 !important; border-radius: 500px !important;
    }
    .stButton > button[kind="secondary"] {
        background: #fff !important; color: #000 !important;
        border: none !important; font-weight: 600 !important; border-radius: 500px !important;
    }
</style>
"""

TRENDING = [
    ("Ban Ja Tu", "Charan Preet, Badshah", "#c45c26"),
    ("Die With A Smile", "Lady Gaga, Bruno Mars", "#8b4513"),
    ("Ordinary", "Alex Warren", "#2f4f6f"),
    ("Show Me Love", "WizTheMc, bees & honey", "#6b3fa0"),
    ("Low Fade", "Karan Aujla, Ikky", "#1a1a2e"),
    ("Tu Meri Main Tera", "Karan Aujla, Ikky", "#4a1942"),
]

ARTISTS = [
    ("Pritam", "#2d5a27"),
    ("Karan Aujla", "#1f1f1f"),
    ("Sachin-Jigar", "#5c4033"),
    ("Ikky", "#264653"),
    ("Badshah", "#6b2d5c"),
    ("Charan Preet", "#3d3d3d"),
]

DW_TRACKS = [
    ("Blinding Lights", "The Weeknd", "After Hours", "3:20", True),
    ("As It Was", "Harry Styles", "Harry's House", "2:47", False),
    ("Flowers", "Miley Cyrus", "Endless Summer Vacation", "3:20", True),
    ("Cruel Summer", "Taylor Swift", "Lover", "2:58", False),
    ("Save Your Tears", "The Weeknd", "After Hours", "3:35", True),
    ("Espresso", "Sabrina Carpenter", "Espresso", "2:55", False),
]

EXAMPLES = [
    "Discover Weekly had songs I already saved — feels like my library again.",
    "Same indie mood every Monday. I want something new but still me.",
]


def get_secret(key: str) -> str | None:
    try:
        v = st.secrets.get(key)
        if v:
            return v
    except StreamlitSecretNotFoundError:
        pass
    return os.getenv(key)


def init() -> None:
    for k, v in {
        "view": "home",
        "step": "entry",
        "frustration": "",
        "diagnosis": None,
        "openness": "Nudge me slightly outside my comfort zone",
        "recs": None,
    }.items():
        if k not in st.session_state:
            st.session_state[k] = v


def chrome(active: str) -> None:
    """Fixed Spotify shell matching shared screenshot."""
    st.markdown(
        f"""
        <div class="ui-left">
          <div class="ui-lib-box">
            <div class="ui-lib-head">Your Library <span style="color:#b3b3b3;font-size:20px">+</span></div>
            <div class="ui-podcast">
              <h4>Let's find some podcasts to follow</h4>
              <p>We'll keep you updated on new episodes</p>
              <span class="ui-podcast-btn">Browse podcasts</span>
            </div>
          </div>
          <div class="ui-left-foot">
            Legal · Safety &amp; Privacy Center · Privacy Policy · Cookies · About Ads · Accessibility<br>
            <span class="ui-lang">🌐 English</span>
          </div>
        </div>
        <div class="ui-top">
          <div>{SPOTIFY_LOGO}</div>
          <div class="ui-home">⌂</div>
          <div class="ui-search">🔍 &nbsp; What do you want to play? <span class="lib">📚</span></div>
          <div class="ui-top-links">
            <span>Premium</span><span>Support</span><span>Download</span>
            <span class="sep"></span>
            <span>Install App</span><span>Sign up</span>
            <span class="ui-login">Log in</span>
          </div>
        </div>
        <div class="ui-player">Fellowship prototype — Loop Break feature demo · not affiliated with Spotify AB</div>
        """,
        unsafe_allow_html=True,
    )


def hint(text: str) -> None:
    st.markdown(f'<div class="step-hint">{text}</div>', unsafe_allow_html=True)


def nav_buttons() -> None:
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("Home", key="nav_home", use_container_width=True):
            st.session_state["view"] = "home"
            st.session_state["step"] = "entry"
            st.rerun()
    with c2:
        if st.button("Discover Weekly", key="nav_dw", use_container_width=True):
            st.session_state["view"] = "dw"
            st.rerun()
    with c3:
        if st.button("Loop Break", key="nav_lb", use_container_width=True):
            st.session_state["view"] = "loop"
            st.session_state["step"] = "entry"
            st.rerun()
    with c4:
        if st.button("Reset", key="nav_reset", use_container_width=True):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()


def page_home() -> None:
    hint("<b>Step 1:</b> Browse Spotify Home (matches live web UI). Click <b>Discover Weekly</b> above or the button below.")
    if st.button("Open Discover Weekly →", type="primary", key="go_dw"):
        st.session_state["view"] = "dw"
        st.rerun()

    cards = ""
    for title, artist, color in TRENDING:
        cards += f"""
        <div class="t-card">
          <div class="t-cover" style="background:{color}"></div>
          <p class="t-title">{title}</p>
          <p class="t-artist">{artist}</p>
        </div>"""

    artists = ""
    for name, color in ARTISTS:
        artists += f"""
        <div class="a-card">
          <div class="a-img" style="background:{color}"></div>
          <p class="t-title">{name}</p>
        </div>"""

    st.markdown(
        f"""
        <div class="main-view">
          <div class="row-head"><h2>Trending songs</h2><a href="#">Show all</a></div>
          <div class="h-scroll">{cards}</div>
          <div class="row-head"><h2>Popular artists</h2><a href="#">Show all</a></div>
          <div class="h-scroll">{artists}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def page_dw() -> None:
    hint("<b>Step 2:</b> Discover Weekly playlist — note <b>In your library</b> tags. Click <b>Loop Break</b> above or the button below.")
    c1, c2 = st.columns([1, 1])
    with c1:
        if st.button("Break the loop →", type="primary", key="go_loop"):
            st.session_state["view"] = "loop"
            st.session_state["step"] = "entry"
            st.rerun()
    with c2:
        if st.button("← Home", key="dw_home"):
            st.session_state["view"] = "home"
            st.rerun()

    rows = ""
    for i, (song, artist, album, dur, lib) in enumerate(DW_TRACKS, 1):
        tag = '<span class="tag">In your library</span>' if lib else ""
        rows += f"<tr><td>{i}</td><td class='name'>{song}{tag}<br><span style='color:#b3b3b3;font-size:13px'>{artist}</span></td><td>{album}</td><td>{dur}</td></tr>"

    st.markdown(
        f"""
        <div class="main-view">
          <div class="pl-hero">
            <div class="pl-cover"></div>
            <div>
              <p class="pl-kicker">Playlist</p>
              <h1 class="pl-name">Discover Weekly</h1>
              <p class="pl-meta">Spotify · 30 songs · Updated Monday</p>
            </div>
          </div>
          <div class="banner">
            <strong>This week feels familiar</strong>
            <p>3 songs already in your library. Loop Break diagnoses why and suggests 3 explained resets.</p>
          </div>
          <table class="tracks">
            <thead><tr><th>#</th><th>Title</th><th>Album</th><th>⏱</th></tr></thead>
            <tbody>{rows}</tbody>
          </table>
        </div>
        """,
        unsafe_allow_html=True,
    )


def page_loop() -> None:
    step = st.session_state["step"]

    if step == "entry":
        hint("<b>Step 3:</b> Describe DW frustration → <b>Run Loop Diagnostic</b>.")
        st.markdown(
            '<div class="loop-box"><h2>Loop Break</h2><p>AI reset when Discover Weekly stops feeling new.</p></div>',
            unsafe_allow_html=True,
        )
        if st.button("← Back to Discover Weekly", key="lb_back_dw"):
            st.session_state["view"] = "dw"
            st.rerun()

        text = st.text_area(
            "msg",
            value=st.session_state["frustration"],
            height=100,
            placeholder="What felt off about this week's Discover Weekly?",
            label_visibility="collapsed",
        )
        for i, ex in enumerate(EXAMPLES):
            if st.button(ex[:50] + "…", key=f"ex{i}"):
                st.session_state["frustration"] = ex
                st.rerun()
        if st.button("Run Loop Diagnostic", type="primary", key="diag"):
            if len(text.strip()) < 15:
                st.error("Enter at least 15 characters.")
                return
            st.session_state["frustration"] = text.strip()
            key = get_secret("GROQ_API_KEY")
            with st.spinner("Analyzing…"):
                try:
                    d = classify_loop_groq(text.strip(), key) if key else classify_loop_keyword(text.strip())
                except Exception:
                    d = classify_loop_keyword(text.strip())
            st.session_state["diagnosis"] = d
            st.session_state["step"] = "diagnostic"
            st.rerun()

    elif step == "diagnostic":
        hint("<b>Step 3b:</b> Review loop type → <b>Get 3 Loop Break picks</b>.")
        d = st.session_state["diagnosis"]
        lt = d["loop_type"]
        st.markdown(
            f"""
            <div class="loop-box">
              <span class="pill">{LOOP_LABELS[lt]}</span>
              <h2>Loop Diagnostic</h2>
              <p>{d.get("diagnosis_summary", LOOP_DESCRIPTIONS[lt])}</p>
              <p><b style="color:#1db954">Intervention:</b> {d.get("intervention_preview", INTERVENTIONS[lt])}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        mood = st.selectbox("mood", ["Calm", "Energetic", "Melancholy", "Focused", "Open to anything"], index=4, label_visibility="collapsed")
        openness = st.select_slider(
            "nov",
            ["Stay close", "Nudge outside comfort zone", "Surprise me completely"],
            value="Nudge outside comfort zone",
            label_visibility="collapsed",
        )
        if st.button("Get 3 Loop Break picks", type="primary", key="picks"):
            key = get_secret("GROQ_API_KEY")
            with st.spinner("Building picks…"):
                try:
                    r = (
                        generate_loop_break_groq(lt, st.session_state["frustration"], mood, openness, key)
                        if key
                        else generate_loop_break_keyword(lt, st.session_state["frustration"], mood, openness)
                    )
                except Exception:
                    r = generate_loop_break_keyword(lt, st.session_state["frustration"], mood, openness)
            st.session_state["recs"] = r
            st.session_state["step"] = "results"
            st.rerun()
        if st.button("← Back", key="diag_back"):
            st.session_state["step"] = "entry"
            st.rerun()

    else:
        hint("<b>Step 4:</b> Review 3 explained picks → rate trust → Done.")
        d = st.session_state["diagnosis"]
        r = st.session_state["recs"]
        lt = LOOP_LABELS[d["loop_type"]]
        picks = ""
        for i, t in enumerate(r.get("tracks", [])[:3], 1):
            picks += f"""
            <div class="pick">
              <p class="s">{i}. {t.get('song','')}</p>
              <p class="ar">{t.get('artist','')}</p>
              <p class="w"><em>Why it fits:</em> {t.get('why_fit','')}</p>
              <p class="w"><em>Not last DW:</em> {t.get('novelty_rationale','')}</p>
            </div>"""
        st.markdown(
            f"""
            <div class="loop-box">
              <span class="pill">{lt} reset</span>
              <h2>{r.get('intervention_headline', 'Your Loop Break')}</h2>
              <p>{r.get('loop_break_message', '')}</p>
            </div>
            {picks}
            """,
            unsafe_allow_html=True,
        )
        for t in r.get("tracks", [])[:3]:
            st.link_button(
                f"▶ {t.get('song','')} — {t.get('artist','')}",
                spotify_search_url(t.get("artist", ""), t.get("song", "")),
                use_container_width=True,
            )
        trust = st.slider("trust", 1, 5, 4, label_visibility="collapsed")
        st.caption(f"Trust vs last Discover Weekly: **{trust}/5**")
        if st.button("Done — back to Home", type="primary", key="done"):
            st.session_state["view"] = "home"
            st.session_state["step"] = "entry"
            st.session_state["frustration"] = ""
            st.session_state["diagnosis"] = None
            st.session_state["recs"] = None
            st.rerun()


def main() -> None:
    st.set_page_config(page_title="Spotify — Web Player", layout="wide")
    st.markdown(CSS, unsafe_allow_html=True)
    init()
    chrome(st.session_state["view"])

    st.markdown('<div class="nav-row">', unsafe_allow_html=True)
    nav_buttons()
    st.markdown("</div>", unsafe_allow_html=True)

    view = st.session_state["view"]
    if view == "home":
        page_home()
    elif view == "dw":
        page_dw()
    else:
        page_loop()


if __name__ == "__main__":
    main()
