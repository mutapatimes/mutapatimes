#!/usr/bin/env python3
"""
Fetch Zimbabwe news from Google News RSS for all categories.
Replaces GNews API (unreliable free tier) with free, unlimited RSS.
Optionally generates AI descriptions via Gemini free tier.
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

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
GNEWS_API_KEY = os.environ.get("GNEWS_API_KEY", "")
DATA_DIR = "data"

# Category-specific Google News RSS feeds (replace GNews API)
CATEGORIES = {
    "business": [
        "https://news.google.com/rss/search?q=Zimbabwe+business+OR+Zimbabwe+economy+OR+Zimbabwe+finance&hl=en&gl=US&ceid=US:en",
    ],
    "technology": [
        "https://news.google.com/rss/search?q=Zimbabwe+technology+OR+Zimbabwe+tech+OR+Zimbabwe+digital&hl=en&gl=US&ceid=US:en",
    ],
    "entertainment": [
        "https://news.google.com/rss/search?q=Zimbabwe+entertainment+OR+Zimbabwe+music+OR+Zimbabwe+arts+OR+Zimbabwe+culture&hl=en&gl=US&ceid=US:en",
    ],
    "sports": [
        "https://news.google.com/rss/search?q=Zimbabwe+sports+OR+Zimbabwe+cricket+OR+Zimbabwe+football+OR+Zimbabwe+rugby&hl=en&gl=US&ceid=US:en",
    ],
    "science": [
        "https://news.google.com/rss/search?q=Zimbabwe+science+OR+Zimbabwe+research+OR+Zimbabwe+environment+OR+Zimbabwe+wildlife&hl=en&gl=US&ceid=US:en",
    ],
    "health": [
        "https://news.google.com/rss/search?q=Zimbabwe+health+OR+Zimbabwe+medical+OR+Zimbabwe+hospital&hl=en&gl=US&ceid=US:en",
    ],
}

# All RSS feeds for description generation (same as config.js)
ALL_RSS_FEEDS = [
    "https://news.google.com/rss/search?q=Zimbabwe&hl=en&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=Zimbabwe+news+today&hl=en&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=Harare+OR+Bulawayo+OR+Mutare&hl=en&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=Zimbabwe+politics+government+economy&hl=en&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=site:zimlive.com+OR+site:newsday.co.zw+OR+site:herald.co.zw+OR+site:bulawayo24.com+OR+site:263chat.com&hl=en&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=site:pindula.co.zw+OR+site:nehanda+radio+OR+site:newzimbabwe.com+OR+site:thezimbabwemail.com&hl=en&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=Zimbabwe+local+news&hl=en&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=Zimbabwe+business+sports+entertainment+health&hl=en&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=Harare+Bulawayo+Gweru+Masvingo+Mutare+Chitungwiza&hl=en&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=Zimbabwe+site:bbc.com+OR+site:reuters.com+OR+site:nytimes.com+OR+site:theguardian.com+OR+site:aljazeera.com+OR+site:ft.com+OR+site:economist.com+OR+site:bloomberg.com+OR+site:apnews.com&hl=en&gl=US&ceid=US:en",
]

MAX_NEW_DESCRIPTIONS = 10  # Cap per run to stay within Gemini free-tier rate limits


def fetch_url(url):
    """Fetch raw bytes from URL."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "MutapaTimes/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read()
    except Exception as e:
        print(f"    fetch error: {e}")
        return None


def parse_rss_feed(xml_bytes):
    """Parse Google News RSS XML into article dicts matching GNews format."""
    articles = []
    try:
        root = ET.fromstring(xml_bytes)
        for item in root.iter("item"):
            title_el = item.find("title")
            link_el = item.find("link")
            pub_el = item.find("pubDate")
            if title_el is None or link_el is None:
                continue

            raw_title = title_el.text or ""
            # Google News format: "Headline - Source Name"
            parts = raw_title.rsplit(" - ", 1)
            headline = parts[0].strip()
            source_name = parts[1].strip() if len(parts) > 1 else ""
            url = (link_el.text or "").strip()
            pub_date = (pub_el.text or "").strip() if pub_el is not None else ""

            if headline and url:
                articles.append({
                    "title": headline,
                    "url": url,
                    "description": "",
                    "publishedAt": pub_date,
                    "source": {"name": source_name, "url": ""},
                })
    except ET.ParseError as e:
        print(f"    XML parse error: {e}")
    return articles


