/*
 * Editorial sponsor renderer — two formats:
 *
 *   1. Strip   — hairline "Sponsored briefing by X" line near the top
 *                of the page. Used on editorial surfaces (news, articles,
 *                economy, jobs, markets, city pages) so we never drop a
 *                rectangular banner into article body content.
 *
 *   2. Card    — a "Presented by X" card with the affiliate's actual
 *                creative (image or iframe), an editorial eyebrow, the
 *                creative, and a one-line caption. Used on chic luxury
 *                surfaces (/flights/, /airports/, /diaspora/*) where a
 *                visual makes sense.
 *
 * Each sponsor in /data/sponsors.json may declare:
 *   - placements         → which page keys get the STRIP
 *   - card_placements    → which page keys get the CARD
 *   - creative_url       → Impact /display-ad/... image
 *   - creative_iframe_src→ Impact /gen-ad-code/... iframe (for rich media)
 *   - creative_width/height
 *   - creative_eyebrow   → defaults to "PRESENTED BY {NAME}"
 *   - creative_caption   → defaults to strip_copy
 *   - impression_pixel   → Impact /i/... pixel, fired as hidden 0×0
 *   - weight             → relative share when several sponsors match
 *
 * Page key is read from <body data-sponsor-page> or derived from the URL.
 * One sponsor per page per pageview, weighted-random when several match.
 */
