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

  // SPARQL query: Zimbabwean business people
  var SPARQL_QUERY = [
    'SELECT ?person ?personLabel ?personDescription ?image ?occupationLabel ?birthDate WHERE {',
    '  ?person wdt:P31 wd:Q5.',
    '  ?person wdt:P27 wd:Q954.',
    '  ?person wdt:P106 ?occupation.',
    '  VALUES ?occType { wd:Q43845 wd:Q131524 wd:Q484876 wd:Q806798 }',
    '  ?occupation wdt:P279* ?occType.',
    '  OPTIONAL { ?person wdt:P18 ?image. }',
    '  OPTIONAL { ?person wdt:P569 ?birthDate. }',
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
        map[qid] = {
          id: qid,
          source: 'wikidata',
          name: label,
          description: b.personDescription ? b.personDescription.value : '',
          image: b.image ? b.image.value : '',
          occupation: b.occupationLabel ? b.occupationLabel.value : '',
          birthDate: b.birthDate ? b.birthDate.value : '',
          wikidataUrl: uri
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
      ? '<img src="' + escapeHtml(person.image) + '" alt="' + escapeHtml(person.name) + '" class="person-card-img" loading="lazy">'
      : '<div class="person-card-img person-card-placeholder"><svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round"><circle cx="12" cy="8" r="4"/><path d="M4 20c0-4 4-7 8-7s8 3 8 7"/></svg></div>';
    var sourceTag = person.source === 'cms'
      ? '<span class="press-marker original-press">Original</span>'
      : '';
    return '<button class="person-card" data-index="' + index + '" aria-expanded="false">'
      + imgHtml
      + '<div class="person-card-body">'
      + '<h3 class="person-card-name">' + escapeHtml(person.name) + '</h3>'
      + '<p class="person-card-role">' + escapeHtml(person.occupation || person.title || '') + '</p>'
      + (person.company ? '<p class="person-card-company">' + escapeHtml(person.company) + '</p>' : '')
      + sourceTag
      + '</div></button>';
  }

  // === Detail expand ===

  function handleCardClick(e) {
    var card = e.currentTarget;
    var index = parseInt(card.getAttribute('data-index'), 10);
    var detail = document.getElementById('person-detail');

    // Toggle closed if clicking same card
    if (_activeIndex === index) {
      detail.style.display = 'none';
      card.setAttribute('aria-expanded', 'false');
      card.classList.remove('person-card-active');
      _activeIndex = -1;
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
    detail.style.display = 'block';
    detail.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  function renderDetail(container, person) {
    var imgHtml = person.image
      ? '<img src="' + escapeHtml(person.image) + '" alt="' + escapeHtml(person.name) + '" class="person-detail-img">'
      : '';
    var wikiLink = person.wikidataUrl
      ? '<a href="' + escapeHtml(person.wikidataUrl) + '" target="_blank" rel="noopener" class="person-detail-link">View on Wikidata &rarr;</a>'
      : '';
    var birthStr = '';
    if (person.birthDate) {
      var bd = new Date(person.birthDate);
      if (!isNaN(bd.getTime())) {
        var months = ["January","February","March","April","May","June",
                      "July","August","September","October","November","December"];
        birthStr = '<p class="person-detail-birth">Born: ' + months[bd.getMonth()] + ' ' + bd.getDate() + ', ' + bd.getFullYear() + '</p>';
      }
    }

    container.innerHTML = '<div class="person-detail-inner">'
      + '<button class="person-detail-close" aria-label="Close detail">&times;</button>'
      + '<div class="person-detail-layout">'
      + (imgHtml ? '<div class="person-detail-img-wrap">' + imgHtml + '</div>' : '')
      + '<div class="person-detail-content">'
      + '<h2 class="person-detail-name">' + escapeHtml(person.name) + '</h2>'
      + '<p class="person-detail-role">' + escapeHtml(person.occupation || '') + '</p>'
      + (person.company ? '<p class="person-detail-company">' + escapeHtml(person.company) + '</p>' : '')
      + birthStr
      + '<p class="person-detail-bio">' + escapeHtml(person.description || '') + '</p>'
      + wikiLink
      + '</div></div></div>';

    container.querySelector('.person-detail-close').addEventListener('click', function () {
      container.style.display = 'none';
      var prev = document.querySelector('.person-card-active');
      if (prev) {
        prev.classList.remove('person-card-active');
        prev.setAttribute('aria-expanded', 'false');
      }
      _activeIndex = -1;
    });
  }

  // === Search ===

  function setupSearch() {
    var input = document.getElementById('people-search');
    if (!input) return;
    input.addEventListener('input', function () {
      var query = input.value.toLowerCase().trim();
      var cards = document.querySelectorAll('.person-card');
      for (var i = 0; i < cards.length; i++) {
        var idx = parseInt(cards[i].getAttribute('data-index'), 10);
        var person = _allPeople[idx];
        var searchable = (person.name + ' ' + person.occupation + ' ' +
                         (person.company || '') + ' ' + person.description).toLowerCase();
        cards[i].style.display = searchable.indexOf(query) !== -1 ? '' : 'none';
      }
    });
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
