#!/usr/bin/env python3
"""
Build a daily Metricool import CSV from spotlight + category news JSONs.

Picks the top 5 unqueued articles, generates platform-specific captions
(LinkedIn, Facebook, Threads, Instagram), generates a 1080x1080 branded
headline card per article, and writes data/metricool-queue.csv.

The user reviews + imports the CSV via Metricool's Planner > Import CSV.
Headline cards are committed to img/cards/ and served by GitHub Pages.

Required env: GEMINI_API_KEY (optional — falls back to default captions).
Required pip dep: Pillow (for image generation).
"""
import csv
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("ERROR: Pillow not installed. Run: pip install Pillow", file=sys.stderr)
    sys.exit(1)

# Reuse the slug + URL helpers so the CSV points to the same /news/{slug}.html
# pages that build_news_pages.py creates.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_news_pages import landing_url as mutapa_landing_url  # noqa: E402

# ── Config ────────────────────────────────────────────────────
DATA_DIR = "data"
CARDS_DIR = "img/cards"
CARDS_PUBLIC_BASE = "https://www.mutapatimes.com/img/cards"

QUEUED_FILE = os.path.join(DATA_DIR, ".metricool_queued.json")
OUTPUT_CSV = os.path.join(DATA_DIR, "metricool-queue.csv")
SPOTLIGHT_FILE = os.path.join(DATA_DIR, "spotlight.json")
CATEGORY_FILES = ["business", "technology", "entertainment", "sports", "science", "health"]

ARTICLES_PER_DAY = 5
PRUNE_AFTER_DAYS = 30  # how long to keep dedup entries

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

# Per-platform posting times in CAT (UTC+2). Index = position in 5-article slate.
# Spread through the day using each platform's known good slots.
SCHEDULE_CAT = {
    "LinkedIn":  ["09:00", "10:30", "12:00", "13:30", "15:00"],
    "Facebook":  ["11:00", "13:00", "15:00", "17:00", "19:00"],
    "Threads":   ["12:00", "14:00", "16:00", "18:00", "20:00"],
    "Twitter":   ["08:00", "11:00", "13:00", "17:00", "20:00"],
    "Instagram": ["18:00", "19:30", "21:00", "10:00", "16:00"],  # IG less aggressive
}
CAT_OFFSET = timedelta(hours=2)  # CAT is UTC+2

# ── Headline card rendering ───────────────────────────────────
CARD_SIZE = 1080
CARD_BG = (13, 13, 13)
CARD_FG = (245, 245, 240)
ACCENT = (192, 57, 43)

