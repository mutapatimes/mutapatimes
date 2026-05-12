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
  var MAX_PER_HIGHLIGHT = 12;       // cap so a single category doesn't run forever
  var MIN_PER_HIGHLIGHT = 3;        // hide groups too thin to be interesting
  var INDEX_URL = "/content/articles/index.json";

  // Highlight order — categories shown left-to-right when present.
  var CATEGORY_ORDER = [
    "Business", "Politics", "Policy", "Tech", "Health", "Crime",
    "Sport", "Culture", "Environment", "Education",
  ];

  // Each highlight gets its own muted brand-extended colour so the rail
  // reads at a glance — category lives inside the circle, no thumbnail.
  // All tones are dark enough that white text reads cleanly.
  var CATEGORY_COLORS = {
    "_latest":     "#C41E1E",  // brand red
    "Business":    "#1A1A1A",  // ink
    "Politics":    "#7A2436",  // deep wine
    "Policy":      "#3D5A4F",  // forest
    "Tech":        "#3B5780",  // slate blue
    "Health":      "#5C7A4E",  // sage darker
    "Crime":       "#3A2424",  // dark brown
    "Sport":       "#A8632B",  // burnt orange
    "Culture":     "#6E4582",  // muted plum
    "Environment": "#3F6A4E",  // forest green
    "Education":   "#4F6299",  // dusty blue
    "More":        "#444",
  };
  function colorFor(key) {
    return CATEGORY_COLORS[key] || "#1A1A1A";
  }

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

    // "Latest" — top across all categories, always first
    hi.push({
      key: "_latest",
      label: "Latest",
      items: fresh.slice(0, MAX_PER_HIGHLIGHT),
    });

    // Category buckets in the order we want them
    CATEGORY_ORDER.forEach(function (cat) {
      var items = byCat[cat];
      if (!items || items.length < MIN_PER_HIGHLIGHT) return;
      hi.push({ key: cat, label: cat, items: items.slice(0, MAX_PER_HIGHLIGHT) });
    });

    // Anything else, alphabetically
    Object.keys(byCat).sort().forEach(function (cat) {
      if (CATEGORY_ORDER.indexOf(cat) !== -1) return;
      var items = byCat[cat];
      if (items.length < MIN_PER_HIGHLIGHT) return;
      hi.push({ key: cat, label: cat, items: items.slice(0, MAX_PER_HIGHLIGHT) });
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
      var thumb = el("button", {
        class: "story-thumb" + (viewed ? " is-viewed" : " is-unviewed"),
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
            style: "background:" + colorFor(h.key),
          }, [
            el("span", { class: "story-chip-label", text: h.label }),
          ]),
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

    // Card — wrap the existing 4:5 PNG in a 9:16 butter frame so the
    // viewer matches IG Story dimensions. Bottom fade overlay makes the
    // title + CTA legible without depending on background luck.
    var card = el("div", { class: "story-card", style: "background:" + colorFor(h.key) }, [
      el("img", { class: "story-card-image", src: snap.card_image, alt: snap.title || "" }),
      el("div", { class: "story-card-fade" }),
    ]);

    // Bottom caption
    var bottom = el("div", { class: "story-bottom" }, [
      el("p", { class: "story-bottom-eyebrow", text: (h.label === "Latest" ? (snap.category || "Story") : h.label) }),
      el("p", { class: "story-bottom-title", text: snap.title || "" }),
      el("a", {
        class: "story-bottom-cta",
        href: "/articles/" + encodeURIComponent(snap.slug),
        text: "Read the full briefing →",
      }),
    ]);

    // Tap zones (don't intercept clicks on top/bottom UI)
    var tapLeft = el("button", { class: "story-tap story-tap--left", type: "button", "aria-label": "Previous", onclick: prev });
    var tapRight = el("button", { class: "story-tap story-tap--right", type: "button", "aria-label": "Next", onclick: next });

    v.overlay.innerHTML = "";
    v.overlay.appendChild(segs);
    v.overlay.appendChild(top);
    v.overlay.appendChild(tapLeft);
    v.overlay.appendChild(tapRight);
    v.overlay.appendChild(card);
    v.overlay.appendChild(bottom);

    // Animate the active progress segment and arm the next-snap timer
    var activeSeg = v.overlay.querySelector(".story-progress-seg.is-active .story-progress-fill");
    if (activeSeg) {
      activeSeg.style.transition = "none";
      activeSeg.style.width = "0%";
      // Force reflow so the transition restarts even when we navigate
      // back-and-forth within the same highlight.
      void activeSeg.offsetWidth;
      activeSeg.style.transition = "width " + SNAP_DURATION_MS + "ms linear";
      activeSeg.style.width = "100%";
    }
    v.startedAt = Date.now();
    v.elapsedBeforePause = 0;
    if (v.timer) clearTimeout(v.timer);
    v.timer = setTimeout(next, SNAP_DURATION_MS);

    // Mark this snap as viewed for the dim-the-ring state.
    markViewed(h.key, snap.slug);

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
    fetchJSON(INDEX_URL).then(function (data) {
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
