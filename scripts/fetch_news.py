#!/usr/bin/env python3
"""
Fetch Zimbabwe news from GNews API for all categories.
Also fetches Google News RSS feeds and generates AI descriptions
for articles missing them (using Gemini free tier).
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
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
DATA_DIR = "data"

# Google News RSS feeds — same as config.js
RSS_FEEDS = [
    "https://news.google.com/rss/search?q=Zimbabwe&hl=en&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=Zimbabwe+news+today&hl=en&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=Harare+OR+Bulawayo+OR+Mutare&hl=en&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=Zimbabwe+politics+government+economy&hl=en&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=site:zimlive.com+OR+site:newsday.co.zw+OR+site:herald.co.zw+OR+site:bulawayo24.com+OR+site:263chat.com&hl=en&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=site:pindula.co.zw+OR+site:nehanda radio+OR+site:newzimbabwe.com+OR+site:thezimbabwemail.com&hl=en&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=Zimbabwe+local+news&hl=en&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=Zimbabwe+business+sports+entertainment+health&hl=en&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=Harare+Bulawayo+Gweru+Masvingo+Mutare+Chitungwiza&hl=en&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=Zimbabwe+site:bbc.com+OR+site:reuters.com+OR+site:nytimes.com+OR+site:theguardian.com+OR+site:aljazeera.com+OR+site:ft.com+OR+site:economist.com+OR+site:bloomberg.com+OR+site:apnews.com&hl=en&gl=US&ceid=US:en",
]

CATEGORIES = {
    "business":      {"query": "Zimbabwe business OR Zimbabwe economy OR Zimbabwe finance OR Zimbabwe trade"},
    "technology":    {"query": "Zimbabwe technology OR Zimbabwe tech OR Zimbabwe digital OR Zimbabwe innovation"},
    "entertainment": {"query": "Zimbabwe entertainment OR Zimbabwe music OR Zimbabwe arts OR Zimbabwe culture OR Zimbabwe film"},
    "sports":        {"query": "Zimbabwe sports OR Zimbabwe cricket OR Zimbabwe football OR Zimbabwe rugby OR Zimbabwe athletics"},
    "science":       {"query": "Zimbabwe science OR Zimbabwe research OR Zimbabwe environment OR Zimbabwe wildlife"},
    "health":        {"query": "Zimbabwe health OR Zimbabwe medical OR Zimbabwe hospital OR Zimbabwe disease"},
}


def fetch_url(url, as_json=True):
    """Fetch from URL, return parsed JSON or raw bytes."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "MutapaTimes/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read()
            return json.loads(data.decode("utf-8")) if as_json else data
    except Exception as e:
        print(f"    fetch error: {e}")
        return None


def fetch_search(query):
    """Fetch via search endpoint — Zimbabwe-focused, global English."""
    encoded_q = urllib.parse.quote(query)
    url = (
        f"https://gnews.io/api/v4/search"
        f"?q={encoded_q}&apikey={API_KEY}&lang=en&max=10&sortby=publishedAt&nullable=image"
    )
    return fetch_url(url)


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


