#!/usr/bin/env python3
"""Promotional cards for the Isn't it lovely Venice essay.

Produces ten standalone PNGs to /img/cards/venice-isnt-it-lovely/:

  story-1.png  ...  story-5.png    1080 x 1920  9:16  Instagram / TikTok stories
  portrait-1.png ... portrait-5.png 1080 x 1350  4:5   Instagram feed portrait

Each card carries enough context to read on its own (no caption needed).
Cards are split between dark editorial (the Scene Report palette
#0c1410 / cream #f4ede0 / red #c41e1e) and full-bleed photographic
backgrounds taken from the article's own image set.

Run:
  python3 scripts/build_venice_anchor_cards.py
"""
import os
import sys
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from card_lib import load_font, wrap_text  # noqa: E402

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT_DIR = os.path.join(ROOT, "img", "cards", "venice-isnt-it-lovely")
os.makedirs(OUT_DIR, exist_ok=True)

# ─── palette ───────────────────────────────────────────────────────
FOREST = (12, 20, 16)              # #0c1410 — Scene Report background
CREAM = (244, 237, 224)            # #f4ede0 — Scene Report foreground
RED = (196, 30, 30)                # brand red
GOLD = (184, 137, 61)              # gentle gold accent
INK = (26, 26, 26)
WHITE = (255, 255, 255)

ARTICLE_URL = "mutapatimes.com/scene-report"


# ─── helpers ───────────────────────────────────────────────────────
def open_bg(path, size, *, darken=0.55, blur=0):
    """Open + cover-crop + optional darken/blur the background image."""
    img = Image.open(os.path.join(ROOT, path)).convert("RGB")
    target_w, target_h = size
    iw, ih = img.size
    scale = max(target_w / iw, target_h / ih)
    new_size = (int(iw * scale), int(ih * scale))
    img = img.resize(new_size, Image.LANCZOS)
    # Centre-crop
    left = (img.size[0] - target_w) // 2
    top = (img.size[1] - target_h) // 2
    img = img.crop((left, top, left + target_w, top + target_h))
    if blur:
        img = img.filter(ImageFilter.GaussianBlur(blur))
    if darken:
        overlay = Image.new("RGBA", size, (0, 0, 0, int(255 * darken)))
        img = img.convert("RGBA")
        img.alpha_composite(overlay)
        img = img.convert("RGB")
    return img


def gradient_overlay(img, *, top=0, bottom=200, color=(0, 0, 0)):
    """Paint a vertical alpha-gradient over img (top..bottom alpha values)."""
    w, h = img.size
    grad = Image.new("L", (1, h))
    for y in range(h):
        a = int(top + (bottom - top) * (y / max(1, h - 1)))
        grad.putpixel((0, y), max(0, min(255, a)))
    grad = grad.resize((w, h))
    overlay = Image.new("RGBA", (w, h), color + (0,))
    overlay.putalpha(grad)
    base = img.convert("RGBA")
    base.alpha_composite(overlay)
    return base.convert("RGB")


