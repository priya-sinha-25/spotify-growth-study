"""Part 4: Loop Break — Spotify web UI (Streamlit-native layout, no overlap)."""

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

CSS = """
<style>
    #MainMenu, footer, header {visibility: hidden;}
    section[data-testid="stSidebar"] {display: none !important;}
    .stApp {background: #121212;}
    .main .block-container {padding: 1rem 2rem 2rem; max-width: 1400px;}

    .sb-box {background: #000; border-radius: 8px; padding: 12px; min-height: 520px;}
    .sb-title {color: #fff; font-weight: 700; font-size: 16px; margin-bottom: 12px;}
    .sb-card {background: #181818; border-radius: 8px; padding: 16px; margin-top: 8px;}
    .sb-card h4 {color: #fff; font-size: 14px; margin: 0 0 8px;}
    .sb-card p {color: #b3b3b3; font-size: 12px; margin: 0 0 12px; line-height: 1.4;}
    .sb-foot {color: #6a6a6a; font-size: 10px; margin-top: 24px; line-height: 1.6;}

    .top-row {background: #000; border-radius: 8px; padding: 12px 20px; margin-bottom: 16px;
              display: flex; align-items: center; gap: 16px; flex-wrap: wrap;}
    .top-row .logo {color: #1ed760; font-weight: 900; font-size: 22px;}
    .top-search {flex: 1; min-width: 200px; background: #1f1f1f; border-radius: 500px;
                 padding: 10px 16px; color: #b3b3b3; font-size: 14px;}
    .top-links {color: #b3b3b3; font-size: 13px; font-weight: 600;}

    .main-pane {background: linear-gradient(180deg, #1f1f1f 0%, #121212 280px); border-radius: 8px;
                padding: 20px 24px; min-height: 520px;}
    .sec-title {color: #fff; font-size: 22px; font-weight: 700; margin: 20px 0 12px;}
    .cards {display: flex; gap: 16px; flex-wrap: wrap;}
    .card {width: 150px;}
    .card-img {width: 150px; height: 150px; border-radius: 6px; margin-bottom: 10px;}
    .card-t {color: #fff; font-size: 14px; font-weight: 600; margin: 0;}
    .card-s {color: #b3b3b3; font-size: 12px; margin: 4px 0 0;}

    .pl-row {display: flex; gap: 20px; align-items: flex-end; flex-wrap: wrap;}
    .pl-art {width: 180px; height: 180px; border-radius: 4px;
             background: linear-gradient(145deg, #1ed760, #509bf5, #8c67ab);}
    .pl-h {color: #fff; font-size: 42px; font-weight: 900; margin: 4px 0;}
    .pl-sub {color: #b3b3b3; font-size: 14px;}

    .banner {background: #1a2e1a; border: 1px solid #1db954; border-radius: 8px;
             padding: 14px 16px; margin: 16px 0;}
    .banner b {color: #fff;}
    .banner span {color: #b3b3b3; font-size: 13px;}

    .track {display: flex; gap: 12px; padding: 8px 0; border-bottom: 1px solid #282828;
            color: #b3b3b3; font-size: 13px;}
    .track .n {color: #fff; font-weight: 500;}
    .tag {background: #3e3e3e; font-size: 10px; padding: 2px 6px; border-radius: 3px; margin-left: 6px;}

    .loop-h {color: #fff; font-size: 26px; font-weight: 700; margin: 0 0 8px;}
    .loop-p {color: #b3b3b3; font-size: 14px; margin-bottom: 16px;}
    .pill {display: inline-block; color: #1db954; border: 1px solid #1db954; border-radius: 500px;
           padding: 4px 10px; font-size: 12px; font-weight: 600; margin-bottom: 10px;}
    .pick {background: #181818; border-radius: 8px; padding: 12px; margin: 8px 0;}
    .pick b {color: #fff;}
    .pick small {color: #b3b3b3;}

    .player {background: linear-gradient(90deg, #5038a0, #1e3264); border-radius: 8px;
             padding: 12px 16px; margin-top: 16px; color: #fff; font-size: 12px;}

    .stButton > button[kind="primary"] {
        background: #1db954 !important; color: #000 !important; font-weight: 700 !important;
        border: none !important; border-radius: 500px !important;
    }
</style>
"""

TRENDING = [
    ("Ban Ja Tu", "Charan Preet, Badshah", "#c45c26"),
    ("Die With A Smile", "Lady Gaga, Bruno Mars", "#8b4513"),
    ("Ordinary", "Alex Warren", "#2f4f6f"),
    ("Show Me Love", "WizTheMc", "#6b3fa0"),
]

ARTISTS = [
    ("Pritam", "#2d5a27"),
    ("Karan Aujla", "#1f1f1f"),
    ("Badshah", "#6b2d5c"),
    ("Ikky", "#264653"),
]

