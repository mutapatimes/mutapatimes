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
    var Browser = Cap && Cap.Plugins && Cap.Plugins.Browser;
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
      e.preventDefault();
      haptic('light');
      if (Browser && Browser.open) {
        try { Browser.open({ url: url.href, presentationStyle: 'fullscreen' }); return; } catch (_) {}
      }
      try { window.open(url.href, '_blank'); } catch (_) { location.href = url.href; }
    }, true);
  }

  // ── Inject styles (gated; harmless on desktop). ──────────────────────
  var css =
    /* native-feel polish */
    'html.is-app-like,html.is-app-like body{overscroll-behavior-y:none;}' +
    'html.is-native-app{-webkit-tap-highlight-color:transparent;}' +
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
    '@keyframes mtspin{to{transform:rotate(360deg);}}';
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
})();
