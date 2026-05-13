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
  var hamburger = document.querySelector('.nav-hamburger');
  var drawer = document.getElementById('navDrawer');
  var backdrop = document.querySelector('.nav-drawer-backdrop');

  function openDrawer() {
    if (!drawer) return;
    drawer.classList.add('is-open');
    if (backdrop) backdrop.classList.add('is-visible');
    document.documentElement.classList.add('nav-drawer-locked');
    if (hamburger) hamburger.setAttribute('aria-expanded', 'true');
    drawer.setAttribute('aria-hidden', 'false');
  }
  function closeDrawer() {
    if (!drawer) return;
    drawer.classList.remove('is-open');
    if (backdrop) backdrop.classList.remove('is-visible');
    document.documentElement.classList.remove('nav-drawer-locked');
    if (hamburger) hamburger.setAttribute('aria-expanded', 'false');
    drawer.setAttribute('aria-hidden', 'true');
  }
  function toggleDrawer() {
    if (!drawer) return;
    if (drawer.classList.contains('is-open')) closeDrawer();
    else openDrawer();
  }

  if (hamburger) {
    hamburger.addEventListener('click', function (e) {
      e.preventDefault();
      toggleDrawer();
    });
  }
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
