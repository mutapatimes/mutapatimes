#!/usr/bin/env python3
"""Build 9:16 Instagram-Story cards (1080×1920) for the mixed
stories-feed.xml. One card per business article + property listing +
job — same brand chrome, big headline, red "Read more on Mutapa Times"
pill at the bottom.

Output: img/cards/stories/{md5}.png — hash derived from the canonical
mutapatimes.com URL the story links to.
"""
import glob
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone

try:
    from PIL import Image, ImageDraw
except ImportError:
    raise SystemExit("ERROR: Pillow not installed. Run: pip install Pillow")

# Reuse the shared brand primitives (BUTTER, ACCENT, fonts, wrap_text)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from card_lib import (  # noqa: E402
    BUTTER, ACCENT, CARD_FG, CARD_FG_MUTED, load_font, wrap_text,
)

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT_DIR = os.path.join(ROOT, "img", "cards", "stories")
os.makedirs(OUT_DIR, exist_ok=True)

# Instagram Story dimensions
W = 1080
H = 1920

# ── URL → card filename ───────────────────────────────────
def card_hash(url):
    return hashlib.md5((url or "").encode("utf-8")).hexdigest()[:12]


def card_filename(url):
    return f"{card_hash(url)}.png"


def card_public_url(url):
    return f"/img/cards/stories/{card_filename(url)}"


# ── Layout helper: find the largest font size that fits ──
def fit_headline(draw, text, max_width, max_lines,
                 max_size=92, min_size=46, step=4):
    """Step font size down until the wrapped headline fits in `max_lines`."""
    for size in range(max_size, min_size - 1, -step):
        font = load_font("serif_bold", size)
        lines = wrap_text(text, font, max_width, draw)
        if len(lines) <= max_lines:
            return size, font, lines
    # Last-resort: smallest size + clip
    font = load_font("serif_bold", min_size)
    lines = wrap_text(text, font, max_width, draw)[:max_lines]
    return min_size, font, lines


def _text_w(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0]


