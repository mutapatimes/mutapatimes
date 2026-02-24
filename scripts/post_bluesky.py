#!/usr/bin/env python3
"""
Post Mutapa Times headlines to Bluesky via AT Protocol.
Reads data/*.json, deduplicates via data/.posted_bluesky.json, posts new
headlines with clickable links. Stdlib only — no pip dependencies.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

# ── Configuration ────────────────────────────────────────────
BLUESKY_HANDLE = os.environ.get("BLUESKY_HANDLE", "")
BLUESKY_APP_PASSWORD = os.environ.get("BLUESKY_APP_PASSWORD", "")

BSKY_API = "https://bsky.social/xrpc"
DATA_DIR = "data"
POSTED_FILE = os.path.join(DATA_DIR, ".posted_bluesky.json")

MAX_POSTS_PER_RUN = 30
MAX_POST_LENGTH = 300
SLEEP_BETWEEN_POSTS = 2  # seconds
CATEGORIES = ["business", "technology", "entertainment", "sports", "science", "health"]


# ── Bluesky API client ──────────────────────────────────────
def bsky_request(endpoint, payload, token=None):
    """Make a request to the Bluesky XRPC API."""
    url = f"{BSKY_API}/{endpoint}"
    data = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            err = json.loads(body)
        except json.JSONDecodeError:
            err = {"error": body[:200]}
        return e.code, err


def create_session():
    """Authenticate and return (access_jwt, did)."""
    status, resp = bsky_request("com.atproto.server.createSession", {
        "identifier": BLUESKY_HANDLE,
        "password": BLUESKY_APP_PASSWORD,
    })
    if status != 200:
        print(f"  Auth failed ({status}): {resp}")
        return None, None
    return resp.get("accessJwt"), resp.get("did")


def create_post(token, did, text, facets=None):
    """Create a Bluesky post. Returns (success, response)."""
    record = {
        "$type": "app.bsky.feed.post",
        "text": text,
        "createdAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z"),
    }
    if facets:
        record["facets"] = facets

    status, resp = bsky_request("com.atproto.repo.createRecord", {
        "repo": did,
        "collection": "app.bsky.feed.post",
        "record": record,
    }, token=token)

    if status in (200, 201):
        uri = resp.get("uri", "?")
        print(f"    OK: {uri}")
        return True, resp

    print(f"    FAIL ({status}): {json.dumps(resp)[:200]}")
    if status == 429:
        print("    Rate limited. Stopping run.")
        return False, {"abort": True}
    return False, {"error": status}


# ── Post formatting with facets ──────────────────────────────
def build_link_facet(text, link_text, url):
    """Build a Bluesky link facet for link_text within text.

    Bluesky requires UTF-8 byte offsets, not character positions.
    """
    text_bytes = text.encode("utf-8")
    link_bytes = link_text.encode("utf-8")

    # Find the byte offset of the link text
    byte_start = text_bytes.find(link_bytes)
    if byte_start == -1:
        return None
    byte_end = byte_start + len(link_bytes)

    return {
        "index": {"byteStart": byte_start, "byteEnd": byte_end},
        "features": [{"$type": "app.bsky.richtext.facet#link", "uri": url}],
    }


def format_post(title, url):
    """Format a Bluesky post with a clickable link.

    Format:
        {headline}

        🔗 Read more →

        🇿🇼 The Mutapa Times #Zimbabwe

    "Read more →" is a clickable link pointing to the article URL.
    """
    link_text = "Read more \u2192"
    suffix = f"\n\n\U0001f517 {link_text}\n\n\U0001f1ff\U0001f1fc The Mutapa Times #Zimbabwe"

    # Overhead in characters (suffix length)
    overhead = len(suffix)
    max_title_len = MAX_POST_LENGTH - overhead

    if len(title) > max_title_len:
        title = title[: max_title_len - 1].rstrip() + "\u2026"

    # Add UTM tracking to URL
    sep = "?" if "?" not in url else "&"
    tracked_url = f"{url}{sep}utm_source=bluesky&utm_medium=social&utm_campaign=auto_post"

    text = f"{title}{suffix}"
    facet = build_link_facet(text, link_text, tracked_url)
    facets = [facet] if facet else []

    return text, facets


# ── Data loading & dedup tracking ────────────────────────────
def load_posted():
    """Load already-posted URLs from tracker file."""
    if not os.path.exists(POSTED_FILE):
        return {}
    try:
        with open(POSTED_FILE) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def save_posted(posted):
    """Save posted URLs tracker. Format: {url: iso_timestamp}."""
    with open(POSTED_FILE, "w") as f:
        json.dump(posted, f, indent=2)


def prune_old_entries(posted, max_age_days=60):
    """Remove entries older than max_age_days."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=max_age_days)).isoformat()
    pruned = {url: ts for url, ts in posted.items() if ts >= cutoff}
    removed = len(posted) - len(pruned)
    if removed:
        print(f"  Pruned {removed} old entries from post tracker")
    return pruned


