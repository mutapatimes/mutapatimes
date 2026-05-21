#!/usr/bin/env python3
"""Trial: halftone newspaper-style AI imagery for Mutapa Times cards.

Aesthetic rebuild:
  - black-ink halftone on coloured paper (palette rotates per card)
  - sparse-dot disintegration: dots get rarer toward the edge of an irregular
    organic shape so the image fades into the paper as a "rip"
  - per-card noise-driven shape — never the same boundary twice
  - editorial layout: small italic masthead on paper, generous whitespace,
    serif headline at the bottom — no Instagram-template chrome bars

Outputs 1080x1350 PNGs to /img/cards/halftone-trial/. Trial only — not wired
into the site.
"""
import hashlib
import io
import os
import random as pyrand
import sys
import urllib.parse

import requests
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageOps

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from card_lib import (  # noqa: E402
    CARD_FG, CARD_FG_MUTED, ACCENT, load_font, wrap_text,
)

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT_DIR = os.path.join(ROOT, "img", "cards", "halftone-trial")
CARTOON_DIR = os.path.join(ROOT, "img", "cards", "halftone-trial", "cartoon")

# Butter palette colour used by cartoon mode (the original card background).
BUTTER = (245, 232, 200)

CARD_W, CARD_H = 1080, 1350

# Muted paper palette. Each card picks one deterministically from its slug.
PAPER_PALETTE = [
    (245, 232, 200),   # warm butter cream
    (234, 218, 213),   # dusty rose
    (218, 226, 213),   # sage
    (215, 218, 232),   # periwinkle
    (236, 218, 192),   # ochre
    (226, 216, 208),   # warm putty
]
INK = (34, 26, 20)         # dark warm brown — the "ink"
INK_MUTED = (84, 72, 60)   # decks and small text

# ─── editorial trials ─────────────────────────────────────────────
WIRE_TRIALS = [
    {
        "slug": "wire-01-safari-camp",
        "section": "TRAVEL",
        "title": "Exclusive-use safari camp opens on Zimbabwe's Jafuta Reserve near Victoria Falls",
        "deck": "Jafuta Reserve, near Victoria Falls.",
    },
    {
        "slug": "wire-02-winter-chill",
        "section": "WEATHER",
        "title": "Zimbabwe braces for harsh winter chill",
        "deck": "Cold-front warning across the country.",
    },
    {
        "slug": "wire-03-smuggled-vehicles",
        "section": "BUSINESS",
        "title": "Over 70 smuggled vehicles seized in major clampdown",
        "deck": "Customs enforcement at the border.",
    },
    {
        "slug": "wire-04-tunzi",
        "section": "CULTURE",
        "title": "Tunzi's Zim debut sparks excitement",
        "deck": "Zozibini Tunzi visits Zimbabwe for the first time.",
    },
    {
        "slug": "wire-05-diaspora-takeover",
        "section": "BUSINESS",
        "title": "The Great Diaspora Takeover: how Zimbos abroad are quietly buying Zimbabwe",
        "deck": "Remittance-funded property and business acquisition at home.",
    },
    {
        "slug": "wire-06-tourism-alliance",
        "section": "TRAVEL",
        "title": "Namibia joins South Africa and Zimbabwe in bold tourism alliance",
        "deck": "Three southern African countries on a single visitor visa.",
    },
]