def deduplicate(articles, limit=10):
    """Deduplicate by URL, sort by date descending, return top N."""
    seen = set()
    unique = []
    for a in articles:
        url = a.get("url", "")
        if url and url not in seen:
            seen.add(url)
            unique.append(a)
    unique.sort(key=lambda a: a.get("publishedAt", ""), reverse=True)
    return unique[:limit]


def generate_description(title, content=""):
    """Generate a 1-2 sentence summary using Gemini free tier with rate limiting."""
    if not GEMINI_API_KEY:
        return ""

    source_text = content[:1500] if content else title
    prompt = (
        "You are a Financial Times sub-editor writing a brief for the digest. "
        "Paraphrase the headline below into a 1-2 sentence summary (under 200 characters). "
        "Tone: authoritative, concise, matter-of-fact. No editorialising. "
        "Preserve the core meaning — do not add, speculate, or omit key facts. "
        "Do not start with 'This article' or 'The article'. "
        "Just state what happened or what is happening.\n\n"
        f"Headline: {title}\n"
        f"Context: {source_text}"
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
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            text = result["candidates"][0]["content"]["parts"][0]["text"].strip()
            text = text.strip('"\'')
            # Rate limit: wait 5s between calls (free tier ~15 RPM)
            time.sleep(5)
            return text[:250] if len(text) > 250 else text
    except urllib.error.HTTPError as e:
        if e.code == 429:
            # Don't retry — just skip this article and slow down for the next one
            print(f"    Rate limited, skipping: {title[:50]}")
            time.sleep(10)
        else:
            print(f"    Gemini error: {e}")
    except Exception as e:
        print(f"    Gemini error: {e}")
    return ""


def fetch_category(name, feed_urls):
    """Fetch Zimbabwe articles for a category via Google News RSS."""
    print(f"\n=== {name.upper()} ===")

    all_articles = []
    for feed_url in feed_urls:
        xml_data = fetch_url(feed_url)
        if xml_data:
            all_articles.extend(parse_rss_feed(xml_data))

    if not all_articles:
        print(f"  FAIL: {name} — no articles found")
        # Write empty so file exists
        outpath = os.path.join(DATA_DIR, f"{name}.json")
        with open(outpath, "w") as f:
            json.dump({"articles": []}, f)
        return False

    articles = deduplicate(all_articles)

    outpath = os.path.join(DATA_DIR, f"{name}.json")
    with open(outpath, "w") as f:
        json.dump({"articles": articles}, f)
    print(f"  OK: {name} — {len(articles)} articles saved")
    return True


def fetch_rss_descriptions():
    """Generate AI descriptions for main/sidebar RSS articles."""
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

    # Collect unique articles from all RSS feeds
    all_articles = {}
    for feed_url in ALL_RSS_FEEDS:
        xml_data = fetch_url(feed_url)
        if xml_data:
            for a in parse_rss_feed(xml_data):
                if a["url"] not in all_articles:
                    all_articles[a["url"]] = a["title"]

    print(f"  Found {len(all_articles)} unique RSS articles")

    # Generate descriptions for new articles (capped)
    new_count = 0
    descriptions = {}
    for url, title in all_articles.items():
        if url in existing and existing[url]:
            descriptions[url] = existing[url]
            continue
        if new_count >= MAX_NEW_DESCRIPTIONS:
            continue
        generated = generate_description(title)
        if generated:
            descriptions[url] = generated
            new_count += 1
            print(f"    AI desc: {title[:50]}...")

    with open(lookup_path, "w") as f:
        json.dump(descriptions, f)
    print(f"  OK: {len(descriptions)} descriptions ({new_count} new)")


def fetch_spotlight():
    """Fetch spotlight articles from GNews API — reputable western sources only."""
    print("\n=== SPOTLIGHT ===")
    if not GNEWS_API_KEY:
        print("  SKIP: GNEWS_API_KEY not set")
        return

    # Reputable source domains to filter for
    reputable_domains = [
        # Major international
        "bbc.com", "bbc.co.uk", "reuters.com", "nytimes.com",
        "theguardian.com", "aljazeera.com", "ft.com", "economist.com",
        "bloomberg.com", "apnews.com", "washingtonpost.com", "cnn.com",
        "news.sky.com", "telegraph.co.uk", "independent.co.uk",
        "france24.com", "dw.com", "npr.org", "pbs.org", "abcnews.go.com",
        "time.com", "foreignpolicy.com", "theconversation.com",
        # International with Africa desks
        "voanews.com", "rfi.fr", "africanews.com",
        # Reputable African outlets
        "allafrica.com", "dailymaverick.co.za", "mg.co.za",
        "news24.com", "theeastafrican.co.ke", "sabc.co.za",
        "nation.africa", "citizen.co.za", "ewn.co.za",
        "iol.co.za", "timeslive.co.za",
    ]

    # Multiple queries to cast a wider net for reputable sources
    queries = [
        "Zimbabwe",
        "Zimbabwe OR %22Southern Africa%22 OR SADC",
    ]
    articles = []
    for q in queries:
        url = (
            f"https://gnews.io/api/v4/search?q={q}&lang=en&max=20"
            f"&apikey={GNEWS_API_KEY}"
        )
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "MutapaTimes/1.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            articles.extend(data.get("articles", []))
            print(f"  Fetched {len(data.get('articles', []))} articles for query: {q}")
        except Exception as e:
            print(f"  WARN: GNews query '{q}' failed: {e}")

    if not articles:
        print("  FAIL: no articles returned from any query")
        return

    # Build new candidates — prefer reputable sources, then any source
    reputable = []
    others = []
    for a in articles:
        item = {
            "title": a.get("title", ""),
            "description": a.get("description", ""),
            "url": a.get("url", ""),
            "image": a.get("image", ""),
            "publishedAt": a.get("publishedAt", ""),
            "source": a.get("source", {}).get("name", ""),
        }
        source_url = a.get("source", {}).get("url", "")
        if any(d in source_url for d in reputable_domains):
            reputable.append(item)
        else:
            others.append(item)

    new_articles = reputable + others

    # Load existing spotlight to preserve stories that are still fresh
    outpath = os.path.join(DATA_DIR, "spotlight.json")
    existing = []
    if os.path.exists(outpath):
        try:
            with open(outpath) as f:
                existing = json.load(f).get("articles", [])
        except (json.JSONDecodeError, IOError):
            existing = []

    # Merge: new articles first, then existing ones (deduped by URL)
    seen_urls = set()
    merged = []
    for a in new_articles + existing:
        url = a.get("url", "")
        if url in seen_urls:
            continue
        seen_urls.add(url)
        # Drop articles older than spotlight max age (30 days — reputable sources only)
        pub = a.get("publishedAt", "")
        if pub:
            try:
                from datetime import datetime, timezone
                dt = datetime.fromisoformat(pub.replace("Z", "+00:00"))
                age_days = (datetime.now(timezone.utc) - dt).days
                if age_days > 30:
                    continue
            except Exception:
                pass
        merged.append(a)

    # Sort by date (newest first), prefer reputable sources only
    merged.sort(key=lambda a: a.get("publishedAt", ""), reverse=True)
    reputable_kw = [
        "bbc", "reuters", "nytimes", "new york times", "guardian", "al jazeera",
        "bloomberg", "ap news", "associated press", "financial times", "economist",
        "cnn", "washington post", "sky news", "france 24", "dw", "deutsche welle",
        "npr", "pbs", "abc news", "time magazine", "foreign policy", "the conversation",
        "voa", "voice of america", "rfi", "africanews",
        "allafrica", "daily maverick", "mail & guardian", "news24", "the east african",
        "sabc", "nation africa", "the citizen", "eyewitness news", "iol", "timeslive",
        "sunday times",
    ]
    reputable_merged = [a for a in merged if any(d in a.get("source", "").lower() for d in reputable_kw)]
    others_merged = [a for a in merged if a not in reputable_merged]
    # Reputable sources only — no fallback to unvetted sources
    spotlight = reputable_merged[:3]

    if not spotlight:
        print("  WARN: no articles found in results")

    with open(outpath, "w") as f:
        json.dump({"articles": spotlight}, f)
    print(f"  OK: {len(spotlight)} spotlight articles saved (merged from {len(articles)} new + {len(existing)} existing)")


def main():
    os.makedirs(DATA_DIR, exist_ok=True)

    # Fetch category articles from Google News RSS
    for name, feeds in CATEGORIES.items():
        fetch_category(name, feeds)

    # Fetch spotlight articles from GNews API (1 call, includes images + descriptions)
    fetch_spotlight()

    print("\nDone.")


if __name__ == "__main__":
    main()
