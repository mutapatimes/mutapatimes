#!/usr/bin/env python3
"""Render a daily portrait 1080x1350 FX snapshot card.

Output: img/cards/fx-snapshot.png (single canonical file, overwritten
daily). Content: today's USD/ZWG rate + which provider gives the best
recipient amount for £100 from UK, $100 from US, R1000 from SA.

This is the image that the autolist RSS item references each day, so
every social platform connected to the autolist gets a fresh FX post
without any manual work.
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
FX_FILE = os.path.join(ROOT, "data", "fx-rates.json")
PROVIDERS_FILE = os.path.join(ROOT, "data", "remittance-providers.json")
OUT_DIR = os.path.join(ROOT, "img", "cards")
OUT_FILE = os.path.join(OUT_DIR, "fx-snapshot.png")

# ── Card dimensions + palette (matches build_metricool_csv.py) ──
CARD_W = 1080
CARD_H = 1350
CARD_FG = (26, 26, 26)
CARD_FG_MUTED = (95, 92, 84)
ACCENT = (192, 57, 43)
# Faded green for money/economy theme
BG = (216, 230, 213)


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


def fmt_money(amount, decimals=2):
    return f"{amount:,.{decimals}f}"


# ── Best-provider math (mirrors js/fx.js) ──
# recipient_usd = (send - fee) × (1/mid) × (1 - margin/100)
def best_provider(rates, providers, send_currency, send_amount):
    """Return dict with name, recipient_usd, all_count for the best provider."""
    if send_currency not in rates:
        return None
    mid_usd_per_send = 1 / rates[send_currency]
    corridor = providers.get("corridors", {}).get(send_currency)
    if not corridor:
        return None
    best = None
    for p in corridor.get("providers", []):
        net = max(0, send_amount - p.get("fee", 0))
        prate = mid_usd_per_send * (1 - p.get("fx_margin_pct", 0) / 100)
        recv = net * prate
        if best is None or recv > best["recipient_usd"]:
            best = {
                "name": p["name"],
                "recipient_usd": recv,
                "fee": p.get("fee", 0),
                "margin": p.get("fx_margin_pct", 0),
            }
    if best:
        best["count"] = len(corridor.get("providers", []))
    return best


# ── Card rendering ────────────────────────────────────────────
def render_card(rates, providers, out_path):
    img = Image.new("RGB", (CARD_W, CARD_H), BG)
    draw = ImageDraw.Draw(img)

    masthead_font = load_font("serif_bold", 38)
    eyebrow_font = load_font("sans_bold", 22)
    big_currency_font = load_font("serif_bold", 64)
    big_rate_font = load_font("serif_bold", 150)
    sub_font = load_font("sans", 28)
    corridor_lbl_font = load_font("sans_bold", 30)
    corridor_amt_font = load_font("serif_bold", 48)
    corridor_via_font = load_font("sans", 24)
    cta_font = load_font("sans_bold", 28)
    small_font = load_font("sans", 22)

    # Top accent bar + masthead
    draw.rectangle([(0, 0), (140, 10)], fill=ACCENT)
    draw.text((60, 60), "THE MUTAPA TIMES", font=masthead_font, fill=CARD_FG)
    today_str = datetime.now(timezone(timedelta(hours=2))).strftime("%a %d %B %Y").upper()
    draw.text((60, 114), f"ZIM FX SNAPSHOT · {today_str}",
              font=eyebrow_font, fill=ACCENT)

    # ── HERO RATE ──
    zwg = rates.get("ZWG")
    if zwg is None:
        draw.text((60, 240), "ZWG rate unavailable", font=big_rate_font, fill=CARD_FG)
    else:
        # "1 USD =" prefix line
        draw.text((60, 200), "1 USD =", font=big_currency_font, fill=CARD_FG_MUTED)
        # Big rate
        rate_str = f"{zwg:,.4f}"
        draw.text((60, 270), rate_str, font=big_rate_font, fill=CARD_FG)
        # Suffix "ZWG"
        draw.text((60, 440), "ZWG · Zim Gold (Reserve Bank official rate)",
                  font=sub_font, fill=CARD_FG_MUTED)

    # Divider
    draw.line([(60, 510), (CARD_W - 60, 510)], fill=CARD_FG_MUTED, width=1)

    # ── BEST PROVIDER BY CORRIDOR ──
    draw.text((60, 540), "BEST RATE TO SEND",
              font=eyebrow_font, fill=ACCENT)

    corridors_to_show = [
        ("GBP", 100, "🇬🇧", "£100 from UK"),
        ("USD", 100, "🇺🇸", "$100 from US"),
        ("ZAR", 1000, "🇿🇦", "R1,000 from SA"),
    ]

    y = 600
    row_h = 200
    for code, amount, flag, label in corridors_to_show:
        best = best_provider(rates, providers, code, amount)
        # Label column
        draw.text((60, y), label, font=corridor_lbl_font, fill=CARD_FG)
        if best is None:
            draw.text((60, y + 50), "(no providers configured)",
                      font=corridor_via_font, fill=CARD_FG_MUTED)
        else:
            recv_str = f"→ ${fmt_money(best['recipient_usd'], 2)}"
            via_str = f"via {best['name']}  ·  beats {best['count'] - 1} other"
            via_str += "s" if best['count'] > 2 else ""
            draw.text((60, y + 50), recv_str, font=corridor_amt_font, fill=ACCENT)
            draw.text((60, y + 120), via_str, font=corridor_via_font, fill=CARD_FG_MUTED)
        y += row_h

    # ── CTA footer ──
    cta_y = CARD_H - 140
    draw.line([(60, cta_y - 24), (CARD_W - 60, cta_y - 24)],
              fill=CARD_FG_MUTED, width=1)
    draw.text((60, cta_y), "Compare all providers →",
              font=cta_font, fill=CARD_FG)
    draw.text((60, cta_y + 40), "mutapatimes.com/fx",
              font=cta_font, fill=ACCENT)
    draw.text((60, cta_y + 84),
              "Rates indicative — verify on provider site before sending.",
              font=small_font, fill=CARD_FG_MUTED)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    img.save(out_path, "PNG", optimize=True)


def main():
    print("=== BUILD FX SNAPSHOT CARD ===")
    if not os.path.exists(FX_FILE):
        print(f"  ERROR: {FX_FILE} not found. Run fetch_fx.py first.")
        sys.exit(1)
    if not os.path.exists(PROVIDERS_FILE):
        print(f"  ERROR: {PROVIDERS_FILE} not found.")
        sys.exit(1)

    with open(FX_FILE) as f:
        fx_data = json.load(f)
    with open(PROVIDERS_FILE) as f:
        providers = json.load(f)

    rates = fx_data.get("rates") or {}
    if not rates:
        print("  ERROR: empty rates payload")
        sys.exit(1)

    render_card(rates, providers, OUT_FILE)
    print(f"  Wrote {OUT_FILE}")
    # Print headline values to the workflow log
    print(f"  ZWG: {rates.get('ZWG'):.4f}")
    for code, amount in [("GBP", 100), ("USD", 100), ("ZAR", 1000)]:
        b = best_provider(rates, providers, code, amount)
        if b:
            print(f"  Best from {code} {amount}: {b['name']} → ${b['recipient_usd']:.2f}")
    print("\n=== DONE ===")


if __name__ == "__main__":
    main()
