#!/usr/bin/env python3
"""Render the daily portrait economy card — 1080x1350 PNG that is the
hero image for the dedicated economy autolist.

Day-of-year rotation through 31 distinct stat angles (see
scripts/economy_chapters.py) so no stat repeats inside any 30-day
calendar window. This matters: ZimStat / RBZ often does not refresh
quarterly data for months at a time, so a small rotation set would
quickly look repetitive on the social feeds.

Output: img/cards/economy-snapshot.png  (overwritten daily).
"""
import os
import sys
from datetime import datetime, timezone, timedelta

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("ERROR: Pillow not installed. Run: pip install Pillow")
    sys.exit(1)

# Shared chapter library — single source of truth for facts + RSS text.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from economy_chapters import (   # noqa: E402
    pick_chapter_for_today, num_chapters,
)

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT_DIR = os.path.join(ROOT, "img", "cards")
OUT_FILE = os.path.join(OUT_DIR, "economy-snapshot.png")

# ── Brand palette (matches the card library) ──────────────────
CARD_W = 1080
CARD_H = 1350
CARD_FG = (26, 26, 26)
CARD_FG_MUTED = (95, 92, 84)
ACCENT = (192, 57, 43)
CHART_BAR_PRIMARY = (192, 57, 43)
CHART_BAR_SECONDARY = (26, 127, 55)
CHART_BAR_MUTED = (180, 178, 165)


