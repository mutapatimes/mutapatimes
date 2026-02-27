#!/usr/bin/env python3
"""Generate RSS 2.0 feed (feed.xml) for The Mutapa Times."""
import glob
import json
import os
import re
from datetime import datetime, timezone
from email.utils import format_datetime
from xml.sax.saxutils import escape

BASE_URL = "https://www.mutapatimes.com"
FEED_URL = f"{BASE_URL}/feed.xml"
MAX_ITEMS = 50


def _parse_date(s):
    """Try to parse an ISO-ish date string into a datetime."""
    if not s:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(s.strip(), fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    return None


def collect_cms_articles(base):
    """Read CMS markdown articles and return list of dicts."""
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
        title = re.search(r'^title:\s*["\']?(.+?)["\']?\s*$', fm, re.MULTILINE)
        date = re.search(r"^date:\s*['\"]?(\S+)", fm, re.MULTILINE)
        summary = re.search(r'^summary:\s*["\']?(.+?)["\']?\s*$', fm, re.MULTILINE)
        category = re.search(r'^category:\s*["\']?(.+?)["\']?\s*$', fm, re.MULTILINE)
        author = re.search(r'^author:\s*["\']?(.+?)["\']?\s*$', fm, re.MULTILINE)
        image = re.search(r'^image:\s*["\']?(.+?)["\']?\s*$', fm, re.MULTILINE)
        dt = _parse_date(date.group(1)) if date else None
        items.append({
            "title": title.group(1) if title else slug,
            "link": f"{BASE_URL}/articles/{slug}.html",
            "description": (summary.group(1) if summary else body[:200].strip()),
            "pubDate": dt,
            "category": category.group(1) if category else "News",
            "author": author.group(1) if author else None,
            "image": image.group(1) if image else None,
        })
    return items


def collect_json_articles(base):
    """Read data/*.json news files and return list of dicts."""
    items = []
    data_dir = os.path.join(base, "data")
    for jf in glob.glob(os.path.join(data_dir, "*.json")):
        fname = os.path.basename(jf)
        if fname in ("rss_descriptions.json",):
            continue
        try:
            with open(jf, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue
        # Handle both flat list and object with "articles"/"more" keys
        articles = []
        if isinstance(data, list):
            articles = data
        elif isinstance(data, dict):
            for key in ("articles", "more", "items"):
                articles.extend(data.get(key, []))
            if not articles and "title" in data:
                articles = [data]
        for a in articles:
            title = a.get("title", "")
            url = a.get("url") or a.get("link", "")
            if not title or not url:
                continue
            dt = _parse_date(a.get("publishedAt") or a.get("published_at") or a.get("date", ""))
            items.append({
                "title": title,
                "link": url,
                "description": a.get("description") or a.get("summary", ""),
                "pubDate": dt,
                "category": a.get("category", "News"),
            })
    return items


def build_rss(items):
    """Build RSS 2.0 XML string."""
    now = format_datetime(datetime.now(timezone.utc))
    # Sort by date descending, take top MAX_ITEMS
    items.sort(key=lambda x: x.get("pubDate") or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    items = items[:MAX_ITEMS]

    entries = []
    for item in items:
        pub = format_datetime(item["pubDate"]) if item.get("pubDate") else now
        cat = f"      <category>{escape(item.get('category', 'News'))}</category>\n" if item.get("category") else ""
        author = f"      <dc:creator>{escape(item.get('author', 'The Mutapa Times'))}</dc:creator>\n" if item.get("author") else ""
        image = ""
        if item.get("image"):
            image = f'      <media:content url="{escape(item["image"])}" medium="image"/>\n'
        entries.append(
            f"    <item>\n"
            f"      <title>{escape(item['title'])}</title>\n"
            f"      <link>{escape(item['link'])}</link>\n"
            f"      <description>{escape(item.get('description', ''))}</description>\n"
            f"      <pubDate>{pub}</pubDate>\n"
            f"      <guid isPermaLink=\"true\">{escape(item['link'])}</guid>\n"
            f"{cat}{author}{image}"
            f"    </item>"
        )

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
        f"      <title>The Mutapa Times</title>\n"
        f"      <url>{BASE_URL}/img/logo.png</url>\n"
        f"      <link>{BASE_URL}</link>\n"
        "    </image>\n"
        "    <copyright>Copyright 2020-2026 The Mutapa Times</copyright>\n"
        "    <managingEditor>news@mutapatimes.com (The Mutapa Times)</managingEditor>\n"
        "    <webMaster>news@mutapatimes.com (The Mutapa Times)</webMaster>\n"
        "\n".join(entries) + "\n"
        "  </channel>\n"
        "</rss>\n"
    )


def main():
    base = os.path.join(os.path.dirname(__file__), "..")
    items = collect_cms_articles(base) + collect_json_articles(base)
    # Deduplicate by link
    seen = set()
    unique = []
    for item in items:
        if item["link"] not in seen:
            seen.add(item["link"])
            unique.append(item)
    rss = build_rss(unique)
    out = os.path.join(base, "feed.xml")
    with open(out, "w", encoding="utf-8") as f:
        f.write(rss)
    print(f"feed.xml written with {min(len(unique), MAX_ITEMS)} items")


if __name__ == "__main__":
    main()
