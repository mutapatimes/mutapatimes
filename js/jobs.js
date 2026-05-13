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
      title: 'Junior Social Media Assistant',
      company: 'The Mutapa Times',
      location: 'Remote — Worldwide',
      type: 'Internship · 3 months · 3 days/week',
      summary: 'Grow and shape our presence across the major social ' +
        'platforms. Spot trends, pitch social-first stories, try ' +
        'new formats. Bring your own ideas — rolling intake.',
      url: mt('Junior Social Media Assistant', 'My social handles / portfolio links:'),
      source: 'Mutapa Times',
      _internship: true,
      _detail: {
        whatYouDo: [
          'Help grow our presence across the major social platforms — every channel we publish to.',
          'Reply, repost, and grow our audience among Zimbabweans at home and in the diaspora.',
          'Spot trends and pitch social-first stories that fit the brand.',
          'Refine the brand voice in captions and reply copy — tight, witty, never preachy.',
          'Track engagement and tell us what worked each week.',
          'Bring entirely new ideas — formats, partnerships, content series.',
        ],
        whoWeWant: [
          'You live on social — you know the formats, the culture, the timing.',
          'Sharp written voice in English. Shona or Ndebele a plus.',
          'Curiosity about Zimbabwean business, economics and culture.',
          'Self-starter, comfortable working async across timezones.',
          'No formal experience required — bring your own portfolio of work.',
        ],
      },
    },
    {
      title: 'Junior Editorial Coordinator',
      company: 'The Mutapa Times',
      location: 'Remote — Worldwide',
      type: 'Internship · 3 months · 3 days/week',
      summary: 'Pitch, draft and edit original explainers and analysis. ' +
        'Fact-check stories. Help shape the newsletter. Bring fresh ' +
        'editorial angles and new ways to tell Zimbabwean stories — ' +
        'rolling intake.',
      url: mt('Junior Editorial Coordinator', 'Three writing samples (links or attached):'),
      source: 'Mutapa Times',
      _internship: true,
      _detail: {
        whatYouDo: [
          "Pitch, draft and edit original explainers, op-eds and analysis.",
          "Fact-check stories before they hit the homepage.",
          "Maintain editorial standards — headlines, summaries, structure.",
          "Help shape the newsletter and the weekly editorial agenda.",
          "Find new angles on Zimbabwean stories no one else is telling.",
        ],
        whoWeWant: [
          "Strong writing in English — clear, well-structured, evidence-led.",
          "Comfortable with basic CMS workflow (we'll show you ours).",
          "Reads widely across Zimbabwean and African press.",
          "Opinionated when it matters; open to feedback and fast turnarounds.",
          "Bring fresh editorial ideas — formats, columns, story shapes.",
        ],
      },
    },
    {
      title: 'Junior Data Analyst',
      company: 'The Mutapa Times',
      location: 'Remote — Worldwide',
      type: 'Internship · 3 months · 3 days/week',
      summary: 'Turn Zimbabwean public data into clear, visual stories. ' +
        'Extend the live economy briefing. Prototype new ways to make ' +
        'numbers readable. Bring your own data ideas — rolling intake.',
      url: mt('Junior Data Analyst', "A repo, notebook or dataset I'm proud of:"),
      source: 'Mutapa Times',
      _internship: true,
      _detail: {
        whatYouDo: [
          "Turn Zimbabwean public data into clear, visual stories.",
          "Extend the live economy briefing with new chapters and angles.",
          "Maintain the data pipelines behind FX, jobs, property and economy pages.",
          "Prototype new ways to make numbers readable — charts, infographics, cards.",
          "Pitch data-led stories we haven't told yet.",
        ],
        whoWeWant: [
          "Comfortable with Python — CSV/JSON wrangling, basic scripts.",
          "Reads economic statistics for fun. Basic statistical literacy.",
          "Knowledge of Zimbabwe's data landscape is a strong plus.",
          "Bonus: a chart library, or basic web (HTML/CSS/JS).",
          "Quietly accurate — we publish the source for every number.",
        ],
      },
    },
    {
      title: 'Business Development Associate',
      company: 'The Mutapa Times',
      location: 'Remote — Worldwide',
      type: 'Internship · 3 months · 3 days/week',
      summary: 'Open doors for The Mutapa Times. Pitch advertisers, ' +
        'sponsors and content partners across the Zim diaspora corridor. ' +
        'Bring your own contact list and ideas — rolling intake.',
      url: mt('Business Development Associate', "Brands or partners I'd open conversations with first:"),
      source: 'Mutapa Times',
      _internship: true,
      _detail: {
        whatYouDo: [
          "Identify and reach out to potential advertisers, sponsors and partners — remittance, fintech, airlines, education, diaspora services.",
          "Draft pitch decks and rate cards alongside the editor.",
          "Build and maintain a CRM of warm contacts and conversations.",
          "Respond to inbound advertising and partnership inquiries.",
          "Represent The Mutapa Times at virtual partner meetings.",
          "Pitch new revenue formats — sponsored briefings, content partnerships, branded series.",
        ],
        whoWeWant: [
          "Comfortable cold-emailing and following up — politely persistent.",
          "Network in (or knowledge of) the Zimbabwe diaspora business community.",
          "Clear writing in English — your pitches will represent the brand.",
          "Curious about media business models — newsletters, sponsorships, affiliate.",
          "Bonus: existing relationships in fintech, remittance, airlines or education.",
        ],
      },
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

    var head = '<div class="job-card-head">' + logo +
        '<div class="job-card-headtext">' +
          '<h3 class="job-card-title">' + escapeHtml(j.title) + '</h3>' +
          (j.company ? '<p class="job-card-company">' + escapeHtml(j.company) + '</p>' : '') +
        '</div>' +
      '</div>';
    var summaryHtml = j.summary ? '<p class="job-card-summary">' + escapeHtml(j.summary) + '</p>' : '';
    var metaHtml = metaLine.length ? '<div class="job-card-meta">' + metaLine.join('') + '</div>' : '';
    var postedHtml = j.posted ? '<p class="job-card-posted">Posted ' + escapeHtml(j.posted) + ' ago · ' + escapeHtml(j.source || '') + '</p>' : '';

    // Mutapa Times internships are expandable in-place; scraped jobs are
    // simple <a> cards that open the source posting in a new tab.
    if (j._internship && j._detail) {
      var detail = j._detail;
      var listHtml = function (items) {
        return (items || []).map(function (b) {
          return '<li>' + escapeHtml(b) + '</li>';
        }).join('');
      };
      var expanded =
        '<div class="job-card-expanded">' +
          '<p class="job-card-expanded-label">What you’ll do</p>' +
          '<ul class="job-card-bullets">' + listHtml(detail.whatYouDo) + '</ul>' +
          '<p class="job-card-expanded-label">Who we’re looking for</p>' +
          '<ul class="job-card-bullets">' + listHtml(detail.whoWeWant) + '</ul>' +
          '<a class="job-card-apply" href="' + escapeHtml(j.url) + '">Apply by email →</a>' +
        '</div>';
      return (
        '<div class="job-card job-card--intern" data-intern="1" tabindex="0" role="button" aria-expanded="false">' +
          head + summaryHtml + metaHtml + postedHtml + expanded +
          '<button class="job-card-toggle" type="button" aria-hidden="true">Read more &amp; apply</button>' +
        '</div>'
      );
    }

    return (
      '<a class="job-card" href="' + escapeHtml(j.url) +
      '" target="_blank" rel="noopener" data-source="' + escapeHtml(j.source || '') + '">' +
        head + summaryHtml + metaHtml + postedHtml +
      '</a>'
    );
  }

  // Click anywhere on an internship card (other than the apply link)
  // toggles the expanded state. Delegated so the listener survives
  // grid re-renders on filter changes.
  function onGridClick(e) {
    var apply = e.target.closest && e.target.closest('.job-card-apply');
    if (apply) return;             // let the mailto link fire normally
    var card = e.target.closest && e.target.closest('.job-card--intern');
    if (!card) return;
    e.preventDefault();
    var open = card.classList.toggle('expanded');
    card.setAttribute('aria-expanded', open ? 'true' : 'false');
    var btn = card.querySelector('.job-card-toggle');
    if (btn) btn.textContent = open ? 'Hide details' : 'Read more & apply';
  }
  grid.addEventListener('click', onGridClick);
  grid.addEventListener('keydown', function (e) {
    if (e.key !== 'Enter' && e.key !== ' ') return;
    var card = e.target.closest && e.target.closest('.job-card--intern');
    if (!card) return;
    e.preventDefault();
    onGridClick(e);
  });

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
