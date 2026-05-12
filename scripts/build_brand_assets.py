#!/usr/bin/env python3
"""Render the Mutapa Times brand-asset set.

Outputs (img/brand/):
    wordmark-light.png      transparent bg · ink wordmark · 2400x768
    wordmark-dark.png       transparent bg · cream wordmark · 2400x768
    mark-1080.png           profile-pic monogram · 1080x1080
    mark-512.png            smaller monogram · 512x512
    mark-favicon-256.png    favicon-grade monogram · 256x256
    og-share.png            social share preview · 1200x630
    twitter-header.png      Twitter banner · 1500x500

Run after a brand tweak (CSS or this script):

    python3 scripts/build_brand_assets.py

Outputs are committed; the next deploy serves them. Twitter / IG /
LinkedIn profile images need to be uploaded manually after a refresh.
"""
import os
import sys

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("ERROR: Pillow not installed. Run: pip install Pillow")
    sys.exit(1)

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT_DIR = os.path.join(ROOT, "img", "brand")

# ── Brand palette ──────────────────────────────────────────────
INK = (26, 26, 26)
PAPER = (250, 250, 247)         # off-white site background
PAPER_DEEP = (236, 226, 207)    # warm cream — used for accent panels
ACCENT = (196, 30, 30)          # brand red
CREAM = (245, 232, 200)         # soft butter — alt panel
MUTED = (95, 92, 84)


