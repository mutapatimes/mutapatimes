#!/usr/bin/env python3
"""Build 9:16 Instagram-Story cards (1080×1920) for stories-feed.xml.

Metricool's Story autopublish strips captions ("Max characters
allowed 0"), so EVERY piece of context the post needs has to live
inside the image itself. Each card therefore carries:

  • brand chrome (wordmark + red rule + ZIMBABWE OUTSIDE-IN sub)
  • category eyebrow in brand red
  • big serif headline (auto-sized to fit ~4 lines)
  • editorial body paragraph in smaller text — the article summary,
    listing specs, or job blurb that would otherwise live in the caption
  • a prominent red "Read more on Mutapa Times" CTA pill

Output: img/cards/stories/{md5}.png — hash derived from the canonical
mutapatimes.com URL the story links to.
"""
import glob
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone

try:
    from PIL import Image, ImageDraw
except ImportError:
    raise SystemExit("ERROR: Pillow not installed. Run: pip install Pillow")

# Reuse the shared brand primitives (BUTTER, ACCENT, fonts, wrap_text)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from card_lib import (  # noqa: E402
    BUTTER, ACCENT, CARD_FG, CARD_FG_MUTED, load_font, wrap_text,
)

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT_DIR = os.path.join(ROOT, "img", "cards", "stories")
os.makedirs(OUT_DIR, exist_ok=True)

# Instagram Story dimensions — 9:16 full-screen
W = 1080
H = 1920

# Only render cards for articles published in the last N days. The CMS
# index spans years, so without this gate every archive article from
# 2017 onward keeps a 9:16 card alive (~110KB each) and the directory
# grows until GitHub Pages refuses to publish. 30d matches build_feed_cards.
MAX_AGE_DAYS = 30


def _is_fresh(date_str):
    """Return True if the date string parses and is within MAX_AGE_DAYS.
    Internships and other dateless items pass through (collectors flag
    them with date=None to opt out of the freshness gate)."""
    if not date_str:
        return True
    try:
        clean = date_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(clean)
    except (ValueError, TypeError):
        return True  # unparseable → keep, don't lose data on a format quirk
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    try:
        return (datetime.now(timezone.utc) - dt).days <= MAX_AGE_DAYS
    except (TypeError, ValueError):
        return True

# ── URL → card filename ───────────────────────────────────
def card_hash(url):
    return hashlib.md5((url or "").encode("utf-8")).hexdigest()[:12]


def card_filename(url):
    return f"{card_hash(url)}.png"


def card_public_url(url):
    return f"/img/cards/stories/{card_filename(url)}"


# ── Layout helper: find the largest font size that fits ──
def fit_headline(draw, text, max_width, max_lines,
                 max_size=92, min_size=46, step=4):
    """Step font size down until the wrapped headline fits in `max_lines`."""
    for size in range(max_size, min_size - 1, -step):
        font = load_font("serif_bold", size)
        lines = wrap_text(text, font, max_width, draw)
        if len(lines) <= max_lines:
            return size, font, lines
    # Last-resort: smallest size + clip
    font = load_font("serif_bold", min_size)
    lines = wrap_text(text, font, max_width, draw)[:max_lines]
    return min_size, font, lines


def _text_w(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0]


