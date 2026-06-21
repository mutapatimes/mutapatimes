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
WIRES_DIR = os.path.join(ROOT, "content", "wires")

OUT_DIR = os.path.join(ROOT, "img", "cards", "news")
PUBLIC_BASE = "https://mutapatimes.com/img/cards/news"

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


def _url_region(url):
    """Which edition a URL belongs to, by path prefix — generic over every
    non-default region in regions.py (so new editions need no edit here)."""
    u = url or ""
    try:
        from regions import all_region_codes, region_path_prefix, DEFAULT_REGION
        for code in all_region_codes():
            if code == DEFAULT_REGION:
                continue
            pre = region_path_prefix(code)        # e.g. "/za"
            if pre and (pre + "/") in u:
                return code
    except ImportError:
        if "/za/" in u:
            return "za"
    return "zw"


def card_dir(region="zw"):
    """On-disk card folder. Per-region so a non-root build's prune pass
    can never delete another edition's cards."""
    return OUT_DIR if region == "zw" else os.path.join(ROOT, "img", "cards", region, "news")


def card_public_base(region="zw"):
    return PUBLIC_BASE if region == "zw" else f"https://mutapatimes.com/img/cards/{region}/news"


def card_public_url(url):
    # Region inferred from the URL so callers (build_static_pages etc.) need
    # no change: a /za/... canonical resolves to the /za card folder, a root
    # URL to the original folder (Zimbabwe output unchanged).
    return f"{card_public_base(_url_region(url))}/{card_filename(url)}"


# ── Image-rights risk ────────────────────────────────────────────────────
# Major international news agencies / outlets whose photographs are routinely
# enforced by image-rights firms (e.g. PicRights acting for AFP, Reuters, AP,
# Getty, EPA). We never hotlink these as a page hero; the generators swap in
# our own gradient artwork instead. Zimbabwean / local outlets are NOT listed
# here on purpose — they are left untouched. Match is a substring on the host.
BIG_LEAGUE_IMAGE_HOSTS = (
    "guim.co.uk", "theguardian.com",
    "reuters.com", "reutersmedia",
    "bbci.co.uk", "bbc.co.uk", "bbc.com",
    "apnews.com", "ap.org",
    "gettyimages", "gstatic",
    "afp.com",
    "nytimes.com", "nyt.com", "washingtonpost", "cnn.com", "cnn.io",
    "aljazeera", "bloomberg", "ft.com",
    "telegraph.co.uk", "telegraphindia.com",
    "thetimes.co.uk", "thetimes.com",
    "independent.co.uk", "mirror.co.uk", "thesun.co.uk",
    "sky.com", "skynews", "dw.com", "france24", "euronews.com",
    "nbcnews", "abcnews", "cbsnews", "foxnews",
    "news18.com", "ndtvimg.com", "ndtv.com", "tribuneindia.com",
    "hindustantimes", "indianexpress", "news18", "india.com",
    "cricbuzz.com", "hscicdn.com", "imgci.com", "icc-cricket.com",
    "espncdn", "espncricinfo", "flashscore",
    "creamermedia.com", "engineeringnews.co.za",
    "modernghana.com", "allafrica.com", "briefly.co.za",
    "news24.com", "iol.co.za", "iol-prod", "mg.co.za", "dailymaverick",
    "b37mrtl.ru", "rt.com", "tass.",
    "assettype.com", "simplywall.st", "euronews",
)


def is_rights_risky(url):
    """True if the image URL is hosted by a major international agency/outlet
    we should not hotlink. Local/Zimbabwean outlets return False."""
    if not url:
        return False
    u = str(url).strip().lower()
    if not u.startswith("http"):
        return False
    try:
        from urllib.parse import urlparse
        host = (urlparse(u).hostname or "")
    except Exception:
        host = u
    return any(h in host for h in BIG_LEAGUE_IMAGE_HOSTS)


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


