/*
 * Site-wide nav handlers:
 *   • Hamburger button → slide-in drawer
 *   • Cities dropdown toggle (button + .nav-cities-item wrapper)
 *
 * Loaded on every page (top-level HTML and article templates).
 * Vanilla JS, no dependencies, defensive null-checks throughout.
 */
(function () {
  'use strict';

  // ── Hamburger drawer ──────────────────────────────────────────
  // Multiple buttons can open the drawer: the masthead .nav-hamburger
  // AND the sticky topbar [data-open-drawer] button. Both share state.
  var hamburgers = document.querySelectorAll('.nav-hamburger, [data-open-drawer]');
  var drawer = document.getElementById('navDrawer');
  var backdrop = document.querySelector('.nav-drawer-backdrop');

  function setHamburgerState(expanded) {
    hamburgers.forEach(function (h) {
      h.setAttribute('aria-expanded', expanded ? 'true' : 'false');
    });
  }
  function openDrawer() {
    if (!drawer) return;
    drawer.classList.add('is-open');
    if (backdrop) backdrop.classList.add('is-visible');
    document.documentElement.classList.add('nav-drawer-locked');
    setHamburgerState(true);
    drawer.setAttribute('aria-hidden', 'false');
  }
  function closeDrawer() {
    if (!drawer) return;
    drawer.classList.remove('is-open');
    if (backdrop) backdrop.classList.remove('is-visible');
    document.documentElement.classList.remove('nav-drawer-locked');
    setHamburgerState(false);
    drawer.setAttribute('aria-hidden', 'true');
  }
  function toggleDrawer() {
    if (!drawer) return;
    if (drawer.classList.contains('is-open')) closeDrawer();
    else openDrawer();
  }

  hamburgers.forEach(function (h) {
    h.addEventListener('click', function (e) {
      // Don't double-handle close clicks (the close button has
      // [data-close-drawer] which is handled separately below).
      if (h.closest('[data-close-drawer]')) return;
      e.preventDefault();
      toggleDrawer();
    });
  });

  // ── Sticky topbar reveal + reading progress bar ──────────────
  // One scroll listener drives both: rAF-throttled, passive.
  // Topbar slides in once the user has scrolled ~10% of the page
  // (or at least 160px) — feels like "you're meaningfully into the
  // content" without being trigger-happy.
  (function () {
    function computeThreshold() {
      var doc = document.documentElement;
      return Math.max(160, doc.scrollHeight * 0.10);
    }
    var topbarThreshold = computeThreshold();
    window.addEventListener('resize', function () {
      topbarThreshold = computeThreshold();
    }, { passive: true });
    // Optional reading-progress bar — only on article-like pages.
    // Auto-injects a thin top strip whose ::after fills as you scroll.
    var hasArticle = document.querySelector('.article-full, .news-landing, .article-body');
    var progress = null;
    if (hasArticle && !document.querySelector('.read-progress')) {
      progress = document.createElement('div');
      progress.className = 'read-progress';
      document.body.appendChild(progress);
    }
    var raf = null;
    function onScroll() {
      if (raf) return;
      raf = requestAnimationFrame(function () {
        raf = null;
        var y = window.scrollY || document.documentElement.scrollTop || 0;
        document.body.classList.toggle('is-scrolled', y > topbarThreshold);
        if (progress) {
          var doc = document.documentElement;
          var max = (doc.scrollHeight || 1) - window.innerHeight;
          var pct = max > 0 ? Math.min(100, (y / max) * 100) : 0;
          progress.style.setProperty('--read-progress', pct.toFixed(2) + '%');
        }
      });
    }
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  })();

  // ── Smooth scroll-to-top for the legacy onclick="window.scrollTo"
  // and any [data-scroll-top] button — already smooth-on-modern via
  // CSS, but this preserves behaviour where reduced-motion is set.
  document.querySelectorAll('[data-scroll-top], .back-to-top-btn').forEach(function (b) {
    b.addEventListener('click', function (e) {
      e.preventDefault();
      try {
        window.scrollTo({ top: 0, behavior: 'smooth' });
      } catch (_) {
        window.scrollTo(0, 0);
      }
    });
  });

  // ── Smooth-scroll for any in-page anchor link with #target ────
  // (CSS scroll-behavior covers this on modern browsers; this is the
  // belt-and-braces fallback for older Safari and respects reduced-motion.)
  document.addEventListener('click', function (e) {
    var a = e.target && e.target.closest && e.target.closest('a[href^="#"]');
    if (!a) return;
    var href = a.getAttribute('href') || '';
    if (href === '#' || href === '#!') return;
    var target = document.querySelector(href);
    if (!target) return;
    e.preventDefault();
    var prefersReduce = window.matchMedia &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    target.scrollIntoView({
      behavior: prefersReduce ? 'auto' : 'smooth',
      block: 'start',
    });
    // Keep the URL hash in sync without jumping
    if (history.pushState) history.pushState(null, '', href);
  });
  // Close on backdrop tap, close-button tap, or any anchor tap inside drawer
  document.addEventListener('click', function (e) {
    var t = e.target;
    if (!t) return;
    if (t.closest && t.closest('[data-close-drawer]')) {
      e.preventDefault();
      closeDrawer();
      return;
    }
    if (drawer && drawer.classList.contains('is-open')) {
      // tap on a drawer link → let the navigation happen, but close first
      if (t.closest && t.closest('.nav-drawer a')) {
        closeDrawer();
      }
    }
  });
  // Esc closes
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && drawer && drawer.classList.contains('is-open')) {
      closeDrawer();
    }
  });

  // ── Cities dropdown toggle ────────────────────────────────────
  document.querySelectorAll('.cities-nav-toggle').forEach(function (btn) {
    btn.addEventListener('click', function (e) {
      e.preventDefault();
      var wrap = btn.closest('.nav-cities-item');
      if (!wrap) return;
      var open = wrap.classList.toggle('is-open');
      btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
  });
  document.addEventListener('click', function (e) {
    document.querySelectorAll('.nav-cities-item.is-open').forEach(function (wrap) {
      if (!wrap.contains(e.target)) {
        wrap.classList.remove('is-open');
        var t = wrap.querySelector('.cities-nav-toggle');
        if (t) t.setAttribute('aria-expanded', 'false');
      }
    });
  });
})();
