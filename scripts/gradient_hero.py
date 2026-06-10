#!/usr/bin/env python3
"""
Generate a stunning, deterministic gradient hero for longform articles that
have no photograph. Seeded by the article slug, so the same article always
gets the same artwork (no churn on rebuild), but every article gets its own.

The look: a deep base wash with several soft, overlapping colour blooms
(aurora / mesh style), a directional light, fine film grain, a vignette and a
bottom scrim so the white headline the longform hero overlays stays legible.
Pure Pillow, no numpy.

CLI:  python3 scripts/gradient_hero.py <slug> <out.jpg> [width height]
Lib:  from gradient_hero import make_gradient_hero
"""
import hashlib
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageEnhance


def _lighten(c, t):
    return tuple(int(v + (255 - v) * t) for v in c)

# Curated, harmonious palettes (base first, then 3-4 bloom colours). Picked by
# seed. Rich and saturated so the result reads as art, not a flat fill.
PALETTES = [
    # ember (on-brand red/amber)
    ((28, 14, 16), [(196, 30, 30), (232, 116, 58), (120, 18, 40), (250, 196, 120)]),
    # aurora (teal / violet / pink)
    ((10, 18, 30), [(34, 197, 174), (124, 92, 220), (236, 110, 168), (40, 120, 200)]),
    # dusk (magenta / indigo / orange)
    ((18, 12, 32), [(214, 64, 132), (96, 64, 200), (240, 138, 72), (60, 40, 120)]),
    # deep ocean (blue / cyan / indigo)
    ((8, 16, 34), [(38, 110, 200), (44, 196, 210), (70, 60, 168), (24, 70, 140)]),
    # forest gold (green / teal / amber)
    ((10, 22, 20), [(38, 150, 110), (28, 110, 120), (224, 178, 84), (18, 80, 70)]),
    # nebula (violet / blue / rose)
    ((14, 12, 28), [(126, 88, 224), (52, 96, 214), (228, 96, 150), (36, 40, 96)]),
    # sunset clay (terracotta / rose / gold)
    ((26, 14, 18), [(214, 92, 64), (196, 60, 96), (236, 176, 96), (120, 36, 52)]),
    # ink & jade (slate / jade / cyan)
    ((10, 16, 22), [(36, 166, 140), (40, 84, 130), (96, 200, 188), (22, 52, 78)]),
]


def _seed(slug):
    return int(hashlib.md5(slug.encode("utf-8")).hexdigest(), 16)


class _Rng:
    """Tiny deterministic PRNG (LCG) so we never touch global random state."""

    def __init__(self, seed):
        self.s = seed & 0xFFFFFFFFFFFFFFFF

    def next(self):
        self.s = (self.s * 6364136223846793005 + 1442695040888963407) & 0xFFFFFFFFFFFFFFFF
        return self.s

    def rand(self):
        return self.next() / 0xFFFFFFFFFFFFFFFF

    def uniform(self, a, b):
        return a + (b - a) * self.rand()

    def choice(self, seq):
        return seq[self.next() % len(seq)]


def _radial(size, cx, cy, radius):
    """A soft white radial blob mask (L) centred at cx,cy."""
    w, h = size
    m = Image.new("L", size, 0)
    d = ImageDraw.Draw(m)
    bbox = [cx - radius, cy - radius, cx + radius, cy + radius]
    d.ellipse(bbox, fill=255)
    m = m.filter(ImageFilter.GaussianBlur(radius * 0.55))
    return m


def make_gradient_hero(slug, out_path, width=1600, height=900):
    rng = _Rng(_seed(slug))
    W, H = width, height
    base, blooms = rng.choice(PALETTES)

    # Work at half-res for speed, upscale at the end (keeps blends buttery).
    w, h = W // 2, H // 2
    img = Image.new("RGB", (w, h), base)

    # Main colour blooms, NORMAL-blended over the dark base so the palette
    # stays saturated and the composition keeps depth and contrast.
    n = 5 + (rng.next() % 2)
    for i in range(n):
        color = rng.choice(blooms)
        cx = int(rng.uniform(-0.15, 1.15) * w)
        cy = int(rng.uniform(-0.15, 1.15) * h)
        radius = int(rng.uniform(0.40, 0.95) * w)
        alpha = rng.uniform(0.65, 0.95)
        mask = _radial((w, h), cx, cy, radius).point(lambda p: int(p * alpha))
        layer = Image.new("RGB", (w, h), color)
        img = Image.composite(layer, img, mask)

    # Two bright glow accents, screen-blended for luminous focal points.
    for i in range(2):
        glow = _lighten(rng.choice(blooms), 0.45)
        cx = int(rng.uniform(0.1, 0.9) * w)
        cy = int(rng.uniform(0.05, 0.6) * h)
        radius = int(rng.uniform(0.18, 0.38) * w)
        mask = _radial((w, h), cx, cy, radius).point(lambda p: int(p * 0.7))
        layer = Image.new("RGB", (w, h), glow)
        img = Image.composite(ImageChops.screen(img, layer), img, mask)

    # Smooth everything into one continuous field, then enrich.
    img = img.filter(ImageFilter.GaussianBlur(w * 0.035))
    img = img.resize((W, H), Image.LANCZOS)
    img = ImageEnhance.Color(img).enhance(1.22)
    img = ImageEnhance.Contrast(img).enhance(1.08)

    # Fine film grain.
    grain = Image.effect_noise((W, H), 16).convert("L")
    img = Image.composite(
        ImageChops.add(img, Image.merge("RGB", (grain, grain, grain))),
        img,
        grain.point(lambda p: 36),
    )

    # Vignette + stronger bottom scrim for headline legibility.
    vig = Image.new("L", (W, H), 0)
    vd = ImageDraw.Draw(vig)
    vd.ellipse([-W * 0.25, -H * 0.35, W * 1.25, H * 1.25], fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(W * 0.12)).point(lambda p: 255 - p)
    img = Image.composite(Image.new("RGB", (W, H), (0, 0, 0)), img, vig.point(lambda p: int(p * 0.55)))

    scrim = Image.new("L", (W, H), 0)
    sd = ImageDraw.Draw(scrim)
    for y in range(H):
        t = max(0.0, (y - H * 0.45) / (H * 0.55))
        sd.line([(0, y), (W, y)], fill=int(150 * (t ** 1.6)))
    img = Image.composite(Image.new("RGB", (W, H), (0, 0, 0)), img, scrim)

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    img.save(out_path, "JPEG", quality=88, optimize=True, progressive=True)
    return out_path


if __name__ == "__main__":
    if len(sys.argv) < 3:
        raise SystemExit("usage: gradient_hero.py <slug> <out.jpg> [width height]")
    slug, out = sys.argv[1], sys.argv[2]
    dims = (int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) >= 5 else (1600, 900)
    p = make_gradient_hero(slug, out, *dims)
    print("wrote", p)
