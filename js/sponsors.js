/*
 * Editorial sponsor strip — reads /data/sponsors.json (CMS-edited via
 * content/sponsors/*.md → scripts/build_sponsors.py) and renders a
 * single hairline strip near the top of the matching page.
 *
 * Strip-only by editorial policy: never a rectangular banner. Reads
 * `data-sponsor-page` from <body> to know which page we're on; falls
 * back to the URL pathname for the page keys ("news", "articles", ...).
 * If no active sponsor targets this page, the script renders nothing
 * — completely silent.
 */
(function () {
  'use strict';

  function detectPage() {
    var bodyKey = document.body.getAttribute('data-sponsor-page');
    if (bodyKey) return bodyKey;
    var path = (location.pathname || '/').replace(/\/$/, '');
    if (path === '' || path === '/index.html') return 'news';
    var seg = path.split('/').filter(Boolean)[0] || 'news';
    return seg.replace(/-news$/, '-cities').replace(/\.html$/, '');
  }

  function buildStrip(s) {
    var strip = document.createElement('aside');
    strip.className = 'sponsor-strip';
    strip.setAttribute('role', 'complementary');
    strip.setAttribute('aria-label', 'Sponsored briefing');

    var inner = document.createElement('div');
    inner.className = 'sponsor-strip-inner';

    var eyebrow = document.createElement('span');
    eyebrow.className = 'sponsor-strip-eyebrow';
    eyebrow.textContent = 'SPONSORED';
    inner.appendChild(eyebrow);

    var a = document.createElement('a');
    a.className = 'sponsor-strip-link';
    a.href = s.url;
    a.target = '_blank';
    a.rel = 'noopener sponsored';
    a.textContent = s.strip_copy;
    inner.appendChild(a);

    strip.appendChild(inner);
    return strip;
  }

  function place(strip) {
    // Slot the strip between the masthead and the main content.
    // First try a dedicated host; otherwise insert before the first
    // <main>/<.paper> or as the first body element.
    var host = document.getElementById('sponsorSlot');
    if (host) { host.appendChild(strip); return; }
    var paper = document.querySelector('.paper');
    var main = document.querySelector('main');
    var anchor = paper || main || document.body.firstElementChild;
    if (anchor && anchor.parentNode) {
      anchor.parentNode.insertBefore(strip, anchor);
    }
  }

  fetch('/data/sponsors.json', { cache: 'no-store' })
    .then(function (r) { return r.ok ? r.json() : null; })
    .then(function (d) {
      if (!d || !Array.isArray(d.sponsors) || !d.sponsors.length) return;
      var page = detectPage();
      var match = d.sponsors.find(function (s) {
        return (s.placements || []).indexOf(page) !== -1;
      });
      if (match) place(buildStrip(match));
    })
    .catch(function () {});
})();