def _text_h(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[3] - bbox[1]


def render_story_card(eyebrow, headline, body, attribution, output_path):
    """Render a 1080×1920 butter story card with:
      • brand chrome (top)
      • eyebrow + headline (mid-upper)
      • editorial body paragraph (mid)
      • attribution line (mid-lower)
      • red CTA pill anchored to the bottom

    `body` is the longer description that would otherwise live in the
    post caption — Stories strip captions, so it has to render here."""
    img = Image.new("RGB", (W, H), BUTTER)
    draw = ImageDraw.Draw(img)
    pad = 96

    # ── TOP: brand wordmark + red rule + subtitle ──
    wordmark_font = load_font("serif_bold", 52)
    draw.text((pad, 110), "THE MUTAPA TIMES", font=wordmark_font, fill=CARD_FG)
    rule_y = 110 + _text_h(draw, "THE MUTAPA TIMES", wordmark_font) + 22
    draw.rectangle([pad, rule_y, pad + 110, rule_y + 5], fill=ACCENT)
    sub_font = load_font("sans_bold", 20)
    draw.text((pad, rule_y + 22), "ZIMBABWE OUTSIDE-IN",
              font=sub_font, fill=CARD_FG_MUTED)

    # ── MIDDLE: eyebrow + headline + body + attribution ──
    max_width = W - 2 * pad

    eyebrow_y = 440
    eyebrow_font = load_font("sans_bold", 26)
    draw.text((pad, eyebrow_y), (eyebrow or "BRIEFING").upper(),
              font=eyebrow_font, fill=ACCENT)

    headline_y = eyebrow_y + 56
    # Cap headline to 5 lines so we leave breathing room for the body
    headline_size, headline_font, headline_lines = fit_headline(
        draw, headline or "", max_width, max_lines=5,
        max_size=84, min_size=46,
    )
    headline_lh = int(headline_size * 1.16)
    y = headline_y
    for line in headline_lines:
        draw.text((pad, y), line, font=headline_font, fill=CARD_FG)
        y += headline_lh

    # ── Body paragraph (the caption that Stories strip) ──
    body_clean = (body or "").strip()
    if body_clean:
        body_size, body_font, body_lines = fit_body(
            draw, body_clean, max_width,
            max_lines=10, max_size=34, min_size=24,
        )
        body_lh = int(body_size * 1.4)
        body_y = y + 48
        for line in body_lines:
            draw.text((pad, body_y), line, font=body_font, fill=CARD_FG)
            body_y += body_lh
        y = body_y

    # ── Attribution line (small, italic-feeling) ──
    if attribution:
        attr_font = load_font("sans_bold", 20)
        attr_text = attribution.strip()
        # Allow wrap to 2 lines
        attr_lines = wrap_text(attr_text, attr_font, max_width, draw)[:2]
        # Small accent dot before the attribution
        attr_y = y + 36
        draw.ellipse([pad, attr_y + 8, pad + 8, attr_y + 16], fill=ACCENT)
        attr_x = pad + 20
        for line in attr_lines:
            draw.text((attr_x, attr_y), line.upper(),
                      font=attr_font, fill=CARD_FG_MUTED)
            attr_y += 30

    # ── BOTTOM: CTA pill anchored to the bottom ──
    cta_text = "Read more on Mutapa Times  →"
    cta_font = load_font("sans_bold", 36)
    cta_w = _text_w(draw, cta_text, cta_font)
    cta_h = _text_h(draw, cta_text, cta_font)
    pill_padding_x = 56
    pill_padding_y = 28
    pill_w = cta_w + pill_padding_x * 2
    pill_h = cta_h + pill_padding_y * 2
    pill_x = (W - pill_w) // 2
    pill_y = H - pad - pill_h - 80
    radius = pill_h // 2
    draw.rounded_rectangle(
        [pill_x, pill_y, pill_x + pill_w, pill_y + pill_h],
        radius=radius, fill=ACCENT,
    )
    bbox = draw.textbbox((0, 0), cta_text, font=cta_font)
    text_y = pill_y + (pill_h - (bbox[3] - bbox[1])) // 2 - bbox[1]
    text_x = pill_x + pill_padding_x
    draw.text((text_x, text_y), cta_text, font=cta_font, fill=(255, 255, 255))

    # URL hint below pill
    url_font = load_font("sans", 24)
    url_text = "mutapatimes.com"
    url_w = _text_w(draw, url_text, url_font)
    draw.text(((W - url_w) // 2, pill_y + pill_h + 26),
              url_text, font=url_font, fill=CARD_FG_MUTED)

    img.save(output_path, "PNG", optimize=True)


def fit_body(draw, text, max_width, max_lines, max_size=34, min_size=22, step=2):
    """Step the body font size down until the paragraph fits in
    `max_lines`. Final fallback: hard-clip the wrap to max_lines."""
    for size in range(max_size, min_size - 1, -step):
        font = load_font("sans", size)
        lines = wrap_text(text, font, max_width, draw)
        if len(lines) <= max_lines:
            return size, font, lines
    font = load_font("sans", min_size)
    lines = wrap_text(text, font, max_width, draw)[:max_lines]
    # Add an ellipsis to the last line if we truncated
    if lines and len(wrap_text(text, font, max_width, draw)) > max_lines:
        last = lines[-1].rstrip(".,;: ")
        lines[-1] = last + "…"
    return min_size, font, lines


# ── Sources: business articles, property, jobs ──────────────
def collect_business_cards():
    """One story per fresh CMS article. Returns list of dicts with
    {url, eyebrow, headline, body, attribution, slug, date}."""
    out = []
    idx_path = os.path.join(ROOT, "content", "articles", "index.json")
    if not os.path.exists(idx_path):
        return out
    try:
        entries = json.load(open(idx_path))
    except (json.JSONDecodeError, OSError):
        return out
    keep_cats = {"Business", "Policy", "Tech", "Economy", "Environment", "Culture"}
    for e in entries:
        if not isinstance(e, dict):
            continue
        slug = e.get("slug")
        cat = (e.get("category") or "").strip()
        title = (e.get("title") or "").strip()
        author = (e.get("author") or "").strip()
        summary = (e.get("summary") or "").strip()
        if not slug or not title or cat not in keep_cats:
            continue
        url = f"https://mutapatimes.com/articles/{slug}"
        out.append({
            "url": url,
            "eyebrow": cat or "BUSINESS",
            "headline": title,
            "body": summary,
            "attribution": f"via {author}" if author else "",
            "slug": slug,
            "date": e.get("date", ""),
        })
    return out


def _fmt_usd(amount):
    try:
        n = float(amount)
    except (TypeError, ValueError):
        return ""
    if n >= 1_000_000:
        return f"USD {n / 1_000_000:.2f}M"
    if n >= 1_000:
        return f"USD {n / 1_000:.0f}K"
    return f"USD {n:.0f}"


def collect_property_cards():
    """One story per property listing — body assembles a prose
    description from price, beds, baths and location."""
    out = []
    p = os.path.join(ROOT, "data", "property-listings.json")
    if not os.path.exists(p):
        return out
    try:
        data = json.load(open(p))
    except (json.JSONDecodeError, OSError):
        return out
    listings = data.get("listings") or data.get("items") or []
    for li in listings:
        if not isinstance(li, dict):
            continue
        url = (li.get("url") or "").strip()
        title = (li.get("title") or "").strip()
        if not url or not title:
            continue
        price = li.get("price") or li.get("price_usd") or ""
        location = li.get("location") or li.get("suburb") or ""
        beds = li.get("bedrooms") or li.get("beds")
        baths = li.get("bathrooms") or li.get("baths")
        ptype = li.get("type") or li.get("category") or "property"
        agent = li.get("agent") or li.get("agency") or ""
        # Body — small editorial prose assembled from specs
        bits = []
        if price:
            bits.append(_fmt_usd(price) if isinstance(price, (int, float)) else str(price))
        spec_parts = []
        if beds:
            spec_parts.append(f"{beds} bedrooms")
        if baths:
            spec_parts.append(f"{baths} bathrooms")
        if spec_parts:
            bits.append(", ".join(spec_parts))
        if location:
            bits.append(str(location))
        body = " · ".join(bits) if bits else "Zimbabwe property listing"
        # Add the publisher description if present and short enough
        extra = (li.get("description") or li.get("summary") or "").strip()
        if extra:
            body = f"{body}.  {extra[:200]}"
        out.append({
            "url": url,
            "eyebrow": ptype.upper() if isinstance(ptype, str) else "PROPERTY",
            "headline": title,
            "body": body,
            "attribution": f"via {agent}" if agent else "via property.co.zw",
            "slug": None,
            "date": li.get("date") or li.get("publishedAt") or "",
        })
    return out


def collect_job_cards():
    """One story per active job + the three Mutapa internships."""
    out = []
    # Internships — each gets a rich pitch in the body so applicants
    # have everything they need from the Story alone.
    internships = [
        ("social-media", "Junior Social Media Assistant",
         "Help grow our social channels. Pitch fresh formats and ideas, spot trends, and shape how The Mutapa Times shows up across Instagram, Threads, X, TikTok and LinkedIn. Bring your own thinking — we like innovation.",
         "Fully remote · 3 days a week · 3 months · Rolling intake"),
        ("editorial", "Junior Editorial Coordinator",
         "Pitch, draft and edit original explainers and analysis. Fact-check stories, help shape the twice-weekly newsletter, and bring new editorial angles for telling Zimbabwean stories to a diaspora audience.",
         "Fully remote · 3 days a week · 3 months · Rolling intake"),
        ("data", "Junior Data Analyst",
         "Turn Zimbabwean public data into clear, visual stories. Extend the live economy briefing, prototype new ways to make numbers readable, and bring your own data ideas.",
         "Fully remote · 3 days a week · 3 months · Rolling intake"),
        ("biz-dev", "Business Development Associate",
         "Open doors for The Mutapa Times. Reach out to advertisers, sponsors and content partners across the Zim diaspora corridor — remittance, fintech, airlines, education — and build the revenue side of the publication. Bring your own contact list and ideas.",
         "Fully remote · 3 days a week · 3 months · Rolling intake"),
    ]
    # Internships are evergreen — stamp them with today's date every run
    # so they always pass the 30-day freshness gate. Self-bumping, no
    # monthly maintenance.
    intern_date = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    for slug, headline, body, attribution in internships:
        out.append({
            "url": f"https://mutapatimes.com/jobs#{slug}",
            "eyebrow": "INTERNSHIP — The Mutapa Times",
            "headline": headline,
            "body": body,
            "attribution": attribution,
            "slug": slug,
            "date": intern_date,
        })
    # External jobs
    p = os.path.join(ROOT, "data", "jobs.json")
    if not os.path.exists(p):
        return out
    try:
        data = json.load(open(p))
    except (json.JSONDecodeError, OSError):
        return out
    for j in (data.get("jobs") or []):
        url = (j.get("url") or "").strip()
        title = (j.get("title") or "").strip()
        if not url or not title:
            continue
        company = (j.get("company") or "").strip()
        loc = (j.get("location") or "").strip()
        jtype = (j.get("type") or "").strip()
        salary = (j.get("salary") or "").strip()
        summary = (j.get("summary") or "").strip()
        # Body: editorial prose if we have a summary, otherwise a spec list
        spec_bits = [b for b in [loc, jtype, salary] if b]
        if summary:
            body = summary
            if spec_bits:
                body = body + "  " + " · ".join(spec_bits)
        else:
            body = " · ".join(spec_bits) if spec_bits else ""
        out.append({
            "url": url,
            "eyebrow": (company or "JOB").upper(),
            "headline": title,
            "body": body,
            "attribution": "Apply via Vacancymail",
            "slug": None,
            "date": j.get("posted_at") or j.get("date") or "",
        })
    return out


# ── Pruning: drop cards whose URLs no longer appear in any source ──
def prune_stale(active_hashes):
    pruned = 0
    for path in glob.glob(os.path.join(OUT_DIR, "*.png")):
        name = os.path.splitext(os.path.basename(path))[0]
        if name not in active_hashes:
            try:
                os.remove(path)
                pruned += 1
            except OSError:
                pass
    return pruned


def main():
    # CLI flag: --force re-renders even cached cards. Useful after a
    # layout change (e.g. switching to a body-paragraph layout).
    force = "--force" in sys.argv

    print(f"=== BUILD STORY CARDS ({W}x{H}) ===")
    items = []
    items += collect_business_cards()
    items += collect_property_cards()
    items += collect_job_cards()
    raw_count = len(items)

    # Freshness gate — drop anything older than MAX_AGE_DAYS so old
    # archive articles stop keeping cards alive forever. Items with no
    # date (internships) pass through.
    items = [it for it in items if _is_fresh(it.get("date"))]
    stale = raw_count - len(items)
    print(f"  Collected {len(items)} fresh items "
          f"(business + property + jobs + internships)"
          + (f"  · dropped {stale} > {MAX_AGE_DAYS}d" if stale else "")
          + ("  [--force]" if force else ""))

    rendered = cached = failed = 0
    active = set()
    for it in items:
        h = card_hash(it["url"])
        active.add(h)
        out_path = os.path.join(OUT_DIR, f"{h}.png")
        if not force and os.path.exists(out_path):
            cached += 1
            continue
        try:
            render_story_card(
                eyebrow=it["eyebrow"],
                headline=it["headline"],
                body=it.get("body", ""),
                attribution=it.get("attribution", ""),
                output_path=out_path,
            )
            rendered += 1
        except Exception as e:
            failed += 1
            print(f"    FAIL {it['headline'][:48]}: {e}")

    pruned = prune_stale(active)
    print(f"  Rendered {rendered} new · Cached {cached} · Pruned {pruned} · Failed {failed}")
    print(f"  Output:  {OUT_DIR}")
    print("=== DONE ===")


if __name__ == "__main__":
    main()
