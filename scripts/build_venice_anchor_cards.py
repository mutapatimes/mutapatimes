#!/usr/bin/env python3
"""Render 10 launch cards (x2 sizes) for the Isn't it lovely Venice
Biennale anchor essay. Forked from build_ruka_assets.py — same
visual vocabulary (butter background, dark Playfair headlines, red
accent, MUTAPATIMES.COM footer band), new content.

Output:
  img/cards/venice-isnt-it-lovely/story-NN-*.png      1080 x 1920
  img/cards/venice-isnt-it-lovely/portrait-NN-*.png   1080 x 1350
"""
import os
import sys
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from card_lib import (  # noqa: E402
    BUTTER, CARD_FG, CARD_FG_MUTED, ACCENT, load_font, wrap_text,
)

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT_DIR = os.path.join(ROOT, "img", "cards", "venice-isnt-it-lovely")

STORY = (1080, 1920)
PORTRAIT = (1080, 1350)
BRAND_TOP = (240, 224, 188)

ARTICLE_URL = "mutapatimes.com"
ARTICLE_SECTION = "ARTS"
ARTICLE_BYLINE = "Valentine Eluwasi"
ARTICLE_TITLE = "Isn't it lovely."
ARTICLE_DECK = (
    "A letter from Venice, written in the wake of the opening of "
    "Zimbabwe's eighth pavilion at the 61st Biennale."
)

# Six quotes the user nominated, in the order they appear in the
# narrative. Each renders on its own pull-quote card.
QUOTES = [
    {
        "text": "I will give the algorithm credit. It handed me a small bit of optimism: a fifty-second video by the American painter Henry Taylor, posted earlier that day.",
        "attr": "VALENTINE ELUWASI",
        "src":  "FROM 'ISN'T IT LOVELY' · THE MUTAPA TIMES",
    },
    {
        "text": "Isn't it lovely. Isn't it beautiful. Come on. It could be great. Sometimes it's okay.",
        "attr": "HENRY TAYLOR",
        "src":  "ON A BOAT IN THE LAGOON · VENICE · 5 MAY 2026",
    },
    {
        "text": "It is something closer to a long companion essay, with photography and ephemera, designed to sit alongside the official record rather than to replicate it.",
        "attr": "VALENTINE ELUWASI",
        "src":  "ON THE 1925 GLEN NORAH BOOK · 'ISN'T IT LOVELY'",
    },
    {
        "text": "The lineage was visible in the room. People who had been the pavilion in 2013, in 2015, in 2019, in 2022 had come back to be the pavilion's audience in 2026.",
        "attr": "VALENTINE ELUWASI",
        "src":  "FROM 'ISN'T IT LOVELY' · THE MUTAPA TIMES",
    },
    {
        "text": "The pavilion was beauty. The lagoon walls were beauty, in their long argument with the weather. The friends and the alumni in the room on opening night were beauty.",
        "attr": "VALENTINE ELUWASI",
        "src":  "FROM 'ISN'T IT LOVELY' · THE MUTAPA TIMES",
    },
]

CTA_HEADLINE = "Read the letter."
CTA_SUBHEAD = "A Scene Report from the 61st Venice Biennale, hand-edited from our newsroom."
CTA_PATH = "/articles/2026-05-14-second-nature-manyonga-venice-biennale-pavilion-of-zimbabwe"


# ─── reusable chrome (matches build_ruka_assets.py) ────────────────
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


