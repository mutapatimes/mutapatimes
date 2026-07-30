#!/usr/bin/env python3
"""Render a single PRIVATE PREVIEW article to a random, noindex URL.

For sharing a draft with a subject for approval before publishing. Reuses
build_static_pages' longform renderer (markdown_to_html + page chrome) so the
preview looks exactly like a real long read, but:
  - robots = noindex, nofollow
  - lives at a random /preview/<token>.html path (unguessable)
  - is NOT added to content/articles/index.json or the sitemap

To publish for real later: move the body into content/articles/<slug>.md,
set draft:false, drop the preview.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_static_pages as B  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# (source md, random output path). The token is fixed so the shared link is
# stable, but random enough to be unguessable.
PREVIEWS = [
    ("content/previews/dr-rumbi.md", "preview/dr-rumbi-4c1f9a7e30d2.html"),
]


def render(src_rel, out_rel):
    raw = open(os.path.join(ROOT, src_rel), encoding="utf-8").read()
    meta, body = B.parse_frontmatter(raw)
    author_map = B._load_author_map()
    title = meta.get("title", "Untitled")
    summary = meta.get("summary", "")
    author = meta.get("author", "")
    category = meta.get("category", "")
    image = meta.get("image", "")
    image_mobile = meta.get("image_mobile", "").strip()
    date_str = meta.get("date", "")
    read_minutes = meta.get("read_minutes", "")
    hero_credit = meta.get("hero_image_credit", "")
    date_display = B.format_date(date_str)
    body_html = B.markdown_to_html(body)
    canonical = f"{B.BASE_URL}/{out_rel}"
    og_image = meta.get("og_image", "").strip() or image or f"{B.BASE_URL}/img/brand/og-share.png"
    depth = 1  # /preview/x.html is one level deep, like /articles/x.html

    p = []
    p.append(B.page_head(f"{title} | The Mutapa Times (preview)", summary, canonical,
                         "article", og_image, depth=depth, robots="noindex, nofollow", pfx=""))
    p.append(B.page_nav("articles", depth=depth, body_class="longform-page", pfx="", region="zw"))
    p.append('\n  <main>\n    <article class="article-full article-longform">')

    if image:
        if image_mobile:
            hero_media = (f'<picture>'
                          f'<source media="(max-width: 640px)" srcset="{B.esc(image_mobile)}">'
                          f'<img src="{B.esc(image)}" alt="{B.esc(title)}" class="article-longform-hero-img">'
                          f'</picture>')
        else:
            hero_media = f'<img src="{B.esc(image)}" alt="{B.esc(title)}" class="article-longform-hero-img">'
        p.append(f'''
      <header class="article-longform-header">
        <div class="article-longform-hero">
          {hero_media}
          <div class="article-longform-hero-overlay"></div>
          <div class="article-longform-hero-inner">
            <h1 class="article-longform-title">{B.esc(title)}</h1>
            <p class="article-longform-deck">{B.esc(summary)}</p>
            <div class="article-longform-meta">''')
        tag = "Long Read" + ("  ·  " + category if category else "")
        p.append(f'              <span class="article-longform-tag">{B.esc(tag)}</span>')
        if author:
            p.append(f'              <span class="article-longform-author">{B._byline_html(author, author_map, depth=depth)}</span>')
        if date_display:
            p.append(f'              <time datetime="{B.esc(date_str)}">{date_display}</time>')
        if read_minutes:
            p.append(f'              <span class="article-longform-read">{B.esc(read_minutes)} min read</span>')
        p.append('            </div>')
        if hero_credit:
            p.append(f'            <p class="article-longform-credit">{B.esc(hero_credit)}</p>')
        p.append('          </div>\n        </div>\n      </header>')

    p.append(f'      <div class="article-body article-body-longform">{body_html}</div>')
    p.append(f'      {B.article_share_buttons(title, canonical)}')
    p.append('      <div class="article-back"><a href="../articles.html">&larr; All articles</a></div>')
    p.append('\n    </article>\n  </main>\n')
    p.append(B.page_footer(depth=depth, extra_scripts="", pfx="", region="zw"))

    out_path = os.path.join(ROOT, out_rel)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(p))
    print(f"Wrote /{out_rel}  ->  {canonical}")


def main():
    for src_rel, out_rel in PREVIEWS:
        render(src_rel, out_rel)


if __name__ == "__main__":
    main()
