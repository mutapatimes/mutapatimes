#!/usr/bin/env python3
"""
Render the 10-slide "Meet Dr Rumbi" carousel in both the feed format
(1080x1350, 4:5) and the stories format (1080x1920, 9:16).

Output: img/cards/campaign/dr-rumbi/feed-{1..10}.png
        img/cards/campaign/dr-rumbi/story-{1..10}.png

Same butter-cream brand style as the rest of the site (accent tick +
masthead, accent eyebrow, big serif copy, footer cue), with two GREEN
slides for the branded set-pieces: About Glacie Health and the Sally
Mugabe Fertility Clinic. Opening cover slide + closing CTA slide in the
normal style. Copy is grounded in the published profile, no invented
figures.
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
OUT_DIR = os.path.join(ROOT, "img", "cards", "campaign", "dr-rumbi")
W = 1080

# Green set-piece palette (mirrors the article's dark section, in green):
# deep forest ground, butter text, muted sage body, soft-gold eyebrow.
GREEN_BG = (22, 51, 42)
GREEN_FG = BUTTER
GREEN_MUTED = (198, 214, 200)
GOLD = (224, 194, 120)

# 10 slides. kind 'cover' = big title; 'body' = eyebrow + paragraph;
# 'cta' = close. theme 'green' flips to the forest set-piece palette.
SLIDES = [
    {"kind": "cover", "eyebrow": "IN CONVERSATION",
     "text": "Meet Dr Rumbi"},
    {"kind": "body", "eyebrow": "WHO SHE IS",
     "text": "Dr Rumbi Mutenga is a practising NHS GP, an educator, and the founder and CEO of Glacie Health, a women's-health venture built to close the gap between good intentions and the care women actually receive."},
    {"kind": "body", "eyebrow": "THE AFTERNOON",
     "text": "A cool July afternoon at the Wellcome Collection, where art, science and technology sit side by side. She flew in from Toronto to teach at the Zimbabwean Embassy, part of a mission to carry dignified healthcare home."},
    {"kind": "body", "theme": "green", "eyebrow": "ABOUT GLACIE HEALTH",
     "text": "A women's-health venture with a single organising idea: closing the gap between intention and measurable impact, so care is designed around women's real needs rather than assumed for them."},
    {"kind": "body", "theme": "green", "eyebrow": "GLACIE HEALTH",
     "text": "Its work runs through advocacy, collaboration and consultation. Recent projects include a Women's Health Hackathon, community Walk and Talk events, and reports on endometriosis, fibroids and the future of period care."},
    {"kind": "body", "eyebrow": "EDUCATION IS THE MEDICINE",
     "text": "\"If we don't have education about certain things, we can't access the healthcare at all. If I don't know I'm meant to check my breasts, how would I ever know I had a lump?\""},
    {"kind": "body", "theme": "green", "eyebrow": "IN FOCUS",
     "text": "The Sally Mugabe Fertility Clinic. Reactivated in Harare, it offers low-cost, science-based care for women who might otherwise spend years and thousands of dollars searching elsewhere."},
    {"kind": "body", "theme": "green", "eyebrow": "SALLY MUGABE FERTILITY CLINIC",
     "text": "The point the clinic makes, and Glacie builds into its campaigns: infertility is not a woman's problem alone. In roughly half of couples the man is a factor. Glacie Health is backing the reactivation."},
    {"kind": "body", "eyebrow": "\"IT'S YOUR COMPETITIVE ADVANTAGE\"",
     "text": "\"When you've trained here and you go back, there is an advantage waiting for you. It is, quite literally, your competitive advantage. Nobody loses if it brings investment and expertise home.\""},
    {"kind": "cta", "eyebrow": "THE FULL PROFILE",
     "text": "On calling, on education as medicine, and on carrying what the West knows back home.",
     "cta": "Read the interview at mutapatimes.com"},
]


def _palette(slide):
    if slide.get("theme") == "green":
        return {"bg": GREEN_BG, "fg": GREEN_FG, "muted": GREEN_MUTED,
                "eyebrow": GOLD, "tick": GOLD, "cue": GOLD}
    return {"bg": BUTTER, "fg": CARD_FG, "muted": CARD_FG_MUTED,
            "eyebrow": ACCENT, "tick": ACCENT, "cue": ACCENT}


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
    pal = _palette(slide)
    img = Image.new("RGB", (W, card_h), pal["bg"])
    d = ImageDraw.Draw(img)
    pad = 60
    maxw = W - pad * 2

    # Brand chrome
    d.rectangle([(0, 0), (140, 10)], fill=pal["tick"])
    d.text((pad, 70), "THE MUTAPA TIMES", font=load_font("serif_bold", 42), fill=pal["fg"])
    d.text((pad, 124), "Southern Africa outside-in", font=load_font("sans", 28), fill=pal["muted"])

    # Eyebrow
    d.text((pad, 200), slide["eyebrow"], font=load_font("sans_bold", 26), fill=pal["eyebrow"])

    # Main copy — bigger for the cover slide
    if slide["kind"] == "cover":
        font, lines, size = _fit(d, slide["text"], "serif_bold", 128, 72, maxw, 4)
        lh = int(size * 1.14)
    else:
        font, lines, size = _fit(d, slide["text"], "serif_bold", 70, 38, maxw, 9)
        lh = int(size * 1.3)
    block_h = len(lines) * lh
    y = _centre_block_y(card_h, block_h)
    for ln in lines:
        d.text((pad, y), ln, font=font, fill=pal["fg"])
        y += lh

    # Footer
    footer_y = card_h - 140
    if slide["kind"] == "cta":
        d.text((pad, footer_y), slide["cta"], font=load_font("sans_bold", 30), fill=pal["cue"])
        d.text((pad, footer_y + 44), "The Mutapa Times",
               font=load_font("sans", 26), fill=pal["muted"])
    else:
        d.text((pad, footer_y), "READ THE FULL PROFILE", font=load_font("sans_bold", 22), fill=pal["muted"])
        d.text((pad, footer_y + 32), "mutapatimes.com →", font=load_font("sans", 28), fill=pal["cue"])

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
