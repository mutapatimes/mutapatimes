#!/usr/bin/env python3
"""Generate the per-region shell pages — homepage, articles listing, article
viewer — from templates/region/*.html, filled from regions.py.

NON-DEFAULT regions only: Zimbabwe is the root edition and keeps its rich,
hand-maintained index.html / articles.html / article.html. This generator
refuses to run for the default region, so the root shells are never overwritten.

Adding a region therefore needs no hand-authored HTML — its index/articles/
article pages come from these shared templates + its regions.py entry. Titles,
descriptions and keywords derive from the region's name/demonym/cities.
"""
import argparse
import html as html_mod
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from regions import (  # noqa: E402
    get_region, region_path_prefix, region_newsletter_form, DEFAULT_REGION,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TPL_DIR = os.path.join(ROOT, "templates", "region")
SHELLS = ["index.html", "articles.html", "article.html"]


def esc(s):
    return html_mod.escape(s or "", quote=True)


def _city_fragments(cities, pfx):
    dropdown = "".join(
        f'<li><a href="{pfx}/{c["slug"]}-news">{esc(c["name"])}</a></li>' for c in cities)
    drawer = "\n" + "\n".join(
        f'      <a href="{pfx}/{c["slug"]}-news">{esc(c["name"])}</a>' for c in cities) + "\n    "
    footer = "\n" + "\n".join(
        f'            <li><a href="{pfx}/{c["slug"]}-news">{esc(c["name"])}</a></li>'
        for c in cities) + "\n          "
    return dropdown, drawer, footer


def build(region):
    if (region or "").lower() == DEFAULT_REGION:
        raise SystemExit(
            f"build_region_shells: refusing to generate root shells for the "
            f"default region '{DEFAULT_REGION}' (its pages are hand-maintained).")
    r = get_region(region)
    pfx = region_path_prefix(region)
    cities = r["cities"]
    name = r["name"]
    keywords = r.get("home_keywords") or (
        "The Mutapa Times, " + name + ", news, "
        + ", ".join(c["name"] for c in cities)
        + ", business, health, sport")
    dropdown, drawer, footer = _city_fragments(cities, pfx)

    # City fragments first (they already contain pfx, no nested tokens), then
    # the scalar tokens; DEMONYM_PL before DEMONYM before NAME doesn't matter
    # here because we only replace the {{TOKENS}}, never literal text.
    city_subs = [
        ("{{CITIES_DROPDOWN}}", dropdown),
        ("{{CITIES_DRAWER}}", drawer),
        ("{{CITIES_FOOTER}}", footer),
    ]
    scalar_subs = [
        ("{{DEMONYM_PL}}", r.get("demonym_plural", r["demonym"] + "s")),
        ("{{DEMONYM}}", r["demonym"]),
        ("{{NAME}}", name),
        ("{{HREFLANG}}", r["hreflang"]),
        ("{{KEYWORDS}}", keywords),
        ("{{NEWSLETTER_FORM}}", region_newsletter_form(region)),
        ("{{PFX}}", pfx),
    ]
    out_dir = os.path.join(ROOT, region)
    os.makedirs(out_dir, exist_ok=True)
    for shell in SHELLS:
        s = open(os.path.join(TPL_DIR, shell), encoding="utf-8").read()
        for k, v in city_subs + scalar_subs:
            s = s.replace(k, v)
        assert "{{" not in s, f"unfilled placeholder in {shell}: {s[s.index('{{'):s.index('{{')+30]}"
        with open(os.path.join(out_dir, shell), "w", encoding="utf-8") as f:
            f.write(s)
    print(f"Wrote {region}/index.html, {region}/articles.html, {region}/article.html")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", required=True, help="non-default region code, e.g. za")
    build(ap.parse_args().region)


if __name__ == "__main__":
    main()
