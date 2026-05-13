#!/usr/bin/env python3
"""Render the daily weather card — ONE portrait 1080x1350 image with all
6 Zim cities + Tsumo yezuva at the bottom. This single image is what
the autolist posts everywhere; no swipe-through carousel needed.

Layout:
  ┌──────────────────────────┐
  │ THE MUTAPA TIMES         │  ← masthead + accent bar
  │ ZIM WEATHER · DATE       │
  │                          │
  │ Mangwanani · Livukile.   │  ← Shona + Ndebele greeting
  │                          │
  │ ┌──────┐ ┌──────┐        │  ← 2-col × 3-row city grid
  │ │ HRE  │ │ BYO  │        │     each cell: name · emoji ·
  │ │ 27/15│ │ 27/14│        │     high/low · condition ·
  │ └──────┘ └──────┘        │     rain chance
  │ (6 cities total)         │
  │                          │
  │ TSUMO YEZUVA             │  ← Shona proverb + English
  │ "…"                      │
  │                          │
  │ mutapatimes.com          │
  └──────────────────────────┘
"""
import json
import os
import shutil
import sys
import time
from datetime import datetime, timezone, timedelta

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("ERROR: Pillow not installed. Run: pip install Pillow")
    sys.exit(1)

# pilmoji renders color emoji via Twemoji — falls back to monochrome if missing.
try:
    from pilmoji import Pilmoji
    from pilmoji.source import Twemoji
    HAS_PILMOJI = True
except ImportError:
    HAS_PILMOJI = False

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
WEATHER_FILE = os.path.join(ROOT, "data", "weather.json")
OUT_DIR = os.path.join(ROOT, "img", "cards")
OUT_FILE = os.path.join(OUT_DIR, "weather-snapshot.png")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from send_newsletter import SHONA_PROVERBS  # noqa: E402


# ── Brand palette + dimensions ─────────────────────────────
CARD_W = 1080
CARD_H = 1350
CARD_FG = (26, 26, 26)
CARD_FG_MUTED = (95, 92, 84)
ACCENT = (192, 57, 43)
BG = (245, 232, 200)        # butter #F5E8C8 — brand-locked card background
CELL_BG = (255, 255, 255)


