/**
 * Live Zimbabwe job listings — renders data/jobs.json (scraped from
 * vacancymail.co.zw + other boards every 6h by GitHub Actions).
 * Each card links to the original posting so the apply flow happens
 * on the source site.
 */
(function () {
  var DATA_URL = 'data/jobs.json';
  var grid = document.getElementById('jobsGrid');
  var meta = document.getElementById('jobsMeta');
  var searchEl = document.getElementById('jobsSearch');
  var locationEl = document.getElementById('jobsLocation');
  var typeEl = document.getElementById('jobsType');
  if (!grid) return;

  var _allJobs = [];

  function escapeHtml(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function relativeAge(iso) {
    if (!iso) return '';
    var then = new Date(iso).getTime();
    if (isNaN(then)) return '';
    var diffMin = Math.round((Date.now() - then) / 60000);
    if (diffMin < 1) return 'updated just now';
    if (diffMin < 60) return 'updated ' + diffMin + ' min ago';
    var diffHr = Math.round(diffMin / 60);
    if (diffHr < 24) return 'updated ' + diffHr + ' hr ago';
    var diffDay = Math.round(diffHr / 24);
    return 'updated ' + diffDay + ' day' + (diffDay === 1 ? '' : 's') + ' ago';
  }

  function renderCard(j) {
    var logo = j.logo
      ? '<img class="job-card-logo" src="' + escapeHtml(j.logo) + '" alt="' +
        escapeHtml(j.company || '') + '" loading="lazy" onerror="this.style.display=\'none\'">'
      : '<div class="job-card-logo job-card-logo--placeholder">' +
        escapeHtml((j.company || j.title || '?').slice(0, 1).toUpperCase()) +
        '</div>';

    var metaLine = [];
    if (j.location) metaLine.push('<span class="job-card-pill job-card-pill--loc">📍 ' + escapeHtml(j.location) + '</span>');
    if (j.type) metaLine.push('<span class="job-card-pill">' + escapeHtml(j.type) + '</span>');
    if (j.salary) metaLine.push('<span class="job-card-pill job-card-pill--pay">' + escapeHtml(j.salary) + '</span>');
    if (j.expires) metaLine.push('<span class="job-card-pill job-card-pill--time">Closes ' + escapeHtml(j.expires) + '</span>');

    return (
      '<a class="job-card" href="' + escapeHtml(j.url) +
      '" target="_blank" rel="noopener" data-source="' + escapeHtml(j.source || '') + '">' +
        '<div class="job-card-head">' + logo +
          '<div class="job-card-headtext">' +
            '<h3 class="job-card-title">' + escapeHtml(j.title) + '</h3>' +
            (j.company ? '<p class="job-card-company">' + escapeHtml(j.company) + '</p>' : '') +
          '</div>' +
        '</div>' +
        (j.summary ? '<p class="job-card-summary">' + escapeHtml(j.summary) + '</p>' : '') +
        (metaLine.length ? '<div class="job-card-meta">' + metaLine.join('') + '</div>' : '') +
        (j.posted ? '<p class="job-card-posted">Posted ' + escapeHtml(j.posted) + ' ago · ' + escapeHtml(j.source || '') + '</p>' : '') +
      '</a>'
    );
  }

  function populateFilters(jobs) {
    var locations = {};
    var types = {};
    jobs.forEach(function (j) {
      if (j.location) locations[j.location] = true;
      if (j.type) types[j.type] = true;
    });
    var locOpts = Object.keys(locations).sort();
    var typeOpts = Object.keys(types).sort();
    if (locationEl) {
      locOpts.forEach(function (l) {
        var o = document.createElement('option');
        o.value = l; o.textContent = l;
        locationEl.appendChild(o);
      });
    }
    if (typeEl) {
      typeOpts.forEach(function (t) {
        var o = document.createElement('option');
        o.value = t; o.textContent = t;
        typeEl.appendChild(o);
      });
    }
  }

  function applyFilters() {
    var q = (searchEl && searchEl.value || '').toLowerCase().trim();
    var loc = locationEl && locationEl.value || '';
    var typ = typeEl && typeEl.value || '';

    var filtered = _allJobs.filter(function (j) {
      if (loc && j.location !== loc) return false;
      if (typ && j.type !== typ) return false;
      if (q) {
        var hay = (
          (j.title || '') + ' ' +
          (j.company || '') + ' ' +
          (j.location || '') + ' ' +
          (j.summary || '')
        ).toLowerCase();
        if (hay.indexOf(q) === -1) return false;
      }
      return true;
    });

    if (!filtered.length) {
      grid.innerHTML = '<p class="jobs-empty">No vacancies match your filters.</p>';
      return;
    }
    grid.innerHTML = filtered.map(renderCard).join('');
  }

  function render(data) {
    _allJobs = (data && data.jobs) || [];
    if (!_allJobs.length) {
      grid.innerHTML = '<p class="jobs-empty">No vacancies available right now. Check back soon.</p>';
      if (meta) meta.textContent = '';
      return;
    }
    populateFilters(_allJobs);
    applyFilters();
    if (meta && data.fetched_at) {
      var sources = (data.sources || []).join(' + ');
      meta.textContent = (sources ? 'Sourced from ' + sources + ' · ' : '') +
        relativeAge(data.fetched_at) + ' · ' + data.jobs.length + ' active vacancies';
    }
  }

  if (searchEl) {
    var debounceTimer;
    searchEl.addEventListener('input', function () {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(applyFilters, 250);
    });
  }
  if (locationEl) locationEl.addEventListener('change', applyFilters);
  if (typeEl) typeEl.addEventListener('change', applyFilters);

  fetch(DATA_URL, { cache: 'no-cache' })
    .then(function (r) {
      if (!r.ok) throw new Error('HTTP ' + r.status);
      return r.json();
    })
    .then(render)
    .catch(function (err) {
      grid.innerHTML = '<p class="jobs-empty">Vacancies unavailable. <a href="https://vacancymail.co.zw/jobs/" target="_blank" rel="noopener">Browse vacancymail.co.zw</a></p>';
      if (window.console) console.warn('Jobs fetch failed:', err);
    });
})();
