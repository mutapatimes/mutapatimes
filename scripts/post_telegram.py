#!/usr/bin/env python3
"""
Post Mutapa Times headlines to a Telegram channel via Bot API.
Reads data/*.json, deduplicates via data/.posted_telegram.json, posts new
headlines with clickable links. Stdlib only — no pip dependencies.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

# ── Configuration ────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID", "")

TELEGRAM_API = "https://api.telegram.org"
DATA_DIR = "data"
POSTED_FILE = os.path.join(DATA_DIR, ".posted_telegram.json")

MAX_POSTS_PER_RUN = 30
MAX_MESSAGE_LENGTH = 4096  # Telegram message limit
SLEEP_BETWEEN_POSTS = 2  # seconds (Telegram allows ~20 msg/min to same chat)
CATEGORIES = ["business", "technology", "entertainment", "sports", "science", "health"]

# Category emoji map for visual distinction
CATEGORY_EMOJI = {
    "spotlight": "\U0001f4a5",   # 💥
    "business": "\U0001f4b0",    # 💰
    "technology": "\U0001f4bb",  # 💻
    "entertainment": "\U0001f3ac",  # 🎬
    "sports": "\u26bd",          # ⚽
    "science": "\U0001f52c",     # 🔬
    "health": "\U0001f3e5",      # 🏥
}


# ── Telegram API client ─────────────────────────────────────
def telegram_request(method, params):
    """Make a request to the Telegram Bot API. Returns (success, response)."""
    url = f"{TELEGRAM_API}/bot{TELEGRAM_BOT_TOKEN}/{method}"
    data = json.dumps(params).encode("utf-8")
    headers = {"Content-Type": "application/json"}

    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            return True, body
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8")
        try:
            err = json.loads(raw)
        except json.JSONDecodeError:
            err = {"description": raw[:200]}
        return False, {"http_code": e.code, **err}
    except Exception as e:
        return False, {"description": str(e)}


def send_message(chat_id, text, parse_mode="HTML", disable_preview=False):
    """Send a message to a Telegram chat/channel."""
    params = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
    }
    if disable_preview:
        params["disable_web_page_preview"] = True

    ok, resp = telegram_request("sendMessage", params)

    if ok and resp.get("ok"):
        msg_id = resp.get("result", {}).get("message_id", "?")
        print(f"    OK: message {msg_id}")
        return True, resp

    error_code = resp.get("error_code", resp.get("http_code", "?"))
    description = resp.get("description", "Unknown error")
    print(f"    FAIL ({error_code}): {description[:200]}")

    # Rate limited — Telegram returns retry_after in seconds
    if error_code == 429:
        retry_after = resp.get("parameters", {}).get("retry_after", 30)
        print(f"    Rate limited. Retry after {retry_after}s. Stopping run.")
        return False, {"abort": True}

    # Bot blocked or chat not found
    if error_code in (403, 400):
        print(f"    Bot may not have permission to post to {chat_id}.")
        return False, {"abort": True}

    return False, {"error": error_code}


# ── Message formatting ───────────────────────────────────────
def escape_html(text):
    """Escape HTML special characters for Telegram HTML parse mode."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def format_message(title, url, category):
    """Format a Telegram message with HTML markup.

    Format:
        {emoji} <b>{headline}</b>

        🔗 <a href="{url}">Read more</a>

        🇿🇼 The Mutapa Times
    """
    emoji = CATEGORY_EMOJI.get(category, "\U0001f4f0")  # 📰 default
    safe_title = escape_html(title)

    # Trim title if it would exceed message limit (very unlikely but safe)
    max_title_len = MAX_MESSAGE_LENGTH - 200  # generous overhead for markup
    if len(safe_title) > max_title_len:
        safe_title = safe_title[: max_title_len - 1].rstrip() + "\u2026"

    return (
        f'{emoji} <b>{safe_title}</b>\n\n'
        f'\U0001f517 <a href="{url}">Read more</a>\n\n'
        f'\U0001f1ff\U0001f1fc The Mutapa Times'
    )


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
    if not TELEGRAM_BOT_TOKEN:
        print("ERROR: TELEGRAM_BOT_TOKEN not set")
        sys.exit(1)
    if not TELEGRAM_CHANNEL_ID:
        print("ERROR: TELEGRAM_CHANNEL_ID not set")
        sys.exit(1)

    print("=== POST TO TELEGRAM ===")
    print(f"  Channel: {TELEGRAM_CHANNEL_ID}")

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

        text = format_message(title, url, source)
        ok, resp = send_message(TELEGRAM_CHANNEL_ID, text)

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
