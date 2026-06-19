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
  // Static data lives at a region SUFFIX (data/za), unlike pages which live at
  // a /za PREFIX. So data fetches use MT_DATA_DIR, not mtUrl.
  var REGION_DATA = { zw: "data", za: "data/za" };

  // The homepage feed is built client-side from live Google News RSS. Those
  // query sets are Zimbabwe-specific by default; a non-root edition overrides
  // them here (the browser can't read scripts/regions.py). config.js falls back
  // to its own Zimbabwe arrays when these are unset, so the root is unchanged.
  var REGION_FEEDS = {
    za: {
      main: [
        "https://news.google.com/rss/search?q=South+Africa&hl=en&gl=ZA&ceid=ZA:en",
        "https://news.google.com/rss/search?q=South+Africa+news+today&hl=en&gl=ZA&ceid=ZA:en",
        "https://news.google.com/rss/search?q=Johannesburg+OR+Cape+Town+OR+Durban&hl=en&gl=ZA&ceid=ZA:en",
        "https://news.google.com/rss/search?q=South+Africa+politics+government+economy&hl=en&gl=ZA&ceid=ZA:en",
        "https://news.google.com/rss/search?q=South+Africa+health+education+sport&hl=en&gl=ZA&ceid=ZA:en",
        "https://news.google.com/rss/search?q=South+Africa+mining+business+tourism&hl=en&gl=ZA&ceid=ZA:en",
        "https://news.google.com/rss/search?q=site:news24.com+OR+site:timeslive.co.za+OR+site:iol.co.za+OR+site:sowetanlive.co.za+OR+site:citizen.co.za&hl=en&gl=ZA&ceid=ZA:en",
        "https://news.google.com/rss/search?q=site:dailymaverick.co.za+OR+site:businesslive.co.za+OR+site:moneyweb.co.za+OR+site:mg.co.za&hl=en&gl=ZA&ceid=ZA:en"
      ],
      sidebar: [
        "https://news.google.com/rss/search?q=South+Africa+local+news&hl=en&gl=ZA&ceid=ZA:en",
        "https://news.google.com/rss/search?q=South+Africa+business+sports+entertainment+health&hl=en&gl=ZA&ceid=ZA:en",
        "https://news.google.com/rss/search?q=Johannesburg+Cape+Town+Durban+Pretoria+Gqeberha+Bloemfontein&hl=en&gl=ZA&ceid=ZA:en",
        "https://news.google.com/rss/search?q=Gauteng+OR+Western+Cape+OR+KwaZulu-Natal+OR+Limpopo&hl=en&gl=ZA&ceid=ZA:en",
        "https://news.google.com/rss/search?q=South+Africa+culture+music+festival+education&hl=en&gl=ZA&ceid=ZA:en"
      ],
      spotlight: [
        "https://news.google.com/rss/search?q=South+Africa+site:bbc.com+OR+site:reuters.com+OR+site:nytimes.com+OR+site:theguardian.com+OR+site:aljazeera.com+OR+site:bloomberg.com+OR+site:apnews.com+OR+site:cnn.com&hl=en&gl=ZA&ceid=ZA:en",
        "https://news.google.com/rss/search?q=South+Africa+site:news24.com+OR+site:dailymaverick.co.za+OR+site:businesslive.co.za+OR+site:timeslive.co.za+OR+site:mg.co.za+OR+site:moneyweb.co.za+OR+site:ewn.co.za&hl=en&gl=ZA&ceid=ZA:en",
        "https://news.google.com/rss/search?q=South+Africa+site:reuters.com+OR+site:bbc.com+OR+site:theguardian.com+OR+site:aljazeera.com&hl=en&gl=ZA&ceid=ZA:en"
      ]
    }
  };

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
  // Local newsrooms for the "Local" filter (config.js falls back to its
  // Zimbabwe list when unset, so the root is unchanged).
  var REGION_LOCAL = {
    za: ["news24", "daily maverick", "businessday", "business day", "times live",
         "timeslive", "moneyweb", "iol", "sowetan", "the citizen",
         "mail & guardian", "ewn", "eyewitness news", "fin24", "businesstech"]
  };
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
