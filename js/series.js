/*
 * The Mutapa Times — Series carousel + read-next.
 *
 * Drives the "Scene Report" treatment: a curated series of articles
 * promoted across the site as a single editorial package.
 *
 * Looks for two kinds of mount points:
 *
 *   <div class="series-carousel-slot" data-series="venice-biennale-2026"></div>
 *     → injects a horizontal scroll-snap carousel hero.
 *
 *   <div class="series-readnext-slot" data-series="venice-biennale-2026"
 *        data-current-slug="2026-05-14-felix-shumba-…"></div>
 *     → injects an end-of-article strip with the rest of the series
 *       (current article excluded), styled to match the series theme.
 *
 * One manifest per series, fetched from /data/series-<key>.json.
 */
(function () {
  "use strict";

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function articleUrl(slug) {
    return "/articles/" + encodeURIComponent(slug) + ".html";
  }

  // Cache by series key so a page with multiple slots only fetches once.
  var manifestCache = {};
  var manifestPending = {};

  function loadManifest(key, cb) {
    if (manifestCache[key]) { cb(null, manifestCache[key]); return; }
    if (manifestPending[key]) { manifestPending[key].push(cb); return; }
    manifestPending[key] = [cb];
    var xhr = new XMLHttpRequest();
    xhr.open("GET", "/data/series-" + key + ".json", true);
    xhr.onreadystatechange = function () {
      if (xhr.readyState !== 4) return;
      var err = null, data = null;
      if (xhr.status >= 200 && xhr.status < 300) {
        try { data = JSON.parse(xhr.responseText); }
        catch (e) { err = e; }
        if (data) manifestCache[key] = data;
      } else {
        err = new Error("HTTP " + xhr.status);
      }
      var waiters = manifestPending[key];
      manifestPending[key] = null;
      for (var i = 0; i < waiters.length; i++) waiters[i](err, data);
    };
    xhr.send();
  }

  // Build the big carousel hero used on the home page + /articles top.
  function renderCarousel(slot, manifest) {
    var arts = (manifest.articles || []).slice().sort(function (a, b) {
      return (a.order || 0) - (b.order || 0);
    });
    if (!arts.length) return;

    var theme = manifest.theme === "dark" ? "is-dark" : "is-light";
    var bg = manifest.color_bg || "#0c1410";
    var fg = manifest.color_fg || "#fff";
    var accent = manifest.color_accent || "#f4ede0";

    var cards = arts.map(function (a, i) {
      var href = a.url || articleUrl(a.slug);
      var label = a.label ? '<span class="series-card-label">' + esc(a.label) + '</span>' : '';
      var orderText = (a.order || (i + 1)) + " · of " + arts.length;
      return (
        '<a class="series-card" href="' + esc(href) + '"' +
          (a.image ? ' style="--series-card-img: url(\'' + esc(a.image) + '\')"' : '') + '>' +
          '<div class="series-card-imgwrap">' +
            (a.image ? '<img src="' + esc(a.image) + '" alt="" loading="lazy" class="series-card-img">' : '') +
            '<div class="series-card-shade"></div>' +
          '</div>' +
          '<div class="series-card-body">' +
            '<span class="series-card-num">' + esc(orderText) + '</span>' +
            label +
            '<h3 class="series-card-title">' + esc(a.title || "") + '</h3>' +
          '</div>' +
        '</a>'
      );
    }).join("");

    var landing = manifest.landing_url || (arts[0] ? articleUrl(arts[0].slug) : "#");
    var html =
      '<section class="series-carousel ' + theme + '" ' +
        'style="--series-bg: ' + esc(bg) + '; --series-fg: ' + esc(fg) + '; --series-accent: ' + esc(accent) + ';" ' +
        'aria-label="' + esc(manifest.name || "Series") + '">' +
        '<div class="series-carousel-head">' +
          '<div class="series-carousel-headtext">' +
            '<p class="series-carousel-eyebrow">' + esc(manifest.eyebrow || "Scene Report") + '</p>' +
            '<h2 class="series-carousel-title">' + esc(manifest.name || "") + '</h2>' +
            (manifest.tagline ? '<p class="series-carousel-tagline">' + esc(manifest.tagline) + '</p>' : '') +
          '</div>' +
          '<a class="series-carousel-cta" href="' + esc(landing) + '">Enter the series &rarr;</a>' +
        '</div>' +
        '<div class="series-carousel-rail" tabindex="0">' +
          cards +
        '</div>' +
        '<div class="series-carousel-nav" aria-hidden="true">' +
          '<button type="button" class="series-carousel-prev" aria-label="Scroll left">&larr;</button>' +
          '<button type="button" class="series-carousel-next" aria-label="Scroll right">&rarr;</button>' +
          '<div class="series-carousel-dots"></div>' +
        '</div>' +
      '</section>';

    slot.innerHTML = html;
    wireCarouselControls(slot, arts.length);
  }

  function wireCarouselControls(slot, count) {
    var rail = slot.querySelector(".series-carousel-rail");
    var prev = slot.querySelector(".series-carousel-prev");
    var next = slot.querySelector(".series-carousel-next");
    var dotsWrap = slot.querySelector(".series-carousel-dots");
    if (!rail) return;

    function scrollBy(dir) {
      var card = rail.querySelector(".series-card");
      var step = card ? card.getBoundingClientRect().width + 18 : rail.clientWidth * 0.85;
      rail.scrollBy({ left: dir * step, behavior: "smooth" });
    }
    if (prev) prev.addEventListener("click", function () { scrollBy(-1); });
    if (next) next.addEventListener("click", function () { scrollBy(1); });

    // Dots — one per card. Active dot follows scroll position.
    if (dotsWrap) {
      var dotHtml = "";
      for (var i = 0; i < count; i++) {
        dotHtml += '<span class="series-carousel-dot" data-i="' + i + '"></span>';
      }
      dotsWrap.innerHTML = dotHtml;
      var dots = dotsWrap.querySelectorAll(".series-carousel-dot");
      function updateDots() {
        var cards = rail.querySelectorAll(".series-card");
        if (!cards.length) return;
        var railRect = rail.getBoundingClientRect();
        var center = railRect.left + railRect.width / 2;
        var bestI = 0, bestDist = Infinity;
        for (var i = 0; i < cards.length; i++) {
          var r = cards[i].getBoundingClientRect();
          var c = r.left + r.width / 2;
          var d = Math.abs(c - center);
          if (d < bestDist) { bestDist = d; bestI = i; }
        }
        for (var j = 0; j < dots.length; j++) {
          dots[j].classList.toggle("is-active", j === bestI);
        }
      }
      rail.addEventListener("scroll", function () {
        window.requestAnimationFrame(updateDots);
      });
      window.addEventListener("resize", updateDots);
      updateDots();
      for (var k = 0; k < dots.length; k++) {
        (function (idx) {
          dots[idx].addEventListener("click", function () {
            var cards = rail.querySelectorAll(".series-card");
            if (!cards[idx]) return;
            cards[idx].scrollIntoView({ behavior: "smooth", inline: "center", block: "nearest" });
          });
        })(k);
      }
    }
  }

  // End-of-article horizontal read-next strip. Excludes the current slug.
  function renderReadNext(slot, manifest) {
    var currentSlug = slot.getAttribute("data-current-slug") || "";
    var arts = (manifest.articles || [])
      .slice()
      .sort(function (a, b) { return (a.order || 0) - (b.order || 0); });

    // Find current index so we can lead with "Next in the series" and
    // also offer a back-to-the-anchor link if relevant.
    var curIdx = -1;
    for (var i = 0; i < arts.length; i++) {
      if (arts[i].slug === currentSlug) { curIdx = i; break; }
    }
    var nextIdx = curIdx >= 0 && curIdx < arts.length - 1 ? curIdx + 1 : -1;
    var nextArt = nextIdx >= 0 ? arts[nextIdx] : null;

    // Build cards (current excluded). Mark the "next" one for emphasis.
    var cards = arts
      .filter(function (a) { return a.slug !== currentSlug; })
      .map(function (a) {
        var href = a.url || articleUrl(a.slug);
        var isNext = nextArt && a.slug === nextArt.slug;
        return (
          '<a class="series-readnext-card' + (isNext ? ' is-next' : '') + '" href="' + esc(href) + '">' +
            (a.image ? '<div class="series-readnext-imgwrap"><img src="' + esc(a.image) + '" alt="" loading="lazy"></div>' : '') +
            '<div class="series-readnext-body">' +
              (isNext ? '<span class="series-readnext-flag">Next in the series</span>' : '') +
              '<span class="series-readnext-order">' + (a.order || "") + ' · of ' + arts.length + '</span>' +
              '<h3 class="series-readnext-title">' + esc(a.title || "") + '</h3>' +
            '</div>' +
          '</a>'
        );
      }).join("");

    var bg = manifest.color_bg || "#0c1410";
    var fg = manifest.color_fg || "#fff";
    var accent = manifest.color_accent || "#f4ede0";

    slot.innerHTML =
      '<aside class="series-readnext" ' +
        'style="--series-bg: ' + esc(bg) + '; --series-fg: ' + esc(fg) + '; --series-accent: ' + esc(accent) + ';" ' +
        'aria-label="More from ' + esc(manifest.name || "this series") + '">' +
        '<div class="series-readnext-head">' +
          '<p class="series-readnext-eyebrow">' + esc(manifest.eyebrow || "Scene Report") + '</p>' +
          '<h2 class="series-readnext-heading">' + esc(manifest.name || "") + '</h2>' +
          (manifest.tagline ? '<p class="series-readnext-tagline">' + esc(manifest.tagline) + '</p>' : '') +
        '</div>' +
        '<div class="series-readnext-rail">' + cards + '</div>' +
      '</aside>';
  }

  function init() {
    var slots = document.querySelectorAll(
      ".series-carousel-slot[data-series], .series-readnext-slot[data-series]"
    );
    if (!slots.length) return;

    // Group slots by series key so we batch fetches.
    var bySeries = {};
    slots.forEach(function (slot) {
      var key = slot.getAttribute("data-series");
      if (!key) return;
      (bySeries[key] = bySeries[key] || []).push(slot);
    });

    Object.keys(bySeries).forEach(function (key) {
      loadManifest(key, function (err, manifest) {
        if (err || !manifest) return;
        bySeries[key].forEach(function (slot) {
          if (slot.classList.contains("series-carousel-slot")) {
            renderCarousel(slot, manifest);
          } else {
            renderReadNext(slot, manifest);
          }
        });
      });
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
