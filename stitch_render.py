"""Load and patch Stitch HTML screens for Loop Break Streamlit app."""

import re
from pathlib import Path

STITCH_DIR = Path(__file__).parent / "stitch_ui"

SCREENS = {
    "home": STITCH_DIR / "spotify_home" / "code.html",
    "dw": STITCH_DIR / "discover_weekly_loop_break_trigger" / "code.html",
    "loop_entry": STITCH_DIR / "loop_break_diagnostic" / "code.html",
    "loop_diagnostic": STITCH_DIR / "loop_break_diagnosis_result" / "code.html",
    "loop_results": STITCH_DIR / "loop_break_results" / "code.html",
}


def load_screen(name: str) -> str:
    path = SCREENS.get(name)
    if not path or not path.exists():
        raise FileNotFoundError(f"Stitch screen not found: {name}")
    return path.read_text(encoding="utf-8")


def inject_diagnostic(
    html: str,
    label: str,
    summary: str,
    intervention: str,
    mood: str = "Open to anything",
    openness: str = "Nudge outside comfort zone",
) -> str:
    html = html.replace("Library Leak", label, 1)
    html = re.sub(
        r"Your recent listening patterns show a high density of repeat tracks.*?exceeded 85%\.",
        summary,
        html,
        count=1,
        flags=re.DOTALL,
    )
    html = html.replace(
        "Hard exclude library overlap — prioritize unheard artists",
        intervention,
        1,
    )
    for m in ["Calm", "Energetic", "Melancholy", "Focused", "Open to anything"]:
        inactive = (
            f'<button class="px-4 py-2 rounded-full bg-surface-container-highest text-on-surface '
            f'border border-transparent hover:border-primary/50 transition-all text-body-md font-bold">{m}</button>'
        )
        active = (
            f'<button class="px-4 py-2 rounded-full bg-primary text-background text-body-md font-bold '
            f'shadow-lg shadow-primary/30">{m}</button>'
        )
        if m == mood:
            html = html.replace(inactive, active, 1)
        else:
            html = html.replace(active, inactive, 1)
    novelty_map = {"Stay close": 1, "Nudge outside comfort zone": 2, "Surprise me completely": 3}
    val = novelty_map.get(openness, 2)
    html = re.sub(
        r'(<input class="novelty-slider[^"]*"[^>]*value=")[^"]*(")',
        rf'\g<1>{val}\2',
        html,
        count=1,
    )
    return html


def _track_card(song: str, artist: str, why: str, novelty: str, img_idx: int) -> str:
    imgs = [
        "https://lh3.googleusercontent.com/aida-public/AB6AXuCX_KjJtEKKfUcMFueyDf5o_xuVqE-6-xfJCEgfTH4EOSZo5HGQ8Z6P6i9XzisXDObNwg_WgnUIlTwDEiPsHmoxNrtLkjXGtHxP-vk0W56MP3M5kbtOBUF2dv14tO939gO1PGexBpgSD5GEPLXyfyYh7JVrwbNr3FsDwmDdZ2S0tp--9ZgE7KzBFUfdciW6Co4Es-qeuW3YU5vDgDZ1TJaYUZwl-vMUh6h4j31EpqNpYacWRfyRL40ZZVYUQXZzke-eCTCQtinjCjj4",
        "https://lh3.googleusercontent.com/aida-public/AB6AXuDIR6PshPG6WG8hhEeeHnBcgU6m4iCDDJwpjNrLcHMzARhaN_MnN6urAunTpVoeWQAhd3khgOY2OWY671wXfHcZVIX0avrK0dke15-BmaStY2NA0H0zJjEprP-4mBu65hRFOmz365M_RLg5KIiHhfAKvtrJerKCskXS2R7r8owYOSkC1Sop7jHi9nLIB4YX4Mbz0mushP8pqB47cUeEhu4xYrrr7lO4UrbW0pGbHhjCYvPQ_z_w-bld67dVXt9B32d0FnsQmib6LnVr",
        "https://lh3.googleusercontent.com/aida-public/AB6AXuA9THwiLLHoMdUs96329J0kbxHM9TH17GLcgb2jXk4agPFHMI1wC43piTr2EdecEIUHaM57LX-haTybqsQz91ILtsL4vEvP7KWXhqvAf4nv_9k3HzjUmI7b9oHHGhmaLsx0-Aofvpm3zKQXEhsRymtoGJOzRvnPGi4K4UZP1Ff6Zak47BGIDmTB5lKApULMZnSNUt-4d76iATKHJMP2_KDgTi2VD8BJCm7eni4bnPM5ym9L_DZUR6DHmWEtRWDg_OGFg7bLP6D4GMPj",
    ]
    img = imgs[img_idx % len(imgs)]
    return f"""
<div class="group track-card glass-card rounded-xl overflow-hidden hover:bg-surface-container-highest transition-all duration-300 transform hover:-translate-y-1">
  <div class="relative aspect-square">
    <img class="w-full h-full object-cover" src="{img}" alt="{song}"/>
    <div class="play-overlay absolute inset-0 bg-black/40 opacity-0 flex items-center justify-center transition-all duration-300 translate-y-4">
      <div class="bg-primary text-black w-12 h-12 rounded-full flex items-center justify-center shadow-2xl">
        <span class="material-symbols-outlined" style="font-variation-settings: 'FILL' 1;">play_arrow</span>
      </div>
    </div>
  </div>
  <div class="p-5">
    <h3 class="text-body-lg font-bold text-white">{song}</h3>
    <p class="text-label-md text-on-surface-variant mb-4">{artist}</p>
    <div class="space-y-3">
      <div>
        <p class="text-label-sm text-primary uppercase tracking-widest font-bold">Why it fits</p>
        <p class="text-body-md text-on-surface">{why}</p>
      </div>
      <div class="pt-2 border-t border-white/10">
        <p class="text-label-sm text-on-surface-variant uppercase tracking-widest font-bold">Novel Difference</p>
        <p class="text-body-md text-on-surface-variant italic">{novelty}</p>
      </div>
    </div>
  </div>
</div>"""


def inject_results(html: str, headline: str, message: str, tracks: list[dict]) -> str:
    cards = ""
    for i, t in enumerate(tracks[:3]):
        cards += _track_card(
            t.get("song", ""),
            t.get("artist", ""),
            t.get("why_fit", ""),
            t.get("novelty_rationale", ""),
            i,
        )
    start = html.find('<div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">')
    end = html.find("<!-- Feedback & Action Area -->")
    if start != -1 and end != -1:
        html = html[:start] + f'<div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">{cards}</div>\n' + html[end:]
    html = html.replace("Cross-genre bridge reset", headline, 1)
    if message and "<!-- LOOP_MESSAGE -->" not in html:
        html = html.replace(
            '<p class="text-headline-lg text-primary font-medium">Cross-genre bridge reset</p>',
            f'<p class="text-headline-lg text-primary font-medium">{headline}</p>'
            f'<p class="text-body-md text-on-surface-variant mt-2">{message}</p>',
            1,
        )
    if tracks:
        first = tracks[0]
        html = html.replace("Midnight Monolith", first.get("song", "Midnight Monolith"), 1)
        html = html.replace("Looming Shadows", first.get("artist", "Looming Shadows"), 1)
    return html


def hide_nonfunctional_buttons(html: str) -> str:
    """Disable Stitch demo buttons so users use Streamlit controls below."""
    return html.replace("<button ", '<button disabled style="opacity:0.55;pointer-events:none" ')
