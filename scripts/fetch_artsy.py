#!/usr/bin/env python3
"""Fetch Zimbabwean Art from the Artsy public API.

Auth: client_credentials → X-Xapp-Token (valid 1 week).
Endpoint: /api/artworks?gene_id=zimbabwean-art (paginated via HAL+JSON _links.next).
Output:
  data/arts.json    — all artworks (+ artist summary), schema documented below.

ENV REQUIRED to run:
  ARTSY_CLIENT_ID
  ARTSY_CLIENT_SECRET

⚠ Artsy is deprecating the public API. This fetcher is built for snapshot
durability: if the API dies we keep the last successful arts.json and the
site continues to render from it.

Schema (data/arts.json):
{
  "fetched_at": ISO-8601 UTC,
  "source": "artsy.net public API",
  "gene": "zimbabwean-art",
  "count": int,
  "artworks": [ { id, slug, title, year, artist_name, artist_slug,
                  medium, category, dimensions, price, partner_name,
                  image_url, image_aspect, artsy_url, rarity }, ... ],
  "artists":  [ { slug, name, nationality, birthday, deathday,
                  image_url, artwork_count }, ... ]
}
"""
import json
import os
import sys
import time
from datetime import datetime, timezone

import requests

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT_PATH = os.path.join(ROOT, "data", "arts.json")

API_BASE = "https://api.artsy.net/api"
GENE_ID = "zimbabwean-art"
PAGE_SIZE = 100  # API max
USER_AGENT = "MutapaTimes/1.0 (+https://www.mutapatimes.com)"


def get_xapp_token() -> str:
    cid = os.environ.get("ARTSY_CLIENT_ID")
    cs = os.environ.get("ARTSY_CLIENT_SECRET")
    if not cid or not cs:
        raise RuntimeError(
            "Set ARTSY_CLIENT_ID and ARTSY_CLIENT_SECRET. "
            "Register an app at https://www.artsy.net/developers."
        )
    r = requests.post(
        f"{API_BASE}/tokens/xapp_token",
        data={"client_id": cid, "client_secret": cs},
        headers={"User-Agent": USER_AGENT},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["token"]


def hal_paginate(start_url: str, token: str):
    """Walk HAL+JSON pagination via _links.next.href."""
    url = start_url
    while url:
        r = requests.get(
            url,
            headers={"X-Xapp-Token": token, "User-Agent": USER_AGENT},
            timeout=60,
        )
        r.raise_for_status()
        body = r.json()
        yield body
        url = body.get("_links", {}).get("next", {}).get("href")
        # Light rate-limit courtesy
        time.sleep(0.25)


def hal_link(obj, rel):
    return obj.get("_links", {}).get(rel, {}).get("href")


def best_image_url(artwork: dict) -> tuple:
    """Return (url, aspect_ratio) for the artwork's primary image, large size."""
    img_link = hal_link(artwork, "image")
    if not img_link:
        return ("", 1.0)
    versions = artwork.get("image_versions", []) or []
    # Prefer "large", then "medium", then "tall", then first available.
    for v in ("large", "medium", "tall", "square"):
        if v in versions:
            return (img_link.replace("{image_version}", v), 1.0)
    if versions:
        return (img_link.replace("{image_version}", versions[0]), 1.0)
    return ("", 1.0)


def artsy_url(artwork: dict) -> str:
    perma = hal_link(artwork, "permalink")
    if perma:
        return perma
    slug = artwork.get("slug")
    return f"https://www.artsy.net/artwork/{slug}" if slug else ""


def shrink_artwork(artwork: dict) -> dict:
    """Strip Artsy response down to what the site renders. Resolves the
    embedded artist if present so each artwork carries display fields."""
    img_url, aspect = best_image_url(artwork)
    artist = (artwork.get("_embedded", {}) or {}).get("artist") or {}
    return {
        "id": artwork.get("id"),
        "slug": artwork.get("slug"),
        "title": (artwork.get("title") or "").strip(),
        "year": (artwork.get("date") or "").strip(),
        "artist_name": (artist.get("name") or "").strip(),
        "artist_slug": artist.get("slug") or "",
        "medium": (artwork.get("medium") or "").strip(),
        "category": (artwork.get("category") or "").strip(),
        "dimensions": ((artwork.get("dimensions") or {}).get("in") or {}).get("text", ""),
        "price": (artwork.get("price") or artwork.get("sale_message") or "").strip(),
        "partner_name": "",  # filled in a second pass via /partner link
        "image_url": img_url,
        "image_aspect": aspect,
        "artsy_url": artsy_url(artwork),
        "rarity": (artwork.get("unique") and "unique")
                  or (artwork.get("edition_sets") and "edition")
                  or "",
    }


def shrink_artist(artist: dict) -> dict:
    img_url = ""
    img_link = hal_link(artist, "image")
    versions = artist.get("image_versions") or []
    if img_link and versions:
        for v in ("square", "medium", "large"):
            if v in versions:
                img_url = img_link.replace("{image_version}", v)
                break
        if not img_url:
            img_url = img_link.replace("{image_version}", versions[0])
    return {
        "slug": artist.get("slug"),
        "name": (artist.get("name") or "").strip(),
        "nationality": (artist.get("nationality") or "").strip(),
        "birthday": (artist.get("birthday") or "").strip(),
        "deathday": (artist.get("deathday") or "").strip(),
        "image_url": img_url,
        "artwork_count": 0,  # filled after artworks are tallied
    }


def fetch_all() -> dict:
    token = get_xapp_token()
    print(f"got xapp token ({token[:10]}…)", file=sys.stderr)

    artworks = []
    start = f"{API_BASE}/artworks?gene_id={GENE_ID}&size={PAGE_SIZE}"
    for page in hal_paginate(start, token):
        items = (page.get("_embedded", {}) or {}).get("artworks", [])
        for item in items:
            artworks.append(shrink_artwork(item))
        print(f"  artworks +{len(items)}  total={len(artworks)}", file=sys.stderr)

    artists = []
    start = f"{API_BASE}/artists?gene_id={GENE_ID}&size={PAGE_SIZE}"
    for page in hal_paginate(start, token):
        items = (page.get("_embedded", {}) or {}).get("artists", [])
        for item in items:
            artists.append(shrink_artist(item))
        print(f"  artists  +{len(items)}  total={len(artists)}", file=sys.stderr)

    # Tally artwork_count per artist
    by_slug = {a["slug"]: 0 for a in artists if a["slug"]}
    for w in artworks:
        if w["artist_slug"] in by_slug:
            by_slug[w["artist_slug"]] += 1
    for a in artists:
        a["artwork_count"] = by_slug.get(a["slug"], 0)

    return {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source": "artsy.net public API",
        "gene": GENE_ID,
        "count": len(artworks),
        "artworks": artworks,
        "artists": artists,
    }


def main():
    try:
        data = fetch_all()
    except Exception as exc:
        # Resilient by design: don't blow away the last good snapshot
        print(f"fetch failed: {exc}", file=sys.stderr)
        if os.path.exists(OUT_PATH):
            print("keeping existing arts.json", file=sys.stderr)
            sys.exit(2)
        raise

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"wrote {OUT_PATH}: {data['count']} artworks, {len(data['artists'])} artists",
          file=sys.stderr)


if __name__ == "__main__":
    main()