def load_all_articles():
    """Load all articles from spotlight + category JSON files."""
    articles = []

    # Spotlight first (highest priority)
    spotlight_path = os.path.join(DATA_DIR, "spotlight.json")
    if os.path.exists(spotlight_path):
        try:
            with open(spotlight_path) as f:
                data = json.load(f)
            for a in data.get("articles", []):
                articles.append({
                    "title": a.get("title", ""),
                    "url": a.get("url", ""),
                    "source": "spotlight",
                })
        except (json.JSONDecodeError, IOError) as e:
            print(f"  WARN: could not load spotlight.json: {e}")

    # Category articles
    for cat in CATEGORIES:
        filepath = os.path.join(DATA_DIR, f"{cat}.json")
        if not os.path.exists(filepath):
            continue
        try:
            with open(filepath) as f:
                data = json.load(f)
            for a in data.get("articles", []):
                articles.append({
                    "title": a.get("title", ""),
                    "url": a.get("url", ""),
                    "source": cat,
                })
        except (json.JSONDecodeError, IOError) as e:
            print(f"  WARN: could not load {cat}.json: {e}")

    return articles


# ── Main ────────────────────────────────────────────────────
def main():
    if not BLUESKY_HANDLE:
        print("ERROR: BLUESKY_HANDLE not set")
        sys.exit(1)
    if not BLUESKY_APP_PASSWORD:
        print("ERROR: BLUESKY_APP_PASSWORD not set")
        sys.exit(1)

    print("=== POST TO BLUESKY ===")

    # Authenticate
    print(f"  Authenticating as {BLUESKY_HANDLE}...")
    token, did = create_session()
    if not token:
        print("  Authentication failed. Check handle and app password.")
        sys.exit(1)
    print(f"  Authenticated (DID: {did[:20]}...)")

    # Load dedup tracker
    posted = load_posted()
    posted = prune_old_entries(posted)
    print(f"  Tracking {len(posted)} previously posted URLs")

    # Load all articles
    articles = load_all_articles()
    print(f"  Found {len(articles)} total articles across all sources")

    # Filter to unposted articles only
    new_articles = [a for a in articles if a["url"] and a["url"] not in posted]
    print(f"  {len(new_articles)} new (unposted) articles")

    if not new_articles:
        print("  No new articles to post. Done.")
        save_posted(posted)
        return

    # Cap per run
    to_post = new_articles[:MAX_POSTS_PER_RUN]
    print(f"  Will post up to {len(to_post)} articles (cap: {MAX_POSTS_PER_RUN})")

    # Post articles
    success_count = 0
    fail_count = 0

    for i, article in enumerate(to_post):
        title = article["title"]
        url = article["url"]
        source = article["source"]

        print(f"\n  [{i + 1}/{len(to_post)}] ({source}) {title[:70]}...")

        text, facets = format_post(title, url)
        ok, resp = create_post(token, did, text, facets)

        if ok:
            success_count += 1
            posted[url] = datetime.now(timezone.utc).isoformat()
        else:
            fail_count += 1
            if resp.get("abort"):
                print("  Aborting run.")
                break

        # Sleep between posts
        if i < len(to_post) - 1:
            time.sleep(SLEEP_BETWEEN_POSTS)

    # Save updated tracker
    save_posted(posted)

    print(f"\n=== DONE: {success_count} posted, {fail_count} failed ===")


if __name__ == "__main__":
    main()
