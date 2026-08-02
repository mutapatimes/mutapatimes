#!/usr/bin/env python3
"""Render the ZSE end-of-day social card (1080x1350) from
data/zse-market-activity.json.

Butter-cream brand style shared with the feed/story/campaign cards
(card_lib). Output: img/cards/zse/eod-latest.png plus a dated copy
img/cards/zse/eod-<YYYY-MM-DD>.png. Auto-posters attach eod-latest.png.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from card_lib import BUTTER, ACCENT, CARD_FG, CARD_FG_MUTED, load_font, wrap_text  # noqa: E402

try:
    from PIL import Image, ImageDraw
except ImportError:
    raise SystemExit("ERROR: Pillow not installed. Run: pip install Pillow")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "zse-market-activity.json")
OUT_DIR = os.path.join(ROOT, "img", "cards", "zse")
W, H = 1080, 1350
GREEN = (26, 127, 55)
PAD = 64

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def nice_date(iso):
    p = (iso or "").split("-")
    if len(p) != 3:
        return iso or ""
    return f"{int(p[2])} {MONTHS[int(p[1]) - 1]} {p[0]}"


def commas(n, dp=0):
    if n is None:
        return "--"
    return f"{float(n):,.{dp}f}"


def big(n):
    if n is None:
        return "--"
    n = float(n)
    if n >= 1e9:
        return f"{n / 1e9:.2f}bn"
    if n >= 1e6:
        return f"{n / 1e6:.2f}m"
    return commas(n)


def pct(p):
    if p is None:
        return ""
    v = float(p)
    return f"{'+' if v > 0 else ''}{v:.2f}%"


def colour(v):
    try:
        v = float(v)
    except (TypeError, ValueError):
        return CARD_FG_MUTED
    return GREEN if v > 0 else (ACCENT if v < 0 else CARD_FG_MUTED)


def arrow(v):
    try:
        v = float(v)
    except (TypeError, ValueError):
        return ""
    return "▲" if v > 0 else ("▼" if v < 0 else "■")


def all_share(d):
    for x in d.get("indices", []):
        if (x.get("name") or "").upper() == "ALL SHARE":
            return x
    return None


def render(d):
    img = Image.new("RGB", (W, H), BUTTER)
    dr = ImageDraw.Draw(img)
    maxw = W - PAD * 2

    # Brand chrome
    dr.rectangle([(0, 0), (140, 10)], fill=ACCENT)
    dr.text((PAD, 60), "THE MUTAPA TIMES", font=load_font("serif_bold", 40), fill=CARD_FG)
    dr.text((PAD, 110), "Southern Africa outside-in", font=load_font("sans", 25), fill=CARD_FG_MUTED)

    dr.text((PAD, 176), "ZSE · END OF DAY", font=load_font("sans_bold", 24), fill=ACCENT)
    dr.text((PAD, 214), "ZSE at the close", font=load_font("serif_bold", 72), fill=CARD_FG)
    dr.text((PAD, 300), nice_date(d.get("as_of")) + "   ·   ZWG",
            font=load_font("sans", 28), fill=CARD_FG_MUTED)

    a = d.get("activity", {})
    as_ = all_share(d)

    # All Share headline
    y = 372
    dr.text((PAD, y), "ALL SHARE", font=load_font("sans_bold", 24), fill=CARD_FG_MUTED)
    if as_:
        dr.text((PAD, y + 34), commas(as_.get("value"), 2), font=load_font("serif_bold", 82), fill=CARD_FG)
        chg = f"{arrow(as_.get('change_pct'))} {pct(as_.get('change_pct'))}"
        dr.text((PAD + 6, y + 140), chg, font=load_font("sans_bold", 40), fill=colour(as_.get("change_pct")))

    # KPI row: Trades / Turnover / Market cap
    ky = 560
    cols = [("TRADES", commas(a.get("trades"))),
            ("TURNOVER", commas(a.get("turnover"))),
            ("MKT CAP", big(a.get("market_cap")))]
    cw = maxw // 3
    for i, (lbl, val) in enumerate(cols):
        x = PAD + i * cw
        dr.text((x, ky), lbl, font=load_font("sans_bold", 22), fill=CARD_FG_MUTED)
        dr.text((x, ky + 30), val, font=load_font("serif_bold", 44), fill=CARD_FG)

    # Divider
    dr.line([(PAD, 690), (W - PAD, 690)], fill=(0, 0, 0), width=1)

    # Gainers / Losers
    def movers(x0, title, rows):
        dr.text((x0, 712), title, font=load_font("sans_bold", 24), fill=ACCENT)
        yy = 754
        for m in rows[:4]:
            sym = m.get("symbol") or m.get("name") or ""
            dr.text((x0, yy), sym[:14], font=load_font("sans_bold", 28), fill=CARD_FG)
            ch = pct(m.get("change_pct"))
            f = load_font("sans_bold", 28)
            w = dr.textbbox((0, 0), ch, font=f)[2]
            dr.text((x0 + cw + 90 - w, yy), ch, font=f, fill=colour(m.get("change_pct")))
            yy += 46

    movers(PAD, "TOP GAINERS", d.get("gainers", []))
    movers(PAD + maxw // 2 + 30, "TOP LOSERS", d.get("losers", []))

    # Indices strip (compact, up to 5)
    iy = 966
    dr.line([(PAD, iy - 16), (W - PAD, iy - 16)], fill=(0, 0, 0), width=1)
    dr.text((PAD, iy), "INDICES", font=load_font("sans_bold", 24), fill=ACCENT)
    iy += 40
    want = ["ZSE TOP 10", "ZSE TOP 15", "MID CAP INDEX", "SMALL CAP INDEX"]
    idx = {x.get("name"): x for x in d.get("indices", [])}
    for nm in want:
        x = idx.get(nm)
        if not x:
            continue
        dr.text((PAD, iy), nm.title(), font=load_font("sans", 28), fill=CARD_FG)
        val = commas(x.get("value"), 2)
        dr.text((PAD + 460, iy), val, font=load_font("sans", 28), fill=CARD_FG)
        ch = f"{arrow(x.get('change_pct'))} {pct(x.get('change_pct'))}"
        dr.text((PAD + 660, iy), ch, font=load_font("sans_bold", 28), fill=colour(x.get("change_pct")))
        iy += 46

    # Footer
    fy = H - 108
    dr.rectangle([(0, fy - 26), (W, fy - 24)], fill=(0, 0, 0))
    dr.text((PAD, fy), "Full close, indices & notices", font=load_font("sans", 26), fill=CARD_FG_MUTED)
    dr.text((PAD, fy + 34), "mutapatimes.com/zse", font=load_font("sans_bold", 30), fill=ACCENT)
    note = "End of day · not investment advice"
    f = load_font("sans", 22)
    w = dr.textbbox((0, 0), note, font=f)[2]
    dr.text((W - PAD - w, fy + 40), note, font=f, fill=CARD_FG_MUTED)

    return img


def main():
    with open(DATA, encoding="utf-8") as f:
        d = json.load(f)
    os.makedirs(OUT_DIR, exist_ok=True)
    img = render(d)
    latest = os.path.join(OUT_DIR, "eod-latest.png")
    img.save(latest, "PNG", optimize=True)
    dated = os.path.join(OUT_DIR, f"eod-{d.get('as_of', 'latest')}.png")
    img.save(dated, "PNG", optimize=True)
    print(f"Wrote {os.path.relpath(latest, ROOT)} and {os.path.relpath(dated, ROOT)}")


if __name__ == "__main__":
    main()
