#!/usr/bin/env python3
"""Build a 1080x1920 YouTube Short MP4 from a Mutapa Times article or
data Short (FX / weather / markets). Phase 1 of the YouTube pipeline:
local rendering only — upload comes in Phase 3.

Pipeline:
  1. Resolve source -> (title, summary, hero_image, kind)
  2. Compose a short script (Hook + Body + CTA, 60-90 words)
  3. edge-tts -> voice.mp3 in /tmp/yt-short/{slug}/
  4. Measure voice duration via ffprobe -> set video duration to
     voice + 0.5s tail.
  5. Render a single 1080x1920 base frame with PIL (butter background,
     centered hero card area, top brand bar, lower-third).
  6. ffmpeg zoompan filter applies Ken Burns motion to the base frame
     for the audio duration, muxes voice.mp3, encodes H.264/AAC.
  7. Output MP4 + sidecar meta.json in data/youtube-queue/.

Usage examples:
  python3 scripts/build_youtube_short.py --article 2026-05-13-shumba-maasai-venice-biennale-zimbabwean-cultural-interventions
  python3 scripts/build_youtube_short.py --spotlight
  python3 scripts/build_youtube_short.py --fx
  python3 scripts/build_youtube_short.py --weather
  python3 scripts/build_youtube_short.py --markets
  python3 scripts/build_youtube_short.py --article SLUG --voice en-GB-SoniaNeural

Requires:
  pip install edge-tts Pillow
  ffmpeg, ffprobe on PATH (brew install ffmpeg, apt install ffmpeg)
"""
import argparse
import asyncio
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from card_lib import (  # noqa: E402
    BUTTER, CARD_FG, CARD_FG_MUTED, ACCENT, load_font, wrap_text,
)

try:
    from PIL import Image, ImageDraw
except ImportError:
    raise SystemExit("ERROR: Pillow not installed. Run: pip3 install Pillow")

try:
    import edge_tts  # noqa: F401
except ImportError:
    raise SystemExit("ERROR: edge-tts not installed. Run: pip3 install edge-tts")


# ── Brand + format constants ──────────────────────────────
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT_DIR = os.path.join(ROOT, "data", "youtube-queue")
VIDEO_W, VIDEO_H = 1080, 1920          # vertical 9:16 (Shorts spec)
FPS = 30
DEFAULT_VOICE = "en-GB-SoniaNeural"    # UK female newsreader; smoother prosody than Ryan
ALT_VOICES = {                          # short aliases for the CLI
    "ryan":   "en-GB-RyanNeural",
    "sonia":  "en-GB-SoniaNeural",
    "thomas": "en-GB-ThomasNeural",
    "leah":   "en-ZA-LeahNeural",
    "luke":   "en-ZA-LukeNeural",
    "libby":  "en-GB-LibbyNeural",
}

# Tricky words / acronyms — substituted phonetically just before TTS.
# Display copy in titles/descriptions is unaffected.
PHONETIC_SUBS = [
    (r"\bBeuys\b",        "Boyce"),
    (r"\bMurehwa\b",      "Moo-ray-wa"),
    (r"\bMnangagwa\b",    "Mnan-gag-wa"),
    (r"\bChiwenga\b",     "Chee-wen-ga"),
    (r"\bTsvangirai\b",   "Tsvan-gee-rai"),
    (r"\bBulawayo\b",     "Boo-la-way-oh"),
    (r"\bMasvingo\b",     "Mas-ving-oh"),
    (r"\bMosi-oa-Tunya\b","Moe-see oh-ah Toon-ya"),
    (r"\bZWG\b",          "Zim gold"),
    (r"\bZWL\b",          "Zim dollar"),
    (r"\bVFEX\b",         "V-Fex"),
    (r"\bZSE\b",          "Zee S E"),
    (r"\bRBZ\b",          "Reserve Bank of Zimbabwe"),
    (r"\bSADC\b",         "Sadek"),
    (r"\bdare\b",         "dah-ray"),     # Shona communal forum, not English 'dare'
    (r"\bcampi\b",        "cam-pee"),
    (r"\bcampo\b",        "cam-poh"),
    (r"\bdurée\b",        "doo-ray"),
    (r"\barte útil\b",    "arte u-teel"),
    (r"\bSozialkunst\b",  "Zotzee-al-koonst"),
]

