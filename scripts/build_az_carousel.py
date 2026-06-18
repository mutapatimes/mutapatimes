#!/usr/bin/env python3
"""
Render the 5-slide Air Zimbabwe "back to London" carousel in both the
feed format (1080x1350, 4:5) and the stories format (1080x1920, 9:16).

Output: img/cards/campaign/az-london/feed-{1..5}.png
        img/cards/campaign/az-london/story-{1..5}.png

One consistent butter-cream brand style across every slide: accent tick +
masthead, an accent eyebrow, the slide copy in big serif, and a footer.
Grounded in the published exclusive; no invented numbers (the revenue
figures match the article's back-of-the-envelope model).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from card_lib import BUTTER, ACCENT, CARD_FG, CARD_FG_MUTED, load_font, wrap_text  # noqa: E402

try:
    from PIL import Image, ImageDraw
except ImportError:
    raise SystemExit("ERROR: Pillow not installed. Run: pip install Pillow")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "img", "cards", "campaign", "az-london")
W = 1080

# 5 slides. kind 'cover' = big title; 'body' = eyebrow + paragraph; 'cta' = close.
SLIDES = [
    {"kind": "cover", "eyebrow": "EXCLUSIVE",
     "text": "Air Zimbabwe is going back to London"},
    {"kind": "body", "eyebrow": "THE DEAL",
     "text": "From 1 July, a wide-body Airbus A330 flies Harare to London several times a week, under the Air Zimbabwe code. A 13-month wet-lease with Spain's Plus Ultra."},
    {"kind": "body", "eyebrow": "THE CLEVER BIT",
     "text": "Air Zimbabwe is still on the UK safety list. The fix: fly a non-banned operator's aircraft, crew and insurance. Same rulebook, a deliberate door back to London."},
    {"kind": "body", "eyebrow": "WHAT IT IS WORTH",
     "text": "Back of the envelope: about £34m a year in passenger revenue, base case, and up to £47m at peak. A multi-million-pound route, fought back."},
    {"kind": "cta", "eyebrow": "THE FULL STORY",
     "text": "The paper trail, the aircraft, the economics.",
     "cta": "Read the exclusive at mutapatimes.com"},
]


def _centre_block_y(card_h, block_h):
    available = card_h - 360
    return 230 + (available - block_h) // 2


def _fit(draw, text, font_role, max_size, min_size, max_width, max_lines):
    for size in range(max_size, min_size - 1, -2):
        font = load_font(font_role, size)
        lines = wrap_text(text, font, max_width, draw)
        if len(lines) <= max_lines:
            return font, lines, size
    font = load_font(font_role, min_size)
    return font, wrap_text(text, font, max_width, draw), min_size


def render_slide(slide, card_h, path):
    img = Image.new("RGB", (W, card_h), BUTTER)
    d = ImageDraw.Draw(img)
    pad = 60
    maxw = W - pad * 2

    # Brand chrome
    d.rectangle([(0, 0), (140, 10)], fill=ACCENT)
    d.text((pad, 70), "THE MUTAPA TIMES", font=load_font("serif_bold", 42), fill=CARD_FG)
    d.text((pad, 124), "Southern Africa outside-in", font=load_font("sans", 28), fill=CARD_FG_MUTED)

    # Eyebrow
    d.text((pad, 200), slide["eyebrow"], font=load_font("sans_bold", 26), fill=ACCENT)

    # Main copy — bigger for the cover slide
    if slide["kind"] == "cover":
        font, lines, size = _fit(d, slide["text"], "serif_bold", 96, 56, maxw, 6)
        lh = int(size * 1.14)
    else:
        font, lines, size = _fit(d, slide["text"], "serif_bold", 70, 38, maxw, 9)
        lh = int(size * 1.3)
    block_h = len(lines) * lh
    y = _centre_block_y(card_h, block_h)
    for ln in lines:
        d.text((pad, y), ln, font=font, fill=CARD_FG)
        y += lh

    # Footer
    footer_y = card_h - 140
    if slide["kind"] == "cta":
        d.text((pad, footer_y), slide["cta"], font=load_font("sans_bold", 30), fill=ACCENT)
        d.text((pad, footer_y + 44), "The Mutapa Times exclusive",
               font=load_font("sans", 26), fill=CARD_FG_MUTED)
    else:
        d.text((pad, footer_y), "READ THE EXCLUSIVE", font=load_font("sans_bold", 22), fill=CARD_FG_MUTED)
        cue = "mutapatimes.com →"
        d.text((pad, footer_y + 32), cue, font=load_font("sans", 28), fill=ACCENT)

    img.save(path, "PNG", optimize=True)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    for fmt, h in (("feed", 1350), ("story", 1920)):
        for i, slide in enumerate(SLIDES, start=1):
            path = os.path.join(OUT_DIR, f"{fmt}-{i}.png")
            render_slide(slide, h, path)
            print(f"  {os.path.relpath(path, ROOT)}")
    print(f"Rendered {len(SLIDES) * 2} slides in {OUT_DIR}")


if __name__ == "__main__":
    main()
