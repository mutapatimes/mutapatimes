#!/usr/bin/env python3
"""Generate RSS 2.0 feed (feed.xml) for The Mutapa Times.

Every item links to a page on mutapatimes.com (a /news/{slug}.html landing
page for spotlight/category articles, or /articles/{slug}.html for CMS-
authored articles). This is what Metricool's Autolist will repost, so each
item MUST drive traffic to us rather than to the source publisher.

Items older than MAX_ITEM_AGE_DAYS are filtered out so a stale Google News
resurface can't auto-publish through Autolists.
"""
import glob
import json
import os
import re
import sys
from datetime import datetime, timezone, timedelta
from email.utils import format_datetime
from xml.sax.saxutils import escape

# Reuse the canonical slug + landing-page URL logic from build_news_pages
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_news_pages import make_slug as news_make_slug  # noqa: E402
from twitter_mentions import all_mentions  # noqa: E402

BASE_URL = "https://www.mutapatimes.com"
FEED_URL = f"{BASE_URL}/feed.xml"
# Bumped from 50 → 500 so a high-cadence Metricool Autolist on Twitter
# (~20/day) has enough fresh inventory to never starve before the next
# fetch-news run refills the feed.
MAX_ITEMS = 500
MAX_ITEM_AGE_DAYS = 30  # Autolists shouldn't ever republish stale wires


def _parse_date(s):
    """Try to parse ISO 8601 or RFC 2822 into a tz-aware datetime.
    Handles fractional seconds ('2026-05-10T17:46:27.000Z') used by CMS
    timestamps — the previous strptime patterns silently dropped these,
    so every CMS article fell out of the feed."""
    if not s:
        return None
    s = s.strip()
    # ISO 8601 via fromisoformat — accepts most variants once we normalise
    # the trailing Z to a UTC offset.
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        pass
    # Fallbacks: strptime patterns for date-only or simple ISO forms
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(s, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    # RFC 2822 (e.g., "Wed, 23 Jan 2019 08:00:00 GMT") used by Google News RSS
    try:
        from email.utils import parsedate_to_datetime
        return parsedate_to_datetime(s)
    except (TypeError, ValueError):
        return None


def _is_fresh(dt):
    if dt is None:
        return False
    try:
        return (datetime.now(timezone.utc) - dt).days <= MAX_ITEM_AGE_DAYS
    except (TypeError, ValueError):
        return False


def _normalize_source(src):
    if isinstance(src, dict):
        return (src.get("name") or "").strip()
    return str(src or "").strip()


def collect_cms_articles(base):
    """Read CMS markdown articles and return list of dicts. Links point to
    /articles/{slug}.html on mutapatimes.com."""
    items = []
    articles_dir = os.path.join(base, "content", "articles")
    for md in glob.glob(os.path.join(articles_dir, "*.md")):
        slug = os.path.splitext(os.path.basename(md))[0]
        if slug == "index":
            continue
        with open(md, "r", encoding="utf-8") as f:
            text = f.read()
        m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)", text, re.DOTALL)
        if not m:
            continue
        fm, body = m.group(1), m.group(2)
        # Use [^\S\n] (space/tab but NOT newline) so an empty 'image: ' line
        # doesn't greedily swallow the newline and steal the next field's
        # value. Same defensive change for the other fields.
        title = re.search(r'^title:[^\S\n]*["\']?(.+?)["\']?[^\S\n]*$', fm, re.MULTILINE)
        date = re.search(r"^date:[^\S\n]*['\"]?(\S+)", fm, re.MULTILINE)
        summary = re.search(r'^summary:[^\S\n]*["\']?(.+?)["\']?[^\S\n]*$', fm, re.MULTILINE)
        category = re.search(r'^category:[^\S\n]*["\']?(.+?)["\']?[^\S\n]*$', fm, re.MULTILINE)
        author = re.search(r'^author:[^\S\n]*["\']?(.+?)["\']?[^\S\n]*$', fm, re.MULTILINE)
        image = re.search(r'^image:[^\S\n]*["\']?(.+?)["\']?[^\S\n]*$', fm, re.MULTILINE)
        dt = _parse_date(date.group(1)) if date else None
        if not _is_fresh(dt):
            continue
        items.append({
            "title": title.group(1) if title else slug,
            "link": f"{BASE_URL}/articles/{slug}.html",
            "description": (summary.group(1) if summary else body[:240].strip()),
            "pubDate": dt,
            "category": category.group(1) if category else "News",
            "author": author.group(1) if author else None,
            "image": image.group(1) if image else None,
        })
    return items


