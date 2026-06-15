#!/usr/bin/env python3
"""
Build the Academy 'Reading Room' list.

Reads content/articles/index.json, keeps only original Mutapa Times articles
(source_type == "original", not drafts), newest first, and writes a small
academy/reading.json the academy app fetches. Keeping it small means the
browser never has to download the full 4,000-entry feed.

Run: python3 scripts/build_reading_list.py
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(ROOT, "content", "articles", "index.json")
OUT = os.path.join(ROOT, "academy", "reading.json")
LIMIT = 8


def main():
    try:
        with open(INDEX, "r", encoding="utf-8") as f:
            entries = json.load(f)
    except (IOError, json.JSONDecodeError) as e:
        print("build_reading_list: cannot read index.json:", e)
        return 1

    orig = [
        e for e in entries
        if isinstance(e, dict)
        and e.get("source_type") == "original"
        and e.get("slug") and e.get("title")
        and not e.get("draft")
    ]
    orig.sort(key=lambda e: e.get("date") or "", reverse=True)

    items = []
    for e in orig[:LIMIT]:
        items.append({
            "title": e.get("title", ""),
            "slug": e.get("slug", ""),
            "url": "/articles/" + e.get("slug", "") + ".html",
            "summary": (e.get("summary") or "").strip(),
            "category": e.get("category", ""),
            "date": e.get("date", ""),
        })

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump({"updated": items[0]["date"] if items else "", "articles": items}, f, ensure_ascii=False)
    print("build_reading_list: wrote %d articles to academy/reading.json" % len(items))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
