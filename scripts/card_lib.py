"""Shared card-rendering primitives used by build_metricool_csv.py,
build_feed_cards.py, and any future card pipeline.

Single source of truth for brand colour palette, font discovery,
text wrapping, and the canonical 1080x1350 portrait headline card.
"""
import os

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:  # pragma: no cover
    raise SystemExit("ERROR: Pillow not installed. Run: pip install Pillow")


# ── Card dimensions + palette ─────────────────────────────
CARD_W = 1080
CARD_H = 1350           # portrait 4:5 — Instagram-optimal
CARD_FG = (26, 26, 26)
CARD_FG_MUTED = (95, 92, 84)
ACCENT = (192, 57, 43)  # brand red

# Brand background — every card (feeds + CSVs + economy + jobs + property)
# renders on butter #F5E8C8. Kept as a single-element list so existing
# call-sites that do `CARD_BACKGROUNDS[idx % len(...)]` still resolve.
BUTTER = (245, 232, 200)
CARD_BACKGROUNDS = [BUTTER]


def card_bg(index):
    return CARD_BACKGROUNDS[index % len(CARD_BACKGROUNDS)]


# ── Font discovery ────────────────────────────────────────
# Checks bundled fonts/ first, then OS-specific locations. Each role
# lists candidates from highest to lowest preference.
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
    "serif_italic": [
        "fonts/PlayfairDisplay-Italic.ttf",
        "/System/Library/Fonts/Supplemental/Georgia Italic.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf",
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
    """Pick the first available font for the given role, with sane fallback."""
    for path in FONT_ROLES.get(role, []):
        if os.path.isfile(path):
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default()


def wrap_text(text, font, max_width, draw):
    """Greedy word-wrap text into lines that fit max_width pixels."""
    words = (text or "").split()
    lines, line = [], []
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


# ── The canonical headline card ───────────────────────────
def render_headline_card(headline, source, output_path, color_idx=0):
    """1080x1350 portrait headline card with rotating brand bg + branded chrome.

    This is the SAME card design used in the Metricool CSV pipeline — by
    sharing the renderer here we guarantee every social image (autolist,
    CSV batch, OG previews) stays visually consistent.
    """
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
    draw.text((60, 124), "Zimbabwe outside-in",
              font=source_font, fill=CARD_FG_MUTED)

    # Headline (wrapped, vertically centered in the middle band)
    available_width = CARD_W - 120
    lines = wrap_text(headline, headline_font, available_width, draw)
    if len(lines) > 7:
        lines = lines[:6] + [lines[6] + "…"]

    line_height = 96
    block_h = len(lines) * line_height
    available_h = CARD_H - 360
    y = 230 + (available_h - block_h) // 2
    for ln in lines:
        draw.text((60, y), ln, font=headline_font, fill=CARD_FG)
        y += line_height

    # Footer source attribution + read-more cue
    footer_y = CARD_H - 140
    draw.text((60, footer_y), "VIA", font=label_font, fill=CARD_FG_MUTED)
    if source:
        draw.text((60, footer_y + 32), source.upper(),
                  font=source_font, fill=CARD_FG)
    cue = "READ MORE → mutapatimes.com"
    bbox = draw.textbbox((0, 0), cue, font=source_font)
    cue_w = bbox[2] - bbox[0]
    draw.text((CARD_W - 60 - cue_w, footer_y + 32), cue,
              font=source_font, fill=ACCENT)

    img.save(output_path, "PNG", optimize=True)


# Backward-compat alias so callers using the old name still work.
render_card = render_headline_card