def _text_h(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[3] - bbox[1]


def render_story_card(eyebrow, headline, subline, output_path):
    """Render a 1080×1920 butter story card with brand chrome, big
    headline, optional subline, and a red 'Read more on Mutapa Times'
    pill anchored at the bottom."""
    img = Image.new("RGB", (W, H), BUTTER)
    draw = ImageDraw.Draw(img)
    pad = 96

    # ── TOP: brand wordmark + red rule + subtitle ──
    wordmark_font = load_font("serif_bold", 52)
    draw.text((pad, 110), "THE MUTAPA TIMES", font=wordmark_font, fill=CARD_FG)
    rule_y = 110 + _text_h(draw, "THE MUTAPA TIMES", wordmark_font) + 22
    draw.rectangle([pad, rule_y, pad + 110, rule_y + 5], fill=ACCENT)
    sub_font = load_font("sans_bold", 20)
    draw.text((pad, rule_y + 22), "ZIMBABWE OUTSIDE-IN",
              font=sub_font, fill=CARD_FG_MUTED)

    # ── MIDDLE: eyebrow + auto-sized headline ──
    eyebrow_y = 480
    eyebrow_font = load_font("sans_bold", 26)
    draw.text((pad, eyebrow_y), (eyebrow or "BRIEFING").upper(),
              font=eyebrow_font, fill=ACCENT)

    headline_y = eyebrow_y + 60
    max_width = W - 2 * pad
    # 9 lines is the practical max before the headline crowds the CTA
    headline_size, headline_font, headline_lines = fit_headline(
        draw, headline or "", max_width, max_lines=9,
        max_size=92, min_size=46,
    )
    line_height = int(headline_size * 1.18)
    y = headline_y
    for line in headline_lines:
        draw.text((pad, y), line, font=headline_font, fill=CARD_FG)
        y += line_height

    # Subline below headline (optional — price, location, source name)
    if subline:
        subline_font = load_font("sans", 28)
        # Wrap subline to two lines max
        sub_lines = wrap_text(subline, subline_font, max_width, draw)[:2]
        sub_y = y + 36
        for line in sub_lines:
            draw.text((pad, sub_y), line, font=subline_font, fill=CARD_FG_MUTED)
            sub_y += int(28 * 1.4)

    # ── BOTTOM: CTA pill anchored to the bottom ──
    cta_text = "Read more on Mutapa Times  →"
    cta_font = load_font("sans_bold", 36)
    cta_w = _text_w(draw, cta_text, cta_font)
    cta_h = _text_h(draw, cta_text, cta_font)
    pill_padding_x = 56
    pill_padding_y = 28
    pill_w = cta_w + pill_padding_x * 2
    pill_h = cta_h + pill_padding_y * 2
    pill_x = (W - pill_w) // 2
    pill_y = H - pad - pill_h - 80  # leave room for the small URL line
    radius = pill_h // 2
    draw.rounded_rectangle(
        [pill_x, pill_y, pill_x + pill_w, pill_y + pill_h],
        radius=radius, fill=ACCENT,
    )
    # Centre the CTA text inside the pill (textbbox is anchored at baseline-ish,
    # so subtract the bbox top to land on the visual centre).
    bbox = draw.textbbox((0, 0), cta_text, font=cta_font)
    text_y = pill_y + (pill_h - (bbox[3] - bbox[1])) // 2 - bbox[1]
    text_x = pill_x + pill_padding_x
    draw.text((text_x, text_y), cta_text, font=cta_font, fill=(255, 255, 255))

    # URL hint below pill
    url_font = load_font("sans", 24)
    url_text = "mutapatimes.com"
    url_w = _text_w(draw, url_text, url_font)
    draw.text(((W - url_w) // 2, pill_y + pill_h + 26),
              url_text, font=url_font, fill=CARD_FG_MUTED)

    img.save(output_path, "PNG", optimize=True)


# ── Sources: business articles, property, jobs ──────────────
def collect_business_cards():
    """One story per fresh CMS article. Returns list of dicts:
    {url, eyebrow, headline, subline, slug}."""
    out = []
    idx_path = os.path.join(ROOT, "content", "articles", "index.json")
    if not os.path.exists(idx_path):
        return out
    try:
        entries = json.load(open(idx_path))
    except (json.JSONDecodeError, OSError):
        return out
    # Filter to recent business-like categories (banned ones already stripped)
    keep_cats = {"Business", "Policy", "Tech", "Economy", "Environment"}
    for e in entries:
        if not isinstance(e, dict):
            continue
        slug = e.get("slug")
        cat = (e.get("category") or "").strip()
        title = (e.get("title") or "").strip()
        author = (e.get("author") or "").strip()
        if not slug or not title or cat not in keep_cats:
            continue
        url = f"https://mutapatimes.com/articles/{slug}"
        out.append({
            "url": url,
            "eyebrow": cat or "BUSINESS",
            "headline": title,
            "subline": f"via {author}" if author else "",
            "slug": slug,
            "date": e.get("date", ""),
        })
    return out


def _fmt_usd(amount):
    try:
        n = float(amount)
    except (TypeError, ValueError):
        return ""
    if n >= 1_000_000:
        return f"USD {n / 1_000_000:.2f}M"
    if n >= 1_000:
        return f"USD {n / 1_000:.0f}K"
    return f"USD {n:.0f}"


def collect_property_cards():
    """One story per property listing."""
    out = []
    p = os.path.join(ROOT, "data", "property-listings.json")
    if not os.path.exists(p):
        return out
    try:
        data = json.load(open(p))
    except (json.JSONDecodeError, OSError):
        return out
    listings = data.get("listings") or data.get("items") or []
    for li in listings:
        if not isinstance(li, dict):
            continue
        url = (li.get("url") or "").strip()
        title = (li.get("title") or "").strip()
        if not url or not title:
            continue
        price = li.get("price") or li.get("price_usd") or ""
        location = li.get("location") or li.get("suburb") or ""
        beds = li.get("bedrooms") or li.get("beds")
        bits = []
        if price:
            bits.append(_fmt_usd(price) if isinstance(price, (int, float)) else str(price))
        if beds:
            bits.append(f"{beds} bed")
        if location:
            bits.append(str(location))
        subline = " · ".join(bits) if bits else "Zimbabwe property listing"
        out.append({
            "url": url,
            "eyebrow": "PROPERTY",
            "headline": title,
            "subline": subline,
            "slug": None,
            "date": li.get("date") or li.get("publishedAt") or "",
        })
    return out


def collect_job_cards():
    """One story per active job + the three Mutapa internships."""
    out = []
    # Internships first — stable, always present
    internships = [
        ("social-intern", "Social Intern — The Mutapa Times",
         "Fully remote · 3 days/week · 3 months · Rolling intake"),
        ("editor-intern", "Editor Intern — The Mutapa Times",
         "Fully remote · 3 days/week · 3 months · Rolling intake"),
        ("data-intern",  "Data Intern — The Mutapa Times",
         "Fully remote · 3 days/week · 3 months · Rolling intake"),
    ]
    for slug, headline, subline in internships:
        out.append({
            "url": f"https://mutapatimes.com/jobs#{slug}",
            "eyebrow": "INTERNSHIP",
            "headline": headline,
            "subline": subline,
            "slug": slug,
            "date": "2026-05-01T00:00:00Z",   # pinned recent
        })
    # External jobs
    p = os.path.join(ROOT, "data", "jobs.json")
    if not os.path.exists(p):
        return out
    try:
        data = json.load(open(p))
    except (json.JSONDecodeError, OSError):
        return out
    for j in (data.get("jobs") or []):
        url = (j.get("url") or "").strip()
        title = (j.get("title") or "").strip()
        if not url or not title:
            continue
        company = (j.get("company") or "").strip()
        loc = (j.get("location") or "").strip()
        jtype = (j.get("type") or "").strip()
        bits = [b for b in [company, loc, jtype] if b]
        out.append({
            "url": url,
            "eyebrow": "JOB",
            "headline": title,
            "subline": " · ".join(bits) if bits else "",
            "slug": None,
            "date": j.get("posted_at") or j.get("date") or "",
        })
    return out


# ── Pruning: drop cards whose URLs no longer appear in any source ──
def prune_stale(active_hashes):
    pruned = 0
    for path in glob.glob(os.path.join(OUT_DIR, "*.png")):
        name = os.path.splitext(os.path.basename(path))[0]
        if name not in active_hashes:
            try:
                os.remove(path)
                pruned += 1
            except OSError:
                pass
    return pruned


def main():
    print("=== BUILD STORY CARDS (1080x1920) ===")
    items = []
    items += collect_business_cards()
    items += collect_property_cards()
    items += collect_job_cards()
    print(f"  Collected {len(items)} items "
          f"(business + property + jobs + internships)")

    rendered = cached = failed = 0
    active = set()
    for it in items:
        h = card_hash(it["url"])
        active.add(h)
        out_path = os.path.join(OUT_DIR, f"{h}.png")
        if os.path.exists(out_path):
            cached += 1
            continue
        try:
            render_story_card(
                eyebrow=it["eyebrow"],
                headline=it["headline"],
                subline=it["subline"],
                output_path=out_path,
            )
            rendered += 1
        except Exception as e:
            failed += 1
            print(f"    FAIL {it['headline'][:48]}: {e}")

    pruned = prune_stale(active)
    print(f"  Rendered {rendered} new · Cached {cached} · Pruned {pruned} · Failed {failed}")
    print(f"  Output:  {OUT_DIR}")
    print("=== DONE ===")


if __name__ == "__main__":
    main()
