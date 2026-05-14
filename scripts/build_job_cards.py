#!/usr/bin/env python3
"""Render a brand headline card for every active job in data/jobs.json.

Mirrors scripts/build_feed_cards.py - each card is keyed by an MD5 hash
of the job URL so re-runs are cheap and stable. The Metricool jobs
autolist (https://www.mutapatimes.com/jobs-feed.xml) attaches these as
the post image so every social preview is on-brand.

Output:
    img/cards/jobs/{12-char-md5-of-url}.png  (1080x1350 portrait)
"""
import glob
import hashlib
import json
import os
import sys

# Shared brand card primitives
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from card_lib import (   # noqa: E402
    CARD_W, CARD_H, CARD_FG, CARD_FG_MUTED, ACCENT, CARD_BACKGROUNDS,
    load_font, wrap_text,
)

try:
    from PIL import Image, ImageDraw
except ImportError:
    print("ERROR: Pillow not installed. Run: pip install Pillow")
    sys.exit(1)


ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
JOBS_FILE = os.path.join(ROOT, "data", "jobs.json")
OUT_DIR = os.path.join(ROOT, "img", "cards", "jobs")
PUBLIC_BASE = "https://www.mutapatimes.com/img/cards/jobs"


def card_hash(url):
    return hashlib.md5((url or "").encode("utf-8")).hexdigest()[:12]


def card_filename(url):
    return f"{card_hash(url)}.png"


def card_public_url(url):
    return f"{PUBLIC_BASE}/{card_filename(url)}"


def _bg_for(url):
    """Deterministic palette index per URL - the same job always gets
    the same colour, the feed-level rotation feels varied."""
    h = card_hash(url)
    return int(h, 16) % len(CARD_BACKGROUNDS)


def render_job_card(job, output_path):
    """1080x1350 portrait card. Layout intentionally close to the
    headline card so the social grid feels coherent."""
    bg_idx = _bg_for(job.get("url") or "")
    bg = CARD_BACKGROUNDS[bg_idx]
    img = Image.new("RGB", (CARD_W, CARD_H), bg)
    draw = ImageDraw.Draw(img)

    masthead_font = load_font("serif_bold", 38)
    eyebrow_font = load_font("sans_bold", 22)
    title_font = load_font("serif_bold", 68)
    co_font = load_font("sans_bold", 32)
    meta_font = load_font("sans", 26)
    apply_font = load_font("sans_bold", 28)
    small_font = load_font("sans", 22)

    # Chrome
    draw.rectangle([(0, 0), (140, 10)], fill=ACCENT)
    draw.text((60, 60), "THE MUTAPA TIMES", font=masthead_font, fill=CARD_FG)
    draw.text((60, 114), "JOBS · ZIMBABWE",
              font=eyebrow_font, fill=ACCENT)

    # Title - wrap into up to 5 lines
    title = (job.get("title") or "Open role").strip()
    title_lines = wrap_text(title, title_font, CARD_W - 120, draw)[:5]
    line_height = 84
    title_y = 220
    for ln in title_lines:
        draw.text((60, title_y), ln, font=title_font, fill=CARD_FG)
        title_y += line_height

    # Company name - bold sans, accent-coloured
    company = (job.get("company") or "").strip()
    if company:
        draw.text((60, title_y + 30), company.upper(),
                  font=co_font, fill=ACCENT)

    # Meta line: location · type · salary (whichever exist)
    meta_bits = []
    for key in ("location", "type", "salary"):
        v = (job.get(key) or "").strip()
        if v:
            meta_bits.append(v)
    if meta_bits:
        meta_str = "  ·  ".join(meta_bits)
        # Wrap the meta line if it overflows
        meta_lines = wrap_text(meta_str, meta_font, CARD_W - 120, draw)[:2]
        my = title_y + 30 + (45 if company else 0)
        for ln in meta_lines:
            draw.text((60, my), ln, font=meta_font, fill=CARD_FG_MUTED)
            my += 36

    # Footer: divider + CTA + tagline
    cta_y = CARD_H - 140
    draw.line([(60, cta_y - 24), (CARD_W - 60, cta_y - 24)],
              fill=CARD_FG_MUTED, width=1)
    draw.text((60, cta_y), "Apply via mutapatimes.com/jobs",
              font=apply_font, fill=CARD_FG)
    draw.text((60, cta_y + 42), f"Source: {(job.get('source') or 'Various').strip()}",
              font=small_font, fill=CARD_FG_MUTED)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path, "PNG", optimize=True)


