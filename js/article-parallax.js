/*
 * Article longform behaviours.
 * Three independent observers/handlers:
 *   1. Full-bleed parallax — translates .article-fullbleed-media as the
 *      frame moves through the viewport.
 *   2. Count-up — animates .count-up spans to their data-to value when
 *      they enter the viewport. Tabular figures, decimals supported.
 *   3. Scroll-reveal — adds .is-visible to .reveal-on-scroll elements
 *      and (by default) every <p>, <h2>, <figure>, <aside> inside an
 *      .article-body-longform, on first entry to the viewport.
 *
 * All three respect prefers-reduced-motion: reduce. Each guards on the
 * presence of its target so the module is a no-op on non-longform pages.
 */
(function () {
  'use strict';

  var reduceMotion = window.matchMedia &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // ── 1. Parallax (existing behaviour) ──────────────────────────
  var frames = [].slice.call(
    document.querySelectorAll('.article-fullbleed-frame')
  );
  if (frames.length && !reduceMotion) {
    parallax(frames);
  }

  // ── 2. Count-up animations ────────────────────────────────────
  var counters = [].slice.call(document.querySelectorAll('.count-up'));
  if (counters.length) countUp(counters);

  // ── 3. Scroll-reveal ──────────────────────────────────────────
  scrollReveal();
})();

function parallax(frames) {
  'use strict';

  // Cache references and the parallax magnitude (px of travel).
  var items = frames.map(function (frame) {
    var media = frame.querySelector('.article-fullbleed-media');
    return { frame: frame, media: media, travel: 80 };  // ±80px
  });

  var ticking = false;
  function onScroll() {
    if (ticking) return;
    ticking = true;
    window.requestAnimationFrame(update);
  }
  function update() {
    var vh = window.innerHeight || document.documentElement.clientHeight;
    items.forEach(function (it) {
      if (!it.media) return;
      var rect = it.frame.getBoundingClientRect();
      if (rect.bottom < 0 || rect.top > vh) return;  // off-screen
      // progress 0 when frame's top is at the bottom of the viewport,
      // 1 when frame's bottom is at the top. Maps to [-travel, +travel].
      var progress = (vh - rect.top) / (vh + rect.height);
      progress = Math.max(0, Math.min(1, progress));
      var y = (progress - 0.5) * 2 * it.travel;  // -travel..+travel
      it.media.style.transform = 'translate3d(0, ' + y.toFixed(1) + 'px, 0)';
    });
    ticking = false;
  }

  window.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('resize', onScroll, { passive: true });
  // Kick once on load so already-visible frames get the right offset.
  update();
}

// ── Count-up animation ───────────────────────────────────────────
function countUp(elements) {
  'use strict';
  var reduceMotion = window.matchMedia &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function format(n, decimals) {
    if (decimals > 0) {
      var s = n.toFixed(decimals);
      // Thousands separators on the integer part
      var parts = s.split('.');
      parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ',');
      return parts.join('.');
    }
    return Math.round(n).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
  }

  function animate(el) {
    var to = parseFloat(el.getAttribute('data-to') || '0');
    var decimals = parseInt(el.getAttribute('data-decimals') || '0', 10);
    var prefix = el.getAttribute('data-prefix') || '';
    var suffix = el.getAttribute('data-suffix') || '';
    var duration = parseInt(el.getAttribute('data-duration') || '1200', 10);
    var start = performance.now();
    if (reduceMotion || to === 0) {
      el.textContent = prefix + format(to, decimals) + suffix;
      return;
    }
    function tick(now) {
      var elapsed = now - start;
      var t = Math.min(1, elapsed / duration);
      // ease-out cubic
      var eased = 1 - Math.pow(1 - t, 3);
      var current = to * eased;
      el.textContent = prefix + format(current, decimals) + suffix;
      if (t < 1) requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  }

  if (!('IntersectionObserver' in window)) {
    elements.forEach(animate);
    return;
  }
  var seen = new WeakSet();
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (e.isIntersecting && !seen.has(e.target)) {
        seen.add(e.target);
        animate(e.target);
        io.unobserve(e.target);
      }
    });
  }, { threshold: 0.5, rootMargin: '0px 0px -10% 0px' });
  elements.forEach(function (el) { io.observe(el); });
}

// ── Scroll-reveal ─────────────────────────────────────────────────
function scrollReveal() {
  'use strict';
  var reduceMotion = window.matchMedia &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (reduceMotion) return;
  if (!('IntersectionObserver' in window)) return;

  // Tag every meaningful block inside a longform article body for reveal,
  // skipping anything already tagged. Pull quotes, figures, stat rows,
  // headings and paragraphs all qualify.
  var body = document.querySelector('.article-body-longform');
  if (body) {
    var selectors = 'p, h2, h3, figure, aside, blockquote, .article-stat-row, .article-fullbleed';
    var els = [].slice.call(body.querySelectorAll(selectors));
    els.forEach(function (el) {
      if (!el.classList.contains('reveal-on-scroll')) {
        el.classList.add('reveal-on-scroll');
      }
    });
  }

  var targets = [].slice.call(document.querySelectorAll('.reveal-on-scroll'));
  if (!targets.length) return;

  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (e.isIntersecting) {
        e.target.classList.add('is-visible');
        io.unobserve(e.target);
      }
    });
  }, { threshold: 0.12, rootMargin: '0px 0px -8% 0px' });
  targets.forEach(function (el) { io.observe(el); });
}
