#!/usr/bin/env python3
"""Render hybrid property cards — listing photo on top, branded info
strip on the bottom — for the Mutapa Times properties autolist feed.

Each card is 1080x1350 portrait, sized for IG feed + Twitter + IG
stories (close enough for Metricool to push to all three). The source
photo fills the top ~58% of the canvas; the bottom strip is a
faded-paper brand panel with price (big serif), beds/baths, location,
and the listing title.

Output:
    img/cards/properties/{12-char-md5-of-url}.png

Cards are keyed by URL hash so re-runs are cheap. Listings whose
source image is unreachable get a fallback colour block in place of
the photo so the autolist never goes empty.
"""
import glob
import hashlib
import io
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from card_lib import (   # noqa: E402
    CARD_W, CARD_H, CARD_FG, CARD_FG_MUTED, ACCENT, CARD_BACKGROUNDS,
    load_font, wrap_text,
)

try:
    from PIL import Image, ImageDraw, ImageOps
except ImportError:
    print("ERROR: Pillow not installed. Run: pip install Pillow")
    sys.exit(1)


ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
PROPERTIES_FILE = os.path.join(ROOT, "data", "property-listings.json")
OUT_DIR = os.path.join(ROOT, "img", "cards", "properties")
PUBLIC_BASE = "https://www.mutapatimes.com/img/cards/properties"

# Layout: top 58% is photo, bottom 42% is brand info strip
PHOTO_H = 780
STRIP_H = CARD_H - PHOTO_H


def card_hash(url):
    return hashlib.md5((url or "").encode("utf-8")).hexdigest()[:12]


def card_filename(url):
    return f"{card_hash(url)}.png"


def card_public_url(url):
    return f"{PUBLIC_BASE}/{card_filename(url)}"


def _bg_for(url):
    h = card_hash(url)
    return int(h, 16) % len(CARD_BACKGROUNDS)


def _fetch_image(url, timeout=8):
    """Download a remote image and return it as a PIL Image, or None
    if anything goes wrong. We do NOT raise — the autolist must keep
    flowing even when the source image is dead."""
    if not url or not url.startswith(("http://", "https://")):
        return None
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "MutapaTimes-PropertyCard/1.0",
        })
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = r.read()
        return Image.open(io.BytesIO(data)).convert("RGB")
    except Exception as e:  # broad on purpose — every failure is non-fatal
        print(f"    photo fetch failed ({type(e).__name__}): {url[:80]}")
        return None


def _photo_panel(src_img, width, height):
    """Crop-fill source photo to exactly width × height (center-crop)."""
    if src_img is None:
        return None
    return ImageOps.fit(src_img, (width, height), Image.LANCZOS)