BRAND_TOP = (240, 224, 188)            # warmer butter for top/bottom bands
URL_TEXT = "MUTAPATIMES.COM"
TAGLINE = "ZIMBABWE OUTSIDE-IN"

# Hero rectangle within the 1080x1920 canvas — where the source image
# lives and where the gentle pan/zoom motion is constrained. Brand
# chrome (top band, caption, bottom band) sits outside this rect and
# never moves.
HERO_X = 60
HERO_Y = 220
HERO_W = VIDEO_W - 2 * HERO_X            # 960
HERO_H = VIDEO_H - HERO_Y - 480          # 1220 (leaves caption + bottom band)


# ── Source resolvers ──────────────────────────────────────
def _parse_frontmatter(text):
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.DOTALL)
    if not m:
        return {}, text
    fm_raw, body = m.group(1), m.group(2)
    fm = {}
    for line in fm_raw.splitlines():
        mm = re.match(r"^([a-z_]+):\s*[\"']?(.*?)[\"']?\s*$", line)
        if mm:
            fm[mm.group(1)] = mm.group(2)
    return fm, body


def resolve_article(slug):
    """Find {slug}.md in either content/articles (originals) or
    content/wires (auto-imported archive)."""
    candidates = [
        os.path.join(ROOT, "content", "articles", f"{slug}.md"),
        os.path.join(ROOT, "content", "wires", f"{slug}.md"),
    ]
    path = next((p for p in candidates if os.path.exists(p)), None)
    if path is None:
        raise SystemExit(f"Article not found in content/articles or content/wires: {slug}.md")
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    fm, body = _parse_frontmatter(text)
    image_rel = fm.get("image", "").lstrip("/")
    image_path = os.path.join(ROOT, image_rel) if image_rel else None
    return {
        "kind": "article",
        "slug": slug,
        "title": fm.get("title", "The Mutapa Times"),
        "summary": fm.get("summary", ""),
        "body": body,
        "category": fm.get("category", "News"),
        "image": image_path if image_path and os.path.isfile(image_path) else None,
        "tags": [fm.get("category", "Zimbabwe"), "Zimbabwe", "Mutapa Times"],
    }


def resolve_spotlight():
    path = os.path.join(ROOT, "data", "spotlight.json")
    with open(path, "r", encoding="utf-8") as f:
        d = json.load(f)
    arts = d.get("articles") or []
    if not arts:
        raise SystemExit("No spotlight stories available.")
    a = arts[0]
    title = a.get("title", "")
    # Re-slug from URL if it's a CMS article so we can deep-link cleanly
    slug = re.sub(r"[^a-z0-9-]+", "-", title.lower())[:80]
    return {
        "kind": "spotlight",
        "slug": slug,
        "title": title,
        "summary": a.get("description", "")[:280],
        "body": "",
        "category": "News",
        "image": _resolve_spotlight_image(a),
        "tags": ["Zimbabwe", "News", a.get("source", "Mutapa Times")],
    }


def _resolve_spotlight_image(article):
    """Spotlight items often have a `card_image` URL pointing at our
    own brand-rendered card under img/cards/news/. Map that back to
    the local file if possible; otherwise return None and let the
    composer fall through to a brand-only layout."""
    card_url = article.get("card_image") or ""
    m = re.search(r"/img/cards/news/([0-9a-f]+\.png)$", card_url)
    if m:
        local = os.path.join(ROOT, "img", "cards", "news", m.group(1))
        if os.path.isfile(local):
            return local
    return None


