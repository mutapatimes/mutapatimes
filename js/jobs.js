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

  // First-party Mutapa Times internships — three rolling tracks that
  // sit in the grid alongside the scraped vacancies. Each card's URL
  // is a mailto: with a prefilled subject and short application
  // template so clicking through opens the user's mail client.
  // Role descriptions are intentionally loose on tools and sources —
  // we want interns who bring their own ideas, not check a tool list.
  function mt(role, samplesQuestion) {
    return 'mailto:news@mutapatimes.com' +
      '?subject=' + encodeURIComponent('Application: ' + role + ' — Mutapa Times') +
      '&body=' + encodeURIComponent(
        'Hi Mutapa Times team,\n\n' +
        "I'd like to apply for the " + role + ' role.\n\n' +
        '1. A short intro about me:\n\n' +
        '2. ' + samplesQuestion + '\n\n' +
        '3. Why this role, in one paragraph:\n\n' +
        "4. One new idea I'd bring to the Mutapa Times:\n\n" +
        '5. Earliest start date:\n\n' +
        'Thanks,\n'
      );
  }
  var INTERNAL_INTERNSHIPS = [
    {
      title: 'Social Intern',
      company: 'The Mutapa Times',
      location: 'Remote — Worldwide',
      type: 'Internship · 3 months · 3 days/week',
      summary: 'Grow and shape our presence across the major social ' +
        'platforms. Spot trends, pitch social-first stories, try ' +
        'new formats. Bring your own ideas — rolling intake, ' +
        'always recruiting.',
      url: mt('Social Intern', 'My social handles / portfolio links:'),
      source: 'Mutapa Times',
      _internship: true,
    },
    {
      title: 'Editor Intern',
      company: 'The Mutapa Times',
      location: 'Remote — Worldwide',
      type: 'Internship · 3 months · 3 days/week',
      summary: 'Pitch, draft and edit original explainers and analysis. ' +
        'Fact-check stories. Help shape the newsletter. Bring fresh ' +
        'editorial angles and new ways to tell Zimbabwean stories — ' +
        'rolling intake.',
      url: mt('Editor Intern', 'Three writing samples (links or attached):'),
      source: 'Mutapa Times',
      _internship: true,
    },
    {
      title: 'Data Intern',
      company: 'The Mutapa Times',
      location: 'Remote — Worldwide',
      type: 'Internship · 3 months · 3 days/week',
      summary: 'Turn Zimbabwean public data into clear, visual stories. ' +
        'Extend the live economy briefing. Prototype new ways to make ' +
        'numbers readable. Bring your own data ideas — rolling intake.',
      url: mt('Data Intern', "A repo, notebook or dataset I'm proud of:"),
      source: 'Mutapa Times',
      _internship: true,
    },
  ];

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
    var scraped = (data && data.jobs) || [];
    // Mix the first-party internships in with the scraped vacancies.
    // They appear at the top so they don't get lost on the second
    // page, but use exactly the same card layout as everything else.
    _allJobs = INTERNAL_INTERNSHIPS.concat(scraped);
    if (!_allJobs.length) {
      grid.innerHTML = '<p class="jobs-empty">No vacancies available right now. Check back soon.</p>';
      if (meta) meta.textContent = '';
      return;
    }
    populateFilters(_allJobs);
    applyFilters();
    if (meta) {
      var sources = (data && data.sources || []).join(' + ');
      var freshness = data && data.fetched_at ? relativeAge(data.fetched_at) : '';
      var parts = [];
      if (sources) parts.push('Sourced from ' + sources);
      if (freshness) parts.push(freshness);
      parts.push(scraped.length + ' active vacancies · ' +
                 INTERNAL_INTERNSHIPS.length + ' Mutapa Times internships');
      meta.textContent = parts.join(' · ');
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
      // Even if the scraped feed is down, still show the in-house
      // internships — those are the most important roles on this page.
      render({ jobs: [], sources: [], fetched_at: null });
      if (window.console) console.warn('Jobs fetch failed:', err);
    });
})();
