#!/usr/bin/env python3
"""Generate per-artwork and per-artist detail pages from data/arts.json.

Outputs:
  /arts/<artwork-slug>.html        — one per artwork (potentially thousands)
  /arts/artist/<artist-slug>.html  — one per artist

Each detail page links out to the canonical Artsy listing (artwork.artsy_url)
and lists other works by the same artist sourced from the cached snapshot.

Run after fetch_artsy.py (or after editing data/arts.json by hand):
  python scripts/build_arts_pages.py
"""
import html
import json
import os
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
DATA = os.path.join(ROOT, "data", "arts.json")
ARTS_DIR = os.path.join(ROOT, "arts")
ARTIST_DIR = os.path.join(ARTS_DIR, "artist")


def esc(s: str) -> str:
    return html.escape(s or "", quote=True)


def palette_for(slug: str) -> str:
    pal = ["#f5e8c8", "#eadad5", "#dae2d5", "#d7dae8", "#ecdac0", "#e2d8d0"]
    h = 0
    for ch in slug:
        h = (h * 31 + ord(ch)) & 0xFFFFFFFF
    return pal[h % len(pal)]


HEAD = """<!doctype html>
<html class="no-js" lang="en">
<head>
<meta charset="utf-8">
<title>{title} | The Mutapa Times</title>
<link rel="canonical" href="https://www.mutapatimes.com{canonical}">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="description" content="{desc}">
<meta name="robots" content="index, follow">
<meta property="og:type" content="article">
<meta property="og:title" content="{title} | The Mutapa Times">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="https://www.mutapatimes.com{canonical}">
<meta property="og:image" content="{og_image}">
<meta property="og:site_name" content="The Mutapa Times">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Playfair+Display:ital,wght@0,400;0,700;0,900;1,400&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css" media="print" onload="this.media='all'"><noscript><link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css"></noscript>
<link rel="stylesheet" href="../css/normalize.css">
<link rel="stylesheet" href="../css/main.css?v=102">
<link rel="stylesheet" href="../css/arts.css?v=1">
{ld_json}
</head>
<body>
<div class="topbar"><a href="/" class="topbar-brand"><em>The Mutapa Times</em></a><a href="/subscribe" class="topbar-cta">Subscribe</a></div>
<div class="paper">
<a href="/" class="title-link"><div class="titleDiv"><h1 class="title notranslate">THE MUTAPA TIMES</h1></div><h4 class="sub notranslate">Zimbabwe outside-in</h4></a>
<nav id="mainNav">
  <p><a href="/">News</a></p>
  <p><a href="/economy">Economy</a></p>
  <p><a href="/fx">FX</a></p>
  <p><a href="/property">Property</a></p>
  <p><a href="/jobs">Jobs</a></p>
  <p><a class="active" href="/arts">Arts</a></p>
  <p><a href="/articles">Articles</a></p>
</nav>
<hr class="topHr"><hr class="bottomHr"><hr class="dateHr">
<nav style="max-width:1000px;margin:24px auto 0;padding:0 24px;font-size:13px;color:#6b665a">
  <a href="/arts" style="color:#6b665a">← All Zimbabwean art</a>
</nav>
"""

FOOT = """
<footer class="atlantic-foot"><div class="atlantic-foot-inner">
  <div class="atlantic-foot-fine">
    <a href="/">Home</a><span class="sep">·</span>
    <a href="/arts">All Zimbabwean art</a><span class="sep">·</span>
    <a href="/privacy">Privacy</a><span class="sep">·</span>
    <a href="/terms">Terms</a>
  </div>
  <p class="atlantic-foot-copy">© 2020–2026 The Mutapa Times. All rights reserved.</p>
</div></footer>
</div>
</body>
</html>
"""


