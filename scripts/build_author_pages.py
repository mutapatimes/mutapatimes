#!/usr/bin/env python3
"""
Build static author pages.

Reads content/authors/*.md, scans every article in
content/articles/ + content/wires/, and writes one HTML page per
author at authors/{slug}.html with:
  - hero block (photo or monogram, name, role, bio, beat, social)
  - archive grid of every article the author has written

Run: python3 scripts/build_author_pages.py
"""
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_static_pages import (  # noqa: E402
    ARTICLES_SRC, WIRES_SRC, ROOT_DIR, BASE_URL,
    esc, format_date, parse_frontmatter,
    page_head, page_nav, page_footer,
)

AUTHORS_SRC = os.path.join(ROOT_DIR, "content", "authors")
AUTHORS_OUT = os.path.join(ROOT_DIR, "authors")


def load_authors():
    """Return list of author dicts, sorted by order then name.

    Adds aliases[] (lowercased name variants) so an article with
    `author: Valentine Eluwasi` matches the same author as
    `author: valentine eluwasi`.
    """
    authors = []
    for path in sorted(glob.glob(os.path.join(AUTHORS_SRC, "*.md"))):
        with open(path, "r", encoding="utf-8") as f:
            raw = f.read()
        meta, body = parse_frontmatter(raw)
        if not meta.get("name"):
            continue
        if meta.get("active", "true").lower() == "false":
            continue
        slug = meta.get("slug") or os.path.splitext(os.path.basename(path))[0]
        try:
            order = int(meta.get("order", "10"))
        except ValueError:
            order = 10
        authors.append({
            "slug": slug,
            "name": meta.get("name", "").strip(),
            "role": meta.get("role", "").strip(),
            "beat": meta.get("beat", "").strip(),
            "bio": meta.get("bio", "").strip(),
            "photo": meta.get("photo", "").strip(),
            "location": meta.get("location", "").strip(),
            "twitter": meta.get("twitter", "").strip().lstrip("@"),
            "instagram": meta.get("instagram", "").strip().lstrip("@"),
            "linkedin": meta.get("linkedin", "").strip(),
            "email": meta.get("email", "").strip(),
            "website": meta.get("website", "").strip(),
            "academy": str(meta.get("academy", "")).strip().lower() in ("true", "yes", "1"),
            "order": order,
            "body": body.strip(),
            "aliases": {meta.get("name", "").strip().lower()},
        })
    authors.sort(key=lambda a: (a["order"], a["name"]))
    return authors


def build_name_to_slug(authors):
    """Map every lowercased author name (and alias) to its slug.
    Used by build_static_pages to wrap matching bylines in a link."""
    out = {}
    for a in authors:
        for alias in a["aliases"]:
            if alias:
                out[alias] = a["slug"]
    return out


def find_articles_by_author(author):
    """Walk all article markdown files and return the ones whose
    `author:` frontmatter matches this author's name (case-insensitive)."""
    matches = []
    paths = (sorted(glob.glob(os.path.join(ARTICLES_SRC, "*.md")))
             + sorted(glob.glob(os.path.join(WIRES_SRC, "*.md"))))
    target_names = author["aliases"]
    for md_path in paths:
        slug = os.path.splitext(os.path.basename(md_path))[0]
        if slug == "index":
            continue
        with open(md_path, "r", encoding="utf-8") as f:
            raw = f.read()
        meta, _ = parse_frontmatter(raw)
        if meta.get("draft", "").lower() == "true":
            continue
        author_val = (meta.get("author", "") or "").strip().lower()
        if author_val and author_val in target_names:
            matches.append({
                "slug": slug,
                "title": meta.get("title", "Untitled"),
                "date": meta.get("date", ""),
                "category": meta.get("category", "").strip(),
                "summary": meta.get("summary", "").strip(),
                "image": meta.get("image", "").strip(),
                "longform": meta.get("longform", "").lower() == "true",
            })
    matches.sort(key=lambda a: a.get("date", ""), reverse=True)
    return matches


def monogram(name):
    parts = [p for p in name.split() if p]
    if not parts:
        return "MT"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()


def render_social(author):
    """Render the social-link row. Returns '' if author has no socials."""
    items = []
    if author["twitter"]:
        items.append(f'<a href="https://twitter.com/{esc(author["twitter"])}" rel="me noopener" target="_blank" aria-label="X / Twitter">X / Twitter</a>')
    if author["instagram"]:
        items.append(f'<a href="https://instagram.com/{esc(author["instagram"])}" rel="me noopener" target="_blank" aria-label="Instagram">Instagram</a>')
    if author["linkedin"]:
        items.append(f'<a href="https://linkedin.com/in/{esc(author["linkedin"])}" rel="me noopener" target="_blank" aria-label="LinkedIn">LinkedIn</a>')
    if author["website"]:
        items.append(f'<a href="{esc(author["website"])}" rel="me noopener" target="_blank" aria-label="Website">Website</a>')
    if author["email"]:
        items.append(f'<a href="mailto:{esc(author["email"])}" aria-label="Email">{esc(author["email"])}</a>')
    if not items:
        return ""
    return '\n          <div class="author-page-social">\n            ' + "\n            ".join(items) + '\n          </div>'