def resolve_fx():
    """Daily FX Short — uses the editor-curated copy from data/fx-rates.json."""
    path = os.path.join(ROOT, "data", "fx-rates.json")
    if not os.path.exists(path):
        raise SystemExit("data/fx-rates.json missing — run scripts/fetch_fx.py first.")
    with open(path, "r", encoding="utf-8") as f:
        d = json.load(f)
    rates = d.get("rates", {})
    def _r(k, default="?"):
        v = rates.get(k)
        try:
            return f"{float(v):.2f}"
        except (TypeError, ValueError):
            return default
    title = "Zimbabwe FX today"
    try:
        gbp_to_usd = 1.0 / float(rates.get("GBP", 0))
    except (TypeError, ValueError, ZeroDivisionError):
        gbp_to_usd = None
    parts = [f"One US dollar trades at {_r('ZWG')} Zim gold."]
    if rates.get("ZAR"):
        parts.append(f"Against the rand, one US dollar is {_r('ZAR')}.")
    if gbp_to_usd:
        parts.append(f"Against sterling, one pound buys {gbp_to_usd:.2f} dollars.")
    summary = " ".join(parts)
    return {
        "kind": "fx",
        "slug": f"fx-{datetime.now().strftime('%Y%m%d')}",
        "title": title,
        "summary": summary,
        "body": "",
        "category": "FX",
        "image": _find_card("fx-snapshot"),
        "tags": ["Zimbabwe", "FX", "ZWG", "Forex"],
    }


def resolve_weather():
    path = os.path.join(ROOT, "data", "zim-weather.json")
    if not os.path.exists(path):
        raise SystemExit("data/zim-weather.json missing — run scripts/fetch_weather.py first.")
    with open(path, "r", encoding="utf-8") as f:
        d = json.load(f)
    cities = d.get("cities", [])
    bits = []
    for c in cities[:4]:
        bits.append(f"{c.get('name', '?')} {c.get('condition', '')}, high {c.get('high', '?')} degrees.")
    summary = " ".join(bits) if bits else "Live weather across Zimbabwe's major cities."
    return {
        "kind": "weather",
        "slug": f"weather-{datetime.now().strftime('%Y%m%d')}",
        "title": "Zimbabwe weather today",
        "summary": summary,
        "body": "",
        "category": "Weather",
        "image": _find_card("weather-card"),
        "tags": ["Zimbabwe", "Weather", "Harare", "Bulawayo"],
    }


def resolve_markets():
    path = os.path.join(ROOT, "data", "markets-indices.json")
    if not os.path.exists(path):
        raise SystemExit("data/markets-indices.json missing.")
    with open(path, "r", encoding="utf-8") as f:
        d = json.load(f)
    rows = d.get("indices", [])
    bits = []
    for r in rows[:4]:
        bits.append(f"{r.get('label', '?')} {r.get('day_change', 'flat')}.")
    summary = " ".join(bits) if bits else "Today's close across Africa's major bourses."
    return {
        "kind": "markets",
        "slug": f"markets-{datetime.now().strftime('%Y%m%d')}",
        "title": "African markets today",
        "summary": summary,
        "body": "",
        "category": "Markets",
        "image": None,
        "tags": ["Zimbabwe", "Africa", "ZSE", "Markets"],
    }


def _find_card(stem):
    """Pick the most recent rendered card matching {stem}*.png if any."""
    for pat in (f"img/cards/{stem}*.png", f"img/cards/news/{stem}*.png"):
        hits = sorted(glob.glob(os.path.join(ROOT, pat)))
        if hits:
            return hits[-1]
    return None


