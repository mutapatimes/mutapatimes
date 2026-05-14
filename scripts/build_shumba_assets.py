#!/usr/bin/env python3
"""One-off: render 10 launch cards for the Shumba Maasai article.

Outputs to img/uploads/shumba-launch/:
  5 IG Story (1080x1920):  story-1-headline .. story-5-cta
  5 IG Portrait (1080x1350): portrait-1-headline .. portrait-5-cta

Card types per format:
  1. Headline    — title + deck + section pill
  2-4. Quotes    — pull-quotes #1, #2, #3 with attribution
  5. CTA         — "Read the full piece" + URL

Brand tokens reused from scripts/card_lib.py: butter background,
Playfair serif, Inter sans, accent red.
"""
import os
import sys
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from card_lib import (
    BUTTER, CARD_FG, CARD_FG_MUTED, ACCENT, load_font, wrap_text,
)

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT_DIR = os.path.join(ROOT, "img", "uploads", "shumba-launch")

STORY = (1080, 1920)         # 9:16 IG/TikTok story
PORTRAIT = (1080, 1350)      # 4:5 IG feed
BRAND_TOP = (240, 224, 188)  # warmer butter for top/bottom bands

# ── Content ──────────────────────────────────────────────
ARTICLE_URL = "mutapatimes.com"
ARTICLE_SECTION = "CULTURE"
ARTICLE_BYLINE = "Tendai Kuwanda"
ARTICLE_TITLE = "Shumba Maasai in Venice"
ARTICLE_DECK = (
    "A day-long procession through the city's campi, "
    "performed under the borrowed authority of a Murehwa chief, "
    "restages the social-sculpture lineage of Joseph Beuys for a "
    "contemporary African discursive practice."
)
QUOTES = [
    "The chief, on Saturday afternoon, was not a costume. He was a structure.",
    "Spectacle requires spectators; the work withheld both.",
    "The procession was not a performance. It was an argument about who, in 2026, gets to convene a public square.",
]
CTA_HEADLINE = "Read the full piece."
CTA_SUBHEAD = "Art criticism that takes Zimbabwe seriously."


# ── Layout primitives ────────────────────────────────────
def new_canvas(w, h):
    return Image.new("RGB", (w, h), BUTTER)


def draw_top_band(img, draw, h_band=180):
    w, _ = img.size
    draw.rectangle([0, 0, w, h_band], fill=BRAND_TOP)
    serif = load_font("serif_bold", 56)
    draw.text((60, 60), "THE MUTAPA TIMES", font=serif, fill=CARD_FG)


