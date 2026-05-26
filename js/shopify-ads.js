/*
 * Shopify negative-space ads — auto-injects Shopify campaign 13624
 * banners into the editorial gaps across the site.
 *
 * Independent of /js/sponsors.js (which handles the curated luxury
 * sponsor card). This one is volume inventory: it picks one creative
 * per slot from the Shopify rotation and drops it in. Different page
 * types get different formats:
 *
 *   article         → 728×90 leaderboard before .more-to-read
 *                     + a 1200×628 hero just before the related rail
 *   article-list    → 728×90 leaderboard between blocks of cards
 *   hub             → 1200×628 hero before footer
 *   home            → 728×90 between lower-section blocks
 *   city-page       → 728×90 mid-list
 *
 * No banner ever lands inside a paragraph of body copy.
 *
 * Impact campaign 13624. Tracking pixel format:
 *   https://imp.pxf.io/i/7333540/{creative_id}/13624
 * Click URL format:
 *   https://shopify.pxf.io/c/7333540/{creative_id}/13624
 * Image URL format:
 *   //a.impactradius-go.com/display-ad/13624-{creative_id}
 */
(function () {
  'use strict';

  if (window.__shopifyAdsLoaded) return;
  window.__shopifyAdsLoaded = true;

  // ─── Inventory ─────────────────────────────────────────────────────
  var INVENTORY = {
    leaderboard: [
      // Sidekick — "Starting a store is easier than you think"
      { id: 3797165, label: 'Starting a store is easier than you think',
        cta: 'Start free trial →' },
      { id: 3797169, label: 'Starting a store is easier than you think',
        cta: 'Start free trial →' },
      // Evergreen — "Daydream to Dream Job"
      { id: 3323854, label: 'From daydream to dream job',
        cta: 'Try Shopify for $1 →' },
      // Evergreen — "Idea to Business"
      { id: 3323861, label: 'Turn your idea into your business',
        cta: 'Try Shopify for $1 →' },
    ],
    hero: [
      { id: 3797168, label: 'Starting a store is easier than you think',
        cta: 'Start free trial →' },
      { id: 3323855, label: 'Turn your idea into your business',
        cta: 'Try Shopify for $1 →' },
      { id: 3323848, label: 'From daydream to dream job',
        cta: 'Try Shopify for $1 →' },
      { id: 3323841, label: 'Change your life',
        cta: 'Try Shopify for $1 →' },
    ],
    rectangle: [
      { id: 3323850, label: 'From daydream to dream job',
        cta: 'Try Shopify for $1 →' },
      { id: 3323857, label: 'Turn your idea into your business',
        cta: 'Try Shopify for $1 →' },
      { id: 3323860, label: 'Turn your idea into your business',
        cta: 'Try Shopify for $1 →' },
    ],
  };

  var FORMAT_DIMS = {
    leaderboard: { w: 728,  h: 90  },
    hero:        { w: 1200, h: 628 },
    rectangle:   { w: 300,  h: 250 },
  };

  function pick(format) {
    var pool = INVENTORY[format];
    return pool[Math.floor(Math.random() * pool.length)];
  }

  // ─── Build ─────────────────────────────────────────────────────────
  function build(format, ix) {
    var c = pick(format);
    if (!c) return null;
    var dim = FORMAT_DIMS[format];

    var card = document.createElement('aside');
    card.className = 'shopify-banner shopify-banner--' + format;
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
    img.width = dim.w;
    img.height = dim.h;
    a.appendChild(img);
    card.appendChild(a);

    var cap = document.createElement('p');
    cap.className = 'shopify-banner-caption';
    cap.textContent = c.label + ' — ' + c.cta;
    card.appendChild(cap);

    // Fire impression pixel
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
      // 1) leaderboard between share + more-to-read
      if (moreToRead) injectBefore(moreToRead, build('leaderboard', slotIx++));
      else if (share) insertAfter(share, build('leaderboard', slotIx++));
      // 2) hero before the cross-site rail (visual finale before footer)
      if (rrRail) injectBefore(rrRail, build('hero', slotIx++));
      return;
    }

    if (type === 'hub') {
      // pre-footer hero on hub pages
      var main = document.querySelector('main');
      if (main) appendInto(main, build('hero', slotIx++));
      return;
    }

    if (type === 'list' || type === 'home') {
      // After every ~8 cards, drop a leaderboard
      var cards = document.querySelectorAll(
        '.article-card, .more-card, .news-card, .card, .post-summary'
      );
      var n = cards.length;
      [8, 16, 24].forEach(function (target) {
        if (n > target && cards[target]) {
          insertAfter(cards[target], build('leaderboard', slotIx++));
        }
      });
      // pre-footer hero on these too
      var mainEl = document.querySelector('main') || document.querySelector('.lower-section');
      if (mainEl) appendInto(mainEl, build('hero', slotIx++));
      return;
    }

    if (type === 'city') {
      // city-page: leaderboard after the weather strip if present, else top of list
      var weather = document.querySelector('.city-weather');
      if (weather) insertAfter(weather, build('leaderboard', slotIx++));
      var mainCity = document.querySelector('main') || document.body;
      appendInto(mainCity, build('hero', slotIx++));
      return;
    }

    // other / unknown — silent
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', inject);
  } else {
    inject();
  }
})();
