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
    if (window.MTHaptic) window.MTHaptic('light');
  }
  function closeDrawer() {
    if (!drawer) return;
    drawer.classList.remove('is-open');
    if (backdrop) backdrop.classList.remove('is-visible');
    document.documentElement.classList.remove('nav-drawer-locked');
    setHamburgerState(false);
    drawer.setAttribute('aria-hidden', 'true');
    if (window.MTHaptic) window.MTHaptic('light');
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
    'padding-bottom:env(safe-area-inset-bottom,0px);' +
    /* horizontally scrollable: items grow to fill when they fit, and swipe
       when there are more than the screen holds (More sits at the end) */
    'overflow-x:auto;overflow-y:hidden;-webkit-overflow-scrolling:touch;' +
    'touch-action:pan-x;scrollbar-width:none;overscroll-behavior-x:contain;}' +
    '.mt-tabbar::-webkit-scrollbar{display:none;}' +
    '.mt-tabbar>a,.mt-tabbar>button{flex:1 0 auto;min-width:62px;display:flex;flex-direction:column;' +
    'align-items:center;justify-content:center;gap:3px;padding:7px 6px 6px;background:none;border:0;' +
    'cursor:pointer;text-decoration:none;color:#6b6b66;font-family:Inter,system-ui,-apple-system,sans-serif;' +
    'font-size:10px;font-weight:600;letter-spacing:.02em;-webkit-tap-highlight-color:transparent;white-space:nowrap;}' +
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
    property:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 21V5a1 1 0 0 1 1-1h7a1 1 0 0 1 1 1v16"/><path d="M14 21V9h5a1 1 0 0 1 1 1v11"/><path d="M7.5 8h2M7.5 12h2M7.5 16h2"/></svg>',
    jobs:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="7.5" width="18" height="12" rx="2"/><path d="M8.5 7.5V6a2 2 0 0 1 2-2h3a2 2 0 0 1 2 2v1.5"/><path d="M3 12.5h18"/></svg>',
    originals:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3.5l2.5 5.4 5.9.6-4.4 4 1.3 5.8L12 16.9 6.7 19.3 8 13.5 3.6 9.5l5.9-.6z"/></svg>',
    verified:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M8.3 12.3l2.4 2.4 4.9-5.4"/></svg>',
    local:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 21s7-5.5 7-11a7 7 0 1 0-14 0c0 5.5 7 11 7 11z"/><circle cx="12" cy="10" r="2.5"/></svg>',
    business:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="7.5" width="18" height="12" rx="2"/><path d="M8.5 7.5V6a2 2 0 0 1 2-2h3a2 2 0 0 1 2 2v1.5"/></svg>',
    tech:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="6.5" y="6.5" width="11" height="11" rx="2"/><rect x="9.5" y="9.5" width="5" height="5"/><path d="M9.5 3v3M14.5 3v3M9.5 18v3M14.5 18v3M3 9.5h3M3 14.5h3M18 9.5h3M18 14.5h3"/></svg>',
    health:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 13h3l2-5 3 9 2.5-6 1.5 2H20"/></svg>',
    sport:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M12 3v6M12 15v6M3.5 8l5 3M15.5 13l5 3M20.5 8l-5 3M8.5 13l-5 3"/></svg>',
    culture:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><circle cx="8.5" cy="10" r="1"/><circle cx="15.5" cy="10" r="1"/><path d="M8.5 14.5s1.5 1.5 3.5 1.5 3.5-1.5 3.5-1.5"/></svg>',
    environment:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M5 18c0-7 6-12 14-12 0 8-5 14-12 14a5 5 0 0 1-2-2z"/><path d="M9 18c2-4.5 5-7 8-8"/></svg>',
    education:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-4 9 4-9 4z"/><path d="M7 11v4.5c0 1.4 2.4 2.5 5 2.5s5-1.1 5-2.5V11"/><path d="M21 9.5v4.5"/></svg>',
    markets:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="5" y="8" width="3.6" height="7" rx="1"/><rect x="15.4" y="10" width="3.6" height="7" rx="1"/><path d="M6.8 4v4M6.8 15v5M17.2 4v6M17.2 17v3"/></svg>',
    more:'<svg viewBox="0 0 24 24" fill="currentColor"><circle cx="6" cy="12" r="1.5"/><circle cx="12" cy="12" r="1.5"/><circle cx="18" cy="12" r="1.5"/></svg>'
  };
  // Most tabs are news-feed category filters (they set the homepage filter via
  // a #cat=… hash); Originals and Markets are sections; More opens the drawer.
  var TABS = [
    { label:'Originals',   href:'/originals', match:['/originals'], icon:I.originals },
    { label:'Verified',    cat:'_verified',                         icon:I.verified },
    { label:'Local',       cat:'_local',                            icon:I.local },
    { label:'Business',    cat:'Business',                          icon:I.business },
    { label:'Tech',        cat:'Tech',                              icon:I.tech },
    { label:'Health',      cat:'Health',                            icon:I.health },
    { label:'Sport',       cat:'Sport',                             icon:I.sport },
    { label:'Culture',     cat:'Culture',                           icon:I.culture },
    { label:'Environment', cat:'Environment',                       icon:I.environment },
    { label:'Education',   cat:'Education',                          icon:I.education },
    { label:'Markets',     href:'/markets',   match:['/markets'],   icon:I.markets },
    { label:'More',        more:true,                               icon:I.more }
  ];

  var path = location.pathname.replace(/\/index\.html$/, '/').replace(/\.html$/, '');
  var onHome = (path === '/');
  function curCat() {
    var m = (location.hash || '').match(/^#cat=(.+)$/);
    return m ? decodeURIComponent(m[1]) : (onHome ? 'all' : null);
  }
  function isActive(t) {
    if (t.cat) return onHome && curCat() === t.cat;
    if (t.match) {
      for (var i=0;i<t.match.length;i++){ var x=t.match[i];
        if (x==='/') { if (path==='/' && !curCat()) return true; }
        else if (path===x || path.indexOf(x+'/')===0) return true; }
    }
    return false;
  }

  // Apply the category in the URL hash on the homepage by triggering the
  // existing filter chip (config.js owns the actual filtering + render).
  function applyCatFromHash() {
    if (!onHome) return;
    var m = (location.hash || '').match(/^#cat=(.+)$/);
    if (!m) return;
    var cat = decodeURIComponent(m[1]);
    var chip = document.querySelector('.category-chip[data-category="' + cat + '"]');
    if (chip) { chip.click(); var feed = document.querySelector('.category-filter'); if (feed) feed.scrollIntoView({ block: 'start' }); }
  }

  var nav = document.createElement('nav');
  nav.className = 'mt-tabbar'; nav.setAttribute('aria-label','Primary');
  TABS.forEach(function (t) {
    var el = document.createElement(t.more ? 'button' : 'a');
    if (t.more) { el.type = 'button'; }
    else if (t.cat) { el.href = '/#cat=' + encodeURIComponent(t.cat); }
    else { el.href = t.href; }
    if (!t.more && isActive(t)) el.className = 'is-active';
    el.innerHTML = t.icon + '<span>' + t.label + '</span>';
    if (t.more) {
      el.addEventListener('click', function () {
        var d = document.querySelector('[data-open-drawer]');
        if (d) d.click(); else location.href = '/articles';
      });
    } else if (t.cat && onHome) {
      // Already home: filter in place instead of a no-op hash navigation.
      el.addEventListener('click', function (e) {
        e.preventDefault();
        if (location.hash !== '#cat=' + encodeURIComponent(t.cat)) {
          location.hash = 'cat=' + encodeURIComponent(t.cat);
        } else { applyCatFromHash(); }
      });
    }
    nav.appendChild(el);
  });
  document.body.appendChild(nav);
  document.body.classList.add('mt-has-tabbar');

  function refreshActive() {
    var tabs = nav.children, cat = curCat();
    for (var i=0;i<tabs.length;i++) {
      var t = TABS[i], on = false;
      if (t.cat) on = onHome && cat === t.cat;
      else if (t.match) on = isActive(t);
      tabs[i].classList.toggle('is-active', !!on);
    }
    var a = nav.querySelector('.is-active');
    if (a && nav.scrollWidth > nav.clientWidth) { try { a.scrollIntoView({ inline:'center', block:'nearest' }); } catch (e) {} }
  }
  refreshActive();

  if (onHome) {
    window.addEventListener('hashchange', function () { applyCatFromHash(); refreshActive(); });
    // Apply once the feed/chips are ready (config.js binds on ready).
    if (document.readyState === 'complete') applyCatFromHash();
    else window.addEventListener('load', applyCatFromHash);
  }
})();