def draw_section_pill(img, draw, label, h_band=180):
    w, _ = img.size
    sans_bold = load_font("sans_bold", 26)
    pad_x, pad_y = 22, 10
    bbox = draw.textbbox((0, 0), label, font=sans_bold)
    pw = (bbox[2] - bbox[0]) + pad_x * 2
    ph = (bbox[3] - bbox[1]) + pad_y * 2
    px = w - pw - 60
    py = (h_band - ph) // 2
    draw.rounded_rectangle([px, py, px + pw, py + ph],
                           radius=ph // 2, fill=ACCENT)
    draw.text((px + pad_x, py + pad_y - 2), label,
              font=sans_bold, fill=(255, 255, 255))


def draw_bottom_band(img, draw, url=ARTICLE_URL, byline=None, h_band=180):
    w, h = img.size
    draw.rectangle([0, h - h_band, w, h], fill=BRAND_TOP)
    url_font = load_font("sans_bold", 38)
    tag_font = load_font("sans", 22)
    # Accent rule
    accent_w = 80
    rule_y = h - h_band + 22
    draw.rectangle([(w - accent_w) // 2, rule_y,
                    (w + accent_w) // 2, rule_y + 4], fill=ACCENT)
    # Centred URL
    url_text = url.upper()
    url_bbox = draw.textbbox((0, 0), url_text, font=url_font)
    ux = (w - (url_bbox[2] - url_bbox[0])) // 2
    draw.text((ux, h - h_band + 50), url_text, font=url_font, fill=CARD_FG)
    # Byline (if provided) underneath, muted sans
    if byline:
        tag = byline.upper()
        tag_bbox = draw.textbbox((0, 0), tag, font=tag_font)
        tx = (w - (tag_bbox[2] - tag_bbox[0])) // 2
        draw.text((tx, h - h_band + 105), tag, font=tag_font, fill=CARD_FG_MUTED)


# ── Card renderers ───────────────────────────────────────
def render_headline(size, out_path):
    img = new_canvas(*size)
    draw = ImageDraw.Draw(img)
    w, h = size
    draw_top_band(img, draw)
    draw_section_pill(img, draw, ARTICLE_SECTION)

    # Eyebrow above headline
    eyebrow_font = load_font("sans_bold", 28)
    draw.text((80, 280), "FROM VENICE BIENNALE 61", font=eyebrow_font, fill=ACCENT)

    # Headline: very large Playfair, multi-line allowed
    head_font_size = 150 if h >= 1900 else 130
    head_font = load_font("serif_bold", head_font_size)
    head_lines = wrap_text(ARTICLE_TITLE, head_font, w - 160, draw)
    line_h = int(head_font_size * 1.05)
    cy = 340
    for line in head_lines:
        draw.text((80, cy), line, font=head_font, fill=CARD_FG)
        cy += line_h

    # Deck
    deck_font_size = 42 if h >= 1900 else 38
    deck_font = load_font("sans", deck_font_size)
    deck_lines = wrap_text(ARTICLE_DECK, deck_font, w - 160, draw)
    cy += 60
    for line in deck_lines:
        draw.text((80, cy), line, font=deck_font, fill=CARD_FG_MUTED)
        cy += int(deck_font_size * 1.35)

    # Byline (small, bottom-aligned region above bottom band)
    by_font = load_font("sans_bold", 22)
    draw.text((80, h - 280),
              f"BY {ARTICLE_BYLINE.upper()}  ·  {ARTICLE_SECTION}",
              font=by_font, fill=CARD_FG)

    draw_bottom_band(img, draw, byline=ARTICLE_BYLINE)
    img.save(out_path, "PNG")
    return out_path


def render_quote(size, idx, quote, out_path):
    img = new_canvas(*size)
    draw = ImageDraw.Draw(img)
    w, h = size
    draw_top_band(img, draw)
    draw_section_pill(img, draw, ARTICLE_SECTION)

    # Big curly opening quote mark in accent red
    q_mark_font = load_font("serif_bold", 320)
    draw.text((60, 200), "“", font=q_mark_font, fill=ACCENT)

    # Quote text — Playfair, large
    q_font_size = 90 if h >= 1900 else 78
    q_font = load_font("serif_bold", q_font_size)
    q_text = "“" + quote.rstrip(".!? ") + ".”"
    # We've already painted the big floating quote — use plain text without
    # extra leading quotes:
    q_text_clean = quote.rstrip(".!? ") + "."
    # Wrap to width
    max_lines = 9 if h >= 1900 else 7
    while q_font_size >= 50:
        q_font = load_font("serif_bold", q_font_size)
        lines = wrap_text(q_text_clean, q_font, w - 160, draw)
        if len(lines) <= max_lines:
            break
        q_font_size -= 6
    line_h = int(q_font_size * 1.18)
    total_h = len(lines) * line_h
    block_top = (h - total_h) // 2 - 40
    cy = block_top
    for line in lines:
        draw.text((80, cy), line, font=q_font, fill=CARD_FG)
        cy += line_h

    # Attribution under the quote
    attr_font = load_font("sans_bold", 24)
    attr = f"FROM “{ARTICLE_TITLE.upper()}”  ·  BY {ARTICLE_BYLINE.upper()}"
    bbox = draw.textbbox((0, 0), attr, font=attr_font)
    # If attribution is too wide, use a shorter form
    if (bbox[2] - bbox[0]) > w - 160:
        attr = f"“{ARTICLE_TITLE.upper()}”  ·  {ARTICLE_BYLINE.upper()}"
    draw.text((80, cy + 50), attr, font=attr_font, fill=ACCENT)

    # Small index marker top-left under the masthead
    idx_font = load_font("sans_bold", 22)
    draw.text((80, 220), f"PULL-QUOTE  ·  {idx:02d} OF 03",
              font=idx_font, fill=CARD_FG_MUTED)

    draw_bottom_band(img, draw, byline=ARTICLE_BYLINE)
    img.save(out_path, "PNG")
    return out_path


def render_cta(size, out_path):
    img = new_canvas(*size)
    draw = ImageDraw.Draw(img)
    w, h = size
    draw_top_band(img, draw)
    draw_section_pill(img, draw, ARTICLE_SECTION)

    # Eyebrow
    eyebrow_font = load_font("sans_bold", 28)
    draw.text((80, 260), "FROM THE MUTAPA TIMES", font=eyebrow_font, fill=ACCENT)

    # Big headline call-out
    head_font_size = 180 if h >= 1900 else 150
    head_font = load_font("serif_bold", head_font_size)
    lines = wrap_text(CTA_HEADLINE, head_font, w - 160, draw)
    line_h = int(head_font_size * 1.0)
    cy = h // 2 - (len(lines) * line_h) // 2 - 200
    for line in lines:
        draw.text((80, cy), line, font=head_font, fill=CARD_FG)
        cy += line_h

    # Subhead
    sub_font = load_font("sans", 42 if h >= 1900 else 38)
    sub_lines = wrap_text(CTA_SUBHEAD, sub_font, w - 160, draw)
    cy += 50
    for line in sub_lines:
        draw.text((80, cy), line, font=sub_font, fill=CARD_FG_MUTED)
        cy += int(42 * 1.35) if h >= 1900 else int(38 * 1.35)

    # Big URL block in lower-middle
    url_font = load_font("serif_bold", 76 if h >= 1900 else 64)
    url_text = "mutapatimes.com"
    bbox = draw.textbbox((0, 0), url_text, font=url_font)
    ux = (w - (bbox[2] - bbox[0])) // 2
    uy = h - 480 if h >= 1900 else h - 380
    draw.text((ux, uy), url_text, font=url_font, fill=ACCENT)
    # Accent rule under URL
    rule_w = 280
    draw.rectangle([(w - rule_w) // 2, uy + (88 if h >= 1900 else 76),
                    (w + rule_w) // 2, uy + (94 if h >= 1900 else 82)],
                   fill=ACCENT)

    # Direct link path under URL
    path_font = load_font("sans", 26)
    path_text = "/articles/shumba-maasai-in-venice".upper()
    bbox = draw.textbbox((0, 0), path_text, font=path_font)
    px = (w - (bbox[2] - bbox[0])) // 2
    draw.text((px, uy + (130 if h >= 1900 else 115)),
              path_text, font=path_font, fill=CARD_FG_MUTED)

    draw_bottom_band(img, draw, byline=ARTICLE_BYLINE)
    img.save(out_path, "PNG")
    return out_path


# ── Orchestration ────────────────────────────────────────
def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    print(f"=== Rendering Shumba Maasai launch assets → {OUT_DIR} ===")
    plan = [
        # (size, label, renderer fn or callable lambda)
        (STORY,    "story-1-headline",    lambda p: render_headline(STORY, p)),
        (STORY,    "story-2-quote-1",     lambda p: render_quote(STORY, 1, QUOTES[0], p)),
        (STORY,    "story-3-quote-2",     lambda p: render_quote(STORY, 2, QUOTES[1], p)),
        (STORY,    "story-4-quote-3",     lambda p: render_quote(STORY, 3, QUOTES[2], p)),
        (STORY,    "story-5-cta",         lambda p: render_cta(STORY, p)),
        (PORTRAIT, "portrait-1-headline", lambda p: render_headline(PORTRAIT, p)),
        (PORTRAIT, "portrait-2-quote-1",  lambda p: render_quote(PORTRAIT, 1, QUOTES[0], p)),
        (PORTRAIT, "portrait-3-quote-2",  lambda p: render_quote(PORTRAIT, 2, QUOTES[1], p)),
        (PORTRAIT, "portrait-4-quote-3",  lambda p: render_quote(PORTRAIT, 3, QUOTES[2], p)),
        (PORTRAIT, "portrait-5-cta",      lambda p: render_cta(PORTRAIT, p)),
    ]
    for size, label, fn in plan:
        out = os.path.join(OUT_DIR, f"{label}.png")
        fn(out)
        kb = os.path.getsize(out) // 1024
        print(f"  {size[0]:>4}x{size[1]:<4}  {label:<24s}  {kb:>5} KB")
    print("=== DONE ===")


if __name__ == "__main__":
    main()
