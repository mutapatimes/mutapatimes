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
def _setup(title, subtitle, source,
           header="RUKA HAIR LTD.  ·  COMPANIES HOUSE  ·  £'000"):
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
    draw.text((60, 100), header, font=sans, fill=CARD_FG_MUTED)
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
        "Working capital, three snapshots before the new round",
        "Inventory peaked in the 18 months to April 2024 then ran down 39%. Debtors compressed 43%. Cash rebuilt from £40k to £399k, almost entirely from working-capital release rather than fresh equity.",
        "Source: Ruka Hair Ltd. unaudited abridged accounts at Companies House — 12 months to 31 Oct 2022, 18 months to 30 Apr 2024, 12 months to 30 Apr 2025.",
    )
    # Three periods: Oct 2022 (12mo), Apr 2024 (18mo), Apr 2025 (12mo)
    # values in £'000
    series = [
        ("Stocks",        593.9, 727.5, 447.2),
        ("Debtors",       251.3, 602.4, 342.3),
        ("Cash at bank",   10.8,  40.0, 398.7),
        ("Creditors <1y", 306.6, 900.0, 823.7),
    ]
    chart_x0, chart_y0 = 100, 380
    chart_x1, chart_y1 = 1340, 800
    chart_w = chart_x1 - chart_x0
    chart_h = chart_y1 - chart_y0
    max_val = 1000
    grid_font = load_font("sans", 16)
    for v in (0, 250, 500, 750, 1000):
        y = chart_y1 - int((v / max_val) * chart_h)
        draw.line([(chart_x0, y), (chart_x1, y)], fill=HAIRLINE, width=1)
        draw.text((chart_x0 - 80, y - 10), f"{v}", font=grid_font, fill=INK_SOFT)
    n = len(series)
    group_w = chart_w / n
    bar_w = group_w * 0.21
    gap = group_w * 0.03
    label_font = load_font("sans_bold", 18)
    val_font = load_font("sans_bold", 15)
    MUTED_BAR = (140, 132, 110)  # Oct 2022 column — muted tan
    for i, (label, v22, v24, v25) in enumerate(series):
        gx = chart_x0 + group_w * i + group_w * 0.5
        cols = [(v22, MUTED_BAR), (v24, NAVY), (v25, ACCENT)]
        for ci, (v, col) in enumerate(cols):
            offset = (ci - 1) * (bar_w + gap)
            x1 = gx + offset - bar_w / 2
            x2 = gx + offset + bar_w / 2
            y_top = chart_y1 - int((v / max_val) * chart_h)
            draw.rectangle([x1, y_top, x2, chart_y1], fill=col)
            draw.text((x1 - 6, y_top - 22),
                      f"£{int(v)}", font=val_font, fill=col)
        bb = draw.textbbox((0, 0), label, font=label_font)
        lx = gx - (bb[2] - bb[0]) // 2
        draw.text((lx, chart_y1 + 14), label, font=label_font, fill=CARD_FG)
    # Legend
    legend_x, legend_y = 1080, 320
    swatch = 18
    leg_font = load_font("sans_bold", 16)
    items = [
        ("12 months to Oct 2022", MUTED_BAR),
        ("18 months to Apr 2024", NAVY),
        ("12 months to Apr 2025", ACCENT),
    ]
    for li, (txt, col) in enumerate(items):
        y = legend_y + li * 26
        draw.rectangle([legend_x, y, legend_x + swatch, y + swatch], fill=col)
        draw.text((legend_x + 26, y + 1), txt, font=leg_font, fill=CARD_FG)
    return _save(img, "chart-balance-sheet.png")


