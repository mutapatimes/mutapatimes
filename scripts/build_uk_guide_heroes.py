#!/usr/bin/env python3
"""Generate halftone hero images for the /moving-to-zimbabwe/ microsite.

Reuses the halftone pipeline from build_halftone_trial.py (Pollinations AI
into a render_halftone treatment on coloured paper) but outputs clean
landscape art with no card chrome — these are page heroes, not social cards.

Outputs to /img/uk-guide/{slug}.png at 1600x900.

Topic prompts deliberately avoid people entirely (per the project's
no-faces rule for AI imagery) and lean on objects, architecture and
atmosphere instead.
"""
import os
import sys
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_halftone_trial import (  # noqa: E402
    fetch_pollinations,
    halftone_prompt,
    paper_for_slug,
    render_halftone,
)

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT_DIR = os.path.join(ROOT, "img", "uk-guide")

HERO_W, HERO_H = 1600, 900

HEROES = [
    {
        "slug": "moving-to-zimbabwe",
        "topic": (
            "a vintage leather steamer trunk with brass buckles and weathered "
            "travel labels reading Harare and Bulawayo, resting on a sunlit "
            "railway platform, no human figures, atmospheric documentary still life"
        ),
    },
    {
        "slug": "visa-on-arrival",
        "topic": (
            "a worn passport open on a wooden immigration counter beside an "
            "airline boarding pass and a rubber ink stamp, soft window light "
            "from a tropical departures hall, no human figures, archival photograph"
        ),
    },
    {
        "slug": "healthcare-and-medical-aid",
        "topic": (
            "the exterior of a southern African modernist private clinic at "
            "dusk, white walls with deep verandah shadows, a single palm tree, "
            "warm Harare evening light, no human figures, architectural photograph"
        ),
    },
    {
        "slug": "international-schools",
        "topic": (
            "an empty colonial-era African schoolyard quadrangle at golden "
            "hour, jacaranda tree casting long shadows, a leather satchel "
            "resting on a wooden bench, no human figures, nostalgic editorial photograph"
        ),
    },
    {
        "slug": "money-and-banking",
        "topic": (
            "a still life of folded US dollar banknotes and Zimbabwean Gold "
            "(ZiG) notes spread across a dark wooden counter, beside a brass "
            "set of jeweller's scales, dim banking-hall light, no human figures"
        ),
    },
    {
        "slug": "driving-and-vehicle-import",
        "topic": (
            "an empty Zimbabwean tarmac highway stretching toward a distant "
            "mountain horizon, jacaranda trees lining the verge, a weathered "
            "white-and-black road sign in the foreground, no human figures, "
            "atmospheric documentary photograph"
        ),
    },
]


def make_hero(slug: str, topic: str, out_path: str) -> None:
    import hashlib
    seed = int(hashlib.md5(slug.encode()).hexdigest()[:8], 16) % (1 << 31)
    paper = paper_for_slug(slug)
    print(f"  {slug:<32s}  paper={paper}  seed={seed}")

    prompt = halftone_prompt(topic)
    # Pollinations supports arbitrary aspect ratio — ask for the same shape
    # we will render at so render_halftone does no scaling.
    raw = fetch_pollinations(prompt, seed, w=HERO_W, h=HERO_H)
    raw = raw.resize((HERO_W, HERO_H))
    art = render_halftone(raw, paper, seed)

    # The halftone treatment already fades to paper at the edges, but we
    # want a hard bleed edge for web hero rectangles — composite onto a
    # full paper rectangle so the result has no transparent gutter.
    canvas = Image.new("RGB", (HERO_W, HERO_H), paper)
    canvas.paste(art, (0, 0))
    canvas.save(out_path, "PNG", optimize=True)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    only = sys.argv[1] if len(sys.argv) > 1 else None
    print(f"=== UK guide heroes -> {OUT_DIR} ===")
    for h in HEROES:
        if only and only != h["slug"]:
            continue
        out = os.path.join(OUT_DIR, f"{h['slug']}.png")
        try:
            make_hero(h["slug"], h["topic"], out)
            kb = os.path.getsize(out) // 1024
            print(f"    OK {kb:>5} KB")
        except Exception as e:
            print(f"    FAILED: {e}")
    print("=== DONE ===")


if __name__ == "__main__":
    main()
