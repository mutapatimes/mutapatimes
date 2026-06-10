#!/usr/bin/env python3
"""Post fresh Zimbabwe articles to relevant subreddits.

Reddit is the single biggest untapped distribution channel for The
Mutapa Times — diaspora users live in r/Zimbabwe, r/Africa,
r/UKVisas, etc. One self-post that hits r/Zimbabwe's home page can
mean 500-3,000 readers; some compound for weeks via Google's "Reddit
results" carousel.

Strategy:
  • Target 1-2 articles per subreddit per run, never the same article
    to multiple subreddits within 24h (auto-mod spam flag).
  • Self-text post (text + link below) — drives 5-10× the engagement
    of a link-only submission.
  • Cap at 3 subreddits per run to stay under Reddit's anti-spam
    velocity threshold.

Credentials required (set as GH Actions secrets, or env vars locally):
  REDDIT_CLIENT_ID
  REDDIT_CLIENT_SECRET
  REDDIT_USERNAME
  REDDIT_PASSWORD
  REDDIT_USER_AGENT   (default: "mutapatimes-bot/0.1 by /u/<username>")

Run:
  python3 scripts/post_reddit.py            # dry-run if no creds
  python3 scripts/post_reddit.py --live     # actually post

Uses only stdlib (no praw dep) so it runs in any CI env without pip.
"""
import base64
import json
import os
import random
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
INDEX_PATH = os.path.join(ROOT, "content", "articles", "index.json")
STATE_PATH = os.path.join(ROOT, "data", ".posted_reddit.json")

CLIENT_ID     = os.environ.get("REDDIT_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("REDDIT_CLIENT_SECRET", "")
USERNAME      = os.environ.get("REDDIT_USERNAME", "")
PASSWORD      = os.environ.get("REDDIT_PASSWORD", "")
USER_AGENT    = os.environ.get(
    "REDDIT_USER_AGENT",
    f"mutapatimes-bot/0.1 by /u/{USERNAME}" if USERNAME else "mutapatimes-bot/0.1",
)

BASE = "https://mutapatimes.com"

# Subreddit → which categories belong there. First match wins.
# Tuned for actual Reddit community rules — r/Zimbabwe is liberal,
# r/Africa wants continent-wide framing, r/UKVisas only wants
# immigration content.
SUBREDDIT_RULES = [
    {
        "name": "Zimbabwe",
        "categories": {"Business", "Policy", "Tech", "Culture", "Sport",
                       "Environment", "Health", "Economy"},
        "title_prefix": "",  # raw headline
    },
    {
        "name": "africa",
        "categories": {"Business", "Policy", "Economy", "Environment"},
        "title_prefix": "Zimbabwe: ",
    },
]
MAX_POSTS_PER_RUN = 3
MIN_GAP_SECONDS_PER_SUBREDDIT = 30 * 60   # ≥30 min between posts to same sub


# ── State ────────────────────────────────────────────────────
def load_state():
    try:
        return json.load(open(STATE_PATH))
    except (IOError, json.JSONDecodeError):
        return {"posted": {}, "last_per_sub": {}}


def save_state(state):
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2, sort_keys=True)


# ── Reddit OAuth ─────────────────────────────────────────────
def get_access_token():
    """Script-app OAuth: client creds + user login = bearer token."""
    auth = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    data = urllib.parse.urlencode({
        "grant_type": "password",
        "username": USERNAME,
        "password": PASSWORD,
    }).encode()
    req = urllib.request.Request(
        "https://www.reddit.com/api/v1/access_token",
        data=data,
        headers={
            "Authorization": f"Basic {auth}",
            "User-Agent": USER_AGENT,
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.load(resp).get("access_token")


def submit(token, subreddit, title, body, url):
    """Submit a self-post (text body, with the article URL at the foot)."""
    full_body = f"{body}\n\n[Read the full briefing on The Mutapa Times]({url})"
    data = urllib.parse.urlencode({
        "sr": subreddit,
        "kind": "self",
        "title": title[:300],
        "text": full_body[:40000],
        "api_type": "json",
        "sendreplies": "true",
    }).encode()
    req = urllib.request.Request(
        "https://oauth.reddit.com/api/submit",
        data=data,
        headers={
            "Authorization": f"bearer {token}",
            "User-Agent": USER_AGENT,
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        body = json.load(resp)
    j = body.get("json", {})
    errors = j.get("errors") or []
    if errors:
        return False, "; ".join(" ".join(map(str, e)) for e in errors)
    return True, j.get("data", {}).get("url", "")


# ── Article picker ───────────────────────────────────────────
def pick_articles(state, want=MAX_POSTS_PER_RUN):
    """Pick fresh articles that haven't been posted to any sub yet.
    Returns list of (subreddit_rule, article_dict)."""
    try:
        entries = json.load(open(INDEX_PATH))
    except (IOError, json.JSONDecodeError):
        return []

    # Newest first
    entries = sorted(
        [e for e in entries if isinstance(e, dict) and e.get("slug")],
        key=lambda e: e.get("date") or "", reverse=True,
    )

    posted_slugs = set(state.get("posted", {}).keys())
    now_ts = time.time()
    last_per_sub = state.get("last_per_sub", {})

    picks = []
    used_slugs = set()
    for e in entries:
        if len(picks) >= want:
            break
        slug = e.get("slug")
        if slug in posted_slugs or slug in used_slugs:
            continue
        cat = (e.get("category") or "").strip()
        for rule in SUBREDDIT_RULES:
            sub = rule["name"]
            if cat not in rule["categories"]:
                continue
            last_post = last_per_sub.get(sub, 0)
            if now_ts - last_post < MIN_GAP_SECONDS_PER_SUBREDDIT:
                continue
            picks.append((rule, e))
            used_slugs.add(slug)
            # Reserve this sub's slot in-run too
            last_per_sub[sub] = now_ts
            break
    return picks


# ── Main ─────────────────────────────────────────────────────
def main():
    live = "--live" in sys.argv
    creds_ok = all([CLIENT_ID, CLIENT_SECRET, USERNAME, PASSWORD])

    print("=== POST TO REDDIT ===")
    print(f"  Mode: {'LIVE' if live and creds_ok else 'DRY-RUN'}")
    if live and not creds_ok:
        print("  WARN: --live requested but credentials missing — staying dry-run")

    state = load_state()
    picks = pick_articles(state)
    if not picks:
        print("  Nothing to post. Done.")
        return

    print(f"  Picked {len(picks)} article(s):")
    for rule, art in picks:
        title = (art.get("title") or "").strip()
        slug = art.get("slug")
        url = f"{BASE}/articles/{slug}.html"
        full_title = f"{rule['title_prefix']}{title}"
        summary = (art.get("summary") or "").strip()
        body = summary if summary else title
        print(f"   → r/{rule['name']}: {full_title[:80]}")

        if not live or not creds_ok:
            continue

        try:
            token = get_access_token()
            ok, info = submit(token, rule["name"], full_title, body, url)
            if ok:
                print(f"      posted: {info}")
                state["posted"][slug] = {
                    "subreddit": rule["name"],
                    "url": info,
                    "ts": int(time.time()),
                }
            else:
                print(f"      FAILED: {info}")
        except (urllib.error.URLError, urllib.error.HTTPError) as e:
            print(f"      network error: {e}")

    if live and creds_ok:
        save_state(state)
    print("\n=== DONE ===")


if __name__ == "__main__":
    main()