FONT_ROLES = {
    "serif_bold": [
        "fonts/PlayfairDisplay-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
        "/System/Library/Fonts/Supplemental/Georgia Bold.ttf",
        "/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf",
    ],
    "serif_italic": [
        "fonts/PlayfairDisplay-Italic.ttf",
        "/System/Library/Fonts/Supplemental/Georgia Italic.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf",
    ],
    "sans": [
        "fonts/Inter-Medium.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ],
    "sans_bold": [
        "fonts/Inter-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    ],
}


def load_font(role, size):
    for path in FONT_ROLES.get(role, []):
        if os.path.isfile(path):
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default()


def pick_tsumo():
    """Same daily rotation as send_newsletter so the social post matches
    what newsletter subscribers see."""
    day_index = int(time.time() // 86400) % len(SHONA_PROVERBS)
    return SHONA_PROVERBS[day_index]


def wrap_text(draw, text, font, max_width):
    """Greedy word-wrap into lines that fit max_width."""
    words = (text or "").split()
    lines, line = [], []
    for word in words:
        test = " ".join(line + [word])
        if draw.textlength(test, font=font) <= max_width:
            line.append(word)
        else:
            if line:
                lines.append(" ".join(line))
            line = [word]
    if line:
        lines.append(" ".join(line))
    return lines


def _draw_emoji(img, draw, xy, text, font, fill):
    if HAS_PILMOJI:
        with Pilmoji(img, source=Twemoji) as p:
            p.text(xy, text, fill, font, emoji_scale_factor=1.0,
                   emoji_position_offset=(0, 4))
    else:
        draw.text(xy, text, font=font, fill=fill)


# ── The card ──────────────────────────────────────────────
def render_card(weather, tsumo, date_label, out_path):
    img = Image.new("RGB", (CARD_W, CARD_H), BG)
    draw = ImageDraw.Draw(img)

    # ── Chrome: masthead + eyebrow date ──
    masthead_font = load_font("serif_bold", 36)
    eyebrow_font = load_font("sans_bold", 20)
    draw.rectangle([(0, 0), (140, 10)], fill=ACCENT)
    draw.text((60, 56), "THE MUTAPA TIMES", font=masthead_font, fill=CARD_FG)
    draw.text((60, 106), f"ZIM WEATHER · {date_label}",
              font=eyebrow_font, fill=ACCENT)

    # ── Greeting: Shona · Ndebele, one warm line ──
    greet_font = load_font("serif_bold", 50)
    greeting = "Mangwanani · Livukile,"
    country = "Zimbabwe."
    gw = draw.textlength(greeting, font=greet_font)
    cw = draw.textlength(country, font=greet_font)
    draw.text(((CARD_W - gw) // 2, 165), greeting,
              font=greet_font, fill=CARD_FG)
    draw.text(((CARD_W - cw) // 2, 225), country,
              font=greet_font, fill=ACCENT)

    # Subtitle: tiny credit / translation
    sub_font = load_font("serif_italic", 22)
    sub = "Good morning, Zimbabwe — in Shona & Ndebele."
    sw = draw.textlength(sub, font=sub_font)
    draw.text(((CARD_W - sw) // 2, 300), sub,
              font=sub_font, fill=CARD_FG_MUTED)

    # ── 2-col × 3-row city grid ──
    cells = (weather.get("cities") or [])[:6]
    grid_x0 = 60
    grid_y0 = 365
    cell_w = (CARD_W - grid_x0 * 2 - 24) // 2   # 24px col gap
    cell_h = 195
    col_gap = 24
    row_gap = 16

    name_font = load_font("sans_bold", 22)
    temp_font = load_font("serif_bold", 56)
    cond_font = load_font("sans", 19)
    precip_font = load_font("sans", 17)
    emoji_font = load_font("sans_bold", 84)

    for i, c in enumerate(cells):
        row, col = divmod(i, 2)
        x = grid_x0 + col * (cell_w + col_gap)
        y = grid_y0 + row * (cell_h + row_gap)

        # White cell with thin outline
        draw.rounded_rectangle(
            [(x, y), (x + cell_w, y + cell_h)],
            radius=10, fill=CELL_BG, outline=CARD_FG_MUTED, width=1,
        )

        # City name top-left
        draw.text((x + 22, y + 18), c["city"].upper(),
                  font=name_font, fill=CARD_FG)

        # Big weather emoji top-right
        emoji = c.get("emoji", "")
        if emoji:
            _draw_emoji(img, draw, (x + cell_w - 110, y + 14), emoji,
                        emoji_font, CARD_FG)

        # Big high/low temp on the left, vertically centred-ish
        high = c.get("high")
        low = c.get("low")
        if high is not None and low is not None:
            temp_str = f"{round(high)}° / {round(low)}°"
            draw.text((x + 22, y + 72), temp_str,
                      font=temp_font, fill=CARD_FG)

        # Condition + rain chance stacked at the bottom of the cell
        cond_y = y + 138
        label = c.get("label") or ""
        if label:
            draw.text((x + 22, cond_y), label,
                      font=cond_font, fill=CARD_FG_MUTED)
        pp = c.get("precip_prob")
        if pp is not None:
            draw.text((x + 22, cond_y + 26),
                      f"{int(pp)}% chance of rain",
                      font=precip_font, fill=CARD_FG_MUTED)

    # ── Divider ──
    grid_bottom = grid_y0 + 3 * cell_h + 2 * row_gap
    divider_y = grid_bottom + 26
    draw.line([(60, divider_y), (CARD_W - 60, divider_y)],
              fill=CARD_FG_MUTED, width=1)

    # ── Tsumo of the day ──
    tsumo_eyebrow_font = load_font("sans_bold", 20)
    tsumo_shona_font = load_font("serif_italic", 30)
    tsumo_en_font = load_font("sans", 22)

    tsumo_y = divider_y + 22
    draw.text((60, tsumo_y), "TSUMO YEZUVA · PROVERB OF THE DAY",
              font=tsumo_eyebrow_font, fill=ACCENT)

    shona = f"“{tsumo['shona']}”"
    en = tsumo["english"]
    shona_lines = wrap_text(draw, shona, tsumo_shona_font, CARD_W - 120)[:2]
    en_lines = wrap_text(draw, en, tsumo_en_font, CARD_W - 120)[:2]

    sy = tsumo_y + 38
    for ln in shona_lines:
        draw.text((60, sy), ln, font=tsumo_shona_font, fill=CARD_FG)
        sy += 40
    sy += 4
    for ln in en_lines:
        draw.text((60, sy), ln, font=tsumo_en_font, fill=CARD_FG_MUTED)
        sy += 30

    # ── Footer ──
    footer_font = load_font("sans_bold", 20)
    draw.text((60, CARD_H - 55), "mutapatimes.com",
              font=footer_font, fill=ACCENT)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    img.save(out_path, "PNG", optimize=True)


def main():
    print("=== BUILD WEATHER CARD ===")
    if not os.path.exists(WEATHER_FILE):
        print(f"  ERROR: {WEATHER_FILE} not found. Run fetch_weather.py first.")
        sys.exit(1)

    with open(WEATHER_FILE) as f:
        weather = json.load(f)
    if not (weather.get("cities") or []):
        print("  ERROR: no cities in payload")
        sys.exit(1)
    tsumo = pick_tsumo()
    if not HAS_PILMOJI:
        print("  NOTE: pilmoji missing — emoji render monochrome.")

    date_label = datetime.now(timezone(timedelta(hours=2))).strftime("%a %d %b %Y").upper()
    render_card(weather, tsumo, date_label, OUT_FILE)
    print(f"  Wrote {OUT_FILE}")
    print(f"  Cities: {len(weather['cities'])}")
    print(f"  Tsumo:  {tsumo['shona']}")

    # Mirror the snapshot to weather-1-cover.png so the existing feed
    # image URL keeps resolving for already-deployed feed consumers.
    legacy = os.path.join(OUT_DIR, "weather-1-cover.png")
    shutil.copyfile(OUT_FILE, legacy)
    print(f"  Mirrored → {legacy} (legacy filename for cached feeds)")

    print("\n=== DONE ===")


if __name__ == "__main__":
    main()