TRIALS = [
    {
        "slug": "01-isnt-it-lovely",
        "section": "ARTS",
        "title": "Isn't it lovely.",
        "deck": "A letter from Venice, written in the wake of Zimbabwe's eighth pavilion.",
        "topic": ("a single gondola on a Venetian canal at dusk, rain on the water, "
                  "palazzo facades, atmospheric photograph"),
    },
    {
        "slug": "02-felix-shumba",
        "section": "ARTS",
        "title": "Felix Shumba: charcoal and the practice of disappearance",
        "deck": "On the six-metre charcoal wall and the figures who refuse to settle.",
        "topic": ("heavy charcoal smudges and erased marks on torn newsprint, "
                  "dense black abstract textures, ghostly absence, no figures"),
    },
    {
        "slug": "03-franklyn-dzingai",
        "section": "ARTS",
        "title": "Franklyn Dzingai: family albums and the neural commons",
        "deck": "Collaged photographs and the studio portrait as a transcontinental language.",
        "topic": ("an open mid-century family photo album on a wooden table, "
                  "sepia photographs lying face-down, ornate wallpaper backdrop, "
                  "no faces visible"),
    },
    {
        "slug": "04-gideon-gomo",
        "section": "ARTS",
        "title": "Gideon Gomo: from stone to bronze",
        "deck": "An ancestral algorithm between Harare, Ouagadougou, and Venice.",
        "topic": ("abstract bronze sculptural fragments on a plinth, geometric "
                  "metalwork, foundry tools and copper sheet, no human likeness"),
    },
    {
        "slug": "05-pardon-mapondera",
        "section": "ARTS",
        "title": "Pardon Mapondera: gone but not forgotten",
        "deck": "Glass jars, soil, and a quiet devotional installation.",
        "topic": ("rows of small glass jars on a wooden shelf, each holding "
                  "fragments of paper, soil and string, museum reliquary"),
    },
    {
        "slug": "06-eva-raath",
        "section": "ARTS",
        "title": "Eva Raath: a slow archive of stitched memory",
        "deck": "Quilted memory and the discipline of repair.",
        "topic": ("a hand-stitched patchwork quilt close-up, irregular squares, "
                  "African textile patterns, visible thread and stitching"),
    },
]


# ─── prompts ──────────────────────────────────────────────────────
def halftone_prompt(topic: str) -> str:
    return (
        f"{topic}. "
        "Vintage 1960s newspaper halftone print, coarse Ben Day dot pattern, "
        "monochrome on aged sepia newsprint, high contrast offset print, "
        "gritty print imperfection, archival photograph. "
        "ABSOLUTELY NO faces, NO portraits, NO eyes, NO recognizable human features. "
        "Any human presence is silhouette or distant figure only. "
        "Prefer landscapes, architecture, objects, textures, abstract symbolic imagery. "
        "No text, no captions, no watermarks, no logos."
    )


def topic_from_headline(headline: str) -> str:
    cleaned = headline.strip().rstrip(".!?")
    return (
        f"abstract symbolic illustration evoking the theme of: {cleaned}. "
        "Show the place, objects, atmosphere, or symbolic scene — never people."
    )


def fetch_pollinations(prompt: str, seed: int, w: int = 1024, h: int = 1024) -> Image.Image:
    enc = urllib.parse.quote(prompt, safe="")
    url = (f"https://image.pollinations.ai/prompt/{enc}"
           f"?width={w}&height={h}&model=flux&seed={seed}&nologo=true")
    resp = requests.get(url, timeout=180)
    resp.raise_for_status()
    return Image.open(io.BytesIO(resp.content)).convert("RGB")


# ─── deterministic noise helpers (no numpy in env) ────────────────
def make_random_field(w: int, h: int, seed: int) -> Image.Image:
    """Cheap deterministic random L-mode image, w x h, derived from hashlib."""
    buf = bytearray()
    counter = 0
    target = w * h
    seed_bytes = (seed & 0xFFFFFFFFFFFFFFFF).to_bytes(8, "little")
    while len(buf) < target:
        chunk = hashlib.shake_256(
            seed_bytes + counter.to_bytes(8, "little")
        ).digest(min(65536, target - len(buf)))
        buf.extend(chunk)
        counter += 1
    return Image.frombytes("L", (w, h), bytes(buf[:target]))


