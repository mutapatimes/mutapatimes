#!/usr/bin/env python3
"""Render the daily portrait economy card — 1080x1350 PNG that is the
hero image for the dedicated economy autolist.

Day-of-week rotation (CAT) so the daily Metricool post shows a
different angle on the same data each day:

    Mon — GDP composition (largest sector, latest quarter)
    Tue — Trade gap (goods exports vs imports)
    Wed — Top growing sector (biggest YoY gainer)
    Thu — Mining vs Agriculture
    Fri — Diaspora remittances (personal transfers)
    Sat — Top imports vs exports (services balance)
    Sun — The missing money (current account vs net errors)

All numbers from data/gdp-zimbabwe-quarterly.json and
data/zimstat-bop-quarterly.json — no third-party data.

Output: img/cards/economy-snapshot.png  (overwritten daily).
"""
import json
import os
import sys
from datetime import datetime, timezone, timedelta

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("ERROR: Pillow not installed. Run: pip install Pillow")
    sys.exit(1)

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
GDP_FILE = os.path.join(ROOT, "data", "gdp-zimbabwe-quarterly.json")
BOP_FILE = os.path.join(ROOT, "data", "zimstat-bop-quarterly.json")
OUT_DIR = os.path.join(ROOT, "img", "cards")
OUT_FILE = os.path.join(OUT_DIR, "economy-snapshot.png")

# ── Brand palette (matches build_fx_snapshot_card.py) ─────────
CARD_W = 1080
CARD_H = 1350
CARD_FG = (26, 26, 26)
CARD_FG_MUTED = (95, 92, 84)
ACCENT = (192, 57, 43)
BG = (245, 232, 200)        # soft butter — economic / paper feel
BG_ALT = (216, 230, 213)    # sage — used by some chapters
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
    """Format a USD value (raw, not millions) into a compact label."""
    if n is None:
        return "—"
    abs_v = abs(n)
    sign = "−" if n < 0 else ""
    if abs_v >= 1e9:
        return f"{sign}${abs_v / 1e9:.1f}B"
    if abs_v >= 1e6:
        return f"{sign}${abs_v / 1e6:.0f}M"
    if abs_v >= 1e3:
        return f"{sign}${abs_v / 1e3:.0f}K"
    return f"{sign}${abs_v:,.0f}"


def fmt_bop(n_millions):
    """BoP data is stored in millions of USD."""
    if n_millions is None:
        return "—"
    return fmt_money_compact(n_millions * 1e6)


def fmt_pct(n):
    if n is None:
        return "—"
    sign = "+" if n >= 0 else "−"
    return f"{sign}{abs(n):.1f}%"


SHORT_SECTOR = {
    "Wholesale and retail trade; repair of motor vehicles and motorcycles": "Wholesale & retail",
    "Public administration and defence; compulsory social security": "Public admin & defence",
    "Water supply; sewerage, waste management and remediation activities": "Water & waste",
    "Electricity, gas, steam and air conditioning supply": "Electricity & gas",
    "Agiculture, Hunting and Fishing and forestry": "Agriculture",
    "Professional, scientific and technical activities": "Professional & scientific",
    "Administrative and support service activities": "Admin & support",
    "Human health and social work activities": "Health & social work",
    "Arts, entertainment and recreation": "Arts & entertainment",
    "Accommodation and food service activities": "Hospitality",
    "Information and communication": "ICT",
    "Financial and insurance activities": "Finance & insurance",
    "Transportation and storage": "Transport & storage",
    "Mining and quarrying": "Mining",
    "Manufacturing": "Manufacturing",
    "Construction": "Construction",
    "Real estate activities": "Real estate",
    "Education": "Education",
    "Other service activities": "Other services",
}


def short(name):
    return SHORT_SECTOR.get(name, name)


# ── Per-chapter compute functions ─────────────────────────────
# Each returns a dict with:
#   eyebrow   : small all-caps line under the date
#   headline  : the analytical sentence ("Where the money lives")
#   big_num   : the dominant stat ("$11.45B")
#   big_lbl   : caption right below the big number
#   sub       : explanatory caption paragraph
#   bars      : list of (label, value, is_highlight) for the mini-chart
#   bar_unit  : label for the chart axis (e.g. "USD")
#   bg        : background color tuple


