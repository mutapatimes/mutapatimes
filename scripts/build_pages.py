#!/usr/bin/env python3
"""Inject CMS-edited static page copy from content/pages/{name}.md into
the corresponding top-level HTML files.

How it works:
  • Each markdown file in content/pages/ is a single page's CMS record
    (frontmatter only — body is informational).
  • The matching HTML file (about.html, advertising.html, ...) has
    HTML comment markers:
        <!-- CMS:HERO -->
        ...page hero markup...
        <!-- /CMS:HERO -->
    Anything between those markers is replaced on each build with a
    freshly-rendered hero block driven by the markdown frontmatter
    (eyebrow / headline / deck).
  • Pages without markers are skipped silently. This lets us migrate
    one page at a time without breaking anything.

This is intentionally minimal. The full-body migration for terms /
privacy / etc. can be layered on later with additional marker pairs
(e.g. <!-- CMS:BODY -->).
"""
import glob
import html as html_mod
import os
import re

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
PAGES_DIR = os.path.join(ROOT, "content", "pages")

# (markdown stem) → (target HTML, CSS class prefix used by the hero block)
PAGE_MAP = {
    "about":       ("about.html",       "about"),
    "advertising": ("advertising.html", "ad"),
    "subscribe":   ("subscribe.html",   "sub"),
    "privacy":     ("privacy.html",     None),  # no hero pattern on this page
    "terms":       ("terms.html",       None),
}


def _grab(fm, key, default=""):
    mm = re.search(rf'^{key}:\s*["\']?(.*?)["\']?\s*$', fm, re.MULTILINE)
    return mm.group(1).strip() if mm else default


def _esc(s):
    return html_mod.escape(s, quote=False)


def render_hero(prefix, fm):
    """Build the hero block. Adapts to each page's existing CSS:
       about.html uses .about-hero / .about-eyebrow / .about-headline,
       advertising.html uses .advertising-hero / ...,
       subscribe.html uses .sub-hero / .sub-eyebrow / .sub-headline.
       Deck is rendered only if present."""
    eyebrow = _grab(fm, "eyebrow")
    headline = _grab(fm, "headline")
    deck = _grab(fm, "deck")
    out = [f'<header class="{prefix}-hero">']
    if eyebrow:
        out.append(f'  <p class="{prefix}-eyebrow">{_esc(eyebrow)}</p>')
    if headline:
        out.append(f'  <h1 class="{prefix}-headline">{_esc(headline)}</h1>')
    if deck:
        out.append(f'  <p class="{prefix}-deck">{_esc(deck)}</p>')
    out.append("</header>")
    return "\n".join(out)


def inject(html_path, block):
    if not os.path.exists(html_path):
        return False
    with open(html_path, "r", encoding="utf-8") as f:
        s = f.read()
    pattern = re.compile(r"<!--\s*CMS:HERO\s*-->.*?<!--\s*/CMS:HERO\s*-->",
                         flags=re.DOTALL)
    if not pattern.search(s):
        return False  # no marker yet — page not migrated, skip silently
    new = pattern.sub("<!-- CMS:HERO -->\n" + block + "\n<!-- /CMS:HERO -->", s)
    if new == s:
        return False
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(new)
    return True


def main():
    print("=== BUILD STATIC PAGES (CMS hero injection) ===")
    n_injected = 0
    for md_path in sorted(glob.glob(os.path.join(PAGES_DIR, "*.md"))):
        stem = os.path.splitext(os.path.basename(md_path))[0]
        target = PAGE_MAP.get(stem)
        if not target or not target[1]:
            continue
        html_target, prefix = target
        with open(md_path, "r", encoding="utf-8") as f:
            text = f.read()
        m = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
        if not m:
            continue
        fm = m.group(1)
        block = render_hero(prefix, fm)
        if inject(os.path.join(ROOT, html_target), block):
            print(f"  Injected hero -> {html_target}")
            n_injected += 1
        else:
            print(f"  Skipped {html_target} (no <!-- CMS:HERO --> markers yet)")
    print(f"=== DONE — {n_injected} page(s) updated ===")


if __name__ == "__main__":
    main()
