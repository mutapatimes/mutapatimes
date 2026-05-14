#!/usr/bin/env python3
"""Render 4 financial charts for the Ruka Hair article. PIL-only,
on-brand (butter background, Playfair labels, Inter ticks, accent red
emphasis). Each chart is 1400x900 px so it crisps on retina.

Charts:
  1. balance-sheet.png      — working-capital swing: stocks, debtors,
                              cash, creditors over 2024 vs 2025
  2. capital-structure.png  — equity raised vs accumulated losses vs
                              net assets, before and after the round
  3. geography.png          — donut, customer geographic mix
  4. pricing.png            — synths-2 vs human-hair bundle, $
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from card_lib import BUTTER, CARD_FG, CARD_FG_MUTED, ACCENT, load_font, wrap_text

from PIL import Image, ImageDraw

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT_DIR = os.path.join(ROOT, "img", "uploads", "ruka-launch")
SIZE = (1400, 900)
INK_SOFT = (90, 88, 80)
HAIRLINE = (200, 192, 168)
NAVY = (38, 56, 92)        # secondary chart colour (2024 period bars)


# ── Common chart chrome ───────────────────────────────────
def _setup(title, subtitle, source):
    img = Image.new("RGB", SIZE, BUTTER)
    draw = ImageDraw.Draw(img)
    w, h = SIZE
    # Top-left brand
    serif = load_font("serif_bold", 28)
    draw.text((60, 50), "THE MUTAPA TIMES", font=serif, fill=CARD_FG)
    # accent rule
    draw.rectangle([60, 88, 110, 92], fill=ACCENT)
    # Top-right small label
    sans = load_font("sans_bold", 18)
    draw.text((60, 100), "RUKA HAIR LTD.  ·  COMPANIES HOUSE  ·  £'000",
              font=sans, fill=CARD_FG_MUTED)
    # Title block — wrap to canvas width
    title_font = load_font("serif_bold", 48)
    max_text_w = w - 120
    t_lines = wrap_text(title, title_font, max_text_w, draw)[:2]
    ty = 150
    for line in t_lines:
        draw.text((60, ty), line, font=title_font, fill=CARD_FG)
        ty += 56
    sub_font = load_font("sans", 22)
    s_lines = wrap_text(subtitle, sub_font, max_text_w, draw)[:3]
    sy = ty + 10
    for line in s_lines:
        draw.text((60, sy), line, font=sub_font, fill=INK_SOFT)
        sy += 30
    # Footer source
    foot_font = load_font("sans", 16)
    draw.text((60, h - 50), source, font=foot_font, fill=CARD_FG_MUTED)
    return img, draw


def _save(img, name):
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, name)
    img.save(path, "PNG")
    print(f"  {SIZE[0]}x{SIZE[1]}  {name}  ({os.path.getsize(path)//1024} KB)")
    return path


# ── 1. Balance-sheet bars ────────────────────────────────
def chart_balance_sheet():
    img, draw = _setup(
        "Working capital cycle tightened over the year to April 2025",
        "Stocks down 39%, debtors down 43%, cash up nearly tenfold over the 12 months to April 2025. The most recent public picture, a year before the new round.",
        "Source: Companies House, Ruka Hair Ltd. unaudited abridged accounts, year to 30 April 2025. Next filing due January 2027.",
    )
    # Data — values in £'000
    series = [
        ("Stocks",       727.5, 447.2),
        ("Debtors",      602.4, 342.3),
        ("Cash at bank", 40.0,  398.7),
        ("Creditors <1y",900.0, 823.7),
    ]
    chart_x0, chart_y0 = 80, 360
    chart_x1, chart_y1 = 1340, 800
    chart_w = chart_x1 - chart_x0
    chart_h = chart_y1 - chart_y0
    max_val = 1000  # round up from 900 creditors so axis breathes
    # y-axis grid lines (every 250)
    grid_font = load_font("sans", 16)
    for v in (0, 250, 500, 750, 1000):
        y = chart_y1 - int((v / max_val) * chart_h)
        draw.line([(chart_x0, y), (chart_x1, y)], fill=HAIRLINE, width=1)
        draw.text((chart_x0 - 60, y - 10), f"{v}", font=grid_font, fill=INK_SOFT)
    # Bars: 4 groups of 2
    n = len(series)
    group_w = chart_w / n
    bar_w = group_w * 0.32
    gap = group_w * 0.05
    label_font = load_font("sans_bold", 18)
    val_font = load_font("sans_bold", 18)
    for i, (label, v_old, v_new) in enumerate(series):
        gx = chart_x0 + group_w * i + group_w * 0.5
        # Old (2024) bar — navy
        x1 = gx - bar_w - gap
        x2 = gx - gap
        y_top = chart_y1 - int((v_old / max_val) * chart_h)
        draw.rectangle([x1, y_top, x2, chart_y1], fill=NAVY)
        draw.text((x1, y_top - 26),
                  f"£{int(v_old)}", font=val_font, fill=NAVY)
        # New (2025) bar — accent
        x1 = gx + gap
        x2 = gx + bar_w + gap
        y_top = chart_y1 - int((v_new / max_val) * chart_h)
        draw.rectangle([x1, y_top, x2, chart_y1], fill=ACCENT)
        draw.text((x1, y_top - 26),
                  f"£{int(v_new)}", font=val_font, fill=ACCENT)
        # Label below
        bb = draw.textbbox((0, 0), label, font=label_font)
        lx = gx - (bb[2] - bb[0]) // 2
        draw.text((lx, chart_y1 + 14), label, font=label_font, fill=CARD_FG)
    # Legend top-right of chart area
    legend_y = 320
    draw.rectangle([1080, legend_y, 1100, legend_y + 20], fill=NAVY)
    draw.text((1108, legend_y + 1),
              "18 months to Apr 2024", font=label_font, fill=CARD_FG)
    draw.rectangle([1080, legend_y + 30, 1100, legend_y + 50], fill=ACCENT)
    draw.text((1108, legend_y + 31),
              "Year to Apr 2025", font=label_font, fill=CARD_FG)
    return _save(img, "chart-balance-sheet.png")


# ── 2. Capital structure / runway ───────────────────────
def chart_capital_structure():
    img, draw = _setup(
        "Capital raised against losses accumulated",
        "By April 2025, the last public snapshot, Ruka had absorbed £4.53m in cumulative losses against £4.89m of equity raised. The new $4.5m round, twelve months later, materially refills the tank.",
        "Source: Companies House abridged accounts (Apr 2025) + SH01 share allotment filing (Apr 2026). Round value converted at $1.32/£. Interim 12 months not yet public.",
    )
    # Values in £'000
    bars = [
        ("Equity raised\n(to Apr 2025)",       4894, NAVY),
        ("Accumulated losses\n(to Apr 2025)",  -4528, ACCENT),
        ("Net shareholder\nfunds Apr 2025",    368, CARD_FG),
        ("New round\n(Apr 2026, ~£3.4m)",      3400, (210, 160, 60)),
        ("Implied post-money\nnet assets",     3768, NAVY),
    ]
    chart_x0, chart_y0 = 80, 360
    chart_x1, chart_y1 = 1340, 770
    chart_w = chart_x1 - chart_x0
    chart_h = chart_y1 - chart_y0
    max_pos = 5000
    min_neg = -5000
    zero_y = chart_y0 + int((max_pos / (max_pos - min_neg)) * chart_h)
    # Zero baseline
    draw.line([(chart_x0, zero_y), (chart_x1, zero_y)], fill=CARD_FG, width=2)
    # Grid lines
    grid_font = load_font("sans", 16)
    for v in (-5000, -2500, 0, 2500, 5000):
        y = chart_y0 + int(((max_pos - v) / (max_pos - min_neg)) * chart_h)
        if v != 0:
            draw.line([(chart_x0, y), (chart_x1, y)], fill=HAIRLINE, width=1)
        draw.text((chart_x0 - 70, y - 10), f"{v//1000:+d}k" if v else "0",
                  font=grid_font, fill=INK_SOFT)
    # Bars
    n = len(bars)
    group_w = chart_w / n
    bar_w = group_w * 0.45
    label_font = load_font("sans_bold", 16)
    val_font = load_font("sans_bold", 20)
    for i, (label, v, col) in enumerate(bars):
        gx = chart_x0 + group_w * i + group_w * 0.5
        x1 = gx - bar_w / 2
        x2 = gx + bar_w / 2
        if v >= 0:
            y_top = chart_y0 + int(((max_pos - v) / (max_pos - min_neg)) * chart_h)
            draw.rectangle([x1, y_top, x2, zero_y], fill=col)
            draw.text((x1, y_top - 28),
                      f"£{abs(v)/1000:.2f}m", font=val_font, fill=col)
        else:
            y_bot = chart_y0 + int(((max_pos - v) / (max_pos - min_neg)) * chart_h)
            draw.rectangle([x1, zero_y, x2, y_bot], fill=col)
            draw.text((x1, y_bot + 6),
                      f"-£{abs(v)/1000:.2f}m", font=val_font, fill=col)
        # Label below bottom band
        for li, line in enumerate(label.split("\n")):
            bb = draw.textbbox((0, 0), line, font=label_font)
            lx = gx - (bb[2] - bb[0]) // 2
            draw.text((lx, chart_y1 + 8 + li * 22),
                      line, font=label_font, fill=CARD_FG)
    return _save(img, "chart-capital-structure.png")


# ── 3. Geography donut ──────────────────────────────────
def chart_geography():
    img, draw = _setup(
        "Where Ruka's customers live",
        "47% United States · 48% United Kingdom · 4% European Union · 1% Africa. The next leg of growth is American.",
        "Source: Ruka management figures, May 2026.",
    )
    # Donut centre and radii
    cx, cy = 480, 600
    r_outer = 220
    r_inner = 130
    segments = [
        ("United States",  47, ACCENT),
        ("United Kingdom", 48, NAVY),
        ("European Union", 4,  (210, 160, 60)),
        ("Africa",         1,  CARD_FG),
    ]
    start = -90
    for label, pct, col in segments:
        end = start + (pct / 100.0) * 360.0
        # Pie slice
        draw.pieslice([cx - r_outer, cy - r_outer, cx + r_outer, cy + r_outer],
                      start, end, fill=col)
        start = end
    # Inner hole (donut)
    draw.ellipse([cx - r_inner, cy - r_inner, cx + r_inner, cy + r_inner],
                 fill=BUTTER)
    # Centre label
    centre_serif = load_font("serif_bold", 36)
    centre_sans = load_font("sans_bold", 16)
    draw.text((cx - 90, cy - 36), "47% + 48%",
              font=centre_serif, fill=CARD_FG)
    draw.text((cx - 92, cy + 12),
              "US AND UK", font=centre_sans, fill=ACCENT)
    # Legend on right
    legend_x = 820
    legend_y = 400
    swatch = 22
    legend_label = load_font("sans_bold", 24)
    legend_val = load_font("serif_bold", 30)
    for i, (label, pct, col) in enumerate(segments):
        y = legend_y + i * 100
        draw.rectangle([legend_x, y, legend_x + swatch, y + swatch], fill=col)
        draw.text((legend_x + 40, y - 4), label,
                  font=legend_label, fill=CARD_FG)
        draw.text((legend_x + 40, y + 28), f"{pct}%",
                  font=legend_val, fill=col)
    return _save(img, "chart-geography.png")


# ── 4. Pricing — Synths 2 vs human hair ─────────────────
def chart_pricing():
    img, draw = _setup(
        "The price gap Ruka is trying to invert",
        "Synths 2 collagen-fibre braiding hair sells at $31 a bundle. The equivalent human-hair bundle sells at $170 — 5.5 times the price.",
        "Source: Ruka Hair retail pricing, ruka-hair.com, May 2026.",
    )
    chart_x0, chart_y0 = 200, 360
    chart_x1, chart_y1 = 1240, 770
    chart_h = chart_y1 - chart_y0
    max_val = 200
    # Y-axis ticks
    grid_font = load_font("sans", 18)
    for v in (0, 50, 100, 150, 200):
        y = chart_y1 - int((v / max_val) * chart_h)
        draw.line([(chart_x0, y), (chart_x1, y)], fill=HAIRLINE, width=1)
        draw.text((chart_x0 - 70, y - 12), f"${v}",
                  font=grid_font, fill=INK_SOFT)
    pairs = [
        ("Synths 2\n(collagen fibre)", 31,  ACCENT),
        ("Human hair\n(bundle)",      170,  NAVY),
    ]
    bar_w = 220
    label_font = load_font("sans_bold", 22)
    val_font = load_font("serif_bold", 64)
    sub_font = load_font("sans", 18)
    cx_left, cx_right = 520, 920
    for i, (label, v, col) in enumerate(pairs):
        cx = cx_left if i == 0 else cx_right
        y_top = chart_y1 - int((v / max_val) * chart_h)
        x1, x2 = cx - bar_w // 2, cx + bar_w // 2
        draw.rectangle([x1, y_top, x2, chart_y1], fill=col)
        # Value above the bar
        v_str = f"${v}"
        bb = draw.textbbox((0, 0), v_str, font=val_font)
        draw.text((cx - (bb[2] - bb[0]) // 2, y_top - 84),
                  v_str, font=val_font, fill=col)
        # Label below
        for li, line in enumerate(label.split("\n")):
            bb = draw.textbbox((0, 0), line, font=label_font)
            draw.text((cx - (bb[2] - bb[0]) // 2, chart_y1 + 18 + li * 28),
                      line, font=label_font, fill=CARD_FG)
        draw.text((cx - 60, y_top - 84 + 64 + 6), "per bundle",
                  font=sub_font, fill=CARD_FG_MUTED)
    # Big "5.5x" callout between bars
    multi_font = load_font("serif_bold", 96)
    draw.text((690, chart_y0 + 50), "5.5×",
              font=multi_font, fill=ACCENT)
    callout_font = load_font("sans_bold", 20)
    draw.text((670, chart_y0 + 160),
              "price gap, same use", font=callout_font, fill=ACCENT)
    return _save(img, "chart-pricing.png")


def main():
    print("=== Build Ruka launch charts ===")
    chart_balance_sheet()
    chart_capital_structure()
    chart_geography()
    chart_pricing()
    print("=== DONE ===")


if __name__ == "__main__":
    main()
