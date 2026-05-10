#!/usr/bin/env python3
"""
Scrape Zimbabwe house listings from property.co.zw and save to
data/property-listings.json for client-side rendering on /property.html.
Server-rendered HTML, parsed with stdlib regex — no third-party deps.
"""
import html as html_mod
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

SOURCE_URL = "https://www.property.co.zw/houses-for-sale"
SITE_BASE = "https://www.property.co.zw"
DATA_DIR = "data"
OUTPUT_FILE = os.path.join(DATA_DIR, "property-listings.json")
USER_AGENT = "Mozilla/5.0 (compatible; MutapaTimesBot/1.0; +https://www.mutapatimes.com)"
MAX_LISTINGS = 24  # client renders top 12; extra is buffer


# ── Card extraction ────────────────────────────────────────
CARD_OPEN_RE = re.compile(
    r'<div\b[^>]*\bclass="[^"]*\bResultCardItem\b[^"]*"[^>]*>'
)
DIV_OPEN_RE = re.compile(r'<div\b')
DIV_CLOSE_RE = re.compile(r'</div\s*>')

TITLE_RE = re.compile(
    r'<h2\b[^>]*>\s*<a\b[^>]*href="([^"]+)"[^>]*>\s*([^<]+?)\s*</a>',
    re.DOTALL,
)
PRICE_RE = re.compile(
    r'<div\b[^>]*class="[^"]*\bresult-price\b[^"]*"[^>]*>\s*<a\b[^>]*>\s*'
    r'([A-Z]{3}\s*[\d,]+(?:\.\d+)?|\$\s*[\d,]+(?:\.\d+)?)',
    re.DOTALL,
)
LOCATION_RE = re.compile(
    r'<div\s+class="text-graypurpledark[^"]*overflow-ellipse[^"]*"[^>]*>\s*'
    r'([^<]+?)\s*</div>',
    re.DOTALL,
)
IMAGE_RE = re.compile(
    r'<img\b[^>]*\b(?:src|data-src)="([^"]+)"[^>]*\bclass="[^"]*\bswiper-lazy\b',
    re.DOTALL,
)
BED_RE = re.compile(
    r'<span\s+class="bed[^"]*"[^>]*>.*?(\d+)\s*</span>', re.DOTALL,
)
BATH_RE = re.compile(
    r'<span\s+class="bath[^"]*"[^>]*>.*?(\d+)\s*</span>', re.DOTALL,
)


def fetch_html(url):
    """GET the page with a real User-Agent; many sites 403 anonymous bots."""
    req = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-US,en;q=0.9",
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def find_card_end(text, start):
    """Given the index of the opening <div for a card, return the index just
    past the matching </div>. Returns -1 if unmatched."""
    depth = 1
    i = start
    while i < len(text):
        next_open = DIV_OPEN_RE.search(text, i)
        next_close = DIV_CLOSE_RE.search(text, i)
        if not next_close:
            return -1
        if next_open and next_open.start() < next_close.start():
            depth += 1
            i = next_open.end()
        else:
            depth -= 1
            i = next_close.end()
            if depth == 0:
                return i
    return -1


def clean_text(s):
    """Decode entities, collapse whitespace."""
    if not s:
        return ""
    s = html_mod.unescape(s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def absolute_url(url):
    if not url:
        return ""
    if url.startswith("//"):
        return "https:" + url
    if url.startswith("/"):
        return SITE_BASE + url
    return url


def parse_card(card_html):
    """Extract fields from one card. Returns dict or None if title missing."""
    m_title = TITLE_RE.search(card_html)
    if not m_title:
        return None
    href = m_title.group(1)
    title = clean_text(m_title.group(2))
    if not title:
        return None

    m_price = PRICE_RE.search(card_html)
    price = clean_text(m_price.group(1)) if m_price else ""

    m_location = LOCATION_RE.search(card_html)
    location = clean_text(m_location.group(1)) if m_location else ""

    m_image = IMAGE_RE.search(card_html)
    image = absolute_url(m_image.group(1)) if m_image else ""

    m_bed = BED_RE.search(card_html)
    beds = m_bed.group(1) if m_bed else ""

    m_bath = BATH_RE.search(card_html)
    baths = m_bath.group(1) if m_bath else ""

    return {
        "title": title,
        "url": absolute_url(href),
        "price": price,
        "location": location,
        "image": image,
        "beds": beds,
        "baths": baths,
    }


def extract_listings(html):
    """Walk the page, extract one record per ResultCardItem."""
    listings = []
    pos = 0
    while True:
        m = CARD_OPEN_RE.search(html, pos)
        if not m:
            break
        end = find_card_end(html, m.end())
        if end < 0:
            break
        card_html = html[m.end():end]
        record = parse_card(card_html)
        if record:
            listings.append(record)
        pos = end
    return listings


def main():
    print("=== FETCH PROPERTY LISTINGS ===")
    print(f"  Source: {SOURCE_URL}")

    try:
        page = fetch_html(SOURCE_URL)
    except urllib.error.HTTPError as e:
        print(f"  HTTP {e.code}: {e.reason}")
        sys.exit(1)
    except Exception as e:
        print(f"  ERROR fetching: {e}")
        sys.exit(1)

    print(f"  Fetched {len(page):,} bytes")

    all_listings = extract_listings(page)
    print(f"  Parsed {len(all_listings)} listings")

    if not all_listings:
        print("  WARN: 0 listings parsed. Site may have changed structure.")
        print("  Not overwriting existing data.")
        sys.exit(1)

    listings = all_listings[:MAX_LISTINGS]

    output = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source": SOURCE_URL,
        "count": len(listings),
        "listings": listings,
    }

    os.makedirs(DATA_DIR, exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"  Wrote {OUTPUT_FILE} ({len(listings)} listings)")
    print("\n=== DONE ===")


if __name__ == "__main__":
    main()