# First-party Mutapa Times internships - always rendered, fixed filenames
# so generate_rss.py can reference them deterministically.
INTERNSHIPS = [
    {
        "slug": "social-intern",
        "title": "Social Intern",
        "company": "The Mutapa Times",
        "location": "Remote - Worldwide",
        "type": "Internship · 3 months · 3 days/week",
        "source": "mutapatimes.com",
        "url": "https://www.mutapatimes.com/jobs.html#social-intern",
    },
    {
        "slug": "editor-intern",
        "title": "Editor Intern",
        "company": "The Mutapa Times",
        "location": "Remote - Worldwide",
        "type": "Internship · 3 months · 3 days/week",
        "source": "mutapatimes.com",
        "url": "https://www.mutapatimes.com/jobs.html#editor-intern",
    },
    {
        "slug": "data-intern",
        "title": "Data Intern",
        "company": "The Mutapa Times",
        "location": "Remote - Worldwide",
        "type": "Internship · 3 months · 3 days/week",
        "source": "mutapatimes.com",
        "url": "https://www.mutapatimes.com/jobs.html#data-intern",
    },
]


def collect_active_jobs():
    if not os.path.exists(JOBS_FILE):
        return []
    try:
        data = json.load(open(JOBS_FILE))
    except (json.JSONDecodeError, OSError):
        return []
    return [j for j in (data.get("jobs") or []) if (j.get("url") or "").strip()]


def prune_stale_cards(active_url_hashes):
    """Delete card PNGs whose job is no longer in the active feed -
    keeps img/cards/jobs/ tracking the live listings, prevents the
    1 GB GitHub Pages cap drift."""
    pruned = 0
    for path in glob.glob(os.path.join(OUT_DIR, "*.png")):
        name = os.path.splitext(os.path.basename(path))[0]
        # Internship cards use stable filenames (internship-<slug>) - leave them.
        if name.startswith("internship-"):
            continue
        # Only touch the 12-hex-char hashed cards we own
        if len(name) != 12 or not all(c in "0123456789abcdef" for c in name):
            continue
        if name not in active_url_hashes:
            try:
                os.remove(path)
                pruned += 1
            except OSError as e:
                print(f"    prune FAIL {name}: {e}")
    return pruned


def main():
    print("=== BUILD JOB CARDS ===")
    os.makedirs(OUT_DIR, exist_ok=True)
    jobs = collect_active_jobs()
    print(f"  {len(jobs)} active jobs in data/jobs.json")

    rendered = cached = failed = 0
    active_hashes = set()

    # First-party internships - rendered with a stable filename
    # (internship-{slug}.png) so the RSS feed can reference them
    # deterministically. Always re-rendered so copy tweaks take effect.
    for it in INTERNSHIPS:
        out_path = os.path.join(OUT_DIR, f"internship-{it['slug']}.png")
        try:
            render_job_card(it, out_path)
            rendered += 1
        except Exception as e:
            failed += 1
            print(f"    FAIL internship {it['slug']}: {e}")

    # Live aggregated jobs - hash-keyed, cached by file existence
    for job in jobs:
        url = job["url"].strip()
        active_hashes.add(card_hash(url))
        out_path = os.path.join(OUT_DIR, card_filename(url))
        if os.path.exists(out_path):
            cached += 1
            continue
        try:
            render_job_card(job, out_path)
            rendered += 1
        except Exception as e:
            failed += 1
            print(f"    FAIL {job.get('title', '?')[:50]}: {e}")

    pruned = prune_stale_cards(active_hashes)
    print(f"  Rendered  {rendered} new")
    print(f"  Cached    {cached} existing")
    print(f"  Pruned    {pruned} stale")
    if failed:
        print(f"  Failed    {failed}")
    print(f"\n  Output:   {OUT_DIR}")
    print("\n=== DONE ===")


if __name__ == "__main__":
    main()
