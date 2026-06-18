/* region.js — runtime edition base-path for multi-country support.
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
 */
(function () {
  if (window.mtUrl) return; // idempotent

  // Non-root editions. Add a country's path + content folder here when it
  // launches. content_dir is the repo path the CMS originals live in (read
  // via the GitHub API), so it is region-scoped too.
  var REGION_PATHS = { za: "/za" };
  var REGION_CONTENT = { zw: "content", za: "content/za" };

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
