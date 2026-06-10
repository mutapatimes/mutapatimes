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
SITE_BASE_URL = "https://mutapatimes.com"
DATA_DIR = "data"
POSTED_FILE = os.path.join(DATA_DIR, ".posted_bluesky.json")
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NEWS_DIR = os.path.join(REPO_ROOT, "news")
ARTICLES_DIR = os.path.join(REPO_ROOT, "articles")

MAX_POSTS_PER_RUN = 30
MAX_POST_LENGTH = 300
SLEEP_BETWEEN_POSTS = 2  # seconds
CATEGORIES = ["business", "technology", "entertainment", "sports", "science", "health"]

# Reuse the wire-article slug logic from build_news_pages.py so the share
# URL we post points at the same /news/{slug}.html landing page the
# article was rendered to. Keeps the two scripts authoritative on the
# same slug shape rather than each duplicating slugification.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_news_pages import make_slug as make_news_slug  # noqa: E402


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


def derive_share_url(article, source):
    """Map an article record to its mutapatimes.com landing page URL.

    Returns the canonical https://mutapatimes.com/... URL we want to
    share on Bluesky, or None if no landing page exists on disk (which
    means the article either pre-dates the news-page generator or is too
    old to have a landing page rendered for it). We post the share URL
    instead of the upstream wire URL so social traffic lands on us, not
    on news.google.com or the syndication source.
    """
    raw_url = (article.get("url") or "").strip()
    if not raw_url:
        return None

    # Spotlight (CMS) articles: legacy URL form is "article.html?slug=foo".
    # Canonical landing is /articles/{slug}.html.
    if raw_url.startswith("article.html?slug="):
        slug = raw_url.split("slug=", 1)[1].split("&", 1)[0]
        if os.path.exists(os.path.join(ARTICLES_DIR, f"{slug}.html")):
            return f"{SITE_BASE_URL}/articles/{slug}.html"
        return None

    # Already an absolute mutapatimes URL — pass through.
    if raw_url.startswith(SITE_BASE_URL) or raw_url.startswith("https://mutapatimes.com"):
        return raw_url

    # Wire articles (news.google.com/rss/... or upstream publisher URLs).
    # build_news_pages.py renders a /news/{slug}.html landing for these;
    # only share the URL if that file actually exists, otherwise we'd
    # link to a 404 (e.g. older than MAX_ARTICLE_AGE_DAYS).
    slug = make_news_slug(article)
    if os.path.exists(os.path.join(NEWS_DIR, f"{slug}.html")):
        return f"{SITE_BASE_URL}/news/{slug}.html"
    return None


def load_all_articles():
    """Load all articles from spotlight + category JSON files.

    Each returned record carries both the original wire `url` (used for
    deduplication against past posts in .posted_bluesky.json) and a
    `share_url` (the mutapatimes.com landing page we will actually post).
    """
    articles = []

    def _record(a, source):
        share = derive_share_url(a, source)
        return {
            "title": a.get("title", ""),
            "url": a.get("url", ""),
            "share_url": share,
            "publishedAt": a.get("publishedAt", ""),
            "source": source,
        }

    # Spotlight first (highest priority)
    spotlight_path = os.path.join(DATA_DIR, "spotlight.json")
    if os.path.exists(spotlight_path):
        try:
            with open(spotlight_path) as f:
                data = json.load(f)
            for a in data.get("articles", []):
                articles.append(_record(a, "spotlight"))
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
                articles.append(_record(a, cat))
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

    # An article is postable only if we have a mutapatimes.com landing
    # page for it — otherwise we'd be sharing an empty/404 URL.
    with_landing = [a for a in articles if a["share_url"]]
    print(f"  {len(with_landing)} have a mutapatimes.com landing page "
          f"({len(articles) - len(with_landing)} skipped — no landing yet)")

    # Dedup is on the original wire `url` so the existing .posted_bluesky.json
    # keys (Google News / publisher URLs) stay authoritative across this
    # switch — we don't want to re-post every previously-shared headline
    # just because the share format changed.
    new_articles = [a for a in with_landing if a["url"] and a["url"] not in posted]
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
        url = article["url"]            # wire URL, used as dedup key only
        share_url = article["share_url"]  # what actually gets posted
        source = article["source"]

        print(f"\n  [{i + 1}/{len(to_post)}] ({source}) {title[:70]}...")
        print(f"      sharing: {share_url}")

        text, facets = format_post(title, share_url)
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