# ─── card renderers ───────────────────────────────────────────────
def render_headline(size, out_path):
    img = new_canvas(*size)
    draw = ImageDraw.Draw(img)
    w, h = size
    draw_top_band(img, draw)
    draw_section_pill(img, draw, ARTICLE_SECTION)

    eyebrow_font = load_font("sans_bold", 28)
    draw.text((80, 280),
              "SCENE REPORT  ·  VENICE BIENNALE  ·  1 OF 7",
              font=eyebrow_font, fill=ACCENT)

    deck_font_size = 38 if h >= 1900 else 34
    deck_font = load_font("sans", deck_font_size)
    deck_lines = wrap_text(ARTICLE_DECK, deck_font, w - 160, draw)
    cy = 360
    for line in deck_lines:
        draw.text((80, cy), line, font=deck_font, fill=CARD_FG_MUTED)
        cy += int(deck_font_size * 1.35)

    by_font = load_font("sans_bold", 22)
    draw.text((80, h - 280),
              f"BY {ARTICLE_BYLINE.upper()}  ·  ARTS",
              font=by_font, fill=CARD_FG)

    draw_bottom_band(img, draw, byline=ARTICLE_BYLINE)
    img.save(out_path, "PNG")


def render_quote(size, idx, total, quote, out_path):
    img = new_canvas(*size)
    draw = ImageDraw.Draw(img)
    w, h = size
    draw_top_band(img, draw)
    draw_section_pill(img, draw, ARTICLE_SECTION)

    # Pull-quote position index, like the Ruka cards
    idx_font = load_font("sans_bold", 22)
    draw.text((80, 220), f"PULL-QUOTE  ·  {idx:02d} OF {total:02d}",
              font=idx_font, fill=CARD_FG_MUTED)

    # Quote body — opening and closing curly marks inline, in the body
    # colour. Auto-fit so even the longer quotes fit a comfortable
    # number of lines and leave room for the attribution + footer band.
    q_text_clean = "“" + quote["text"].rstrip(".!? ") + ".”"
    safe_w = w - 160
    text_top_min = 280
    text_bottom_max = h - 180 - 160  # bottom band + attribution block
    avail_h = text_bottom_max - text_top_min
    q_font_size = 90 if h >= 1900 else 78
    lines = None
    while q_font_size >= 40:
        q_font = load_font("serif_bold", q_font_size)
        lines = wrap_text(q_text_clean, q_font, safe_w, draw)
        widest = 0
        for ln in lines:
            bb = draw.textbbox((0, 0), ln, font=q_font)
            widest = max(widest, bb[2] - bb[0])
        line_h = int(q_font_size * 1.18)
        if widest <= safe_w and len(lines) * line_h <= avail_h:
            break
        q_font_size -= 4
    q_font = load_font("serif_bold", q_font_size)
    line_h = int(q_font_size * 1.18)

    total_h = len(lines) * line_h
    block_top = text_top_min + max(0, (avail_h - total_h) // 2 - 30)
    cy = block_top
    for line in lines:
        draw.text((80, cy), line, font=q_font, fill=CARD_FG)
        cy += line_h

    attr_font = load_font("sans_bold", 24)
    attr = quote["attr"]
    bb = draw.textbbox((0, 0), attr, font=attr_font)
    draw.text((80, cy + 50), attr, font=attr_font, fill=ACCENT)

    src_font = load_font("sans", 20)
    draw.text((80, cy + 86), quote["src"],
              font=src_font, fill=CARD_FG_MUTED)

    draw_bottom_band(img, draw, byline=ARTICLE_BYLINE)
    img.save(out_path, "PNG")


def render_stat(size, big_text, label, support, out_path,
                index_label=None, eyebrow=None):
    img = new_canvas(*size)
    draw = ImageDraw.Draw(img)
    w, h = size
    draw_top_band(img, draw)
    draw_section_pill(img, draw, ARTICLE_SECTION)

    eyebrow_font = load_font("sans_bold", 28)
    draw.text((80, 260), (eyebrow or "BY THE NUMBERS").upper(),
              font=eyebrow_font, fill=ACCENT)

    if index_label:
        idx_font = load_font("sans_bold", 22)
        draw.text((80, 220), index_label.upper(),
                  font=idx_font, fill=CARD_FG_MUTED)

    big_size = 360 if h >= 1900 else 300
    while big_size >= 140:
        big_font = load_font("serif_bold", big_size)
        bbox = draw.textbbox((0, 0), big_text, font=big_font)
        if (bbox[2] - bbox[0]) <= w - 160:
            break
        big_size -= 14
    big_font = load_font("serif_bold", big_size)
    bbox = draw.textbbox((0, 0), big_text, font=big_font)
    bw = bbox[2] - bbox[0]
    bh = bbox[3] - bbox[1]
    bx = (w - bw) // 2
    by = (h // 2) - bh - 40
    draw.text((bx, by), big_text, font=big_font, fill=CARD_FG)

    rule_w = bw + 40
    rule_y = by + bh + 36
    draw.rectangle([(w - rule_w) // 2, rule_y,
                    (w + rule_w) // 2, rule_y + 5], fill=ACCENT)

    label_font = load_font("sans_bold", 30)
    label_text = label.upper()
    lbbox = draw.textbbox((0, 0), label_text, font=label_font)
    lx = (w - (lbbox[2] - lbbox[0])) // 2
    draw.text((lx, rule_y + 30), label_text, font=label_font, fill=CARD_FG_MUTED)

    support_font_size = 36 if h >= 1900 else 32
    support_font = load_font("sans", support_font_size)
    support_lines = wrap_text(support, support_font, w - 220, draw)
    cy = rule_y + 100
    for line in support_lines:
        sbbox = draw.textbbox((0, 0), line, font=support_font)
        sx = (w - (sbbox[2] - sbbox[0])) // 2
        draw.text((sx, cy), line, font=support_font, fill=CARD_FG)
        cy += int(support_font_size * 1.35)

    draw_bottom_band(img, draw, byline=ARTICLE_BYLINE)
    img.save(out_path, "PNG")


def render_artists(size, out_path):
    """Pavilion artists roll-call — substitutes for the Ruka "founder"
    card. Replaces a single founder profile with the five-artist line-up."""
    img = new_canvas(*size)
    draw = ImageDraw.Draw(img)
    w, h = size
    draw_top_band(img, draw)
    draw_section_pill(img, draw, ARTICLE_SECTION)

    eyebrow_font = load_font("sans_bold", 28)
    draw.text((80, 260), "MEET THE ARTISTS", font=eyebrow_font, fill=ACCENT)

    name_font_size = 92 if h >= 1900 else 78
    name_font = load_font("serif_bold", name_font_size)
    title_lines = wrap_text("Pavilion of Zimbabwe.", name_font, w - 160, draw)
    cy = 340
    for line in title_lines:
        draw.text((80, cy), line, font=name_font, fill=CARD_FG)
        cy += int(name_font_size * 1.02)

    sub_font = load_font("serif_italic", 44 if h >= 1900 else 38)
    sub_text = "Five artists, one room, 61st Venice Biennale."
    sub_lines = wrap_text(sub_text, sub_font, w - 160, draw)
    cy += 30
    for line in sub_lines:
        draw.text((80, cy), line, font=sub_font, fill=CARD_FG_MUTED)
        cy += int(sub_font.size * 1.25)

    bullets = [
        "Felix Shumba",
        "Franklyn Dzingai",
        "Gideon Gomo",
        "Pardon Mapondera",
        "Eva Raath",
    ]
    cv_font = load_font("sans_bold", 32 if h >= 1900 else 28)
    cy += 50
    for name in bullets:
        dot_r = 8
        draw.ellipse([80, cy + 14, 80 + dot_r * 2, cy + 14 + dot_r * 2],
                     fill=ACCENT)
        draw.text((80 + 30, cy), name, font=cv_font, fill=CARD_FG)
        cy += int(cv_font.size * 1.55)

    draw_bottom_band(img, draw, byline=ARTICLE_BYLINE)
    img.save(out_path, "PNG")


def render_cta(size, out_path):
    img = new_canvas(*size)
    draw = ImageDraw.Draw(img)
    w, h = size
    draw_top_band(img, draw)
    draw_section_pill(img, draw, ARTICLE_SECTION)

    eyebrow_font = load_font("sans_bold", 28)
    draw.text((80, 260), "FROM THE MUTAPA TIMES",
              font=eyebrow_font, fill=ACCENT)

    head_font_size = 200 if h >= 1900 else 170
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
    path_text = "/SCENE-REPORT · VENICE BIENNALE"
    bbox = draw.textbbox((0, 0), path_text, font=path_font)
    px = (w - (bbox[2] - bbox[0])) // 2
    draw.text((px, uy + (130 if h >= 1900 else 115)),
              path_text, font=path_font, fill=CARD_FG_MUTED)

    draw_bottom_band(img, draw, byline=ARTICLE_BYLINE)
    img.save(out_path, "PNG")


# ─── ten-card narrative arc ────────────────────────────────────────
def build_plan(size, prefix):
    """Narrative arc, ten beats:
       1  headline
       2  PULL-QUOTE 1 of 5 — give the algorithm credit
       3  stat — US$10.1m exports
       4  PULL-QUOTE 2 of 5 — Henry Taylor's "isn't it lovely"
       5  stat — US$70bn market by 2032
       6  meet the artists (five-name roll)
       7  PULL-QUOTE 3 of 5 — the 1925 Glen Norah book
       8  PULL-QUOTE 4 of 5 — the lineage in the room
       9  PULL-QUOTE 5 of 5 — the pavilion was beauty
       10 CTA — read the letter on mutapatimes.com
    """
    quotes_used = 5
    return [
        (f"{prefix}-01-headline",
            lambda p: render_headline(size, p)),
        (f"{prefix}-02-quote-algorithm",
            lambda p: render_quote(size, 1, quotes_used, QUOTES[0], p)),
        (f"{prefix}-03-exports",
            lambda p: render_stat(
                size, "US$10.1m", "Zimbabwean art & craft exports",
                "ZimTrade reports the 2023 figure, roughly double the "
                "US$5.4m exported in 2020. The Venice pavilion sits "
                "inside that growing line item.",
                p, eyebrow="WHY THIS MATTERS")),
        (f"{prefix}-04-quote-taylor",
            lambda p: render_quote(size, 2, quotes_used, QUOTES[1], p)),
        (f"{prefix}-05-market-size",
            lambda p: render_stat(
                size, "US$70bn", "Global art & craft market by 2032",
                "Projected at a 5.6% CAGR. Zimbabwe is positioned to "
                "take a larger share if quality and capacity scale "
                "with demand.",
                p, eyebrow="THE OPPORTUNITY")),
        (f"{prefix}-06-artists",
            lambda p: render_artists(size, p)),
        (f"{prefix}-07-quote-glennorah",
            lambda p: render_quote(size, 3, quotes_used, QUOTES[2], p)),
        (f"{prefix}-08-quote-lineage",
            lambda p: render_quote(size, 4, quotes_used, QUOTES[3], p)),
        (f"{prefix}-09-quote-beauty",
            lambda p: render_quote(size, 5, quotes_used, QUOTES[4], p)),
        (f"{prefix}-10-cta",
            lambda p: render_cta(size, p)),
    ]


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    # Wipe any previous output so we don't leave stale cards behind
    for fn in os.listdir(OUT_DIR):
        if fn.endswith(".png"):
            os.remove(os.path.join(OUT_DIR, fn))

    print(f"=== Rendering Venice / Isn't it lovely cards -> {OUT_DIR} ===")
    plan = []
    for size, prefix in [(STORY, "story"), (PORTRAIT, "portrait")]:
        plan.extend((size, label, fn) for (label, fn) in build_plan(size, prefix))
    for size, label, fn in plan:
        out = os.path.join(OUT_DIR, f"{label}.png")
        fn(out)
        kb = os.path.getsize(out) // 1024
        print(f"  {size[0]:>4}x{size[1]:<4}  {label:<32s}  {kb:>5} KB")
    print("=== DONE ===")


if __name__ == "__main__":
    main()
