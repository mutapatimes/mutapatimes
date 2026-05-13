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
    """Editorial weather card — same left-aligned typographic chrome as
    every other 1080×1350 card on the IG grid. No white boxes; cities
    render as clean typographic lines instead of a 2×3 cell grid."""
    img = Image.new("RGB", (CARD_W, CARD_H), BG)
    draw = ImageDraw.Draw(img)

    PAD = 60  # left margin shared with every other card in the system

    # ── Chrome (matches other editorial cards exactly) ──
    masthead_font = load_font("serif_bold", 36)
    eyebrow_font  = load_font("sans_bold", 20)
    draw.rectangle([(0, 0), (140, 10)], fill=ACCENT)
    draw.text((PAD, 56), "THE MUTAPA TIMES", font=masthead_font, fill=CARD_FG)
    draw.text((PAD, 106), f"ZIM WEATHER · {date_label}",
              font=eyebrow_font, fill=ACCENT)

    # ── Headline: Shona · Ndebele greeting, LEFT-aligned ──
    greet_font = load_font("serif_bold", 60)
    draw.text((PAD, 170), "Mangwanani · Livukile,",
              font=greet_font, fill=CARD_FG)
    draw.text((PAD, 238), "Zimbabwe.", font=greet_font, fill=ACCENT)

    # ── City lines: typographic, left-aligned, no boxes ──
    cells = (weather.get("cities") or [])[:6]
    city_y0 = 340
    line_h  = 116          # gap between city blocks

    city_font   = load_font("sans_bold", 26)   # CITY NAME
    temp_font   = load_font("serif_bold", 50)  # 26° / 16°
    cond_font   = load_font("sans", 19)        # condition · rain
    emoji_font  = load_font("sans_bold", 56)   # emoji

    for i, c in enumerate(cells):
        y = city_y0 + i * line_h

        # CITY NAME — top of the row, left
        name = (c.get("city") or "").upper()
        draw.text((PAD, y), name, font=city_font, fill=CARD_FG)

        # Temp — same row, pushed right but still left of the emoji column
        high = c.get("high")
        low  = c.get("low")
        if high is not None and low is not None:
            temp_str = f"{round(high)}° / {round(low)}°"
            tw = draw.textlength(temp_str, font=temp_font)
            draw.text((CARD_W - PAD - 90 - tw, y - 12), temp_str,
                      font=temp_font, fill=CARD_FG)

        # Emoji — far right, vertically aligned with temp
        emoji = c.get("emoji", "")
        if emoji:
            _draw_emoji(img, draw, (CARD_W - PAD - 70, y - 18),
                        emoji, emoji_font, CARD_FG)

        # Sub-line: condition · rain chance (muted, sans, smaller)
        sub_parts = []
        label = (c.get("label") or "").strip()
        if label:
            sub_parts.append(label)
        pp = c.get("precip_prob")
        if pp is not None:
            sub_parts.append(f"{int(pp)}% chance of rain")
        if sub_parts:
            draw.text((PAD, y + 44), "  ·  ".join(sub_parts),
                      font=cond_font, fill=CARD_FG_MUTED)

        # Hairline separator between rows (very subtle)
        if i < len(cells) - 1:
            sep_y = y + line_h - 12
            draw.line([(PAD, sep_y), (CARD_W - PAD, sep_y)],
                      fill=CARD_FG_MUTED, width=1)

    # ── Tsumo: small italic block above the footer ──
    tsumo_eyebrow_font = load_font("sans_bold", 18)
    tsumo_shona_font   = load_font("serif_italic", 24)
    tsumo_en_font      = load_font("sans", 18)

    tsumo_y = city_y0 + len(cells) * line_h + 12
    draw.text((PAD, tsumo_y), "TSUMO YEZUVA · PROVERB OF THE DAY",
              font=tsumo_eyebrow_font, fill=ACCENT)

    shona = f"“{tsumo['shona']}”"
    en = tsumo["english"]
    shona_lines = wrap_text(draw, shona, tsumo_shona_font, CARD_W - PAD * 2)[:2]
    en_lines    = wrap_text(draw, en,    tsumo_en_font,    CARD_W - PAD * 2)[:2]

    sy = tsumo_y + 32
    for ln in shona_lines:
        draw.text((PAD, sy), ln, font=tsumo_shona_font, fill=CARD_FG)
        sy += 32
    sy += 2
    for ln in en_lines:
        draw.text((PAD, sy), ln, font=tsumo_en_font, fill=CARD_FG_MUTED)
        sy += 24

    # ── Footer: VIA / CTA, mirrors other editorial cards ──
    footer_font = load_font("sans_bold", 18)
    via_label   = load_font("sans_bold", 16)

    foot_y = CARD_H - 70
    draw.text((PAD, foot_y), "VIA", font=via_label, fill=CARD_FG_MUTED)
    draw.text((PAD, foot_y + 22), "ZIM WEATHER",
              font=footer_font, fill=CARD_FG)

    cta = "READ MORE → mutapatimes.com/weather"
    cw  = draw.textlength(cta, font=footer_font)
    draw.text((CARD_W - PAD - cw, foot_y + 22), cta,
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
