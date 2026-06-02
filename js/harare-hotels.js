/*
 * Harare Hotels rail — affiliate inventory from Hotels.com (Commission
 * Junction advertiser 1702763, ad 13344203). Renders into any element
 * with a `data-harare-hotels` attribute. Placement is editorial:
 * strip-style "Sponsored stays" eyebrow, image + name + neighbourhood
 * + Book CTA. No price (inventory feed doesn't ship rates) and no
 * autoplay, no popovers. Day-rotated picks so a given visitor sees
 * the same 6 hotels for the day instead of a thrashing carousel.
 *
 * Data lives in /data/harare-hotels.json, loaded once per page.
 */
(function () {
  'use strict';

  var SLOTS = document.querySelectorAll('[data-harare-hotels]');
  if (!SLOTS.length) return;

  var FEED_URL = '/data/harare-hotels.json';
  var DEFAULT_COUNT = 6;

  function daySeed() {
    // Same seed all day for a given UTC date so the picks are stable.
    var d = new Date();
    return Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate()) / 86400000;
  }

  // Mulberry32 — small deterministic PRNG so the day's pick is
  // reproducible without a heavy hashing dependency.
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
      var i = Math.floor(r() * pool.length);
      out.push(pool.splice(i, 1)[0]);
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

  function render(slot, hotels) {
    slot.innerHTML = '';
    slot.className = (slot.className || '') + ' hh-rail';

    var head = el('div', { class: 'hh-rail-head' }, [
      el('p', { class: 'hh-rail-eyebrow', text: 'Sponsored stays' }),
      el('h2', { class: 'hh-rail-title', text: 'Where to stay in Harare' }),
      el('p', { class: 'hh-rail-sub', text: 'Curated rooms and lodges in Harare. Booked through Hotels.com.' })
    ]);
    slot.appendChild(head);

    var track = el('div', { class: 'hh-rail-track' });
    hotels.forEach(function (h) {
      var img = el('img', {
        class: 'hh-card-img',
        src: h.image,
        alt: h.name,
        loading: 'lazy',
        width: '350',
        height: '195',
        referrerpolicy: 'no-referrer-when-downgrade'
      });
      var card = el('a', {
        class: 'hh-card',
        href: h.url,
        target: '_blank',
        rel: 'noopener sponsored nofollow',
        'aria-label': h.name + ' in Harare. Book on Hotels.com'
      }, [
        el('div', { class: 'hh-card-imgwrap' }, [img]),
        el('div', { class: 'hh-card-body' }, [
          el('p', { class: 'hh-card-area', text: h.area }),
          el('h3', { class: 'hh-card-name', text: h.name }),
          el('p', { class: 'hh-card-cta', text: 'Book on Hotels.com →' })
        ])
      ]);
      track.appendChild(card);
    });
    slot.appendChild(track);

    // Disclosure line
    slot.appendChild(el('p', {
      class: 'hh-rail-disclosure',
      html: 'The Mutapa Times earns a commission on bookings made via these links. Editorial coverage is independent.'
    }));
  }

  // Single fetch shared across all slots on the page
  fetch(FEED_URL, { cache: 'force-cache' })
    .then(function (r) { return r.json(); })
    .then(function (data) {
      var all = (data && data.hotels) || [];
      if (!all.length) return;
      SLOTS.forEach(function (slot) {
        var n = parseInt(slot.getAttribute('data-count') || DEFAULT_COUNT, 10);
        if (isNaN(n) || n < 2) n = DEFAULT_COUNT;
        if (n > all.length) n = all.length;
        var picked = pickHotels(all, n, daySeed() + slot.getAttribute('data-seed-salt') * 1 || daySeed());
        render(slot, picked);
      });
    })
    .catch(function () { /* swallow — never block the page */ });
})();
