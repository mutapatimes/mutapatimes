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

  // ── Advertising contact form → formatted mailto handoff ──────
  // Builds a readable plain-text email body from the form fields
  // and hands off to the user's default email client. No third-
  // party form service required.
  (function () {
    var form = document.getElementById('advertForm');
    if (!form) return;
    var status = document.getElementById('advertFormStatus');
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var data = new FormData(form);
      var lines = [];
      data.forEach(function (val, key) {
        var clean = String(val || '').trim();
        if (!clean) return;
        lines.push(key + ':');
        lines.push(clean);
        lines.push('');
      });
      var body = "Advertising enquiry — The Mutapa Times\n\n" + lines.join('\n');
      var subject = 'Advertising enquiry · ' + (data.get('Company') || 'Mutapa Times');
      var href = 'mailto:news@mutapatimes.com'
               + '?subject=' + encodeURIComponent(subject)
               + '&body=' + encodeURIComponent(body);
      window.location.href = href;
      if (status) {
        status.textContent =
          'Opening your email app… if nothing happens, copy your details to news@mutapatimes.com.';
        status.classList.add('is-success');
      }
    });
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

/* ─── iOS-style bottom tab bar (mobile web + Capacitor app) ───────────────
 * Self-contained: injects its own styles + markup. Shows on narrow screens
 * only (the desktop top nav stays). Loaded site-wide because nav.js is. */
(function () {
  if (window.matchMedia && !window.matchMedia('(max-width: 820px)')) {} // noop guard
  if (document.querySelector('.mt-tabbar')) return;

  var css =
    '.mt-tabbar{position:fixed;left:0;right:0;bottom:0;z-index:9990;display:none;' +
    'background:rgba(255,255,255,.94);-webkit-backdrop-filter:saturate(180%) blur(14px);' +
    'backdrop-filter:saturate(180%) blur(14px);border-top:1px solid #e4e2db;' +
    'padding-bottom:env(safe-area-inset-bottom,0px);}' +
    '.mt-tabbar>a,.mt-tabbar>button{flex:1;display:flex;flex-direction:column;align-items:center;' +
    'justify-content:center;gap:3px;padding:7px 2px 6px;background:none;border:0;cursor:pointer;' +
    'text-decoration:none;color:#6b6b66;font-family:Inter,system-ui,-apple-system,sans-serif;' +
    'font-size:10px;font-weight:600;letter-spacing:.02em;-webkit-tap-highlight-color:transparent;}' +
    '.mt-tabbar svg{width:23px;height:23px;display:block;}' +
    '.mt-tabbar span{line-height:1;}' +
    '.mt-tabbar .is-active{color:#c41e1e;}' +
    '@media(max-width:820px){.mt-tabbar{display:flex;}' +
    'body.mt-has-tabbar{padding-bottom:calc(52px + env(safe-area-inset-bottom,0px));}' +
    'body.mt-has-tabbar .cookie-consent{bottom:calc(52px + env(safe-area-inset-bottom,0px));}}';
  var st = document.createElement('style'); st.textContent = css; document.head.appendChild(st);

  var I = {
    news:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 10.5 12 3l9 7.5"/><path d="M5 9.8V20h14V9.8"/></svg>',
    econ:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4v16h16"/><path d="M7.5 15v2.5M12 10v7.5M16.5 6v11.5"/></svg>',
    fx:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 8.5h13l-3.2-3.2"/><path d="M20 15.5H7l3.2 3.2"/></svg>',
    articles:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="5" y="3" width="14" height="18" rx="2"/><path d="M8.5 8h7M8.5 12h7M8.5 16h4"/></svg>',
    more:'<svg viewBox="0 0 24 24" fill="currentColor"><circle cx="6" cy="12" r="1.5"/><circle cx="12" cy="12" r="1.5"/><circle cx="18" cy="12" r="1.5"/></svg>'
  };
  var TABS = [
    { label:'News',     href:'/',         match:['/'],                      icon:I.news },
    { label:'Economy',  href:'/economy',  match:['/economy'],               icon:I.econ },
    { label:'FX',       href:'/fx',       match:['/fx'],                    icon:I.fx },
    { label:'Articles', href:'/articles', match:['/articles','/originals'], icon:I.articles },
    { label:'More',     more:true,                                          icon:I.more }
  ];

  var path = location.pathname.replace(/\/index\.html$/, '/').replace(/\.html$/, '');
  function isActive(m) {
    for (var i=0;i<m.length;i++){ var x=m[i];
      if (x==='/') { if (path==='/') return true; }
      else if (path===x || path.indexOf(x+'/')===0) return true; }
    return false;
  }

  var nav = document.createElement('nav');
  nav.className = 'mt-tabbar'; nav.setAttribute('aria-label','Primary');
  TABS.forEach(function (t) {
    var el = document.createElement(t.more ? 'button' : 'a');
    if (t.more) { el.type='button'; } else { el.href = t.href; if (isActive(t.match)) el.className='is-active'; }
    el.innerHTML = t.icon + '<span>' + t.label + '</span>';
    if (t.more) el.addEventListener('click', function () {
      var d = document.querySelector('[data-open-drawer]');
      if (d) d.click(); else location.href = '/articles';
    });
    nav.appendChild(el);
  });
  document.body.appendChild(nav);
  document.body.classList.add('mt-has-tabbar');
})();