def render_archive_cards(articles):
    if not articles:
        return '<p class="author-archive-empty">No published articles yet.</p>'
    cards = []
    for a in articles:
        href = f"../articles/{a['slug']}.html"
        cat = (a["category"] or "News").upper()
        date = format_date(a["date"])
        summary = a["summary"][:160]
        cards.append(
            f'    <a class="author-archive-card" href="{href}">\n'
            f'      <div class="author-archive-card-body">\n'
            f'        <span class="author-archive-card-cat">{esc(cat)}</span>\n'
            f'        <h3 class="author-archive-card-title">{esc(a["title"])}</h3>\n'
            f'        <p class="author-archive-card-summary">{esc(summary)}</p>\n'
            f'        <span class="author-archive-card-date">{esc(date)}</span>\n'
            f'      </div>\n'
            f'    </a>'
        )
    return (
        '  <div class="author-archive-grid">\n'
        + "\n".join(cards)
        + '\n  </div>'
    )


def render_author_page(author):
    name = author["name"]
    slug = author["slug"]
    canonical = f"{BASE_URL}/authors/{slug}.html"
    page_title = f"{name} | The Mutapa Times"
    description = author["bio"] or f"Articles by {name} for The Mutapa Times."

    # Photo or monogram fallback
    if author["photo"]:
        avatar = f'<img src="{esc(author["photo"])}" alt="{esc(name)}" class="author-page-photo">'
    else:
        avatar = f'<span class="author-page-monogram" aria-hidden="true">{esc(monogram(name))}</span>'

    # Schema.org Person + their articles
    articles = find_articles_by_author(author)
    schema = {
        "@context": "https://schema.org",
        "@type": "Person",
        "name": name,
        "url": canonical,
        "jobTitle": author["role"],
        "description": author["bio"],
        "worksFor": {
            "@type": "Organization",
            "name": "The Mutapa Times",
            "url": BASE_URL,
        },
    }
    sameAs = []
    if author["twitter"]:
        sameAs.append(f"https://twitter.com/{author['twitter']}")
    if author["instagram"]:
        sameAs.append(f"https://instagram.com/{author['instagram']}")
    if author["linkedin"]:
        sameAs.append(f"https://linkedin.com/in/{author['linkedin']}")
    if author["website"]:
        sameAs.append(author["website"])
    if sameAs:
        schema["sameAs"] = sameAs

    breadcrumb = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{BASE_URL}/"},
            {"@type": "ListItem", "position": 2, "name": "Authors", "item": f"{BASE_URL}/authors/"},
            {"@type": "ListItem", "position": 3, "name": name, "item": canonical},
        ],
    }

    og_image = author["photo"] if author["photo"] else f"{BASE_URL}/img/brand/og-share.png"

    parts = []
    parts.append(page_head(page_title, description, canonical, "profile", og_image, depth=1))
    parts.append(f"""
<script type="application/ld+json">
{json.dumps(schema)}
</script>
<script type="application/ld+json">
{json.dumps(breadcrumb)}
</script>""")
    parts.append(page_nav("articles", depth=1))

    long_bio_html = ""
    if author["body"]:
        # Treat blank-line-separated paragraphs as <p>.
        paras = [p.strip() for p in author["body"].split("\n\n") if p.strip()]
        long_bio_html = (
            '\n      <div class="author-page-long-bio">\n'
            + "\n".join(f"        <p>{esc(p)}</p>" for p in paras)
            + '\n      </div>'
        )

    parts.append(f"""
  <main>
    <article class="author-page">
      <nav class="article-breadcrumb" aria-label="Breadcrumb">
        <a href="../index.html">Home</a> <span aria-hidden="true">/</span>
        <a href="./">Authors</a> <span aria-hidden="true">/</span>
        <span>{esc(name)}</span>
      </nav>

      <header class="author-page-hero">
        <div class="author-page-avatar">
          {avatar}
        </div>
        <div class="author-page-text">
          <p class="author-page-eyebrow">Author</p>
          <h1 class="author-page-name">{esc(name)}</h1>
          {'<a class="author-page-pill" href="../academy/">Mutapa Times Academy alumni</a>' if author["academy"] else ''}
          {f'<p class="author-page-role">{esc(author["role"])}</p>' if author["role"] else ''}
          {f'<p class="author-page-bio">{esc(author["bio"])}</p>' if author["bio"] else ''}
          {f'<p class="author-page-beat"><span>Covers:</span> {esc(author["beat"])}</p>' if author["beat"] else ''}
          {f'<p class="author-page-location">{esc(author["location"])}</p>' if author["location"] else ''}{render_social(author)}
        </div>
      </header>{long_bio_html}

      <section class="author-archive">
        <h2 class="author-archive-heading">Articles by {esc(name)}</h2>
{render_archive_cards(articles)}
      </section>
    </article>
  </main>""")

    parts.append(page_footer(depth=1))
    parts.append("""
  <script defer src="../js/vendor/modernizr-3.11.2.min.js"></script>
  <script src="https://code.jquery.com/jquery-3.4.1.min.js" integrity="sha256-CSXorXvZcTkaix6Yvo6HppcZGetbYMGWSFlBw8HfCJo=" crossorigin="anonymous"></script>
  <script>window.jQuery || document.write('<script src="../js/vendor/jquery-3.4.1.min.js"><\\/script>')</script>
  <script defer src="../js/plugins.js"></script>
  <script defer src="../js/main.js"></script>
  </body>
</html>""")
    return "\n".join(parts)