def chapter_mon_gdp(gdp, bop):
    """Largest sector — latest quarter."""
    last = len(gdp["quarters"]) - 1
    quarter = gdp["quarters"][last]
    total = gdp["aggregates"]["GDP at Market Prices"][last]
    pairs = [(n, gdp["sectors"][n][last]) for n in gdp["sector_order"]]
    pairs.sort(key=lambda p: p[1], reverse=True)
    top_name, top_val = pairs[0]
    share = (top_val / total) * 100 if total else 0
    second = short(pairs[1][0]) if len(pairs) > 1 else None
    third = short(pairs[2][0]) if len(pairs) > 2 else None
    follow = ""
    if second and third:
        follow = f" {second} and {third} follow."
    elif second:
        follow = f" {second} follows."
    bars = [(short(n), v, n == top_name) for n, v in pairs[:5]]
    return {
        "eyebrow": "GDP COMPOSITION",
        "headline": "Where the money lives.",
        "big_num": fmt_money_compact(top_val),
        "big_lbl": short(top_name),
        "sub": f"The largest sector by gross value added in {quarter} — "
               f"{share:.1f}% of all GDP.{follow}",
        "bars": bars,
        "bar_unit": "USD, latest quarter",
        "bg": BG,
        "footer_src": "Source: ZimStat, Quarterly GDP Tables.",
    }


def chapter_tue_trade(gdp, bop):
    """Trade gap — latest quarter goods exports vs imports."""
    n = len(bop["quarters"])
    last = n - 1
    quarter = bop["quarters"][last]
    exp = bop["series"]["exports_goods"][last]
    imp = bop["series"]["imports_goods"][last]
    gap = (imp or 0) - (exp or 0)
    in_surplus = gap < 0
    bars = [
        ("Exports", (exp or 0) * 1e6, in_surplus),
        ("Imports", (imp or 0) * 1e6, not in_surplus),
    ]
    return {
        "eyebrow": "GOODS TRADE",
        "headline": "The trade balance.",
        "big_num": fmt_bop(abs(gap)),
        "big_lbl": "trade surplus" if in_surplus else "trade deficit",
        "sub": f"In {quarter} Zimbabwe exported {fmt_bop(exp)} of goods "
               f"and imported {fmt_bop(imp)} — the gap has flipped to a "
               f"surplus in recent quarters, driven by mining exports."
               if in_surplus else
               f"In {quarter} Zimbabwe imported {fmt_bop(imp)} of goods "
               f"and exported {fmt_bop(exp)}.",
        "bars": bars,
        "bar_unit": "USD, latest quarter",
        "bg": BG,
        "footer_src": "Source: RBZ / ZimStat, Balance of Payments.",
    }


def chapter_wed_growth(gdp, bop):
    """Biggest YoY gainer in the latest quarter — top-5 movers."""
    last = len(gdp["quarters"]) - 1
    quarter = gdp["quarters"][last]
    movers = []
    for n in gdp["sector_order"]:
        v_now = gdp["sectors"][n][last]
        v_ago = gdp["sectors"][n][last - 4] if last - 4 >= 0 else None
        if v_ago and v_ago > 0:
            yoy_pct = ((v_now - v_ago) / v_ago) * 100
            movers.append((n, yoy_pct, v_now))
    movers.sort(key=lambda x: x[1], reverse=True)
    top_name, top_yoy, top_val = movers[0]
    bars = [(short(n), pct, n == top_name) for n, pct, _ in movers[:5]]
    return {
        "eyebrow": "FASTEST GROWING SECTOR",
        "headline": "Where the growth is.",
        "big_num": fmt_pct(top_yoy),
        "big_lbl": short(top_name) + " YoY",
        "sub": f"Strongest year-on-year growth in {quarter} across all "
               f"19 tracked sectors. Numbers reflect ZimStat's post-2024 "
               f"re-based series.",
        "bars": bars,
        "bar_unit": "YoY %, top 5 sectors",
        "bg": BG_ALT,
        "footer_src": "Source: ZimStat, Quarterly GDP Tables.",
    }


