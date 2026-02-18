#!/usr/bin/env python3
"""
Fetch news from GNews API for all categories.
Targets western media: US, UK, AU, CA top-headlines merged + search fallback.
"""
import json
import os
import sys
import time
import urllib.request
import urllib.error
import urllib.parse

API_KEY = os.environ.get("GNEWS_API_KEY", "")
DATA_DIR = "data"

CATEGORIES = {
    "business":      {"topic": "business",      "query": "business OR economy OR finance OR markets"},
    "technology":    {"topic": "technology",     "query": "technology OR AI OR software OR startups"},
    "entertainment": {"topic": "entertainment",  "query": "entertainment OR movies OR music OR celebrity"},
    "sports":        {"topic": "sports",         "query": "sports OR football OR basketball OR tennis"},
    "science":       {"topic": "science",        "query": "science OR research OR space OR climate"},
    "health":        {"topic": "health",         "query": "health OR medical OR disease OR WHO"},
}

COUNTRIES = ["us", "gb", "au", "ca"]


def fetch_url(url):
    """Fetch JSON from URL, return parsed dict or None."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "MutapaTimes/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"    fetch error: {e}")
        return None


def fetch_headlines(topic, country):
    """Fetch top-headlines for a topic from a specific country."""
    url = (
        f"https://gnews.io/api/v4/top-headlines"
        f"?topic={topic}&apikey={API_KEY}&lang=en&country={country}&max=10&nullable=image"
    )
    return fetch_url(url)


def fetch_search(query):
    """Fetch via search endpoint (global English)."""
    encoded_q = urllib.parse.quote(query)
    url = (
        f"https://gnews.io/api/v4/search"
        f"?q={encoded_q}&apikey={API_KEY}&lang=en&max=10&sortby=publishedAt&nullable=image"
    )
    return fetch_url(url)


def merge_articles(all_articles):
    """Deduplicate by URL, sort by date descending, return top 10."""
    seen = set()
    unique = []
    for a in all_articles:
        url = a.get("url", "")
        if url and url not in seen:
            seen.add(url)
            unique.append(a)
    unique.sort(key=lambda a: a.get("publishedAt", ""), reverse=True)
    return unique[:10]


def fetch_category(name, config):
    """Fetch articles for a category from multiple western countries."""
    print(f"\n=== {name.upper()} ===")
    all_articles = []

    # Try top-headlines from each western country
    for country in COUNTRIES:
        print(f"  Fetching top-headlines country={country}...")
        data = fetch_headlines(config["topic"], country)
        if data and data.get("articles"):
            count = len(data["articles"])
            all_articles.extend(data["articles"])
            print(f"    got {count} articles")
        else:
            print(f"    no articles")
        time.sleep(1)

    if all_articles:
        merged = merge_articles(all_articles)
        output = {"articles": merged}
        outpath = os.path.join(DATA_DIR, f"{name}.json")
        with open(outpath, "w") as f:
            json.dump(output, f)
        print(f"  OK: {name} — {len(merged)} articles saved (from {len(all_articles)} total)")
        return True

    # Fallback: search endpoint
    print(f"  Trying search fallback...")
    data = fetch_search(config["query"])
    if data and data.get("articles"):
        output = {"articles": data["articles"][:10]}
        outpath = os.path.join(DATA_DIR, f"{name}.json")
        with open(outpath, "w") as f:
            json.dump(output, f)
        print(f"  OK: {name} — {len(output['articles'])} articles (search fallback)")
        return True

    print(f"  FAIL: {name} — no articles found")
    return False


def main():
    if not API_KEY:
        print("ERROR: GNEWS_API_KEY not set")
        sys.exit(1)

    os.makedirs(DATA_DIR, exist_ok=True)

    for name, config in CATEGORIES.items():
        fetch_category(name, config)
        time.sleep(2)

    print("\nDone.")


if __name__ == "__main__":
    main()
