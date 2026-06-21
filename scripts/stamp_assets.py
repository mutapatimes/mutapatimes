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
import hashlib
import glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# asset path (relative to repo root)  ->  reference substring used in HTML
ASSETS = {
    "js/nav.js": "js/nav.js",
    "css/main.css": "css/main.css",
    # region.js is generated from regions.py; content-hash it so adding a region
    # (which changes the file) auto-busts the cache and never misroutes /xx.
    "js/region.js": "js/region.js",
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


if __name__ == "__main__":
    main()
