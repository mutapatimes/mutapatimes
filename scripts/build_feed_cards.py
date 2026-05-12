#!/usr/bin/env python3
"""Render a beautifully-designed branded card for every article that
appears in feed.xml. The cards become each RSS item's image — so every
post that flows through the Metricool autolist is visually on-brand,
no scraped-source thumbnails.

Output:
    img/cards/news/{12-char-md5-of-url}.png  (1080x1350 portrait)

Cards are cached by URL hash, so re-running only renders new articles.
The faded brand palette (dusty rose · sage green · butter · cream) is
chosen deterministically from the URL hash so each article keeps the
same colour run-to-run, but the feed-level rotation feels varied.
"""
import glob
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone

# Shared card primitives — single source of truth
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from card_lib import CARD_BACKGROUNDS, render_headline_card  # noqa: E402

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
DATA_DIR = os.path.join(ROOT, "data")
SPOTLIGHT_FILE = os.path.join(DATA_DIR, "spotlight.json")
CATEGORY_FILES = ["business", "technology", "entertainment",
                  "sports", "science", "health"]
CMS_DIR = os.path.join(ROOT, "content", "articles")

OUT_DIR = os.path.join(ROOT, "img", "cards", "news")
PUBLIC_BASE = "https://www.mutapatimes.com/img/cards/news"

# Skip rendering anything published more than this many days ago. Same
# 30-day window we use everywhere else; keeps the on-disk footprint
# bounded and avoids rendering 4,000+ cards on first run.
MAX_AGE_DAYS = 30


def card_hash(url):
    """Stable 12-char MD5 of the article URL — used both as filename
    and as the per-card colour-index seed."""
    return hashlib.md5((url or "").encode("utf-8")).hexdigest()[:12]


def card_filename(url):
    return f"{card_hash(url)}.png"


def card_public_url(url):
    return f"{PUBLIC_BASE}/{card_filename(url)}"


def color_for(url):
    """Deterministic colour index per URL. int(hex, 16) makes the
    distribution effectively random across articles."""
    h = card_hash(url)
    return int(h, 16) % len(CARD_BACKGROUNDS)


def _normalize_source(src):
    if isinstance(src, dict):
        return (src.get("name") or "").strip()
    return str(src or "").strip()