def collect_news_landing_articles(base):
    """Read data/spotlight.json + data/{category}.json and emit one feed item
    per article, linking to the mutapatimes.com /news/{slug}.html landing
    page (NOT the source publisher's URL). Old articles are dropped."""
    items = []
    data_dir = os.path.join(base, "data")
    # Same set of feeds that build_news_pages reads + spotlight
    candidates = ["spotlight.json"] + [
        f"{cat}.json"
        for cat in ("business", "technology", "entertainment", "sports", "science", "health")
    ]
    seen_source_urls = set()
    for fname in candidates:
        path = os.path.join(data_dir, fname)
        if not os.path.exists(path):
            continue
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue
        if not isinstance(data, dict):
            continue
        for key in ("articles", "more"):
            for a in data.get(key) or []:
                if not isinstance(a, dict):
                    continue
                source_url = (a.get("url") or "").strip()
                title = (a.get("title") or "").strip()
                if not source_url or not title:
                    continue
                if source_url in seen_source_urls:
                    continue
                seen_source_urls.add(source_url)
                dt = _parse_date(a.get("publishedAt") or a.get("published_at") or "")
                if not _is_fresh(dt):
                    continue
                source_name = _normalize_source(a.get("source"))
                # Build the canonical mutapatimes.com landing URL — matches
                # what build_news_pages.py renders for the same article.
                landing = (
                    f"{BASE_URL}/news/"
                    f"{news_make_slug({'title': title, 'url': source_url, 'publishedAt': a.get('publishedAt') or ''})}.html"
                )
                desc = (a.get("description") or "").strip()
                # Add inline attribution so Autolist posts credit the source
                # while still linking to us. (Metricool's Autolist template
                # variables — ${title}, ${description}, ${link} — pull from
                # these three.)
                if source_name and source_name.lower() not in desc.lower():
                    desc = f"{desc} (via {source_name})" if desc else f"{title} — via {source_name}"
                items.append({
                    "title": title,
                    "link": landing,
                    "description": desc,
                    "pubDate": dt,
                    "category": fname.replace(".json", "").title() if fname != "spotlight.json" else "News",
                    "author": source_name or None,
                    "image": (a.get("image") or "").strip() or None,
                })
    return items


