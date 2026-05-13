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

  // ── Sticky topbar reveal — show once user scrolls past masthead ──
  (function () {
    var threshold = 220;   // px scrolled before the topbar slides in
    var raf = null;
    function onScroll() {
      if (raf) return;
      raf = requestAnimationFrame(function () {
        raf = null;
        var y = window.scrollY || document.documentElement.scrollTop || 0;
        document.body.classList.toggle('is-scrolled', y > threshold);
      });
    }
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();  // initialise on load (handles refreshes mid-page)
  })();
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