DW = [
    ("Blinding Lights", "The Weeknd", True),
    ("As It Was", "Harry Styles", False),
    ("Flowers", "Miley Cyrus", True),
    ("Cruel Summer", "Taylor Swift", False),
    ("Save Your Tears", "The Weeknd", True),
    ("Espresso", "Sabrina Carpenter", False),
]

EXAMPLES = [
    "Discover Weekly had songs I already saved — feels like my library again.",
    "Same indie mood every Monday — I want something new but still me.",
]


def secret(key: str) -> str | None:
    try:
        v = st.secrets.get(key)
        if v:
            return v
    except StreamlitSecretNotFoundError:
        pass
    return os.getenv(key)


def init() -> None:
    defaults = {"view": "home", "step": "entry", "text": "", "dx": None, "recs": None}
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def topbar() -> None:
    st.markdown(
        """
        <div class="top-row">
          <span class="logo">♫ Spotify</span>
          <div class="top-search">🔍  What do you want to play?</div>
          <span class="top-links">Premium · Support · Download · Sign up · Log in</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def sidebar() -> None:
    st.markdown(
        """
        <div class="sb-box">
          <div class="sb-title">Your Library  +</div>
          <div class="sb-card">
            <h4>Let's find some podcasts to follow</h4>
            <p>We'll keep you updated on new episodes</p>
          </div>
          <div class="sb-foot">
            Legal · Privacy · Cookies · About Ads<br>🌐 English
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def player() -> None:
    st.markdown(
        '<div class="player">Fellowship prototype — not affiliated with Spotify AB</div>',
        unsafe_allow_html=True,
    )


def nav() -> None:
    """Clear demo navigation — always visible, no overlap."""
    st.markdown("##### Where are you in the demo?")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("① Spotify Home", use_container_width=True, type="primary" if st.session_state["view"] == "home" else "secondary"):
            st.session_state["view"] = "home"
            st.session_state["step"] = "entry"
            st.rerun()
    with c2:
        if st.button("② Discover Weekly", use_container_width=True, type="primary" if st.session_state["view"] == "dw" else "secondary"):
            st.session_state["view"] = "dw"
            st.rerun()
    with c3:
        if st.button("③ Loop Break", use_container_width=True, type="primary" if st.session_state["view"] == "loop" else "secondary"):
            st.session_state["view"] = "loop"
            st.session_state["step"] = "entry"
            st.rerun()
    with c4:
        if st.button("Reset", use_container_width=True):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()
    st.divider()


def view_home() -> None:
    st.info("**Step 1:** You are on Spotify Home. Click **② Discover Weekly** above to continue.")
    cards = "".join(
        f'<div class="card"><div class="card-img" style="background:{c}"></div>'
        f'<p class="card-t">{t}</p><p class="card-s">{a}</p></div>'
        for t, a, c in TRENDING
    )
    arts = "".join(
        f'<div class="card"><div class="card-img" style="background:{c};border-radius:50%"></div>'
        f'<p class="card-t">{n}</p></div>'
        for n, c in ARTISTS
    )
    st.markdown(
        f'<div class="main-pane"><p class="sec-title">Trending songs</p><div class="cards">{cards}</div>'
        f'<p class="sec-title">Popular artists</p><div class="cards">{arts}</div></div>',
        unsafe_allow_html=True,
    )


def view_dw() -> None:
    st.info("**Step 2:** Discover Weekly — songs tagged **In your library** show the problem. Click **③ Loop Break** above.")
    tracks = ""
    for i, (s, a, lib) in enumerate(DW, 1):
        tag = '<span class="tag">In your library</span>' if lib else ""
        tracks += f'<div class="track"><span>{i}</span><span class="n">{s}{tag}</span><span>{a}</span></div>'
    st.markdown(
        f"""
        <div class="main-pane">
          <div class="pl-row">
            <div class="pl-art"></div>
            <div><p class="pl-sub">Playlist</p><p class="pl-h">Discover Weekly</p>
            <p class="pl-sub">Spotify · 30 songs · Updated Monday</p></div>
          </div>
          <div class="banner"><b>This week feels familiar</b><br>
          <span>3 songs already in your library — Loop Break diagnoses why.</span></div>
          {tracks}
        </div>
        """,
        unsafe_allow_html=True,
    )


def view_loop() -> None:
    step = st.session_state["step"]

    if step == "entry":
        st.info("**Step 3:** Describe what felt wrong → click **Run Loop Diagnostic**.")
        st.markdown('<p class="loop-h">Loop Break</p><p class="loop-p">AI reset when Discover Weekly stops feeling new.</p>', unsafe_allow_html=True)
        txt = st.text_area("Message", value=st.session_state["text"], height=100, placeholder="e.g. Half the songs were already in my library…", label_visibility="collapsed")
        c1, c2 = st.columns(2)
        with c1:
            if st.button(EXAMPLES[0][:40] + "…", key="e0"):
                st.session_state["text"] = EXAMPLES[0]
                st.rerun()
        with c2:
            if st.button(EXAMPLES[1][:40] + "…", key="e1"):
                st.session_state["text"] = EXAMPLES[1]
                st.rerun()
        if st.button("Run Loop Diagnostic", type="primary", key="run_diag"):
            if len(txt.strip()) < 15:
                st.error("Please enter at least 15 characters.")
                return
            st.session_state["text"] = txt.strip()
            k = secret("GROQ_API_KEY")
            with st.spinner("Analyzing…"):
                try:
                    d = classify_loop_groq(txt.strip(), k) if k else classify_loop_keyword(txt.strip())
                except Exception:
                    d = classify_loop_keyword(txt.strip())
            st.session_state["dx"] = d
            st.session_state["step"] = "diagnostic"
            st.rerun()

    elif step == "diagnostic":
        st.info("**Step 3b:** Review loop type → click **Get 3 Loop Break picks**.")
        d = st.session_state["dx"]
        lt = d["loop_type"]
        st.markdown(f'<span class="pill">{LOOP_LABELS[lt]}</span>', unsafe_allow_html=True)
        st.markdown(f"**Diagnosis:** {d.get('diagnosis_summary', LOOP_DESCRIPTIONS[lt])}")
        st.markdown(f"**Intervention:** {d.get('intervention_preview', INTERVENTIONS[lt])}")
        mood = st.selectbox("Mood", ["Calm", "Energetic", "Melancholy", "Focused", "Open to anything"], index=4)
        openness = st.select_slider("Novelty", ["Stay close", "Nudge outside comfort zone", "Surprise me"])
        if st.button("Get 3 Loop Break picks", type="primary", key="get_picks"):
            k = secret("GROQ_API_KEY")
            with st.spinner("Building picks…"):
                try:
                    r = (
                        generate_loop_break_groq(lt, st.session_state["text"], mood, openness, k)
                        if k
                        else generate_loop_break_keyword(lt, st.session_state["text"], mood, openness)
                    )
                except Exception:
                    r = generate_loop_break_keyword(lt, st.session_state["text"], mood, openness)
            st.session_state["recs"] = r
            st.session_state["step"] = "results"
            st.rerun()
        if st.button("← Back", key="back_entry"):
            st.session_state["step"] = "entry"
            st.rerun()

    else:
        st.info("**Step 4:** Review picks → rate trust → **Done**.")
        d = st.session_state["dx"]
        r = st.session_state["recs"]
        st.markdown(f'<span class="pill">{LOOP_LABELS[d["loop_type"]]} reset</span>', unsafe_allow_html=True)
        st.markdown(f"### {r.get('intervention_headline', 'Your Loop Break')}")
        st.write(r.get("loop_break_message", ""))
        for i, t in enumerate(r.get("tracks", [])[:3], 1):
            st.markdown(
                f'<div class="pick"><b>{i}. {t.get("song","")}</b> — <small>{t.get("artist","")}</small><br>'
                f'<small><b style="color:#1db954">Why:</b> {t.get("why_fit","")}</small><br>'
                f'<small><b style="color:#1db954">Novelty:</b> {t.get("novelty_rationale","")}</small></div>',
                unsafe_allow_html=True,
            )
            st.link_button(f"Open in Spotify — {t.get('song','')}", spotify_search_url(t.get("artist", ""), t.get("song", "")))
        trust = st.slider("Trust vs last Discover Weekly (1–5)", 1, 5, 4)
        if st.button("Done — back to Home", type="primary", key="done"):
            st.session_state["view"] = "home"
            st.session_state["step"] = "entry"
            st.session_state["text"] = ""
            st.session_state["dx"] = None
            st.session_state["recs"] = None
            st.success(f"Demo complete — trust score {trust}/5")
            st.rerun()


def main() -> None:
    st.set_page_config(page_title="Spotify — Loop Break Demo", layout="wide")
    st.markdown(CSS, unsafe_allow_html=True)
    init()
    topbar()
    left, right = st.columns([1, 3], gap="medium")
    with left:
        sidebar()
    with right:
        nav()
        v = st.session_state["view"]
        if v == "home":
            view_home()
        elif v == "dw":
            view_dw()
        else:
            view_loop()
    player()
    with st.expander("Why AI? (for graders)"):
        st.write(
            "**Recsys gap:** scores play probability, not why DW failed. "
            "**AI unlocks:** loop diagnosis, matched intervention, 3 explained picks. "
            "**UX change:** passive 30-track dump → guided reset inside Spotify."
        )
    if secret("GROQ_API_KEY"):
        st.caption("Groq API connected")
    else:
        st.caption("No API key — using keyword fallback")


if __name__ == "__main__":
    main()
