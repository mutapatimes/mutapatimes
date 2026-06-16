#!/usr/bin/env python3
"""One-off + repeatable sweep: replace hotlinked major-agency images
(Guardian, Reuters, BBC, etc. — see build_feed_cards.is_rights_risky) in
already-built pages with our own deterministic gradient artwork.

Removes image-rights exposure (PicRights et al.) on existing HTML without a
full rebuild. Zimbabwean / local outlet images are left untouched. Idempotent:
once a page's risky URLs are swapped, re-running is a no-op.

Usage:  python3 scripts/strip_rights_heroes.py
"""
import os
import re
import sys
import glob

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_feed_cards import is_rights_risky  # noqa: E402
from gradient_hero import make_gradient_hero    # noqa: E402

IMG_URL_RE = re.compile(r'https?://[^\s"\'<>]+?\.(?:jpg|jpeg|png|webp)', re.I)

TARGETS = [("articles", "img/articles/auto"), ("news", "img/news/auto")]


def gradient_for(slug, out_dir):
    rel = f"{out_dir}/{slug}.jpg"
    if not os.path.exists(rel):
        os.makedirs(out_dir, exist_ok=True)
        make_gradient_hero(slug, rel)
    return "/" + rel


def sweep():
    pages = swapped = urls = 0
    for d, out_dir in TARGETS:
        for path in glob.glob(os.path.join(d, "*.html")):
            try:
                html = open(path, encoding="utf-8").read()
            except Exception:
                continue
            risky = sorted({u for u in IMG_URL_RE.findall(html) if is_rights_risky(u)})
            if not risky:
                continue
            slug = os.path.splitext(os.path.basename(path))[0]
            local = gradient_for(slug, out_dir)
            new = html
            for u in risky:
                new = new.replace(u, local)
            if new != html:
                open(path, "w", encoding="utf-8").write(new)
                pages += 1
                urls += len(risky)
                swapped += 1
            for u in risky:
                print(f"  {os.path.basename(path)}  <-  {u}")
    print(f"\nDone. {pages} pages updated, {urls} agency URLs replaced with gradient art.")


if __name__ == "__main__":
    sweep()
