#!/usr/bin/env python3
"""Render the daily weather carousel (8 portrait 1080x1350 slides):

  1) COVER  — beautifully designed, positive lead. "Mangwanani, Zimbabwe"
     greeting, sun motif, on-brand warm palette. This is also the image
     used by the dedicated weather autolist for single-image platforms.
  2..7) CITY  — one slide each for Harare, Bulawayo, Mutare, Gweru,
     Masvingo, Victoria Falls. Big emoji, hero high/low temp, condition,
     rain probability, humidity + wind.
  8) TSUMO  — proverb of the day in italic serif + English translation.

Each slide rotates through the brand faded palette (dusty rose, sage
green, butter yellow, warm beige) so the carousel reads as a curated
visual sequence, not 8 identical cards.
"""
import json
import os
import sys
import time
from datetime import datetime, timezone, timedelta

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("ERROR: Pillow not installed. Run: pip install Pillow")
    sys.exit(1)

try:
    from pilmoji import Pilmoji
    from pilmoji.source import Twemoji
    HAS_PILMOJI = True
except ImportError:
    HAS_PILMOJI = False

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
WEATHER_FILE = os.path.join(ROOT, "data", "weather.json")
OUT_DIR = os.path.join(ROOT, "img", "cards")
CAROUSEL_MANIFEST = os.path.join(ROOT, "data", "weather-carousel.json")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from send_newsletter import SHONA_PROVERBS  # noqa: E402


# ── Brand palette + dimensions ─────────────────────────────
CARD_W = 1080
CARD_H = 1350
CARD_FG = (26, 26, 26)
CARD_FG_MUTED = (95, 92, 84)
ACCENT = (192, 57, 43)