def chapter_thu_mining(gdp, bop):
    """Mining vs Agriculture — latest quarter face-off."""
    last = len(gdp["quarters"]) - 1
    quarter = gdp["quarters"][last]
    mining = gdp["sectors"]["Mining and quarrying"][last]
    agri = gdp["sectors"]["Agiculture, Hunting and Fishing and forestry"][last]
    diff = mining - agri
    leader = "Mining" if mining > agri else "Agriculture"
    bars = [
        ("Mining", mining, leader == "Mining"),
        ("Agriculture", agri, leader == "Agriculture"),
    ]
    return {
        "eyebrow": "TWO GREAT SECTORS",
        "headline": "Mining vs agriculture.",
        "big_num": fmt_money_compact(abs(diff)),
        "big_lbl": f"{leader} leads",
        "sub": f"In {quarter}, mining produced {fmt_money_compact(mining)} "
               f"and agriculture produced {fmt_money_compact(agri)}. "
               f"Lithium has lifted mining sharply since 2022.",
        "bars": bars,
        "bar_unit": "USD, latest quarter",
        "bg": BG,
        "footer_src": "Source: ZimStat, Quarterly GDP Tables.",
    }


def chapter_fri_remittances(gdp, bop):
    """Diaspora remittances — trailing 4 quarters."""
    pt = bop["series"]["personal_transfers"]
    n = len(bop["quarters"])
    last = n - 1
    quarter = bop["quarters"][last]
    latest = pt[last]
    start = max(0, n - 4)
    bars = [
        (bop["quarters"][i], (pt[i] or 0) * 1e6, i == last)
        for i in range(start, n)
    ]
    sum4 = sum((pt[i] or 0) for i in range(start, n))
    return {
        "eyebrow": "DIASPORA DIVIDEND",
        "headline": "Money home.",
        "big_num": fmt_bop(latest),
        "big_lbl": f"in {quarter}",
        "sub": f"Personal transfers — money sent home by Zimbabweans living "
               f"abroad. Over the trailing four quarters: {fmt_bop(sum4)}. "
               f"Likely an undercount; informal channels are not counted.",
        "bars": bars,
        "bar_unit": "USD, last four quarters",
        "bg": BG_ALT,
        "footer_src": "Source: RBZ, Balance of Payments — Personal Transfers.",
    }


def chapter_sat_services(gdp, bop):
    """Services trade — exports vs imports of services."""
    n = len(bop["quarters"])
    last = n - 1
    quarter = bop["quarters"][last]
    exp = bop["series"]["exports_services"][last]
    imp = bop["series"]["imports_services"][last]
    bal = (exp or 0) - (imp or 0)
    bars = [
        ("Services exports", (exp or 0) * 1e6, bal > 0),
        ("Services imports", (imp or 0) * 1e6, bal < 0),
    ]
    return {
        "eyebrow": "SERVICES TRADE",
        "headline": "What Zimbabwe sells to the world.",
        "big_num": fmt_bop(abs(bal)),
        "big_lbl": "services deficit" if bal < 0 else "services surplus",
        "sub": f"Zimbabwe sold {fmt_bop(exp)} of services in {quarter} — "
               f"tourism, transport, financial services — and bought "
               f"{fmt_bop(imp)}. The gap is structurally negative.",
        "bars": bars,
        "bar_unit": "USD, latest quarter",
        "bg": BG,
        "footer_src": "Source: RBZ / ZimStat, Balance of Payments.",
    }


def _latest_with_data(series, quarters):
    """Return (idx, value, quarter_name) for the latest non-null,
    non-zero entry. Falls back to the very last index if everything
    is null/zero, so callers can still render something."""
    for i in range(len(series) - 1, -1, -1):
        if series[i] not in (None, 0, 0.0):
            return i, series[i], quarters[i]
    return len(series) - 1, series[-1], quarters[-1]