/* ─── iOS-app experience: pull-to-refresh, haptics, swipeable section nav,
 *     and native-feel polish. Self-contained, injects its own styles, and
 *     runs site-wide (nav.js is loaded everywhere). The Capacitor shell loads
 *     the live site, so this reaches the app instantly with no rebuild. ──── */
(function () {
  'use strict';

  var Cap = window.Capacitor;
  var isNative = !!(Cap && typeof Cap.isNativePlatform === 'function' && Cap.isNativePlatform());
  var isStandalone = (window.matchMedia && window.matchMedia('(display-mode: standalone)').matches) ||
                     window.navigator.standalone === true;
  var appLike = isNative || isStandalone;
  var root = document.documentElement;
  if (isNative) root.classList.add('is-native-app');
  if (appLike) root.classList.add('is-app-like');

  // ── Haptics: Capacitor Haptics plugin when available, else Web Vibration.
  // Guarded so it is a no-op where neither exists (e.g. iOS WKWebView without
  // the plugin) rather than throwing. window.MTHaptic is shared.
  var H = Cap && Cap.Plugins && Cap.Plugins.Haptics;
  function haptic(kind) {
    try {
      if (H) {
        if (kind === 'select' && H.selectionStart) { H.selectionStart(); return; }
        if (H.impact) { H.impact({ style: kind === 'heavy' ? 'HEAVY' : kind === 'medium' ? 'MEDIUM' : 'LIGHT' }); return; }
      }
      if (navigator.vibrate) navigator.vibrate(kind === 'heavy' ? 16 : kind === 'medium' ? 11 : 6);
    } catch (e) {}
  }
  window.MTHaptic = haptic;

  // ── External links open in an in-app browser (Safari View Controller) ──
  // Inside the native app, links to other sites (news sources, FX providers
  // like Wise/Mukuru, affiliate links, etc.) open in an in-app browser with a
  // Done button instead of throwing the user out to Safari. Same-site links
  // navigate normally in the web view. Capture phase so we beat site handlers.
  if (isNative) {
    // Resolve the Browser plugin LAZILY at click time, not once at load:
    // the native plugin proxy can attach to Capacitor.Plugins slightly after
    // this script runs, and capturing it once left it permanently undefined,
    // which dropped every external link to window.open() — i.e. ejected the
    // user out to the system Safari instead of the in-app Safari View.
    function getBrowser() {
      var c = window.Capacitor || Cap;
      return (c && c.Plugins && c.Plugins.Browser) || null;
    }
    document.addEventListener('click', function (e) {
      var a = e.target && e.target.closest && e.target.closest('a[href]');
      if (!a) return;
      var href = a.getAttribute('href') || '';
      if (/^(mailto:|tel:|sms:|javascript:|#)/i.test(href)) return;
      var url;
      try { url = new URL(a.href, location.href); } catch (_) { return; }
      if (url.protocol !== 'http:' && url.protocol !== 'https:') return;
      // Same-site (mutapatimes.com) stays in the app's web view.
      if (url.hostname === location.hostname ||
          url.hostname.indexOf('mutapatimes.com') !== -1) return;
      var Browser = getBrowser();
      if (!Browser || !Browser.open) return; // no in-app browser: let the OS handle it normally
      e.preventDefault();
      haptic('light');
      try { Browser.open({ url: url.href, presentationStyle: 'fullscreen' }); }
      catch (_) { try { window.open(url.href, '_blank'); } catch (e2) { location.href = url.href; } }
    }, true);
  }

  // ── Inject styles (gated; harmless on desktop). ──────────────────────
  var css =
    /* native-feel polish */
    'html.is-app-like,html.is-app-like body{overscroll-behavior-y:none;}' +
    'html.is-native-app{-webkit-tap-highlight-color:transparent;}' +
    /* keep the sticky topbar (menu / logo / Subscribe) clear of the status
       bar and Dynamic Island in the app: pad it down by the safe-area inset */
    'html.is-app-like .topbar{height:calc(56px + env(safe-area-inset-top,0px));' +
    'padding-top:env(safe-area-inset-top,0px);}' +
    'html.is-native-app nav,html.is-native-app .mt-tabbar,html.is-native-app .nav-drawer,' +
    'html.is-native-app .nav-hamburger,html.is-native-app button{-webkit-touch-callout:none;' +
    '-webkit-user-select:none;user-select:none;}' +
    /* tab-bar press feedback */
    '.mt-tabbar>a,.mt-tabbar>button{transition:transform .12s ease,opacity .12s ease;}' +
    '.mt-tabbar>a:active,.mt-tabbar>button:active{transform:scale(.88);opacity:.55;}' +
    /* swipeable section nav on mobile: show every section in a scroll strip */
    '@media(max-width:760px){' +
    '#mainNav{display:flex!important;justify-content:flex-start!important;flex-wrap:nowrap!important;' +
    'overflow-x:auto!important;overflow-y:hidden!important;-webkit-overflow-scrolling:touch;' +
    'touch-action:pan-x;width:100%;max-width:100%;box-sizing:border-box;' +
    'padding-left:12px!important;padding-right:12px!important;overscroll-behavior-x:contain;}' +
    '#mainNav>p,#mainNav>.nav-cities-item{flex:0 0 auto!important;}' +
    '#mainNav p{display:flex!important;padding:0 12px;}' +
    '#mainNav.is-scrollable{-webkit-mask-image:linear-gradient(to right,#000 0,#000 calc(100% - 38px),transparent 100%);' +
    'mask-image:linear-gradient(to right,#000 0,#000 calc(100% - 38px),transparent 100%);}' +
    '#mainNav.is-scrollable.is-scroll-end{-webkit-mask-image:none;mask-image:none;}}' +
    /* declutter: drop the heavy newsletter + mega-footer in the native app
       (the bottom tab bar handles navigation; Subscribe lives in the topbar) */
    'html.is-native-app .essential-subscribe,html.is-native-app .atlantic-foot{display:none!important;}' +
    /* pull to refresh */
    '.mt-ptr{position:fixed;top:0;left:50%;z-index:10000;width:36px;height:36px;' +
    'margin-top:calc(env(safe-area-inset-top,0px) + 8px);display:flex;align-items:center;' +
    'justify-content:center;border-radius:50%;background:rgba(255,255,255,.97);' +
    'box-shadow:0 6px 20px rgba(0,0,0,.18);color:#c41e1e;opacity:0;pointer-events:none;' +
    'transform:translateX(-50%) translateY(0);}' +
    '.mt-ptr.mt-ptr--snap{transition:transform .32s cubic-bezier(.2,.8,.2,1),opacity .32s ease;}' +
    '.mt-ptr svg{width:22px;height:22px;display:block;}' +
    '.mt-ptr circle{fill:none;stroke:currentColor;stroke-width:2.6;stroke-linecap:round;' +
    'stroke-dasharray:54;stroke-dashoffset:15;transform-origin:center;}' +
    '.mt-ptr.is-ready{color:#1a7f44;}' +
    '.mt-ptr.is-spin svg{animation:mtspin .7s linear infinite;}' +
    '@keyframes mtspin{to{transform:rotate(360deg);}}' +
    /* offline fallback (app contexts) so a dropped connection never shows a
       blank web view — a clean branded screen with a Retry button instead */
    '.mt-offline{position:fixed;inset:0;z-index:100000;display:none;align-items:center;' +
    'justify-content:center;padding:24px;padding-top:calc(env(safe-area-inset-top,0px) + 24px);' +
    'background:#fafaf7;color:#1a1a1a;font-family:Inter,system-ui,-apple-system,sans-serif;}' +
    '.mt-offline.is-on{display:flex;}' +
    '.mt-offline-card{max-width:340px;text-align:center;}' +
    '.mt-offline-mark{font-family:"Playfair Display",Georgia,serif;font-weight:900;font-size:1.05rem;margin-bottom:18px;}' +
    '.mt-offline h2{font-family:"Playfair Display",Georgia,serif;font-size:1.5rem;margin:0 0 8px;}' +
    '.mt-offline p{color:#5a5a5a;line-height:1.55;margin:0 0 22px;font-size:.98rem;}' +
    '.mt-offline-retry{font:inherit;font-weight:700;background:#c41e1e;color:#fff;border:0;' +
    'border-radius:99px;padding:.8rem 2.1rem;cursor:pointer;-webkit-tap-highlight-color:transparent;}';
  var st = document.createElement('style'); st.textContent = css; document.head.appendChild(st);

  // ── Swipeable section nav: fade hint + reveal the active item. ───────
  (function () {
    var mn = document.getElementById('mainNav');
    if (!mn) return;
    function sync() {
      var scrollable = (mn.scrollWidth - mn.clientWidth) > 4;
      mn.classList.toggle('is-scrollable', scrollable);
      mn.classList.toggle('is-scroll-end', mn.scrollLeft + mn.clientWidth >= mn.scrollWidth - 4);
    }
    mn.addEventListener('scroll', sync, { passive: true });
    window.addEventListener('resize', sync, { passive: true });
    sync();
    var active = mn.querySelector('a.active');
    if (active && (mn.scrollWidth - mn.clientWidth) > 4) {
      try { active.scrollIntoView({ inline: 'center', block: 'nearest' }); } catch (e) {}
    }
  })();

  // ── Haptic on bottom-tab taps (delegated; tab bar already in the DOM).
  var tabbar = document.querySelector('.mt-tabbar');
  if (tabbar) tabbar.addEventListener('click', function () { haptic('select'); }, { passive: true });

  // ── Pull to refresh (app-like contexts only, to avoid clashing with the
  //    browser's own gesture in a normal mobile tab). ───────────────────
  if (appLike && 'ontouchstart' in window) {
    var ptr = document.createElement('div');
    ptr.className = 'mt-ptr';
    ptr.setAttribute('aria-hidden', 'true');
    ptr.innerHTML = '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/></svg>';
    document.body.appendChild(ptr);
    var svg = ptr.querySelector('svg');

    var startY = 0, startX = 0, pulling = false, raw = 0, busy = false, locked = false;
    var DAMP = 0.5, MAXD = 110, TRIGGER = 62;
    function atTop() { return (window.scrollY || document.documentElement.scrollTop || 0) <= 0; }
    function shown(d) {
      ptr.style.opacity = String(Math.max(0, Math.min(1, d / TRIGGER)));
      ptr.style.transform = 'translateX(-50%) translateY(' + d + 'px)';
      if (svg) svg.style.transform = 'rotate(' + (d * 3.4) + 'deg)';
      ptr.classList.toggle('is-ready', d >= TRIGGER);
    }
    function reset() {
      ptr.classList.add('mt-ptr--snap');
      ptr.style.opacity = '0';
      ptr.style.transform = 'translateX(-50%) translateY(0)';
      ptr.classList.remove('is-ready');
      if (svg) svg.style.transform = '';
    }

    window.addEventListener('touchstart', function (e) {
      if (busy || e.touches.length !== 1 || !atTop()) { pulling = false; return; }
      startY = e.touches[0].clientY; startX = e.touches[0].clientX;
      raw = 0; pulling = true; locked = false;
      ptr.classList.remove('mt-ptr--snap');
    }, { passive: true });

    window.addEventListener('touchmove', function (e) {
      if (!pulling || busy) return;
      raw = e.touches[0].clientY - startY;
      var dx = e.touches[0].clientX - startX;
      // Only act on a clearly VERTICAL pull. A horizontal swipe (e.g. on the
      // scrollable section nav) must pass through untouched. Once we decide a
      // gesture is horizontal, lock out PTR for the rest of the touch.
      if (locked) return;
      if (Math.abs(dx) > Math.abs(raw)) { locked = true; pulling = false; reset(); return; }
      if (raw <= 6 || !atTop()) { if (raw < 0) { pulling = false; reset(); } return; }
      if (e.cancelable) e.preventDefault(); // stop the native bounce fighting us
      shown(Math.min(MAXD, raw * DAMP));
    }, { passive: false });

    window.addEventListener('touchend', function () {
      if (!pulling || busy) { pulling = false; return; }
      pulling = false;
      var d = Math.min(MAXD, raw * DAMP);
      if (d >= TRIGGER) {
        busy = true;
        haptic('medium');
        ptr.classList.add('mt-ptr--snap', 'is-spin');
        if (svg) svg.style.transform = '';
        ptr.style.opacity = '1';
        ptr.style.transform = 'translateX(-50%) translateY(' + Math.round(TRIGGER * 0.92) + 'px)';
        setTimeout(function () { location.reload(); }, 380);
      } else {
        reset();
      }
    }, { passive: true });
  }

  // ── Offline fallback (app contexts) ──────────────────────────────────
  // If the connection drops, show a clean branded screen with a Retry button
  // instead of a blank web view. Auto-dismisses when the network returns.
  if (appLike) {
    var off = document.createElement('div');
    off.className = 'mt-offline';
    off.setAttribute('role', 'alert');
    off.innerHTML =
      '<div class="mt-offline-card">' +
        '<div class="mt-offline-mark">The Mutapa Times</div>' +
        '<h2>You’re offline</h2>' +
        '<p>We can’t reach the newsroom right now. Check your connection and try again.</p>' +
        '<button type="button" class="mt-offline-retry">Retry</button>' +
      '</div>';
    document.body.appendChild(off);
    function showOffline(on) { off.classList.toggle('is-on', on); }
    window.addEventListener('offline', function () { showOffline(true); });
    window.addEventListener('online', function () { showOffline(false); });
    off.querySelector('.mt-offline-retry').addEventListener('click', function () {
      haptic('light');
      if (navigator.onLine) location.reload(); else showOffline(true);
    });
    if (!navigator.onLine) showOffline(true);
  }
})();