# ── Script generation ─────────────────────────────────────
def build_script(src):
    """Compose a 60-90 word TTS script with Hook + Body + CTA. Phase 1
    uses templates — Gemini rewrite slots in here in Phase 2."""
    kind = src["kind"]
    title = re.sub(r"\s+", " ", src["title"]).strip().rstrip(".")
    summary = re.sub(r"\s+", " ", src["summary"]).strip()
    # Ensure summary ends with a single period so TTS pacing is natural
    summary = summary.rstrip(".!? ") + "." if summary else ""

    if kind in ("article", "spotlight"):
        hook = "From The Mutapa Times."
        body = f"{title}. {summary}" if summary else f"{title}."
        cta = "Read the full story at mutapatimes dot com."
    elif kind == "fx":
        hook = "Zimbabwe foreign exchange today."
        body = summary
        cta = "Live rates and the diaspora corridor table at mutapatimes dot com slash F X."
    elif kind == "weather":
        hook = "Zimbabwe weather today."
        body = summary
        cta = "Hourly updates for every major city at mutapatimes dot com slash weather."
    elif kind == "markets":
        hook = "African markets today."
        body = summary
        cta = "Closes and the Zimbabwe Stock Exchange table at mutapatimes dot com slash markets."
    else:
        hook = "The Mutapa Times."
        body = summary or title
        cta = "More at mutapatimes dot com."

    return " ".join([hook, body, cta]).strip()


# ── TTS ───────────────────────────────────────────────────
def _apply_phonetic_subs(text):
    """Replace each tricky word in PHONETIC_SUBS with a phonetic
    spelling just before TTS. Display copy (titles/descriptions) is
    untouched — these substitutions are for the audio track only."""
    for pat, repl in PHONETIC_SUBS:
        text = re.sub(pat, repl, text, flags=re.IGNORECASE)
    return text


async def _tts(text, voice, out_path):
    import edge_tts
    # rate=-10% gives a measured newsreader pace; pitch unchanged.
    comm = edge_tts.Communicate(text, voice, rate="-10%")
    await comm.save(out_path)


def synthesize(text, voice, out_path):
    asyncio.run(_tts(text, voice, out_path))


def probe_duration(mp3_path):
    out = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", mp3_path,
    ])
    return float(out.decode().strip())


