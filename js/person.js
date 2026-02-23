/*
 * The Mutapa Times - Person Profile
 * Renders a single person profile page with SEO-optimised schema.org markup.
 * Used by person.html?id=Q12345 (Wikidata) or person.html?id=cms-slug (CMS)
 */

(function () {
  var GITHUB_REPO = "mutapatimes/mutapatimes";
  var GITHUB_BRANCH = "main";
  var PEOPLE_API = "https://api.github.com/repos/" + GITHUB_REPO + "/contents/content/people?ref=" + GITHUB_BRANCH;
  var PEOPLE_RAW = "https://raw.githubusercontent.com/" + GITHUB_REPO + "/" + GITHUB_BRANCH + "/content/people/";
  var WIKIDATA_ENDPOINT = "https://query.wikidata.org/sparql";
  var WIKIPEDIA_API = "https://en.wikipedia.org/api/rest_v1/page/summary/";
  var BASE_URL = "https://www.mutapatimes.com";

  function fetchText(url, callback) {
    var xhr = new XMLHttpRequest();
    xhr.open("GET", url, true);
    xhr.onreadystatechange = function () {
      if (xhr.readyState === 4) {
        if (xhr.status === 200) callback(null, xhr.responseText);
        else callback(new Error("HTTP " + xhr.status), null);
      }
    };
    xhr.send();
  }

  function fetchJSON(url, callback) {
    var xhr = new XMLHttpRequest();
    xhr.open("GET", url, true);
    xhr.onreadystatechange = function () {
      if (xhr.readyState === 4) {
        if (xhr.status === 200) {
          try { callback(null, JSON.parse(xhr.responseText)); }
          catch (e) { callback(e, null); }
        } else { callback(new Error("HTTP " + xhr.status), null); }
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

  function formatDate(dateStr) {
    if (!dateStr) return "";
    var d = new Date(dateStr);
    if (isNaN(d.getTime())) return "";
    var months = ["January","February","March","April","May","June",
                  "July","August","September","October","November","December"];
    return months[d.getMonth()] + " " + d.getDate() + ", " + d.getFullYear();
  }

  // Build SPARQL query for a single Wikidata QID
  function sparqlForQid(qid) {
    return [
      'SELECT ?personLabel ?personDescription ?image ?occupationLabel ?birthDate ?article WHERE {',
      '  BIND(wd:' + qid + ' AS ?person)',
      '  ?person wdt:P31 wd:Q5.',
      '  OPTIONAL { ?person wdt:P18 ?image. }',
      '  OPTIONAL { ?person wdt:P106 ?occupation. }',
      '  OPTIONAL { ?person wdt:P569 ?birthDate. }',
      '  OPTIONAL { ?article schema:about ?person. ?article schema:isPartOf <https://en.wikipedia.org/>. }',
      '  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }',
      '}'
    ].join('\n');
  }

  // Fetch a single person from Wikidata
  function fetchWikidataPerson(qid, callback) {
    var url = WIKIDATA_ENDPOINT + '?query=' + encodeURIComponent(sparqlForQid(qid)) + '&format=json';
    var xhr = new XMLHttpRequest();
    xhr.open('GET', url, true);
    xhr.setRequestHeader('Accept', 'application/sparql-results+json');
    xhr.timeout = 15000;
    xhr.onreadystatechange = function () {
      if (xhr.readyState === 4) {
        if (xhr.status === 200) {
          try {
            var data = JSON.parse(xhr.responseText);
            var bindings = data.results.bindings;
            if (!bindings.length) { callback(null, null); return; }

            var occupations = [];
            var person = null;
            for (var i = 0; i < bindings.length; i++) {
              var b = bindings[i];
              if (!person) {
                var wpUrl = b.article ? b.article.value : '';
                var wpTitle = wpUrl ? decodeURIComponent(wpUrl.split('/wiki/').pop()) : '';
                person = {
                  id: qid,
                  source: 'wikidata',
                  name: b.personLabel ? b.personLabel.value : '',
                  description: b.personDescription ? b.personDescription.value : '',
                  image: b.image ? b.image.value : '',
                  occupation: '',
                  birthDate: b.birthDate ? b.birthDate.value : '',
                  wikidataUrl: 'https://www.wikidata.org/wiki/' + qid,
                  wikipediaTitle: wpTitle,
                  wikipediaUrl: wpUrl
                };
              }
              var occ = b.occupationLabel ? b.occupationLabel.value : '';
              if (occ && occupations.indexOf(occ) === -1) occupations.push(occ);
            }
            if (person) person.occupation = occupations.join(', ');
            callback(null, person);
          } catch (e) { callback(e, null); }
        } else { callback(new Error('Wikidata HTTP ' + xhr.status), null); }
      }
    };
    xhr.ontimeout = function () { callback(new Error('Wikidata timeout'), null); };
    xhr.send();
  }

  // Check CMS for an override by wikidata_id
  function fetchCmsOverride(qid, callback) {
    fetchJSON(PEOPLE_API, function (err, entries) {
      if (err || !entries || !entries.length) { callback(null, null); return; }
      var mdFiles = [];
      for (var i = 0; i < entries.length; i++) {
        if (entries[i].name && /\.md$/.test(entries[i].name)) mdFiles.push(entries[i].name);
      }
      if (!mdFiles.length) { callback(null, null); return; }

      var pending = mdFiles.length;
      var found = null;
      mdFiles.forEach(function (filename) {
        fetchText(PEOPLE_RAW + filename, function (err2, raw) {
          if (!err2 && raw && !found) {
            var parsed = parseFrontmatter(raw);
            var m = parsed.meta;
            if (m.wikidata_id === qid || 'cms-' + filename.replace(/\.md$/, '') === qid) {
              found = {
                name: m.name || '',
                title: m.title || '',
                company: m.company || '',
                description: m.bio || '',
                image: m.image || '',
                occupation: m.title || '',
                body: parsed.body
              };
            }
          }
          pending--;
          if (pending === 0) callback(null, found);
        });
      });
    });
  }

  // Fetch CMS-only person (id starts with 'cms-')
  function fetchCmsPerson(slug, callback) {
    var filename = slug.replace(/^cms-/, '') + '.md';
    fetchText(PEOPLE_RAW + filename, function (err, raw) {
      if (err || !raw) { callback(new Error('Not found'), null); return; }
      var parsed = parseFrontmatter(raw);
      var m = parsed.meta;
      callback(null, {
        id: slug,
        source: 'cms',
        name: m.name || '',
        description: m.bio || '',
        image: m.image || '',
        occupation: m.title || '',
        company: m.company || '',
        birthDate: '',
        wikidataUrl: m.wikidata_id ? 'https://www.wikidata.org/wiki/' + m.wikidata_id : '',
        wikipediaTitle: '',
        wikipediaUrl: '',
        body: parsed.body
      });
    });
  }

  // Update page meta tags
  function updateMeta(person) {
    var title = person.name;
    if (person.occupation) title += ' - ' + person.occupation.split(',')[0].trim();
    title += ' | The Mutapa Times';
    document.title = title;

    var desc = person.name;
    if (person.occupation) desc += ' is a ' + person.occupation;
    if (person.description) desc += '. ' + person.description;
    if (desc.length > 160) desc = desc.substring(0, 157) + '...';

    var pageUrl = BASE_URL + '/person.html?id=' + encodeURIComponent(person.id);
    var imgUrl = person.image || BASE_URL + '/img/banner.png';

    // Update canonical
    var canonical = document.querySelector('link[rel="canonical"]');
    if (canonical) canonical.setAttribute('href', pageUrl);

    // Update meta description
    var metaDesc = document.querySelector('meta[name="description"]');
    if (metaDesc) metaDesc.setAttribute('content', desc);

    // Update OG tags
    var ogTags = {
      'og:title': title.replace(' | The Mutapa Times', ''),
      'og:description': desc,
      'og:image': imgUrl,
      'og:url': pageUrl
    };
    for (var prop in ogTags) {
      var el = document.querySelector('meta[property="' + prop + '"]');
      if (el) el.setAttribute('content', ogTags[prop]);
    }

    // Update Twitter tags
    var twTags = {
      'twitter:title': title.replace(' | The Mutapa Times', ''),
      'twitter:description': desc,
      'twitter:image': imgUrl
    };
    for (var name in twTags) {
      var el2 = document.querySelector('meta[name="' + name + '"]');
      if (el2) el2.setAttribute('content', twTags[name]);
    }
  }

  // Inject Person schema.org JSON-LD
  function injectSchema(person) {
    var schema = {
      '@context': 'https://schema.org',
      '@type': 'Person',
      'name': person.name,
      'url': BASE_URL + '/person.html?id=' + encodeURIComponent(person.id),
      'description': person.description || ''
    };

    if (person.image) schema.image = person.image;
    if (person.occupation) schema.jobTitle = person.occupation.split(',')[0].trim();
    if (person.company) {
      schema.worksFor = { '@type': 'Organization', 'name': person.company };
    }
    if (person.birthDate) {
      var bd = new Date(person.birthDate);
      if (!isNaN(bd.getTime())) schema.birthDate = bd.toISOString().split('T')[0];
    }

    var sameAs = [];
    if (person.wikipediaUrl) sameAs.push(person.wikipediaUrl);
    if (person.wikidataUrl) sameAs.push(person.wikidataUrl);
    if (sameAs.length) schema.sameAs = sameAs;

    var script = document.createElement('script');
    script.type = 'application/ld+json';
    script.textContent = JSON.stringify(schema);
    document.head.appendChild(script);

    // Also add BreadcrumbList schema
    var breadcrumb = {
      '@context': 'https://schema.org',
      '@type': 'BreadcrumbList',
      'itemListElement': [
        { '@type': 'ListItem', 'position': 1, 'name': 'Home', 'item': BASE_URL + '/' },
        { '@type': 'ListItem', 'position': 2, 'name': 'People', 'item': BASE_URL + '/people.html' },
        { '@type': 'ListItem', 'position': 3, 'name': person.name, 'item': BASE_URL + '/person.html?id=' + encodeURIComponent(person.id) }
      ]
    };
    var script2 = document.createElement('script');
    script2.type = 'application/ld+json';
    script2.textContent = JSON.stringify(breadcrumb);
    document.head.appendChild(script2);
  }

  // Build share buttons HTML
  function shareButtons(person) {
    var url = encodeURIComponent(BASE_URL + '/person.html?id=' + encodeURIComponent(person.id));
    var text = encodeURIComponent(person.name + ' - Profile on The Mutapa Times');
    return '<div class="person-profile-share">'
      + '<span class="person-profile-share-label">Share</span>'
      + '<div class="share-group">'
      + '<a href="https://twitter.com/intent/tweet?url=' + url + '&text=' + text + '&via=mutapatimes" target="_blank" rel="noopener" class="share-btn" title="Share on X">'
      + '<svg viewBox="0 0 24 24" width="14" height="14"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" fill="currentColor"/></svg>'
      + '</a>'
      + '<a href="https://www.facebook.com/sharer/sharer.php?u=' + url + '" target="_blank" rel="noopener" class="share-btn" title="Share on Facebook">'
      + '<svg viewBox="0 0 24 24" width="14" height="14"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z" fill="currentColor"/></svg>'
      + '</a>'
      + '<a href="https://www.linkedin.com/sharing/share-offsite/?url=' + url + '" target="_blank" rel="noopener" class="share-btn" title="Share on LinkedIn">'
      + '<svg viewBox="0 0 24 24" width="14" height="14"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" fill="currentColor"/></svg>'
      + '</a>'
      + '<a href="https://api.whatsapp.com/send?text=' + text + '%20' + url + '" target="_blank" rel="noopener" class="whatsapp-btn" title="Share on WhatsApp">'
      + '<svg viewBox="0 0 24 24" width="14" height="14"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z" fill="currentColor"/></svg>'
      + '</a>'
      + '</div></div>';
  }

  // Render the full profile page
  function renderProfile(container, person) {
    updateMeta(person);
    injectSchema(person);

    var imgHtml = person.image
      ? '<img src="' + escapeHtml(person.image) + '" alt="' + escapeHtml(person.name) + ', ' + escapeHtml(person.occupation || '') + '" class="person-profile-img">'
      : '';

    var links = '';
    if (person.wikipediaUrl) {
      links += '<a href="' + escapeHtml(person.wikipediaUrl) + '" target="_blank" rel="noopener" class="person-profile-extlink">Wikipedia</a>';
    }
    if (person.wikidataUrl) {
      links += (links ? ' ' : '') + '<a href="' + escapeHtml(person.wikidataUrl) + '" target="_blank" rel="noopener" class="person-profile-extlink">Wikidata</a>';
    }

    var birthStr = '';
    if (person.birthDate) {
      var formatted = formatDate(person.birthDate);
      if (formatted) {
        birthStr = '<p class="person-profile-birth"><strong>Born:</strong> <time datetime="' + new Date(person.birthDate).toISOString().split('T')[0] + '">' + formatted + '</time></p>';
      }
    }

    var html = '<nav class="person-profile-breadcrumb" aria-label="Breadcrumb">'
      + '<a href="index.html">Home</a> <span aria-hidden="true">/</span> '
      + '<a href="people.html">People</a> <span aria-hidden="true">/</span> '
      + '<span>' + escapeHtml(person.name) + '</span>'
      + '</nav>'
      + '<div class="person-profile-header">'
      + (imgHtml ? '<div class="person-profile-img-wrap">' + imgHtml + '</div>' : '')
      + '<div class="person-profile-info">'
      + '<h1 class="person-profile-name">' + escapeHtml(person.name) + '</h1>'
      + '<p class="person-profile-role">' + escapeHtml(person.occupation || '') + '</p>'
      + (person.company ? '<p class="person-profile-company">' + escapeHtml(person.company) + '</p>' : '')
      + birthStr
      + (links ? '<div class="person-profile-extlinks">' + links + '</div>' : '')
      + shareButtons(person)
      + '</div></div>'
      + '<div class="person-profile-bio" id="person-profile-bio"></div>'
      + '<div class="person-profile-back"><a href="people.html">&larr; All people</a></div>';

    container.innerHTML = html;

    // Load bio
    var bioEl = document.getElementById('person-profile-bio');
    if (person.body && person.body.trim()) {
      bioEl.innerHTML = '<p>' + escapeHtml(person.body.trim()).replace(/\n\n/g, '</p><p>').replace(/\n/g, '<br>') + '</p>';
    } else if (person.wikipediaTitle) {
      bioEl.innerHTML = '<p class="person-bio-loading">Loading biography&#8230;</p>';
      var url = WIKIPEDIA_API + encodeURIComponent(person.wikipediaTitle);
      var xhr = new XMLHttpRequest();
      xhr.open('GET', url, true);
      xhr.timeout = 10000;
      xhr.onreadystatechange = function () {
        if (xhr.readyState === 4 && xhr.status === 200) {
          try {
            var data = JSON.parse(xhr.responseText);
            if (data.extract) bioEl.innerHTML = '<p>' + escapeHtml(data.extract) + '</p>';
            else bioEl.innerHTML = person.description ? '<p>' + escapeHtml(person.description) + '</p>' : '';
          } catch (e) {
            bioEl.innerHTML = person.description ? '<p>' + escapeHtml(person.description) + '</p>' : '';
          }
        }
      };
      xhr.ontimeout = function () {
        bioEl.innerHTML = person.description ? '<p>' + escapeHtml(person.description) + '</p>' : '';
      };
      xhr.send();
    } else if (person.description) {
      bioEl.innerHTML = '<p>' + escapeHtml(person.description) + '</p>';
    }
  }

  // Main init
  function init() {
    var container = document.getElementById('person-profile');
    if (!container) return;

    var params = new URLSearchParams(window.location.search);
    var id = params.get('id');
    if (!id) {
      container.innerHTML = '<p>Person not found. <a href="people.html">Back to people</a></p>';
      return;
    }

    // CMS-only person
    if (id.indexOf('cms-') === 0) {
      fetchCmsPerson(id, function (err, person) {
        if (err || !person) {
          container.innerHTML = '<p>Person not found. <a href="people.html">Back to people</a></p>';
          return;
        }
        renderProfile(container, person);
      });
      return;
    }

    // Wikidata person (QID)
    fetchWikidataPerson(id, function (err, person) {
      if (err || !person) {
        container.innerHTML = '<p>Person not found. <a href="people.html">Back to people</a></p>';
        return;
      }

      // Check for CMS override
      fetchCmsOverride(id, function (err2, override) {
        if (override) {
          if (override.name) person.name = override.name;
          if (override.description) person.description = override.description;
          if (override.image) person.image = override.image;
          if (override.occupation) person.occupation = override.occupation;
          if (override.company) person.company = override.company;
          if (override.body) person.body = override.body;
          person.source = 'cms';
        }
        renderProfile(container, person);
      });
    });
  }

  init();
})();
