#!/usr/bin/env python3
"""
Post Mutapa Times headlines to X/Twitter via API v2.
OAuth 1.0a implemented with stdlib only (hmac, hashlib, base64).
Reads data/*.json, deduplicates via data/.tweeted_urls.json, rate-limits to
stay within the free tier (500 tweets/month, 17/day).
"""
import base64
import hashlib
import hmac
import json
import os
import random
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

# ── Configuration ────────────────────────────────────────────
TWITTER_CONSUMER_KEY = os.environ.get("TWITTER_CONSUMER_KEY", "")
TWITTER_CONSUMER_SECRET = os.environ.get("TWITTER_CONSUMER_SECRET", "")
TWITTER_ACCESS_TOKEN = os.environ.get("TWITTER_ACCESS_TOKEN", "")
TWITTER_ACCESS_TOKEN_SECRET = os.environ.get("TWITTER_ACCESS_TOKEN_SECRET", "")

TWITTER_API_URL = "https://api.twitter.com/2/tweets"
DATA_DIR = "data"
TWEETED_URLS_FILE = os.path.join(DATA_DIR, ".tweeted_urls.json")

MAX_TWEETS_PER_RUN = 15     # 15 × 31 = 465, safely under 500/month
MAX_TWEET_LENGTH = 280
SLEEP_BETWEEN_TWEETS = 5    # seconds between posts
CATEGORIES = ["business", "technology", "entertainment", "sports", "science", "health"]


# ── OAuth 1.0a (stdlib only) ────────────────────────────────
def percent_encode(s):
    """RFC 5849 percent-encode (unreserved: A-Za-z0-9 - . _ ~)."""
    return urllib.parse.quote(str(s), safe="")


def generate_nonce():
    """Generate a 32-char random hex nonce."""
    return "%032x" % random.getrandbits(128)


def build_oauth_signature(method, url, params, consumer_secret, token_secret):
    """Build OAuth 1.0a HMAC-SHA1 signature per RFC 5849."""
    sorted_params = sorted(params.items(), key=lambda kv: (kv[0], kv[1]))
    param_string = "&".join(
        f"{percent_encode(k)}={percent_encode(v)}" for k, v in sorted_params
    )
    base_string = "&".join([
        method.upper(),
        percent_encode(url),
        percent_encode(param_string),
    ])
    signing_key = f"{percent_encode(consumer_secret)}&{percent_encode(token_secret)}"
    hashed = hmac.new(
        signing_key.encode("utf-8"),
        base_string.encode("utf-8"),
        hashlib.sha1,
    ).digest()
    return base64.b64encode(hashed).decode("utf-8")


def build_authorization_header(method, url):
    """Build the full OAuth 1.0a Authorization header value."""
    oauth_params = {
        "oauth_consumer_key": TWITTER_CONSUMER_KEY,
        "oauth_nonce": generate_nonce(),
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": str(int(time.time())),
        "oauth_token": TWITTER_ACCESS_TOKEN,
        "oauth_version": "1.0",
    }

    # Parse any query params from URL (none for /2/tweets, but keeps it generic)
    parsed = urllib.parse.urlparse(url)
    query_params = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
    all_params = dict(oauth_params)
    for k, v_list in query_params.items():
        for v in v_list:
            all_params[k] = v

    base_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

    signature = build_oauth_signature(
        method, base_url, all_params,
        TWITTER_CONSUMER_SECRET, TWITTER_ACCESS_TOKEN_SECRET,
    )
    oauth_params["oauth_signature"] = signature

    header_parts = ", ".join(
        f'{percent_encode(k)}="{percent_encode(v)}"'
        for k, v in sorted(oauth_params.items())
    )
    return f"OAuth {header_parts}"


