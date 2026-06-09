#!/usr/bin/env python3
"""
Add an "Originals" link to the site nav, right after the "Articles" link, in
both the desktop #mainNav and the mobile nav-drawer. Idempotent and safe to run
on either generator templates (.py) or static pages (.html): the inserted link
uses a literal class (no f-string cls() call), and Originals is never the
"active" item on generated pages (the only Originals page, originals.html, is
hand-authored with its own active state).
"""
import re
import sys

# Desktop #mainNav: the Articles <p> block (matches both the static form
# `class="active notranslate"` and the f-string form `{cls("articles")}`).
DESKTOP_RE = re.compile(
    r'(<p>\s*<a target="_self"[^>]*?href="/articles">Articles</a>\s*</p>)'
)
DESKTOP_ADD = (
    '\n      <p>\n          '
    '<a target="_self" class="notranslate" href="/originals">Originals</a>'
    '\n      </p>'
)

# Mobile drawer: a standalone `<a href="/articles">Articles</a>` line (NOT the
# <li>-wrapped variants used in footer/cities lists).
DRAWER_RE = re.compile(r'^([ \t]*)<a href="/articles">Articles</a>[ \t]*$', re.M)


def patch(text):
    changed = False
    # Desktop — only if an Originals desktop link is not already present.
    if 'href="/originals">Originals</a>' not in text or \
       'target="_self" class="notranslate" href="/originals"' not in text:
        if not re.search(r'target="_self"[^>]*href="/originals"', text):
            new, n = DESKTOP_RE.subn(lambda m: m.group(1) + DESKTOP_ADD, text, count=1)
            if n:
                text = new
                changed = True
    # Drawer — only if a standalone Originals drawer link is not present.
    if not re.search(r'^[ \t]*<a href="/originals">Originals</a>[ \t]*$', text, re.M):
        new, n = DRAWER_RE.subn(
            lambda m: m.group(0) + '\n' + m.group(1) + '<a href="/originals">Originals</a>',
            text, count=1)
        if n:
            text = new
            changed = True
    return text, changed


def main(paths):
    for p in paths:
        try:
            src = open(p, encoding="utf-8").read()
        except (OSError, UnicodeDecodeError):
            continue
        out, changed = patch(src)
        status = "updated" if changed else "skip   "
        if changed:
            open(p, "w", encoding="utf-8").write(out)
        print(f"  {status}  {p}")


if __name__ == "__main__":
    main(sys.argv[1:])