def chapter_sun_missing(gdp, bop):
    """Net errors & omissions — the informal economy proxy. Uses the
    latest quarter with a real (non-zero, non-null) reading — ZimStat
    publishes a 0 placeholder for the most recent quarter until it is
    finalised."""
    idx, ne, quarter = _latest_with_data(
        bop["series"]["net_errors_omissions"], bop["quarters"])
    ca = bop["series"]["current_account"][idx]
    bars = [
        ("Current account", (ca or 0) * 1e6, False),
        ("Net errors & omissions", (ne or 0) * 1e6, True),
    ]
    return {
        "eyebrow": "THE MISSING MONEY",
        "headline": "What the books cannot see.",
        "big_num": fmt_bop(ne),
        "big_lbl": "unrecorded balance",
        "sub": f"In {quarter}, Zimbabwe's official current account read "
               f"{fmt_bop(ca)}. The Balance-of-Payments residual — money "
               f"that should add up but does not — read {fmt_bop(ne)}.",
        "bars": bars,
        "bar_unit": "USD, latest reported quarter",
        "bg": BG_ALT,
        "footer_src": "Source: RBZ, Balance of Payments — Net Errors & Omissions.",
    }


CHAPTERS = [
    chapter_mon_gdp,         # 0 = Monday
    chapter_tue_trade,       # 1 = Tuesday
    chapter_wed_growth,      # 2 = Wednesday
    chapter_thu_mining,      # 3 = Thursday
    chapter_fri_remittances, # 4 = Friday
    chapter_sat_services,    # 5 = Saturday
    chapter_sun_missing,     # 6 = Sunday
]


