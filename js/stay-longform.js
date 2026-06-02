/*
 * Scrollytelling enhancements for the "Where to stay" longform guides
 * by Tendai Kuwanda. No-ops on any page without [data-stay-section]
 * blocks, so it is safe to load site-wide on article pages.
 *
 * Adds, progressively (nothing is required for the article to read):
 *   1. A reading-progress bar pinned under the topbar.
 *   2. A sticky in-article section nav built from each
 *      <section data-stay-section data-stay-label="…" id="…"> block,
 *      with the active section highlighted on scroll.
 *   3. Scroll-reveal of each section (skipped under prefers-reduced-motion).
 *   4. A neighbourhood filter above the embedded hotels carousel
 *      ([data-stay-carousel]) that filters cards by their data-area once
 *      js/harare-hotels.js has rendered them.
 */
(function () {
  'use strict';

  var sections = Array.prototype.slice.call(
    document.querySelectorAll('[data-stay-section]')
  );
  if (!sections.length) return;

  var REDUCED = window.matchMedia &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function el(tag, attrs, kids) {
    var n = document.createElement(tag);
    if (attrs) for (var k in attrs) {
      if (k === 'class') n.className = attrs[k];
      else if (k === 'text') n.textContent = attrs[k];
      else n.setAttribute(k, attrs[k]);
    }
    (kids || []).forEach(function (c) { if (c) n.appendChild(c); });
    return n;
  }

  /* ---- 1. Reading progress bar ---------------------------------- */
  var bar = el('div', { class: 'stay-progress', 'aria-hidden': 'true' });
  document.body.appendChild(bar);
  function onScroll() {
    var h = document.documentElement;
    var max = h.scrollHeight - h.clientHeight;
    bar.style.transform = 'scaleX(' + (max > 0 ? h.scrollTop / max : 0) + ')';
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  /* ---- 2. Sticky section nav ------------------------------------ */
  var labelled = sections.filter(function (s) {
    return s.getAttribute('data-stay-label');
  });
  labelled.forEach(function (s, i) {
    if (!s.id) s.id = 'stay-sec-' + i;
  });

  var links = {};
  if (labelled.length > 1) {
    var nav = el('nav', { class: 'stay-nav', 'aria-label': 'Jump to area' });
    var list = el('div', { class: 'stay-nav-inner' });
    labelled.forEach(function (s) {
      var a = el('a', {
        class: 'stay-nav-link',
        href: '#' + s.id,
        text: s.getAttribute('data-stay-label')
      });
      links[s.id] = a;
      list.appendChild(a);
    });
    nav.appendChild(list);
    var first = labelled[0];
    first.parentNode.insertBefore(nav, first);

    if ('IntersectionObserver' in window) {
      var spy = new IntersectionObserver(function (entries) {
        entries.forEach(function (e) {
          if (e.isIntersecting && links[e.target.id]) {
            Object.keys(links).forEach(function (id) {
              links[id].classList.toggle('is-active', id === e.target.id);
            });
          }
        });
      }, { rootMargin: '-45% 0px -50% 0px' });
      labelled.forEach(function (s) { spy.observe(s); });
    }
  }

  /* ---- 3. Scroll reveal ----------------------------------------- */
  if (!REDUCED && 'IntersectionObserver' in window) {
    var revealer = new IntersectionObserver(function (entries, obs) {
      entries.forEach(function (e) {
        if (e.isIntersecting) {
          e.target.classList.add('is-visible');
          obs.unobserve(e.target);
        }
      });
    }, { rootMargin: '0px 0px -12% 0px' });
    sections.forEach(function (s) {
      s.classList.add('stay-reveal');
      revealer.observe(s);
    });
  }

  /* ---- 4. Neighbourhood filter on the embedded carousel --------- */
  var carousel = document.querySelector('[data-stay-carousel]');
  if (!carousel) return;

  function buildFilter() {
    var cards = Array.prototype.slice.call(carousel.querySelectorAll('.hh-card'));
    if (!cards.length) return false;
    var areas = [];
    cards.forEach(function (c) {
      var a = (c.getAttribute('data-area') || '').trim();
      if (a && areas.indexOf(a) === -1) areas.push(a);
    });
    if (areas.length < 2) return true; // nothing useful to filter by

    var filter = el('div', { class: 'stay-filter', role: 'group', 'aria-label': 'Filter stays by area' });
    var mk = function (label, value) {
      var b = el('button', { type: 'button', class: 'stay-filter-chip', text: label });
      b.addEventListener('click', function () {
        filter.querySelectorAll('.stay-filter-chip').forEach(function (x) {
          x.classList.toggle('is-active', x === b);
        });
        cards.forEach(function (c) {
          var a = (c.getAttribute('data-area') || '').trim();
          c.hidden = !(value === null || a === value);
        });
      });
      return b;
    };
    var allBtn = mk('All areas', null);
    allBtn.classList.add('is-active');
    filter.appendChild(allBtn);
    areas.forEach(function (a) { filter.appendChild(mk(a, a)); });

    var head = carousel.querySelector('.hh-rail-head');
    if (head) head.appendChild(filter); else carousel.insertBefore(filter, carousel.firstChild);
    return true;
  }

  if (!buildFilter()) {
    // Cards render async (fetch). Watch the slot until they appear.
    if ('MutationObserver' in window) {
      var mo = new MutationObserver(function () {
        if (buildFilter()) mo.disconnect();
      });
      mo.observe(carousel, { childList: true, subtree: true });
      setTimeout(function () { mo.disconnect(); }, 8000);
    }
  }
})();