# Faded brand palette — rotates per slide so the carousel looks
# composed, not monotone.
PALETTE = [
    (236, 226, 207),  # warm beige   — cover
    (216, 230, 213),  # sage green   — Harare
    (245, 232, 200),  # butter       — Bulawayo
    (242, 218, 213),  # dusty rose   — Mutare
    (216, 230, 213),  # sage green   — Gweru
    (245, 232, 200),  # butter       — Masvingo
    (242, 218, 213),  # dusty rose   — Victoria Falls
    (236, 226, 207),  # warm beige   — tsumo
]


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
    what subscribers see."""
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
    """Render text with color emoji via pilmoji/Twemoji when available.
    Plain draw.text fallback if pilmoji is missing."""
    if HAS_PILMOJI:
        with Pilmoji(img, source=Twemoji) as p:
            p.text(xy, text, fill, font, emoji_scale_factor=1.0,
                   emoji_position_offset=(0, 4))
    else:
        draw.text(xy, text, font=font, fill=fill)


# ── Slide chrome (consistent header + footer across all 8) ──
def _draw_chrome(img, draw, eyebrow_text):
    masthead_font = load_font("serif_bold", 38)
    eyebrow_font = load_font("sans_bold", 22)
    footer_font = load_font("sans_bold", 22)

    draw.rectangle([(0, 0), (140, 10)], fill=ACCENT)
    draw.text((60, 60), "THE MUTAPA TIMES", font=masthead_font, fill=CARD_FG)
    draw.text((60, 114), eyebrow_text, font=eyebrow_font, fill=ACCENT)

    # Footer always says the same thing — keeps the carousel cohesive.
    draw.text((60, CARD_H - 60), "mutapatimes.com",
              font=footer_font, fill=ACCENT)


# ── Slide 1: Cover ─────────────────────────────────────────
# Composition rules:
#   - The big weather emoji is the visual anchor and sits centred
#     in the IG profile square crop (the centre 1080x1080 of the
#     1080x1350 portrait). So the emoji centre lives around y=675.
#   - Greeting stays small + centred above the emoji so the card
#     still reads instantly even at thumbnail size.
#   - Emoji rotates daily based on the dominant weather condition
#     across the 6 cities, so the cover changes with the day.
def render_cover(bg, date_label, summary_line, hero_emoji, out_path):
    img = Image.new("RGB", (CARD_W, CARD_H), bg)
    draw = ImageDraw.Draw(img)

    _draw_chrome(img, draw, f"DAILY BRIEFING · {date_label}")

    # ── Greeting (compact, centred) ──
    greet_font = load_font("serif_bold", 72)
    greet_sub_font = load_font("serif_italic", 26)

    line_shona_ndebele = "Mangwanani · Livukile."
    line_country = "Zimbabwe."
    w1 = draw.textlength(line_shona_ndebele, font=greet_font)
    w2 = draw.textlength(line_country, font=greet_font)
    draw.text(((CARD_W - w1) // 2, 210), line_shona_ndebele,
              font=greet_font, fill=CARD_FG)
    draw.text(((CARD_W - w2) // 2, 290), line_country,
              font=greet_font, fill=ACCENT)

    sub = "Good morning, Zimbabwe · in Shona & Ndebele"
    sub_w = draw.textlength(sub, font=greet_sub_font)
    draw.text(((CARD_W - sub_w) // 2, 385), sub,
              font=greet_sub_font, fill=CARD_FG_MUTED)

    # ── BIG hero emoji (dominant) ──
    # Twemoji at size N renders roughly NxN pixels. We push to ~440 so
    # the emoji really dominates the card — and lives in the IG-square
    # crop zone (centre of the card).
    emoji_font = load_font("sans_bold", 440)
    emoji = hero_emoji or "☀️"
    # Centre horizontally; offset y so emoji centre is around y≈700
    _draw_emoji(img, draw, (CARD_W // 2 - 220, 500), emoji,
                emoji_font, CARD_FG)

    # ── Tagline below the emoji ──
    tagline_font = load_font("serif_italic", 30)
    tagline = summary_line or "Weather, news, and wisdom from home."
    lines = wrap_text(draw, tagline, tagline_font, CARD_W - 120)[:2]
    ty = 1090
    for ln in lines:
        w = draw.textlength(ln, font=tagline_font)
        draw.text(((CARD_W - w) // 2, ty), ln,
                  font=tagline_font, fill=CARD_FG)
        ty += 38

    # ── Swipe hint ──
    swipe_font = load_font("sans_bold", 22)
    swipe_text = "SWIPE FOR TODAY'S FORECAST"
    sw = draw.textlength(swipe_text, font=swipe_font)
    draw.text(((CARD_W - sw) // 2, CARD_H - 130), swipe_text,
              font=swipe_font, fill=ACCENT)

    img.save(out_path, "PNG", optimize=True)


def dominant_emoji(cities):
    """Return the most common weather emoji across the cities. Falls
    back to the first city's emoji, then to ☀️."""
    from collections import Counter
    emojis = [c.get("emoji") for c in cities if c.get("emoji")]
    if not emojis:
        return "☀️"
    counter = Counter(emojis)
    # If there's a tie, prefer the more visually distinctive option
    # (e.g. ⛈️ over ☁️) so the cover stays interesting.
    most_common = counter.most_common()
    top_count = most_common[0][1]
    tied = [e for e, n in most_common if n == top_count]
    priority = ["⛈️", "🌧️", "🌦️", "❄️", "🌫️", "⛅", "🌤️", "☁️", "☀️"]
    for p in priority:
        if p in tied:
            return p
    return tied[0]


