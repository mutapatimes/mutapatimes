#!/usr/bin/env python3
"""
Fetch Zimbabwe news for all categories.
1. Try GNews API (if GNEWS_API_KEY is set)
2. Fall back to Google News RSS + og:image scraping from article pages
"""
import json
import os
import re
import sys
import time
import urllib.request
import urllib.error
import urllib.parse
import xml.etree.ElementTree as ET

API_KEY = os.environ.get("GNEWS_API_KEY", "")
DATA_DIR = "data"

CATEGORIES = {
    "business":      {
        "query": "Zimbabwe business OR Zimbabwe economy OR Zimbabwe finance OR Zimbabwe trade",
        "rss": "https://news.google.com/rss/search?q=Zimbabwe+business+economy+finance+trade&hl=en&gl=US&ceid=US:en"
    },
    "technology":    {
        "query": "Zimbabwe technology OR Zimbabwe tech OR Zimbabwe digital OR Zimbabwe innovation",
        "rss": "https://news.google.com/rss/search?q=Zimbabwe+technology+tech+digital+innovation&hl=en&gl=US&ceid=US:en"
    },
    "entertainment": {
        "query": "Zimbabwe entertainment OR Zimbabwe music OR Zimbabwe arts OR Zimbabwe culture OR Zimbabwe film",
        "rss": "https://news.google.com/rss/search?q=Zimbabwe+entertainment+music+arts+culture+film&hl=en&gl=US&ceid=US:en"
    },
    "sports":        {
        "query": "Zimbabwe sports OR Zimbabwe cricket OR Zimbabwe football OR Zimbabwe rugby OR Zimbabwe athletics",
        "rss": "https://news.google.com/rss/search?q=Zimbabwe+sports+cricket+football+rugby+athletics&hl=en&gl=US&ceid=US:en"
    },
    "science":       {
        "query": "Zimbabwe science OR Zimbabwe research OR Zimbabwe environment OR Zimbabwe wildlife",
        "rss": "https://news.google.com/rss/search?q=Zimbabwe+science+research+environment+wildlife&hl=en&gl=US&ceid=US:en"
    },
    "health":        {
        "query": "Zimbabwe health OR Zimbabwe medical OR Zimbabwe hospital OR Zimbabwe disease",
        "rss": "https://news.google.com/rss/search?q=Zimbabwe+health+medical+hospital+disease&hl=en&gl=US&ceid=US:en"
    },
}

HEADERS = {"User-Agent": "MutapaTimes/1.0 (news aggregator)"}


def fetch_url(url, as_json=True):
    """Fetch content from URL."""
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read().decode("utf-8", errors="replace")
            return json.loads(data) if as_json else data
    except Exception as e:
        print(f"    fetch error: {e}")
        return None


def extract_og_image(url):
    """Fetch a page and extract og:image meta tag."""
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=10) as resp:
            # Read only first 50KB to find meta tags quickly
            html = resp.read(50000).decode("utf-8", errors="replace")
        # Look for og:image meta tag
        match = re.search(
            r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
            html, re.IGNORECASE
        )
        if not match:
            match = re.search(
                r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
                html, re.IGNORECASE
            )
        if match:
            return match.group(1)
    except Exception:
        pass
    return ""


def extract_source(title):
    """Extract source name from 'Headline - Source' format."""
    idx = title.rfind(" - ")
    if idx > 0 and idx > len(title) * 0.3:
        return title[:idx].strip(), title[idx + 3:].strip()
    return title, ""


# ============================================================
# GNews API path
# ============================================================
def fetch_gnews(query):
    """Fetch via GNews search endpoint."""
    encoded_q = urllib.parse.quote(query)
    url = (
        f"https://gnews.io/api/v4/search"
        f"?q={encoded_q}&apikey={API_KEY}&lang=en&max=10&sortby=publishedAt&nullable=image"
    )
    return fetch_url(url)


# ============================================================
# RSS fallback path
# ============================================================
def fetch_rss(rss_url):
    """Fetch Google News RSS and parse into articles with og:image."""
    xml_text = fetch_url(rss_url, as_json=False)
    if not xml_text:
        return []

    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        print(f"    RSS parse error: {e}")
        return []

    articles = []
    items = root.findall(".//item")
    for item in items[:10]:
        title_el = item.find("title")
        link_el = item.find("link")
        pub_el = item.find("pubDate")
        desc_el = item.find("description")

        title = title_el.text if title_el is not None else ""
        link = link_el.text if link_el is not None else ""
        pub_date = pub_el.text if pub_el is not None else ""
        desc_html = desc_el.text if desc_el is not None else ""

        if not title:
            continue

        headline, source = extract_source(title)
        # Strip HTML from description
        desc_clean = re.sub(r'<[^>]+>', '', desc_html).strip()

        # Try to get og:image from the article URL
        image = ""
        if link:
            print(f"    Fetching og:image from: {link[:80]}...")
            image = extract_og_image(link)
            time.sleep(0.5)  # Be polite

        articles.append({
            "title": headline,
            "url": link,
            "description": desc_clean,
            "content": desc_clean,
            "image": image,
            "publishedAt": pub_date,
            "source": {"name": source} if source else {"name": ""},
        })

    return articles


def deduplicate(articles):
    """Deduplicate by URL, sort by date descending, return top 10."""
    seen = set()
    unique = []
    for a in articles:
        url = a.get("url", "")
        if url and url not in seen:
            seen.add(url)
            unique.append(a)
    unique.sort(key=lambda a: a.get("publishedAt", ""), reverse=True)
    return unique[:10]


def save_articles(name, articles):
    """Save articles to JSON file."""
    outpath = os.path.join(DATA_DIR, f"{name}.json")
    with open(outpath, "w") as f:
        json.dump({"articles": articles}, f)
    print(f"  OK: {name} — {len(articles)} articles saved")


def fetch_category(name, config):
    """Fetch Zimbabwe articles for a category."""
    print(f"\n=== {name.upper()} ===")

    # Try GNews API first
    if API_KEY:
        data = fetch_gnews(config["query"])
        if data and data.get("articles"):
            articles = deduplicate(data["articles"])
            save_articles(name, articles)
            return True
        print(f"  GNews returned no results for {name}, trying RSS...")

    # Fall back to Google News RSS with og:image scraping
    print(f"  Using RSS fallback for {name}...")
    articles = fetch_rss(config["rss"])
    if articles:
        articles = deduplicate(articles)
        save_articles(name, articles)
        return True

    print(f"  FAIL: {name} — no articles found from any source")
    return False


def main():
    if not API_KEY:
        print("WARNING: GNEWS_API_KEY not set — using RSS fallback with og:image scraping")

    os.makedirs(DATA_DIR, exist_ok=True)

    for name, config in CATEGORIES.items():
        fetch_category(name, config)
        time.sleep(2)

    print("\nDone.")


if __name__ == "__main__":
    main()
