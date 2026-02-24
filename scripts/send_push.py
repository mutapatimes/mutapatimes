#!/usr/bin/env python3
"""Send FCM push notification for breaking/spotlight news.

Called by the fetch-news GitHub Action after updating spotlight.json.
Requires FIREBASE_SERVER_KEY and FIREBASE_PROJECT_ID secrets.
"""
import json
import os
import urllib.request
import urllib.error
from datetime import datetime, timezone

FIREBASE_SERVER_KEY = os.environ.get("FIREBASE_SERVER_KEY", "")
FIREBASE_PROJECT_ID = os.environ.get("FIREBASE_PROJECT_ID", "")
SPOTLIGHT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "spotlight.json")
MAX_AGE_HOURS = 3  # Match the cron interval


def _parse_date(s):
    """Try to parse an ISO-ish date string."""
    if not s:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(s.strip(), fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    return None


def get_tokens_from_firestore():
    """Read push tokens from Firestore REST API."""
    if not FIREBASE_PROJECT_ID:
        print("No FIREBASE_PROJECT_ID set, skipping push.")
        return []
    url = (
        f"https://firestore.googleapis.com/v1/projects/{FIREBASE_PROJECT_ID}"
        f"/databases/(default)/documents/push_tokens?pageSize=500"
    )
    try:
        req = urllib.request.Request(url)
        resp = urllib.request.urlopen(req, timeout=15)
        data = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, json.JSONDecodeError) as e:
        print(f"Failed to read Firestore: {e}")
        return []
    tokens = []
    for doc in data.get("documents", []):
        fields = doc.get("fields", {})
        token = fields.get("token", {}).get("stringValue", "")
        if token:
            tokens.append(token)
    return tokens


def send_push(title, body, url, tokens):
    """Send FCM push to a list of tokens."""
    if not FIREBASE_SERVER_KEY:
        print("No FIREBASE_SERVER_KEY set, skipping push.")
        return
    sent = 0
    for token in tokens:
        payload = json.dumps({
            "to": token,
            "notification": {
                "title": title,
                "body": body,
                "icon": "https://www.mutapatimes.com/img/android-icon-192x192.png",
            },
            "data": {"url": url},
        }).encode("utf-8")
        req = urllib.request.Request(
            "https://fcm.googleapis.com/fcm/send",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": "key=" + FIREBASE_SERVER_KEY,
            },
        )
        try:
            resp = urllib.request.urlopen(req, timeout=10)
            result = json.loads(resp.read().decode("utf-8"))
            if result.get("success", 0) > 0:
                sent += 1
        except (urllib.error.URLError, json.JSONDecodeError) as e:
            print(f"Failed to send to token: {e}")
    print(f"Push sent to {sent}/{len(tokens)} devices")


def main():
    if not os.path.exists(SPOTLIGHT_PATH):
        print("No spotlight.json found, skipping push.")
        return

    with open(SPOTLIGHT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    articles = data.get("articles", [])
    if not articles:
        print("No spotlight articles, skipping push.")
        return

    top = articles[0]
    pub_date = _parse_date(
        top.get("publishedAt") or top.get("published_at") or top.get("date", "")
    )
    now = datetime.now(timezone.utc)

    if pub_date and (now - pub_date).total_seconds() > MAX_AGE_HOURS * 3600:
        print(f"Top article too old ({pub_date}), skipping push.")
        return

    tokens = get_tokens_from_firestore()
    if not tokens:
        print("No push tokens found, skipping.")
        return

    title_text = top.get("title", "Breaking News")[:80]
    body_text = top.get("description", "")[:150]
    article_url = top.get("url", "https://www.mutapatimes.com/")

    send_push(
        title=f"Breaking: {title_text}",
        body=body_text,
        url=article_url,
        tokens=tokens,
    )


if __name__ == "__main__":
    main()
