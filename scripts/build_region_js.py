#!/usr/bin/env python3
"""Generate js/region.js from scripts/regions.py — the single source of truth.

js/region.js runs in the browser (before config.js) and tells each edition which
URL base, content/data dir, RSS feeds and local sources to use. It used to be
hand-maintained in parallel with regions.py, and that Python<->JS split caused
production bugs (wrong feeds, poisoned cache). This generator derives it from the
registry so adding a region is a regions.py-only change.

ZW safety: the default region (zw) NEVER gets feed/local overrides emitted here —
the root keeps config.js's own literals as its source of truth. Only
REGION_CONTENT / REGION_DATA carry a zw entry (the dir names), exactly as before.

The non-data JS body (detect/mtUrl/wiring) is a fixed template; only five data
blocks are rendered. Run it and `git diff js/region.js` — the output is designed
to be byte-identical to the committed file for the current registry.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from regions import REGIONS, DEFAULT_REGION, region_path_prefix  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "js", "region.js")

TEMPLATE = '''/* region.js — runtime edition base-path for multi-country support.
 *
 * The Mutapa Times serves one edition per country. Zimbabwe is the default
 * edition at the site root; other countries live under /<cc>/ (e.g. /za/).
 *
 * This must load BEFORE any script that fetches data or builds links
 * (config.js, articles.js, markets.js, ...). It defines:
 *   window.MT_REGION  -> "zw" | "za" | ...     (current edition code)
 *   window.MT_BASE    -> ""    | "/za" | ...    (URL prefix for this edition)
 *   window.mtUrl(p)   -> prefixes an absolute "/..." path with MT_BASE
 *
 * CRITICAL: at the root edition MT_BASE is "" so mtUrl() is the identity
 * function. Routing existing absolute paths through mtUrl() therefore cannot
 * change Zimbabwe behaviour; it only takes effect under a /<cc>/ edition.
 *
 * GENERATED from scripts/regions.py by scripts/build_region_js.py — do not edit
 * by hand; change regions.py and re-run the generator.
 */
(function () {
  if (window.mtUrl) return; // idempotent

  // Non-root editions. Add a country's path + content folder here when it
  // launches. content_dir is the repo path the CMS originals live in (read
  // via the GitHub API), so it is region-scoped too.
  var REGION_PATHS = @@PATHS@@;
  var REGION_CONTENT = @@CONTENT@@;
  // Static data lives at a region SUFFIX (data/za), unlike pages which live at
  // a /za PREFIX. So data fetches use MT_DATA_DIR, not mtUrl.
  var REGION_DATA = @@DATA@@;

  // The homepage feed is built client-side from live Google News RSS. Those
  // query sets are Zimbabwe-specific by default; a non-root edition overrides
  // them here (the browser can't read scripts/regions.py). config.js falls back
  // to its own Zimbabwe arrays when these are unset, so the root is unchanged.
@@FEEDS@@

  // Weather-card cities (client-fetched from open-meteo by config.js). Non-root
  // editions override config.js's Zimbabwe default with their own cities.
@@WEATHER@@

  function detect() {
    var path = (location.pathname || "/");
    for (var code in REGION_PATHS) {
      var pre = REGION_PATHS[code];
      if (path === pre || path.indexOf(pre + "/") === 0) {
        return { code: code, base: pre };
      }
    }
    return { code: "zw", base: "" };
  }

  var r = detect();
  window.MT_REGION = r.code;
  window.MT_BASE = r.base;
  window.MT_CONTENT_DIR = REGION_CONTENT[r.code] || "content";
  window.MT_DATA_DIR = REGION_DATA[r.code] || "data";
  if (REGION_FEEDS[r.code]) {
    window.MT_MAIN_RSS_FEEDS = REGION_FEEDS[r.code].main;
    window.MT_SIDEBAR_RSS_FEEDS = REGION_FEEDS[r.code].sidebar;
    window.MT_SPOTLIGHT_RSS_FEEDS = REGION_FEEDS[r.code].spotlight;
  }
  if (REGION_WEATHER[r.code]) window.MT_WEATHER_CITIES = REGION_WEATHER[r.code];
  // Local newsrooms for the "Local" filter (config.js falls back to its
  // Zimbabwe list when unset, so the root is unchanged).
@@LOCAL@@
  if (REGION_LOCAL[r.code]) window.MT_LOCAL_SOURCES = REGION_LOCAL[r.code];

  // Prefix an absolute same-origin path with the edition base. Leaves
  // unchanged: the root edition (base ""), already-prefixed paths, absolute
  // URLs (http...), protocol-relative (//...), and page-relative paths.
  window.mtUrl = function (p) {
    if (!p || !window.MT_BASE) return p;
    if (p.charAt(0) !== "/") return p;          // page-relative, leave as is
    if (p.charAt(1) === "/") return p;          // protocol-relative //host
    if (p.indexOf(window.MT_BASE + "/") === 0 || p === window.MT_BASE) return p;
    return window.MT_BASE + p;
  };
})();
'''


def _inline_obj(pairs):
    """Render {a: "x", b: "y"} on one line (bare identifier keys)."""
    if not pairs:
        return "{}"
    inner = ", ".join(f"{k}: {json.dumps(v)}" for k, v in pairs)
    return "{ " + inner + " }"


def _feed_array(key, urls, indent, last):
    """Render a `key: [ ... ]` block; 8-space URL indent; comma unless last."""
    lines = [f"{indent}{key}: ["]
    for i, u in enumerate(urls):
        comma = "" if i == len(urls) - 1 else ","
        lines.append(f"{indent}  {json.dumps(u)}{comma}")
    lines.append(f"{indent}]" + ("" if last else ","))
    return "\n".join(lines)


def render_feeds(regions):
    """REGION_FEEDS = { za: { main:[...], sidebar:[...], spotlight:[...] } }"""
    feeds_regions = [(c, r) for c, r in regions if r.get("browser_feeds")]
    out = ["  var REGION_FEEDS = {"]
    for ri, (code, r) in enumerate(feeds_regions):
        bf = r["browser_feeds"]
        spotlight = bf.get("spotlight", r.get("spotlight_rss", []))
        last_region = ri == len(feeds_regions) - 1
        out.append(f"    {code}: {{")
        out.append(_feed_array("main", bf.get("main", []), "      ", last=False))
        out.append(_feed_array("sidebar", bf.get("sidebar", []), "      ", last=False))
        out.append(_feed_array("spotlight", spotlight, "      ", last=True))
        out.append("    }" + ("" if last_region else ","))
    out.append("  };")
    return "\n".join(out)


def render_weather(regions):
    """REGION_WEATHER = { za: [{ id, name, lat, lon }, ...] } — non-default only."""
    wx = [(c, r) for c, r in regions
          if c != DEFAULT_REGION and r.get("weather_cities")]
    out = ["  var REGION_WEATHER = {"]
    for ri, (code, r) in enumerate(wx):
        last = ri == len(wx) - 1
        items = []
        for c in r["weather_cities"]:
            cid = c["name"].lower().replace(" ", "").replace("'", "")
            items.append("{ id: %s, name: %s, lat: %s, lon: %s }" % (
                json.dumps(cid), json.dumps(c["name"]), c["lat"], c["lon"]))
        out.append(f"    {code}: [" + ", ".join(items) + "]" + ("" if last else ","))
    out.append("  };")
    return "\n".join(out)


def render_local(regions):
    """REGION_LOCAL = { za: [ ...wrapped 5/line, aligned under first item... ] }"""
    local_regions = [(c, r) for c, r in regions if r.get("browser_local")]
    out = ["  var REGION_LOCAL = {"]
    for ri, (code, r) in enumerate(local_regions):
        items = r["browser_local"]
        cont = " " * len(f"    {code}: [")
        chunks = [items[i:i + 5] for i in range(0, len(items), 5)]
        rendered = [", ".join(json.dumps(x) for x in chunk) for chunk in chunks]
        body = (",\n" + cont).join(rendered)
        last_region = ri == len(local_regions) - 1
        out.append(f"    {code}: [{body}]" + ("" if last_region else ","))
    out.append("  };")
    return "\n".join(out)


def build():
    # Preserve registry order (zw first, then others).
    regions = list(REGIONS.items())
    non_default = [(c, r) for c, r in regions if c != DEFAULT_REGION]

    paths = _inline_obj([(c, region_path_prefix(c)) for c, r in non_default])
    content = _inline_obj([(c, r["content_dir"]) for c, r in regions])
    data = _inline_obj([(c, r["data_dir"]) for c, r in regions])

    out = (TEMPLATE
           .replace("@@PATHS@@", paths)
           .replace("@@CONTENT@@", content)
           .replace("@@DATA@@", data)
           .replace("@@FEEDS@@", render_feeds(regions))
           .replace("@@WEATHER@@", render_weather(regions))
           .replace("@@LOCAL@@", render_local(regions)))

    # Safety assert: the default region must never get feed/local/path overrides.
    assert f"\n  var REGION_FEEDS = {{\n    {DEFAULT_REGION}:" not in out, "zw in REGION_FEEDS!"
    assert f"\n    {DEFAULT_REGION}: [" not in out, "zw in REGION_LOCAL!"
    return out


def main():
    out = build()
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(out)
    print(f"Wrote {OUT} ({len(out)} bytes)")


if __name__ == "__main__":
    main()