# ── Slides 2..7: City forecasts ───────────────────────────
# Each city gets one slide. Visual hierarchy (top → bottom):
#   1. City name (centred serif, with an accent underline)
#   2. Big emoji — the visual anchor
#   3. Hero high / low temp (huge serif)
#   4. Condition label (italic serif, soft tone)
#   5. One supporting stat: chance of rain
#
# We deliberately dropped the humidity/wind row — three competing
# numbers diluted the slide. Rain chance is the only metric a Zim
# diaspora reader actually needs to share with family.
def render_city(bg, city, date_label, out_path):
    img = Image.new("RGB", (CARD_W, CARD_H), bg)
    draw = ImageDraw.Draw(img)

    _draw_chrome(img, draw, f"WEATHER · {date_label}")

    # ── City name ──
    name_font = load_font("serif_bold", 96)
    name = city["city"].upper()
    name_w = draw.textlength(name, font=name_font)
    name_y = 200
    draw.text(((CARD_W - name_w) // 2, name_y), name,
              font=name_font, fill=CARD_FG)

    # Accent underline — short, centred, signature touch
    rule_y = name_y + 122
    rule_w = 80
    draw.rectangle([
        ((CARD_W - rule_w) // 2, rule_y),
        ((CARD_W + rule_w) // 2, rule_y + 4),
    ], fill=ACCENT)

    # ── Big emoji (centred) ──
    emoji_font = load_font("sans_bold", 300)
    emoji = city.get("emoji", "")
    if emoji:
        _draw_emoji(img, draw, (CARD_W // 2 - 175, 400), emoji,
                    emoji_font, CARD_FG)

    # ── Hero temp ──
    temp_font = load_font("serif_bold", 158)
    high = city.get("high")
    low = city.get("low")
    temp_y = 760
    if high is not None and low is not None:
        temp_str = f"{round(high)}°"
        slash_str = "  /  "
        low_str = f"{round(low)}°"
        # Render high in CARD_FG, then a muted slash, then low in muted
        high_w = draw.textlength(temp_str, font=temp_font)
        slash_w = draw.textlength(slash_str, font=temp_font)
        low_w = draw.textlength(low_str, font=temp_font)
        total = high_w + slash_w + low_w
        start_x = (CARD_W - total) // 2
        draw.text((start_x, temp_y), temp_str,
                  font=temp_font, fill=CARD_FG)
        draw.text((start_x + high_w, temp_y), slash_str,
                  font=temp_font, fill=CARD_FG_MUTED)
        draw.text((start_x + high_w + slash_w, temp_y), low_str,
                  font=temp_font, fill=CARD_FG_MUTED)

    # Tiny "HIGH / LOW" eyebrow under the temps
    micro_font = load_font("sans_bold", 18)
    eyebrow = "HIGH         LOW"
    ew = draw.textlength(eyebrow, font=micro_font)
    draw.text(((CARD_W - ew) // 2, temp_y + 175), eyebrow,
              font=micro_font, fill=CARD_FG_MUTED)

    # ── Condition (italic serif, soft) ──
    cond_font = load_font("serif_italic", 42)
    label = city.get("label") or ""
    if label:
        lw = draw.textlength(label, font=cond_font)
        draw.text(((CARD_W - lw) // 2, 1010), label,
                  font=cond_font, fill=CARD_FG)

    # ── Single supporting stat: chance of rain ──
    rain_pct = city.get("precip_prob")
    if rain_pct is not None:
        rain_font = load_font("sans", 24)
        rain_str = f"Chance of rain: {int(rain_pct)}%"
        rw = draw.textlength(rain_str, font=rain_font)
        draw.text(((CARD_W - rw) // 2, 1080), rain_str,
                  font=rain_font, fill=CARD_FG_MUTED)

    img.save(out_path, "PNG", optimize=True)


# ── Slide N: Tsumo of the day ─────────────────────────────
def render_tsumo(bg, tsumo, date_label, out_path):
    img = Image.new("RGB", (CARD_W, CARD_H), bg)
    draw = ImageDraw.Draw(img)

    _draw_chrome(img, draw, f"TSUMO YEZUVA · {date_label}")

    # Big serif label
    title_font = load_font("serif_bold", 90)
    draw.text((60, 240), "Tsumo", font=title_font, fill=CARD_FG)
    draw.text((60, 340), "yezuva.", font=title_font, fill=ACCENT)
    sub_font = load_font("serif_italic", 30)
    draw.text((60, 450), "Proverb of the day.",
              font=sub_font, fill=CARD_FG_MUTED)

    # Shona text in italic serif, wrapped
    shona = f"“{tsumo['shona']}”"
    shona_font = load_font("serif_italic", 50)
    shona_lines = wrap_text(draw, shona, shona_font, CARD_W - 120)[:4]
    sy = 600
    for ln in shona_lines:
        draw.text((60, sy), ln, font=shona_font, fill=CARD_FG)
        sy += 64

    # English translation below
    en_font = load_font("sans", 30)
    en_lines = wrap_text(draw, tsumo["english"], en_font, CARD_W - 120)[:5]
    sy += 30
    for ln in en_lines:
        draw.text((60, sy), ln, font=en_font, fill=CARD_FG_MUTED)
        sy += 40

    img.save(out_path, "PNG", optimize=True)


# ── Main ──────────────────────────────────────────────────
CITY_SLUGS = {
    "Harare": "harare",
    "Bulawayo": "bulawayo",
    "Mutare": "mutare",
    "Gweru": "gweru",
    "Masvingo": "masvingo",
    "Victoria Falls": "victoria-falls",
}


def main():
    print("=== BUILD WEATHER CAROUSEL ===")
    if not os.path.exists(WEATHER_FILE):
        print(f"  ERROR: {WEATHER_FILE} not found. Run fetch_weather.py first.")
        sys.exit(1)

    with open(WEATHER_FILE) as f:
        weather = json.load(f)
    cities = weather.get("cities") or []
    if not cities:
        print("  ERROR: no cities in payload")
        sys.exit(1)
    tsumo = pick_tsumo()
    if not HAS_PILMOJI:
        print("  NOTE: pilmoji missing — emoji render monochrome.")

    date_label = datetime.now(timezone(timedelta(hours=2))).strftime("%a %d %b %Y").upper()

    # Positive summary line for the cover — pick the most positive
    # condition across the 6 cities so the cover sets an upbeat tone.
    positive_codes = {0, 1, 2}  # clear, mainly clear, partly cloudy
    sunny = sum(1 for c in cities if c.get("code") in positive_codes)
    if sunny >= 4:
        summary_line = f"Mostly sunny across {sunny} of {len(cities)} cities today."
    elif sunny >= 2:
        summary_line = f"Mixed skies — sunshine in {sunny} of {len(cities)} cities."
    else:
        summary_line = "Cloud cover across the country today — stay cosy."

    os.makedirs(OUT_DIR, exist_ok=True)
    slides = []

    # Slide 1: Cover — hero emoji rotates with today's weather so the
    # cover visibly changes day-to-day on the IG/profile grid.
    cover_path = os.path.join(OUT_DIR, "weather-1-cover.png")
    hero_emoji = dominant_emoji(cities)
    render_cover(PALETTE[0], date_label, summary_line, hero_emoji, cover_path)
    slides.append({"index": 1, "type": "cover", "path": cover_path,
                   "hero_emoji": hero_emoji})
    print(f"  1 · cover ({hero_emoji})  → {os.path.basename(cover_path)}")

    # Slides 2..7: Cities (one per city, in the order returned by fetcher)
    for i, c in enumerate(cities[:6]):
        slug = CITY_SLUGS.get(c["city"], c["city"].lower().replace(" ", "-"))
        slide_idx = i + 2
        path = os.path.join(OUT_DIR, f"weather-{slide_idx}-{slug}.png")
        bg = PALETTE[(slide_idx - 1) % len(PALETTE)]
        render_city(bg, c, date_label, path)
        slides.append({"index": slide_idx, "type": "city",
                       "city": c["city"], "path": path})
        print(f"  {slide_idx} · {c['city']:<15} → {os.path.basename(path)}")

    # Final slide: Tsumo
    final_idx = len(slides) + 1
    tsumo_path = os.path.join(OUT_DIR, f"weather-{final_idx}-tsumo.png")
    render_tsumo(PALETTE[(final_idx - 1) % len(PALETTE)],
                 tsumo, date_label, tsumo_path)
    slides.append({"index": final_idx, "type": "tsumo", "path": tsumo_path,
                   "shona": tsumo["shona"], "english": tsumo["english"]})
    print(f"  {final_idx} · tsumo           → {os.path.basename(tsumo_path)}")

    # The cover is also the canonical single-image fallback (RSS autolist,
    # OG image on landing pages, etc.). Symlink it via filename copy.
    legacy_path = os.path.join(OUT_DIR, "weather-snapshot.png")
    import shutil
    shutil.copyfile(cover_path, legacy_path)
    print(f"  Cover copied to weather-snapshot.png (single-image fallback)")

    # Carousel manifest so consumers (Metricool CSV pipeline, Insta API
    # client, future feed enhancements) can pick up the slide order +
    # URLs without re-listing img/cards/.
    BASE_PUBLIC = "https://www.mutapatimes.com/img/cards"
    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "date_label": date_label,
        "tsumo": tsumo,
        "slides": [
            {**{k: v for k, v in s.items() if k != "path"},
             "url": f"{BASE_PUBLIC}/{os.path.basename(s['path'])}"}
            for s in slides
        ],
    }
    with open(CAROUSEL_MANIFEST, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print(f"  Manifest → {CAROUSEL_MANIFEST}")
    print("\n=== DONE ===")


if __name__ == "__main__":
    main()
