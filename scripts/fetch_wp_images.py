#!/usr/bin/env python3
"""Fetch Wikipedia page images for ATS schools that have a verified WP article.

We pull each article's lead image, check its Commons license, and only download
free-licensed images (CC-BY-*, CC0, Public Domain). Fair-use crests/logos are
skipped — we cannot redistribute those from our own server.

Outputs:
  img/schools/<slug>.jpg                    — downloaded image
  data/ats-schools-wp.json (in-place)       — updated with image metadata
"""
import json, urllib.request, urllib.parse, time, re
from pathlib import Path

ROOT = Path("/Users/valentineeluwasi/Documents/GitHub/mutapatimes")
IMG_DIR = ROOT / "img" / "schools"
IMG_DIR.mkdir(parents=True, exist_ok=True)

UA = "MutapaTimes/1.0 (https://mutapatimes.com; news@mutapatimes.com)"

# Free licenses we accept. Wikipedia/Commons extmetadata gives a LicenseShortName
# like "CC BY-SA 4.0", "CC0", "Public domain". Fair-use crests come back as
# things like "Fair use" or have UsageTerms saying so.
FREE_LICENSE_RE = re.compile(
    r"\b(CC[ -]?BY(?:[ -]?SA)?(?:[ -]?\d(?:\.\d)?)?|CC0|Public[ ]?domain|PDM|GFDL|Government[ ]Open[ ]Data|OGL)\b",
    re.I,
)
NONFREE_HINT_RE = re.compile(r"\bfair[ -]?use\b|\bnon[- ]?free\b", re.I)

def http_get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)

def http_download(url, dest):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        dest.write_bytes(r.read())

def fetch_article_image(title):
    """Return dict with image URL, filename, license, attribution; or None."""
    # First: get the lead pageimage filename
    url = (f"https://en.wikipedia.org/w/api.php?action=query"
           f"&titles={title}&prop=pageimages&piprop=name&format=json&redirects=1")
    try:
        j = http_get_json(url)
    except Exception as e:
        print(f"  pageimage err: {e}")
        return None
    pages = j.get("query", {}).get("pages", {})
    page = next(iter(pages.values()), {})
    fname = page.get("pageimage")
    if not fname:
        return None
    file_title = "File:" + fname

    # Second: get imageinfo (URL, license, etc) for that File:
    url2 = (f"https://en.wikipedia.org/w/api.php?action=query"
            f"&titles={urllib.parse.quote(file_title)}"
            f"&prop=imageinfo&iiprop=url|extmetadata|mime"
            f"&format=json&redirects=1")
    try:
        j2 = http_get_json(url2)
    except Exception as e:
        print(f"  imageinfo err: {e}")
        return None
    info_pages = j2.get("query", {}).get("pages", {})
    info_page = next(iter(info_pages.values()), {})
    infos = info_page.get("imageinfo")
    if not infos:
        return None
    info = infos[0]
    meta = info.get("extmetadata") or {}
    short = (meta.get("LicenseShortName") or {}).get("value", "")
    usage = (meta.get("UsageTerms") or {}).get("value", "")
    artist = (meta.get("Artist") or {}).get("value", "")
    credit = (meta.get("Credit") or {}).get("value", "")
    mime = info.get("mime", "")
    src = info.get("url", "")

    # Strip HTML from credit/artist
    def strip_html(s):
        s = re.sub(r"<[^>]+>", "", s or "")
        s = re.sub(r"\s+", " ", s).strip()
        return s
    artist_clean = strip_html(artist)
    credit_clean = strip_html(credit)

    # License gate
    license_text = short + " | " + usage
    is_free = bool(FREE_LICENSE_RE.search(license_text)) and not NONFREE_HINT_RE.search(license_text)

    return {
        "filename": fname,
        "url": src,
        "mime": mime,
        "license": short,
        "usage_terms": strip_html(usage),
        "artist": artist_clean,
        "credit": credit_clean,
        "is_free": is_free,
        "commons_page": f"https://commons.wikimedia.org/wiki/{file_title.replace(' ', '_')}",
    }

def ext_for_mime(mime, url):
    if "jpeg" in mime: return ".jpg"
    if "png" in mime: return ".png"
    if "webp" in mime: return ".webp"
    if "svg" in mime: return ".svg"
    if "gif" in mime: return ".gif"
    # Fall back to URL
    m = re.search(r"\.(jpe?g|png|webp|svg|gif)(?:$|\?)", url, re.I)
    return ("." + m.group(1).lower()) if m else ".jpg"

if __name__ == "__main__":
    wp_path = ROOT / "data" / "ats-schools-wp.json"
    wp = json.loads(wp_path.read_text())

    # Need ATS-name -> WP-title mapping (same as enrich script)
    mapping_titles = {}
    for name, data in wp.items():
        # Reconstruct WP title from the wikipedia URL
        m = re.search(r"wikipedia\.org/wiki/(.+)$", data.get("wikipedia",""))
        if m: mapping_titles[name] = m.group(1)

    # Need slug for filenames — load from ats-schools.json
    schools_data = json.loads((ROOT / "data" / "ats-schools.json").read_text())
    slug_for = {s["name"]: s["slug"] for s in schools_data["schools"]}

    n_free = 0
    n_skip_license = 0
    n_no_image = 0
    for name, wp_title in mapping_titles.items():
        print(f"  {name}  <-  {wp_title}")
        img = fetch_article_image(wp_title)
        if not img:
            print("    no image")
            n_no_image += 1
            wp[name].pop("image", None)
            continue
        if not img["is_free"]:
            print(f"    SKIP (license: {img['license']!r}, usage: {img['usage_terms'][:60]!r})")
            n_skip_license += 1
            # Still store metadata so we can show a "View on Wikipedia" link
            wp[name]["image"] = {**img, "local": None}
            continue
        slug = slug_for.get(name)
        if not slug:
            print(f"    no slug — skipping save")
            continue
        ext = ext_for_mime(img["mime"], img["url"])
        local = IMG_DIR / f"{slug}{ext}"
        try:
            http_download(img["url"], local)
            print(f"    saved {local.name}  ({local.stat().st_size//1024}KB, {img['license']})")
            wp[name]["image"] = {
                "filename": img["filename"],
                "license": img["license"],
                "artist": img["artist"],
                "credit": img["credit"],
                "commons_page": img["commons_page"],
                "local": f"/img/schools/{local.name}",
            }
            n_free += 1
        except Exception as e:
            print(f"    download err: {e}")
        time.sleep(0.6)

    wp_path.write_text(json.dumps(wp, indent=2, ensure_ascii=False))
    print(f"\nDone. free={n_free}  license-skip={n_skip_license}  no-image={n_no_image}")