# ── Frame composition ─────────────────────────────────────
def compose_chrome(src, out_path):
    """Render the static 1080x1920 chrome layer. The hero rectangle is
    left as butter — the animated hero stream is overlaid onto that
    rectangle by ffmpeg, so the chrome itself never moves.

    Layout, top to bottom:
        [ Top band: 'THE MUTAPA TIMES' + section pill ]
        [ Hero rectangle (butter, will be replaced by overlay) ]
        [ Caption band: short title, max 3 lines ]
        [ Bottom band: 'MUTAPATIMES.COM' + tagline ]
    """
    img = Image.new("RGB", (VIDEO_W, VIDEO_H), BUTTER)
    draw = ImageDraw.Draw(img)

    # ── Top band ────────────────────────────────────────
    draw.rectangle([0, 0, VIDEO_W, 180], fill=BRAND_TOP)
    serif_md = load_font("serif_bold", 56)
    sans_bold = load_font("sans_bold", 26)
    draw.text((60, 60), "THE MUTAPA TIMES", font=serif_md, fill=CARD_FG)

    # Section pill (top-right)
    pill_text = src["category"].upper()
    pill_pad_x, pill_pad_y = 22, 10
    pill_bbox = draw.textbbox((0, 0), pill_text, font=sans_bold)
    pill_w = (pill_bbox[2] - pill_bbox[0]) + pill_pad_x * 2
    pill_h = (pill_bbox[3] - pill_bbox[1]) + pill_pad_y * 2
    px = VIDEO_W - pill_w - 60
    py = (180 - pill_h) // 2
    draw.rounded_rectangle([px, py, px + pill_w, py + pill_h],
                           radius=pill_h // 2, fill=ACCENT)
    draw.text((px + pill_pad_x, py + pill_pad_y - 2), pill_text,
              font=sans_bold, fill=(255, 255, 255))

    # ── Hero rectangle hairline (the overlay sits inside this frame) ──
    draw.rectangle([HERO_X, HERO_Y, HERO_X + HERO_W, HERO_Y + HERO_H],
                   outline=CARD_FG, width=2)

    # ── Caption band (short title) ──────────────────────
    cap_top = HERO_Y + HERO_H + 30
    cap_bot = VIDEO_H - 220
    title = src["title"]
    cap_font = load_font("serif_bold", 56)
    lines = wrap_text(title, cap_font, VIDEO_W - 160, draw)[:3]
    cap_h = len(lines) * 70
    cy = cap_top + (cap_bot - cap_top - cap_h) // 2
    for line in lines:
        draw.text((80, cy), line, font=cap_font, fill=CARD_FG)
        cy += 70

    # ── Bottom band ─────────────────────────────────────
    draw.rectangle([0, VIDEO_H - 180, VIDEO_W, VIDEO_H], fill=BRAND_TOP)
    url_font = load_font("sans_bold", 38)
    tag_font = load_font("sans", 22)
    url_bbox = draw.textbbox((0, 0), URL_TEXT, font=url_font)
    ux = (VIDEO_W - (url_bbox[2] - url_bbox[0])) // 2
    draw.text((ux, VIDEO_H - 140), URL_TEXT, font=url_font, fill=CARD_FG)
    tag_bbox = draw.textbbox((0, 0), TAGLINE, font=tag_font)
    tx = (VIDEO_W - (tag_bbox[2] - tag_bbox[0])) // 2
    draw.text((tx, VIDEO_H - 80), TAGLINE, font=tag_font, fill=CARD_FG_MUTED)
    accent_w = 80
    draw.rectangle([(VIDEO_W - accent_w) // 2, VIDEO_H - 158,
                    (VIDEO_W + accent_w) // 2, VIDEO_H - 154], fill=ACCENT)

    img.save(out_path, "JPEG", quality=92)


def compose_hero(src, out_path):
    """Render the hero image alone, sized to fill the hero rectangle
    (HERO_W × HERO_H). This image gets gently pan/zoomed by ffmpeg and
    overlaid onto the static chrome. If there's no source image we
    fall back to a typographic block so we still have something
    visually anchoring the hero rect."""
    hero = Image.new("RGB", (HERO_W, HERO_H), BUTTER)
    draw = ImageDraw.Draw(hero)
    if src.get("image"):
        try:
            im = Image.open(src["image"]).convert("RGB")
            im = _fit_cover(im, HERO_W, HERO_H)
            ix = (HERO_W - im.width) // 2
            iy = (HERO_H - im.height) // 2
            hero.paste(im, (ix, iy))
        except Exception:
            _draw_typographic_hero(draw, src, 0, 0, HERO_W, HERO_H)
    else:
        _draw_typographic_hero(draw, src, 0, 0, HERO_W, HERO_H)
    hero.save(out_path, "JPEG", quality=92)


def _fit_cover(im, max_w, max_h):
    """Scale to fill the box, then centre-crop. Used for the hero so
    there are no butter bars inside the hero rectangle — the gentle
    pan stays within meaningful image pixels."""
    ratio = max(max_w / im.width, max_h / im.height)
    nw, nh = int(im.width * ratio), int(im.height * ratio)
    im = im.resize((nw, nh), Image.LANCZOS)
    left = (nw - max_w) // 2
    top = (nh - max_h) // 2
    return im.crop((left, top, left + max_w, top + max_h))


def _fit_within(im, max_w, max_h):
    ratio = min(max_w / im.width, max_h / im.height)
    if ratio >= 1.0:
        # Don't upscale; keep at native size
        return im
    return im.resize((int(im.width * ratio), int(im.height * ratio)),
                     Image.LANCZOS)


def _draw_typographic_hero(draw, src, x, y, w, h):
    """Fallback hero — no source image, render a typographic block."""
    title = src["title"]
    body_font = load_font("serif_bold", 110)
    lines = wrap_text(title, body_font, w - 80, draw)[:5]
    line_h = 130
    total = len(lines) * line_h
    cy = y + (h - total) // 2
    for line in lines:
        draw.text((x + 40, cy), line, font=body_font, fill=CARD_FG)
        cy += line_h


# ── ffmpeg assembly ───────────────────────────────────────
def assemble(chrome_jpg, hero_jpg, voice_mp3, duration, out_mp4):
    """ffmpeg pipeline with contained hero motion:

         Input 0: chrome.jpg — looped, 1080x1920, brand chrome with
                  empty (butter) hero rectangle. Never moves.
         Input 1: hero.jpg   — looped, HERO_W x HERO_H, source image
                  cropped/scaled to fill. Gets gentle zoompan motion
                  inside its rectangle.
         Input 2: voice.mp3  — the TTS narration.

       The animated hero stream is overlaid onto the static chrome at
       (HERO_X, HERO_Y). Brand bands, masthead, section pill, caption,
       URL and tagline stay completely locked.

       Motion: zoom from 1.00 to 1.06 over the duration with a slow
       horizontal sine drift (±20px). Imperceptible at a glance —
       enough to feel alive, not enough to be busy."""
    frames = int(round(duration * FPS))
    # zoompan output stays at HERO_W x HERO_H so the overlay lines up.
    filter_complex = (
        f"[1:v]zoompan="
        f"z='min(zoom+0.0004,1.06)':"
        f"x='iw/2-(iw/zoom/2)+sin(in/{FPS * 4})*20':"
        f"y='ih/2-(ih/zoom/2)':"
        f"d={frames}:s={HERO_W}x{HERO_H}:fps={FPS}[hero];"
        f"[0:v][hero]overlay={HERO_X}:{HERO_Y}:shortest=1,"
        f"format=yuv420p[v]"
    )
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-framerate", str(FPS), "-i", chrome_jpg,
        "-loop", "1", "-framerate", str(FPS), "-i", hero_jpg,
        "-i", voice_mp3,
        "-filter_complex", filter_complex,
        "-map", "[v]", "-map", "2:a",
        "-t", f"{duration:.2f}",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        out_mp4,
    ]
    subprocess.run(cmd, check=True, stderr=subprocess.DEVNULL)


# ── Orchestration ─────────────────────────────────────────
def render(src, voice, work_dir, slug_suffix=""):
    os.makedirs(work_dir, exist_ok=True)
    chrome_jpg = os.path.join(work_dir, "chrome.jpg")
    hero_jpg = os.path.join(work_dir, "hero.jpg")
    voice_mp3 = os.path.join(work_dir, "voice.mp3")

    script = build_script(src)
    print(f"  Script ({len(script.split())} words):")
    print(f"    {script}")
    tts_text = _apply_phonetic_subs(script)
    if tts_text != script:
        print(f"  Phonetic-substituted for TTS:")
        print(f"    {tts_text}")

    print(f"  TTS -> {voice_mp3}  (voice={voice})")
    synthesize(tts_text, voice, voice_mp3)
    voice_dur = probe_duration(voice_mp3)
    video_dur = voice_dur + 0.6
    print(f"  Voice {voice_dur:.2f}s  → video {video_dur:.2f}s")

    print(f"  Composing chrome -> {chrome_jpg}")
    compose_chrome(src, chrome_jpg)
    print(f"  Composing hero   -> {hero_jpg}")
    compose_hero(src, hero_jpg)

    os.makedirs(OUT_DIR, exist_ok=True)
    date_prefix = datetime.now().strftime("%Y-%m-%d")
    safe_slug = re.sub(r"[^a-z0-9-]+", "-", src["slug"].lower()).strip("-")
    # CMS article slugs already start with YYYY-MM-DD — don't double-prefix
    safe_slug = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", safe_slug)[:60].strip("-")
    if slug_suffix:
        safe_slug = f"{safe_slug}-{slug_suffix}"
    out_mp4 = os.path.join(OUT_DIR, f"{date_prefix}-{safe_slug}.mp4")
    print(f"  ffmpeg -> {out_mp4}")
    assemble(chrome_jpg, hero_jpg, voice_mp3, video_dur, out_mp4)

    meta = {
        "kind": src["kind"],
        "title": _yt_title(src),
        "description": _yt_description(src, script),
        "tags": src.get("tags", []) + ["Shorts"],
        "category_id": "25",   # News & Politics
        "default_language": "en",
        "made_for_kids": False,
        "ai_disclosure": True,
        "voice": voice,
        "duration_sec": round(video_dur, 2),
        "script": script,
        "source": {
            "slug": src.get("slug"),
            "kind": src["kind"],
        },
        "approved": False,
        "uploaded": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    meta_path = out_mp4.replace(".mp4", ".meta.json")
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)
    print(f"  Meta -> {meta_path}")
    return out_mp4, meta_path


def _yt_title(src):
    base = src["title"].strip()
    if len(base) > 70:
        base = base[:67].rstrip() + "…"
    return f"{base} | The Mutapa Times"


def _yt_description(src, script):
    parts = [
        script,
        "",
        "The Mutapa Times — Zimbabwe outside-in.",
        "https://www.mutapatimes.com",
        "",
        "#Zimbabwe #" + src["category"].replace(" ", ""),
    ]
    return "\n".join(parts)


# ── CLI ───────────────────────────────────────────────────
def main():
    p = argparse.ArgumentParser(description="Build a YouTube Short MP4")
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--article", help="CMS slug (under content/articles/)")
    group.add_argument("--spotlight", action="store_true", help="Top spotlight story")
    group.add_argument("--fx", action="store_true", help="Daily FX Short")
    group.add_argument("--weather", action="store_true", help="Daily weather Short")
    group.add_argument("--markets", action="store_true", help="Daily markets Short")
    p.add_argument("--voice", default=DEFAULT_VOICE,
                   help=f"edge-tts voice (default {DEFAULT_VOICE}). Short aliases: " +
                        ", ".join(ALT_VOICES.keys()))
    p.add_argument("--voices-test", action="store_true",
                   help="Render the same Short with several edge-tts voices "
                        "side-by-side for A/B listening.")
    p.add_argument("--keep-work", action="store_true",
                   help="Don't clean the /tmp scratch dir on exit")
    args = p.parse_args()

    voice = ALT_VOICES.get(args.voice, args.voice)

    if args.article:
        src = resolve_article(args.article)
    elif args.spotlight:
        src = resolve_spotlight()
    elif args.fx:
        src = resolve_fx()
    elif args.weather:
        src = resolve_weather()
    elif args.markets:
        src = resolve_markets()
    else:
        raise SystemExit("No source flag passed.")

    print(f"=== BUILD YOUTUBE SHORT — {src['kind']} ===")
    print(f"  Title: {src['title']}")

    if args.voices_test:
        candidates = [
            ("en-GB-SoniaNeural",  "sonia"),
            ("en-GB-ThomasNeural", "thomas"),
            ("en-GB-LibbyNeural",  "libby"),
            ("en-ZA-LeahNeural",   "leah"),
        ]
        results = []
        for v, label in candidates:
            print(f"\n--- voice: {v} ---")
            work = tempfile.mkdtemp(prefix=f"yt-short-{label}-")
            try:
                out_mp4, meta_path = render(src, v, work, slug_suffix=label)
                results.append((label, v, out_mp4))
            finally:
                if not args.keep_work:
                    shutil.rmtree(work, ignore_errors=True)
        print("\n=== DONE (voices-test) ===")
        for label, v, out_mp4 in results:
            print(f"  [{label:>6}]  {v:<22s}  {out_mp4}")
        return

    work = tempfile.mkdtemp(prefix="yt-short-")
    try:
        out_mp4, meta_path = render(src, voice, work)
    finally:
        if not args.keep_work:
            shutil.rmtree(work, ignore_errors=True)

    print("=== DONE ===")
    print(f"  MP4:  {out_mp4}")
    print(f"  Meta: {meta_path}")


if __name__ == "__main__":
    main()