def _parse_pub_date(s):
    """ISO 8601 or RFC 2822 → tz-aware datetime, or None."""
    if not s:
        return None
    s = s.strip()
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, AttributeError):
        pass
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(s, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    try:
        from email.utils import parsedate_to_datetime
        return parsedate_to_datetime(s)
    except (TypeError, ValueError):
        return None


def _is_fresh(dt):
    if dt is None:
        return False
    try:
        return (datetime.now(timezone.utc) - dt).days <= MAX_AGE_DAYS
    except (TypeError, ValueError):
        return False


def _walk_news_json(filepath):
    """Yield {title, source, url, publishedAt} per article in a
    spotlight/category JSON."""
    if not os.path.isfile(filepath):
        return
    try:
        data = json.load(open(filepath))
    except (json.JSONDecodeError, OSError):
        return
    for a in data.get("articles", []) or []:
        url = (a.get("url") or "").strip()
        title = (a.get("title") or "").strip()
        if not url or not title:
            continue
        yield {
            "title": title,
            "source": _normalize_source(a.get("source")),
            "url": url,
            "publishedAt": a.get("publishedAt") or "",
        }


def _walk_cms_articles():
    """Yield {title, source, url, publishedAt} per CMS markdown article."""
    for md in glob.glob(os.path.join(CMS_DIR, "*.md")):
        slug = os.path.splitext(os.path.basename(md))[0]
        if slug == "index":
            continue
        try:
            with open(md, "r", encoding="utf-8") as f:
                text = f.read()
        except OSError:
            continue
        m = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
        if not m:
            continue
        fm = m.group(1)
        title_m = re.search(r'^title:[^\S\n]*["\']?(.+?)["\']?[^\S\n]*$', fm,
                            re.MULTILINE)
        date_m = re.search(r"^date:[^\S\n]*['\"]?(\S+)", fm, re.MULTILINE)
        author_m = re.search(r'^author:[^\S\n]*["\']?(.+?)["\']?[^\S\n]*$', fm,
                              re.MULTILINE)
        title = title_m.group(1) if title_m else slug
        author = author_m.group(1) if author_m else "Mutapa Times"
        # CMS articles live at /articles/{slug}.html — same URL build_news_pages
        # links to and what generate_rss.collect_cms_articles emits.
        url = f"https://www.mutapatimes.com/articles/{slug}.html"
        yield {
            "title": title,
            "source": author,
            "url": url,
            "publishedAt": date_m.group(1) if date_m else "",
        }


def collect_articles():
    """De-dupe by URL across all sources."""
    seen = set()
    out = []
    # CMS first (richer metadata + we like the /articles/ link wining)
    for a in _walk_cms_articles():
        if a["url"] in seen:
            continue
        seen.add(a["url"])
        out.append(a)
    # Then news landing JSONs (spotlight + categories)
    for src in [SPOTLIGHT_FILE] + [os.path.join(DATA_DIR, f"{c}.json")
                                    for c in CATEGORY_FILES]:
        for a in _walk_news_json(src):
            if a["url"] in seen:
                continue
            seen.add(a["url"])
            out.append(a)
    return out


def prune_stale_cards(active_url_hashes):
    """Delete any card PNG whose article URL is no longer in the active
    corpus. Keeps img/cards/news/ tracking the live feed window
    (~30 days) instead of growing forever — without this, the repo
    breaks GitHub Pages' 1 GB site-size cap in ~3 months."""
    pruned = 0
    for path in glob.glob(os.path.join(OUT_DIR, "*.png")):
        name = os.path.splitext(os.path.basename(path))[0]
        # Cards we own follow the 12-char-md5 naming convention. Anything
        # else (manual uploads, legacy assets) we leave alone.
        if len(name) != 12 or not all(c in "0123456789abcdef" for c in name):
            continue
        if name not in active_url_hashes:
            try:
                os.remove(path)
                pruned += 1
            except OSError as e:
                print(f"    prune FAIL {name}: {e}")
    return pruned


def main():
    print("=== BUILD FEED CARDS ===")
    os.makedirs(OUT_DIR, exist_ok=True)

    articles = collect_articles()
    print(f"  Walked {len(articles)} articles across CMS + spotlight + categories")

    rendered = 0
    skipped_existing = 0
    skipped_stale = 0
    failed = 0
    # URLs that survived the 30-day freshness filter — these are the
    # *only* cards that should remain on disk after the prune pass.
    active_hashes = set()

    for art in articles:
        dt = _parse_pub_date(art.get("publishedAt"))
        if not _is_fresh(dt):
            skipped_stale += 1
            continue
        active_hashes.add(card_hash(art["url"]))
        out_path = os.path.join(OUT_DIR, card_filename(art["url"]))
        if os.path.exists(out_path):
            skipped_existing += 1
            continue
        try:
            render_headline_card(
                headline=art["title"],
                source=art.get("source") or "",
                output_path=out_path,
                color_idx=color_for(art["url"]),
            )
            rendered += 1
        except Exception as e:
            failed += 1
            print(f"    FAIL {art['title'][:50]}: {e}")

    # ── Cleanup pass: delete cards whose article is no longer active ──
    pruned = prune_stale_cards(active_hashes)

    print(f"  Rendered  {rendered} new cards")
    print(f"  Cached    {skipped_existing} existing")
    print(f"  Stale     {skipped_stale} (>{MAX_AGE_DAYS}d old, skipped)")
    print(f"  Pruned    {pruned} stale card files")
    if failed:
        print(f"  Failed    {failed}")
    print(f"\n  Output:   {OUT_DIR}")
    print("\n=== DONE ===")


if __name__ == "__main__":
    main()
