#!/usr/bin/env python3
"""Stamp cache-busting version strings onto our shared front-end assets.

The iOS app and the website both load /js/nav.js and /css/main.css. Cloudflare
serves them with a long browser-cache TTL, so edits used to take hours to show
up. This stamps every HTML page's reference to those assets with a short hash
of the asset's *current contents* (e.g. nav.js?v=ab12cd34). When the file
changes, the hash changes, the URL changes, and every browser/web-view fetches
the new copy immediately. When the file is unchanged the hash is identical, so
re-running is a no-op (no churn).

Run it as the final step of any build (after the generators have written HTML).

Usage:  python3 scripts/stamp_assets.py
"""
import os
import re
import sys
import json
import hashlib
import glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_FILE = os.path.join(ROOT, "data", "asset-versions.json")

# asset path (relative to repo root)  ->  reference substring used in HTML
ASSETS = {
    "js/nav.js": "js/nav.js",
    "css/main.css": "css/main.css",
    # region.js is generated from regions.py; content-hash it so adding a region
    # (which changes the file) auto-busts the cache and never misroutes /xx.
    "js/region.js": "js/region.js",
    "js/stories.js": "js/stories.js",
}

SKIP_DIRS = ("node_modules", ".git", "ios", "android")


def short_hash(path):
    try:
        with open(os.path.join(ROOT, path), "rb") as f:
            return hashlib.md5(f.read()).hexdigest()[:8]
    except OSError:
        return None


def build_patterns(versions):
    pats = []
    for ref, ver in versions.items():
        # match  .../js/nav.js  optionally followed by ?v=xxxx, capturing the
        # leading path so relative ("../js/nav.js") and absolute ("/js/nav.js")
        # references are both handled.
        rx = re.compile(r'((?:[^"\'\s=()]*?)' + re.escape(ref) + r')(\?v=[0-9a-zA-Z]+)?')
        pats.append((rx, "?v=" + ver))
    return pats


def main():
    versions = {}
    for path in ASSETS:
        h = short_hash(path)
        if not h:
            print(f"  !! missing asset {path}, skipping")
            continue
        versions[ASSETS[path]] = h
    if not versions:
        print("No assets to stamp.")
        return
    print("Asset versions:", ", ".join(f"{k}={v}" for k, v in versions.items()))

    # This script is the unconditional last step of four different CI
    # workflows (fetch-news, fetch-news-regions, rebuild-articles,
    # rebuild-microsites), each running many times a day. A full walk over
    # every HTML file in the repo (30,000+, growing) took 3+ minutes locally
    # and was silently eating most of each workflow's timeout budget on CI's
    # slower runners -- rebuild-microsites was getting killed by its 10-minute
    # timeout on every single run before it ever reached the commit step.
    # Since the substitution is a guaranteed no-op whenever these hashes
    # haven't changed since the last run, skip the walk entirely in that case.
    try:
        with open(CACHE_FILE) as f:
            cached = json.load(f)
    except (OSError, ValueError):
        cached = None
    if cached == versions:
        print("Asset versions unchanged since last run -- nothing to stamp.")
        return

    pats = build_patterns(versions)

    changed = scanned = 0
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if not fn.endswith(".html"):
                continue
            fp = os.path.join(dirpath, fn)
            scanned += 1
            try:
                html = open(fp, encoding="utf-8").read()
            except OSError:
                continue
            new = html
            for rx, repl in pats:
                new = rx.sub(lambda m: m.group(1) + repl, new)
            if new != html:
                open(fp, "w", encoding="utf-8").write(new)
                changed += 1
    print(f"Done. Scanned {scanned} HTML files, stamped {changed}.")

    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    with open(CACHE_FILE, "w") as f:
        json.dump(versions, f, indent=2)


if __name__ == "__main__":
    main()
