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

# How many days of content this run should cover (Mon = 3, Thu = 4, manual = 1).
# Used to size the article slate so the queue stretches to the next run.
DAYS_BY_WEEKDAY = {0: 3, 3: 4}  # Mon, Thu

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

# ── Metricool CSV format ──────────────────────────────────────
# Mirrors Metricool's import template (data/metricool-template-reference.csv).
# DO NOT REORDER — Metricool relies on column position for some imports.
METRICOOL_COLUMNS = [
    "Text", "Date", "Time", "Draft",
    "Facebook", "Twitter/X", "LinkedIn", "GBP", "Instagram",
    "Pinterest", "TikTok", "Youtube", "Threads", "Bluesky",
    "Picture Url 1", "Picture Url 2", "Picture Url 3", "Picture Url 4", "Picture Url 5",
    "Picture Url 6", "Picture Url 7", "Picture Url 8", "Picture Url 9", "Picture Url 10",
    "Alt text picture 1", "Alt text picture 2", "Alt text picture 3", "Alt text picture 4", "Alt text picture 5",
    "Alt text picture 6", "Alt text picture 7", "Alt text picture 8", "Alt text picture 9", "Alt text picture 10",
    "Document title", "Shortener",
    "Video Thumbnail Url", "Video Cover Frame",
    "Twitter/X Can reply", "Twitter/X Type",
    "Twitter/X Poll Duration minutes",
    "Twitter/X Poll Option 1", "Twitter/X Poll Option 2",
    "Twitter/X Poll Option 3", "Twitter/X Poll Option 4",
    "Pinterest Board", "Pinterest Pin Title", "Pinterest Pin Link", "Pinterest Pin New Format",
    "Instagram Post Type", "Instagram Show Reel On Feed",
    "Youtube Video Title", "Youtube Video Type", "Youtube Video Privacy",
    "Youtube video for kids", "Youtube Video Category", "Youtube Video Tags", "Youtube playlist",
    "GBP Post Type",
    "Facebook Post Type", "Facebook Title", "First Comment Text",
    "TikTok Title",
    "TikTok disable comments", "TikTok disable duet", "TikTok disable stitch",
    "TikTok Post Privacy", "TikTok Branded Content", "TikTok Your Brand",
    "TikTok Auto Add Music", "TikTok Photo Cover Index",
    "TikTok musicId", "TikTok music title", "TikTok music author",
    "TikTok music previewUrl", "TikTok music thumbnailUrl",
    "TikTok music soundVolume", "TikTok music originalVolume",
    "TikTok music startMillis", "TikTok music endMillis",
    "TikTok Ai generated content",
    "LinkedIn Type", "LinkedIn Poll Question",
    "LinkedIn Poll Option 1", "LinkedIn Poll Option 2",
    "LinkedIn Poll Option 3", "LinkedIn Poll Option 4",
    "LinkedIn Poll Duration",
    "LinkedIn Show link preview", "LinkedIn Images as Carousel",
    "Threads Reply Control", "Threads Is Spoiler", "Threads Post Type",
    "Brand name",
]

# Map internal platform identifier → Metricool boolean column to flip "true"
PLATFORM_TO_FLAG = {
    "LinkedIn": "LinkedIn",
    "Facebook": "Facebook",
    "Threads": "Threads",
    "Twitter": "Twitter/X",
    "Instagram": "Instagram",
}

# All boolean platform columns — used to default-zero each row
PLATFORM_FLAGS = [
    "Facebook", "Twitter/X", "LinkedIn", "GBP", "Instagram",
    "Pinterest", "TikTok", "Youtube", "Threads", "Bluesky",
]

BRAND_NAME = os.environ.get("METRICOOL_BRAND_NAME", "")
SUBSCRIBE_URL = "https://www.mutapatimes.com/subscribe.html"

# ── Evening-mode override (ad-hoc smoke-test runs) ────────────
EVENING_START_CAT = os.environ.get("METRICOOL_EVENING_START", "")
EVENING_ARTICLES = int(os.environ.get("METRICOOL_EVENING_ARTICLES", "2"))
EVENING_INTERVAL_MIN = int(os.environ.get("METRICOOL_EVENING_INTERVAL", "30"))
PLATFORMS_ORDERED = ("LinkedIn", "Facebook", "Threads", "Twitter", "Instagram")

