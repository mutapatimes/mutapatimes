/*
 * Instagram-Stories-style viewer for The Mutapa Times.
 *
 * Loads only on /articles. Reads content/articles/index.json (which
 * already has a `card_image` field stamped by fetch_news.py), groups
 * entries by category into "highlights", and shows a horizontally
 * scrollable rail above the articles grid. Tapping a highlight opens
 * a fullscreen viewer that plays the cards with auto-advance, progress
 * segments, tap-zones and swipe-down to dismiss — the IG Stories UX.
 *
 * Cards are 1080x1350 PNGs on butter #F5E8C8. Rendered centered on a
 * black background — IG handles non-9:16 content the same way.
 *
 * No external dependencies (no jQuery, no frameworks). Vanilla DOM.
 */
(function () {
  "use strict";

  if (!document.getElementById("stories-rail")) return;

  // Tunables
  var SNAP_DURATION_MS = 5000;     // each card holds for 5s
  var FEATURE_AD_DURATION_MS = 7000; // feature ad lingers a little longer
  var MAX_PER_HIGHLIGHT = 12;       // cap so a single category doesn't run forever
  var MIN_PER_HIGHLIGHT = 3;        // hide groups too thin to be interesting
  var FEATURE_AD_EVERY = 5;         // insert the Feature Story slide after every N cards
  var SUBSCRIBE_AD_EVERY = 8;       // insert a Subscribe slide after every N cards
  var SUBSCRIBE_AD_DURATION_MS = 6000;
  var SHOPIFY_AD_EVERY = 6;         // insert a Shopify slide after every N real cards
  var SHOPIFY_AD_DURATION_MS = 6000;
  var mtUrl = window.mtUrl || function (p) { return p; };
  var INDEX_URL = mtUrl("/content/articles/index.json");
  var FEATURE_AD_URL = mtUrl("/data/feature-story.json");
  // Curated editorial series promoted at the front of the rail. Each
  // becomes a single highlight that plays through every article in the
  // series with the series colour scheme. Order here = order on the rail.
  var SERIES_KEYS = ["venice-biennale-2026"];
  function seriesManifestUrl(key) { return mtUrl("/data/series-" + key + ".json"); }

  // Rotating Shopify sponsored slides. Impact campaign 13624.
  // Image URL format: https://a.impactradius-go.com/display-ad/13624-{id}
  // Click URL format: https://shopify.pxf.io/c/7333540/{id}/13624
  // Impression pixel:  https://imp.pxf.io/i/7333540/{id}/13624
  // Creatives chosen for the full-bleed story slide are the landscape
  // hero formats (look right on the 9:16 viewer once cover-positioned).
  var SHOPIFY_AD_VARIANTS = [
    {
      creativeId: 3797168,
      eyebrow: "Sponsored by Shopify",
      title: "Starting a store is easier than you think.",
      summary: "Build, run and grow a business with the platform behind millions of brands worldwide.",
      ctaText: "Start free trial",
    },
    {
      creativeId: 3323855,
      eyebrow: "Sponsored by Shopify",
      title: "Turn your idea into your business.",
      summary: "From first sale to first hire. Try Shopify for $1 a month for your first three months.",
      ctaText: "Try Shopify for $1",
    },
    {
      creativeId: 3323848,
      eyebrow: "Sponsored by Shopify",
      title: "From daydream to dream job.",
      summary: "Open the door to your own brand. Set up your storefront in minutes, no code needed.",
      ctaText: "Try Shopify for $1",
    },
  ];
  // Walking counter so Shopify creatives rotate evenly across the rail.
  var _shopifyAdIndex = 0;
  // De-duped set of impression pixel URLs already fired in this session.
  var _firedImpressions = {};

  // Rotating subscribe-promo slides. Each uses one of the break-N.jpg
  // hero photos and links to /subscribe. Same full-height layout as
  // the Feature Story slide.
  var SUBSCRIBE_AD_VARIANTS = [
    {
      image: "/img/break-1.jpg",
      eyebrow: "The briefing",
      title: "Get the next story first.",
      summary: "Curated foreign press, market data and original analysis. Twice a week. Free.",
    },
    {
      image: "/img/break-2.jpg",
      eyebrow: "The Mutapa Times",
      title: "Zimbabwe, outside-in.",
      summary: "Join readers in over thirty countries. The diaspora's intelligence newspaper.",
    },
    {
      image: "/img/break-3.jpg",
      eyebrow: "Mondays & Thursdays",
      title: "Essential intelligence for the diaspora.",
      summary: "Two briefings a week, hand-edited from our newsroom. Free forever.",
    },
  ];

  // Pre-loaded Feature Story payload. Filled at init() before
  // highlights are built. Used by injectFeatureAds() to splice an
  // ad slide in after every Nth card in each highlight.
  var _featureAd = null;
  // Walking counter so subscribe variants rotate evenly across the rail.
  var _subscribeAdIndex = 0;
  // Loaded series manifests, keyed by series key. Populated in init().
  var _seriesManifests = {};

  // Ensure URLs that point to an article have the .html extension.
  // GH Pages serves /articles/foo.html, not /articles/foo, so the
  // feature ad anchor was 404'ing without this.
  function withHtml(u) {
    if (!u) return u;
    if (/^https?:\/\//i.test(u)) return u;            // absolute, leave alone
    if (/^mailto:|^tel:/i.test(u)) return u;
    if (/\.[a-z]{2,5}(\?|#|$)/i.test(u)) return u;    // already has extension
    if (/^#/.test(u)) return u;                       // pure fragment
    return u.replace(/\/$/, "") + ".html";
  }

  // Highlight order — categories shown left-to-right when present.
  // Editorial choice: no Crime, no Politics rails.
  var CATEGORY_ORDER = [
    "Business", "Policy", "Tech", "Health",
    "Sport", "Culture", "Environment", "Education",
  ];

  // Two palettes:
  //  • CHIP — faded brand tones for the rail circles (dark ink text)
  //  • VIEWER — saturated tones for the fullscreen story background
  //    (white text reads cleanly against them)
  var CHIP_COLORS = {
    "_latest":     "#E8C9C5",  // faded brand-red (rose-tinted)
    "Business":    "#ECE2CF",  // warm cream
    "Policy":      "#D8E6D5",  // sage green
    "Tech":        "#DDE4ED",  // pale slate
    "Health":      "#E1E8D2",  // pale moss
    "Sport":       "#F0DCC6",  // warm peach
    "Culture":     "#E5DBE8",  // pale lavender
    "Environment": "#D2E2D2",  // pale forest
    "Education":   "#D8E1F0",  // pale sky
    "More":        "#E4E0D8",  // soft taupe
  };
  var VIEWER_COLORS = {
    "_latest":     "#C41E1E",
    "Business":    "#1A1A1A",
    "Policy":      "#3D5A4F",
    "Tech":        "#3B5780",
    "Health":      "#5C7A4E",
    "Sport":       "#A8632B",
    "Culture":     "#6E4582",
    "Environment": "#3F6A4E",
    "Education":   "#4F6299",
    "More":        "#444",
  };
  // Back-compat alias — most call-sites still use colorFor for the rail.
  var CATEGORY_COLORS = CHIP_COLORS;
  function colorFor(key) {
    // Default exported helper — returns the rail chip colour.
    return CHIP_COLORS[key] || "#E4E0D8";
  }
  function viewerColorFor(key) {
    return VIEWER_COLORS[key] || "#1A1A1A";
  }
  // Read a colour off the highlight first (set by buildSeriesHighlight),
  // fall back to the static palette by key. Lets series themes paint
  // the chip + viewer without registering keys in CHIP_COLORS.
  function chipColorFor(h) { return (h && h.chipColor) || colorFor(h && h.key); }
  function viewerColorForH(h) { return (h && h.viewerColor) || viewerColorFor(h && h.key); }

  // ---- DOM helpers ----
  function el(tag, props, children) {
    var node = document.createElement(tag);
    if (props) {
      for (var k in props) {
        if (k === "class") node.className = props[k];
        else if (k === "text") node.textContent = props[k];
        else if (k === "html") node.innerHTML = props[k];
        else if (k.indexOf("on") === 0) node.addEventListener(k.slice(2), props[k]);
        else node.setAttribute(k, props[k]);
      }
    }
    if (children) {
      for (var i = 0; i < children.length; i++) {
        if (children[i]) node.appendChild(children[i]);
      }
    }
    return node;
  }

  function fetchJSON(url) {
    return new Promise(function (resolve, reject) {
      var xhr = new XMLHttpRequest();
      xhr.open("GET", url, true);
      xhr.onreadystatechange = function () {
        if (xhr.readyState !== 4) return;
        if (xhr.status === 200) {
          try { resolve(JSON.parse(xhr.responseText)); }
          catch (e) { reject(e); }
        } else {
          reject(new Error("HTTP " + xhr.status));
        }
      };
      xhr.send();
    });
  }

  // ---- Feature ad injection ----
  // Splice the Feature Story slide into a highlight's items array
  // after every FEATURE_AD_EVERY cards. Skips the highlight where
  // the feature article would naturally appear (so we don't show
  // it back-to-back with itself).
  function injectFeatureAds(items) {
    if (!_featureAd) return items;
    var alreadyInHighlight = items.some(function (it) {
      return it && it.slug === _featureAd.slug;
    });
    if (alreadyInHighlight) return items;
    var out = [];
    for (var i = 0; i < items.length; i++) {
      out.push(items[i]);
      if ((i + 1) % FEATURE_AD_EVERY === 0 && i < items.length - 1) {
        out.push(_featureAd);
      }
    }
    return out;
  }

  // Subscribe promos rotate through SUBSCRIBE_AD_VARIANTS, one slide
  // inserted after every SUBSCRIBE_AD_EVERY real story cards. Runs
  // after injectFeatureAds so the two ad types co-exist without
  // double-counting positions; feature ads are passed through.
  function injectSubscribeAds(items) {
    var out = [];
    var realCardCount = 0;
    for (var i = 0; i < items.length; i++) {
      var it = items[i];
      out.push(it);
      // Don't count ads when computing the every-N-real-cards rhythm.
      if (it && (it._isFeatureAd || it._isSubscribeAd)) continue;
      realCardCount++;
      var isLast = i === items.length - 1;
      if (realCardCount % SUBSCRIBE_AD_EVERY === 0 && !isLast) {
        var v = SUBSCRIBE_AD_VARIANTS[_subscribeAdIndex % SUBSCRIBE_AD_VARIANTS.length];
        _subscribeAdIndex++;
        out.push({
          _isSubscribeAd: true,
          slug: "subscribe-" + _subscribeAdIndex,
          title: v.title,
          summary: v.summary,
          eyebrow: v.eyebrow,
          image: v.image,
          url: "/subscribe.html",
        });
      }
    }
    return out;
  }

  // Shopify sponsored slides rotate through SHOPIFY_AD_VARIANTS, one
  // inserted after every SHOPIFY_AD_EVERY real story cards. Runs after
  // both injectFeatureAds and injectSubscribeAds so it counts only real
  // story cards toward the cadence and won't appear adjacent to itself.
  // It WILL on a long highlight share neighbourhoods with the other two
  // ad types; that's acceptable for a rail capped at 12 + a few promos.
  function injectShopifyAds(items) {
    if (!SHOPIFY_AD_VARIANTS.length) return items;
    var out = [];
    var realCardCount = 0;
    for (var i = 0; i < items.length; i++) {
      var it = items[i];
      out.push(it);
      if (it && (it._isFeatureAd || it._isSubscribeAd || it._isShopifyAd)) continue;
      realCardCount++;
      var isLast = i === items.length - 1;
      if (realCardCount % SHOPIFY_AD_EVERY === 0 && !isLast) {
        var v = SHOPIFY_AD_VARIANTS[_shopifyAdIndex % SHOPIFY_AD_VARIANTS.length];
        _shopifyAdIndex++;
        out.push({
          _isShopifyAd: true,
          slug: "shopify-" + v.creativeId + "-" + _shopifyAdIndex,
          title: v.title,
          summary: v.summary,
          eyebrow: v.eyebrow,
          image: "https://a.impactradius-go.com/display-ad/13624-" + v.creativeId,
          url: "https://shopify.pxf.io/c/7333540/" + v.creativeId + "/13624",
          ctaText: v.ctaText,
          impressionPixel: "https://imp.pxf.io/i/7333540/" + v.creativeId + "/13624",
        });
      }
    }
    return out;
  }

  // Build a single highlight from a loaded series manifest. The series
  // is a curated package, so it sidesteps MIN/MAX caps and feature-ad
  // injection — every article in the manifest, in order, gets its own
  // snap. The chip uses the manifest's rail_chip_image instead of a
  // text label so it stands out on the rail.
  function buildSeriesHighlight(manifest) {
    if (!manifest || !manifest.articles || !manifest.articles.length) return null;
    var ordered = manifest.articles.slice().sort(function (a, b) {
      return (a.order || 0) - (b.order || 0);
    });
    var items = ordered.map(function (a) {
      return {
        slug: a.slug,
        title: a.title || "",
        summary: a.summary || "",
        image: a.image || "",
        // No baked card; the story-card image-fallback chain in
        // renderViewer() will use snap.image or the cream typographic card.
        card_image: "",
        category: manifest.eyebrow || "Scene Report",
        _isSeriesSnap: true,
      };
    });
    return {
      key: "_series_" + manifest.key,
      label: manifest.name ? manifest.name.replace(/^Scene Report:\s*/i, "") : "Scene Report",
      items: items,
      chipImage: manifest.rail_chip_image || manifest.hero_image || "",
      chipColor: manifest.color_bg || "#0c1410",
      viewerColor: manifest.color_bg || "#0c1410",
      isSeries: true,
    };
  }

  // ---- Highlight construction ----
  function buildHighlights(entries) {
    // Keep only entries with a card_image (fresh enough to still be on disk).
    var fresh = entries.filter(function (e) { return e && e.card_image; });
    // Newest first
    fresh.sort(function (a, b) { return (b.date || "").localeCompare(a.date || ""); });

    var byCat = {};
    fresh.forEach(function (e) {
      var c = e.category || "More";
      (byCat[c] = byCat[c] || []).push(e);
    });

    var hi = [];

    // Curated series — promoted at the very front of the rail so the
    // editorial package leads. One highlight per series.
    SERIES_KEYS.forEach(function (key) {
      var sh = buildSeriesHighlight(_seriesManifests[key]);
      if (sh) hi.push(sh);
    });

    // "Latest" — top across all categories, always first
    hi.push({
      key: "_latest",
      label: "Latest",
      items: injectShopifyAds(injectSubscribeAds(injectFeatureAds(fresh.slice(0, MAX_PER_HIGHLIGHT)))),
    });

    // Category buckets in the order we want them
    CATEGORY_ORDER.forEach(function (cat) {
      var items = byCat[cat];
      if (!items || items.length < MIN_PER_HIGHLIGHT) return;
      hi.push({ key: cat, label: cat, items: injectShopifyAds(injectSubscribeAds(injectFeatureAds(items.slice(0, MAX_PER_HIGHLIGHT)))) });
    });

    // Anything else, alphabetically
    Object.keys(byCat).sort().forEach(function (cat) {
      if (CATEGORY_ORDER.indexOf(cat) !== -1) return;
      var items = byCat[cat];
      if (items.length < MIN_PER_HIGHLIGHT) return;
      hi.push({ key: cat, label: cat, items: injectShopifyAds(injectSubscribeAds(injectFeatureAds(items.slice(0, MAX_PER_HIGHLIGHT)))) });
    });

    return hi;
  }

  // ---- Viewed state (localStorage) ----
  var VIEWED_KEY = "mt-stories-viewed";
  function loadViewed() {
    try { return JSON.parse(localStorage.getItem(VIEWED_KEY) || "{}"); }
    catch (e) { return {}; }
  }
  function saveViewed(v) {
    try { localStorage.setItem(VIEWED_KEY, JSON.stringify(v)); } catch (e) {}
  }
  function markViewed(highlightKey, slug) {
    var v = loadViewed();
    var bucket = v[highlightKey] || (v[highlightKey] = {});
    bucket[slug] = 1;
    saveViewed(v);
  }
  function isHighlightFullyViewed(h) {
    var v = loadViewed();
    var bucket = v[h.key] || {};
    for (var i = 0; i < h.items.length; i++) {
      // Ad slides (Feature Story + Subscribe + Shopify) aren't editorial
      // cards; they don't get a viewed tick, otherwise the ring would
      // never dim.
      if (h.items[i] && (h.items[i]._isFeatureAd || h.items[i]._isSubscribeAd || h.items[i]._isShopifyAd)) continue;
      if (!bucket[h.items[i].slug]) return false;
    }
    return true;
  }

  // ---- Rail rendering ----
  function renderRail(rail, highlights) {
    rail.innerHTML = "";
    var inner = el("div", { class: "stories-rail-inner" });
    highlights.forEach(function (h, i) {
      var viewed = isHighlightFullyViewed(h);
      // Series chips render the rail_chip_image as a full-bleed
      // background instead of the standard text-on-colour treatment.
      var chipStyle = "background:" + chipColorFor(h);
      var chipChildren = [el("span", { class: "story-chip-label", text: h.label })];
      if (h.chipImage) {
        chipStyle += ";background-image:url('" + h.chipImage.replace(/'/g, "\\'") +
                     "');background-size:cover;background-position:center;";
        // Replace the label with a wordmark badge that reads cleanly
        // on top of a photo.
        chipChildren = [
          el("span", { class: "story-chip-label story-chip-label--badge", text: h.label }),
        ];
      }
      var thumbCls = "story-thumb" + (viewed ? " is-viewed" : " is-unviewed");
      if (h.isSeries) thumbCls += " story-thumb--series";
      var thumb = el("button", {
        class: thumbCls,
        type: "button",
        "data-highlight": h.key,
        "aria-label": h.label + " — " + h.items.length + " stories" + (viewed ? " (all viewed)" : ""),
        onclick: function () { openViewer(highlights, i, 0); },
      }, [
        // Glow ring — conic gradient, slowly rotates while unviewed.
        // Dims to a flat gray once every snap in this highlight is seen.
        el("span", { class: "story-chip-glow" }, [
          el("span", {
            class: "story-chip",
            style: chipStyle,
          }, chipChildren),
        ]),
      ]);
      inner.appendChild(thumb);
    });
    rail.appendChild(inner);
  }

  // ---- Viewer ----
  var viewerState = null;
  var railEl = null;          // remembered so we can re-render after close
  var allHighlights = null;   // ditto

  function openViewer(highlights, hIndex, sIndex) {
    closeViewer();
    var overlay = el("div", { class: "story-viewer", role: "dialog", "aria-label": "Stories" });
    document.body.appendChild(overlay);
    document.body.classList.add("story-viewer-open");

    viewerState = {
      overlay: overlay,
      highlights: highlights,
      h: hIndex,
      s: sIndex,
      timer: null,
      paused: false,
      startedAt: 0,
      elapsedBeforePause: 0,
    };
    renderViewer();
    bindViewerEvents();
  }

  function closeViewer() {
    if (!viewerState) return;
    if (viewerState.timer) clearTimeout(viewerState.timer);
    if (viewerState.overlay && viewerState.overlay.parentNode) {
      viewerState.overlay.parentNode.removeChild(viewerState.overlay);
    }
    document.body.classList.remove("story-viewer-open");
    viewerState = null;
    document.removeEventListener("keydown", onKeyDown);
    // Strip ?story=... from the URL on close so reload doesn't reopen.
    try {
      var url = new URL(window.location.href);
      if (url.searchParams.has("story") || url.searchParams.has("snap")) {
        url.searchParams.delete("story");
        url.searchParams.delete("snap");
        window.history.replaceState({}, "", url.toString());
      }
    } catch (e) {}
    // Re-render the rail so newly-viewed highlights dim.
    if (railEl && allHighlights) renderRail(railEl, allHighlights);
  }

  function currentHighlight() { return viewerState.highlights[viewerState.h]; }
  function currentSnap() { return currentHighlight().items[viewerState.s]; }

  function renderViewer() {
    var v = viewerState;
    var h = currentHighlight();
    var snap = currentSnap();

    // Progress segments
    var segs = el("div", { class: "story-progress" });
    for (var i = 0; i < h.items.length; i++) {
      var seg = el("div", { class: "story-progress-seg" + (i < v.s ? " is-done" : (i === v.s ? " is-active" : "")) });
      var fill = el("div", { class: "story-progress-fill" });
      seg.appendChild(fill);
      segs.appendChild(seg);
    }

    // Top bar — label + share + close
    var top = el("div", { class: "story-top" }, [
      el("p", { class: "story-top-label", text: h.label }),
      el("div", { class: "story-top-actions" }, [
        el("button", {
          class: "story-share", type: "button", "aria-label": "Share this story",
          html:
            '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
              '<circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/>' +
              '<line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/>' +
            '</svg>',
          onclick: function (ev) { ev.stopPropagation(); shareCurrent(); },
        }),
        el("button", {
          class: "story-close", type: "button", "aria-label": "Close stories",
          html: "&times;",
          onclick: closeViewer,
        }),
      ]),
    ]);

    var isFeatureAd = !!snap._isFeatureAd;
    var isSubscribeAd = !!snap._isSubscribeAd;
    var isShopifyAd = !!snap._isShopifyAd;
    var isAd = isFeatureAd || isSubscribeAd || isShopifyAd;
    var snapDuration = isFeatureAd ? FEATURE_AD_DURATION_MS
                     : isSubscribeAd ? SUBSCRIBE_AD_DURATION_MS
                     : isShopifyAd ? SHOPIFY_AD_DURATION_MS
                     : SNAP_DURATION_MS;

    // Tap zones (don't intercept clicks on top/bottom UI)
    var tapLeft = el("button", { class: "story-tap story-tap--left", type: "button", "aria-label": "Previous", onclick: prev });
    var tapRight = el("button", { class: "story-tap story-tap--right", type: "button", "aria-label": "Next", onclick: next });

    v.overlay.innerHTML = "";
    v.overlay.appendChild(segs);
    v.overlay.appendChild(top);
    v.overlay.appendChild(tapLeft);
    v.overlay.appendChild(tapRight);

    if (isAd) {
      // Full-bleed ad slide. The slide itself is NOT a link — tapping
      // the slide advances to the next snap, exactly like an editorial
      // card. Only the CTA pill navigates to the destination URL.
      // Top bar (close + share) stays visible on ad slides.
      v.overlay.style.background = "#0a0a0a";
      var adHref;
      if (isSubscribeAd) adHref = "/subscribe.html";
      else if (isShopifyAd) adHref = snap.url;
      else adHref = withHtml(snap.url || mtUrl("/articles/" + snap.slug));
      var adWrap = el("div", { class: "story-feature-ad" +
                                       (isShopifyAd ? " story-feature-ad--shopify" : "") });
      var adBg = el("div", { class: "story-feature-ad-bg" });
      if (snap.image) adBg.style.backgroundImage = 'url("' + snap.image + '")';
      var eyebrowText = isShopifyAd
        ? (snap.eyebrow || "Sponsored by Shopify")
        : isSubscribeAd
          ? (snap.eyebrow || "The Mutapa Times")
          : "Feature Story of the Week";
      var ctaText = isShopifyAd
        ? (snap.ctaText || "Visit Shopify") + " →"
        : isSubscribeAd
          ? "Subscribe — it’s free"
          : "Read the full feature";
      // CTA is now its own anchor so clicks on the pill navigate while
      // clicks anywhere else on the slide hit the tap zones beneath.
      var ctaProps = {
        class: "story-feature-ad-cta",
        href: adHref,
        text: ctaText,
        onclick: function (ev) { ev.stopPropagation(); },
      };
      if (isShopifyAd) {
        ctaProps.target = "_blank";
        ctaProps.rel = "noopener sponsored";
      }
      var ctaLink = el("a", ctaProps);
      var adInner = el("div", { class: "story-feature-ad-inner" }, [
        el("p", { class: "story-feature-ad-eyebrow", text: eyebrowText }),
        el("h2", { class: "story-feature-ad-title", text: snap.title || "" }),
        el("p", { class: "story-feature-ad-summary", text: (snap.summary || "").slice(0, 180) }),
        ctaLink,
      ]);
      adWrap.appendChild(adBg);
      adWrap.appendChild(adInner);
      v.overlay.appendChild(adWrap);

      // Fire the Shopify impression pixel once per session per creative.
      if (isShopifyAd && snap.impressionPixel && !_firedImpressions[snap.impressionPixel]) {
        _firedImpressions[snap.impressionPixel] = 1;
        var px = new Image(0, 0);
        px.alt = "";
        px.referrerPolicy = "no-referrer-when-downgrade";
        px.src = snap.impressionPixel;
      }
    } else {
      // Standard snap — title area + butter card + bottom CTA pill.
      var titleArea = el("div", { class: "story-title-area" }, [
        el("p", { class: "story-title-eyebrow", text: (h.label === "Latest" ? (snap.category || "Story") : h.label) }),
        el("p", { class: "story-title-headline", text: snap.title || "" }),
      ]);
      // Card source preference:
      //   1. baked card_image PNG (on-brand 1080x1350 butter card)
      //   2. article hero `image` from frontmatter
      //   3. cream typographic fallback rendered in JS
      // Each level is tried in turn via the img error handler.
      var card;
      function buildCreamFallback() {
        var fallback = el("div", { class: "story-card story-card--fallback" }, [
          el("p", { class: "story-card-fallback-eyebrow", text: snap.category || h.label || "The Mutapa Times" }),
          el("p", { class: "story-card-fallback-headline", text: snap.title || "" }),
          el("p", { class: "story-card-fallback-mark", text: "The Mutapa Times" }),
        ]);
        return fallback;
      }
      if (snap.card_image) {
        card = el("img", { class: "story-card", src: snap.card_image, alt: snap.title || "" });
        card.addEventListener("error", function onPrimaryErr() {
          card.removeEventListener("error", onPrimaryErr);
          if (snap.image) {
            // Try the article hero image, full-bleed framed inside the card area.
            var hero = el("img", { class: "story-card story-card--hero", src: snap.image, alt: snap.title || "" });
            hero.addEventListener("error", function onHeroErr() {
              hero.removeEventListener("error", onHeroErr);
              if (hero.parentNode) hero.parentNode.replaceChild(buildCreamFallback(), hero);
            }, { once: true });
            if (card.parentNode) card.parentNode.replaceChild(hero, card);
            card = hero;
          } else if (card.parentNode) {
            card.parentNode.replaceChild(buildCreamFallback(), card);
          }
        }, { once: true });
      } else if (snap.image) {
        card = el("img", { class: "story-card story-card--hero", src: snap.image, alt: snap.title || "" });
        card.addEventListener("error", function onHeroOnlyErr() {
          card.removeEventListener("error", onHeroOnlyErr);
          if (card.parentNode) card.parentNode.replaceChild(buildCreamFallback(), card);
        }, { once: true });
      } else {
        card = buildCreamFallback();
      }
      var bottom = el("div", { class: "story-bottom" }, [
        el("a", {
          class: "story-bottom-cta",
          href: mtUrl("/articles/" + encodeURIComponent(snap.slug)),
          text: "Read the full briefing →",
        }),
      ]);
      v.overlay.style.background = viewerColorForH(h);
      v.overlay.appendChild(titleArea);
      v.overlay.appendChild(card);
      v.overlay.appendChild(bottom);
    }

    // Animate the active progress segment and arm the next-snap timer.
    var activeSeg = v.overlay.querySelector(".story-progress-seg.is-active .story-progress-fill");
    if (activeSeg) {
      activeSeg.style.transition = "none";
      activeSeg.style.width = "0%";
      void activeSeg.offsetWidth;
      activeSeg.style.transition = "width " + snapDuration + "ms linear";
      activeSeg.style.width = "100%";
    }
    v.startedAt = Date.now();
    v.elapsedBeforePause = 0;
    if (v.timer) clearTimeout(v.timer);
    v.timer = setTimeout(next, snapDuration);

    // Mark this snap as viewed for the dim-the-ring state - but only
    // real snaps. Ads aren't editorial content, they shouldn't move the
    // 'viewed' state of the highlight.
    if (!isAd) markViewed(h.key, snap.slug);

    // Reflect the current snap in the URL so refresh / share works.
    try {
      var url = new URL(window.location.href);
      url.searchParams.set("story", h.key);
      url.searchParams.set("snap", String(v.s));
      window.history.replaceState({}, "", url.toString());
    } catch (e) {}
  }

  // ---- Share ----
  function buildShareUrl() {
    if (!viewerState) return window.location.href;
    var url = new URL(window.location.origin + window.location.pathname);
    url.searchParams.set("story", currentHighlight().key);
    url.searchParams.set("snap", String(viewerState.s));
    return url.toString();
  }

  function showToast(text) {
    if (!viewerState) return;
    var existing = viewerState.overlay.querySelector(".story-toast");
    if (existing) existing.parentNode.removeChild(existing);
    var toast = el("div", { class: "story-toast", role: "status", text: text });
    viewerState.overlay.appendChild(toast);
    // Force reflow then add visible class for the CSS transition
    void toast.offsetWidth;
    toast.classList.add("is-visible");
    setTimeout(function () {
      toast.classList.remove("is-visible");
      setTimeout(function () { if (toast.parentNode) toast.parentNode.removeChild(toast); }, 220);
    }, 1800);
  }

  function shareCurrent() {
    if (!viewerState) return;
    var snap = currentSnap();
    var h = currentHighlight();
    var url = buildShareUrl();
    var shareData = {
      title: (snap.title || h.label) + " — The Mutapa Times",
      text: snap.title || "",
      url: url,
    };
    pause();
    function done() { resume(); }
    if (navigator.share) {
      navigator.share(shareData).then(done).catch(done);
    } else if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(url).then(function () {
        showToast("Link copied — share with a friend");
        done();
      }).catch(done);
    } else {
      // Last-resort fallback for old browsers
      window.prompt("Copy this link to share:", url);
      done();
    }
  }

  function next() {
    if (!viewerState) return;
    var v = viewerState;
    if (v.s + 1 < currentHighlight().items.length) {
      v.s++;
      renderViewer();
    } else if (v.h + 1 < v.highlights.length) {
      v.h++;
      v.s = 0;
      renderViewer();
    } else {
      closeViewer();
    }
  }

  function prev() {
    if (!viewerState) return;
    var v = viewerState;
    if (v.s > 0) {
      v.s--;
      renderViewer();
    } else if (v.h > 0) {
      v.h--;
      v.s = 0;
      renderViewer();
    }
  }

  function pause() {
    if (!viewerState || viewerState.paused) return;
    var v = viewerState;
    v.paused = true;
    v.elapsedBeforePause += Date.now() - v.startedAt;
    if (v.timer) clearTimeout(v.timer);
    var activeSeg = v.overlay.querySelector(".story-progress-seg.is-active .story-progress-fill");
    if (activeSeg) {
      var rect = activeSeg.getBoundingClientRect();
      activeSeg.style.transition = "none";
      activeSeg.style.width = rect.width + "px";
    }
  }

  function resume() {
    if (!viewerState || !viewerState.paused) return;
    var v = viewerState;
    v.paused = false;
    var remaining = SNAP_DURATION_MS - v.elapsedBeforePause;
    if (remaining <= 0) { next(); return; }
    var activeSeg = v.overlay.querySelector(".story-progress-seg.is-active .story-progress-fill");
    if (activeSeg) {
      void activeSeg.offsetWidth;
      activeSeg.style.transition = "width " + remaining + "ms linear";
      activeSeg.style.width = "100%";
    }
    v.startedAt = Date.now();
    v.timer = setTimeout(next, remaining);
  }

  // Pause while long-pressing (mousedown/touchstart) anywhere; resume on release.
  function bindViewerEvents() {
    var v = viewerState;
    document.addEventListener("keydown", onKeyDown);

    // Swipe down to dismiss + long-press to pause
    var startY = null;
    var pressTimer = null;
    v.overlay.addEventListener("touchstart", function (e) {
      startY = e.touches[0].clientY;
      pressTimer = setTimeout(pause, 220);
    }, { passive: true });
    v.overlay.addEventListener("touchmove", function (e) {
      if (startY == null) return;
      var dy = e.touches[0].clientY - startY;
      if (dy > 80) { closeViewer(); startY = null; }
    }, { passive: true });
    v.overlay.addEventListener("touchend", function () {
      if (pressTimer) { clearTimeout(pressTimer); pressTimer = null; }
      resume();
      startY = null;
    });
    v.overlay.addEventListener("mousedown", function () {
      pressTimer = setTimeout(pause, 220);
    });
    v.overlay.addEventListener("mouseup", function () {
      if (pressTimer) { clearTimeout(pressTimer); pressTimer = null; }
      resume();
    });
    v.overlay.addEventListener("mouseleave", function () {
      if (pressTimer) { clearTimeout(pressTimer); pressTimer = null; }
      resume();
    });
  }

  function onKeyDown(e) {
    if (!viewerState) return;
    if (e.key === "Escape") closeViewer();
    else if (e.key === "ArrowRight") next();
    else if (e.key === "ArrowLeft") prev();
    else if (e.key === " ") { e.preventDefault(); viewerState.paused ? resume() : pause(); }
  }

  // ---- Boot ----
  function maybeAutoOpen() {
    if (!allHighlights) return;
    try {
      var params = new URLSearchParams(window.location.search);
      var key = params.get("story");
      if (!key) return;
      var hIdx = -1;
      for (var i = 0; i < allHighlights.length; i++) {
        if (allHighlights[i].key === key) { hIdx = i; break; }
      }
      if (hIdx === -1) return;
      var snapParam = parseInt(params.get("snap") || "0", 10);
      var sIdx = isNaN(snapParam) ? 0 : Math.max(0, Math.min(
        snapParam, allHighlights[hIdx].items.length - 1
      ));
      openViewer(allHighlights, hIdx, sIdx);
    } catch (e) {}
  }

  function init() {
    var rail = document.getElementById("stories-rail");
    if (!rail) return;
    // Kick off the Feature Story fetch in parallel with the index
    // load. Highlights are built after both promises settle so the
    // ad insertion has the latest payload.
    var featurePromise = fetchJSON(FEATURE_AD_URL)
      .then(function (data) {
        if (data && data.slug) {
          _featureAd = {
            _isFeatureAd: true,
            slug: data.slug,
            title: data.title || "",
            summary: data.summary || "",
            image: data.image || "",
            category: data.category || "",
            url: data.url || mtUrl("/articles/" + data.slug),
          };
        }
      })
      .catch(function () { /* no feature, no ads - silent no-op */ });
    // Curated series manifests — each becomes a single highlight at
    // the front of the rail. Failures are silent (skipped).
    var seriesPromises = SERIES_KEYS.map(function (key) {
      return fetchJSON(seriesManifestUrl(key))
        .then(function (m) { if (m) _seriesManifests[key] = m; })
        .catch(function () { /* no manifest -> highlight skipped */ });
    });
    Promise.all([featurePromise].concat(seriesPromises).concat([fetchJSON(INDEX_URL)])).then(function (results) {
      var data = results[results.length - 1];
      if (!Array.isArray(data) || !data.length) return;
      var hi = buildHighlights(data);
      if (!hi.length) { rail.style.display = "none"; return; }
      railEl = rail;
      allHighlights = hi;
      renderRail(rail, hi);
      maybeAutoOpen();
    }).catch(function () { rail.style.display = "none"; });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