# ── 2. Capital structure / runway ───────────────────────
def chart_capital_structure():
    img, draw = _setup(
        "Capital raised against losses accumulated, four-period arc",
        "Equity raised has tracked accumulated losses with a thinning buffer through 2022 to 2025. The April 2026 round (the $4.5m, struck at ~$1.32/£) is the first vertical move on the equity line in twelve months.",
        "Source: Companies House abridged accounts (Oct 2022, Apr 2024, Apr 2025) + SH01 share allotment filing (Apr 2026). Interim 12 months to Apr 2026 not yet public.",
    )
    # Time-series points: (label, equity raised £'000, accumulated losses £'000)
    pts = [
        ("Oct 2022", 3381.8, -2821.6),
        ("Apr 2024", 4544.4, -4065.8),
        ("Apr 2025", 4896.4, -4528.5),
        ("Apr 2026\n(post-round)", 8296.4, -4528.5),  # add ~£3.4m new round
    ]
    chart_x0, chart_y0 = 110, 380
    chart_x1, chart_y1 = 1340, 750
    chart_w = chart_x1 - chart_x0
    chart_h = chart_y1 - chart_y0
    max_pos = 9000
    min_neg = -5500
    zero_y = chart_y0 + int((max_pos / (max_pos - min_neg)) * chart_h)
    # Zero baseline
    draw.line([(chart_x0, zero_y), (chart_x1, zero_y)], fill=CARD_FG, width=2)
    grid_font = load_font("sans", 16)
    for v in (-5000, -2500, 0, 2500, 5000, 7500):
        y = chart_y0 + int(((max_pos - v) / (max_pos - min_neg)) * chart_h)
        if v != 0:
            draw.line([(chart_x0, y), (chart_x1, y)], fill=HAIRLINE, width=1)
        draw.text((chart_x0 - 90, y - 10),
                  f"£{v//1000:+d}k" if v else "£0",
                  font=grid_font, fill=INK_SOFT)

    n = len(pts)
    x_step = chart_w / (n - 1)
    label_font = load_font("sans_bold", 18)
    val_font = load_font("sans_bold", 18)
    # Compute pixel coords
    def _to_xy(i, v):
        x = chart_x0 + int(i * x_step)
        y = chart_y0 + int(((max_pos - v) / (max_pos - min_neg)) * chart_h)
        return x, y
    eq_pts, loss_pts = [], []
    for i, (_, eq, loss) in enumerate(pts):
        eq_pts.append(_to_xy(i, eq))
        loss_pts.append(_to_xy(i, loss))
    # Shade the gap between the two lines (net shareholder funds region)
    gap_poly = eq_pts + loss_pts[::-1]
    from PIL import ImageDraw as _D  # noqa
    # Use a translucent shade by drawing a lighter polygon
    GAP = (230, 220, 195)
    draw.polygon(gap_poly, fill=GAP)
    # Draw lines
    for i in range(len(pts) - 1):
        draw.line([eq_pts[i], eq_pts[i + 1]], fill=NAVY, width=4)
        draw.line([loss_pts[i], loss_pts[i + 1]], fill=ACCENT, width=4)
    # Dots and value labels
    dot_r = 8
    for i, (lbl, eq, loss) in enumerate(pts):
        ex, ey = eq_pts[i]
        lx, ly = loss_pts[i]
        draw.ellipse([ex - dot_r, ey - dot_r, ex + dot_r, ey + dot_r], fill=NAVY)
        draw.ellipse([lx - dot_r, ly - dot_r, lx + dot_r, ly + dot_r], fill=ACCENT)
        draw.text((ex - 28, ey - 36), f"£{eq/1000:.2f}m",
                  font=val_font, fill=NAVY)
        draw.text((lx - 28, ly + 14), f"-£{abs(loss)/1000:.2f}m",
                  font=val_font, fill=ACCENT)
        # x-axis date label
        for li, line in enumerate(lbl.split("\n")):
            bb = draw.textbbox((0, 0), line, font=label_font)
            tx = ex - (bb[2] - bb[0]) // 2
            draw.text((tx, chart_y1 + 14 + li * 22),
                      line, font=label_font, fill=CARD_FG)

    # Legend top-right
    legend_x = 1080
    legend_y = 320
    leg_font = load_font("sans_bold", 16)
    draw.rectangle([legend_x, legend_y, legend_x + 18, legend_y + 18], fill=NAVY)
    draw.text((legend_x + 26, legend_y + 1),
              "Cumulative equity raised", font=leg_font, fill=CARD_FG)
    draw.rectangle([legend_x, legend_y + 26, legend_x + 18, legend_y + 44],
                   fill=ACCENT)
    draw.text((legend_x + 26, legend_y + 27),
              "Accumulated P&L losses", font=leg_font, fill=CARD_FG)
    draw.rectangle([legend_x, legend_y + 52, legend_x + 18, legend_y + 70],
                   fill=GAP)
    draw.text((legend_x + 26, legend_y + 53),
              "Net shareholder funds", font=leg_font, fill=CARD_FG)
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