# Font discovery — checks bundled fonts/ first, then OS-specific locations.
# Each role lists candidates from highest to lowest preference.
FONT_ROLES = {
    "serif_bold": [
        "fonts/PlayfairDisplay-Bold.ttf",
        # Linux (Ubuntu CI runner)
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
        # macOS
        "/System/Library/Fonts/Supplemental/Georgia Bold.ttf",
        "/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf",
    ],
    "sans": [
        "fonts/Inter-Medium.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ],
    "sans_bold": [
        "fonts/Inter-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    ],
}


def load_font(role, size):
    for path in FONT_ROLES.get(role, []):
        if os.path.isfile(path):
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    # Last resort: PIL default (tiny bitmap, but at least it runs)
    return ImageFont.load_default()


def wrap_text(text, font, max_width, draw):
    """Greedy word-wrap text to fit within max_width pixels."""
    words = text.split()
    lines = []
    line = []
    for word in words:
        test = " ".join(line + [word])
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_width:
            line.append(word)
        else:
            if line:
                lines.append(" ".join(line))
            line = [word]
    if line:
        lines.append(" ".join(line))
    return lines


def render_card(headline, source, output_path):
    """Generate a 1080x1080 branded headline card."""
    img = Image.new("RGB", (CARD_SIZE, CARD_SIZE), CARD_BG)
    draw = ImageDraw.Draw(img)

    # Top brand bar
    masthead_font = load_font("serif_bold", 38)
    headline_font = load_font("serif_bold", 64)
    source_font = load_font("sans", 24)
    label_font = load_font("sans_bold", 20)

    # Accent bar top-left
    draw.rectangle([(0, 0), (140, 8)], fill=ACCENT)

    # Masthead
    draw.text((60, 60), "THE MUTAPA TIMES", font=masthead_font, fill=CARD_FG)
    draw.text((60, 110), "Zimbabwe outside-in", font=source_font, fill=(160, 160, 155))

    # Headline (wrapped)
    available_width = CARD_SIZE - 120  # 60px margin both sides
    lines = wrap_text(headline, headline_font, available_width, draw)
    # Cap to 6 lines, ellipsize last if too long
    if len(lines) > 6:
        lines = lines[:5] + [lines[5] + "…"]

    # Vertical center the headline block
    line_height = 78
    block_h = len(lines) * line_height
    y = (CARD_SIZE - block_h) // 2 - 30
    for ln in lines:
        draw.text((60, y), ln, font=headline_font, fill=CARD_FG)
        y += line_height

    # Footer source attribution + read more cue
    footer_y = CARD_SIZE - 110
    draw.text((60, footer_y), "VIA", font=label_font, fill=(120, 120, 115))
    draw.text((60, footer_y + 26), source.upper(), font=source_font, fill=CARD_FG)
    cue = "READ MORE → mutapatimes.com"
    bbox = draw.textbbox((0, 0), cue, font=source_font)
    cue_w = bbox[2] - bbox[0]
    draw.text((CARD_SIZE - 60 - cue_w, footer_y + 26), cue,
              font=source_font, fill=ACCENT)

    img.save(output_path, "PNG", optimize=True)


# ── Data loading ──────────────────────────────────────────────
def load_articles():
    """Load articles from spotlight + categories, deduped by URL."""
    seen = set()
    out = []

    def take(filepath, source_label):
        if not os.path.isfile(filepath):
            return
        try:
            data = json.load(open(filepath))
        except (json.JSONDecodeError, IOError):
            return
        for a in data.get("articles", []):
            url = (a.get("url") or "").strip()
            if not url or url in seen:
                continue
            seen.add(url)
            # source is sometimes a string (spotlight), sometimes {name, url} (categories)
            src = a.get("source") or ""
            if isinstance(src, dict):
                src = src.get("name", "")
            out.append({
                "title": (a.get("title") or "").strip(),
                "description": (a.get("description") or "").strip(),
                "url": url,
                "image": (a.get("image") or "").strip(),
                "source": str(src).strip(),
                "category": source_label,
                "publishedAt": a.get("publishedAt") or "",
            })

    take(SPOTLIGHT_FILE, "spotlight")
    for cat in CATEGORY_FILES:
        take(os.path.join(DATA_DIR, f"{cat}.json"), cat)
    return out


def load_queued():
    if not os.path.isfile(QUEUED_FILE):
        return {}
    try:
        return json.load(open(QUEUED_FILE))
    except (json.JSONDecodeError, IOError):
        return {}


def save_queued(queued):
    cutoff = (datetime.now(timezone.utc) - timedelta(days=PRUNE_AFTER_DAYS)).isoformat()
    pruned = {k: v for k, v in queued.items() if v >= cutoff}
    with open(QUEUED_FILE, "w") as f:
        json.dump(pruned, f, indent=2)


# ── Caption generation (Gemini, with fallback) ────────────────
_SHARED_RULES = (
    "RULES (must follow):\n"
    " - The clickable URL in the post MUST be the MUTAPA_URL (the Mutapa Times "
    "landing page). DO NOT include the SOURCE_URL anywhere in the post.\n"
    " - Always credit the original publisher in the text using the phrase "
    "'via {SOURCE_NAME}' (or similar). Never omit credit.\n"
    " - Do not invent facts not in the headline or description."
)

PROMPTS = {
    "LinkedIn": (
        "Rewrite this Zimbabwe news headline as a LinkedIn post. "
        "Professional tone, lead with the most newsworthy fact, no emojis, "
        "100-180 chars of body text. Credit the source inline with 'via {SOURCE_NAME}'. "
        "End with the MUTAPA_URL on a new line. "
        "Add 2-3 relevant hashtags on a final new line.\n\n"
        + _SHARED_RULES
    ),
    "Facebook": (
        "Rewrite this Zimbabwe news headline as a Facebook post. "
        "Warm, community-framed tone, plain language, 1-2 short sentences "
        "(max 200 chars). Credit the source as 'via {SOURCE_NAME}'. "
        "Then the MUTAPA_URL on a new line. No hashtags.\n\n"
        + _SHARED_RULES
    ),
    "Threads": (
        "Rewrite this Zimbabwe news headline as a Threads post. "
        "Punchy, conversational, max 480 chars. Credit the source with "
        "'via {SOURCE_NAME}' inline. End with the MUTAPA_URL on a new line. "
        "Optionally one line of 1-2 hashtags.\n\n"
        + _SHARED_RULES
    ),
    "Twitter": (
        "Rewrite this Zimbabwe news headline as an X/Twitter post. "
        "STRICT 280 character TOTAL limit including URL — URLs count as 23 "
        "chars regardless of length. Sharp, newsy, no fluff. Lead with the "
        "fact, credit the source as 'via {SOURCE_NAME}'. Append the "
        "MUTAPA_URL on a new line. Optionally end with one hashtag like "
        "#Zimbabwe. Do not exceed 280 chars.\n\n"
        + _SHARED_RULES
    ),
    "Instagram": (
        "Rewrite this Zimbabwe news headline as an Instagram caption. "
        "Hook in the first line (under 100 chars). "
        "Then a short body (1-2 sentences) crediting the source as "
        "'via {SOURCE_NAME}'. "
        "End with: 'Read the full story → mutapatimes.com (link in bio)' on its own line. "
        "Then 5-8 relevant hashtags on a final line.\n\n"
        + _SHARED_RULES
    ),
}


def gemini_rewrite(prompt, headline, description, source, mutapa_url, source_url):
    """Call Gemini to rewrite. Returns string or None on failure."""
    if not GEMINI_API_KEY:
        return None
    user_msg = (
        f"{prompt}\n\n"
        f"HEADLINE: {headline}\n"
        f"DESCRIPTION: {description or '(none)'}\n"
        f"SOURCE_NAME: {source}\n"
        f"MUTAPA_URL: {mutapa_url}\n"
        f"SOURCE_URL (for your reference only — DO NOT include this in the post): {source_url}\n\n"
        f"Output ONLY the post text, no commentary."
    )
    body = {
        "contents": [{"role": "user", "parts": [{"text": user_msg}]}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 400},
    }
    req = urllib.request.Request(
        f"{GEMINI_URL}?key={GEMINI_API_KEY}",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.load(resp)
        candidates = data.get("candidates", [])
        if not candidates:
            return None
        parts = candidates[0].get("content", {}).get("parts", [])
        if not parts:
            return None
        return parts[0].get("text", "").strip()
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, KeyError):
        return None


def fallback_caption(platform, headline, source, mutapa_url):
    """Plain template if Gemini is unavailable. Always uses Mutapa URL +
    credits the source by name in the body text."""
    src = source or "the original publisher"
    if platform == "LinkedIn":
        return (f"{headline}\n\nvia {src}\n\n{mutapa_url}\n\n"
                f"#Zimbabwe #News #Africa")
    if platform == "Facebook":
        return f"{headline}\n\nvia {src}. Read more: {mutapa_url}"
    if platform == "Threads":
        return f"{headline}\n\nvia {src}\n{mutapa_url}"
    if platform == "Twitter":
        # 280 char budget; URLs count as 23 via t.co. Reserve URL (23) +
        # newline (1) + " via {src}" (≈ 5 + len(src)) + safety margin.
        attribution = f" via {src}"
        OVERHEAD = 23 + 2 + len(attribution) + 4
        title = headline
        if len(title) + OVERHEAD > 280:
            title = title[: 280 - OVERHEAD - 1].rstrip() + "…"
        return f"{title}{attribution}\n{mutapa_url}"
    if platform == "Instagram":
        return (f"{headline}\n\nThe full story via {src}.\n\n"
                f"Read more → mutapatimes.com (link in bio)\n\n"
                f"#Zimbabwe #ZimbabweNews #Africa #News #DiasporaNews")
    return headline


def _twitter_safe(text, mutapa_url, source):
    """Enforce X's 280-char limit. URLs count as 23 chars (t.co)."""
    if not text:
        return text
    url_pattern = re.compile(r"https?://\S+")
    sentinel = "x" * 23
    measured = url_pattern.sub(sentinel, text)
    if len(measured) <= 280:
        return text
    # Reflow: keep title + ' via {source}' + mutapa URL only
    body = url_pattern.sub("", text).strip()
    body = re.sub(r"\s+", " ", body)
    src = source or "the publisher"
    attribution = f" via {src}"
    OVERHEAD = 23 + 2 + len(attribution) + 4
    if len(body) + OVERHEAD > 280:
        body = body[: 280 - OVERHEAD - 1].rstrip() + "…"
    return f"{body}{attribution}\n{mutapa_url}"


def caption_for(platform, art, mutapa_url):
    rewritten = gemini_rewrite(
        PROMPTS[platform],
        art["title"],
        art["description"],
        art["source"],
        mutapa_url,
        art["url"],
    )
    text = rewritten or fallback_caption(platform, art["title"], art["source"], mutapa_url)
    if platform == "Twitter":
        text = _twitter_safe(text, mutapa_url, art["source"])
    return text


# ── Slug + scheduling helpers ─────────────────────────────────
def slugify(s, max_len=60):
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    if len(s) > max_len:
        s = s[:max_len].rstrip("-")
    return s or "post"


def schedule_for(platform, slot_index, run_date_utc):
    """Compute UTC datetime for a post given platform + slot."""
    cat_time = SCHEDULE_CAT[platform][slot_index % len(SCHEDULE_CAT[platform])]
    h, m = map(int, cat_time.split(":"))
    cat_dt = datetime(run_date_utc.year, run_date_utc.month, run_date_utc.day,
                      h, m, tzinfo=timezone(CAT_OFFSET))
    return cat_dt.astimezone(timezone.utc)


# ── Main ──────────────────────────────────────────────────────
def main():
    print("=== BUILD METRICOOL CSV ===")
    if not GEMINI_API_KEY:
        print("  WARN: GEMINI_API_KEY not set — using fallback templates.")

    queued = load_queued()
    print(f"  Tracking {len(queued)} previously queued URLs")

    articles = load_articles()
    print(f"  Loaded {len(articles)} unique articles")

    new_articles = [a for a in articles if a["url"] not in queued]
    print(f"  {len(new_articles)} new (not yet queued)")

    if not new_articles:
        print("  Nothing new to queue. Done.")
        # Still write an empty CSV so importers don't choke
        with open(OUTPUT_CSV, "w", encoding="utf-8") as f:
            csv.writer(f).writerow(["caption", "date", "time", "networks", "media_url", "post_type"])
        return

    selected = new_articles[:ARTICLES_PER_DAY]
    print(f"  Selected top {len(selected)} for this run")

    os.makedirs(CARDS_DIR, exist_ok=True)
    today_utc = datetime.now(timezone.utc).date()
    rows = []

    for idx, art in enumerate(selected):
        print(f"\n  [{idx + 1}/{len(selected)}] {art['title'][:70]}")

        # Mutapa Times landing page URL — the link every social post drives to
        mutapa_url = mutapa_landing_url(art)
        print(f"    Landing: {mutapa_url}")

        # Build a stable slug for the card filename
        url_hash = hashlib.md5(art["url"].encode("utf-8")).hexdigest()[:6]
        slug = f"{slugify(art['title'])}-{url_hash}"
        card_path = os.path.join(CARDS_DIR, f"{slug}.png")
        card_url = f"{CARDS_PUBLIC_BASE}/{slug}.png"

        # Render the headline card (used for IG; available for others if you want)
        try:
            render_card(art["title"], art["source"], card_path)
            print(f"    Card: {card_path}")
        except Exception as e:
            print(f"    Card FAILED: {e}")
            card_url = ""

        # One row per platform
        for platform in ("LinkedIn", "Facebook", "Threads", "Twitter", "Instagram"):
            print(f"    Captioning for {platform}…", end=" ", flush=True)
            caption = caption_for(platform, art, mutapa_url)
            print("OK" if caption else "FAIL")

            sched_utc = schedule_for(platform, idx,
                                     datetime.combine(today_utc, datetime.min.time()))
            # Push tomorrow if today's slot has already passed
            if sched_utc <= datetime.now(timezone.utc):
                sched_utc += timedelta(days=1)

            # IG must use the headline card; others use the article image (or card if missing)
            if platform == "Instagram":
                media = card_url
            else:
                media = art["image"] or card_url

            rows.append({
                "caption": caption,
                "date": sched_utc.strftime("%Y-%m-%d"),
                "time": sched_utc.strftime("%H:%M"),
                "networks": platform,
                "media_url": media,
                "post_type": "image" if media else "text",
            })

            # Mild rate limit on Gemini
            time.sleep(0.4)

        queued[art["url"]] = datetime.now(timezone.utc).isoformat()

    # Write CSV
    fieldnames = ["caption", "date", "time", "networks", "media_url", "post_type"]
    with open(OUTPUT_CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print(f"\n  Wrote {OUTPUT_CSV} ({len(rows)} rows)")

    save_queued(queued)
    print("\n=== DONE ===")


if __name__ == "__main__":
    main()