def generate_description(title, content=""):
    """Generate a 1-2 sentence summary using Gemini free tier."""
    if not GEMINI_API_KEY:
        return ""

    source_text = content[:1500] if content else title
    prompt = (
        "Write a 1-2 sentence news summary (under 200 characters) for this article. "
        "Be factual and neutral. Do not start with 'This article'. Just state what happened.\n\n"
        f"Title: {title}\n"
        f"Content: {source_text}"
    )

    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": 100, "temperature": 0.2}
    }).encode("utf-8")

    try:
        req = urllib.request.Request(
            f"{GEMINI_URL}?key={GEMINI_API_KEY}",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            text = result["candidates"][0]["content"]["parts"][0]["text"].strip()
            text = text.strip('"\'')
            return text[:250] if len(text) > 250 else text
    except Exception as e:
        print(f"    Gemini error: {e}")
        return ""


def backfill_descriptions(articles):
    """Fill missing/short descriptions with AI-generated summaries."""
    if not GEMINI_API_KEY:
        return
    for article in articles:
        desc = (article.get("description") or "").strip()
        if len(desc) < 20:
            generated = generate_description(
                article.get("title", ""),
                article.get("content", "")
            )
            if generated:
                article["description"] = generated
                print(f"    AI desc: {article['title'][:50]}...")
            time.sleep(1)


def fetch_category(name, config):
    """Fetch Zimbabwe articles for a category."""
    print(f"\n=== {name.upper()} ===")

    data = fetch_search(config["query"])
    if data and data.get("articles"):
        articles = deduplicate(data["articles"])
        backfill_descriptions(articles)
        output = {"articles": articles}
        outpath = os.path.join(DATA_DIR, f"{name}.json")
        with open(outpath, "w") as f:
            json.dump(output, f)
        print(f"  OK: {name} — {len(articles)} articles saved")
        return True

    print(f"  FAIL: {name} — no articles found")
    return False


def strip_html(html):
    """Remove HTML tags and decode entities."""
    text = re.sub(r"<[^>]+>", " ", html)
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("&quot;", '"').replace("&#39;", "'").replace("&nbsp;", " ")
    return re.sub(r"\s+", " ", text).strip()


def parse_rss_feed(xml_bytes):
    """Parse Google News RSS XML, return list of {title, url} dicts."""
    articles = []
    try:
        root = ET.fromstring(xml_bytes)
        for item in root.iter("item"):
            title_el = item.find("title")
            link_el = item.find("link")
            if title_el is None or link_el is None:
                continue
            raw_title = title_el.text or ""
            # Google News format: "Headline - Source Name"
            # Extract just the headline
            parts = raw_title.rsplit(" - ", 1)
            headline = parts[0].strip()
            url = (link_el.text or "").strip()
            if headline and url:
                articles.append({"title": headline, "url": url})
    except ET.ParseError as e:
        print(f"    XML parse error: {e}")
    return articles


def fetch_rss_descriptions():
    """Fetch Google News RSS feeds, generate AI descriptions, save lookup."""
    if not GEMINI_API_KEY:
        print("\n=== RSS DESCRIPTIONS ===")
        print("  SKIP: GEMINI_API_KEY not set")
        return

    print("\n=== RSS DESCRIPTIONS ===")

    # Load existing lookup to avoid re-generating
    lookup_path = os.path.join(DATA_DIR, "rss_descriptions.json")
    existing = {}
    if os.path.exists(lookup_path):
        try:
            with open(lookup_path) as f:
                existing = json.load(f)
        except (json.JSONDecodeError, IOError):
            existing = {}

    # Collect all unique articles from all RSS feeds
    all_articles = {}
    for feed_url in RSS_FEEDS:
        xml_data = fetch_url(feed_url, as_json=False)
        if xml_data:
            articles = parse_rss_feed(xml_data)
            for a in articles:
                if a["url"] not in all_articles:
                    all_articles[a["url"]] = a["title"]
        time.sleep(1)

    print(f"  Found {len(all_articles)} unique RSS articles")

    # Generate descriptions for articles not already in lookup
    new_count = 0
    descriptions = {}
    for url, title in all_articles.items():
        if url in existing and existing[url]:
            descriptions[url] = existing[url]
            continue
        # Generate from title (RSS doesn't give us content)
        generated = generate_description(title)
        if generated:
            descriptions[url] = generated
            new_count += 1
            print(f"    AI desc: {title[:50]}...")
        time.sleep(1)

    # Save lookup
    with open(lookup_path, "w") as f:
        json.dump(descriptions, f)
    print(f"  OK: {len(descriptions)} descriptions ({new_count} new)")


def main():
    if not API_KEY:
        print("ERROR: GNEWS_API_KEY not set")
        sys.exit(1)

    os.makedirs(DATA_DIR, exist_ok=True)

    for name, config in CATEGORIES.items():
        fetch_category(name, config)
        time.sleep(2)

    # Generate AI descriptions for Google News RSS articles
    fetch_rss_descriptions()

    print("\nDone.")


if __name__ == "__main__":
    main()