FONT_ROLES = {
    "serif_bold": [
        "fonts/PlayfairDisplay-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
        "/System/Library/Fonts/Supplemental/Georgia Bold.ttf",
        "/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf",
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


def wrap_text(draw, text, font, max_width):
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


def fmt_money_compact(n):
    if n is None:
        return "—"
    abs_v = abs(n)
    sign = "−" if n < 0 else ""
    if abs_v >= 1e9: return f"{sign}${abs_v / 1e9:.1f}B"
    if abs_v >= 1e6: return f"{sign}${abs_v / 1e6:.0f}M"
    if abs_v >= 1e3: return f"{sign}${abs_v / 1e3:.0f}K"
    return f"{sign}${abs_v:,.0f}"


def fmt_pct(n):
    if n is None:
        return "—"
    sign = "+" if n >= 0 else "−"
    return f"{sign}{abs(n):.1f}%"


# ── Mini-chart rendering ──────────────────────────────────────
def draw_mini_chart(draw, bars, x0, y0, w, h, unit_label):
    """Horizontal bar chart, editorial. `bars` is a list of
    (label, value, is_highlight). Values can be raw USD or %; we infer
    the formatting from the unit label."""
    if not bars:
        return
    abs_vals = [abs(v) for _, v, _ in bars if v is not None]
    max_v = max(abs_vals) if abs_vals else 1
    label_w = 240
    bar_x0 = x0 + label_w
    bar_max_w = w - label_w - 90

    row_h = h // max(1, len(bars))
    bar_h = max(18, min(38, row_h - 16))

    label_font = load_font("sans_bold", 22)
    value_font = load_font("sans_bold", 24)
    axis_font = load_font("sans", 18)

    is_pct = "%" in (unit_label or "")

    for i, (label, value, highlight) in enumerate(bars):
        if value is None:
            continue
        cy = y0 + i * row_h + (row_h - bar_h) // 2

        # Truncate long labels to fit
        lbl = label
        while draw.textlength(lbl, font=label_font) > label_w - 16 and len(lbl) > 6:
            lbl = lbl[:-2]
        if lbl != label:
            lbl = lbl.rstrip() + "…"
        draw.text((x0, cy + (bar_h - 22) // 2), lbl,
                  font=label_font, fill=CARD_FG)

        bar_w = int((abs(value) / max_v) * bar_max_w) if max_v else 0
        if highlight:
            color = ACCENT
        elif value < 0:
            color = CHART_BAR_SECONDARY
        else:
            color = CHART_BAR_MUTED
        draw.rectangle([(bar_x0, cy), (bar_x0 + bar_w, cy + bar_h)],
                       fill=color)

        val_str = fmt_pct(value) if is_pct else fmt_money_compact(value)
        draw.text((bar_x0 + bar_w + 12, cy + (bar_h - 24) // 2),
                  val_str, font=value_font, fill=CARD_FG)

    draw.text((x0, y0 + h + 6), unit_label, font=axis_font, fill=CARD_FG_MUTED)


# ── Card rendering ────────────────────────────────────────────
def render_card(chapter, out_path, date_label):
    """Render one chapter dict into a 1080x1350 PNG. No italics; two
    fonts only (Playfair Display headlines + Inter for everything else)."""
    bg = chapter.get("bg", (245, 232, 200))
    img = Image.new("RGB", (CARD_W, CARD_H), bg)
    draw = ImageDraw.Draw(img)

    masthead_font = load_font("serif_bold", 38)
    date_font = load_font("sans_bold", 22)
    eyebrow_font = load_font("sans_bold", 22)
    head_font = load_font("serif_bold", 58)
    big_font = load_font("serif_bold", 168)
    big_lbl_font = load_font("sans_bold", 34)
    sub_font = load_font("sans", 27)
    footer_font = load_font("sans_bold", 22)
    footer_src_font = load_font("sans", 20)

    # Chrome
    draw.rectangle([(0, 0), (140, 10)], fill=ACCENT)
    draw.text((60, 60), "THE MUTAPA TIMES",
              font=masthead_font, fill=CARD_FG)
    draw.text((60, 114), f"ZIM ECONOMY · {date_label}",
              font=date_font, fill=ACCENT)

    # Eyebrow + headline
    draw.text((60, 198), chapter["eyebrow"],
              font=eyebrow_font, fill=CARD_FG_MUTED)
    head_lines = wrap_text(draw, chapter["headline"], head_font, CARD_W - 120)[:2]
    hy = 244
    for ln in head_lines:
        draw.text((60, hy), ln, font=head_font, fill=CARD_FG)
        hy += 72

    # Big number
    big_y = hy + 26
    draw.text((60, big_y), chapter["big_num"],
              font=big_font, fill=CARD_FG)
    draw.text((60, big_y + 188), chapter["big_lbl"].upper(),
              font=big_lbl_font, fill=ACCENT)

    # Sub-caption (up to 3 wrapped lines)
    sub_y = big_y + 248
    sub_lines = wrap_text(draw, chapter["sub"], sub_font, CARD_W - 120)[:3]
    for ln in sub_lines:
        draw.text((60, sub_y), ln, font=sub_font, fill=CARD_FG)
        sub_y += 38

    # Divider
    div_y = sub_y + 22
    draw.line([(60, div_y), (CARD_W - 60, div_y)],
              fill=CARD_FG_MUTED, width=1)

    # Mini-chart
    chart_x0 = 60
    chart_y0 = div_y + 28
    chart_w = CARD_W - 120
    chart_h = min(260, CARD_H - chart_y0 - 180)
    draw_mini_chart(draw, chapter["bars"], chart_x0, chart_y0,
                    chart_w, chart_h, chapter["bar_unit"])

    # Footer
    cta_y = CARD_H - 130
    draw.line([(60, cta_y - 18), (CARD_W - 60, cta_y - 18)],
              fill=CARD_FG_MUTED, width=1)
    draw.text((60, cta_y), "Read the full briefing →",
              font=footer_font, fill=CARD_FG)
    draw.text((60, cta_y + 32), "mutapatimes.com/economy",
              font=footer_font, fill=ACCENT)
    draw.text((60, cta_y + 70), chapter["footer_src"],
              font=footer_src_font, fill=CARD_FG_MUTED)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    img.save(out_path, "PNG", optimize=True)


# ── CLI entrypoint ────────────────────────────────────────────
def main():
    print("=== BUILD ECONOMY CARD ===")
    # --chapter N runs a specific chapter (for local testing); default = today.
    override = None
    for flag in ("--chapter", "--day", "--idx"):
        if flag in sys.argv:
            try:
                override = int(sys.argv[sys.argv.index(flag) + 1])
            except (ValueError, IndexError):
                print(f"  ERROR: {flag} requires an integer 0-{num_chapters() - 1}")
                sys.exit(1)
            break

    idx, day_name, chapter = pick_chapter_for_today(override=override)
    print(f"  Day: {day_name}  Chapter {idx}/{num_chapters() - 1} → {chapter['key']}")

    cat = datetime.now(timezone(timedelta(hours=2)))
    date_label = cat.strftime("%a %d %b %Y").upper()
    out = OUT_FILE
    if override is not None:
        out = os.path.join(OUT_DIR, f"economy-snapshot-ch{idx:02d}.png")
    render_card(chapter, out, date_label)
    print(f"  Wrote {out}")
    print(f"  Eyebrow:  {chapter['eyebrow']}")
    print(f"  Headline: {chapter['headline']}")
    print(f"  Big:      {chapter['big_num']} — {chapter['big_lbl']}")
    print("\n=== DONE ===")


if __name__ == "__main__":
    main()
