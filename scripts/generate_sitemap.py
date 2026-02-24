#!/usr/bin/env python3
"""Auto-generate sitemap.xml for The Mutapa Times."""
import glob
import os
import re
from datetime import datetime, timezone

BASE_URL = "https://www.mutapatimes.com"

STATIC_PAGES = [
    ("", 1.0, "hourly"),
    ("index.html", 1.0, "hourly"),
    ("articles.html", 0.9, "daily"),
    ("people.html", 0.9, "weekly"),
    ("businesses.html", 0.9, "weekly"),
    ("economy.html", 0.8, "daily"),
    ("who.html", 0.4, "yearly"),
    ("what.html", 0.4, "yearly"),
    ("why.html", 0.4, "yearly"),
    ("how.html", 0.4, "yearly"),
    ("terms.html", 0.3, "yearly"),
]


def extract_frontmatter(path):
    """Extract date and slug from a markdown article's frontmatter."""
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return None, None
    fm = m.group(1)
    date_match = re.search(r"^date:\s*['\"]?(\d{4}-\d{2}-\d{2})", fm, re.MULTILINE)
    date_str = date_match.group(1) if date_match else None
    # Slug is the filename without .md
    slug = os.path.splitext(os.path.basename(path))[0]
    return slug, date_str


def generate():
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")
    urls = []

    # Static pages
    for page, priority, freq in STATIC_PAGES:
        loc = f"{BASE_URL}/{page}" if page else f"{BASE_URL}/"
        urls.append(
            f"  <url>\n"
            f"    <loc>{loc}</loc>\n"
            f"    <lastmod>{now}</lastmod>\n"
            f"    <changefreq>{freq}</changefreq>\n"
            f"    <priority>{priority}</priority>\n"
            f"  </url>"
        )

    # CMS articles
    articles_dir = os.path.join(os.path.dirname(__file__), "..", "content", "articles")
    for md_path in sorted(glob.glob(os.path.join(articles_dir, "*.md"))):
        slug, date_str = extract_frontmatter(md_path)
        if not slug or slug == "index":
            continue
        lastmod = date_str or now[:10]
        urls.append(
            f"  <url>\n"
            f"    <loc>{BASE_URL}/article.html?slug={slug}</loc>\n"
            f"    <lastmod>{lastmod}</lastmod>\n"
            f"    <changefreq>weekly</changefreq>\n"
            f"    <priority>0.7</priority>\n"
            f"  </url>"
        )

    sitemap = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(urls)
        + "\n</urlset>\n"
    )

    out = os.path.join(os.path.dirname(__file__), "..", "sitemap.xml")
    with open(out, "w", encoding="utf-8") as f:
        f.write(sitemap)
    print(f"sitemap.xml written with {len(urls)} URLs")


if __name__ == "__main__":
    generate()