def generate_organic_mask(w: int, h: int, seed: int) -> Image.Image:
    """Soft irregular shape — the 'paper' inside which the halftone lives.
    Returns an L image: 0 = no ink, 255 = full ink density. Boundary is soft
    and never the same shape twice (varies with seed)."""
    rng = pyrand.Random(seed)

    # Base ellipse, slightly off-centred and with non-round aspect
    cx = w // 2 + rng.randint(-w // 16, w // 16)
    cy = h // 2 + rng.randint(-h // 16, h // 16)
    aspect_x = 0.39 + rng.uniform(-0.04, 0.05)
    aspect_y = 0.40 + rng.uniform(-0.04, 0.05)
    rx = int(min(w, h) * aspect_x)
    ry = int(min(w, h) * aspect_y)
    base = Image.new("L", (w, h), 0)
    ImageDraw.Draw(base).ellipse(
        [cx - rx, cy - ry, cx + rx, cy + ry], fill=255
    )
    base = base.filter(ImageFilter.GaussianBlur(radius=int(min(w, h) * 0.07)))

    # Low-freq noise to make the boundary irregular ("torn")
    noise_lo = make_random_field(max(8, w // 30), max(8, h // 30), seed + 7)
    noise = noise_lo.resize((w, h), Image.LANCZOS)
    noise = noise.filter(ImageFilter.GaussianBlur(radius=14))

    # Multiply base by noise, then re-boost so the interior reaches saturation
    out = ImageChops.multiply(base, noise)
    out = out.point(lambda p: min(255, int(p * 2.4)))

    # Second noise pass to add small ragged protrusions
    rag_lo = make_random_field(max(4, w // 90), max(4, h // 90), seed + 11)
    rag = rag_lo.resize((w, h), Image.LANCZOS)
    rag = rag.filter(ImageFilter.GaussianBlur(radius=24))
    # Bias rag so it darkens edges asymmetrically
    rag = rag.point(lambda p: max(0, p - 90))
    out = ImageChops.subtract(out, rag.point(lambda p: p // 3))

    # Light final softening
    out = out.filter(ImageFilter.GaussianBlur(radius=2))
    return out


# ─── halftone composite ───────────────────────────────────────────
def render_halftone(raw: Image.Image, paper: tuple, seed: int) -> Image.Image:
    """Black-ink halftone over coloured paper, dots fading sparser at the
    edge of an organic shape. Output is the same size as `raw`."""
    raw = raw.filter(ImageFilter.GaussianBlur(radius=0.5))
    w, h = raw.size

    # 1-bit Floyd-Steinberg dither at a slightly coarser resolution, then
    # nearest-neighbour back up gives clearly visible dots.
    g = ImageOps.grayscale(raw)
    g = ImageOps.autocontrast(g, cutoff=4)
    scale = 0.55
    sw, sh = max(1, int(w * scale)), max(1, int(h * scale))
    small = g.resize((sw, sh), Image.LANCZOS)
    dithered = small.convert("1", dither=Image.Dither.FLOYDSTEINBERG)
    big_dot = dithered.convert("L").resize((w, h), Image.NEAREST)
    # big_dot: 255 where the dither says "paper", 0 where "ink"
    # Invert so 255 = ink present, 0 = paper.
    ink_mask = ImageOps.invert(big_dot)

    # Sparse-dot fade: AND the ink mask with (random_field < organic_mask).
    organic = generate_organic_mask(w, h, seed)
    random_field = make_random_field(w, h, seed + 23)
    # Where organic > random_field, the pixel "survives" — pillow:
    survives = ImageChops.subtract(organic, random_field)  # 0 where random >= organic
    survives = survives.point(lambda p: 255 if p > 0 else 0)

    keep = ImageChops.multiply(ink_mask, survives)
    keep = keep.point(lambda p: 255 if p > 80 else 0)

    # Composite: ink colour through `keep`, paper everywhere else.
    paper_layer = Image.new("RGB", (w, h), paper)
    ink_layer = Image.new("RGB", (w, h), INK)
    return Image.composite(ink_layer, paper_layer, keep)


# ─── card composition ─────────────────────────────────────────────
def paper_for_slug(slug: str) -> tuple:
    idx = int(hashlib.md5(slug.encode()).hexdigest()[:8], 16) % len(PAPER_PALETTE)
    return PAPER_PALETTE[idx]


def fit_serif(draw, text: str, max_w: int, max_lines: int,
              start: int = 56, floor: int = 30) -> tuple:
    """Auto-fit a serif headline. Returns (font, lines, line_height)."""
    size = start
    while size >= floor:
        font = load_font("serif_bold", size)
        lines = wrap_text(text, font, max_w, draw)
        if len(lines) <= max_lines:
            return font, lines, int(size * 1.06)
        size -= 3
    font = load_font("serif_bold", floor)
    lines = wrap_text(text, font, max_w, draw)
    return font, lines, int(floor * 1.06)


def render_card(trial: dict, out_path: str, paper: tuple = None) -> None:
    seed = int(hashlib.md5(trial["slug"].encode()).hexdigest()[:8], 16) % (1 << 31)
    if paper is None:
        paper = paper_for_slug(trial["slug"])
    print(f"  rendering: {trial['slug']:<28s}  paper={paper}")

    topic = trial.get("topic") or topic_from_headline(trial["title"])
    prompt = halftone_prompt(topic)
    raw = fetch_pollinations(prompt, seed)

    # Halftone the AI output at full art-zone resolution so dots look crisp
    art_w, art_h = CARD_W, 900
    raw_resized = raw.resize((art_w, art_h))
    art = render_halftone(raw_resized, paper, seed)

    # Card canvas in the paper colour
    card = Image.new("RGB", (CARD_W, CARD_H), paper)
    # Subtle paper grain — very low-amplitude noise overlay so the paper
    # doesn't read as a flat fill.
    grain = make_random_field(CARD_W, CARD_H, seed + 99)
    grain = grain.point(lambda p: 128 + (p - 128) // 12)  # tiny amplitude
    grain_rgb = ImageOps.colorize(grain, black=(0, 0, 0), white=(255, 255, 255))
    card = Image.blend(card, grain_rgb, alpha=0.08)

    # Paste the halftone artwork — no rectangle visible because the organic
    # mask in render_halftone is already paper at the edges.
    art_y = 150
    card.paste(art, (0, art_y))

    draw = ImageDraw.Draw(card)

    # Masthead — small italic wordmark on paper, no band
    mast_font = load_font("serif_italic", 32)
    draw.text((60, 56), "The Mutapa Times", font=mast_font, fill=INK)
    # Hairline rule under wordmark
    mbb = draw.textbbox((60, 56), "The Mutapa Times", font=mast_font)
    draw.rectangle([60, mbb[3] + 6, 60 + 56, mbb[3] + 9], fill=ACCENT)

    # Section tag — top right, small caps, accent red
    sect_font = load_font("sans_bold", 20)
    sec = trial["section"]
    sbb = draw.textbbox((0, 0), sec, font=sect_font)
    sx = CARD_W - 60 - (sbb[2] - sbb[0])
    draw.text((sx, 68), sec, font=sect_font, fill=ACCENT)

    # Headline — serif bold, auto-fit, sits below the art zone
    head_top = art_y + art_h + 30   # right below the art
    head_font, head_lines, head_lh = fit_serif(
        draw, trial["title"], CARD_W - 120, max_lines=3, start=54, floor=32,
    )
    cy = head_top
    for line in head_lines:
        draw.text((60, cy), line, font=head_font, fill=INK)
        cy += head_lh

    # Deck — italic serif, muted ink
    deck_font = load_font("serif_italic", 22)
    deck_lines = wrap_text(trial["deck"], deck_font, CARD_W - 120, draw)
    cy += 8
    for line in deck_lines:
        draw.text((60, cy), line, font=deck_font, fill=INK_MUTED)
        cy += int(22 * 1.4)

    # Footer — discreet small caps wordmark, bottom-centred
    foot_font = load_font("sans_bold", 18)
    foot_text = "MUTAPATIMES.COM"
    fbb = draw.textbbox((0, 0), foot_text, font=foot_font)
    fx = (CARD_W - (fbb[2] - fbb[0])) // 2
    draw.text((fx, CARD_H - 56), foot_text, font=foot_font, fill=INK_MUTED)

    card.save(out_path, "PNG")


# ─── cartoon mode ─────────────────────────────────────────────────
# Editorial-cartoon style on butter background. Different aesthetic from
# the halftone-photograph mode above: black-ink line drawings, single
# panel framed like a newspaper comic strip.

def cartoon_prompt(topic: str) -> str:
    return (
        f"a minimal single-panel newspaper editorial cartoon depicting: {topic}. "
        "Very simple bold black ink outlines on white background, "
        "almost no shading, no crosshatching, no fine detail, "
        "maximum three or four large elements per scene, generous white space. "
        "The visual language of Saul Steinberg, Tomi Ungerer, or Quentin Blake — "
        "spare, witty, instantly readable. "
        "Generic archetypal cartoon characters only — never specific named public figures. "
        "No text inside the image, no captions, no speech bubbles, no signature, no panel border."
    )


def cartoon_topic_from_headline(headline: str) -> str:
    cleaned = headline.strip().rstrip(".!?")
    return f"a satirical editorial cartoon evoking the situation: {cleaned}"


def apply_cartoon_post(img: Image.Image) -> Image.Image:
    """Tint a black-on-white cartoon to ink-on-butter (no halftone dither)."""
    img = img.filter(ImageFilter.GaussianBlur(radius=0.3))
    g = ImageOps.grayscale(img)
    g = ImageOps.autocontrast(g, cutoff=2)
    # Deepen mid-blacks slightly so ink lines read crisp on butter
    g = g.point(lambda p: int(p * 0.95) if p > 150 else int(p * 0.7))
    return ImageOps.colorize(g, black=INK, white=BUTTER).convert("RGB")


def render_cartoon_card(trial: dict, out_path: str) -> None:
    seed = int(hashlib.md5(trial["slug"].encode()).hexdigest()[:8], 16) % (1 << 31)
    print(f"  rendering: {trial['slug']:<28s}  (cartoon)")

    topic = trial.get("topic") or cartoon_topic_from_headline(trial["title"])
    prompt = cartoon_prompt(topic)
    raw = fetch_pollinations(prompt, seed)
    art = apply_cartoon_post(raw)

    # Card canvas — butter background, no chrome bars
    card = Image.new("RGB", (CARD_W, CARD_H), BUTTER)

    # Panel: full-width region, clipped to an organic noise-driven shape
    # so the cartoon's boundary varies per card — never the same shape twice.
    panel_w = CARD_W - 60
    panel_h = 860
    panel_x = (CARD_W - panel_w) // 2
    panel_y = 180
    art_resized = art.resize((panel_w, panel_h))

    mask = generate_organic_mask(panel_w, panel_h, seed)
    # Boost the interior so cartoon linework stays opaque inside the shape;
    # the soft Gaussian boundary still fades to butter.
    mask = mask.point(lambda p: min(255, int(p * 1.45)))

    butter_layer = Image.new("RGB", (panel_w, panel_h), BUTTER)
    art_clipped = Image.composite(art_resized, butter_layer, mask)
    card.paste(art_clipped, (panel_x, panel_y))

    draw = ImageDraw.Draw(card)

    # Masthead — small italic top-left with hairline rule
    mast_font = load_font("serif_italic", 30)
    draw.text((60, 60), "The Mutapa Times", font=mast_font, fill=INK)
    mbb = draw.textbbox((60, 60), "The Mutapa Times", font=mast_font)
    draw.rectangle([60, mbb[3] + 6, 60 + 56, mbb[3] + 9], fill=ACCENT)

    # Section tag — top right, small caps red
    sect_font = load_font("sans_bold", 20)
    sec = trial["section"]
    sbb = draw.textbbox((0, 0), sec, font=sect_font)
    sx = CARD_W - 60 - (sbb[2] - sbb[0])
    draw.text((sx, 72), sec, font=sect_font, fill=ACCENT)

    # Headline — serif bold, sits below the panel like a comic caption
    head_top = panel_y + panel_h + 40
    head_font, head_lines, head_lh = fit_serif(
        draw, trial["title"], CARD_W - 120, max_lines=3, start=42, floor=28,
    )
    cy = head_top
    for line in head_lines:
        draw.text((60, cy), line, font=head_font, fill=INK)
        cy += head_lh

    # Deck — italic serif, muted ink
    deck_font = load_font("serif_italic", 22)
    deck_lines = wrap_text(trial["deck"], deck_font, CARD_W - 120, draw)
    cy += 6
    for line in deck_lines:
        draw.text((60, cy), line, font=deck_font, fill=INK_MUTED)
        cy += int(22 * 1.4)

    # Footer
    foot_font = load_font("sans_bold", 18)
    foot_text = "MUTAPATIMES.COM"
    fbb = draw.textbbox((0, 0), foot_text, font=foot_font)
    fx = (CARD_W - (fbb[2] - fbb[0])) // 2
    draw.text((fx, CARD_H - 56), foot_text, font=foot_font, fill=INK_MUTED)

    card.save(out_path, "PNG")


# ─── runner ────────────────────────────────────────────────────────
def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(CARTOON_DIR, exist_ok=True)
    only = sys.argv[1] if len(sys.argv) > 1 else "all"

    # Cartoon mode: editorial-cartoon style, wire trials only.
    # Usage: python build_halftone_trial.py wire-cartoon
    if only == "wire-cartoon":
        print(f"=== Cartoon trial (wire) -> {CARTOON_DIR} ===")
        for trial in WIRE_TRIALS:
            out = os.path.join(CARTOON_DIR, f"{trial['slug']}.png")
            try:
                render_cartoon_card(trial, out)
                kb = os.path.getsize(out) // 1024
                print(f"  {trial['slug']:<28s}  {kb:>5} KB")
            except Exception as e:
                print(f"  {trial['slug']:<28s}  FAILED: {e}")
        print("=== DONE ===")
        return

    # Single-card cartoon preview (uses WIRE_TRIALS[0])
    if only == "cartoon-preview":
        render_cartoon_card(
            WIRE_TRIALS[0],
            os.path.join(CARTOON_DIR, f"{WIRE_TRIALS[0]['slug']}.png"),
        )
        print("=== preview done ===")
        return

    if only in ("01", "preview"):
        # Single-card halftone preview for fast iteration
        render_card(TRIALS[0], os.path.join(OUT_DIR, f"{TRIALS[0]['slug']}.png"))
        print("=== preview done ===")
        return

    batches = []
    if only in ("all", "editorial"):
        batches.append(("editorial", TRIALS))
    if only in ("all", "wire"):
        batches.append(("wire", WIRE_TRIALS))

    print(f"=== Halftone trial -> {OUT_DIR} ===")
    for label, batch in batches:
        print(f"--- {label} ---")
        for trial in batch:
            out = os.path.join(OUT_DIR, f"{trial['slug']}.png")
            try:
                render_card(trial, out)
                kb = os.path.getsize(out) // 1024
                print(f"  {trial['slug']:<28s}  {kb:>5} KB")
            except Exception as e:
                print(f"  {trial['slug']:<28s}  FAILED: {e}")
    print("=== DONE ===")


if __name__ == "__main__":
    main()
