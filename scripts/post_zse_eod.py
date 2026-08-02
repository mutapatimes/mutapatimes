#!/usr/bin/env python3
"""Post the ZSE end-of-day card to social channels once per trading day.

Reads data/zse-market-activity.json + img/cards/zse/eod-latest.png, builds a
concise caption, and posts the card image to whichever channels have
credentials in the environment:

  Telegram  (TELEGRAM_BOT_TOKEN + TELEGRAM_CHANNEL_ID)   sendPhoto
  Bluesky   (BLUESKY_HANDLE + BLUESKY_APP_PASSWORD)      image embed

Deduplicated by `as_of` via data/.posted_zse_eod.json so re-runs are no-ops.
Always writes data/zse-eod-caption.txt for manual X/LinkedIn posting.
Stdlib only. Missing credentials => that channel is skipped (not an error),
so local runs simply write the caption file.
"""
import json
import os
import sys
import uuid
import mimetypes
import urllib.request
import urllib.error
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "zse-market-activity.json")
CARD = os.path.join(ROOT, "img", "cards", "zse", "eod-latest.png")
POSTED = os.path.join(ROOT, "data", ".posted_zse_eod.json")
CAPTION_OUT = os.path.join(ROOT, "data", "zse-eod-caption.txt")
SITE = "https://mutapatimes.com/zse"

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def nice_date(iso):
    p = (iso or "").split("-")
    return f"{int(p[2])} {MONTHS[int(p[1]) - 1]} {p[0]}" if len(p) == 3 else (iso or "")


def big(n):
    if n is None:
        return "--"
    n = float(n)
    if n >= 1e9:
        return f"ZWG {n / 1e9:.2f}bn"
    if n >= 1e6:
        return f"ZWG {n / 1e6:.2f}m"
    return f"ZWG {n:,.0f}"


def pct(p):
    return "" if p is None else f"{'+' if float(p) > 0 else ''}{float(p):.2f}%"


def all_share(d):
    for x in d.get("indices", []):
        if (x.get("name") or "").upper() == "ALL SHARE":
            return x
    return None


def build_caption(d):
    a = d.get("activity", {})
    as_ = all_share(d) or {}
    g = (d.get("gainers") or [{}])[0]
    l = (d.get("losers") or [{}])[0]
    lines = [
        f"ZSE close · {nice_date(d.get('as_of'))}",
        f"All Share {as_.get('value')} ({pct(as_.get('change_pct'))})",
        f"Turnover {big(a.get('turnover'))} · {a.get('trades')} trades · Mkt cap {big(a.get('market_cap'))}",
    ]
    if g.get("symbol") or g.get("name"):
        lines.append(f"Top gainer {g.get('symbol') or g.get('name')} {pct(g.get('change_pct'))} · "
                     f"top faller {l.get('symbol') or l.get('name')} {pct(l.get('change_pct'))}")
    lines.append(f"Full close: {SITE}")
    return "\n".join(lines)


# ── multipart helper (stdlib) ────────────────────────────────
def _multipart(fields, filefield, filepath):
    boundary = "----mt" + uuid.uuid4().hex
    body = b""
    for k, v in fields.items():
        body += (f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n").encode()
    fname = os.path.basename(filepath)
    ctype = mimetypes.guess_type(filepath)[0] or "application/octet-stream"
    body += (f"--{boundary}\r\nContent-Disposition: form-data; name=\"{filefield}\"; "
             f"filename=\"{fname}\"\r\nContent-Type: {ctype}\r\n\r\n").encode()
    with open(filepath, "rb") as f:
        body += f.read()
    body += f"\r\n--{boundary}--\r\n".encode()
    return body, f"multipart/form-data; boundary={boundary}"


def post_telegram(caption):
    tok = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat = os.environ.get("TELEGRAM_CHANNEL_ID", "").strip()
    if not (tok and chat):
        print("  telegram: skipped (no credentials)")
        return False
    body, ctype = _multipart({"chat_id": chat, "caption": caption}, "photo", CARD)
    req = urllib.request.Request(f"https://api.telegram.org/bot{tok}/sendPhoto",
                                 data=body, headers={"Content-Type": ctype})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            r.read()
        print("  telegram: posted")
        return True
    except urllib.error.HTTPError as e:
        print(f"  telegram: FAILED {e} {e.read()[:200]}")
        return False


def _bsky(base, path, token=None, data=None, ctype="application/json"):
    headers = {"Content-Type": ctype}
    if token:
        headers["Authorization"] = "Bearer " + token
    raw = data if isinstance(data, bytes) else (json.dumps(data).encode() if data else None)
    req = urllib.request.Request(base + path, data=raw, headers=headers,
                                 method="POST" if data is not None else "GET")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def post_bluesky(caption):
    handle = os.environ.get("BLUESKY_HANDLE", "").strip()
    pw = os.environ.get("BLUESKY_APP_PASSWORD", "").strip()
    if not (handle and pw):
        print("  bluesky: skipped (no credentials)")
        return False
    base = "https://bsky.social/xrpc"
    try:
        sess = _bsky(base, "/com.atproto.server.createSession",
                     data={"identifier": handle, "password": pw})
        tok, did = sess["accessJwt"], sess["did"]
        with open(CARD, "rb") as f:
            blob_raw = f.read()
        blob = _bsky(base, "/com.atproto.repo.uploadBlob", token=tok,
                     data=blob_raw, ctype="image/png")["blob"]
        rec = {
            "$type": "app.bsky.feed.post",
            "text": caption[:300],
            "createdAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "embed": {"$type": "app.bsky.embed.images",
                      "images": [{"alt": "ZSE end-of-day summary", "image": blob}]},
        }
        _bsky(base, "/com.atproto.repo.createRecord", token=tok,
              data={"repo": did, "collection": "app.bsky.feed.post", "record": rec})
        print("  bluesky: posted")
        return True
    except (urllib.error.HTTPError, urllib.error.URLError, KeyError) as e:
        print(f"  bluesky: FAILED {e}")
        return False


def main():
    if not os.path.isfile(DATA) or not os.path.isfile(CARD):
        print("ERROR: missing data or card; run fetch_zse_market.py + build_zse_eod_card.py first")
        sys.exit(1)
    with open(DATA, encoding="utf-8") as f:
        d = json.load(f)
    as_of = d.get("as_of", "")
    caption = build_caption(d)
    with open(CAPTION_OUT, "w", encoding="utf-8") as f:
        f.write(caption + "\n")
    print("Caption:\n" + caption + "\n")

    force = "--force" in sys.argv
    posted = {}
    if os.path.isfile(POSTED):
        try:
            posted = json.load(open(POSTED))
        except Exception:
            posted = {}
    if posted.get("as_of") == as_of and not force:
        print(f"Already posted for {as_of}; nothing to do (use --force to repost).")
        return

    ok = any([post_telegram(caption), post_bluesky(caption)])
    if ok:
        with open(POSTED, "w", encoding="utf-8") as f:
            json.dump({"as_of": as_of, "posted_at": datetime.now(timezone.utc).isoformat()}, f)
    else:
        print("No channel posted (no credentials present). Caption file written for manual posting.")


if __name__ == "__main__":
    main()