# ── Newsletter-driver posts ───────────────────────────────────
# 4 distinct value propositions per run × 5 platforms = 20 sub posts/run.
# Rotated through different angles to avoid repetition fatigue.
NEWSLETTER_ANGLES = [
    {
        "key": "curation",
        "headline": "30+ sources, one briefing",
        "core": (
            "Sell the editorial curation. The pitch: 'We read The Guardian, "
            "Reuters, NYT, Bloomberg, Al Jazeera, the Herald, and 30+ other "
            "outlets so you don't have to.' Filter down to the ~10-15 "
            "stories that genuinely matter for Zimbabwe each week."
        ),
    },
    {
        "key": "time",
        "headline": "5 minutes. Twice a week.",
        "core": (
            "Sell the time-saving. The pitch: '5-minute briefing, Mondays "
            "and Thursdays. No fluff, no 14 tabs to keep open.' Aimed at "
            "busy professionals who want to stay informed in minimum time."
        ),
    },
    {
        "key": "diaspora",
        "headline": "Zimbabwe outside-in",
        "core": (
            "Sell belonging. The pitch: 'For Zimbabweans living abroad — in "
            "the UK, US, SA, Australia. Stay connected to Harare, Bulawayo, "
            "the economy, the rugby squad, the music charts. From wherever "
            "you are.' Emotional, identity-first."
        ),
    },
    {
        "key": "insider",
        "headline": "Know what's moving — first",
        "core": (
            "Sell the analytical edge. The pitch: 'For analysts, investors, "
            "journalists, NGO/dev workers tracking Zimbabwe. Lithium bans, "
            "ZiG monetary policy, mining licenses, Cabinet shuffles — "
            "before the herd catches up.' Authoritative, dry, factual."
        ),
    },
]

# Off-peak slot for newsletter posts so they don't collide with article slots.
NEWSLETTER_SLOT_CAT = "16:30"
NEWSLETTER_SLOT_EVENING_CAT = "19:30"

# Promo card filenames (one per angle, regenerated on first run, then static)
PROMO_CARDS_DIR = "img/cards"
PROMO_CARD_BASE = "https://www.mutapatimes.com/img/cards"

# ── Headline card rendering ───────────────────────────────────
CARD_W = 1080
CARD_H = 1350  # portrait 4:5 — Instagram-optimal
CARD_FG = (26, 26, 26)         # ink — dark text on light bg
CARD_FG_MUTED = (95, 92, 84)   # secondary text
ACCENT = (192, 57, 43)         # brand red

# Brand-appropriate faded palette — rotated per card so the feed looks varied
# but stays consistent. Each tone is muted/dusty, paper-like.
CARD_BACKGROUNDS = [
    (242, 218, 213),  # faded red — warm dusty rose
    (216, 230, 213),  # faded green — sage
    (245, 232, 200),  # faded yellow — soft butter
    (236, 226, 207),  # faded beige — warm cream
]


def card_bg(index):
    return CARD_BACKGROUNDS[index % len(CARD_BACKGROUNDS)]

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


def render_card(headline, source, output_path, color_idx=0):
    """Generate a 1080x1350 portrait headline card with rotating bg color."""
    bg = card_bg(color_idx)
    img = Image.new("RGB", (CARD_W, CARD_H), bg)
    draw = ImageDraw.Draw(img)

    masthead_font = load_font("serif_bold", 42)
    headline_font = load_font("serif_bold", 78)
    source_font = load_font("sans", 28)
    label_font = load_font("sans_bold", 22)

    # Accent bar top-left
    draw.rectangle([(0, 0), (140, 10)], fill=ACCENT)

    # Masthead
    draw.text((60, 70), "THE MUTAPA TIMES", font=masthead_font, fill=CARD_FG)
    draw.text((60, 124), "Zimbabwe outside-in", font=source_font, fill=CARD_FG_MUTED)

    # Headline (wrapped, vertically centered in the middle band)
    available_width = CARD_W - 120
    lines = wrap_text(headline, headline_font, available_width, draw)
    if len(lines) > 7:
        lines = lines[:6] + [lines[6] + "…"]

    line_height = 96
    block_h = len(lines) * line_height
    # Center between header (~210px) and footer (~150px from bottom)
    available_h = CARD_H - 360
    y = 230 + (available_h - block_h) // 2
    for ln in lines:
        draw.text((60, y), ln, font=headline_font, fill=CARD_FG)
        y += line_height

    # Footer source attribution + read more cue
    footer_y = CARD_H - 140
    draw.text((60, footer_y), "VIA", font=label_font, fill=CARD_FG_MUTED)
    draw.text((60, footer_y + 32), source.upper(), font=source_font, fill=CARD_FG)
    cue = "READ MORE → mutapatimes.com"
    bbox = draw.textbbox((0, 0), cue, font=source_font)
    cue_w = bbox[2] - bbox[0]
    draw.text((CARD_W - 60 - cue_w, footer_y + 32), cue,
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
    "HARD RULES (must follow):\n"
    " - The clickable URL MUST be the MUTAPA_URL. NEVER include SOURCE_URL.\n"
    " - Always credit the publisher inline with 'via {SOURCE_NAME}' or "
    "similar attribution. Never omit credit.\n"
    " - Never invent facts not in the headline/description. If the description "
    "is empty, stick strictly to what the headline says.\n"
    " - HASHTAGS must be DERIVED FROM THE SPECIFIC HEADLINE TOPIC, not just "
    "generic. Examples: a lithium-export story → #Lithium #Mining #Zimbabwe; "
    "a cricket match story → #Cricket #ZimCricket #Zimbabwe; a Mnangagwa "
    "policy story → #Mnangagwa #ZanuPF #Zimbabwe; a Harare infrastructure "
    "story → #Harare #Infrastructure #Zimbabwe. ALWAYS include #Zimbabwe as "
    "the anchor tag, plus 2-3 specific topic tags chosen from the headline.\n"
    " - The post is for The Mutapa Times — a Zimbabwe news outlet for the "
    "diaspora. Audience is informed, mostly Zimbabwean or Africa-watchers.\n"
    " - Do NOT use clickbait phrases like 'You won't believe', 'This will "
    "shock you', 'BREAKING:' (unless genuinely breaking), all-caps shouting.\n"
    " - Output ONLY the post text. No commentary, no markdown code fences."
)