# ── 5. Google Trends time series ────────────────────────
def chart_search_trend():
    img, draw = _setup(
        "Consumer demand for 'ruka hair' has compounded since launch",
        "Google Trends index, May 2021 to May 2026. Search interest crossed 30 in 2022 (Selfridges entry), peaked at 100 in mid-2023, and from late 2023 has held a structurally higher base of 50 to 90.",
        "Source: Google Trends, worldwide, query 'ruka hair', monthly, May 2021–May 2026. May 2026 is a partial month.",
        header="RUKA HAIR LTD.  ·  GOOGLE TRENDS  ·  WORLDWIDE INDEX",
    )
    # 60 monthly data points (May 2021..May 2026)
    series = [
        ("2021-05",13),("2021-06",10),("2021-07",13),("2021-08",10),
        ("2021-09",0),("2021-10",17),("2021-11",13),("2021-12",17),
        ("2022-01",17),("2022-02",37),("2022-03",37),("2022-04",33),
        ("2022-05",30),("2022-06",40),("2022-07",30),("2022-08",40),
        ("2022-09",37),("2022-10",43),("2022-11",47),("2022-12",43),
        ("2023-01",43),("2023-02",47),("2023-03",47),("2023-04",50),
        ("2023-05",40),("2023-06",43),("2023-07",100),("2023-08",77),
        ("2023-09",50),("2023-10",47),("2023-11",70),("2023-12",50),
        ("2024-01",40),("2024-02",43),("2024-03",43),("2024-04",50),
        ("2024-05",47),("2024-06",50),("2024-07",47),("2024-08",50),
        ("2024-09",47),("2024-10",50),("2024-11",57),("2024-12",57),
        ("2025-01",53),("2025-02",50),("2025-03",90),("2025-04",57),
        ("2025-05",50),("2025-06",60),("2025-07",53),("2025-08",87),
        ("2025-09",60),("2025-10",60),("2025-11",90),("2025-12",63),
        ("2026-01",60),("2026-02",53),("2026-03",70),("2026-04",67),
        ("2026-05",43),
    ]
    chart_x0, chart_y0 = 110, 380
    chart_x1, chart_y1 = 1340, 770
    chart_w = chart_x1 - chart_x0
    chart_h = chart_y1 - chart_y0
    max_val = 100
    n = len(series)
    # Y-axis grid
    grid_font = load_font("sans", 16)
    for v in (0, 25, 50, 75, 100):
        y = chart_y1 - int((v / max_val) * chart_h)
        draw.line([(chart_x0, y), (chart_x1, y)], fill=HAIRLINE, width=1)
        draw.text((chart_x0 - 60, y - 10), f"{v}", font=grid_font, fill=INK_SOFT)
    x_step = chart_w / (n - 1)
    pts = []
    for i, (_, v) in enumerate(series):
        x = chart_x0 + int(i * x_step)
        y = chart_y1 - int((v / max_val) * chart_h)
        pts.append((x, y))
    # Area under curve, muted
    AREA = (235, 220, 195)
    area_poly = pts + [(pts[-1][0], chart_y1), (pts[0][0], chart_y1)]
    draw.polygon(area_poly, fill=AREA)
    # Line itself
    for i in range(len(pts) - 1):
        draw.line([pts[i], pts[i + 1]], fill=ACCENT, width=3)
    # Year tick labels at Jan of each year
    year_font = load_font("sans_bold", 16)
    for i, (date, _) in enumerate(series):
        yr = date[:4]
        mo = date[5:7]
        if mo == "01" or i == 0:
            x = chart_x0 + int(i * x_step)
            draw.line([(x, chart_y1), (x, chart_y1 + 6)], fill=CARD_FG, width=1)
            bb = draw.textbbox((0, 0), yr, font=year_font)
            draw.text((x - (bb[2] - bb[0]) // 2, chart_y1 + 12),
                      yr, font=year_font, fill=CARD_FG)
    # Annotations on key peaks
    annot_font = load_font("sans_bold", 14)
    annotations = [
        (26, "Peak 100\n(Jul 2023)",   30),   # index 26 = 2023-07 — below peak
        (46, "Mar 2025: 90",          -50),   # index 46 = 2025-03
        (52, "Aug 2025: 87",          -90),   # 2025-08 — push higher
        (54, "Nov 2025: 90",          -50),   # 2025-11
    ]
    for idx, label, dy in annotations:
        if idx >= len(pts):
            continue
        px, py = pts[idx]
        # small marker dot
        draw.ellipse([px - 5, py - 5, px + 5, py + 5], fill=NAVY)
        # leader line + text
        text_y = py + dy
        draw.line([(px, py), (px, text_y + 14)], fill=NAVY, width=1)
        for li, line in enumerate(label.split("\n")):
            draw.text((px + 6, text_y + li * 16),
                      line, font=annot_font, fill=NAVY)
    return _save(img, "chart-search-trend.png")


def main():
    print("=== Build Ruka launch charts ===")
    chart_balance_sheet()
    chart_capital_structure()
    chart_geography()
    chart_pricing()
    chart_search_trend()
    print("=== DONE ===")


if __name__ == "__main__":
    main()
