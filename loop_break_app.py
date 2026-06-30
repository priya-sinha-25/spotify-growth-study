"""Part 4: Loop Break — Stitch UI + working AI backend."""

import os

import streamlit as st
import streamlit.components.v1 as components
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
from stitch_render import hide_nonfunctional_buttons, inject_diagnostic, inject_results, load_screen

IFRAME_HEIGHT = 820

EXAMPLES = [
    "Discover Weekly had songs I already saved — feels like my library again.",
    "Same indie mood every Monday — I want something new but still me.",
]

MOODS = ["Calm", "Energetic", "Melancholy", "Focused", "Open to anything"]
NOVELTY = ["Stay close", "Nudge outside comfort zone", "Surprise me completely"]


def secret(key: str) -> str | None:
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
        "text": "",
        "dx": None,
        "recs": None,
        "mood": "Open to anything",
        "openness": NOVELTY[1],
    }.items():
        if k not in st.session_state:
            st.session_state[k] = v


def show_stitch(html: str) -> None:
    components.html(hide_nonfunctional_buttons(html), height=IFRAME_HEIGHT, scrolling=False)


def render_view() -> None:
    view = st.session_state["view"]
    if view == "home":
        show_stitch(load_screen("home"))
    elif view == "dw":
        show_stitch(load_screen("dw"))
    elif view == "loop_entry":
        show_stitch(load_screen("loop_entry"))
    elif view == "loop_diagnostic":
        d = st.session_state["dx"] or {}
        lt = d.get("loop_type", "genre_lock")
        mood = st.session_state.get("mood", "Open to anything")
        openness = st.session_state.get("openness", "Nudge outside comfort zone")
        html = load_screen("loop_diagnostic")
        html = inject_diagnostic(
            html,
            LOOP_LABELS.get(lt, "Genre Lock"),
            d.get("diagnosis_summary", LOOP_DESCRIPTIONS.get(lt, "")),
            d.get("intervention_preview", INTERVENTIONS.get(lt, "")),
            mood=mood,
            openness=openness,
        )
        show_stitch(html)
    elif view == "loop_results":
        r = st.session_state["recs"] or {}
        html = load_screen("loop_results")
        html = inject_results(
            html,
            r.get("intervention_headline", "Your Loop Break"),
            r.get("loop_break_message", ""),
            r.get("tracks", []),
        )
        show_stitch(html)