PROMPTS = {
    "LinkedIn": (
        "Write a LinkedIn post about this Zimbabwe news story to maximise "
        "engagement and reach professional readers (diaspora, Africa "
        "investors, journalists, NGO/dev workers).\n\n"
        "STRUCTURE (in order, with line breaks between):\n"
        "  1. HOOK line (under 90 chars) — a sharp, surprising fact OR an "
        "implication, NOT just the headline restated.\n"
        "  2. CONTEXT (1-2 short paragraphs) — why this matters, who it "
        "affects, the underlying tension. Use specifics from the description.\n"
        "  3. INVITATION line — open question OR 'What this means for X:' "
        "framing. Encourages comments.\n"
        "  4. Attribution: 'Source: {SOURCE_NAME}' on its own line.\n"
        "  5. The MUTAPA_URL on its own line.\n"
        "  6. 3-5 hashtags on the final line, mixing #Zimbabwe with one "
        "topic-specific tag (#Mining, #Lithium, #ICT, #Education, etc.).\n\n"
        "TONE: Confident, analytical, no emojis (or at most one 🇿🇼 in hook). "
        "Length: 350-700 chars. Don't pad — be punchy.\n\n"
        + _SHARED_RULES
    ),
    "Facebook": (
        "Write a Facebook Page post about this Zimbabwe news story for a "
        "general diaspora + Zimbabwean audience.\n\n"
        "STRUCTURE:\n"
        "  1. HOOK (one short sentence) — emotional or relatable framing, "
        "NOT just the headline. Examples: 'Big news for Zim's mining sector.' "
        "or 'Something's shifting in Bulawayo.'\n"
        "  2. BODY (2-3 sentences) — explain plainly what happened and "
        "why it matters. Conversational, like talking to a friend.\n"
        "  3. ENGAGEMENT prompt — a clear question to invite comments. "
        "Examples: 'What do you think?' 'Have you noticed this?' "
        "'Tag someone who needs to see this.'\n"
        "  4. 'via {SOURCE_NAME}' on its own line.\n"
        "  5. The MUTAPA_URL on its own line.\n\n"
        "TONE: Warm, plain language, conversational. NO hashtags (Facebook "
        "doesn't reward them). Light emoji OK (1 max). Length: 200-450 chars.\n\n"
        + _SHARED_RULES
    ),
    "Threads": (
        "Write a Threads post about this Zimbabwe news story. Threads "
        "rewards casual, opinion-tinged voice — like a smart friend sharing "
        "a take. Audience skews younger and more conversational.\n\n"
        "STRUCTURE:\n"
        "  1. HOOK (under 80 chars) — your TAKE on the news, framed casually. "
        "Examples: 'Zim just made a huge bet on lithium 🇿🇼' or "
        "'Watching this unfold in real time…'\n"
        "  2. CONTEXT (1-2 short lines, line breaks between) — the key facts.\n"
        "  3. ANGLE — what's interesting/risky/surprising about it.\n"
        "  4. 'via {SOURCE_NAME}' on its own line.\n"
        "  5. The MUTAPA_URL on its own line.\n"
        "  6. (Optional) 1-2 hashtags on a final line.\n\n"
        "TONE: Slightly opinionated, conversational, has a point of view. "
        "1-2 emojis OK. Max 480 chars. Use line breaks generously.\n\n"
        + _SHARED_RULES
    ),
    "Twitter": (
        "Write an X/Twitter post about this Zimbabwe news story. X rewards "
        "speed, sharpness, and a clear angle. Strict 280 char limit including "
        "URL (URLs count as 23 chars regardless of length).\n\n"
        "STRUCTURE:\n"
        "  1. HOOK line — the most newsworthy fact or implication. NOT a "
        "verbatim headline restate. Get to the point.\n"
        "  2. (Optional) one line of context if the hook needs unpacking.\n"
        "  3. Inline attribution: 'via {SOURCE_NAME}' (or '— {SOURCE_NAME}').\n"
        "  4. MUTAPA_URL on its own line.\n"
        "  5. MANDATORY: 2-3 hashtags on the LAST line. Must include "
        "#Zimbabwe plus 1-2 headline-specific topic tags. Examples: "
        "#Zimbabwe #Lithium #Mining for a mining story.\n\n"
        "TONE: Sharp, factual, slight POV welcome. No emoji unless adds info. "
        "ABSOLUTE max 280 chars total (URL = 23). Be concise — count chars.\n\n"
        + _SHARED_RULES
    ),
    "Instagram": (
        "Write an Instagram caption about this Zimbabwe news story. IG "
        "rewards story-style captions where the first line is a hook because "
        "the rest is hidden behind 'more'.\n\n"
        "STRUCTURE:\n"
        "  1. HOOK (FIRST LINE, under 100 chars) — must work standalone in "
        "the feed preview. Surprising, emotional, or curiosity-inducing.\n"
        "  2. STORY (2-3 short paragraphs with line breaks between) — "
        "tell the story: what happened, who it affects, why it matters. "
        "Use specifics. Don't summarize — narrate.\n"
        "  3. CTA line: 'Read the full briefing → mutapatimes.com (link in bio)'.\n"
        "  4. 'via {SOURCE_NAME}' on its own line.\n"
        "  5. Final line: 8-12 hashtags mixing core (#Zimbabwe #ZimbabweNews "
        "#Africa #ZimDiaspora) with topic-specific tags relevant to the story "
        "(e.g. #Mining #Lithium #Harare #Bulawayo). Separate with spaces.\n\n"
        "TONE: Story-driven, emotive without being saccharine. 1-3 emojis OK "
        "in body. Length: 600-1100 chars (IG allows 2200, but ~800 is the "
        "engagement sweet spot). NEVER include the URL inline — IG strips it.\n\n"
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


# ── Headline → topic hashtags (used by fallback templates) ────
# Keyword-to-tag map. First word match wins (sorted longest-first below).
TOPIC_HASHTAG_MAP = {
    "lithium": "#Lithium",
    "mining": "#Mining",
    "minerals": "#Mining",
    "gold": "#Gold",
    "diamond": "#Diamonds",
    "platinum": "#Mining",
    "tobacco": "#Tobacco",
    "cricket": "#Cricket",
    "rugby": "#Rugby",
    "afcon": "#AFCON",
    "football": "#Football",
    "soccer": "#Football",
    "warriors": "#Warriors",
    "zifa": "#ZIFA",
    "election": "#ZimbabweElections",
    "mnangagwa": "#Mnangagwa",
    "zanu-pf": "#ZanuPF",
    "zanu pf": "#ZanuPF",
    "ccc": "#CCC",
    "chamisa": "#Chamisa",
    "parliament": "#ZimParliament",
    "harare": "#Harare",
    "bulawayo": "#Bulawayo",
    "mutare": "#Mutare",
    "victoria falls": "#VicFalls",
    "zig": "#ZiG",
    "currency": "#ZiG",
    "inflation": "#Economy",
    "rbz": "#RBZ",
    "reserve bank": "#RBZ",
    "ecocash": "#FinTech",
    "telecel": "#Telecoms",
    "econet": "#Telecoms",
    "diaspora": "#Diaspora",
    "tourism": "#Tourism",
    "music": "#ZimMusic",
    "sungura": "#Sungura",
    "education": "#Education",
    "health": "#Health",
    "hospital": "#Health",
    "drought": "#Climate",
    "climate": "#Climate",
    "flood": "#Climate",
    "trade": "#Trade",
    "exports": "#Trade",
    "imports": "#Trade",
    "ai ": "#AI",
    "tech": "#Tech",
    "ict": "#ICT",
    "court": "#Justice",
    "police": "#Crime",
    "arrest": "#Crime",
    "wildlife": "#Wildlife",
    "rhino": "#Wildlife",
    "elephant": "#Wildlife",
    "lion": "#Wildlife",
}


def topic_hashtags(headline, max_tags=3):
    """Pick #Zimbabwe + up to (max_tags-1) topic-specific tags from the
    headline. Falls back to #Africa #News if nothing matches."""
    h = headline.lower()
    found = ["#Zimbabwe"]
    # Sort keys by length desc so multi-word keys win over substrings
    for keyword in sorted(TOPIC_HASHTAG_MAP.keys(), key=len, reverse=True):
        if len(found) >= max_tags:
            break
        if keyword in h:
            tag = TOPIC_HASHTAG_MAP[keyword]
            if tag not in found:
                found.append(tag)
    while len(found) < max_tags:
        for fallback in ("#Africa", "#News", "#Diaspora"):
            if fallback not in found:
                found.append(fallback)
                break
        else:
            break
    return " ".join(found)


def fallback_caption(platform, headline, description, source, mutapa_url):
    """Used when Gemini is unavailable. Tries to be reasonably engaging
    even without AI rewriting — uses description for context if present."""
    src = source or "the original publisher"
    summary = (description or "").strip()
    if len(summary) > 200:
        summary = summary[:199].rstrip() + "…"

    # Headline-derived hashtags (3 tags for short posts, 4 for X)
    short_tags = topic_hashtags(headline, max_tags=3)

    if platform == "LinkedIn":
        body_lines = [headline]
        if summary:
            body_lines.append("")
            body_lines.append(summary)
        body_lines += [
            "",
            "What does this mean for Zimbabwe? Share your thoughts below.",
            "",
            f"Source: {src}",
            mutapa_url,
            "",
            short_tags,
        ]
        return "\n".join(body_lines)

    if platform == "Facebook":
        body = headline
        if summary:
            body += f"\n\n{summary}"
        body += "\n\nWhat do you think?\n"
        body += f"\nvia {src}\n{mutapa_url}"
        return body

    if platform == "Threads":
        body = headline
        if summary:
            body += f"\n\n{summary}"
        body += f"\n\nvia {src}\n{mutapa_url}\n\n{short_tags}"
        return body

    if platform == "Twitter":
        # Strict 280-char budget with t.co URL counting as 23. We budget the
        # URL (23) + " via {src}" + headline + 2 newlines + hashtag line.
        tags = short_tags  # e.g. "#Zimbabwe #Lithium #Mining"
        attribution = f" via {src}"
        OVERHEAD = 23 + 4 + len(attribution) + len(tags) + 4
        title = headline
        if len(title) + OVERHEAD > 280:
            title = title[: 280 - OVERHEAD - 1].rstrip() + "…"
        return f"{title}{attribution}\n{mutapa_url}\n\n{tags}"

    if platform == "Instagram":
        # IG gets a richer hashtag set — 8-10 tags for discovery, deduped
        topic = topic_hashtags(headline, max_tags=4).split()
        discovery = ["#ZimbabweNews", "#Africa", "#ZimDiaspora",
                     "#ZimbabweanDiaspora", "#AfricaNews", "#News"]
        seen = set(t.lower() for t in topic)
        ig_tags_list = list(topic)
        for t in discovery:
            if t.lower() not in seen:
                ig_tags_list.append(t)
                seen.add(t.lower())
        ig_tags = " ".join(ig_tags_list)
        body = headline
        if summary:
            body += f"\n\n{summary}"
        body += "\n\nRead the full briefing → mutapatimes.com (link in bio)"
        body += f"\nvia {src}"
        body += f"\n\n{ig_tags}"
        return body

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
    text = rewritten or fallback_caption(
        platform, art["title"], art["description"], art["source"], mutapa_url
    )
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


def schedule_for(platform, article_idx, run_date_utc):
    """Compute UTC datetime for a post.

    Default: articles spread across multiple days using SCHEDULE_CAT slots.
    Evening-mode override (EVENING_START_CAT set): all posts staggered
    tonight from EVENING_START_CAT, 5 min apart per platform, INTERVAL apart
    per article.
    """
    if EVENING_START_CAT:
        h, m = map(int, EVENING_START_CAT.split(":"))
        plat_off = PLATFORMS_ORDERED.index(platform) * 5
        total_min = (article_idx * EVENING_INTERVAL_MIN) + plat_off
        cat_dt = datetime(run_date_utc.year, run_date_utc.month, run_date_utc.day,
                          h, m, tzinfo=timezone(CAT_OFFSET)) + timedelta(minutes=total_min)
        return cat_dt.astimezone(timezone.utc)

    day_offset = article_idx // ARTICLES_PER_DAY
    slot_in_day = article_idx % ARTICLES_PER_DAY
    cat_time = SCHEDULE_CAT[platform][slot_in_day]
    h, m = map(int, cat_time.split(":"))
    target_date = run_date_utc + timedelta(days=day_offset)
    cat_dt = datetime(target_date.year, target_date.month, target_date.day,
                      h, m, tzinfo=timezone(CAT_OFFSET))
    return cat_dt.astimezone(timezone.utc)


def articles_for_this_run():
    """Pick the slate size based on the run mode."""
    if EVENING_START_CAT:
        return EVENING_ARTICLES
    weekday = datetime.now(timezone.utc).weekday()
    days = DAYS_BY_WEEKDAY.get(weekday, 1)
    return days * ARTICLES_PER_DAY


# ── Newsletter promo cards ────────────────────────────────────
def render_promo_card(angle, output_path, color_idx=0):
    """Generate a 1080x1350 portrait newsletter-promo card for one angle."""
    bg = card_bg(color_idx)
    img = Image.new("RGB", (CARD_W, CARD_H), bg)
    draw = ImageDraw.Draw(img)

    title_font = load_font("serif_bold", 108)
    sub_font = load_font("sans", 30)
    masthead_font = load_font("serif_bold", 36)
    cta_font = load_font("sans_bold", 24)

    # Accent bar
    draw.rectangle([(0, 0), (140, 10)], fill=ACCENT)
    draw.text((60, 70), "THE MUTAPA TIMES", font=masthead_font, fill=CARD_FG)
    draw.text((60, 120), "BRIEFING — FREE NEWSLETTER", font=cta_font, fill=ACCENT)

    # Big headline (centered)
    headline = angle["headline"]
    lines = wrap_text(headline, title_font, CARD_W - 120, draw)
    line_h = 130
    block_h = len(lines) * line_h
    y = (CARD_H - block_h) // 2 - 30
    for ln in lines:
        draw.text((60, y), ln, font=title_font, fill=CARD_FG)
        y += line_h

    # Sub text (under headline)
    sub_lines = [
        "Curated Zimbabwe news from foreign press.",
        "Mondays + Thursdays. 5-minute read.",
    ]
    sy = y + 18
    for sl in sub_lines:
        draw.text((60, sy), sl, font=sub_font, fill=CARD_FG_MUTED)
        sy += 44

    # Bottom CTA
    cta_y = CARD_H - 140
    draw.text((60, cta_y), "SUBSCRIBE FREE", font=cta_font, fill=ACCENT)
    draw.text((60, cta_y + 36), "mutapatimes.com/subscribe", font=sub_font, fill=CARD_FG)

    img.save(output_path, "PNG", optimize=True)


def ensure_promo_cards():
    """Render all 4 promo cards if any are missing. Each angle gets its own
    background color for visual variety in the feed. Returns angle_key -> URL."""
    os.makedirs(PROMO_CARDS_DIR, exist_ok=True)
    urls = {}
    for color_idx, angle in enumerate(NEWSLETTER_ANGLES):
        filename = f"newsletter-promo-{angle['key']}.png"
        path = os.path.join(PROMO_CARDS_DIR, filename)
        if not os.path.isfile(path):
            try:
                render_promo_card(angle, path, color_idx=color_idx)
                print(f"    Promo card: {path}")
            except Exception as e:
                print(f"    Promo card FAILED for {angle['key']}: {e}")
        urls[angle["key"]] = f"{PROMO_CARD_BASE}/{filename}"
    return urls


# ── Newsletter caption generation ─────────────────────────────
NEWSLETTER_PROMPTS = {
    "LinkedIn": (
        "Write a LinkedIn post promoting The Mutapa Times Briefing — a "
        "free, twice-weekly Zimbabwe news email — to a professional "
        "diaspora/Africa-watcher audience.\n\n"
        "ANGLE FOR THIS POST:\n{angle_core}\n\n"
        "STRUCTURE:\n"
        "  1. HOOK (under 90 chars) — the angle distilled.\n"
        "  2. CONTEXT (2-3 short paragraphs with line breaks) — what subscribers get.\n"
        "  3. INVITATION line — soft CTA, 'free, 6 seconds, unsubscribe anytime' framing.\n"
        "  4. URL: {SUBSCRIBE_URL} on its own line.\n"
        "  5. 3-5 hashtags including #Zimbabwe.\n\n"
        "TONE: Confident, no emojis (maybe one 🇿🇼). 350-650 chars. Output ONLY the post text."
    ),
    "Facebook": (
        "Write a Facebook Page post promoting The Mutapa Times Briefing — "
        "a free, twice-weekly Zimbabwe news email — for the diaspora.\n\n"
        "ANGLE FOR THIS POST:\n{angle_core}\n\n"
        "STRUCTURE:\n"
        "  1. HOOK (one short sentence, conversational) — the angle.\n"
        "  2. BODY (2-3 sentences) — what's in the briefing, who it's for.\n"
        "  3. ENGAGEMENT prompt — invite shares: 'Tag someone who'd love this' / "
        "'Share with a friend abroad'.\n"
        "  4. URL: {SUBSCRIBE_URL} on its own line.\n"
        "No hashtags. 1 emoji max. 200-400 chars. Output ONLY the post text."
    ),
    "Threads": (
        "Write a Threads post promoting The Mutapa Times Briefing.\n\n"
        "ANGLE: {angle_core}\n\n"
        "STRUCTURE: Conversational hot-take (under 80 chars), then a short "
        "explainer with line breaks, then the URL: {SUBSCRIBE_URL} on its own line. "
        "Optionally 1-2 hashtags. Max 480 chars. 1-2 emojis OK. Output ONLY post text."
    ),
    "Twitter": (
        "Write an X/Twitter post promoting The Mutapa Times Briefing.\n\n"
        "ANGLE: {angle_core}\n\n"
        "Sharp hook + the URL: {SUBSCRIBE_URL} on its own line. STRICT 280 chars TOTAL "
        "including URL (URLs count as 23 chars). Optionally 1 hashtag like #Zimbabwe. "
        "Output ONLY post text."
    ),
    "Instagram": (
        "Write an Instagram caption promoting The Mutapa Times Briefing for "
        "the Zimbabwean diaspora.\n\n"
        "ANGLE FOR THIS POST:\n{angle_core}\n\n"
        "STRUCTURE:\n"
        "  1. HOOK (FIRST LINE, under 100 chars).\n"
        "  2. STORY (2-3 short paragraphs with line breaks) — what they get, "
        "why it matters.\n"
        "  3. CTA: 'Tap the link in our bio to subscribe — it's free.'\n"
        "  4. Final line: 8-12 hashtags mixing #Zimbabwe, #ZimbabweNews, "
        "#ZimDiaspora, #Africa with topic tags. NEVER include the URL inline.\n"
        "TONE: Story-driven, emotive. 1-3 emojis OK. 600-1100 chars. Output ONLY caption."
    ),
}


def fallback_newsletter(platform, angle):
    """Plain-template newsletter caption when Gemini is unavailable."""
    headline = angle["headline"]
    short = angle["core"].split(".")[0] + "."

    if platform == "LinkedIn":
        return (
            f"{headline}.\n\n"
            f"The Mutapa Times Briefing curates Zimbabwean news from 30+ foreign "
            f"sources. Mondays + Thursdays. Free. 5-minute read.\n\n"
            f"Built for the diaspora and informed Africa-watchers.\n\n"
            f"{SUBSCRIBE_URL}\n\n"
            f"#Zimbabwe #Africa #News #Diaspora"
        )
    if platform == "Facebook":
        return (
            f"{headline}.\n\n"
            f"The Mutapa Times Briefing — free, twice a week, 5-minute read. "
            f"Curated Zimbabwe news for the diaspora.\n\n"
            f"Tag a friend who needs this.\n\n"
            f"{SUBSCRIBE_URL}"
        )
    if platform == "Threads":
        return (
            f"{headline} 🇿🇼\n\n"
            f"The Mutapa Times Briefing. Curated Zim news. Free. Mon + Thu.\n\n"
            f"{SUBSCRIBE_URL}\n\n"
            f"#Zimbabwe"
        )
    if platform == "Twitter":
        body = f"{headline} 🇿🇼 The Mutapa Times Briefing. Free Zim news, twice a week."
        OVERHEAD = 23 + 4
        if len(body) + OVERHEAD > 280:
            body = body[: 280 - OVERHEAD - 1].rstrip() + "…"
        return f"{body}\n{SUBSCRIBE_URL}"
    if platform == "Instagram":
        return (
            f"{headline} 🇿🇼\n\n"
            f"The Mutapa Times Briefing is a free, twice-weekly Zimbabwe news email. "
            f"30+ sources, curated down to the 10-15 stories that actually matter.\n\n"
            f"Mondays and Thursdays. 5-minute read.\n\n"
            f"Tap the link in our bio to subscribe — it's free.\n\n"
            f"#Zimbabwe #ZimbabweNews #Africa #ZimDiaspora #Newsletter "
            f"#Harare #Bulawayo #ZimbabweanDiaspora #News #SouthernAfrica"
        )
    return f"{headline}\n{SUBSCRIBE_URL}"


def newsletter_caption(platform, angle):
    """Build a newsletter-driver caption — Gemini if available, else fallback."""
    if not GEMINI_API_KEY:
        return fallback_newsletter(platform, angle)

    prompt = NEWSLETTER_PROMPTS[platform].format(
        angle_core=angle["core"],
        SUBSCRIBE_URL=SUBSCRIBE_URL,
    )
    user_msg = (
        f"{prompt}\n\n"
        f"SUBSCRIBE_URL: {SUBSCRIBE_URL}\n"
        f"Output ONLY the post text, no commentary."
    )
    body = {
        "contents": [{"role": "user", "parts": [{"text": user_msg}]}],
        "generationConfig": {"temperature": 0.8, "maxOutputTokens": 500},
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
            return fallback_newsletter(platform, angle)
        parts = candidates[0].get("content", {}).get("parts", [])
        text = parts[0].get("text", "").strip() if parts else ""
        if not text:
            return fallback_newsletter(platform, angle)
        if platform == "Twitter":
            text = _twitter_safe(text, SUBSCRIBE_URL, "")
        return text
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, KeyError):
        return fallback_newsletter(platform, angle)


def newsletter_schedule_for(angle_idx, run_date_utc, batch_days):
    """Schedule one newsletter post per day of the batch window.
    angle_idx 0..3. For 3-day batches, the 4th post lands evening of day 2."""
    if angle_idx < 3 or batch_days >= 4:
        day_offset = min(angle_idx, batch_days - 1)
        cat_time = NEWSLETTER_SLOT_CAT
    else:
        day_offset = batch_days - 1
        cat_time = NEWSLETTER_SLOT_EVENING_CAT
    h, m = map(int, cat_time.split(":"))
    target_date = run_date_utc + timedelta(days=day_offset)
    cat_dt = datetime(target_date.year, target_date.month, target_date.day,
                      h, m, tzinfo=timezone(CAT_OFFSET))
    return cat_dt.astimezone(timezone.utc)


# ── Metricool row builder ─────────────────────────────────────
def build_metricool_row(platform, caption, article, date_str, time_str, image_url):
    """Build one CSV row in Metricool's import format. All columns present;
    most stay empty since we're publishing a basic image-with-caption post."""
    row = {col: "" for col in METRICOOL_COLUMNS}

    # Core fields
    row["Text"] = caption
    row["Date"] = date_str
    row["Time"] = time_str
    row["Draft"] = "false"

    # Platform flags — set ours to true, all others to false
    for flag in PLATFORM_FLAGS:
        row[flag] = "false"
    row[PLATFORM_TO_FLAG[platform]] = "true"

    # Image (single image per post — Picture Url 1 + alt text)
    if image_url:
        row["Picture Url 1"] = image_url
        # Alt text: headline truncated to 200 chars (Metricool/IG limit-friendly)
        alt = (article.get("title") or "").strip()
        if len(alt) > 200:
            alt = alt[:199].rstrip() + "…"
        row["Alt text picture 1"] = alt

    # Per-platform Post Type defaults (Metricool wants these explicit)
    if platform == "Facebook":
        row["Facebook Post Type"] = "POST"
    elif platform == "Instagram":
        row["Instagram Post Type"] = "POST"
    elif platform == "Threads":
        row["Threads Post Type"] = "POST"
    elif platform == "LinkedIn":
        row["LinkedIn Type"] = "POST"
        # Render the URL preview card on LinkedIn — much higher CTR
        row["LinkedIn Show link preview"] = "true"
    elif platform == "Twitter":
        row["Twitter/X Type"] = "POST"

    row["Brand name"] = BRAND_NAME
    return row


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
        # Still write an empty CSV with the proper Metricool header so a stale
        # download doesn't crash their importer.
        with open(OUTPUT_CSV, "w", encoding="utf-8", newline="") as f:
            csv.writer(f, quoting=csv.QUOTE_ALL).writerow(METRICOOL_COLUMNS)
        return

    slate_size = articles_for_this_run()
    selected = new_articles[:slate_size]
    print(f"  Selected top {len(selected)} articles ({slate_size}-article slate for this run)")

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
            render_card(art["title"], art["source"], card_path, color_idx=idx)
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

            rows.append(build_metricool_row(
                platform=platform,
                caption=caption,
                article=art,
                date_str=sched_utc.strftime("%Y-%m-%d"),
                time_str=sched_utc.strftime("%H:%M:%S"),
                image_url=media,
            ))

            # Mild rate limit on Gemini
            time.sleep(0.4)

        queued[art["url"]] = datetime.now(timezone.utc).isoformat()

    # ── Append newsletter-driver posts ──────────────────────
    # 4 posts per platform per run, one per value-prop angle.
    # Skipped in evening mode — no time to fit 20 promos in one evening.
    if EVENING_START_CAT:
        print(f"\n  Skipping newsletter-driver posts (evening-mode override)")
        with open(OUTPUT_CSV, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=METRICOOL_COLUMNS, quoting=csv.QUOTE_ALL)
            w.writeheader()
            for r in rows:
                w.writerow(r)
        print(f"\n  Wrote {OUTPUT_CSV} ({len(rows)} rows)")
        save_queued(queued)
        print("\n=== DONE ===")
        return

    print(f"\n  Generating newsletter-driver posts (4 angles × 5 platforms)…")
    promo_card_urls = ensure_promo_cards()
    weekday = datetime.now(timezone.utc).weekday()
    batch_days = DAYS_BY_WEEKDAY.get(weekday, 1)

    for platform in ("LinkedIn", "Facebook", "Threads", "Twitter", "Instagram"):
        for angle_idx, angle in enumerate(NEWSLETTER_ANGLES):
            print(f"    {platform} · {angle['key']}…", end=" ", flush=True)
            caption = newsletter_caption(platform, angle)
            print("OK" if caption else "FAIL")

            sched_utc = newsletter_schedule_for(
                angle_idx,
                datetime.combine(today_utc, datetime.min.time()),
                batch_days,
            )
            if sched_utc <= datetime.now(timezone.utc):
                sched_utc += timedelta(days=batch_days)

            # Image: angle-specific promo card
            media = promo_card_urls.get(angle["key"], "")

            rows.append(build_metricool_row(
                platform=platform,
                caption=caption,
                article={"title": f"Subscribe — {angle['headline']}"},
                date_str=sched_utc.strftime("%Y-%m-%d"),
                time_str=sched_utc.strftime("%H:%M:%S"),
                image_url=media,
            ))
            time.sleep(0.4)

    # Write CSV in Metricool's native column order
    with open(OUTPUT_CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=METRICOOL_COLUMNS, quoting=csv.QUOTE_ALL)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print(f"\n  Wrote {OUTPUT_CSV} ({len(rows)} rows)")

    save_queued(queued)
    print("\n=== DONE ===")


if __name__ == "__main__":
    main()