FONT_ROLES = {
    "serif_bold": [
        "fonts/PlayfairDisplay-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
        "/System/Library/Fonts/Supplemental/Georgia Bold.ttf",
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
    return ImageFont.load_default()


def text_width(draw, text, font):
    return draw.textlength(text, font=font)


# ── 1. Wordmark — the canonical horizontal lockup ─────────────
def render_wordmark(out_path, width=2400, fg=INK, with_subtitle=True,
                    transparent=True, padding_ratio=0.06):
    """Centered wordmark: 'THE MUTAPA TIMES' over red accent rule
    over 'ZIMBABWE OUTSIDE-IN'. Aspect ~3.1:1."""
    height = int(width * 0.32)
    if transparent:
        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    else:
        img = Image.new("RGB", (width, height), PAPER)
    draw = ImageDraw.Draw(img)

    # Title — pick the largest Playfair Display Bold that fits in
    # (width - 2*pad) with a small letter-spacing tighten visually.
    title = "THE MUTAPA TIMES"
    pad = int(width * padding_ratio)
    target_w = width - 2 * pad

    # Binary-search-ish sizing — Playfair Bold at given px
    title_px = int(height * 0.45)
    title_font = load_font("serif_bold", title_px)
    while text_width(draw, title, title_font) > target_w and title_px > 60:
        title_px -= 4
        title_font = load_font("serif_bold", title_px)
    tw = text_width(draw, title, title_font)

    # Vertical centre of the title — leave room above for breathing,
    # below for the rule + subtitle.
    title_y = int(height * 0.22)
    draw.text(((width - tw) / 2, title_y), title,
              font=title_font, fill=fg)

    # Red accent rule
    rule_y = title_y + title_px + int(height * 0.05)
    rule_w = int(width * 0.085)
    rule_x = (width - rule_w) // 2
    draw.rectangle([(rule_x, rule_y), (rule_x + rule_w, rule_y + 6)],
                   fill=ACCENT)

    # Subtitle — Inter caps with wide tracking
    if with_subtitle:
        sub = "ZIMBABWE OUTSIDE-IN"
        sub_px = int(height * 0.10)
        sub_font = load_font("sans_bold", sub_px)
        # Approximate "tracked" rendering by inserting hair spaces
        # between glyphs. Most fonts won't render U+200A perfectly,
        # but the visual feel is right.
        tracked = "   ".join(list(sub))
        sw = text_width(draw, tracked, sub_font)
        if sw > target_w:
            tracked = " ".join(list(sub))
            sw = text_width(draw, tracked, sub_font)
        sub_y = rule_y + 20
        draw.text(((width - sw) / 2, sub_y), tracked,
                  font=sub_font, fill=MUTED if fg == INK else fg)

    img.save(out_path, "PNG", optimize=True)


# ── 2. Mark — square monogram (profile pic / favicon) ────────
def render_mark(out_path, size=1080, bg=PAPER, fg=INK):
    """Square M·T monogram. Playfair Display Black with a red dot
    between the letters. Works as IG profile, favicon, dark/light bg."""
    img = Image.new("RGB", (size, size), bg)
    draw = ImageDraw.Draw(img)

    # Find the largest font size that fits 'MT' nicely with margin
    monogram_left = "M"
    monogram_right = "T"
    dot_char = "·"   # U+00B7

    px = int(size * 0.62)
    font = load_font("serif_bold", px)
    # Measure each glyph separately
    while True:
        font = load_font("serif_bold", px)
        wl = text_width(draw, monogram_left, font)
        wr = text_width(draw, monogram_right, font)
        wdot = text_width(draw, dot_char, font)
        gap = int(size * 0.04)
        total = wl + gap + wdot + gap + wr
        if total < size * 0.82:
            break
        px -= 6
        if px < 40:
            break

    # Vertical center via the M bounding box
    bbox = draw.textbbox((0, 0), monogram_left, font=font)
    glyph_h = bbox[3] - bbox[1]
    y = (size - glyph_h) // 2 - bbox[1] - int(size * 0.02)

    x = (size - total) // 2
    draw.text((x, y), monogram_left, font=font, fill=fg)
    x += wl + gap
    draw.text((x, y), dot_char, font=font, fill=ACCENT)
    x += wdot + gap
    draw.text((x, y), monogram_right, font=font, fill=fg)

    img.save(out_path, "PNG", optimize=True)


# ── 3. og:share — large social preview card ───────────────────
def render_og_share(out_path, width=1200, height=630):
    """1200x630 social-share image. Wordmark centred on paper bg
    with subtle accent rule. Replaces the old Harare skyline banner."""
    img = Image.new("RGB", (width, height), PAPER)
    draw = ImageDraw.Draw(img)

    # Top accent block
    draw.rectangle([(0, 0), (140, 8)], fill=ACCENT)

    # Title
    title = "THE MUTAPA TIMES"
    title_px = 110
    title_font = load_font("serif_bold", title_px)
    while text_width(draw, title, title_font) > width - 120 and title_px > 40:
        title_px -= 4
        title_font = load_font("serif_bold", title_px)
    tw = text_width(draw, title, title_font)
    title_y = (height - title_px) // 2 - 60
    draw.text(((width - tw) // 2, title_y), title,
              font=title_font, fill=INK)

    # Red rule
    rule_y = title_y + title_px + 20
    rule_w = 140
    draw.rectangle([
        ((width - rule_w) // 2, rule_y),
        ((width + rule_w) // 2, rule_y + 5),
    ], fill=ACCENT)

    # Subtitle
    sub = "ZIMBABWE  OUTSIDE-IN"
    sub_font = load_font("sans_bold", 30)
    sw = text_width(draw, sub, sub_font)
    draw.text(((width - sw) // 2, rule_y + 30), sub,
              font=sub_font, fill=MUTED)

    # Domain footer
    domain = "mutapatimes.com"
    domain_font = load_font("sans_bold", 26)
    dw = text_width(draw, domain, domain_font)
    draw.text(((width - dw) // 2, height - 70), domain,
              font=domain_font, fill=ACCENT)

    img.save(out_path, "PNG", optimize=True)


# ── 4. Twitter / X banner — 1500x500 ──────────────────────────
def render_twitter_header(out_path, width=1500, height=500):
    """Twitter / X profile header. Wordmark left, accent rule right."""
    img = Image.new("RGB", (width, height), PAPER)
    draw = ImageDraw.Draw(img)

    # Top accent line full width
    draw.rectangle([(0, 0), (width, 6)], fill=ACCENT)

    title = "THE MUTAPA TIMES"
    title_px = 120
    title_font = load_font("serif_bold", title_px)
    while text_width(draw, title, title_font) > width * 0.66 and title_px > 40:
        title_px -= 4
        title_font = load_font("serif_bold", title_px)
    title_y = (height - title_px) // 2 - 30
    draw.text((80, title_y), title, font=title_font, fill=INK)

    # Rule + subtitle below title (left-aligned)
    rule_y = title_y + title_px + 10
    draw.rectangle([(80, rule_y), (80 + 120, rule_y + 5)], fill=ACCENT)

    sub_font = load_font("sans_bold", 26)
    sub = "ZIMBABWE  OUTSIDE-IN  ·  INTELLIGENCE NEWSPAPER"
    draw.text((80, rule_y + 22), sub, font=sub_font, fill=MUTED)

    # Domain on the bottom-right
    domain = "mutapatimes.com"
    domain_font = load_font("sans_bold", 24)
    dw = text_width(draw, domain, domain_font)
    draw.text((width - dw - 80, height - 60), domain,
              font=domain_font, fill=ACCENT)

    img.save(out_path, "PNG", optimize=True)


# ── Main ──────────────────────────────────────────────────────
def main():
    print("=== BUILD BRAND ASSETS ===")
    os.makedirs(OUT_DIR, exist_ok=True)

    targets = [
        ("wordmark-light.png",   lambda p: render_wordmark(p, width=2400, fg=INK)),
        ("wordmark-dark.png",    lambda p: render_wordmark(p, width=2400, fg=PAPER)),
        ("mark-1080.png",        lambda p: render_mark(p, size=1080, bg=PAPER, fg=INK)),
        ("mark-512.png",         lambda p: render_mark(p, size=512, bg=PAPER, fg=INK)),
        ("mark-favicon-256.png", lambda p: render_mark(p, size=256, bg=PAPER, fg=INK)),
        ("mark-dark-1080.png",   lambda p: render_mark(p, size=1080, bg=INK, fg=PAPER)),
        ("og-share.png",         lambda p: render_og_share(p)),
        ("twitter-header.png",   lambda p: render_twitter_header(p)),
    ]
    for fname, fn in targets:
        out = os.path.join(OUT_DIR, fname)
        try:
            fn(out)
            print(f"  Wrote {fname}")
        except Exception as e:
            print(f"  FAIL {fname}: {e}")

    print(f"\n  Output:  {OUT_DIR}")
    print("\n=== DONE ===")


if __name__ == "__main__":
    main()
