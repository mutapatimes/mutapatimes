#!/usr/bin/env python3
"""Rewrite the `Sitemap:` block of robots.txt from regions.py.

Every region with `indexable: True` contributes its sitemap + news-sitemap. A
pre-launch edition (indexable: False) is omitted, so it stays unlisted until
go-live — at which point flipping the flag adds its lines automatically, with no
hand edit. The rest of robots.txt is preserved verbatim.

Run this only in the Zimbabwe (root) workflow: robots.txt is a shared root file,
so keeping it off the per-region matrix avoids commit races.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from regions import (  # noqa: E402
    BASE_URL, all_region_codes, region_path_prefix, region_is_indexable,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROBOTS = os.path.join(ROOT, "robots.txt")


def sitemap_block():
    lines = []
    for code in all_region_codes():
        if not region_is_indexable(code):
            continue
        pfx = region_path_prefix(code)
        lines.append(f"Sitemap: {BASE_URL}{pfx}/sitemap.xml")
        lines.append(f"Sitemap: {BASE_URL}{pfx}/news-sitemap.xml")
    return "\n".join(lines)


def main():
    s = open(ROBOTS, encoding="utf-8").read()
    block = sitemap_block()
    # Replace the first contiguous run of `Sitemap:` lines with the generated
    # block (preserving surrounding blank lines / other directives).
    new = re.sub(r"(?:^Sitemap:.*\n?)+", block + "\n", s, count=1, flags=re.M)
    if new != s:
        open(ROBOTS, "w", encoding="utf-8").write(new)
    print("robots.txt sitemaps:\n" + block)


if __name__ == "__main__":
    main()