def render_artwork(art: dict, all_by_artist: dict) -> str:
    title_full = f"{art['artist_name']} — {art['title']}"
    canonical = f"/arts/{art['slug']}.html"
    desc = f"{art['artist_name']}, {art['title']}{', ' + art['year'] if art['year'] else ''}. {art['medium'] or art['category'] or 'Artwork'}. {art['partner_name']}."
    og_image = art["image_url"] or "https://www.mutapatimes.com/img/brand/og-share.png"

    ld = {
        "@context": "https://schema.org",
        "@type": "VisualArtwork",
        "name": art["title"],
        "creator": {"@type": "Person", "name": art["artist_name"]},
        "dateCreated": art["year"],
        "artform": art["category"],
        "artMedium": art["medium"],
        "url": f"https://www.mutapatimes.com{canonical}",
        "sameAs": art["artsy_url"],
    }
    if art["image_url"]:
        ld["image"] = art["image_url"]
    ld_json = f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>'

    image_block = ""
    if art["image_url"]:
        image_block = f'<img src="{esc(art["image_url"])}" alt="{esc(title_full)}" loading="eager">'
    else:
        bg = palette_for(art["slug"])
        image_block = (
            f'<div class="arts-card-image-fallback" style="background:{bg}">'
            f'<div class="fb-artist">{esc(art["artist_name"])}</div>'
            f'<div class="fb-title">&ldquo;{esc(art["title"])}&rdquo;</div>'
            f'<div class="fb-mark">{esc(art["medium"] or art["category"] or "Artwork")}</div>'
            f'</div>'
        )

    rows = []
    if art["year"]:
        rows.append(f"<dt>Year</dt><dd>{esc(art['year'])}</dd>")
    if art["medium"]:
        rows.append(f"<dt>Medium</dt><dd>{esc(art['medium'])}</dd>")
    if art["category"]:
        rows.append(f"<dt>Category</dt><dd>{esc(art['category'])}</dd>")
    if art["dimensions"]:
        rows.append(f"<dt>Dimensions</dt><dd>{esc(art['dimensions'])}</dd>")
    if art["partner_name"]:
        rows.append(f"<dt>Gallery</dt><dd>{esc(art['partner_name'])}</dd>")
    if art["price"]:
        rows.append(f"<dt>Price</dt><dd>{esc(art['price'])}</dd>")
    if art["rarity"]:
        rows.append(f"<dt>Rarity</dt><dd>{esc(art['rarity'].title())}</dd>")

    siblings = [w for w in all_by_artist.get(art["artist_slug"], []) if w["slug"] != art["slug"]][:8]
    sib_html = ""
    if siblings:
        sib_html = '<section style="max-width:1000px;margin:40px auto 0;padding:0 24px"><h2 style="font-family:\'Playfair Display\',Georgia,serif;font-size:22px;margin:0 0 16px">More by ' + esc(art["artist_name"]) + '</h2><div class="arts-grid">'
        for s in siblings:
            sib_url = f"/arts/{s['slug']}.html"
            img = s["image_url"]
            if img:
                tile_img = f'<div class="arts-card-image-wrap"><img class="arts-card-image" src="{esc(img)}" alt="{esc(s["title"])}" loading="lazy"></div>'
            else:
                bg2 = palette_for(s["slug"])
                tile_img = (
                    f'<div class="arts-card-image-wrap" style="background:{bg2}">'
                    f'<div class="arts-card-image-fallback">'
                    f'<div class="fb-artist">{esc(s["artist_name"])}</div>'
                    f'<div class="fb-title">&ldquo;{esc(s["title"])}&rdquo;</div>'
                    f'<div class="fb-mark">{esc(s["medium"] or s["category"] or "Artwork")}</div>'
                    f'</div></div>'
                )
            sib_html += (
                f'<a class="arts-card" href="{sib_url}">{tile_img}'
                f'<div class="arts-card-meta">'
                f'<p class="arts-card-title">{esc(s["title"])}{(", " + esc(s["year"])) if s["year"] else ""}</p>'
                f'<p class="arts-card-price">{esc(s["price"] or "Inquire")}</p>'
                f'</div></a>'
            )
        sib_html += '</div></section>'

    head = HEAD.format(
        title=esc(title_full),
        canonical=canonical,
        desc=esc(desc),
        og_image=esc(og_image),
        ld_json=ld_json,
    )
    body = f"""
<article class="artwork-detail">
  <div class="artwork-detail-image-wrap">{image_block}</div>
  <div class="artwork-detail-meta">
    <h1>{esc(art['title'])}</h1>
    <p class="artwork-artist">By <a href="/arts/artist/{esc(art['artist_slug'])}.html">{esc(art['artist_name'])}</a></p>
    <dl>{''.join(rows)}</dl>
    <a class="artwork-detail-cta" href="{esc(art['artsy_url'])}" target="_blank" rel="noopener">View on Artsy →</a>
  </div>
</article>
<p class="artwork-detail-foot">Listing surfaced from <a href="{esc(art['artsy_url'])}" target="_blank" rel="noopener">artsy.net</a>. The Mutapa Times receives no commission. Availability and price not guaranteed.</p>
{sib_html}
"""
    return head + body + FOOT