def render_index_page(authors):
    """Build /authors/index.html — the masthead."""
    canonical = f"{BASE_URL}/authors/"
    page_title = "Authors and bylines | The Mutapa Times"
    description = "The journalists and contributors writing for The Mutapa Times."

    parts = []
    parts.append(page_head(page_title, description, canonical, "website",
                           f"{BASE_URL}/img/brand/og-share.png", depth=1))
    parts.append(page_nav("articles", depth=1))

    cards = []
    for a in authors:
        if a["photo"]:
            avatar = f'<img src="{esc(a["photo"])}" alt="{esc(a["name"])}" class="author-list-photo">'
        else:
            avatar = f'<span class="author-list-monogram" aria-hidden="true">{esc(monogram(a["name"]))}</span>'
        role_html = f'<p class="author-list-role">{esc(a["role"])}</p>' if a["role"] else ""
        bio_html = f'<p class="author-list-bio">{esc(a["bio"])}</p>' if a["bio"] else ""
        cards.append(
            f'    <a class="author-list-card" href="./{a["slug"]}.html">\n'
            f'      <div class="author-list-avatar">{avatar}</div>\n'
            f'      <div class="author-list-text">\n'
            f'        <h2 class="author-list-name">{esc(a["name"])}</h2>\n'
            f'        {role_html}\n'
            f'        {bio_html}\n'
            f'      </div>\n'
            f'    </a>'
        )

    parts.append(f"""
  <main>
    <article class="authors-index">
      <header class="authors-index-hero">
        <p class="authors-index-eyebrow">Masthead</p>
        <h1 class="authors-index-title">Authors and bylines</h1>
        <p class="authors-index-deck">The journalists and contributors behind The Mutapa Times.</p>
      </header>
      <div class="author-list-grid">
{chr(10).join(cards)}
      </div>
    </article>
  </main>""")

    parts.append(page_footer(depth=1))
    parts.append("""
  <script defer src="../js/vendor/modernizr-3.11.2.min.js"></script>
  <script src="https://code.jquery.com/jquery-3.4.1.min.js" integrity="sha256-CSXorXvZcTkaix6Yvo6HppcZGetbYMGWSFlBw8HfCJo=" crossorigin="anonymous"></script>
  <script>window.jQuery || document.write('<script src="../js/vendor/jquery-3.4.1.min.js"><\\/script>')</script>
  <script defer src="../js/plugins.js"></script>
  <script defer src="../js/main.js"></script>
  </body>
</html>""")
    return "\n".join(parts)


def build():
    os.makedirs(AUTHORS_OUT, exist_ok=True)
    authors = load_authors()
    if not authors:
        print("No authors found in content/authors/")
        return

    # Per-author pages
    for author in authors:
        out_path = os.path.join(AUTHORS_OUT, f"{author['slug']}.html")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(render_author_page(author))
        print(f"  Wrote authors/{author['slug']}.html")

    # Masthead / index page
    index_path = os.path.join(AUTHORS_OUT, "index.html")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(render_index_page(authors))
    print(f"  Wrote authors/index.html")

    # Author manifest for the build_static_pages byline linker
    manifest = {a["name"].lower(): a["slug"] for a in authors}
    manifest_path = os.path.join(ROOT_DIR, "data", "authors.json")
    os.makedirs(os.path.dirname(manifest_path), exist_ok=True)
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"  Wrote data/authors.json ({len(manifest)} entries)")


if __name__ == "__main__":
    build()
