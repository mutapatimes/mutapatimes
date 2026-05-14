#!/usr/bin/env python3
"""Render 10 launch cards for the Ruka Hair article. Forked from
build_shumba_assets.py — same visual vocabulary, new content."""
import os
import sys
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from card_lib import (
    BUTTER, CARD_FG, CARD_FG_MUTED, ACCENT, load_font, wrap_text,
)

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT_DIR = os.path.join(ROOT, "img", "uploads", "ruka-launch")

STORY = (1080, 1920)
PORTRAIT = (1080, 1350)
BRAND_TOP = (240, 224, 188)

ARTICLE_URL = "mutapatimes.com"
ARTICLE_SECTION = "BUSINESS"
ARTICLE_BYLINE = "Tendai Kuwanda"
ARTICLE_TITLE = "Henkel backs Ruka in $4.5m round"
ARTICLE_DECK = (
    "The London-based textured-hair company founded by Zimbabwean entrepreneur "
    "Varaidzo Tendai Moyo closes a $4.5m round co-led by Henkel Ventures and "
    "Freedom Trail Capital, taking lifetime funding to roughly $10m."
)
QUOTES = [
    "We call ourselves the Apple of haircare.",
    "We want to eradicate human hair out of the whole ecosystem.",
    "A good outcome is having enough capital to make this a category-defining brand. That means being around.",
]
CTA_HEADLINE = "Read the full piece."
CTA_SUBHEAD = "Business reporting that takes Zimbabwean founders seriously."
CTA_PATH = "/articles/henkel-ventures-co-leads-rukas-4-5m-round"


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
    accent_w = 80
    rule_y = h - h_band + 22
    draw.rectangle([(w - accent_w) // 2, rule_y,
                    (w + accent_w) // 2, rule_y + 4], fill=ACCENT)
    url_text = url.upper()
    url_bbox = draw.textbbox((0, 0), url_text, font=url_font)
    ux = (w - (url_bbox[2] - url_bbox[0])) // 2
    draw.text((ux, h - h_band + 50), url_text, font=url_font, fill=CARD_FG)
    if byline:
        tag = byline.upper()
        tag_bbox = draw.textbbox((0, 0), tag, font=tag_font)
        tx = (w - (tag_bbox[2] - tag_bbox[0])) // 2
        draw.text((tx, h - h_band + 105), tag, font=tag_font, fill=CARD_FG_MUTED)


def render_headline(size, out_path):
    img = new_canvas(*size)
    draw = ImageDraw.Draw(img)
    w, h = size
    draw_top_band(img, draw)
    draw_section_pill(img, draw, ARTICLE_SECTION)

    eyebrow_font = load_font("sans_bold", 28)
    draw.text((80, 280), "FUNDING  ·  $4.5M  ·  HENKEL VENTURES",
              font=eyebrow_font, fill=ACCENT)

    head_font_size = 140 if h >= 1900 else 120
    head_font = load_font("serif_bold", head_font_size)
    head_lines = wrap_text(ARTICLE_TITLE, head_font, w - 160, draw)
    line_h = int(head_font_size * 1.05)
    cy = 340
    for line in head_lines:
        draw.text((80, cy), line, font=head_font, fill=CARD_FG)
        cy += line_h

    deck_font_size = 38 if h >= 1900 else 34
    deck_font = load_font("sans", deck_font_size)
    deck_lines = wrap_text(ARTICLE_DECK, deck_font, w - 160, draw)
    cy += 60
    for line in deck_lines:
        draw.text((80, cy), line, font=deck_font, fill=CARD_FG_MUTED)
        cy += int(deck_font_size * 1.35)

    by_font = load_font("sans_bold", 22)
    draw.text((80, h - 280),
              f"BY {ARTICLE_BYLINE.upper()}  ·  BUSINESS",
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

    q_mark_font = load_font("serif_bold", 320)
    draw.text((60, 200), "“", font=q_mark_font, fill=ACCENT)

    q_font_size = 90 if h >= 1900 else 78
    q_text_clean = quote.rstrip(".!? ") + "."
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

    attr_font = load_font("sans_bold", 22)
    attr = "VARAIDZO TENDAI MOYO  ·  CO-FOUNDER & CEO, RUKA"
    bbox = draw.textbbox((0, 0), attr, font=attr_font)
    if (bbox[2] - bbox[0]) > w - 160:
        attr = "TENDAI MOYO  ·  CO-FOUNDER & CEO"
    draw.text((80, cy + 50), attr, font=attr_font, fill=ACCENT)
    # Source credit — quotes were given to Beauty Independent /
    # The Business of Beauty, not to The Mutapa Times.
    src_font = load_font("sans", 18)
    src_text = "VIA BEAUTY INDEPENDENT" if idx != 3 else "VIA BEAUTY INDEPENDENT"
    draw.text((80, cy + 84), src_text, font=src_font, fill=CARD_FG_MUTED)

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

    eyebrow_font = load_font("sans_bold", 28)
    draw.text((80, 260), "FROM THE MUTAPA TIMES", font=eyebrow_font, fill=ACCENT)

    head_font_size = 180 if h >= 1900 else 150
    head_font = load_font("serif_bold", head_font_size)
    lines = wrap_text(CTA_HEADLINE, head_font, w - 160, draw)
    line_h = int(head_font_size * 1.0)
    cy = h // 2 - (len(lines) * line_h) // 2 - 200
    for line in lines:
        draw.text((80, cy), line, font=head_font, fill=CARD_FG)
        cy += line_h

    sub_font_size = 38 if h >= 1900 else 34
    sub_font = load_font("sans", sub_font_size)
    sub_lines = wrap_text(CTA_SUBHEAD, sub_font, w - 160, draw)
    cy += 50
    for line in sub_lines:
        draw.text((80, cy), line, font=sub_font, fill=CARD_FG_MUTED)
        cy += int(sub_font_size * 1.35)

    url_font = load_font("serif_bold", 76 if h >= 1900 else 64)
    url_text = "mutapatimes.com"
    bbox = draw.textbbox((0, 0), url_text, font=url_font)
    ux = (w - (bbox[2] - bbox[0])) // 2
    uy = h - 480 if h >= 1900 else h - 380
    draw.text((ux, uy), url_text, font=url_font, fill=ACCENT)
    rule_w = 280
    draw.rectangle([(w - rule_w) // 2, uy + (88 if h >= 1900 else 76),
                    (w + rule_w) // 2, uy + (94 if h >= 1900 else 82)],
                   fill=ACCENT)

    path_font = load_font("sans", 22)
    path_text = CTA_PATH.upper()
    if draw.textbbox((0, 0), path_text, font=path_font)[2] > w - 120:
        path_text = "/HENKEL-CO-LEADS-RUKA"
    bbox = draw.textbbox((0, 0), path_text, font=path_font)
    px = (w - (bbox[2] - bbox[0])) // 2
    draw.text((px, uy + (130 if h >= 1900 else 115)),
              path_text, font=path_font, fill=CARD_FG_MUTED)

    draw_bottom_band(img, draw, byline=ARTICLE_BYLINE)
    img.save(out_path, "PNG")
    return out_path


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    print(f"=== Rendering Ruka launch assets → {OUT_DIR} ===")
    plan = [
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