def _walk_cms_articles(region="zw"):
    """Yield {title, source, url, publishedAt} per published markdown
    article in both folders: content/articles (originals) and
    content/wires (auto-imported archive). Drafts are skipped.

    Without walking the wires folder, every wire entry in
    content/articles/index.json points to a card_image path that 404s,
    which is what was breaking the stories rail."""
    pfx = "" if region == "zw" else f"/{region}"
    if region == "zw":
        folders = (CMS_DIR, WIRES_DIR)
    else:
        folders = (os.path.join(ROOT, "content", region, "articles"),
                   os.path.join(ROOT, "content", region, "wires"))
    for folder in folders:
        for md in glob.glob(os.path.join(folder, "*.md")):
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
            if re.search(r'^draft:\s*true\s*$', fm, re.MULTILINE | re.IGNORECASE):
                continue
            title_m = re.search(r'^title:[^\S\n]*["\']?(.+?)["\']?[^\S\n]*$', fm,
                                re.MULTILINE)
            date_m = re.search(r"^date:[^\S\n]*['\"]?(\S+)", fm, re.MULTILINE)
            author_m = re.search(r'^author:[^\S\n]*["\']?(.+?)["\']?[^\S\n]*$', fm,
                                  re.MULTILINE)
            title = title_m.group(1) if title_m else slug
            author = author_m.group(1) if author_m else "Mutapa Times"
            # CMS articles live at /articles/{slug}.html — same URL build_news_pages
            # links to and what generate_rss.collect_cms_articles emits.
            url = f"https://mutapatimes.com{pfx}/articles/{slug}.html"
            yield {
                "title": title,
                "source": author,
                "url": url,
                "publishedAt": date_m.group(1) if date_m else "",
            }


def collect_articles(region="zw"):
    """De-dupe by URL across all sources."""
    seen = set()
    out = []
    # CMS first (richer metadata + we like the /articles/ link wining)
    for a in _walk_cms_articles(region):
        if a["url"] in seen:
            continue
        seen.add(a["url"])
        out.append(a)
    # Then news landing JSONs (spotlight + categories)
    data_dir = DATA_DIR if region == "zw" else os.path.join(DATA_DIR, region)
    for src in [os.path.join(data_dir, "spotlight.json")] + [os.path.join(data_dir, f"{c}.json")
                                    for c in CATEGORY_FILES]:
        for a in _walk_news_json(src):
            if a["url"] in seen:
                continue
            seen.add(a["url"])
            out.append(a)
    return out


def prune_stale_cards(active_url_hashes, out_dir=OUT_DIR):
    """Delete any card PNG whose article URL is no longer in the active
    corpus. Keeps the card folder tracking the live feed window
    (~30 days) instead of growing forever — without this, the repo
    breaks GitHub Pages' 1 GB site-size cap in ~3 months. Scoped to a
    single region's out_dir so one edition never prunes another's."""
    pruned = 0
    for path in glob.glob(os.path.join(out_dir, "*.png")):
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
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", default="zw",
                    help="Region edition (default: zw = Zimbabwe at the root)")
    region = ap.parse_args().region
    out_dir = card_dir(region)
    print("=== BUILD FEED CARDS ===")
    os.makedirs(out_dir, exist_ok=True)

    articles = collect_articles(region)
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
        out_path = os.path.join(out_dir, card_filename(art["url"]))
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
    pruned = prune_stale_cards(active_hashes, out_dir)

    print(f"  Rendered  {rendered} new cards")
    print(f"  Cached    {skipped_existing} existing")
    print(f"  Stale     {skipped_stale} (>{MAX_AGE_DAYS}d old, skipped)")
    print(f"  Pruned    {pruned} stale card files")
    if failed:
        print(f"  Failed    {failed}")
    print(f"\n  Output:   {out_dir}")
    print("\n=== DONE ===")


if __name__ == "__main__":
    main()
