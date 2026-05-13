#!/usr/bin/env python3
"""IndexNow pinger — tells Bing, Yandex, Seznam etc. about new URLs the
moment they're published, so they crawl + index within minutes instead
of waiting for the next sitemap pass (3-7 day lag).

Single shared protocol — one POST per batch is fan-out to every
participating engine. Free, no auth other than a key file at the
domain root.

Usage:
    python3 scripts/indexnow_ping.py URL [URL ...]
    python3 scripts/indexnow_ping.py --since-last       # diff against last ping
    python3 scripts/indexnow_ping.py --all-articles     # one-off bulk pass

Integrates with fetch_news.py — called after every CMS wire import
with the list of newly-added article URLs.
"""
import json
import os
import sys
import urllib.error
import urllib.request

# Site identity — must match the canonical URL of every page we ping
HOST = "www.mutapatimes.com"
KEY = "ea3891e3e6604b75a6ef5d02980194ac"
KEY_LOCATION = f"https://{HOST}/{KEY}.txt"
ENDPOINT = "https://api.indexnow.org/indexnow"

# Max 10,000 URLs per call per the spec; we batch in slices of 100 to
# keep payload sizes sane on cron-quality network connections.
BATCH_SIZE = 100

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
STATE_FILE = os.path.join(ROOT, "data", ".indexnow_pinged.json")


def load_state():
    try:
        return set(json.load(open(STATE_FILE)))
    except (IOError, json.JSONDecodeError):
        return set()


def save_state(state):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(sorted(state), f, separators=(",", ":"))


def ping(urls):
    """POST a batch of URLs to IndexNow. Returns (ok, msg)."""
    payload = json.dumps({
        "host": HOST,
        "key": KEY,
        "keyLocation": KEY_LOCATION,
        "urlList": urls,
    }).encode("utf-8")
    req = urllib.request.Request(
        ENDPOINT,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status in (200, 202), f"HTTP {resp.status}"
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:200]
        return False, f"HTTP {e.code}: {body}"
    except (urllib.error.URLError, OSError) as e:
        return False, f"network error: {e}"


def ping_urls(urls, dedupe_against_state=True):
    """Idempotent pinger — by default skips URLs already pinged in
    past runs so we don't waste IndexNow quota re-announcing the
    same article on every fetch-news cron."""
    state = load_state() if dedupe_against_state else set()
    fresh = [u for u in urls if u and u not in state]
    if not fresh:
        print("  IndexNow: nothing new to ping.")
        return
    pinged = 0
    failed = 0
    for i in range(0, len(fresh), BATCH_SIZE):
        batch = fresh[i:i + BATCH_SIZE]
        ok, msg = ping(batch)
        if ok:
            pinged += len(batch)
            state.update(batch)
        else:
            failed += len(batch)
            print(f"  IndexNow batch FAIL ({msg}) — {len(batch)} URLs not retried")
    save_state(state)
    print(f"  IndexNow: pinged {pinged} URL(s), {failed} failed.")


def collect_all_article_urls():
    """One-off bulk-warm pass: every article + every news landing + every
    top-level page. Useful right after first IndexNow setup."""
    BASE = f"https://{HOST}"
    urls = [
        f"{BASE}/",
        f"{BASE}/articles",
        f"{BASE}/economy",
        f"{BASE}/fx",
        f"{BASE}/jobs",
        f"{BASE}/property",
        f"{BASE}/weather",
        f"{BASE}/about",
        f"{BASE}/subscribe",
        f"{BASE}/advertising",
        f"{BASE}/brand",
        f"{BASE}/terms",
        f"{BASE}/privacy",
    ]
    idx_path = os.path.join(ROOT, "content", "articles", "index.json")
    if os.path.exists(idx_path):
        try:
            entries = json.load(open(idx_path))
        except (IOError, json.JSONDecodeError):
            entries = []
        for e in entries:
            slug = e.get("slug") if isinstance(e, dict) else None
            if slug:
                urls.append(f"{BASE}/articles/{slug}.html")
    return urls


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--all-articles":
        urls = collect_all_article_urls()
        print(f"=== IndexNow bulk-warm: {len(urls)} URLs ===")
        ping_urls(urls, dedupe_against_state=True)
        return
    urls = [a for a in sys.argv[1:] if a and not a.startswith("--")]
    if not urls:
        print("Usage: indexnow_ping.py URL [URL ...] | --all-articles")
        sys.exit(0)
    print(f"=== IndexNow: ping {len(urls)} URL(s) ===")
    ping_urls(urls)


if __name__ == "__main__":
    main()
