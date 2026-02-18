#!/usr/bin/env python3
"""
Fetch Zimbabwe news from GNews API for all categories.
Everything is Zimbabwe-focused — search endpoint with Zimbabwe keywords.
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
    "business":      {"query": "Zimbabwe business OR Zimbabwe economy OR Zimbabwe finance OR Zimbabwe trade"},
    "technology":    {"query": "Zimbabwe technology OR Zimbabwe tech OR Zimbabwe digital OR Zimbabwe innovation"},
    "entertainment": {"query": "Zimbabwe entertainment OR Zimbabwe music OR Zimbabwe arts OR Zimbabwe culture OR Zimbabwe film"},
    "sports":        {"query": "Zimbabwe sports OR Zimbabwe cricket OR Zimbabwe football OR Zimbabwe rugby OR Zimbabwe athletics"},
    "science":       {"query": "Zimbabwe science OR Zimbabwe research OR Zimbabwe environment OR Zimbabwe wildlife"},
    "health":        {"query": "Zimbabwe health OR Zimbabwe medical OR Zimbabwe hospital OR Zimbabwe disease"},
}


def fetch_url(url):
    """Fetch JSON from URL, return parsed dict or None."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "MutapaTimes/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
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


def fetch_category(name, config):
    """Fetch Zimbabwe articles for a category."""
    print(f"\n=== {name.upper()} ===")

    data = fetch_search(config["query"])
    if data and data.get("articles"):
        articles = deduplicate(data["articles"])
        output = {"articles": articles}
        outpath = os.path.join(DATA_DIR, f"{name}.json")
        with open(outpath, "w") as f:
            json.dump(output, f)
        print(f"  OK: {name} — {len(articles)} articles saved")
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