def control_panel() -> None:
    """Streamlit controls below Stitch iframe — no overlap."""
    st.markdown(
        """
        <style>
        #MainMenu, footer, header {visibility: hidden;}
        section[data-testid="stSidebar"] {display: none !important;}
        .stApp {background: #0e0e0e;}
        .main .block-container {padding-top: 0.5rem; max-width: 100%;}
        .ctrl-bar {
            background: #181818; border: 1px solid #282828; border-radius: 12px;
            padding: 16px 20px; margin-top: 8px;
        }
        .ctrl-title {color: #fff; font-weight: 700; font-size: 14px; margin-bottom: 12px;}
        div[data-testid="stHorizontalBlock"] button[kind="primary"] {
            background: #1db954 !important; color: #000 !important; font-weight: 700 !important;
            border-radius: 999px !important; border: none !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    view = st.session_state["view"]
    st.markdown('<div class="ctrl-title">Demo controls (powers Loop Break AI)</div>', unsafe_allow_html=True)

    if view == "home":
        st.caption("Step 1 — Spotify Home")
        if st.button("Open Discover Weekly →", type="primary", use_container_width=True):
            st.session_state["view"] = "dw"
            st.rerun()

    elif view == "dw":
        st.caption("Step 2 — Discover Weekly · tap Break the loop")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Break the loop →", type="primary", use_container_width=True):
                st.session_state["view"] = "loop_entry"
                st.rerun()
        with c2:
            if st.button("← Back to Home", use_container_width=True):
                st.session_state["view"] = "home"
                st.rerun()

    elif view == "loop_entry":
        st.caption("Step 3 — Describe what felt wrong, then run diagnostic")
        text = st.text_area(
            "Frustration",
            value=st.session_state["text"],
            height=90,
            placeholder="What felt off about this week's Discover Weekly?",
            label_visibility="collapsed",
        )
        c1, c2 = st.columns(2)
        with c1:
            if st.button(EXAMPLES[0][:42] + "…", key="ex0"):
                st.session_state["text"] = EXAMPLES[0]
                st.rerun()
        with c2:
            if st.button(EXAMPLES[1][:42] + "…", key="ex1"):
                st.session_state["text"] = EXAMPLES[1]
                st.rerun()
        c3, c4 = st.columns(2)
        with c3:
            if st.button("Run Loop Diagnostic", type="primary", use_container_width=True):
                if len(text.strip()) < 15:
                    st.error("Enter at least 15 characters.")
                    return
                st.session_state["text"] = text.strip()
                k = secret("GROQ_API_KEY")
                with st.spinner("Running AI diagnostic…"):
                    try:
                        d = classify_loop_groq(text.strip(), k) if k else classify_loop_keyword(text.strip())
                    except Exception:
                        d = classify_loop_keyword(text.strip())
                st.session_state["dx"] = d
                st.session_state["view"] = "loop_diagnostic"
                st.rerun()
        with c4:
            if st.button("← Back to Discover Weekly", use_container_width=True):
                st.session_state["view"] = "dw"
                st.rerun()

    elif view == "loop_diagnostic":
        st.caption("Step 3b — Set mood & novelty, get 3 picks")
        mood = st.selectbox(
            "Mood",
            MOODS,
            index=MOODS.index(st.session_state.get("mood", "Open to anything")),
            label_visibility="collapsed",
            key="mood_select",
        )
        openness = st.select_slider(
            "Novelty",
            NOVELTY,
            value=st.session_state.get("openness", NOVELTY[1]),
            label_visibility="collapsed",
            key="novelty_select",
        )
        st.session_state["mood"] = mood
        st.session_state["openness"] = openness
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Get 3 Loop Break picks", type="primary", use_container_width=True):
                d = st.session_state["dx"]
                lt = d["loop_type"]
                k = secret("GROQ_API_KEY")
                with st.spinner("Generating picks…"):
                    try:
                        r = (
                            generate_loop_break_groq(lt, st.session_state["text"], mood, openness, k)
                            if k
                            else generate_loop_break_keyword(lt, st.session_state["text"], mood, openness)
                        )
                    except Exception:
                        r = generate_loop_break_keyword(lt, st.session_state["text"], mood, openness)
                st.session_state["recs"] = r
                st.session_state["view"] = "loop_results"
                st.rerun()
        with c2:
            if st.button("← Back", use_container_width=True):
                st.session_state["view"] = "loop_entry"
                st.rerun()

    elif view == "loop_results":
        st.caption("Step 4 — Review picks & rate trust")
        r = st.session_state["recs"] or {}
        for t in r.get("tracks", [])[:3]:
            st.link_button(
                f"▶ Open in Spotify — {t.get('song', '')} · {t.get('artist', '')}",
                spotify_search_url(t.get("artist", ""), t.get("song", "")),
                use_container_width=True,
            )
        trust = st.slider("Trust vs last Discover Weekly (1–5)", 1, 5, 4)
        if st.button("Done — back to Home", type="primary", use_container_width=True):
            st.session_state["view"] = "home"
            st.session_state["text"] = ""
            st.session_state["dx"] = None
            st.session_state["recs"] = None
            st.success(f"Demo complete — trust score {trust}/5")
            st.rerun()

    with st.expander("Why AI? · Groq status"):
        if secret("GROQ_API_KEY"):
            st.success("Groq API connected")
        else:
            st.warning("No API key — keyword fallback active")
        st.write(
            "Recsys can't diagnose why DW failed. Loop Break uses AI to classify loop type, "
            "match intervention, and explain 3 picks — inside Spotify's UI."
        )
    if st.button("Reset demo"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()


def main() -> None:
    st.set_page_config(page_title="Spotify — Loop Break", layout="wide")
    init()
    render_view()
    control_panel()


if __name__ == "__main__":
    main()