def build_rss(items):
    """Build RSS 2.0 XML string."""
    now = format_datetime(datetime.now(timezone.utc))
    items.sort(
        key=lambda x: x.get("pubDate") or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )
    items = items[:MAX_ITEMS]

    entries = []
    for item in items:
        pub = format_datetime(item["pubDate"]) if item.get("pubDate") else now
        cat = (
            f"      <category>{escape(item.get('category', 'News'))}</category>\n"
            if item.get("category") else ""
        )
        author = (
            f"      <dc:creator>{escape(item.get('author') or 'The Mutapa Times')}</dc:creator>\n"
            if item.get("author") else ""
        )
        image = ""
        if item.get("image"):
            # media:content + enclosure — Metricool's Autolist picks up
            # whichever it understands. Both are commonly supported.
            image = (
                f'      <media:content url="{escape(item["image"])}" medium="image"/>\n'
                f'      <enclosure url="{escape(item["image"])}" type="image/jpeg" length="0"/>\n'
            )
        # Append @mentions to the title so the Metricool Autolist tweet
        # template — ${title}\n\n${link}\n\n#Zimbabwe — naturally includes
        # them. Source publisher mention (e.g. @Reuters) + up to 2 entity
        # mentions (e.g. @CyrilRamaphosa @ZANUPF_Official). Capped so we
        # leave room for the URL (23 chars) and #Zimbabwe inside X's 280.
        title_text = item["title"]
        mentions = all_mentions(
            title_text, item.get("description", ""), item.get("author") or "",
        )
        if mentions:
            budget = 280 - 23 - len("\n\n") - len("\n\n#Zimbabwe") - len(title_text) - 1
            joined = []
            for m in mentions:
                cost = len(m) + 1  # leading space
                if cost > budget:
                    break
                joined.append(m)
                budget -= cost
            if joined:
                title_text = f"{title_text} {' '.join(joined)}"
        entries.append(
            "    <item>\n"
            f"      <title>{escape(title_text)}</title>\n"
            f"      <link>{escape(item['link'])}</link>\n"
            f"      <description>{escape(item.get('description', ''))}</description>\n"
            f"      <pubDate>{pub}</pubDate>\n"
            f'      <guid isPermaLink="true">{escape(item["link"])}</guid>\n'
            f"{cat}{author}{image}"
            "    </item>"
        )

    body = "\n".join(entries) + ("\n" if entries else "")
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0"\n'
        '     xmlns:atom="http://www.w3.org/2005/Atom"\n'
        '     xmlns:dc="http://purl.org/dc/elements/1.1/"\n'
        '     xmlns:media="http://search.yahoo.com/mrss/">\n'
        "  <channel>\n"
        "    <title>The Mutapa Times</title>\n"
        f"    <link>{BASE_URL}</link>\n"
        "    <description>Business and intelligence newspaper delivering curated Zimbabwean news from foreign press for the diaspora.</description>\n"
        "    <language>en</language>\n"
        f"    <lastBuildDate>{now}</lastBuildDate>\n"
        f'    <atom:link href="{FEED_URL}" rel="self" type="application/rss+xml"/>\n'
        "    <image>\n"
        "      <title>The Mutapa Times</title>\n"
        f"      <url>{BASE_URL}/img/logo.png</url>\n"
        f"      <link>{BASE_URL}</link>\n"
        "    </image>\n"
        "    <copyright>Copyright 2020-2026 The Mutapa Times</copyright>\n"
        "    <managingEditor>news@mutapatimes.com (The Mutapa Times)</managingEditor>\n"
        "    <webMaster>news@mutapatimes.com (The Mutapa Times)</webMaster>\n"
        f"{body}"
        "  </channel>\n"
        "</rss>\n"
    )


def _norm_title(s):
    """Lowercase + collapse non-alphanumerics so 'Foo!' and 'Foo' match."""
    return re.sub(r"[^a-z0-9]+", "", (s or "").lower())


def main():
    base = os.path.join(os.path.dirname(__file__), "..")
    # CMS first so its /articles/{slug}.html link wins over the /news/{slug}.html
    # landing variant when the same story appears in both (the CMS page has
    # the full body text — better for SEO and reader experience).
    items = collect_cms_articles(base) + collect_news_landing_articles(base)
    seen_links = set()
    seen_titles = set()
    unique = []
    for item in items:
        link = item["link"]
        t_norm = _norm_title(item.get("title", ""))
        if link in seen_links or (t_norm and t_norm in seen_titles):
            continue
        seen_links.add(link)
        if t_norm:
            seen_titles.add(t_norm)
        unique.append(item)
    rss = build_rss(unique)
    out = os.path.join(base, "feed.xml")
    with open(out, "w", encoding="utf-8") as f:
        f.write(rss)
    print(f"feed.xml written with {min(len(unique), MAX_ITEMS)} items "
          f"(linking to mutapatimes.com; <={MAX_ITEM_AGE_DAYS}d old)")


if __name__ == "__main__":
    main()