def draw_text_centered(draw, xy_center, text, font, fill, *, line_spacing=8):
    """Centre a possibly multi-line block of pre-wrapped text on a point."""
    lines = text.split("\n")
    total_h = 0
    line_h = []
    for ln in lines:
        bb = draw.textbbox((0, 0), ln, font=font)
        h = bb[3] - bb[1]
        line_h.append(h)
        total_h += h + line_spacing
    total_h -= line_spacing
    cx, cy = xy_center
    y = cy - total_h // 2
    for i, ln in enumerate(lines):
        bb = draw.textbbox((0, 0), ln, font=font)
        w = bb[2] - bb[0]
        draw.text((cx - w // 2, y - bb[1]), ln, font=font, fill=fill)
        y += line_h[i] + line_spacing


def fit_headline(draw, text, role, max_size, min_size, max_w, max_h):
    """Pick the largest size where text wraps into max_w x max_h.
    Both axes are enforced: a candidate is only acceptable if every
    rendered line is at most max_w wide AND the total stack height
    is at most max_h. Previously we only enforced height, which let
    the headline overflow horizontally when the text was a single
    long line that wrap_text decided to leave alone."""
    size = max_size
    while size >= min_size:
        font = load_font(role, size)
        lines = wrap_text(text, font, max_w, draw)
        if not lines:
            return font, []
        # Width pass: any line wider than max_w forces us smaller.
        widest = 0
        for ln in lines:
            bb = draw.textbbox((0, 0), ln, font=font)
            widest = max(widest, bb[2] - bb[0])
        # Height pass with line-height ~1.12.
        line_metrics = []
        total = 0
        for ln in lines:
            bb = draw.textbbox((0, 0), ln, font=font)
            h = bb[3] - bb[1]
            line_metrics.append((ln, h, bb[1]))
            total += int(h * 1.12)
        if widest <= max_w and total <= max_h:
            return font, line_metrics
        size -= 2
    font = load_font(role, min_size)
    lines = wrap_text(text, font, max_w, draw)
    metrics = []
    for ln in lines:
        bb = draw.textbbox((0, 0), ln, font=font)
        metrics.append((ln, bb[3] - bb[1], bb[1]))
    return font, metrics


def draw_wrapped_block(draw, xy_top_left, text, font, fill, max_w, *, line_h=1.18):
    """Wrap + draw left-aligned. Returns y after the block."""
    x, y = xy_top_left
    lines = wrap_text(text, font, max_w, draw)
    for ln in lines:
        bb = draw.textbbox((0, 0), ln, font=font)
        draw.text((x, y - bb[1]), ln, font=font, fill=fill)
        y += int((bb[3] - bb[1]) * line_h)
    return y


def draw_wordmark(draw, x, y, *, color=CREAM, size=46):
    """Italic Playfair wordmark — The Mutapa Times."""
    font = load_font("serif_italic", size)
    draw.text((x, y), "The Mutapa Times", font=font, fill=color)


def draw_bottom_cta(draw, w, h, *, dark=True, label="Read on mutapatimes.com"):
    """Bottom strip: red bar + label."""
    band_h = 96
    band_y = h - band_h
    if dark:
        # Subtle separator above the band
        draw.rectangle([(0, band_y - 1), (w, band_y)], fill=(244, 237, 224, 60))
    draw.rectangle([(0, band_y), (w, h)], fill=RED)
    font = load_font("sans_bold", 30)
    bb = draw.textbbox((0, 0), label, font=font)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    draw.text(
        ((w - tw) // 2, band_y + (band_h - th) // 2 - bb[1]),
        label,
        font=font,
        fill=WHITE,
    )


def draw_eyebrow(draw, x, y, text, *, color=RED, size=24, letter_spacing_em=0.30):
    """Render an uppercase tracked eyebrow line by character stepping."""
    font = load_font("sans_bold", size)
    cx = x
    for ch in text.upper():
        draw.text((cx, y), ch, font=font, fill=color)
        bb = draw.textbbox((0, 0), ch, font=font)
        cx += (bb[2] - bb[0]) + int(size * letter_spacing_em / 4)
    return cx


def draw_thin_rule(draw, x, y, w, *, color=RED, height=3):
    draw.rectangle([(x, y), (x + w, y + height)], fill=color)


# ─── card 1 (story / portrait) — HERO ─────────────────────────────
def card_hero(size, out_path):
    w, h = size
    img = open_bg(
        "img/uploads/venice-2026/main/biennale-savethedate.jpg",
        size,
        darken=0.40,
        blur=0,
    )
    img = gradient_overlay(img, top=0, bottom=220, color=(0, 0, 0))
    draw = ImageDraw.Draw(img)

    pad = int(w * 0.075)

    # Top brand block — wordmark + rule
    draw_wordmark(draw, pad, int(h * 0.05), color=CREAM, size=int(w * 0.040))
    rule_y = int(h * 0.05) + int(w * 0.040 * 1.4)
    draw_thin_rule(draw, pad, rule_y, int(w * 0.18), color=RED, height=4)

    # Eyebrow
    eye_y = int(h * 0.60)
    eyebrow_font = load_font("sans_bold", int(w * 0.022))
    eyebrow_text = "SCENE REPORT · VENICE · 1 OF 7"
    bb = draw.textbbox((0, 0), eyebrow_text, font=eyebrow_font)
    draw.text((pad, eye_y - bb[1]), eyebrow_text, font=eyebrow_font, fill=GOLD)

    # Headline
    headline = "Isn't it lovely."
    head_max = int(w * 0.18)
    head_min = int(w * 0.10)
    head_font, lines = fit_headline(
        draw, headline, "serif_italic", head_max, head_min, w - 2 * pad, int(h * 0.22)
    )
    hy = eye_y + int(w * 0.045)
    for ln, lh, lt in lines:
        draw.text((pad, hy - lt), ln, font=head_font, fill=CREAM)
        hy += int(lh * 1.08)

    # Deck
    deck_font = load_font("serif_italic", int(w * 0.034))
    deck = "A week in Venice with the Pavilion of Zimbabwe."
    deck_y = hy + int(w * 0.014)
    draw_wrapped_block(draw, (pad, deck_y), deck, deck_font, CREAM, w - 2 * pad)

    # Byline (bottom-left above CTA)
    byl_font = load_font("sans", int(w * 0.020))
    byline = "By Valentine Eluwasi · 12 min read · The Mutapa Times"
    bb = draw.textbbox((0, 0), byline, font=byl_font)
    draw.text(
        (pad, h - 96 - (bb[3] - bb[1]) - 24 - bb[1]),
        byline,
        font=byl_font,
        fill=(244, 237, 224, 220),
    )

    draw_bottom_cta(draw, w, h)
    img.save(out_path, "PNG", optimize=True)


# ─── card 2 — Henry Taylor pull quote ─────────────────────────────
def card_taylor_quote(size, out_path):
    w, h = size
    img = Image.new("RGB", size, FOREST)
    draw = ImageDraw.Draw(img)
    pad = int(w * 0.085)

    draw_wordmark(draw, pad, int(h * 0.05), color=CREAM, size=int(w * 0.040))
    draw_thin_rule(draw, pad, int(h * 0.05) + int(w * 0.040 * 1.4),
                   int(w * 0.18), color=RED, height=4)

    # Mark above quote
    qmark_font = load_font("serif_bold", int(w * 0.30))
    draw.text((pad - int(w * 0.005), int(h * 0.20)), "“",
              font=qmark_font, fill=RED)

    quote = "Isn't it lovely. Isn't it beautiful. Come on. It could be great. Sometimes it's okay."
    q_max = int(w * 0.090)
    q_min = int(w * 0.052)
    q_font, lines = fit_headline(
        draw, quote, "serif_italic", q_max, q_min, w - 2 * pad, int(h * 0.42)
    )
    qy = int(h * 0.36)
    for ln, lh, lt in lines:
        draw.text((pad, qy - lt), ln, font=q_font, fill=CREAM)
        qy += int(lh * 1.10)

    # Attribution
    attr = "HENRY TAYLOR  ·  ON A BOAT IN THE LAGOON"
    attr_font = load_font("sans_bold", int(w * 0.022))
    bb = draw.textbbox((0, 0), attr, font=attr_font)
    draw.text((pad, qy + int(w * 0.030) - bb[1]), attr, font=attr_font, fill=GOLD)

    sub = "Venice · 5 May 2026"
    sub_font = load_font("sans", int(w * 0.022))
    draw.text((pad, qy + int(w * 0.075)), sub, font=sub_font, fill=(244, 237, 224, 200))

    draw_bottom_cta(draw, w, h, label="Read 'Isn't it lovely' on mutapatimes.com")
    img.save(out_path, "PNG", optimize=True)


# ─── card 3 — There is therapy in beauty ──────────────────────────
def card_therapy(size, out_path):
    w, h = size
    img = open_bg(
        "img/uploads/venice-2026/main/elderly-couple.jpg",
        size,
        darken=0.30,
        blur=0,
    )
    img = gradient_overlay(img, top=0, bottom=240, color=(8, 14, 10))
    draw = ImageDraw.Draw(img)
    pad = int(w * 0.085)

    draw_wordmark(draw, pad, int(h * 0.05), color=CREAM, size=int(w * 0.040))
    draw_thin_rule(draw, pad, int(h * 0.05) + int(w * 0.040 * 1.4),
                   int(w * 0.18), color=RED, height=4)

    # Auto-fit the headline. Pass the WHOLE sentence to fit_headline
    # and render whatever lines it returns — earlier I was passing a
    # single line then rendering a different one, so the size pick
    # was wrong and the headline overflowed.
    headline = "There is therapy in beauty."
    fit_font, fit_lines = fit_headline(
        draw, headline, "serif_italic",
        int(w * 0.110), int(w * 0.060),
        w - 2 * pad, int(h * 0.22),
    )
    block_h = 0
    for ln, lh, lt in fit_lines:
        block_h += int(lh * 1.10)
    by = int(h * 0.68) - block_h
    for ln, lh, lt in fit_lines:
        draw.text((pad, by - lt), ln, font=fit_font, fill=CREAM)
        by += int(lh * 1.10)

    # Attribution, with breathing room below the headline block
    attr = "ISN'T IT LOVELY  ·  A LETTER FROM VENICE"
    attr_font = load_font("sans_bold", int(w * 0.022))
    bb = draw.textbbox((0, 0), attr, font=attr_font)
    draw.text((pad, by + int(w * 0.030) - bb[1]),
              attr, font=attr_font, fill=GOLD)

    draw_bottom_cta(draw, w, h)
    img.save(out_path, "PNG", optimize=True)


# ─── card 4 — five artists ────────────────────────────────────────
def card_five_artists(size, out_path):
    w, h = size
    img = Image.new("RGB", size, FOREST)
    draw = ImageDraw.Draw(img)
    pad = int(w * 0.085)

    draw_wordmark(draw, pad, int(h * 0.05), color=CREAM, size=int(w * 0.040))
    draw_thin_rule(draw, pad, int(h * 0.05) + int(w * 0.040 * 1.4),
                   int(w * 0.18), color=RED, height=4)

    eyebrow_y = int(h * 0.22)
    eye_font = load_font("sans_bold", int(w * 0.024))
    eyebrow_text = "PAVILION OF ZIMBABWE · 61ST VENICE BIENNALE"
    bb = draw.textbbox((0, 0), eyebrow_text, font=eye_font)
    draw.text((pad, eyebrow_y - bb[1]), eyebrow_text, font=eye_font, fill=GOLD)

    title = "Five artists.\nOne pavilion."
    t_font = load_font("serif_bold", int(w * 0.105))
    ty = eyebrow_y + int(w * 0.045)
    for ln in title.split("\n"):
        bb = draw.textbbox((0, 0), ln, font=t_font)
        draw.text((pad, ty - bb[1]), ln, font=t_font, fill=CREAM)
        ty += int((bb[3] - bb[1]) * 1.10)

    # Names — left rail with red ticks
    names = [
        "Felix Shumba",
        "Franklyn Dzingai",
        "Gideon Gomo",
        "Pardon Mapondera",
        "Eva Raath",
    ]
    name_font = load_font("serif_bold", int(w * 0.052))
    desc_font = load_font("sans", int(w * 0.022))
    media = [
        "Charcoal",
        "Photography",
        "Bronze",
        "Installation",
        "Textile",
    ]
    ny = ty + int(w * 0.025)
    for n, m in zip(names, media):
        # red square bullet
        sq_size = int(w * 0.013)
        bb = draw.textbbox((0, 0), n, font=name_font)
        draw.rectangle(
            [(pad, ny + (bb[3] - bb[1]) // 2 - sq_size // 2),
             (pad + sq_size, ny + (bb[3] - bb[1]) // 2 + sq_size // 2)],
            fill=RED,
        )
        draw.text((pad + sq_size + int(w * 0.018), ny - bb[1]),
                  n, font=name_font, fill=CREAM)
        # right-aligned medium label
        bb2 = draw.textbbox((0, 0), m.upper(), font=desc_font)
        mw = bb2[2] - bb2[0]
        draw.text(
            (w - pad - mw, ny + (bb[3] - bb[1]) - (bb2[3] - bb2[1]) - int(w * 0.004) - bb2[1]),
            m.upper(),
            font=desc_font,
            fill=GOLD,
        )
        ny += int((bb[3] - bb[1]) * 1.45)

    draw_bottom_cta(draw, w, h, label="Read 'Isn't it lovely' on mutapatimes.com")
    img.save(out_path, "PNG", optimize=True)


# ─── card 5 — CTA / opening-night photographic ───────────────────
def card_cta(size, out_path):
    w, h = size
    img = open_bg(
        "img/uploads/venice-2026/main/opening-night.jpg",
        size,
        darken=0.55,
        blur=1,
    )
    img = gradient_overlay(img, top=80, bottom=200, color=(8, 14, 10))
    draw = ImageDraw.Draw(img)
    pad = int(w * 0.085)

    draw_wordmark(draw, pad, int(h * 0.05), color=CREAM, size=int(w * 0.040))
    draw_thin_rule(draw, pad, int(h * 0.05) + int(w * 0.040 * 1.4),
                   int(w * 0.18), color=RED, height=4)

    title = "A letter from Venice."
    t_font, t_lines = fit_headline(
        draw, title, "serif_italic",
        int(w * 0.120), int(w * 0.070),
        w - 2 * pad, int(h * 0.25),
    )
    ty = int(h * 0.30)
    for ln, lh, lt in t_lines:
        draw.text((pad, ty - lt), ln, font=t_font, fill=CREAM)
        ty += int(lh * 1.06)

    deck_font = load_font("serif_italic", int(w * 0.038))
    deck = "Isn't it lovely — one of seven dispatches from the eighth Pavilion of Zimbabwe at the 61st Venice Biennale."
    draw_wrapped_block(draw,
                       (pad, ty + int(w * 0.030)),
                       deck, deck_font, CREAM, w - 2 * pad,
                       line_h=1.30)

    # Bottom pill CTA (inset above the band)
    pill_y = h - 96 - int(w * 0.16)
    pill_h = int(w * 0.090)
    pill_w = int(w * 0.62)
    pill_x = (w - pill_w) // 2
    draw.rounded_rectangle(
        [(pill_x, pill_y), (pill_x + pill_w, pill_y + pill_h)],
        radius=pill_h // 2,
        fill=RED,
    )
    pill_font = load_font("sans_bold", int(w * 0.030))
    pill_label = "Read it · mutapatimes.com"
    bb = draw.textbbox((0, 0), pill_label, font=pill_font)
    draw.text(
        (pill_x + (pill_w - (bb[2] - bb[0])) // 2,
         pill_y + (pill_h - (bb[3] - bb[1])) // 2 - bb[1]),
        pill_label,
        font=pill_font,
        fill=WHITE,
    )

    draw_bottom_cta(draw, w, h, label="The Mutapa Times · Scene Report")
    img.save(out_path, "PNG", optimize=True)


# ─── card 6 — therapy-in-beauty portrait (different from card 3 with image) ──
def card_therapy_typographic(size, out_path):
    """A purely typographic version of the therapy line — dark forest."""
    w, h = size
    img = Image.new("RGB", size, FOREST)
    draw = ImageDraw.Draw(img)
    pad = int(w * 0.085)

    draw_wordmark(draw, pad, int(h * 0.05), color=CREAM, size=int(w * 0.040))
    draw_thin_rule(draw, pad, int(h * 0.05) + int(w * 0.040 * 1.4),
                   int(w * 0.18), color=RED, height=4)

    headline = "There is therapy in beauty."
    fit_font, fit_lines = fit_headline(
        draw, headline, "serif_italic",
        int(w * 0.115), int(w * 0.060),
        w - 2 * pad, int(h * 0.35),
    )
    block_h = 0
    for ln, lh, lt in fit_lines:
        block_h += int(lh * 1.10)
    cy = (h - block_h) // 2
    for ln, lh, lt in fit_lines:
        draw.text((pad, cy - lt), ln, font=fit_font, fill=CREAM)
        cy += int(lh * 1.10)

    attr = "ISN'T IT LOVELY  ·  A LETTER FROM VENICE"
    attr_font = load_font("sans_bold", int(w * 0.022))
    bb = draw.textbbox((0, 0), attr, font=attr_font)
    draw.text((pad, h - 96 - int(w * 0.045) - bb[1]),
              attr, font=attr_font, fill=GOLD)

    draw_bottom_cta(draw, w, h)
    img.save(out_path, "PNG", optimize=True)


# ─── card 7 — stats card ──────────────────────────────────────────
def card_stats(size, out_path):
    w, h = size
    img = Image.new("RGB", size, FOREST)
    draw = ImageDraw.Draw(img)
    pad = int(w * 0.085)

    draw_wordmark(draw, pad, int(h * 0.05), color=CREAM, size=int(w * 0.040))
    draw_thin_rule(draw, pad, int(h * 0.05) + int(w * 0.040 * 1.4),
                   int(w * 0.18), color=RED, height=4)

    eye_font = load_font("sans_bold", int(w * 0.024))
    eyebrow_text = "PAVILION OF ZIMBABWE · IN NUMBERS"
    bb = draw.textbbox((0, 0), eyebrow_text, font=eye_font)
    draw.text((pad, int(h * 0.22) - bb[1]), eyebrow_text, font=eye_font, fill=GOLD)

    # Four stat blocks stacked. Use a fixed left column for the figure
    # that's wide enough for the widest figure (100%), measure each
    # figure for the actual width, and place the label start past the
    # column boundary with breathing room. Earlier the figure column
    # was 0.32w and "100%" rendered past it into the label.
    stats = [
        ("8th", "Edition of the Pavilion of Zimbabwe at Venice."),
        ("5",   "Zimbabwean artists in the official pavilion."),
        ("100%", "African capital underwriting the 2026 pavilion."),
        ("30+", "Countries reached by The Mutapa Times briefing."),
    ]
    fig_font = load_font("serif_bold", int(w * 0.110))
    label_font = load_font("sans", int(w * 0.024))
    # Figure column = widest figure + comfortable gutter
    widest = 0
    for fig, _ in stats:
        bb = draw.textbbox((0, 0), fig, font=fig_font)
        widest = max(widest, bb[2] - bb[0])
    col_gutter = int(w * 0.05)
    lbl_x = pad + widest + col_gutter
    y = int(h * 0.32)
    row_h = int(h * 0.135)
    for fig, label in stats:
        bb = draw.textbbox((0, 0), fig, font=fig_font)
        draw.text((pad, y - bb[1]), fig, font=fig_font, fill=CREAM)
        # Label start is fixed; centred vertically against the figure.
        label_baseline = y + (bb[3] - bb[1]) // 2 - int(label_font.size * 0.4)
        draw_wrapped_block(draw, (lbl_x, label_baseline),
                           label, label_font,
                           (244, 237, 224, 220),
                           w - lbl_x - pad,
                           line_h=1.25)
        # thin rule between rows
        rule_y = y + row_h - int(w * 0.020)
        draw.line([(pad, rule_y), (w - pad, rule_y)],
                  fill=(244, 237, 224, 50), width=1)
        y += row_h

    draw_bottom_cta(draw, w, h, label="The Mutapa Times · Scene Report")
    img.save(out_path, "PNG", optimize=True)


# ─── card 8 — series promo ───────────────────────────────────────
def card_series_promo(size, out_path):
    w, h = size
    img = open_bg(
        "img/uploads/isnt_it_lovely/joanna_masiyiwa_speach_during_theopening.jpeg",
        size,
        darken=0.55,
        blur=0,
    )
    img = gradient_overlay(img, top=40, bottom=230, color=(8, 14, 10))
    draw = ImageDraw.Draw(img)
    pad = int(w * 0.085)

    draw_wordmark(draw, pad, int(h * 0.05), color=CREAM, size=int(w * 0.040))
    draw_thin_rule(draw, pad, int(h * 0.05) + int(w * 0.040 * 1.4),
                   int(w * 0.18), color=RED, height=4)

    eye_font = load_font("sans_bold", int(w * 0.024))
    eyebrow_text = "A NEW SERIES FROM THE MUTAPA TIMES"
    bb = draw.textbbox((0, 0), eyebrow_text, font=eye_font)
    eye_y = int(h * 0.55)
    draw.text((pad, eye_y - bb[1]), eyebrow_text, font=eye_font, fill=GOLD)

    title_font = load_font("serif_bold", int(w * 0.108))
    title_lines = ["Scene Report:", "Venice Biennale"]
    ty = eye_y + int(w * 0.040)
    for ln in title_lines:
        bb = draw.textbbox((0, 0), ln, font=title_font)
        draw.text((pad, ty - bb[1]), ln, font=title_font, fill=CREAM)
        ty += int((bb[3] - bb[1]) * 1.06)

    sub_font = load_font("serif_italic", int(w * 0.036))
    sub = "Seven dispatches from Zimbabwe's pavilion at the 61st Venice Biennale."
    draw_wrapped_block(draw, (pad, ty + int(w * 0.015)),
                       sub, sub_font, CREAM,
                       w - 2 * pad, line_h=1.30)

    draw_bottom_cta(draw, w, h, label="Read the series · mutapatimes.com")
    img.save(out_path, "PNG", optimize=True)


# ─── card 9 — opening night roll-call (constellation in the room) ──
def card_roll_call(size, out_path):
    w, h = size
    img = Image.new("RGB", size, FOREST)
    draw = ImageDraw.Draw(img)
    pad = int(w * 0.085)

    draw_wordmark(draw, pad, int(h * 0.05), color=CREAM, size=int(w * 0.040))
    draw_thin_rule(draw, pad, int(h * 0.05) + int(w * 0.040 * 1.4),
                   int(w * 0.18), color=RED, height=4)

    eyebrow = "THE CONSTELLATION IN THE ROOM"
    eye_font = load_font("sans_bold", int(w * 0.024))
    eye_y = int(h * 0.20)
    bb = draw.textbbox((0, 0), eyebrow, font=eye_font)
    draw.text((pad, eye_y - bb[1]), eyebrow, font=eye_font, fill=GOLD)

    sub_font = load_font("serif_italic", int(w * 0.040))
    sub = "Pavilion of Zimbabwe vernissage, 15 May 2026."
    draw.text((pad, eye_y + int(w * 0.035)),
              sub, font=sub_font, fill=(244, 237, 224, 220))

    # Names — single column. The earlier two-column layout shoved long
    # names (Fadzai Veronica Muchemwa, Option Dzikamai Nyahunzvi) into
    # the right column and overlapped them. Single column gives every
    # name its own line at a comfortable serif size.
    names = [
        "Fadzai Veronica Muchemwa",
        "Rory Tsapayi",
        "Joey Masiyiwa",
        "Option Dzikamai Nyahunzvi",
        "Belinda Holden",
        "Georgina Maxim",
        "Virginia Chihota",
        "Portia Zvavahera",
        "Wallen Mapondera",
        "Michele Mathison",
    ]
    name_font = load_font("serif_bold", int(w * 0.038))
    nx_y = eye_y + int(w * 0.105)
    line_h = int(w * 0.060)
    for i, n in enumerate(names):
        yy = nx_y + i * line_h
        dot_r = int(w * 0.008)
        bb = draw.textbbox((0, 0), n, font=name_font)
        cy = yy + (bb[3] - bb[1]) // 2
        draw.ellipse([(pad, cy - dot_r), (pad + dot_r * 2, cy + dot_r)],
                     fill=RED)
        draw.text((pad + dot_r * 2 + int(w * 0.014), yy - bb[1]),
                  n, font=name_font, fill=CREAM)

    foot_font = load_font("sans", int(w * 0.022))
    foot = "Catalogue: Second Nature | Manyonga"
    bb = draw.textbbox((0, 0), foot, font=foot_font)
    draw.text((pad, h - 96 - int(w * 0.045) - bb[1]),
              foot, font=foot_font, fill=GOLD)

    draw_bottom_cta(draw, w, h, label="Read the full essay on mutapatimes.com")
    img.save(out_path, "PNG", optimize=True)


# ─── card 10 — the algorithm-credit beat ──────────────────────────
def card_algorithm_optimism(size, out_path):
    w, h = size
    img = open_bg(
        "img/uploads/venice-2026/main/venice-canal.jpg",
        size,
        darken=0.55,
        blur=0,
    )
    img = gradient_overlay(img, top=40, bottom=210, color=(8, 14, 10))
    draw = ImageDraw.Draw(img)
    pad = int(w * 0.085)

    draw_wordmark(draw, pad, int(h * 0.05), color=CREAM, size=int(w * 0.040))
    draw_thin_rule(draw, pad, int(h * 0.05) + int(w * 0.040 * 1.4),
                   int(w * 0.18), color=RED, height=4)

    quote = "For once, I will give the algorithm credit."
    q_max = int(w * 0.090)
    q_min = int(w * 0.055)
    q_font, lines = fit_headline(
        draw, quote, "serif_italic", q_max, q_min, w - 2 * pad, int(h * 0.30)
    )
    qy = int(h * 0.40)
    for ln, lh, lt in lines:
        draw.text((pad, qy - lt), ln, font=q_font, fill=CREAM)
        qy += int(lh * 1.08)

    sub_font = load_font("serif_italic", int(w * 0.036))
    sub = "It handed me a small bit of optimism."
    draw_wrapped_block(draw, (pad, qy + int(w * 0.025)),
                       sub, sub_font, (244, 237, 224, 220),
                       w - 2 * pad, line_h=1.30)

    attr = "FROM 'ISN'T IT LOVELY'  ·  VALENTINE ELUWASI"
    attr_font = load_font("sans_bold", int(w * 0.022))
    bb = draw.textbbox((0, 0), attr, font=attr_font)
    draw.text((pad, h - 96 - int(w * 0.045) - bb[1]),
              attr, font=attr_font, fill=GOLD)

    draw_bottom_cta(draw, w, h)
    img.save(out_path, "PNG", optimize=True)


# ─── card plan ─────────────────────────────────────────────────────
STORY = (1080, 1920)   # 9:16
PORTR = (1080, 1350)   # 4:5

STORY_PLAN = [
    ("story-1-hero.png",            card_hero),
    ("story-2-taylor-quote.png",    card_taylor_quote),
    ("story-3-therapy-in-beauty.png", card_therapy),
    ("story-4-five-artists.png",    card_five_artists),
    ("story-5-cta.png",             card_cta),
]

PORTRAIT_PLAN = [
    ("portrait-1-hero.png",          card_hero),
    ("portrait-2-therapy.png",       card_therapy_typographic),
    ("portrait-3-taylor-quote.png",  card_taylor_quote),
    ("portrait-4-stats.png",         card_stats),
    ("portrait-5-roll-call.png",     card_roll_call),
]

# Two extras the user can swap in if they want:
EXTRAS = [
    ("extra-algorithm.png",     card_algorithm_optimism, PORTR),
    ("extra-series-promo.png",  card_series_promo,       STORY),
]


def main():
    for fn, builder in STORY_PLAN:
        out = os.path.join(OUT_DIR, fn)
        builder(STORY, out)
        print(f"  wrote {out}  (1080x1920)")
    for fn, builder in PORTRAIT_PLAN:
        out = os.path.join(OUT_DIR, fn)
        builder(PORTR, out)
        print(f"  wrote {out}  (1080x1350)")
    for fn, builder, size in EXTRAS:
        out = os.path.join(OUT_DIR, fn)
        builder(size, out)
        print(f"  wrote {out}  ({size[0]}x{size[1]})")
    print(f"\nDone. 10 cards (+2 extras) in {OUT_DIR}")


if __name__ == "__main__":
    main()
