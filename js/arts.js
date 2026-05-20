/**
 * Arts page — renders data/arts.json as a filterable grid.
 *
 * Each artwork tile links to its on-site detail page at /arts/<slug>.html
 * (statically pre-built by scripts/build_arts_pages.py).
 *
 * If an artwork's image_url is empty (sample data, or fetch hasn't run),
 * the tile renders a typographic fallback so the page stays legible.
 */
(function () {
  var DATA_URL = 'data/arts.json';
  var PAGE_SIZE = 60;
  var grid = document.getElementById('artsGrid');
  var pagerEl = document.getElementById('artsPager');
  var searchEl = document.getElementById('artsSearch');
  var mediumEl = document.getElementById('artsMedium');
  var sortEl = document.getElementById('artsSort');
  if (!grid) return;

  var state = {
    artworks: [],
    filtered: [],
    page: 1,
    search: '',
    medium: '',
    sort: 'price-desc'
  };

  // ── price parsing ────────────────────────────────────────────────
  // Convert strings like "US$260,000", "£27,500", "Inquire about availability"
  // into a numeric for sorting. "Inquire" sorts to the end.
  var FX = { 'US$': 1, '$': 1, '£': 1.27, '€': 1.08 };
  function parsePrice(s) {
    if (!s) return null;
    var m = s.match(/^(US\$|\$|£|€)\s*([\d,\.]+)/);
    if (!m) return null;
    var rate = FX[m[1]] || 1;
    var n = parseFloat(m[2].replace(/,/g, ''));
    return isNaN(n) ? null : n * rate;
  }

  // ── rendering ────────────────────────────────────────────────────
  function paperForSlug(slug) {
    // Deterministic muted palette pick — gives sample tiles editorial variety
    var palette = ['#f5e8c8', '#eadad5', '#dae2d5', '#d7dae8', '#ecdac0', '#e2d8d0'];
    var h = 0;
    for (var i = 0; i < slug.length; i++) h = (h * 31 + slug.charCodeAt(i)) >>> 0;
    return palette[h % palette.length];
  }

  function tile(art) {
    var href = 'arts/' + art.slug + '.html';
    var card = document.createElement('a');
    card.className = 'arts-card';
    card.href = href;

    var wrap = document.createElement('div');
    wrap.className = 'arts-card-image-wrap';

    if (art.image_url) {
      var img = document.createElement('img');
      img.className = 'arts-card-image';
      img.src = art.image_url;
      img.alt = art.artist_name + ' — ' + art.title;
      img.loading = 'lazy';
      img.decoding = 'async';
      wrap.appendChild(img);
    } else {
      // Typographic fallback tile
      wrap.style.background = paperForSlug(art.slug);
      var fb = document.createElement('div');
      fb.className = 'arts-card-image-fallback';
      var fbA = document.createElement('div');
      fbA.className = 'fb-artist';
      fbA.textContent = art.artist_name;
      var fbT = document.createElement('div');
      fbT.className = 'fb-title';
      fbT.textContent = '“' + art.title + '”';
      var fbM = document.createElement('div');
      fbM.className = 'fb-mark';
      fbM.textContent = art.medium || art.category || 'Artwork';
      fb.appendChild(fbA);
      fb.appendChild(fbT);
      fb.appendChild(fbM);
      wrap.appendChild(fb);
    }
    card.appendChild(wrap);

    var meta = document.createElement('div');
    meta.className = 'arts-card-meta';
    meta.innerHTML =
      '<p class="arts-card-artist">' + escapeHTML(art.artist_name) + '</p>' +
      '<p class="arts-card-title">' + escapeHTML(art.title) +
        (art.year ? ' <span class="arts-card-year">, ' + escapeHTML(art.year) + '</span>' : '') +
      '</p>' +
      (art.partner_name ? '<p class="arts-card-partner">' + escapeHTML(art.partner_name) + '</p>' : '') +
      '<p class="arts-card-price' + (parsePrice(art.price) === null ? ' is-inquire' : '') + '">' +
        escapeHTML(art.price || 'Inquire') + '</p>';
    card.appendChild(meta);

    return card;
  }

  function escapeHTML(s) {
    return (s || '').replace(/[&<>"']/g, function (c) {
      return ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'})[c];
    });
  }

  // ── filtering / sorting ─────────────────────────────────────────
  function applyFilters() {
    var q = state.search.trim().toLowerCase();
    state.filtered = state.artworks.filter(function (a) {
      if (state.medium && (a.medium || '') !== state.medium) return false;
      if (!q) return true;
      var hay = (a.artist_name + ' ' + a.title + ' ' + (a.partner_name || '')).toLowerCase();
      return hay.indexOf(q) !== -1;
    });
    sortFiltered();
    state.page = 1;
    render();
  }

  function sortFiltered() {
    var s = state.sort;
    state.filtered.sort(function (a, b) {
      if (s === 'price-desc' || s === 'price-asc') {
        var pa = parsePrice(a.price), pb = parsePrice(b.price);
        if (pa === null && pb === null) return 0;
        if (pa === null) return 1;          // inquires always last
        if (pb === null) return -1;
        return s === 'price-desc' ? pb - pa : pa - pb;
      }
      if (s === 'year-desc' || s === 'year-asc') {
        var ya = yearOf(a.year), yb = yearOf(b.year);
        return s === 'year-desc' ? yb - ya : ya - yb;
      }
      if (s === 'artist-asc') {
        return (a.artist_name || '').localeCompare(b.artist_name || '');
      }
      return 0;
    });
  }

  function yearOf(s) {
    var m = (s || '').match(/\d{4}/);
    return m ? parseInt(m[0], 10) : 0;
  }

  function render() {
    grid.innerHTML = '';
    var start = (state.page - 1) * PAGE_SIZE;
    var slice = state.filtered.slice(start, start + PAGE_SIZE);
    if (!slice.length) {
      grid.innerHTML = '<p class="arts-loading">No artworks match.</p>';
      pagerEl.hidden = true;
      return;
    }
    var frag = document.createDocumentFragment();
    slice.forEach(function (a) { frag.appendChild(tile(a)); });
    grid.appendChild(frag);
    renderPager();
  }

  function renderPager() {
    var totalPages = Math.max(1, Math.ceil(state.filtered.length / PAGE_SIZE));
    if (totalPages <= 1) { pagerEl.hidden = true; pagerEl.innerHTML = ''; return; }
    pagerEl.hidden = false;
    pagerEl.innerHTML = '';
    var prev = document.createElement('button');
    prev.textContent = '← Prev';
    prev.disabled = state.page === 1;
    prev.addEventListener('click', function () {
      state.page = Math.max(1, state.page - 1);
      window.scrollTo({ top: grid.offsetTop - 80, behavior: 'smooth' });
      render();
    });
    var status = document.createElement('span');
    status.className = 'arts-pager-status';
    status.textContent = 'Page ' + state.page + ' of ' + totalPages +
      ' · ' + state.filtered.length + ' artworks';
    var next = document.createElement('button');
    next.textContent = 'Next →';
    next.disabled = state.page === totalPages;
    next.addEventListener('click', function () {
      state.page = Math.min(totalPages, state.page + 1);
      window.scrollTo({ top: grid.offsetTop - 80, behavior: 'smooth' });
      render();
    });
    pagerEl.appendChild(prev);
    pagerEl.appendChild(status);
    pagerEl.appendChild(next);
  }

  function populateMediumFilter() {
    var media = {};
    state.artworks.forEach(function (a) {
      if (a.medium) media[a.medium] = (media[a.medium] || 0) + 1;
    });
    var entries = Object.keys(media).sort();
    entries.forEach(function (m) {
      var opt = document.createElement('option');
      opt.value = m;
      opt.textContent = m + ' (' + media[m] + ')';
      mediumEl.appendChild(opt);
    });
  }

  // ── bootstrap ───────────────────────────────────────────────────
  fetch(DATA_URL)
    .then(function (r) { return r.json(); })
    .then(function (data) {
      state.artworks = data.artworks || [];
      populateMediumFilter();
      applyFilters();
    })
    .catch(function (err) {
      grid.innerHTML = '<p class="arts-loading">Could not load Zimbabwean artworks. Please try again later.</p>';
      console.error('arts.js failed:', err);
    });

  searchEl && searchEl.addEventListener('input', function (e) {
    state.search = e.target.value;
    applyFilters();
  });
  mediumEl && mediumEl.addEventListener('change', function (e) {
    state.medium = e.target.value;
    applyFilters();
  });
  sortEl && sortEl.addEventListener('change', function (e) {
    state.sort = e.target.value;
    sortFiltered();
    render();
  });
})();
