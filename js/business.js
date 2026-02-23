/*
 * The Mutapa Times - Business Profile
 * Renders a single business profile page with SEO-optimised schema.org markup.
 * Used by business.html?id=Q12345 (Wikidata) or business.html?id=cms-slug (CMS)
 */

(function () {
  var GITHUB_REPO = "mutapatimes/mutapatimes";
  var GITHUB_BRANCH = "main";
  var BIZ_API = "https://api.github.com/repos/" + GITHUB_REPO + "/contents/content/businesses?ref=" + GITHUB_BRANCH;
  var BIZ_RAW = "https://raw.githubusercontent.com/" + GITHUB_REPO + "/" + GITHUB_BRANCH + "/content/businesses/";
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

  // Build SPARQL query for a single Wikidata QID
  function sparqlForQid(qid) {
    return [
      'SELECT ?orgLabel ?orgDescription ?image ?industryLabel ?inception ?article ?hqLabel WHERE {',
      '  BIND(wd:' + qid + ' AS ?org)',
      '  OPTIONAL { ?org wdt:P18 ?image. }',
      '  OPTIONAL { ?org wdt:P452 ?industry. }',
      '  OPTIONAL { ?org wdt:P571 ?inception. }',
      '  OPTIONAL { ?org wdt:P159 ?hq. }',
      '  OPTIONAL { ?article schema:about ?org. ?article schema:isPartOf <https://en.wikipedia.org/>. }',
      '  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }',
      '}'
    ].join('\n');
  }

  // Fetch a single business from Wikidata
  function fetchWikidataBusiness(qid, callback) {
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

            var industries = [];
            var biz = null;
            for (var i = 0; i < bindings.length; i++) {
              var b = bindings[i];
              if (!biz) {
                var wpUrl = b.article ? b.article.value : '';
                var wpTitle = wpUrl ? decodeURIComponent(wpUrl.split('/wiki/').pop()) : '';
                biz = {
                  id: qid,
                  source: 'wikidata',
                  name: b.orgLabel ? b.orgLabel.value : '',
                  description: b.orgDescription ? b.orgDescription.value : '',
                  image: b.image ? b.image.value : '',
                  industry: '',
                  inception: b.inception ? b.inception.value : '',
                  headquarters: b.hqLabel ? b.hqLabel.value : '',
                  wikidataUrl: 'https://www.wikidata.org/wiki/' + qid,
                  wikipediaTitle: wpTitle,
                  wikipediaUrl: wpUrl
                };
              }
              var ind = b.industryLabel ? b.industryLabel.value : '';
              if (ind && industries.indexOf(ind) === -1) industries.push(ind);
            }
            if (biz) biz.industry = industries.join(', ');
            callback(null, biz);
          } catch (e) { callback(e, null); }
        } else { callback(new Error('Wikidata HTTP ' + xhr.status), null); }
      }
    };
    xhr.ontimeout = function () { callback(new Error('Wikidata timeout'), null); };
    xhr.send();
  }

  // Check CMS for an override by wikidata_id
  function fetchCmsOverride(qid, callback) {
    fetchJSON(BIZ_API, function (err, entries) {
      if (err || !entries || !entries.length) { callback(null, null); return; }
      var mdFiles = [];
      for (var i = 0; i < entries.length; i++) {
        if (entries[i].name && /\.md$/.test(entries[i].name)) mdFiles.push(entries[i].name);
      }
      if (!mdFiles.length) { callback(null, null); return; }

      var pending = mdFiles.length;
      var found = null;
      mdFiles.forEach(function (filename) {
        fetchText(BIZ_RAW + filename, function (err2, raw) {
          if (!err2 && raw && !found) {
            var parsed = parseFrontmatter(raw);
            var m = parsed.meta;
            if (m.wikidata_id === qid || 'cms-' + filename.replace(/\.md$/, '') === qid) {
              found = {
                name: m.name || '',
                industry: m.industry || '',
                headquarters: m.headquarters || '',
                description: m.bio || '',
                image: m.image || '',
                inception: m.founded || '',
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

  // Fetch CMS-only business (id starts with 'cms-')
  function fetchCmsBusiness(slug, callback) {
    var filename = slug.replace(/^cms-/, '') + '.md';
    fetchText(BIZ_RAW + filename, function (err, raw) {
      if (err || !raw) { callback(new Error('Not found'), null); return; }
      var parsed = parseFrontmatter(raw);
      var m = parsed.meta;
      callback(null, {
        id: slug,
        source: 'cms',
        name: m.name || '',
        description: m.bio || '',
        image: m.image || '',
        industry: m.industry || '',
        headquarters: m.headquarters || '',
        inception: m.founded || '',
        wikidataUrl: m.wikidata_id ? 'https://www.wikidata.org/wiki/' + m.wikidata_id : '',
        wikipediaTitle: '',
        wikipediaUrl: '',
        body: parsed.body
      });
    });
  }

  // Update page meta tags
  function updateMeta(biz) {
    var title = biz.name;
    if (biz.industry) title += ' - ' + biz.industry.split(',')[0].trim();
    title += ' | The Mutapa Times';
    document.title = title;

    var desc = biz.name;
    if (biz.industry) desc += ' operates in ' + biz.industry;
    if (biz.headquarters) desc += ', headquartered in ' + biz.headquarters;
    if (biz.description) desc += '. ' + biz.description;
    if (desc.length > 160) desc = desc.substring(0, 157) + '...';

    var pageUrl = BASE_URL + '/business.html?id=' + encodeURIComponent(biz.id);
    var imgUrl = biz.image || BASE_URL + '/img/banner.png';

    var canonical = document.querySelector('link[rel="canonical"]');
    if (canonical) canonical.setAttribute('href', pageUrl);

    var metaDesc = document.querySelector('meta[name="description"]');
    if (metaDesc) metaDesc.setAttribute('content', desc);

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

  // Inject Organization schema.org JSON-LD
  function injectSchema(biz) {
    var schema = {
      '@context': 'https://schema.org',
      '@type': 'Organization',
      'name': biz.name,
      'url': BASE_URL + '/business.html?id=' + encodeURIComponent(biz.id),
      'description': biz.description || ''
    };

    if (biz.image) schema.logo = biz.image;
    if (biz.industry) schema.industry = biz.industry.split(',')[0].trim();
    if (biz.headquarters) {
      schema.location = {
        '@type': 'Place',
        'name': biz.headquarters,
        'address': { '@type': 'PostalAddress', 'addressCountry': 'ZW' }
      };
    }
    if (biz.inception) {
      var d = new Date(biz.inception);
      if (!isNaN(d.getTime())) schema.foundingDate = d.toISOString().split('T')[0];
    }

    var sameAs = [];
    if (biz.wikipediaUrl) sameAs.push(biz.wikipediaUrl);
    if (biz.wikidataUrl) sameAs.push(biz.wikidataUrl);
    if (sameAs.length) schema.sameAs = sameAs;

    var script = document.createElement('script');
    script.type = 'application/ld+json';
    script.textContent = JSON.stringify(schema);
    document.head.appendChild(script);

    // BreadcrumbList schema
    var breadcrumb = {
      '@context': 'https://schema.org',
      '@type': 'BreadcrumbList',
      'itemListElement': [
        { '@type': 'ListItem', 'position': 1, 'name': 'Home', 'item': BASE_URL + '/' },
        { '@type': 'ListItem', 'position': 2, 'name': 'Businesses', 'item': BASE_URL + '/businesses.html' },
        { '@type': 'ListItem', 'position': 3, 'name': biz.name, 'item': BASE_URL + '/business.html?id=' + encodeURIComponent(biz.id) }
      ]
    };
    var script2 = document.createElement('script');
    script2.type = 'application/ld+json';
    script2.textContent = JSON.stringify(breadcrumb);
    document.head.appendChild(script2);
  }

  // Build share buttons HTML
  function shareButtons(biz) {
    var url = encodeURIComponent(BASE_URL + '/business.html?id=' + encodeURIComponent(biz.id));
    var text = encodeURIComponent(biz.name + ' - Business profile on The Mutapa Times');
    return '<div class="business-profile-share">'
      + '<span class="business-profile-share-label">Share</span>'
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

  function formatYear(dateStr) {
    if (!dateStr) return '';
    var d = new Date(dateStr);
    if (isNaN(d.getTime())) return '';
    return d.getFullYear().toString();
  }

  // Render the full profile page
  function renderProfile(container, biz) {
    updateMeta(biz);
    injectSchema(biz);

    var imgHtml = biz.image
      ? '<img src="' + escapeHtml(biz.image) + '" alt="' + escapeHtml(biz.name) + '" class="business-profile-img">'
      : '';

    var links = '';
    if (biz.wikipediaUrl) {
      links += '<a href="' + escapeHtml(biz.wikipediaUrl) + '" target="_blank" rel="noopener" class="business-profile-extlink">Wikipedia</a>';
    }
    if (biz.wikidataUrl) {
      links += (links ? ' ' : '') + '<a href="' + escapeHtml(biz.wikidataUrl) + '" target="_blank" rel="noopener" class="business-profile-extlink">Wikidata</a>';
    }

    var foundedStr = '';
    var foundedYear = formatYear(biz.inception);
    if (foundedYear) {
      foundedStr = '<p class="business-profile-founded"><strong>Founded:</strong> ' + foundedYear + '</p>';
    }

    var html = '<nav class="business-profile-breadcrumb" aria-label="Breadcrumb">'
      + '<a href="index.html">Home</a> <span aria-hidden="true">/</span> '
      + '<a href="businesses.html">Businesses</a> <span aria-hidden="true">/</span> '
      + '<span>' + escapeHtml(biz.name) + '</span>'
      + '</nav>'
      + '<div class="business-profile-header">'
      + (imgHtml ? '<div class="business-profile-img-wrap">' + imgHtml + '</div>' : '')
      + '<div class="business-profile-info">'
      + '<h1 class="business-profile-name">' + escapeHtml(biz.name) + '</h1>'
      + '<p class="business-profile-industry">' + escapeHtml(biz.industry || '') + '</p>'
      + (biz.headquarters ? '<p class="business-profile-hq">' + escapeHtml(biz.headquarters) + '</p>' : '')
      + foundedStr
      + (links ? '<div class="business-profile-extlinks">' + links + '</div>' : '')
      + shareButtons(biz)
      + '</div></div>'
      + '<div class="business-profile-bio" id="business-profile-bio"></div>'
      + '<div class="business-profile-back"><a href="businesses.html">&larr; All businesses</a></div>';

    container.innerHTML = html;

    // Load bio
    var bioEl = document.getElementById('business-profile-bio');
    if (biz.body && biz.body.trim()) {
      bioEl.innerHTML = '<p>' + escapeHtml(biz.body.trim()).replace(/\n\n/g, '</p><p>').replace(/\n/g, '<br>') + '</p>';
    } else if (biz.wikipediaTitle) {
      bioEl.innerHTML = '<p class="business-bio-loading">Loading description&#8230;</p>';
      var url = WIKIPEDIA_API + encodeURIComponent(biz.wikipediaTitle);
      var xhr = new XMLHttpRequest();
      xhr.open('GET', url, true);
      xhr.timeout = 10000;
      xhr.onreadystatechange = function () {
        if (xhr.readyState === 4 && xhr.status === 200) {
          try {
            var data = JSON.parse(xhr.responseText);
            if (data.extract) bioEl.innerHTML = '<p>' + escapeHtml(data.extract) + '</p>';
            else bioEl.innerHTML = biz.description ? '<p>' + escapeHtml(biz.description) + '</p>' : '';
          } catch (e) {
            bioEl.innerHTML = biz.description ? '<p>' + escapeHtml(biz.description) + '</p>' : '';
          }
        }
      };
      xhr.ontimeout = function () {
        bioEl.innerHTML = biz.description ? '<p>' + escapeHtml(biz.description) + '</p>' : '';
      };
      xhr.send();
    } else if (biz.description) {
      bioEl.innerHTML = '<p>' + escapeHtml(biz.description) + '</p>';
    }
  }

  // Main init
  function init() {
    var container = document.getElementById('business-profile');
    if (!container) return;

    var params = new URLSearchParams(window.location.search);
    var id = params.get('id');
    if (!id) {
      container.innerHTML = '<p>Business not found. <a href="businesses.html">Back to businesses</a></p>';
      return;
    }

    // CMS-only business
    if (id.indexOf('cms-') === 0) {
      fetchCmsBusiness(id, function (err, biz) {
        if (err || !biz) {
          container.innerHTML = '<p>Business not found. <a href="businesses.html">Back to businesses</a></p>';
          return;
        }
        renderProfile(container, biz);
      });
      return;
    }

    // Wikidata business (QID)
    fetchWikidataBusiness(id, function (err, biz) {
      if (err || !biz) {
        container.innerHTML = '<p>Business not found. <a href="businesses.html">Back to businesses</a></p>';
        return;
      }

      // Check for CMS override
      fetchCmsOverride(id, function (err2, override) {
        if (override) {
          if (override.name) biz.name = override.name;
          if (override.description) biz.description = override.description;
          if (override.image) biz.image = override.image;
          if (override.industry) biz.industry = override.industry;
          if (override.headquarters) biz.headquarters = override.headquarters;
          if (override.inception) biz.inception = override.inception;
          if (override.body) biz.body = override.body;
          biz.source = 'cms';
        }
        renderProfile(container, biz);
      });
    });
  }

  init();
})();