def render_property_card(listing, output_path):
    """1080x1350 hybrid card — photo top, brand info strip bottom."""
    bg_idx = _bg_for(listing.get("url") or "")
    bg = CARD_BACKGROUNDS[bg_idx]
    img = Image.new("RGB", (CARD_W, CARD_H), bg)

    # ── Photo panel (top) ──
    photo = _photo_panel(_fetch_image(listing.get("image")), CARD_W, PHOTO_H)
    if photo is not None:
        img.paste(photo, (0, 0))
    else:
        # Solid accent block as a fallback — keeps the card visually whole.
        fallback = Image.new("RGB", (CARD_W, PHOTO_H), ACCENT)
        img.paste(fallback, (0, 0))

    draw = ImageDraw.Draw(img)

    # Thin red accent rule between photo and strip
    draw.rectangle([(0, PHOTO_H - 6), (CARD_W, PHOTO_H)], fill=ACCENT)

    # ── Brand info strip (bottom) ──
    eyebrow_font = load_font("sans_bold", 22)
    price_font = load_font("serif_bold", 96)
    specs_font = load_font("sans_bold", 28)
    title_font = load_font("serif_bold", 36)
    footer_font = load_font("sans_bold", 22)
    masthead_font = load_font("sans_bold", 18)

    strip_top = PHOTO_H
    pad = 60

    # Eyebrow: PROPERTY · LOCATION
    location = (listing.get("location") or "Zimbabwe").strip()
    eyebrow = f"PROPERTY · {location.upper()}"
    draw.text((pad, strip_top + 30), eyebrow,
              font=eyebrow_font, fill=ACCENT)

    # Price — hero of the strip
    price = (listing.get("price") or "Price on request").strip()
    draw.text((pad, strip_top + 64), price,
              font=price_font, fill=CARD_FG)

    # Specs row: beds · baths
    spec_bits = []
    if listing.get("beds"):
        b = listing["beds"]
        spec_bits.append(f"{b} BED" + ("S" if str(b) != "1" else ""))
    if listing.get("baths"):
        b = listing["baths"]
        spec_bits.append(f"{b} BATH" + ("S" if str(b) != "1" else ""))
    if spec_bits:
        draw.text((pad, strip_top + 188), "  ·  ".join(spec_bits),
                  font=specs_font, fill=CARD_FG_MUTED)

    # Title (wrapped, up to 2 lines, sits below specs)
    title = (listing.get("title") or "").strip()
    if title:
        title_lines = wrap_text(title, title_font, CARD_W - 2 * pad, draw)[:2]
        ty = strip_top + 240
        for ln in title_lines:
            draw.text((pad, ty), ln, font=title_font, fill=CARD_FG)
            ty += 44

    # Footer chrome
    draw.rectangle([(0, CARD_H - 64), (CARD_W, CARD_H - 60)], fill=CARD_FG_MUTED)
    draw.text((pad, CARD_H - 48), "mutapatimes.com/property",
              font=footer_font, fill=ACCENT)
    src_name = (listing.get("source") or "Property.co.zw").strip()
    src_text = f"Listing source: {src_name}".upper()
    sw = draw.textlength(src_text, font=masthead_font)
    draw.text((CARD_W - pad - sw, CARD_H - 44), src_text,
              font=masthead_font, fill=CARD_FG_MUTED)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path, "PNG", optimize=True)


def collect_listings():
    if not os.path.exists(PROPERTIES_FILE):
        return []
    try:
        data = json.load(open(PROPERTIES_FILE))
    except (json.JSONDecodeError, OSError):
        return []
    out = []
    for L in (data.get("listings") or []):
        if (L.get("url") or "").strip():
            out.append(L)
    return out


def prune_stale_cards(active_hashes):
    pruned = 0
    for path in glob.glob(os.path.join(OUT_DIR, "*.png")):
        name = os.path.splitext(os.path.basename(path))[0]
        if len(name) != 12 or not all(c in "0123456789abcdef" for c in name):
            continue
        if name not in active_hashes:
            try:
                os.remove(path)
                pruned += 1
            except OSError as e:
                print(f"    prune FAIL {name}: {e}")
    return pruned


def main():
    print("=== BUILD PROPERTY CARDS ===")
    os.makedirs(OUT_DIR, exist_ok=True)
    listings = collect_listings()
    print(f"  {len(listings)} active listings")

    rendered = cached = failed = 0
    active_hashes = set()
    for L in listings:
        url = L["url"].strip()
        active_hashes.add(card_hash(url))
        out_path = os.path.join(OUT_DIR, card_filename(url))
        if os.path.exists(out_path):
            cached += 1
            continue
        try:
            render_property_card(L, out_path)
            rendered += 1
        except Exception as e:
            failed += 1
            print(f"    FAIL {L.get('title', '?')[:50]}: {e}")

    pruned = prune_stale_cards(active_hashes)
    print(f"  Rendered  {rendered} new")
    print(f"  Cached    {cached} existing")
    print(f"  Pruned    {pruned} stale")
    if failed:
        print(f"  Failed    {failed}")
    print(f"\n  Output:   {OUT_DIR}")
    print("\n=== DONE ===")


if __name__ == "__main__":
    main()
