/*
 * The Mutapa Times - People
 * Fetches Zimbabwean business profiles from Wikidata SPARQL + CMS content.
 * Used by people.html
 */

(function () {
  var GITHUB_REPO = "mutapatimes/mutapatimes";
  var GITHUB_BRANCH = "main";
  var PEOPLE_API = "https://api.github.com/repos/" + GITHUB_REPO + "/contents/content/people?ref=" + GITHUB_BRANCH;
  var PEOPLE_RAW = "https://raw.githubusercontent.com/" + GITHUB_REPO + "/" + GITHUB_BRANCH + "/content/people/";
  var WIKIDATA_ENDPOINT = "https://query.wikidata.org/sparql";
  var CACHE_KEY = "mutapa_people_cache";
  var CACHE_DURATION = 60 * 60 * 1000; // 1 hour

  var WIKIPEDIA_API = 'https://en.wikipedia.org/api/rest_v1/page/summary/';

  // SPARQL query: Zimbabwean business people + Wikipedia sitelink
  var SPARQL_QUERY = [
    'SELECT ?person ?personLabel ?personDescription ?image ?occupationLabel ?birthDate ?article WHERE {',
    '  ?person wdt:P31 wd:Q5.',
    '  ?person wdt:P27 wd:Q954.',
    '  ?person wdt:P106 ?occupation.',
    '  VALUES ?occType { wd:Q43845 wd:Q131524 wd:Q484876 wd:Q806798 }',
    '  ?occupation wdt:P279* ?occType.',
    '  OPTIONAL { ?person wdt:P18 ?image. }',
    '  OPTIONAL { ?person wdt:P569 ?birthDate. }',
    '  OPTIONAL { ?article schema:about ?person. ?article schema:isPartOf <https://en.wikipedia.org/>. }',
    '  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }',
    '}'
  ].join('\n');

  // === Helpers (same patterns as articles.js) ===

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
            var people = normalizeWikidata(data.results.bindings);
            // Cache
            try {
              localStorage.setItem(CACHE_KEY, JSON.stringify({
                timestamp: Date.now(),
                data: people
              }));
            } catch (e) { /* quota exceeded */ }
            callback(null, people);
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
      var uri = b.person.value;
      var qid = uri.split('/').pop();
      // Skip entries where the label is just the QID (no English label)
      var label = b.personLabel ? b.personLabel.value : '';
      if (!label || label === qid) continue;

      if (!map[qid]) {
        var wpUrl = b.article ? b.article.value : '';
        var wpTitle = wpUrl ? decodeURIComponent(wpUrl.split('/wiki/').pop()) : '';
        map[qid] = {
          id: qid,
          source: 'wikidata',
          name: label,
          description: b.personDescription ? b.personDescription.value : '',
          image: b.image ? b.image.value : '',
          occupation: b.occupationLabel ? b.occupationLabel.value : '',
          birthDate: b.birthDate ? b.birthDate.value : '',
          wikidataUrl: uri,
          wikipediaTitle: wpTitle,
          wikipediaUrl: wpUrl,
          wikiBio: ''
        };
      } else {
        // Append additional occupation
        var existing = map[qid].occupation;
        var newOcc = b.occupationLabel ? b.occupationLabel.value : '';
        if (newOcc && existing.indexOf(newOcc) === -1) {
          map[qid].occupation += ', ' + newOcc;
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

  // === CMS people fetch ===

  function fetchCmsPeople(callback) {
    fetchJSON(PEOPLE_API, function (err, entries) {
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
      var people = [];
      mdFiles.forEach(function (filename) {
        fetchText(PEOPLE_RAW + filename, function (err2, raw) {
          if (!err2 && raw) {
            var parsed = parseFrontmatter(raw);
            var m = parsed.meta;
            if (m.name) {
              people.push({
                id: 'cms-' + filename.replace(/\.md$/, ''),
                source: 'cms',
                name: m.name,
                title: m.title || '',
                company: m.company || '',
                description: m.bio || '',
                image: m.image || '',
                occupation: m.title || '',
                birthDate: '',
                wikidataId: m.wikidata_id || '',
                wikidataUrl: m.wikidata_id ? 'https://www.wikidata.org/wiki/' + m.wikidata_id : '',
                body: parsed.body
              });
            }
          }
          pending--;
          if (pending === 0) callback(null, people);
        });
      });
    });
  }

  // === Merge ===

  function mergePeople(wikidataPeople, cmsPeople) {
    var merged = wikidataPeople.slice();
    for (var i = 0; i < cmsPeople.length; i++) {
      var cms = cmsPeople[i];
      if (cms.wikidataId) {
        var found = false;
        for (var j = 0; j < merged.length; j++) {
          if (merged[j].id === cms.wikidataId) {
            // CMS overrides, keep Wikidata image if CMS has none
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

  var _allPeople = [];
  var _activeIndex = -1;
  var _activeFilter = 'all';

  function renderGrid(container, people) {
    _allPeople = people;
    if (!people.length) {
      container.innerHTML = '<p class="people-empty">No profiles found.</p>';
      return;
    }
    var html = '<div class="people-card-grid">';
    for (var i = 0; i < people.length; i++) {
      html += renderCard(people[i], i);
    }
    html += '</div>';
    container.innerHTML = html;

    // Attach click handlers
    var cards = container.querySelectorAll('.person-card');
    for (var k = 0; k < cards.length; k++) {
      cards[k].addEventListener('click', handleCardClick);
    }
  }

  function renderCard(person, index) {
    var imgHtml = person.image
      ? '<img src="' + escapeHtml(person.image) + '" alt="' + escapeHtml(person.name) + ', ' + escapeHtml(person.occupation || '') + '" class="person-card-img" loading="lazy">'
      : '<div class="person-card-img person-card-placeholder"><svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round"><circle cx="12" cy="8" r="4"/><path d="M4 20c0-4 4-7 8-7s8 3 8 7"/></svg></div>';
    var sourceTag = person.source === 'cms'
      ? '<span class="press-marker original-press">Original</span>'
      : '';
    var personUrl = 'person.html?id=' + encodeURIComponent(person.id);
    return '<a href="' + personUrl + '" class="person-card" data-index="' + index + '" aria-expanded="false">'
      + imgHtml
      + '<div class="person-card-body">'
      + '<h3 class="person-card-name">' + escapeHtml(person.name) + '</h3>'
      + '<p class="person-card-role">' + escapeHtml(person.occupation || person.title || '') + '</p>'
      + (person.company ? '<p class="person-card-company">' + escapeHtml(person.company) + '</p>' : '')
      + sourceTag
      + '</div></a>';
  }

  // === Detail expand ===

  function closeDetail() {
    var detail = document.getElementById('person-detail');
    detail.classList.remove('person-detail-open');
    document.body.style.overflow = '';
    var prev = document.querySelector('.person-card-active');
    if (prev) {
      prev.classList.remove('person-card-active');
      prev.setAttribute('aria-expanded', 'false');
    }
    _activeIndex = -1;
  }

  function handleCardClick(e) {
    e.preventDefault();
    var card = e.currentTarget;
    var index = parseInt(card.getAttribute('data-index'), 10);
    var detail = document.getElementById('person-detail');

    // Toggle closed if clicking same card
    if (_activeIndex === index) {
      closeDetail();
      return;
    }

    // Remove previous active
    var prev = document.querySelector('.person-card-active');
    if (prev) {
      prev.classList.remove('person-card-active');
      prev.setAttribute('aria-expanded', 'false');
    }

    _activeIndex = index;
    card.classList.add('person-card-active');
    card.setAttribute('aria-expanded', 'true');

    renderDetail(detail, _allPeople[index]);
    detail.classList.add('person-detail-open');
    document.body.style.overflow = 'hidden';
  }

  // === Wikipedia bio fetch ===

  function fetchWikipediaBio(person, bioEl) {
    // Already fetched
    if (person.wikiBio) {
      bioEl.textContent = person.wikiBio;
      return;
    }
    // CMS body takes priority
    if (person.body && person.body.trim()) {
      bioEl.textContent = person.body.trim();
      return;
    }
    // No Wikipedia article available
    if (!person.wikipediaTitle) {
      bioEl.textContent = person.description || '';
      return;
    }

    bioEl.innerHTML = '<span class="person-bio-loading">Loading biography&#8230;</span>';

    var url = WIKIPEDIA_API + encodeURIComponent(person.wikipediaTitle);
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
              person.wikiBio = extract;
              bioEl.textContent = extract;
            } else {
              bioEl.textContent = person.description || '';
            }
          } catch (e) {
            bioEl.textContent = person.description || '';
          }
        } else {
          bioEl.textContent = person.description || '';
        }
      }
    };
    xhr.ontimeout = function () {
      bioEl.textContent = person.description || '';
    };
    xhr.send();
  }

  function renderDetail(container, person) {
    var imgHtml = person.image
      ? '<img src="' + escapeHtml(person.image) + '" alt="' + escapeHtml(person.name) + '" class="person-detail-img">'
      : '';
    var links = '';
    if (person.wikipediaUrl) {
      links += '<a href="' + escapeHtml(person.wikipediaUrl) + '" target="_blank" rel="noopener" class="person-detail-link">Wikipedia &rarr;</a>';
    }
    if (person.wikidataUrl) {
      links += (links ? ' &middot; ' : '') + '<a href="' + escapeHtml(person.wikidataUrl) + '" target="_blank" rel="noopener" class="person-detail-link">Wikidata &rarr;</a>';
    }
    var birthStr = '';
    if (person.birthDate) {
      var bd = new Date(person.birthDate);
      if (!isNaN(bd.getTime())) {
        var months = ["January","February","March","April","May","June",
                      "July","August","September","October","November","December"];
        birthStr = '<p class="person-detail-birth">Born: ' + months[bd.getMonth()] + ' ' + bd.getDate() + ', ' + bd.getFullYear() + '</p>';
      }
    }

    var profileUrl = 'person.html?id=' + encodeURIComponent(person.id);

    container.innerHTML = '<div class="person-detail-backdrop"></div>'
      + '<div class="person-detail-inner">'
      + '<button class="person-detail-close" aria-label="Close detail">&times;</button>'
      + '<div class="person-detail-layout">'
      + (imgHtml ? '<div class="person-detail-img-wrap">' + imgHtml + '</div>' : '')
      + '<div class="person-detail-content">'
      + '<h2 class="person-detail-name">' + escapeHtml(person.name) + '</h2>'
      + '<p class="person-detail-role">' + escapeHtml(person.occupation || '') + '</p>'
      + (person.company ? '<p class="person-detail-company">' + escapeHtml(person.company) + '</p>' : '')
      + birthStr
      + '<p class="person-detail-bio" id="person-bio-text"></p>'
      + (links ? '<p class="person-detail-links">' + links + '</p>' : '')
      + '<a href="' + profileUrl + '" class="person-detail-profile-link">View full profile &rarr;</a>'
      + '</div></div></div>';

    // Lazy-load Wikipedia bio
    var bioEl = container.querySelector('#person-bio-text');
    fetchWikipediaBio(person, bioEl);

    container.querySelector('.person-detail-close').addEventListener('click', closeDetail);
    container.querySelector('.person-detail-backdrop').addEventListener('click', closeDetail);
  }

  // Close modal on Escape key
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && _activeIndex !== -1) closeDetail();
  });

  // === Filters ===

  function buildFilters(people) {
    var filtersEl = document.getElementById('people-filters');
    if (!filtersEl) return;

    // Collect unique occupations and count them
    var occMap = {};
    for (var i = 0; i < people.length; i++) {
      var occs = (people[i].occupation || '').split(',');
      for (var j = 0; j < occs.length; j++) {
        var occ = occs[j].trim().toLowerCase();
        if (!occ) continue;
        // Normalise to title case for display
        var display = occ.charAt(0).toUpperCase() + occ.substring(1);
        if (!occMap[occ]) occMap[occ] = { label: display, count: 0 };
        occMap[occ].count++;
      }
    }

    // Sort by count descending, keep top categories
    var sorted = [];
    for (var key in occMap) {
      if (occMap.hasOwnProperty(key)) sorted.push(occMap[key]);
    }
    sorted.sort(function (a, b) { return b.count - a.count; });
    // Keep roles with 2+ people, max 12 chips
    var chips = sorted.filter(function (o) { return o.count >= 2; }).slice(0, 12);

    var html = '<button class="category-chip active" data-filter="all">All</button>';
    for (var c = 0; c < chips.length; c++) {
      html += '<button class="category-chip" data-filter="' + escapeHtml(chips[c].label.toLowerCase()) + '">'
        + escapeHtml(chips[c].label) + '</button>';
    }
    filtersEl.innerHTML = html;

    // Click handlers
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
    var input = document.getElementById('people-search');
    var query = input ? input.value.toLowerCase().trim() : '';
    var cards = document.querySelectorAll('.person-card');
    for (var i = 0; i < cards.length; i++) {
      var idx = parseInt(cards[i].getAttribute('data-index'), 10);
      var person = _allPeople[idx];
      var searchable = (person.name + ' ' + person.occupation + ' ' +
                       (person.company || '') + ' ' + person.description).toLowerCase();
      var matchesSearch = !query || searchable.indexOf(query) !== -1;
      var matchesFilter = _activeFilter === 'all' ||
        (person.occupation || '').toLowerCase().indexOf(_activeFilter) !== -1;
      cards[i].style.display = (matchesSearch && matchesFilter) ? '' : 'none';
    }
  }

  function setupSearch() {
    var input = document.getElementById('people-search');
    if (!input) return;
    input.addEventListener('input', applyFilters);
  }

  // === Init ===

  function init() {
    var container = document.getElementById('people-grid');
    if (!container) return;

    var wikidataResult = null;
    var cmsResult = null;
    var completed = 0;

    function checkDone() {
      completed++;
      if (completed === 2) {
        var merged = mergePeople(wikidataResult || [], cmsResult || []);
        renderGrid(container, merged);
        buildFilters(merged);
        setupSearch();
      }
    }

    fetchWikidata(function (err, people) {
      wikidataResult = err ? [] : people;
      checkDone();
    });

    fetchCmsPeople(function (err, people) {
      cmsResult = err ? [] : people;
      checkDone();
    });
  }

  init();
})();