# ── Mini-chart rendering ──────────────────────────────────────
def draw_mini_chart(draw, bars, x0, y0, w, h, unit_label):
    """Horizontal bar chart, plain and editorial. `bars` is a list of
    (label, value, is_highlight) where is_highlight gets accent color."""
    if not bars:
        return
    abs_vals = [abs(v) for _, v, _ in bars]
    max_v = max(abs_vals) or 1
    label_w = 240
    bar_x0 = x0 + label_w
    bar_max_w = w - label_w - 90  # leave room for value labels

    row_h = h // max(1, len(bars))
    bar_h = max(18, min(38, row_h - 16))

    label_font = load_font("sans_bold", 22)
    value_font = load_font("sans_bold", 24)
    axis_font = load_font("sans", 18)

    for i, (label, value, highlight) in enumerate(bars):
        cy = y0 + i * row_h + (row_h - bar_h) // 2
        # Label (truncate if too wide)
        lbl = label
        while draw.textlength(lbl, font=label_font) > label_w - 16 and len(lbl) > 6:
            lbl = lbl[:-2]
        if lbl != label:
            lbl = lbl.rstrip() + "…"
        draw.text((x0, cy + (bar_h - 22) // 2), lbl,
                  font=label_font, fill=CARD_FG)

        # Bar
        bar_w = int((abs(value) / max_v) * bar_max_w)
        color = ACCENT if highlight else (CHART_BAR_SECONDARY if value < 0
                                          else CHART_BAR_MUTED)
        if value < 0:
            color = CHART_BAR_SECONDARY
        if highlight:
            color = ACCENT
        # Draw bar (zero-baseline at bar_x0)
        if value >= 0:
            draw.rectangle([(bar_x0, cy), (bar_x0 + bar_w, cy + bar_h)],
                           fill=color)
        else:
            draw.rectangle([(bar_x0, cy), (bar_x0 + bar_w, cy + bar_h)],
                           fill=color)

        # Value label, right of the bar
        if isinstance(value, float) and abs(value) < 100 and unit_label.startswith("YoY"):
            val_str = fmt_pct(value)
        else:
            val_str = fmt_money_compact(value)
        draw.text((bar_x0 + bar_w + 12, cy + (bar_h - 24) // 2),
                  val_str, font=value_font, fill=CARD_FG)

    # Tiny axis label below the chart
    draw.text((x0, y0 + h + 6), unit_label, font=axis_font, fill=CARD_FG_MUTED)


# ── Card rendering ────────────────────────────────────────────
def render_card(chapter, out_path, date_label, day_name):
    bg = chapter.get("bg", BG)
    img = Image.new("RGB", (CARD_W, CARD_H), bg)
    draw = ImageDraw.Draw(img)

    masthead_font = load_font("serif_bold", 38)
    date_font = load_font("sans_bold", 22)
    eyebrow_font = load_font("sans_bold", 22)
    head_font = load_font("serif_bold", 58)
    big_font = load_font("serif_bold", 152)
    big_lbl_font = load_font("serif_italic", 36)
    sub_font = load_font("sans", 26)
    footer_font = load_font("sans_bold", 22)
    footer_src_font = load_font("sans", 20)

    # ── Masthead chrome ──
    draw.rectangle([(0, 0), (140, 10)], fill=ACCENT)
    draw.text((60, 60), "THE MUTAPA TIMES",
              font=masthead_font, fill=CARD_FG)
    draw.text((60, 114), f"ZIM ECONOMY · {date_label}",
              font=date_font, fill=ACCENT)

    # ── Eyebrow + analytical headline ──
    draw.text((60, 188), f"{day_name.upper()} · {chapter['eyebrow']}",
              font=eyebrow_font, fill=CARD_FG_MUTED)
    head_lines = wrap_text(draw, chapter["headline"], head_font, CARD_W - 120)[:2]
    hy = 232
    for ln in head_lines:
        draw.text((60, hy), ln, font=head_font, fill=CARD_FG)
        hy += 70

    # ── The big number ──
    big_y = hy + 20
    draw.text((60, big_y), chapter["big_num"],
              font=big_font, fill=CARD_FG)
    # Big label sits right under the number
    draw.text((60, big_y + 170), chapter["big_lbl"],
              font=big_lbl_font, fill=ACCENT)

    # ── Sub caption ──
    sub_y = big_y + 230
    sub_lines = wrap_text(draw, chapter["sub"], sub_font, CARD_W - 120)[:3]
    for ln in sub_lines:
        draw.text((60, sub_y), ln, font=sub_font, fill=CARD_FG)
        sub_y += 36

    # ── Divider ──
    div_y = sub_y + 18
    draw.line([(60, div_y), (CARD_W - 60, div_y)],
              fill=CARD_FG_MUTED, width=1)

    # ── Mini-chart ──
    chart_x0 = 60
    chart_y0 = div_y + 24
    chart_w = CARD_W - 120
    chart_h = min(260, CARD_H - chart_y0 - 180)
    draw_mini_chart(draw, chapter["bars"], chart_x0, chart_y0,
                    chart_w, chart_h, chapter["bar_unit"])

    # ── Footer ──
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


# ── Main ──────────────────────────────────────────────────────
def load_json(path, label):
    if not os.path.exists(path):
        print(f"  ERROR: {label} file missing: {path}")
        sys.exit(1)
    with open(path) as f:
        return json.load(f)


DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday",
             "Friday", "Saturday", "Sunday"]


def pick_chapter_for_today(override_day=None):
    """Pick the chapter based on the current CAT (UTC+2) weekday, or an
    override (0-6) when testing locally.
    Returns (weekday_int, day_name, chapter_dict_builder)."""
    if override_day is not None:
        wd = override_day % 7
        return wd, DAY_NAMES[wd], CHAPTERS[wd]
    cat = datetime.now(timezone(timedelta(hours=2)))
    wd = cat.weekday()  # 0 = Mon
    return wd, cat.strftime("%A"), CHAPTERS[wd]


def main():
    print("=== BUILD ECONOMY CARD ===")
    gdp = load_json(GDP_FILE, "GDP")
    bop = load_json(BOP_FILE, "BoP")

    # --day N runs a specific chapter (for local testing); default = today.
    override = None
    if "--day" in sys.argv:
        try:
            override = int(sys.argv[sys.argv.index("--day") + 1])
        except (ValueError, IndexError):
            print("  ERROR: --day requires an integer 0-6 (Mon=0)")
            sys.exit(1)

    wd, day_name, builder = pick_chapter_for_today(override)
    chapter = builder(gdp, bop)
    print(f"  Day: {day_name} (weekday={wd}) → {chapter['eyebrow']}")

    cat = datetime.now(timezone(timedelta(hours=2)))
    date_label = cat.strftime("%a %d %b %Y").upper()
    # When testing a non-today day, write a per-day file so we can eyeball
    # all variants side-by-side without overwriting each other.
    out = OUT_FILE
    if override is not None:
        out = os.path.join(OUT_DIR, f"economy-snapshot-day{wd}.png")
    render_card(chapter, out, date_label, day_name)
    print(f"  Wrote {out}")
    print(f"  Headline: {chapter['headline']}")
    print(f"  Big:      {chapter['big_num']} — {chapter['big_lbl']}")
    print("\n=== DONE ===")


if __name__ == "__main__":
    main()
