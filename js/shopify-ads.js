/*
 * Shopify negative-space ads — auto-injects Shopify campaign 13624
 * banners into the editorial gaps across the site. Format- AND
 * viewport-aware: each slot picks a desktop creative on wide screens
 * and a mobile creative on narrow ones, so a 728×90 leaderboard does
 * not collapse to 40px tall on a phone.
 *
 * Independent of /js/sponsors.js (curated luxury sponsor card).
 *
 * Page-type → slot map:
 *   article      → leaderboard before .more-to-read,
 *                  hero before the cross-site rail
 *   hub          → hero pre-footer
 *   list / home  → leaderboard after the 8th / 16th / 24th card,
 *                  hero pre-footer
 *   city         → leaderboard below the weather strip, hero pre-footer
 *
 * Impact campaign 13624. Tracking pixel format:
 *   https://imp.pxf.io/i/7333540/{creative_id}/13624
 * Click URL format:
 *   https://shopify.pxf.io/c/7333540/{creative_id}/13624
 * Image URL format:
 *   https://a.impactradius-go.com/display-ad/13624-{creative_id}
 */
(function () {
  'use strict';

  if (window.__shopifyAdsLoaded) return;
  window.__shopifyAdsLoaded = true;

  var MOBILE_MAX = 600;
  var isMobile = function () {
    return (window.innerWidth || document.documentElement.clientWidth || 0) < MOBILE_MAX;
  };

  // ─── Inventory ─────────────────────────────────────────────────────
  // For each "slot format", we keep desktop + mobile creative pools.
  // At render time the script picks the right pool for the viewport.
  var INVENTORY = {
    leaderboard: {
      // Wide screens: 728×90 stripe.
      desktop: [
        { id: 3797165, w: 728, h: 90, label: 'Starting a store is easier than you think', cta: 'Start free trial →' },
        { id: 3797169, w: 728, h: 90, label: 'Starting a store is easier than you think', cta: 'Start free trial →' },
        { id: 3323854, w: 728, h: 90, label: 'From daydream to dream job', cta: 'Try Shopify for $1 →' },
        { id: 3323861, w: 728, h: 90, label: 'Turn your idea into your business', cta: 'Try Shopify for $1 →' }
      ],
      // Mobile: 320×50 — same proportions but legible at phone width.
      mobile: [
        { id: 3797158, w: 320, h: 50, label: 'Build a store in seconds', cta: 'Start free →' },
        { id: 3797159, w: 300, h: 50, label: 'Build a store in seconds', cta: 'Start free →' },
        { id: 3323852, w: 320, h: 50, label: 'From daydream to dream job', cta: 'Try Shopify for $1 →' },
        { id: 3323859, w: 320, h: 50, label: 'Turn your idea into your business', cta: 'Try Shopify for $1 →' }
      ]
    },
    hero: {
      // Wide screens: 1200×628 / 2400×1256 landscape hero.
      desktop: [
        { id: 3797168, w: 2400, h: 1256, label: 'Starting a store is easier than you think', cta: 'Start free trial →' },
        { id: 3323855, w: 1200, h: 628, label: 'Turn your idea into your business', cta: 'Try Shopify for $1 →' },
        { id: 3323848, w: 1200, h: 628, label: 'From daydream to dream job', cta: 'Try Shopify for $1 →' },
        { id: 3323841, w: 1200, h: 628, label: 'Change your life', cta: 'Try Shopify for $1 →' }
      ],
      // Mobile: 320×480 portrait — fills more of the scroll, stays legible.
      mobile: [
        { id: 3323851, w: 320, h: 480, label: 'From daydream to dream job', cta: 'Try Shopify for $1 →' },
        { id: 3323858, w: 320, h: 480, label: 'Turn your idea into your business', cta: 'Try Shopify for $1 →' }
      ]
    },
    rectangle: {
      // 300×250 reads on both. Keep the same pool for both viewports.
      desktop: [
        { id: 3323850, w: 300, h: 250, label: 'From daydream to dream job', cta: 'Try Shopify for $1 →' },
        { id: 3323857, w: 300, h: 250, label: 'Turn your idea into your business', cta: 'Try Shopify for $1 →' },
        { id: 3323860, w: 336, h: 280, label: 'Turn your idea into your business', cta: 'Try Shopify for $1 →' }
      ],
      mobile: [
        { id: 3323850, w: 300, h: 250, label: 'From daydream to dream job', cta: 'Try Shopify for $1 →' },
        { id: 3323857, w: 300, h: 250, label: 'Turn your idea into your business', cta: 'Try Shopify for $1 →' }
      ]
    }
  };

  function pick(format) {
    var pool = (INVENTORY[format] || {})[isMobile() ? 'mobile' : 'desktop'];
    if (!pool || !pool.length) return null;
    return pool[Math.floor(Math.random() * pool.length)];
  }

  // ─── Build ─────────────────────────────────────────────────────────
  function build(format, ix) {
    var c = pick(format);
    if (!c) return null;

    var card = document.createElement('aside');
    card.className = 'shopify-banner shopify-banner--' + format +
                     (isMobile() ? ' shopify-banner--mobile' : ' shopify-banner--desktop');
    card.setAttribute('role', 'complementary');
    card.setAttribute('aria-label', 'Sponsored: Shopify');
    if (ix != null) card.setAttribute('data-slot-ix', String(ix));

    var eyebrow = document.createElement('p');
    eyebrow.className = 'shopify-banner-eyebrow';
    eyebrow.textContent = 'PRESENTED BY SHOPIFY';
    card.appendChild(eyebrow);

    var a = document.createElement('a');
    a.className = 'shopify-banner-link';
    a.href = 'https://shopify.pxf.io/c/7333540/' + c.id + '/13624';
    a.target = '_blank';
    a.rel = 'noopener sponsored';
    a.setAttribute('aria-label', c.label + ' — ' + c.cta);

    var img = document.createElement('img');
    img.src = 'https://a.impactradius-go.com/display-ad/13624-' + c.id;
    img.alt = '';
    img.loading = 'lazy';
    img.referrerPolicy = 'no-referrer-when-downgrade';
    img.width  = c.w;
    img.height = c.h;
    // Inline width hint so the layout doesn't jump while the asset loads.
    img.style.maxWidth = c.w + 'px';
    img.style.aspectRatio = c.w + ' / ' + c.h;
    a.appendChild(img);
    card.appendChild(a);

    var cap = document.createElement('p');
    cap.className = 'shopify-banner-caption';
    cap.textContent = c.label + ' — ' + c.cta;
    card.appendChild(cap);

    // Impression pixel
    var px = new Image(0, 0);
    px.alt = '';
    px.referrerPolicy = 'no-referrer-when-downgrade';
    px.style.position = 'absolute';
    px.style.visibility = 'hidden';
    px.style.width = '0';
    px.style.height = '0';
    px.src = 'https://imp.pxf.io/i/7333540/' + c.id + '/13624';
    card.appendChild(px);

    return card;
  }

  // ─── Page type detection ───────────────────────────────────────────
  function detect() {
    if (document.querySelector('article.article-full')) return 'article';
    if (document.body.classList.contains('city-page') ||
        document.querySelector('main.city-page')) return 'city';
    if (document.body.classList.contains('fl-page') ||
        document.body.classList.contains('dp-page')) return 'hub';
    var path = (location.pathname || '/').replace(/\/$/, '');
    if (path === '' || path === '/index.html') return 'home';
    if (path === '/articles' || path === '/articles.html') return 'list';
    return 'other';
  }

  // ─── Inject ────────────────────────────────────────────────────────
  function injectBefore(el, node) {
    if (el && el.parentNode && node) el.parentNode.insertBefore(node, el);
  }
  function appendInto(el, node) {
    if (el && node) el.appendChild(node);
  }
  function insertAfter(el, node) {
    if (el && el.parentNode && node) {
      el.parentNode.insertBefore(node, el.nextSibling);
    }
  }

  function inject() {
    var type = detect();
    var slotIx = 0;

    if (type === 'article') {
      var moreToRead = document.querySelector('.more-to-read');
      var share      = document.querySelector('.article-share');
      var rrRail     = document.querySelector('.rr-rail');
      if (moreToRead) injectBefore(moreToRead, build('leaderboard', slotIx++));
      else if (share) insertAfter(share, build('leaderboard', slotIx++));
      if (rrRail) injectBefore(rrRail, build('hero', slotIx++));
      return;
    }

    if (type === 'hub') {
      var main = document.querySelector('main');
      if (main) appendInto(main, build('hero', slotIx++));
      return;
    }

    if (type === 'list' || type === 'home') {
      var cards = document.querySelectorAll(
        '.article-card, .more-card, .news-card, .card, .post-summary'
      );
      var n = cards.length;
      [8, 16, 24].forEach(function (target) {
        if (n > target && cards[target]) {
          insertAfter(cards[target], build('leaderboard', slotIx++));
        }
      });
      var mainEl = document.querySelector('main') || document.querySelector('.lower-section');
      if (mainEl) appendInto(mainEl, build('hero', slotIx++));
      return;
    }

    if (type === 'city') {
      var weather = document.querySelector('.city-weather');
      if (weather) insertAfter(weather, build('leaderboard', slotIx++));
      var mainCity = document.querySelector('main') || document.body;
      appendInto(mainCity, build('hero', slotIx++));
      return;
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', inject);
  } else {
    inject();
  }
})();
