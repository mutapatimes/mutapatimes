#!/usr/bin/env python3
"""Pick the active Feature Story of the Week and write its metadata to
data/feature-story.json.

The active feature is the most recent non-draft article in
content/articles/ with frontmatter `feature_story: true`. Consumers
(js/articles.js, js/main.js, build_static_pages.py) read the JSON and
render the feature card in their respective surfaces.

Also pins the active feature to the top of data/spotlight.json so it
leads the spotlight rail on the home page.

Run after any commit that toggles feature_story in frontmatter.
"""
import glob
import json
import os
import re
from datetime import datetime, timezone

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
ARTICLES_DIR = os.path.join(ROOT, "content", "articles")
OUT_JSON = os.path.join(ROOT, "data", "feature-story.json")
SPOTLIGHT_JSON = os.path.join(ROOT, "data", "spotlight.json")


def parse_fm(path):
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return {}
    fm = {}
    for line in m.group(1).split("\n"):
        idx = line.find(":")
        if idx == -1:
            continue
        key = line[:idx].strip()
        val = line[idx + 1:].strip().strip('"').strip("'")
        fm[key] = val
    return fm


def find_feature():
    candidates = []
    for path in glob.glob(os.path.join(ARTICLES_DIR, "*.md")):
        fm = parse_fm(path)
        if fm.get("feature_story", "").lower() != "true":
            continue
        if fm.get("draft", "").lower() == "true":
            continue
        slug = os.path.splitext(os.path.basename(path))[0]
        candidates.append((fm.get("date", ""), slug, fm))
    if not candidates:
        return None
    candidates.sort(reverse=True)
    _, slug, fm = candidates[0]
    return {
        "slug": slug,
        "title": fm.get("title", ""),
        "summary": fm.get("summary", ""),
        "image": fm.get("image", ""),
        "author": fm.get("author", "The Mutapa Times"),
        "category": fm.get("category", ""),
        "date": fm.get("date", ""),
        "longform": fm.get("longform", "").lower() == "true",
        "read_minutes": fm.get("read_minutes", ""),
        "url": f"/articles/{slug}",
        "spotlight_title": fm.get("spotlight_title", ""),
        "spotlight_image": fm.get("spotlight_image", ""),
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00"),
    }


SPOTLIGHT_CAP = 3  # Always keep the spotlight rail at three stories.


def pin_to_spotlight(feature):
    if not feature or not os.path.exists(SPOTLIGHT_JSON):
        return
    try:
        data = json.load(open(SPOTLIGHT_JSON))
    except (IOError, json.JSONDecodeError):
        return
    feature_url_query = f"article.html?slug={feature['slug']}"
    # If alternate spotlight title/image are set on the article, use them
    # so the rail doesn't visually duplicate the Feature Story banner.
    feature_entry = {
        "title": feature.get("spotlight_title") or feature["title"],
        "description": feature["summary"],
        "url": feature_url_query,
        "image": feature.get("spotlight_image") or feature["image"],
        "publishedAt": feature["date"],
        "source": "The Mutapa Times",
        "cms": True,
        "feature_story": True,
    }
    for bucket in ("articles", "more"):
        items = data.get(bucket) or []
        items = [e for e in items if not (isinstance(e, dict) and feature_url_query in str(e.get("url", "")))]
        if bucket == "articles":
            items = [feature_entry] + items
            # Hard-cap the visible spotlight rail at three stories. The
            # rest move into the 'more' bucket so they stay reachable
            # from the news landing pages but don't crowd the top rail.
            overflow = items[SPOTLIGHT_CAP:]
            items = items[:SPOTLIGHT_CAP]
            if overflow:
                data["more"] = overflow + (data.get("more") or [])
        data[bucket] = items
    with open(SPOTLIGHT_JSON, "w") as f:
        json.dump(data, f, separators=(",", ":"))
    print(f"  pinned to top of spotlight.json: {feature['slug']}")
    print(f"  spotlight capped at {SPOTLIGHT_CAP} stories")


def main():
    feature = find_feature()
    if not feature:
        # Write an empty file so downstream consumers know there's no active feature.
        with open(OUT_JSON, "w") as f:
            json.dump({}, f)
        print("No feature_story article found - wrote empty feature-story.json")
        return
    with open(OUT_JSON, "w") as f:
        json.dump(feature, f, indent=2)
    print(f"Active feature: {feature['slug']}")
    print(f"  title: {feature['title']}")
    pin_to_spotlight(feature)


if __name__ == "__main__":
    main()
