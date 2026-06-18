/*
 * Wordle page retention: fills a scrolling headline ticker at the top and
 * a "More from The Mutapa Times" list below the puzzle, both from the main
 * RSS feed. Goal is simple: once a player lands on the Wordle, give them
 * somewhere on the site to go next. No-ops if the feed can't be reached.
 */
(function () {
  'use strict';
  var mtUrl = window.mtUrl || function (p) { return p; };

  var tickerWrap = document.getElementById('sw-ticker');
  var tickerTrack = document.getElementById('sw-ticker-track');
  var newsWrap = document.getElementById('sw-morenews');
  var newsList = document.getElementById('sw-morenews-list');
  if (!tickerTrack && !newsList) return;

  function esc(s) { var d = document.createElement('div'); d.textContent = s; return d.innerHTML; }

  fetch(mtUrl('/feed.xml'), { cache: 'no-cache' })
    .then(function (r) { return r.text(); })
    .then(function (xml) {
      var doc = new DOMParser().parseFromString(xml, 'application/xml');
      var items = Array.prototype.slice.call(doc.querySelectorAll('item'))
        .map(function (it) {
          var t = it.querySelector('title');
          var l = it.querySelector('link');
          return { title: t ? t.textContent.trim() : '', link: l ? l.textContent.trim() : '' };
        })
        .filter(function (x) { return x.title && x.link; });
      if (!items.length) return;

      // ── Ticker: a duplicated headline strip for a seamless marquee ──
      if (tickerTrack && tickerWrap) {
        var top = items.slice(0, 18);
        var strip = top.map(function (a) {
          return '<a class="sw-ticker-item" href="' + a.link + '">' + esc(a.title) + '</a>';
        }).join('<span class="sw-ticker-sep" aria-hidden="true">&bull;</span>');
        // Duplicate so the CSS translateX(-50%) loops without a visible jump.
        tickerTrack.innerHTML = strip +
          '<span class="sw-ticker-sep" aria-hidden="true">&bull;</span>' + strip;
        tickerWrap.hidden = false;
      }

      // ── More news: a small grid of recent headlines below the puzzle ──
      if (newsList && newsWrap) {
        newsList.innerHTML = items.slice(0, 8).map(function (a) {
          return '<a class="sw-news-card" href="' + a.link + '">' +
            '<span class="sw-news-title">' + esc(a.title) + '</span>' +
            '<span class="sw-news-cta">Read &rarr;</span></a>';
        }).join('');
        newsWrap.hidden = false;
      }
    })
    .catch(function () { /* swallow — never block the game */ });
})();