def render_artist(artist: dict, works: list) -> str:
    name = artist["name"]
    slug = artist["slug"]
    canonical = f"/arts/artist/{slug}.html"
    life = ""
    if artist.get("birthday") and artist.get("deathday"):
        life = f" ({artist['birthday']}–{artist['deathday']})"
    elif artist.get("birthday"):
        life = f" (b. {artist['birthday']})"
    desc = f"Works by {name}{life}, surfaced from the Artsy public catalogue. {len(works)} artwork{'s' if len(works) != 1 else ''} indexed by The Mutapa Times."

    ld = {
        "@context": "https://schema.org",
        "@type": "Person",
        "name": name,
        "nationality": artist.get("nationality") or "Zimbabwean",
        "url": f"https://www.mutapatimes.com{canonical}",
        "sameAs": f"https://www.artsy.net/artist/{slug}",
    }
    if artist.get("birthday"):
        ld["birthDate"] = artist["birthday"]
    if artist.get("deathday"):
        ld["deathDate"] = artist["deathday"]
    ld_json = f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>'

    head = HEAD.format(
        title=esc(name),
        canonical=canonical,
        desc=esc(desc),
        og_image=esc("https://www.mutapatimes.com/img/brand/og-share.png"),
        ld_json=ld_json,
    ).replace('href="../css/', 'href="../../css/')

    # Path is one level deeper, fix relative back-link
    head = head.replace('<a href="/arts" style="color:#6b665a">', '<a href="/arts" style="color:#6b665a">')

    body = f"""
<header style="max-width:1000px;margin:32px auto 16px;padding:0 24px">
  <p style="text-transform:uppercase;font-size:12px;letter-spacing:0.1em;color:#6b665a;margin:0 0 6px">Artist</p>
  <h1 style="font-family:'Playfair Display',Georgia,serif;font-weight:700;font-size:40px;line-height:1.1;margin:0">{esc(name)}<small style="font-weight:400;font-size:18px;color:#6b665a;display:block;margin-top:6px">{esc(artist.get("nationality") or "Zimbabwean")}{esc(life)}</small></h1>
  <p style="color:#4a443b;margin:14px 0 0">{len(works)} artwork{'s' if len(works) != 1 else ''} indexed on Mutapa Times — sourced from <a href="https://www.artsy.net/artist/{esc(slug)}" target="_blank" rel="noopener">artsy.net/artist/{esc(slug)}</a>.</p>
</header>
<section class="arts-listings-section" style="margin-top:24px">
  <div class="arts-grid">
"""
    for w in works:
        if w["image_url"]:
            tile_img = f'<div class="arts-card-image-wrap"><img class="arts-card-image" src="{esc(w["image_url"])}" alt="{esc(w["title"])}" loading="lazy"></div>'
        else:
            bg = palette_for(w["slug"])
            tile_img = (
                f'<div class="arts-card-image-wrap" style="background:{bg}">'
                f'<div class="arts-card-image-fallback">'
                f'<div class="fb-artist">{esc(w["artist_name"])}</div>'
                f'<div class="fb-title">&ldquo;{esc(w["title"])}&rdquo;</div>'
                f'<div class="fb-mark">{esc(w["medium"] or w["category"] or "Artwork")}</div>'
                f'</div></div>'
            )
        body += (
            f'<a class="arts-card" href="/arts/{esc(w["slug"])}.html">{tile_img}'
            f'<div class="arts-card-meta">'
            f'<p class="arts-card-title">{esc(w["title"])}{(", " + esc(w["year"])) if w["year"] else ""}</p>'
            f'<p class="arts-card-partner">{esc(w["partner_name"])}</p>'
            f'<p class="arts-card-price">{esc(w["price"] or "Inquire")}</p>'
            f'</div></a>'
        )
    body += """
  </div>
</section>
"""
    return head + body + FOOT


def main():
    if not os.path.exists(DATA):
        print(f"missing {DATA} — run scripts/fetch_artsy.py first (or seed it).", file=sys.stderr)
        sys.exit(1)
    with open(DATA) as f:
        data = json.load(f)

    os.makedirs(ARTS_DIR, exist_ok=True)
    os.makedirs(ARTIST_DIR, exist_ok=True)

    artworks = data.get("artworks", [])
    artists = data.get("artists", [])

    # Group artworks by artist slug for sibling links
    by_artist = {}
    for w in artworks:
        by_artist.setdefault(w["artist_slug"], []).append(w)

    n_works = 0
    for w in artworks:
        out_path = os.path.join(ARTS_DIR, f"{w['slug']}.html")
        with open(out_path, "w") as f:
            f.write(render_artwork(w, by_artist))
        n_works += 1

    n_artists = 0
    for a in artists:
        works = by_artist.get(a["slug"], [])
        if not works:
            continue
        out_path = os.path.join(ARTIST_DIR, f"{a['slug']}.html")
        with open(out_path, "w") as f:
            f.write(render_artist(a, works))
        n_artists += 1

    print(f"wrote {n_works} artwork pages and {n_artists} artist pages")


if __name__ == "__main__":
    main()
