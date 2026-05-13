/*
 * City page hydration — runs on /<city>-news pages.
 *
 *  1. Fetch current weather + today's high/low from Open-Meteo
 *     (free, no API key) and paint the header weather card.
 *  2. Re-fetch /content/articles/index.json client-side and refresh
 *     the article list with anything newer than what the static
 *     build embedded — so visitors arriving between fetch-news cron
 *     runs still see fresh headlines.
 *  3. Wire the "Cities" nav dropdown toggle on tap.
 *
 * Vanilla JS only — no framework. Defensive null-checks throughout.
 */
(function () {
  'use strict';

  function el(tag, attrs, children) {
    var n = document.createElement(tag);
    if (attrs) {
      for (var k in attrs) {
        if (k === 'class') n.className = attrs[k];
        else if (k === 'text') n.textContent = attrs[k];
        else n.setAttribute(k, attrs[k]);
      }
    }
    if (children) {
      children.forEach(function (c) { if (c) n.appendChild(c); });
    }
    return n;
  }

  // ── Weather (Open-Meteo, free, no auth) ─────────────────────────
  var WX_CODE = {
    0: ['Clear sky', '☀'],
    1: ['Mainly clear', '🌤'],
    2: ['Partly cloudy', '⛅'],
    3: ['Overcast', '☁'],
    45: ['Fog', '🌫'], 48: ['Fog', '🌫'],
    51: ['Light drizzle', '🌦'], 53: ['Drizzle', '🌦'], 55: ['Heavy drizzle', '🌧'],
    61: ['Light rain', '🌧'], 63: ['Rain', '🌧'], 65: ['Heavy rain', '⛈'],
    71: ['Light snow', '🌨'], 73: ['Snow', '🌨'], 75: ['Heavy snow', '🌨'],
    80: ['Rain showers', '🌧'], 81: ['Heavy rain showers', '⛈'],
    82: ['Violent rain showers', '⛈'],
    95: ['Thunderstorm', '⛈'], 96: ['Storm + hail', '⛈'], 99: ['Storm + hail', '⛈'],
  };

  function paintWeather(data, cityName) {
    var temp = document.getElementById('cityWxTemp');
    var desc = document.getElementById('cityWxDesc');
    var extra = document.getElementById('cityWxExtra');
    if (!temp || !desc) return;
    var cur = data.current || data.current_weather;
    var d = data.daily || {};
    if (!cur) {
      desc.textContent = 'Weather unavailable';
      return;
    }
    var code = cur.weather_code != null ? cur.weather_code : cur.weathercode;
    var info = WX_CODE[code] || ['Conditions', '·'];
    temp.textContent = Math.round(cur.temperature_2m != null ? cur.temperature_2m : cur.temperature) + '°';
    desc.innerHTML = info[1] + ' ' + info[0] + ' in ' + cityName;
    var bits = [];
    if (d.temperature_2m_max && d.temperature_2m_min) {
      bits.push('High ' + Math.round(d.temperature_2m_max[0]) +
                '° · Low ' + Math.round(d.temperature_2m_min[0]) + '°');
    }
    if (d.precipitation_probability_max && d.precipitation_probability_max[0] != null) {
      bits.push(d.precipitation_probability_max[0] + '% chance of rain');
    }
    if (cur.wind_speed_10m != null) {
      bits.push(Math.round(cur.wind_speed_10m) + ' km/h wind');
    }
    extra.textContent = bits.join(' · ');
  }

  function loadWeather() {
    var main = document.querySelector('.city-page');
    if (!main) return;
    var name = main.getAttribute('data-city-name');
    var lat = main.getAttribute('data-city-lat');
    var lon = main.getAttribute('data-city-lon');
    if (!lat || !lon) return;
    var url = 'https://api.open-meteo.com/v1/forecast'
            + '?latitude=' + lat
            + '&longitude=' + lon
            + '&current=temperature_2m,weather_code,wind_speed_10m'
            + '&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max,weather_code'
            + '&timezone=Africa%2FHarare&forecast_days=1';
    fetch(url, { cache: 'no-cache' })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (d) { if (d) paintWeather(d, name); })
      .catch(function () {});
  }

  // ── Article list refresh ────────────────────────────────────────
  function articleMatchesCity(article, slug) {
    var hay = ((article.title || '') + ' ' + (article.summary || '')).toLowerCase();
    var matchers = {
      'harare':         [/\bharare\b/i],
      'bulawayo':       [/\bbulawayo\b/i],
      'mutare':         [/\bmutare\b/i, /\bmanicaland\b/i],
      'gweru':          [/\bgweru\b/i, /\bmidlands\b/i],
      'masvingo':       [/\bmasvingo\b/i, /\bgreat zimbabwe\b/i],
      'victoria-falls': [/\bvictoria falls\b/i, /\bvic[\s-]?falls\b/i, /\bhwange\b/i, /\bmosi[\s-]?oa[\s-]?tunya\b/i, /\bvfex\b/i],
    };
    var rules = matchers[slug] || [];
    for (var i = 0; i < rules.length; i++) {
      if (rules[i].test(hay)) return true;
    }
    return false;
  }

  function renderArticle(a, idx) {
    var card = el('article', { class: 'city-article' + (idx % 2 ? ' city-article--alt' : '') });
    var h3 = el('h3', { class: 'city-article-title' });
    h3.appendChild(el('a', { href: '/articles/' + a.slug + '.html', text: a.title }));
    card.appendChild(h3);
    if (a.summary) {
      card.appendChild(el('p', { class: 'city-article-summary', text: a.summary.slice(0, 240) }));
    }
    var meta = el('p', { class: 'city-article-meta' });
    if (a.category) {
      meta.appendChild(el('span', { class: 'city-article-cat', text: a.category }));
    }
    if (a.date) {
      try {
        var d = new Date(a.date);
        if (!isNaN(d.getTime())) {
          var months = ['January','February','March','April','May','June',
                        'July','August','September','October','November','December'];
          var when = months[d.getMonth()] + ' ' + d.getDate() + ', ' + d.getFullYear();
          var t = el('time', { datetime: a.date, text: when });
          meta.appendChild(t);
        }
      } catch (e) {}
    }
    card.appendChild(meta);
    return card;
  }

  // Cache of all city-filtered articles so the category chips can re-render
  // without re-fetching the JSON on every click.
  var _cityArticlesCache = null;
  var _activeCategory = 'all';

  function renderArticlesList(picks) {
    var container = document.getElementById('cityArticles');
    if (!container) return;
    container.innerHTML = '';
    if (!picks.length) {
      var msg = el('p', { class: 'loading-msg', text: 'No articles match this filter yet.' });
      container.appendChild(msg);
      return;
    }
    picks.forEach(function (a, i) { container.appendChild(renderArticle(a, i)); });
  }

  function applyCategoryFilter() {
    if (!_cityArticlesCache) return;
    var picks = _cityArticlesCache.filter(function (a) {
      if (_activeCategory === 'all') return true;
      return (a.category || '').toLowerCase() === _activeCategory.toLowerCase();
    }).slice(0, 60);
    renderArticlesList(picks);
  }

  function wireChips() {
    var chips = document.querySelectorAll('#cityFilterChips .articles-chip');
    if (!chips.length) return;
    chips.forEach(function (btn) {
      btn.addEventListener('click', function () {
        chips.forEach(function (b) { b.classList.remove('active'); });
        btn.classList.add('active');
        _activeCategory = btn.getAttribute('data-cat') || 'all';
        applyCategoryFilter();
      });
    });
  }

  function refreshArticles() {
    var main = document.querySelector('.city-page');
    var container = document.getElementById('cityArticles');
    if (!main || !container) return;
    var slug = main.getAttribute('data-city-slug');
    fetch('/content/articles/index.json', { cache: 'no-cache' })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (data) {
        if (!Array.isArray(data) || !data.length) return;
        // Newest first
        data.sort(function (a, b) {
          return (b.date || '').localeCompare(a.date || '');
        });
        var picks = [];
        for (var i = 0; i < data.length; i++) {
          var a = data[i];
          if (a && a.slug && articleMatchesCity(a, slug)) picks.push(a);
        }
        if (!picks.length) return;  // keep the static render
        _cityArticlesCache = picks;
        applyCategoryFilter();      // honours whatever chip is active
      })
      .catch(function () {});
  }

  // ── Cities nav dropdown toggle ─────────────────────────────────
  function wireDropdown() {
    var toggles = document.querySelectorAll('.cities-nav-toggle');
    toggles.forEach(function (t) {
      t.addEventListener('click', function (e) {
        e.preventDefault();
        var wrap = t.closest('.nav-cities-item');
        if (!wrap) return;
        var open = wrap.classList.toggle('is-open');
        t.setAttribute('aria-expanded', open ? 'true' : 'false');
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
  }

  function init() {
    loadWeather();
    wireChips();
    refreshArticles();
    wireDropdown();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
