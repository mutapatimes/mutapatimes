#!/usr/bin/env python3
"""
Post Mutapa Times headlines to Reddit via OAuth2 API.
Submits link posts to a target subreddit. Uses "script" app type
(headless OAuth2 with username/password grant). Stdlib only — no pip
dependencies. Deduplicates via data/.posted_reddit.json.
"""
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

# ── Configuration ────────────────────────────────────────────
REDDIT_CLIENT_ID = os.environ.get("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.environ.get("REDDIT_CLIENT_SECRET", "")
REDDIT_USERNAME = os.environ.get("REDDIT_USERNAME", "")
REDDIT_PASSWORD = os.environ.get("REDDIT_PASSWORD", "")
REDDIT_SUBREDDIT = os.environ.get("REDDIT_SUBREDDIT", "Zimbabwe")

AUTH_URL = "https://www.reddit.com/api/v1/access_token"
API_BASE = "https://oauth.reddit.com"
USER_AGENT = f"MutapaTimes/1.0 (by /u/{REDDIT_USERNAME})"

DATA_DIR = "data"
POSTED_FILE = os.path.join(DATA_DIR, ".posted_reddit.json")

# Conservative limits — Reddit aggressively flags spam
MAX_POSTS_PER_RUN = 5
SLEEP_BETWEEN_POSTS = 12  # seconds (stay well under rate limits)
CATEGORIES = ["business", "technology", "entertainment", "sports", "science", "health"]


# ── Reddit OAuth2 client ────────────────────────────────────
def get_access_token():
    """Authenticate via OAuth2 password grant. Returns access token or None."""
    credentials = base64.b64encode(
        f"{REDDIT_CLIENT_ID}:{REDDIT_CLIENT_SECRET}".encode()
    ).decode()

    data = urllib.parse.urlencode({
        "grant_type": "password",
        "username": REDDIT_USERNAME,
        "password": REDDIT_PASSWORD,
    }).encode("utf-8")

    req = urllib.request.Request(AUTH_URL, data=data, method="POST")
    req.add_header("Authorization", f"Basic {credentials}")
    req.add_header("User-Agent", USER_AGENT)
    req.add_header("Content-Type", "application/x-www-form-urlencoded")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            token = body.get("access_token")
            if token:
                print(f"  Authenticated as /u/{REDDIT_USERNAME}")
                return token
            print(f"  Auth response missing token: {body}")
            return None
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8")
        print(f"  Auth failed ({e.code}): {raw[:200]}")
        return None
    except Exception as e:
        print(f"  Auth error: {e}")
        return None


def reddit_request(endpoint, params, token):
    """Make a POST request to the Reddit API. Returns (success, response)."""
    url = f"{API_BASE}{endpoint}"
    data = urllib.parse.urlencode(params).encode("utf-8")

    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("User-Agent", USER_AGENT)
    req.add_header("Content-Type", "application/x-www-form-urlencoded")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            return True, body
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8")
        try:
            err = json.loads(raw)
        except json.JSONDecodeError:
            err = {"message": raw[:200]}
        return False, {"http_code": e.code, **err}
    except Exception as e:
        return False, {"message": str(e)}


def submit_link(token, subreddit, title, url):
    """Submit a link post to a subreddit. Returns (success, response)."""
    params = {
        "sr": subreddit,
        "kind": "link",
        "title": title,
        "url": url,
        "resubmit": "false",   # don't repost already-submitted URLs
        "send_replies": "false",
    }

    ok, resp = reddit_request("/api/submit", params, token)

    if ok:
        # Reddit wraps response in jquery callback format or JSON
        # Check for errors in the response
        success = resp.get("success", False)
        errors = []

        # Reddit API v1 returns {"success": true/false, "jquery": [...]}
        # or {"json": {"errors": [...], "data": {...}}}
        json_data = resp.get("json", {})
        errors = json_data.get("errors", [])
        post_data = json_data.get("data", {})

        if errors:
            error_msgs = "; ".join(str(e) for e in errors)
            print(f"    FAIL: {error_msgs[:200]}")

            # Rate limited
            for err in errors:
                if isinstance(err, list) and err[0] == "RATELIMIT":
                    print(f"    Rate limited: {err[1] if len(err) > 1 else 'unknown'}")
                    return False, {"abort": True}
                if isinstance(err, list) and err[0] == "ALREADY_SUB":
                    print("    Already submitted. Marking as posted.")
                    return True, resp  # treat as success for dedup

            return False, {"error": error_msgs}

        post_url = post_data.get("url", "?")
        post_id = post_data.get("id", "?")
        print(f"    OK: {post_url} (id: {post_id})")
        return True, resp

    error_code = resp.get("http_code", "?")
    message = resp.get("message", "Unknown error")
    print(f"    FAIL ({error_code}): {message[:200]}")

    if error_code == 429:
        print("    Rate limited. Stopping run.")
        return False, {"abort": True}
    if error_code == 403:
        print(f"    Forbidden. Check bot permissions for r/{subreddit}.")
        return False, {"abort": True}

    return False, {"error": error_code}


# ── Post title formatting ────────────────────────────────────
def format_title(title):
    """Format a Reddit post title.

    Reddit link posts show the title + linked domain automatically.
    Max title length is 300 characters.
    """
    max_len = 295  # leave a small buffer
    if len(title) > max_len:
        title = title[: max_len - 1].rstrip() + "\u2026"
    return title


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
    missing = []
    if not REDDIT_CLIENT_ID:
        missing.append("REDDIT_CLIENT_ID")
    if not REDDIT_CLIENT_SECRET:
        missing.append("REDDIT_CLIENT_SECRET")
    if not REDDIT_USERNAME:
        missing.append("REDDIT_USERNAME")
    if not REDDIT_PASSWORD:
        missing.append("REDDIT_PASSWORD")
    if missing:
        print(f"ERROR: Missing environment variables: {', '.join(missing)}")
        sys.exit(1)

    print("=== POST TO REDDIT ===")
    print(f"  Subreddit: r/{REDDIT_SUBREDDIT}")

    # Authenticate
    token = get_access_token()
    if not token:
        print("  Authentication failed. Check credentials and app config.")
        sys.exit(1)

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

    # Cap per run (conservative for Reddit)
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

        reddit_title = format_title(title)
        ok, resp = submit_link(token, REDDIT_SUBREDDIT, reddit_title, url)

        if ok:
            success_count += 1
            posted[url] = datetime.now(timezone.utc).isoformat()
        else:
            fail_count += 1
            if resp.get("abort"):
                print("  Aborting run.")
                break

        # Sleep between posts (longer for Reddit to avoid spam flags)
        if i < len(to_post) - 1:
            time.sleep(SLEEP_BETWEEN_POSTS)

    # Save updated tracker
    save_posted(posted)

    print(f"\n=== DONE: {success_count} posted, {fail_count} failed ===")


if __name__ == "__main__":
    main()
