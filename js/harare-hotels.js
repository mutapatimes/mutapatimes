/*
 * Hotels carousel — site-wide "Sponsored stays" rail backed by Hotels.com
 * (Commission Junction advertiser 1702763, ad 13344203). Despite the
 * filename it now serves every city, not just Harare.
 *
 * Slot API (any element):
 *   data-hotels-city="harare|bulawayo|victoria-falls|mutare|masvingo|gweru|all"
 *   data-hotels-variant="feature|feed"   (default: feature)
 *   data-count="8"                        (optional, cards to pick)
 *   data-harare-hotels                    (legacy alias → city "harare", feature)
 *
 * "feature" = prominent 4-up rail with large images (article / flight pages).
 * "feed"    = compact rail that blends into a city news feed.
 *
 * Behaviour: prev/next arrows, native swipe via scroll-snap, gentle
 * auto-advance that pauses on hover/focus/touch and is disabled under
 * prefers-reduced-motion. Day-seeded picks so the set is stable per day.
 *
 * Data: /data/hotels.json — { "<city>": {title, scope, hotels:[…]}, "all": […] }
 */
(function () {
  'use strict';

  var SLOTS = document.querySelectorAll('[data-hotels-city], [data-harare-hotels]');
  if (!SLOTS.length) return;

  var FEED_URL = '/data/hotels.json';
  var AUTOPLAY_MS = 5000;
  var GAP = 16; // keep in sync with .hh-rail-track gap in main.css
  var REDUCED = window.matchMedia &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function daySeed() {
    var d = new Date();
    return Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate()) / 86400000;
  }

  // Mulberry32 — small deterministic PRNG so the day's pick is reproducible.
  function rng(seed) {
    var s = seed >>> 0;
    return function () {
      s = (s + 0x6D2B79F5) >>> 0;
      var t = s;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  function pickHotels(all, count, seed) {
    var r = rng(seed);
    var pool = all.slice();
    var out = [];
    while (pool.length && out.length < count) {
      out.push(pool.splice(Math.floor(r() * pool.length), 1)[0]);
    }
    return out;
  }

  function el(tag, attrs, children) {
    var n = document.createElement(tag);
    if (attrs) for (var k in attrs) {
      if (k === 'class') n.className = attrs[k];
      else if (k === 'text') n.textContent = attrs[k];
      else if (k === 'html') n.innerHTML = attrs[k];
      else n.setAttribute(k, attrs[k]);
    }
    if (children) for (var i = 0; i < children.length; i++) if (children[i]) n.appendChild(children[i]);
    return n;
  }

  function arrow(dir) {
    var svg = '<svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true" focusable="false">' +
      (dir === 'prev'
        ? '<path d="M15 5l-7 7 7 7" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>'
        : '<path d="M9 5l7 7-7 7" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>') +
      '</svg>';
    return el('button', {
      type: 'button',
      class: 'hh-rail-arrow hh-rail-arrow--' + dir,
      'aria-label': dir === 'prev' ? 'Previous stays' : 'More stays',
      html: svg
    });
  }

  function step(track) {
    var card = track.querySelector('.hh-card');
    return card ? card.getBoundingClientRect().width + GAP : track.clientWidth * 0.8;
  }
  function atEnd(track) { return track.scrollLeft + track.clientWidth >= track.scrollWidth - 8; }
  function atStart(track) { return track.scrollLeft <= 4; }

  function setupCarousel(stage, track, prevBtn, nextBtn) {
    function syncArrows() {
      var overflow = track.scrollWidth > track.clientWidth + 4;
      stage.classList.toggle('hh-rail-stage--static', !overflow);
      prevBtn.disabled = !overflow || atStart(track);
      nextBtn.disabled = !overflow || atEnd(track);
    }
    function go(delta) { track.scrollBy({ left: delta * step(track), behavior: 'smooth' }); }

    prevBtn.addEventListener('click', function () { go(-1); });
    nextBtn.addEventListener('click', function () { go(1); });
    track.addEventListener('scroll', syncArrows, { passive: true });
    window.addEventListener('resize', syncArrows);
    syncArrows();
    requestAnimationFrame(syncArrows);
    track.querySelectorAll('img').forEach(function (img) {
      img.addEventListener('load', syncArrows, { once: true });
    });

    if (REDUCED) return;
    var timer = null;
    function tick() {
      if (track.scrollWidth <= track.clientWidth + 4) return;
      if (atEnd(track)) track.scrollTo({ left: 0, behavior: 'smooth' });
      else go(1);
    }
    function start() { if (!timer) timer = setInterval(tick, AUTOPLAY_MS); }
    function stop() { if (timer) { clearInterval(timer); timer = null; } }
    stage.addEventListener('mouseenter', stop);
    stage.addEventListener('mouseleave', start);
    stage.addEventListener('focusin', stop);
    stage.addEventListener('focusout', start);
    track.addEventListener('pointerdown', stop);
    document.addEventListener('visibilitychange', function () {
      if (document.hidden) stop(); else start();
    });
    start();
  }

  function render(slot, block, variant) {
    var hotels = block.hotels || [];
    if (!hotels.length) return;
    slot.innerHTML = '';
    slot.className = (slot.className || '') + ' hh-rail hh-rail--' + variant;

    slot.appendChild(el('div', { class: 'hh-rail-head' }, [
      el('p', { class: 'hh-rail-eyebrow', text: 'Sponsored stays' }),
      el('h2', { class: 'hh-rail-title', text: block.title || 'Where to stay' }),
      el('p', { class: 'hh-rail-sub', text: 'Handpicked stays, booked through Hotels.com.' })
    ]));

    var track = el('div', {
      class: 'hh-rail-track',
      tabindex: '0',
      'aria-label': (block.title || 'Hotels') + ' carousel'
    });
    hotels.forEach(function (h) {
      var img = el('img', {
        class: 'hh-card-img', src: h.image, alt: h.name, loading: 'lazy',
        width: '400', height: '260', referrerpolicy: 'no-referrer-when-downgrade'
      });
      track.appendChild(el('a', {
        class: 'hh-card',
        href: h.url,
        target: '_blank',
        rel: 'noopener sponsored nofollow',
        'data-area': h.area || '',
        'aria-label': h.name + '. Book on Hotels.com'
      }, [
        el('div', { class: 'hh-card-imgwrap' }, [img]),
        el('div', { class: 'hh-card-body' }, [
          el('p', { class: 'hh-card-area', text: h.area || '' }),
          el('h3', { class: 'hh-card-name', text: h.name }),
          el('p', { class: 'hh-card-cta', text: 'Book on Hotels.com →' })
        ])
      ]));
    });

    var prevBtn = arrow('prev'), nextBtn = arrow('next');
    var stage = el('div', { class: 'hh-rail-stage' }, [prevBtn, track, nextBtn]);
    slot.appendChild(stage);
    setupCarousel(stage, track, prevBtn, nextBtn);
  }

  fetch(FEED_URL, { cache: 'force-cache' })
    .then(function (r) { return r.json(); })
    .then(function (data) {
      SLOTS.forEach(function (slot) {
        var city = slot.getAttribute('data-hotels-city') || 'harare';
        var variant = slot.getAttribute('data-hotels-variant') || 'feature';
        var block = data[city];
        if (!block || !(block.hotels || []).length) return;
        var n = parseInt(slot.getAttribute('data-count'), 10);
        if (isNaN(n) || n < 2) n = (variant === 'feed' ? 8 : 10);
        var all = block.hotels;
        if (n > all.length) n = all.length;
        var salt = parseInt(slot.getAttribute('data-seed-salt'), 10) || 0;
        render(slot, { title: block.title, scope: block.scope, hotels: pickHotels(all, n, daySeed() + salt) }, variant);
      });
    })
    .catch(function () { /* swallow — never block the page */ });
})();