# ── Twitter API client ──────────────────────────────────────
def post_tweet(text):
    """Post a tweet. Returns (success, response_dict)."""
    payload = json.dumps({"text": text}).encode("utf-8")
    auth_header = build_authorization_header("POST", TWITTER_API_URL)

    req = urllib.request.Request(
        TWITTER_API_URL,
        data=payload,
        headers={
            "Authorization": auth_header,
            "Content-Type": "application/json",
            "User-Agent": "MutapaTimes/1.0",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            tweet_id = body.get("data", {}).get("id", "?")
            print(f"    OK: tweet {tweet_id}")
            return True, body
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        print(f"    FAIL ({e.code}): {body[:200]}")
        if e.code == 429:
            print("    Rate limited. Stopping run.")
            return False, {"rate_limited": True}
        if e.code == 403:
            if "oauth1" in body.lower() and "permission" in body.lower():
                print("    App permissions error — Access Token needs Read+Write.")
                print("    Regenerate token after enabling Write in app settings.")
                return False, {"rate_limited": True}  # abort run
            print("    Forbidden (possibly duplicate). Skipping.")
            return False, {"forbidden": True}
        return False, {"error": e.code}
    except Exception as e:
        print(f"    ERROR: {e}")
        return False, {"error": str(e)}


# ── Data loading & dedup tracking ───────────────────────────
def load_tweeted_urls():
    """Load already-tweeted URLs from tracker file."""
    if not os.path.exists(TWEETED_URLS_FILE):
        return {}
    try:
        with open(TWEETED_URLS_FILE) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def save_tweeted_urls(tweeted):
    """Save tweeted URLs tracker. Format: {url: iso_timestamp}."""
    with open(TWEETED_URLS_FILE, "w") as f:
        json.dump(tweeted, f, indent=2)


def prune_old_entries(tweeted, max_age_days=60):
    """Remove entries older than max_age_days to prevent unbounded growth."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=max_age_days)).isoformat()
    pruned = {url: ts for url, ts in tweeted.items() if ts >= cutoff}
    removed = len(tweeted) - len(pruned)
    if removed:
        print(f"  Pruned {removed} old entries from tweet tracker")
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


# ── Tweet formatting ────────────────────────────────────────
def format_tweet(title, url):
    """Format a tweet under 280 chars.

    Twitter's t.co shortener counts any URL as 23 chars.
    Budget ~60 chars overhead -> max 220 chars for headline.
    """
    # Overhead: 2 newlines + emoji + space + 23 (t.co) + 2 newlines
    #   + flag emoji + " via @MutapaTimes #Zimbabwe"
    OVERHEAD = 60
    max_title_len = MAX_TWEET_LENGTH - OVERHEAD

    if len(title) > max_title_len:
        title = title[: max_title_len - 1].rstrip() + "\u2026"

    return (
        f"{title}\n\n"
        f"\U0001f517 {url}\n\n"
        f"\U0001f1ff\U0001f1fc via @MutapaTimes #Zimbabwe"
    )


# ── Main ────────────────────────────────────────────────────
def main():
    missing = []
    if not TWITTER_CONSUMER_KEY:
        missing.append("TWITTER_CONSUMER_KEY")
    if not TWITTER_CONSUMER_SECRET:
        missing.append("TWITTER_CONSUMER_SECRET")
    if not TWITTER_ACCESS_TOKEN:
        missing.append("TWITTER_ACCESS_TOKEN")
    if not TWITTER_ACCESS_TOKEN_SECRET:
        missing.append("TWITTER_ACCESS_TOKEN_SECRET")
    if missing:
        print(f"ERROR: Missing environment variables: {', '.join(missing)}")
        sys.exit(1)

    print("=== POST TWEETS ===")

    # Load dedup tracker
    tweeted = load_tweeted_urls()
    tweeted = prune_old_entries(tweeted)
    print(f"  Tracking {len(tweeted)} previously tweeted URLs")

    # Load all articles
    articles = load_all_articles()
    print(f"  Found {len(articles)} total articles across all sources")

    # Filter to untweeted articles only
    new_articles = [a for a in articles if a["url"] and a["url"] not in tweeted]
    print(f"  {len(new_articles)} new (untweeted) articles")

    if not new_articles:
        print("  No new articles to tweet. Done.")
        save_tweeted_urls(tweeted)
        return

    # Cap at daily limit
    to_tweet = new_articles[:MAX_TWEETS_PER_RUN]
    print(f"  Will tweet up to {len(to_tweet)} articles (cap: {MAX_TWEETS_PER_RUN})")

    # Post tweets
    success_count = 0
    fail_count = 0

    for i, article in enumerate(to_tweet):
        title = article["title"]
        url = article["url"]
        source = article["source"]

        print(f"\n  [{i + 1}/{len(to_tweet)}] ({source}) {title[:70]}...")

        tweet_text = format_tweet(title, url)
        ok, resp = post_tweet(tweet_text)

        if ok:
            success_count += 1
            tweeted[url] = datetime.now(timezone.utc).isoformat()
        else:
            fail_count += 1
            if resp.get("rate_limited"):
                print("  Stopping due to rate limit.")
                break

        # Sleep between tweets
        if i < len(to_tweet) - 1:
            time.sleep(SLEEP_BETWEEN_TWEETS)

    # Save updated tracker
    save_tweeted_urls(tweeted)

    print(f"\n=== DONE: {success_count} tweeted, {fail_count} failed ===")


if __name__ == "__main__":
    main()
