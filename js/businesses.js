/*
 * The Mutapa Times - Businesses
 * Fetches Zimbabwean business/company profiles from Wikidata SPARQL + CMS content.
 * Used by businesses.html
 */

(function () {
  var GITHUB_REPO = "mutapatimes/mutapatimes";
  var GITHUB_BRANCH = "main";
  var BIZ_API = "https://api.github.com/repos/" + GITHUB_REPO + "/contents/content/businesses?ref=" + GITHUB_BRANCH;
  var BIZ_RAW = "https://raw.githubusercontent.com/" + GITHUB_REPO + "/" + GITHUB_BRANCH + "/content/businesses/";
  var WIKIDATA_ENDPOINT = "https://query.wikidata.org/sparql";
  var CACHE_KEY = "mutapa_businesses_cache";
  var CACHE_DURATION = 60 * 60 * 1000; // 1 hour

  var WIKIPEDIA_API = 'https://en.wikipedia.org/api/rest_v1/page/summary/';

  // SPARQL query: Zimbabwean businesses / companies
  var SPARQL_QUERY = [
    'SELECT ?org ?orgLabel ?orgDescription ?image ?industryLabel ?inception ?article ?hqLabel WHERE {',
    '  ?org wdt:P17 wd:Q954.',
    '  ?org wdt:P31/wdt:P279* wd:Q4830453.',
    '  OPTIONAL { ?org wdt:P18 ?image. }',
    '  OPTIONAL { ?org wdt:P452 ?industry. }',
    '  OPTIONAL { ?org wdt:P571 ?inception. }',
    '  OPTIONAL { ?org wdt:P159 ?hq. }',
    '  OPTIONAL { ?article schema:about ?org. ?article schema:isPartOf <https://en.wikipedia.org/>. }',
    '  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }',
    '}'
  ].join('\n');

  // === Helpers ===

  function fetchJSON(url, callback) {
    var xhr = new XMLHttpRequest();
    xhr.open("GET", url, true);
    xhr.onreadystatechange = function () {
      if (xhr.readyState === 4) {
        if (xhr.status === 200) {
          try { callback(null, JSON.parse(xhr.responseText)); }
          catch (e) { callback(e, null); }
        } else {
          callback(new Error("HTTP " + xhr.status), null);
        }
      }
    };
    xhr.send();
  }

  function fetchText(url, callback) {
    var xhr = new XMLHttpRequest();
    xhr.open("GET", url, true);
    xhr.onreadystatechange = function () {
      if (xhr.readyState === 4) {
        if (xhr.status === 200) {
          callback(null, xhr.responseText);
        } else {
          callback(new Error("HTTP " + xhr.status), null);
        }
      }
    };
    xhr.send();
  }

  function escapeHtml(str) {
    var div = document.createElement("div");
    div.appendChild(document.createTextNode(str));
    return div.innerHTML;
  }

  function parseFrontmatter(raw) {
    var match = raw.match(/^---\s*\n([\s\S]*?)\n---\s*\n([\s\S]*)$/);
    if (!match) return { meta: {}, body: raw };
    var meta = {};
    var lines = match[1].split("\n");
    for (var i = 0; i < lines.length; i++) {
      var colon = lines[i].indexOf(":");
      if (colon === -1) continue;
      var key = lines[i].substring(0, colon).trim();
      var val = lines[i].substring(colon + 1).trim();
      if ((val.charAt(0) === '"' && val.charAt(val.length - 1) === '"') ||
          (val.charAt(0) === "'" && val.charAt(val.length - 1) === "'")) {
        val = val.substring(1, val.length - 1);
      }
      meta[key] = val;
    }
    return { meta: meta, body: match[2] };
  }

  // === Wikidata fetch ===

  function fetchWikidata(callback) {
    // Check localStorage cache
    try {
      var cached = localStorage.getItem(CACHE_KEY);
      if (cached) {
        var parsed = JSON.parse(cached);
        if (Date.now() - parsed.timestamp < CACHE_DURATION) {
          callback(null, parsed.data);
          return;
        }
      }
    } catch (e) { /* ignore */ }

    var url = WIKIDATA_ENDPOINT + '?query=' + encodeURIComponent(SPARQL_QUERY) + '&format=json';
    var xhr = new XMLHttpRequest();
    xhr.open('GET', url, true);
    xhr.setRequestHeader('Accept', 'application/sparql-results+json');
    xhr.timeout = 15000;
    xhr.onreadystatechange = function () {
      if (xhr.readyState === 4) {
        if (xhr.status === 200) {
          try {
            var data = JSON.parse(xhr.responseText);
            var businesses = normalizeWikidata(data.results.bindings);
            // Cache
            try {
              localStorage.setItem(CACHE_KEY, JSON.stringify({
                timestamp: Date.now(),
                data: businesses
              }));
            } catch (e) { /* quota exceeded */ }
            callback(null, businesses);
          } catch (e) { callback(e, null); }
        } else {
          callback(new Error('Wikidata HTTP ' + xhr.status), null);
        }
      }
    };
    xhr.ontimeout = function () { callback(new Error('Wikidata timeout'), null); };
    xhr.send();
  }

  function normalizeWikidata(bindings) {
    var map = {};
    for (var i = 0; i < bindings.length; i++) {
      var b = bindings[i];
      var uri = b.org.value;
      var qid = uri.split('/').pop();
      var label = b.orgLabel ? b.orgLabel.value : '';
      if (!label || label === qid) continue;

      if (!map[qid]) {
        var wpUrl = b.article ? b.article.value : '';
        var wpTitle = wpUrl ? decodeURIComponent(wpUrl.split('/wiki/').pop()) : '';
        map[qid] = {
          id: qid,
          source: 'wikidata',
          name: label,
          description: b.orgDescription ? b.orgDescription.value : '',
          image: b.image ? b.image.value : '',
          industry: b.industryLabel ? b.industryLabel.value : '',
          inception: b.inception ? b.inception.value : '',
          headquarters: b.hqLabel ? b.hqLabel.value : '',
          wikidataUrl: uri,
          wikipediaTitle: wpTitle,
          wikipediaUrl: wpUrl,
          wikiBio: ''
        };
      } else {
        // Append additional industry
        var existing = map[qid].industry;
        var newInd = b.industryLabel ? b.industryLabel.value : '';
        if (newInd && existing.indexOf(newInd) === -1) {
          map[qid].industry += ', ' + newInd;
        }
      }
    }
    var result = [];
    for (var key in map) {
      if (map.hasOwnProperty(key)) result.push(map[key]);
    }
    result.sort(function (a, b) { return a.name.localeCompare(b.name); });
    return result;
  }

  // === CMS businesses fetch ===

  function fetchCmsBusinesses(callback) {
    fetchJSON(BIZ_API, function (err, entries) {
      if (err || !entries || !entries.length) {
        callback(null, []);
        return;
      }
      var mdFiles = [];
      for (var i = 0; i < entries.length; i++) {
        if (entries[i].name && /\.md$/.test(entries[i].name)) {
          mdFiles.push(entries[i].name);
        }
      }
      if (!mdFiles.length) { callback(null, []); return; }

      var pending = mdFiles.length;
      var businesses = [];
      mdFiles.forEach(function (filename) {
        fetchText(BIZ_RAW + filename, function (err2, raw) {
          if (!err2 && raw) {
            var parsed = parseFrontmatter(raw);
            var m = parsed.meta;
            if (m.name) {
              businesses.push({
                id: 'cms-' + filename.replace(/\.md$/, ''),
                source: 'cms',
                name: m.name,
                industry: m.industry || '',
                headquarters: m.headquarters || '',
                description: m.bio || '',
                image: m.image || '',
                inception: m.founded || '',
                wikidataId: m.wikidata_id || '',
                wikidataUrl: m.wikidata_id ? 'https://www.wikidata.org/wiki/' + m.wikidata_id : '',
                body: parsed.body
              });
            }
          }
          pending--;
          if (pending === 0) callback(null, businesses);
        });
      });
    });
  }

  // === Merge ===

  function mergeBusinesses(wikidataBiz, cmsBiz) {
    var merged = wikidataBiz.slice();
    for (var i = 0; i < cmsBiz.length; i++) {
      var cms = cmsBiz[i];
      if (cms.wikidataId) {
        var found = false;
        for (var j = 0; j < merged.length; j++) {
          if (merged[j].id === cms.wikidataId) {
            var img = cms.image || merged[j].image;
            var wUrl = merged[j].wikidataUrl;
            for (var k in cms) {
              if (cms.hasOwnProperty(k) && cms[k]) merged[j][k] = cms[k];
            }
            if (!cms.image) merged[j].image = img;
            merged[j].wikidataUrl = wUrl;
            merged[j].source = 'cms';
            found = true;
            break;
          }
        }
        if (!found) merged.push(cms);
      } else {
        merged.push(cms);
      }
    }
    // CMS (editorial) first, then alphabetical
    merged.sort(function (a, b) {
      if (a.source === 'cms' && b.source !== 'cms') return -1;
      if (a.source !== 'cms' && b.source === 'cms') return 1;
      return a.name.localeCompare(b.name);
    });
    return merged;
  }

  // === Render ===

  var _allBusinesses = [];
  var _activeIndex = -1;
  var _activeFilter = 'all';

  function renderGrid(container, businesses) {
    _allBusinesses = businesses;
    if (!businesses.length) {
      container.innerHTML = '<p class="businesses-empty">No businesses found.</p>';
      return;
    }
    var html = '<div class="businesses-card-grid">';
    for (var i = 0; i < businesses.length; i++) {
      html += renderCard(businesses[i], i);
    }
    html += '</div>';
    container.innerHTML = html;

    // Attach click handlers
    var cards = container.querySelectorAll('.business-card');
    for (var k = 0; k < cards.length; k++) {
      cards[k].addEventListener('click', handleCardClick);
    }
  }

  function renderCard(biz, index) {
    var imgHtml = biz.image
      ? '<img src="' + escapeHtml(biz.image) + '" alt="' + escapeHtml(biz.name) + '" class="business-card-img" loading="lazy">'
      : '<div class="business-card-img business-card-placeholder"><svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M9 21V9"/></svg></div>';
    var sourceTag = biz.source === 'cms'
      ? '<span class="press-marker original-press">Original</span>'
      : '';
    var bizUrl = 'business.html?id=' + encodeURIComponent(biz.id);
    return '<a href="' + bizUrl + '" class="business-card" data-index="' + index + '" aria-expanded="false">'
      + imgHtml
      + '<div class="business-card-body">'
      + '<h3 class="business-card-name">' + escapeHtml(biz.name) + '</h3>'
      + '<p class="business-card-industry">' + escapeHtml(biz.industry || '') + '</p>'
      + (biz.headquarters ? '<p class="business-card-hq">' + escapeHtml(biz.headquarters) + '</p>' : '')
      + sourceTag
      + '</div></a>';
  }

  // === Detail modal ===

  function closeDetail() {
    var detail = document.getElementById('business-detail');
    detail.classList.remove('business-detail-open');
    document.body.style.overflow = '';
    var prev = document.querySelector('.business-card-active');
    if (prev) {
      prev.classList.remove('business-card-active');
      prev.setAttribute('aria-expanded', 'false');
    }
    _activeIndex = -1;
  }

  function handleCardClick(e) {
    e.preventDefault();
    var card = e.currentTarget;
    var index = parseInt(card.getAttribute('data-index'), 10);
    var detail = document.getElementById('business-detail');

    if (_activeIndex === index) {
      closeDetail();
      return;
    }

    var prev = document.querySelector('.business-card-active');
    if (prev) {
      prev.classList.remove('business-card-active');
      prev.setAttribute('aria-expanded', 'false');
    }

    _activeIndex = index;
    card.classList.add('business-card-active');
    card.setAttribute('aria-expanded', 'true');

    renderDetail(detail, _allBusinesses[index]);
    detail.classList.add('business-detail-open');
    document.body.style.overflow = 'hidden';
  }

  // === Wikipedia bio fetch ===

  function fetchWikipediaBio(biz, bioEl) {
    if (biz.wikiBio) {
      bioEl.textContent = biz.wikiBio;
      return;
    }
    if (biz.body && biz.body.trim()) {
      bioEl.textContent = biz.body.trim();
      return;
    }
    if (!biz.wikipediaTitle) {
      bioEl.textContent = biz.description || '';
      return;
    }

    bioEl.innerHTML = '<span class="business-bio-loading">Loading description&#8230;</span>';

    var url = WIKIPEDIA_API + encodeURIComponent(biz.wikipediaTitle);
    var xhr = new XMLHttpRequest();
    xhr.open('GET', url, true);
    xhr.timeout = 10000;
    xhr.onreadystatechange = function () {
      if (xhr.readyState === 4) {
        if (xhr.status === 200) {
          try {
            var data = JSON.parse(xhr.responseText);
            var extract = data.extract || '';
            if (extract) {
              biz.wikiBio = extract;
              bioEl.textContent = extract;
            } else {
              bioEl.textContent = biz.description || '';
            }
          } catch (e) {
            bioEl.textContent = biz.description || '';
          }
        } else {
          bioEl.textContent = biz.description || '';
        }
      }
    };
    xhr.ontimeout = function () {
      bioEl.textContent = biz.description || '';
    };
    xhr.send();
  }

  function renderDetail(container, biz) {
    var imgHtml = biz.image
      ? '<img src="' + escapeHtml(biz.image) + '" alt="' + escapeHtml(biz.name) + '" class="business-detail-img">'
      : '';
    var links = '';
    if (biz.wikipediaUrl) {
      links += '<a href="' + escapeHtml(biz.wikipediaUrl) + '" target="_blank" rel="noopener" class="business-detail-link">Wikipedia &rarr;</a>';
    }
    if (biz.wikidataUrl) {
      links += (links ? ' &middot; ' : '') + '<a href="' + escapeHtml(biz.wikidataUrl) + '" target="_blank" rel="noopener" class="business-detail-link">Wikidata &rarr;</a>';
    }
    var foundedStr = '';
    if (biz.inception) {
      var d = new Date(biz.inception);
      if (!isNaN(d.getTime())) {
        foundedStr = '<p class="business-detail-founded">Founded: ' + d.getFullYear() + '</p>';
      }
    }

    var profileUrl = 'business.html?id=' + encodeURIComponent(biz.id);

    container.innerHTML = '<div class="business-detail-backdrop"></div>'
      + '<div class="business-detail-inner">'
      + '<button class="business-detail-close" aria-label="Close detail">&times;</button>'
      + '<div class="business-detail-layout">'
      + (imgHtml ? '<div class="business-detail-img-wrap">' + imgHtml + '</div>' : '')
      + '<div class="business-detail-content">'
      + '<h2 class="business-detail-name">' + escapeHtml(biz.name) + '</h2>'
      + '<p class="business-detail-industry">' + escapeHtml(biz.industry || '') + '</p>'
      + (biz.headquarters ? '<p class="business-detail-hq">' + escapeHtml(biz.headquarters) + '</p>' : '')
      + foundedStr
      + '<p class="business-detail-bio" id="business-bio-text"></p>'
      + (links ? '<p class="business-detail-links">' + links + '</p>' : '')
      + '<a href="' + profileUrl + '" class="business-detail-profile-link">View full profile &rarr;</a>'
      + '</div></div></div>';

    var bioEl = container.querySelector('#business-bio-text');
    fetchWikipediaBio(biz, bioEl);

    container.querySelector('.business-detail-close').addEventListener('click', closeDetail);
    container.querySelector('.business-detail-backdrop').addEventListener('click', closeDetail);
  }

  // Close modal on Escape key
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && _activeIndex !== -1) closeDetail();
  });

  // === Filters ===

  function buildFilters(businesses) {
    var filtersEl = document.getElementById('businesses-filters');
    if (!filtersEl) return;

    var indMap = {};
    for (var i = 0; i < businesses.length; i++) {
      var inds = (businesses[i].industry || '').split(',');
      for (var j = 0; j < inds.length; j++) {
        var ind = inds[j].trim().toLowerCase();
        if (!ind) continue;
        var display = ind.charAt(0).toUpperCase() + ind.substring(1);
        if (!indMap[ind]) indMap[ind] = { label: display, count: 0 };
        indMap[ind].count++;
      }
    }

    var sorted = [];
    for (var key in indMap) {
      if (indMap.hasOwnProperty(key)) sorted.push(indMap[key]);
    }
    sorted.sort(function (a, b) { return b.count - a.count; });
    var chips = sorted.filter(function (o) { return o.count >= 2; }).slice(0, 12);

    var html = '<button class="category-chip active" data-filter="all">All</button>';
    for (var c = 0; c < chips.length; c++) {
      html += '<button class="category-chip" data-filter="' + escapeHtml(chips[c].label.toLowerCase()) + '">'
        + escapeHtml(chips[c].label) + '</button>';
    }
    filtersEl.innerHTML = html;

    var btns = filtersEl.querySelectorAll('.category-chip');
    for (var b = 0; b < btns.length; b++) {
      btns[b].addEventListener('click', function () {
        var prev = filtersEl.querySelector('.category-chip.active');
        if (prev) prev.classList.remove('active');
        this.classList.add('active');
        _activeFilter = this.getAttribute('data-filter');
        applyFilters();
      });
    }
  }

  function applyFilters() {
    var input = document.getElementById('businesses-search');
    var query = input ? input.value.toLowerCase().trim() : '';
    var cards = document.querySelectorAll('.business-card');
    for (var i = 0; i < cards.length; i++) {
      var idx = parseInt(cards[i].getAttribute('data-index'), 10);
      var biz = _allBusinesses[idx];
      var searchable = (biz.name + ' ' + biz.industry + ' ' +
                       (biz.headquarters || '') + ' ' + biz.description).toLowerCase();
      var matchesSearch = !query || searchable.indexOf(query) !== -1;
      var matchesFilter = _activeFilter === 'all' ||
        (biz.industry || '').toLowerCase().indexOf(_activeFilter) !== -1;
      cards[i].style.display = (matchesSearch && matchesFilter) ? '' : 'none';
    }
  }

  function setupSearch() {
    var input = document.getElementById('businesses-search');
    if (!input) return;
    input.addEventListener('input', applyFilters);
  }

  // === Init ===

  function init() {
    var container = document.getElementById('businesses-grid');
    if (!container) return;

    var wikidataResult = null;
    var cmsResult = null;
    var completed = 0;

    function checkDone() {
      completed++;
      if (completed === 2) {
        var merged = mergeBusinesses(wikidataResult || [], cmsResult || []);
        renderGrid(container, merged);
        buildFilters(merged);
        setupSearch();
      }
    }

    fetchWikidata(function (err, businesses) {
      wikidataResult = err ? [] : businesses;
      checkDone();
    });

    fetchCmsBusinesses(function (err, businesses) {
      cmsResult = err ? [] : businesses;
      checkDone();
    });
  }

  init();
})();