(function () {
  'use strict';
  var mtUrl = window.mtUrl || function (p) { return p; };

  function detectPage() {
    var bodyKey = document.body.getAttribute('data-sponsor-page');
    if (bodyKey) return bodyKey;
    var path = (location.pathname || '/').replace(/\/$/, '');
    if (path === '' || path === '/index.html') return 'news';
    var seg = path.split('/').filter(Boolean)[0] || 'news';
    return seg.replace(/-news$/, '-cities').replace(/\.html$/, '');
  }

  function pickWeighted(matches) {
    if (matches.length === 1) return matches[0];
    var total = 0, i;
    for (i = 0; i < matches.length; i++) {
      total += Math.max(0, Number(matches[i].weight) || 1);
    }
    var r = Math.random() * total;
    for (i = 0; i < matches.length; i++) {
      r -= Math.max(0, Number(matches[i].weight) || 1);
      if (r <= 0) return matches[i];
    }
    return matches[matches.length - 1];
  }

  function firePixel(parent, src) {
    if (!src) return;
    var px = new Image(0, 0);
    px.alt = '';
    px.referrerPolicy = 'no-referrer-when-downgrade';
    px.style.position = 'absolute';
    px.style.visibility = 'hidden';
    px.style.width = '0';
    px.style.height = '0';
    px.src = src;
    parent.appendChild(px);
  }

  // ─── STRIP (editorial surfaces) ────────────────────────────────────

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
    firePixel(strip, s.impression_pixel);
    return strip;
  }

  function placeStrip(strip) {
    var host = document.getElementById('sponsorSlot');
    if (host) { host.appendChild(strip); return; }
    var paper = document.querySelector('.paper');
    var main = document.querySelector('main');
    var anchor = paper || main || document.body.firstElementChild;
    if (anchor && anchor.parentNode) {
      anchor.parentNode.insertBefore(strip, anchor);
    }
  }

  // ─── CARD (chic luxury surfaces) ───────────────────────────────────

  function buildCard(s) {
    var card = document.createElement('aside');
    card.className = 'sponsor-card';
    card.setAttribute('role', 'complementary');
    card.setAttribute('aria-label', 'Presented by ' + (s.name || 'sponsor'));

    var eyebrow = document.createElement('p');
    eyebrow.className = 'sponsor-card-eyebrow';
    eyebrow.textContent = (s.creative_eyebrow
                           || ('Presented by ' + (s.name || 'sponsor'))).toUpperCase();
    card.appendChild(eyebrow);

    var a = document.createElement('a');
    a.className = 'sponsor-card-link';
    a.href = s.url;
    a.target = '_blank';
    a.rel = 'noopener sponsored';

    var media = document.createElement('div');
    media.className = 'sponsor-card-media';
    // Constrain very large creatives by aspect ratio so they don't
    // wreck the layout; CSS clamps the width.
    if (s.creative_width && s.creative_height) {
      media.style.aspectRatio = s.creative_width + ' / ' + s.creative_height;
    }

    if (s.creative_iframe_src) {
      var iframe = document.createElement('iframe');
      iframe.src = s.creative_iframe_src;
      iframe.scrolling = 'no';
      iframe.frameBorder = '0';
      iframe.setAttribute('marginheight', '0');
      iframe.setAttribute('marginwidth', '0');
      iframe.setAttribute('loading', 'lazy');
      iframe.setAttribute('referrerpolicy', 'no-referrer-when-downgrade');
      iframe.style.width = '100%';
      iframe.style.height = '100%';
      iframe.style.border = '0';
      iframe.title = (s.name || 'Sponsor') + ' creative';
      media.appendChild(iframe);
    } else if (s.creative_url) {
      var img = document.createElement('img');
      img.src = (/^\/\//.test(s.creative_url) ? 'https:' + s.creative_url
                                              : s.creative_url);
      img.alt = '';
      img.loading = 'lazy';
      img.referrerPolicy = 'no-referrer-when-downgrade';
      img.style.maxWidth = '100%';
      img.style.height = 'auto';
      img.style.display = 'block';
      img.style.margin = '0 auto';
      if (s.creative_width)  img.width  = s.creative_width;
      if (s.creative_height) img.height = s.creative_height;
      media.appendChild(img);
    } else {
      // No creative provided — degrade to strip-style text inside card.
      var fallback = document.createElement('p');
      fallback.className = 'sponsor-card-fallback';
      fallback.textContent = s.strip_copy || ('Visit ' + (s.name || 'sponsor'));
      media.appendChild(fallback);
    }

    a.appendChild(media);
    card.appendChild(a);

    var caption = document.createElement('p');
    caption.className = 'sponsor-card-caption';
    caption.textContent = s.creative_caption || s.strip_copy || '';
    if (caption.textContent) card.appendChild(caption);

    firePixel(card, s.impression_pixel);
    return card;
  }

  function placeCard(card) {
    // Prefer an explicit host the page author placed. Otherwise drop
    // the card after the hero (or the first <section>) inside <main>.
    var host = document.getElementById('sponsorCardSlot');
    if (host) { host.appendChild(card); return; }
    var main = document.querySelector('main');
    if (!main) { document.body.appendChild(card); return; }
    var hero = main.querySelector('header, .fl-hero, .dp-hero');
    if (hero && hero.parentNode === main) {
      hero.insertAdjacentElement('afterend', card);
      return;
    }
    var firstSection = main.querySelector('section');
    if (firstSection) {
      firstSection.insertAdjacentElement('afterend', card);
      return;
    }
    main.appendChild(card);
  }

  // ─── Boot ──────────────────────────────────────────────────────────

  fetch(mtUrl('/data/sponsors.json'), { cache: 'no-store' })
    .then(function (r) { return r.ok ? r.json() : null; })
    .then(function (d) {
      if (!d || !Array.isArray(d.sponsors) || !d.sponsors.length) return;
      var page = detectPage();

      var stripMatches = d.sponsors.filter(function (s) {
        return (s.placements || []).indexOf(page) !== -1;
      });
      var cardMatches = d.sponsors.filter(function (s) {
        return (s.card_placements || []).indexOf(page) !== -1
            && (s.creative_url || s.creative_iframe_src);
      });

      if (stripMatches.length) placeStrip(buildStrip(pickWeighted(stripMatches)));
      if (cardMatches.length)  placeCard(buildCard(pickWeighted(cardMatches)));
    })
    .catch(function () {});
})();
