#!/usr/bin/env python3
"""
Render img/cards/wordle-card.png — the share/post image for the Shona
Wordle, matching the on-page board look: light paper, italic masthead,
DAILY PUZZLE eyebrow, the title, an empty 6x6 board, and a play CTA.
Used as the wordle-feed.xml post image and the page's og:image.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from card_lib import load_font  # noqa: E402

try:
    from PIL import Image, ImageDraw
except ImportError:
    raise SystemExit("ERROR: Pillow not installed. Run: pip install Pillow")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "img", "cards", "wordle-card.png")

W, H = 1080, 1350
PAPER = (251, 250, 246)      # #fbfaf6, matches the page
INK = (26, 26, 26)
ACCENT = (196, 30, 30)       # brand red used on the page
MUTED = (95, 92, 84)
TILE_BORDER = (208, 207, 200)  # --tile-empty-border


def rrect(draw, box, r, **kw):
    draw.rounded_rectangle(box, radius=r, **kw)


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)

    # Top accent rule + italic wordmark (the page's chrome)
    d.rectangle([(0, 0), (W, 8)], fill=ACCENT)
    masthead = load_font("serif_italic", 44)
    d.text((60, 44), "The Mutapa Times", font=masthead, fill=INK)
    d.line([(0, 116), (W, 116)], fill=(232, 230, 223), width=2)

    # Centred eyebrow + title
    eyebrow = load_font("sans_bold", 28)
    title = load_font("serif_bold", 88)

    def centre(text, font, y, fill):
        bb = d.textbbox((0, 0), text, font=font)
        d.text(((W - (bb[2] - bb[0])) / 2, y), text, font=font, fill=fill)

    centre("DAILY PUZZLE", eyebrow, 168, ACCENT)
    centre("Shona Wordle", title, 212, INK)

    # Empty 6x6 board, centred
    cols = 6
    gap = 16
    board_w = 760
    tile = (board_w - gap * (cols - 1)) // cols   # ~ 121
    board_h = tile * cols + gap * (cols - 1)
    x0 = (W - board_w) // 2
    y0 = 360
    for r in range(cols):
        for c in range(cols):
            x = x0 + c * (tile + gap)
            y = y0 + r * (tile + gap)
            rrect(d, [x, y, x + tile, y + tile], 8, fill=(255, 255, 255),
                  outline=TILE_BORDER, width=3)

    # Footer CTA
    foot = load_font("sans_bold", 30)
    sub = load_font("sans", 26)
    cy = y0 + board_h + 56
    centre("A six-letter Shona word, every day.", sub, cy, MUTED)
    centre("Play free  ·  mutapatimes.com/games/shona-wordle", foot, cy + 46, ACCENT)

    img.save(OUT, "PNG", optimize=True)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
