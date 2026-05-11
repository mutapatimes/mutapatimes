/**
 * The Mutapa Times — Economy narrative.
 *
 * Loads two ZimStat datasets in parallel:
 *   - data/gdp-zimbabwe-quarterly.json   (quarterly GDP by sector)
 *   - data/zimstat-bop-quarterly.json    (quarterly Balance of Payments)
 *
 * Then renders six chapter charts + a four-tile hero, and writes
 * data-driven analytical pull-quotes for each chapter. Pure
 * client-side; no third-party data; designed to degrade gracefully
 * if either feed is missing.
 */
(function () {
  if (typeof Chart === 'undefined') {
    console.warn('Chart.js not loaded — economy charts skipped.');
    return;
  }

  // ── Brand-aligned chart palette ───────────────────────────
  var COLOR_ACCENT     = '#c41e1e';     // brand red
  var COLOR_GREEN      = '#1a7f37';     // money / positive
  var COLOR_BLUE       = '#1f6feb';
  var COLOR_AMBER      = '#bf8700';
  var COLOR_INK        = '#1a1a1a';
  var COLOR_MUTED      = '#5f5c54';
  var COLOR_PAPER      = '#fafaf7';
  var COLOR_FILL_RED   = 'rgba(196,30,30,0.10)';
  var COLOR_FILL_GREEN = 'rgba(26,127,55,0.18)';
  var COLOR_FILL_BLUE  = 'rgba(31,111,235,0.15)';

  var SECTOR_PALETTE = [
    '#c41e1e', '#1f6feb', '#1a7f37', '#bf8700', '#8957e5', '#0a7e8c',
    '#6639ba', '#cf222e', '#0550ae', '#9a6700', '#116329', '#a01818',
    '#3f3f8c', '#7d4900', '#0969da', '#1f6feb', '#2da44e', '#bf8700',
    '#cf222e', '#5d3a9b',
  ];

  // ── Chart.js global defaults (apply once) ─────────────────
  Chart.defaults.font.family = 'Inter, system-ui, sans-serif';
  Chart.defaults.font.size = 11;
  Chart.defaults.color = COLOR_INK;

  // ── Formatters ────────────────────────────────────────────
  function fmtUSD(n) {
    if (n == null || isNaN(n)) return '—';
    var abs = Math.abs(n);
    var sign = n < 0 ? '−' : '';
    if (abs >= 1e9) return sign + '$' + (abs / 1e9).toFixed(1) + 'B';
    if (abs >= 1e6) return sign + '$' + (abs / 1e6).toFixed(1) + 'M';
    if (abs >= 1e3) return sign + '$' + (abs / 1e3).toFixed(0) + 'K';
    return sign + '$' + Math.round(abs);
  }
  // BoP data is in millions; convert to absolute USD for the formatter
  function fmtBopUSD(mn) {
    if (mn == null || isNaN(mn)) return '—';
    return fmtUSD(mn * 1e6);
  }
  function fmtPct(n, signed) {
    if (n == null || isNaN(n)) return '—';
    var s = (n >= 0 && signed ? '+' : '') + n.toFixed(1) + '%';
    return s;
  }
  function escapeHtml(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }
  function shortSectorName(name) {
    var map = {
      'Wholesale and retail trade; repair of motor vehicles and motorcycles': 'Wholesale & retail',
      'Public administration and defence; compulsory social security': 'Public admin & defence',
      'Water supply; sewerage, waste management and remediation activities': 'Water & waste',
      'Electricity, gas, steam and air conditioning supply': 'Electricity & gas',
      'Agiculture, Hunting and Fishing and forestry': 'Agriculture & forestry',
      'Professional, scientific and technical activities': 'Professional & scientific',
      'Administrative and support service activities': 'Admin & support',
      'Human health and social work activities': 'Health & social work',
      'Arts, entertainment and recreation': 'Arts & entertainment',
      'Accommodation and food service activities': 'Hospitality',
      'Information and communication': 'ICT',
      'Financial and insurance activities': 'Finance & insurance',
      'Transportation and storage': 'Transport & storage',
    };
    return map[name] || name;
  }

  // Vertical break-line plugin: dashed line at series re-base.
  function breakLinePlugin(localBreakIdx, label) {
    return {
      id: 'breakLine',
      afterDatasetsDraw: function (chart) {
        if (localBreakIdx < 0) return;
        var ctx = chart.ctx;
        var x = chart.scales.x;
        var y = chart.scales.y;
        var xLeft = x.getPixelForValue(localBreakIdx - 1);
        var xRight = x.getPixelForValue(localBreakIdx);
        var px = (xLeft + xRight) / 2;
        ctx.save();
        ctx.strokeStyle = 'rgba(196,30,30,0.6)';
        ctx.lineWidth = 1.5;
        ctx.setLineDash([5, 4]);
        ctx.beginPath();
        ctx.moveTo(px, y.top);
        ctx.lineTo(px, y.bottom);
        ctx.stroke();
        ctx.setLineDash([]);
        ctx.fillStyle = 'rgba(196,30,30,0.9)';
        ctx.font = '600 10px Inter, sans-serif';
        ctx.textAlign = 'left';
        ctx.fillText(label || 'Series re-based', px + 4, y.top + 12);
        ctx.restore();
      },
    };
  }

  // ── Hero stat cards (four tiles) ──────────────────────────
  function renderHero(gdp, bop) {
    var el = document.getElementById('econHeroStats');
    if (!el) return;

    var tiles = [];

    if (gdp && gdp.quarters && gdp.aggregates) {
      var lastIdx = gdp.quarters.length - 1;
      var quarter = gdp.quarters[lastIdx];
      var totalLatest = gdp.aggregates['GDP at Market Prices'][lastIdx];
      var yearAgo = gdp.aggregates['GDP at Market Prices'][lastIdx - 4];
      var yoy = yearAgo ? ((totalLatest - yearAgo) / yearAgo) * 100 : null;
      tiles.push({
        label: 'Latest quarterly GDP',
        value: fmtUSD(totalLatest),
        sub: quarter + ' &middot; ZimStat',
        meta: yoy == null ? '' :
          '<span class="econ-stat-delta ' + (yoy >= 0 ? 'up' : 'down') + '">' +
          (yoy >= 0 ? '▲' : '▼') + ' ' + fmtPct(Math.abs(yoy), false) + ' YoY</span>',
      });

      // Top sector
      var topName = null, topVal = -Infinity;
      gdp.sector_order.forEach(function (n) {
        var v = gdp.sectors[n][lastIdx];
        if (v > topVal) { topVal = v; topName = n; }
      });
      var share = totalLatest ? (topVal / totalLatest) * 100 : 0;
      tiles.push({
        label: 'Largest sector',
        value: shortSectorName(topName),
        sub: fmtUSD(topVal) + ' &middot; ' + fmtPct(share, false) + ' of GDP',
        meta: '',
      });
    }

    if (bop && bop.series) {
      var bopQuarters = bop.quarters;
      var lastBop = bopQuarters.length - 1;
      var bopQ = bopQuarters[lastBop];

      // Current account, latest
      var ca = bop.series.current_account[lastBop];
      tiles.push({
        label: 'Current account',
        value: fmtBopUSD(ca),
        sub: bopQ + ' &middot; RBZ Balance of Payments',
        meta: ca == null ? '' :
          '<span class="econ-stat-delta ' + (ca >= 0 ? 'up' : 'down') + '">' +
          (ca >= 0 ? '▲ surplus' : '▼ deficit') + '</span>',
      });

      // Remittances trailing 4 quarters
      var sum4 = 0, count4 = 0;
      for (var i = Math.max(0, lastBop - 3); i <= lastBop; i++) {
        var v = bop.series.personal_transfers[i];
        if (v != null) { sum4 += v; count4++; }
      }
      tiles.push({
        label: 'Diaspora remittances (4q)',
        value: count4 ? fmtBopUSD(sum4) : '—',
        sub: 'Trailing four quarters &middot; RBZ',
        meta: '',
      });
    }

    el.innerHTML = tiles.map(function (t) {
      return '<div class="econ-stat-card">' +
        '<p class="econ-stat-label">' + t.label + '</p>' +
        '<p class="econ-stat-value">' + t.value + '</p>' +
        '<p class="econ-stat-sub">' + t.sub + '</p>' +
        (t.meta ? '<p class="econ-stat-meta">' + t.meta + '</p>' : '') +
        '</div>';
    }).join('');
  }

  // ── CHAPTER 1 — GDP composition ──────────────────────────
  var ch1State = { period: 'last4', chartType: 'latest', tableFilter: '',
                   tableSort: { col: 'value', dir: 'desc' } };
  var ch1Chart = null;

  function ch1Slice(gdp) {
    var n = gdp.quarters.length;
    var b = gdp.break_index;
    if (ch1State.period === 'last4') return { start: Math.max(0, n - 4), end: n, breakIdx: -1 };
    if (ch1State.period === 'post')  return { start: b, end: n, breakIdx: -1 };
    return { start: 0, end: n, breakIdx: b };
  }

  function ch1Render(gdp) {
    if (ch1Chart) { ch1Chart.destroy(); ch1Chart = null; }
    var canvas = document.getElementById('ch1Chart');
    if (!canvas) return;
    var ctx = canvas.getContext('2d');
    var slice = ch1Slice(gdp);

    if (ch1State.chartType === 'latest') {
      var lastIdx = gdp.quarters.length - 1;
      var pairs = gdp.sector_order.map(function (n) {
        return { name: n, val: gdp.sectors[n][lastIdx] };
      }).sort(function (a, b) { return b.val - a.val; });
      ch1Chart = new Chart(ctx, {
        type: 'bar',
        data: {
          labels: pairs.map(function (p) { return shortSectorName(p.name); }),
          datasets: [{
            label: gdp.quarters[lastIdx],
            data: pairs.map(function (p) { return p.val; }),
            backgroundColor: SECTOR_PALETTE[0],
            borderWidth: 0,
          }],
        },
        options: {
          indexAxis: 'y', responsive: true, maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
            tooltip: {
              callbacks: {
                label: function (c) { return fmtUSD(c.parsed.x); },
                title: function (i) { return i[0].label; },
              },
            },
          },
          scales: {
            x: { ticks: { callback: function (v) { return fmtUSD(v); } },
                 grid: { color: 'rgba(0,0,0,0.05)' }, beginAtZero: true },
            y: { grid: { display: false } },
          },
        },
      });
    } else {
      // stacked or line over time (top 6 sectors)
      var top6 = gdp.sector_order.slice(0, 6);
      var labels = gdp.quarters.slice(slice.start, slice.end);
      var datasets = top6.map(function (name, i) {
        var color = SECTOR_PALETTE[i % SECTOR_PALETTE.length];
        var arr = gdp.sectors[name].slice(slice.start, slice.end);
        return {
          label: shortSectorName(name),
          data: arr,
          borderColor: color,
          backgroundColor: ch1State.chartType === 'stacked'
            ? hexA(color, 0.55) : color,
          fill: ch1State.chartType === 'stacked',
          tension: 0.25, pointRadius: 1, pointHoverRadius: 4, borderWidth: 2,
        };
      });
      var isStacked = ch1State.chartType === 'stacked';
      ch1Chart = new Chart(ctx, {
        type: 'line',
        data: { labels: labels, datasets: datasets },
        options: {
          responsive: true, maintainAspectRatio: false,
          interaction: { mode: 'index', intersect: false },
          plugins: {
            legend: { position: 'bottom', labels: { boxWidth: 10, padding: 8 } },
            tooltip: { callbacks: { label: function (c) {
              return c.dataset.label + ': ' + fmtUSD(c.parsed.y); } } },
          },
          scales: {
            x: { grid: { display: false },
                 ticks: { maxRotation: 45, autoSkip: true, maxTicksLimit: 14 },
                 stacked: isStacked },
            y: { stacked: isStacked, beginAtZero: true,
                 ticks: { callback: function (v) { return fmtUSD(v); } },
                 grid: { color: 'rgba(0,0,0,0.05)' } },
          },
        },
        plugins: slice.breakIdx >= 0
          ? [breakLinePlugin(slice.breakIdx - slice.start, 'Re-based 2024 Q1')]
          : [],
      });
    }
  }

  function hexA(hex, alpha) {
    var h = hex.replace('#', '');
    var r = parseInt(h.substring(0, 2), 16);
    var g = parseInt(h.substring(2, 4), 16);
    var b = parseInt(h.substring(4, 6), 16);
    return 'rgba(' + r + ',' + g + ',' + b + ',' + alpha + ')';
  }

  // Sector ranking table — sortable, searchable, latest-quarter snapshot.
  function ch1RenderTable(gdp) {
    var tableBody = document.getElementById('ch1SectorTableBody');
    var tableQuarterEl = document.getElementById('ch1TableQuarter');
    if (!tableBody) return;
    var lastIdx = gdp.quarters.length - 1;
    var quarter = gdp.quarters[lastIdx];
    var totalLatest = gdp.aggregates['GDP at Market Prices'][lastIdx];
    if (tableQuarterEl) tableQuarterEl.textContent = quarter;

    var rows = gdp.sector_order.map(function (name) {
      var val = gdp.sectors[name][lastIdx];
      var yearAgo = gdp.sectors[name][lastIdx - 4];
      var yoy = yearAgo ? ((val - yearAgo) / yearAgo) * 100 : null;
      var share = totalLatest ? (val / totalLatest) * 100 : 0;
      return { name: name, value: val, share: share, yoy: yoy };
    });

    var q = ch1State.tableFilter.toLowerCase();
    if (q) rows = rows.filter(function (r) { return r.name.toLowerCase().indexOf(q) !== -1; });

    var sortCol = ch1State.tableSort.col;
    var dir = ch1State.tableSort.dir === 'asc' ? 1 : -1;
    rows.sort(function (a, b) {
      var av, bv;
      if (sortCol === 'name') { av = a.name; bv = b.name; }
      else if (sortCol === 'rank') { av = b.value; bv = a.value; }
      else { av = a[sortCol] == null ? -Infinity : a[sortCol];
             bv = b[sortCol] == null ? -Infinity : b[sortCol]; }
      if (av < bv) return -1 * dir;
      if (av > bv) return 1 * dir;
      return 0;
    });

    tableBody.innerHTML = rows.map(function (r, i) {
      var yoyDisp = '<span class="gdp-yoy-flat">—</span>';
      if (r.yoy != null) {
        var cls = r.yoy > 0.05 ? 'gdp-yoy-up' : r.yoy < -0.05 ? 'gdp-yoy-down' : 'gdp-yoy-flat';
        var arrow = r.yoy > 0.05 ? '▲' : r.yoy < -0.05 ? '▼' : '';
        yoyDisp = '<span class="' + cls + '">' + arrow + ' ' + fmtPct(Math.abs(r.yoy), false) + '</span>';
      }
      return '<tr>' +
        '<td class="gdp-num">' + (i + 1) + '</td>' +
        '<td>' + escapeHtml(r.name) + '</td>' +
        '<td class="gdp-num">' + fmtUSD(r.value) + '</td>' +
        '<td class="gdp-num">' + fmtPct(r.share, false) + '</td>' +
        '<td class="gdp-num">' + yoyDisp + '</td>' +
      '</tr>';
    }).join('');

    document.querySelectorAll('#ch1SectorTable .gdp-th-sortable').forEach(function (th) {
      th.classList.remove('sorted-asc', 'sorted-desc');
      if (th.getAttribute('data-sort') === ch1State.tableSort.col) {
        th.classList.add(ch1State.tableSort.dir === 'asc' ? 'sorted-asc' : 'sorted-desc');
      }
    });
  }

  function ch1Pullquote(gdp) {
    if (!gdp || !gdp.quarters) return;
    var el = document.getElementById('ch1Pull');
    var lastIdx = gdp.quarters.length - 1;
    var quarter = gdp.quarters[lastIdx];
    var totalLatest = gdp.aggregates['GDP at Market Prices'][lastIdx];
    var top = null;
    gdp.sector_order.forEach(function (n) {
      var v = gdp.sectors[n][lastIdx];
      if (!top || v > top.val) top = { name: n, val: v };
    });
    var share = top && totalLatest ? (top.val / totalLatest) * 100 : 0;
    el.innerHTML = '“' + shortSectorName(top.name) + '” contributed ' +
      '<strong>' + fmtUSD(top.val) + '</strong> in ' + quarter +
      ' — <strong>' + fmtPct(share, false) + '</strong> of Zimbabwe’s GDP.';
  }

  // ── CHAPTER 2 — Trade gap ─────────────────────────────────
  function ch2Render(bop) {
    var canvas = document.getElementById('ch2Chart');
    if (!canvas) return;
    var ctx = canvas.getContext('2d');
    var quarters = bop.quarters;
    var exports = bop.series.exports_goods;
    var imports = bop.series.imports_goods;

    new Chart(ctx, {
      type: 'line',
      data: {
        labels: quarters,
        datasets: [
          { label: 'Imports of goods',
            data: imports,
            borderColor: COLOR_ACCENT,
            backgroundColor: COLOR_FILL_RED,
            fill: '+1', tension: 0.25, pointRadius: 2, borderWidth: 2 },
          { label: 'Exports of goods',
            data: exports,
            borderColor: COLOR_GREEN,
            backgroundColor: COLOR_FILL_GREEN,
            fill: false, tension: 0.25, pointRadius: 2, borderWidth: 2 },
        ],
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: { position: 'bottom', labels: { boxWidth: 12, padding: 10 } },
          tooltip: { callbacks: { label: function (c) {
            return c.dataset.label + ': ' + fmtBopUSD(c.parsed.y);
          } } },
          subtitle: { display: false },
        },
        scales: {
          x: { grid: { display: false },
               ticks: { maxRotation: 45, autoSkip: true, maxTicksLimit: 14 } },
          y: { ticks: { callback: function (v) { return fmtBopUSD(v); } },
               grid: { color: 'rgba(0,0,0,0.05)' } },
        },
      },
    });
  }

  function ch2Pullquote(bop) {
    var el = document.getElementById('ch2Pull');
    if (!el || !bop) return;
    var n = bop.quarters.length;
    var exp = bop.series.exports_goods;
    var imp = bop.series.imports_goods;
    var gap = imp[n - 1] - exp[n - 1];
    el.innerHTML = 'In ' + bop.quarters[n - 1] + ', Zimbabwe imported <strong>' +
      fmtBopUSD(imp[n - 1]) + '</strong> of goods and exported <strong>' +
      fmtBopUSD(exp[n - 1]) + '</strong> — a gap of <strong>' +
      fmtBopUSD(Math.abs(gap)) + '</strong>.';
  }

  // ── CHAPTER 3 — Remittances ──────────────────────────────
  function ch3Render(bop) {
    var canvas = document.getElementById('ch3Chart');
    if (!canvas) return;
    var ctx = canvas.getContext('2d');
    var quarters = bop.quarters;
    var pt = bop.series.personal_transfers;

    new Chart(ctx, {
      type: 'bar',
      data: {
        labels: quarters,
        datasets: [{
          label: 'Personal transfers (remittances)',
          data: pt,
          backgroundColor: COLOR_GREEN,
          borderColor: COLOR_GREEN,
          borderWidth: 0,
        }],
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: { callbacks: { label: function (c) {
            return fmtBopUSD(c.parsed.y); } } },
        },
        scales: {
          x: { grid: { display: false },
               ticks: { maxRotation: 45, autoSkip: true, maxTicksLimit: 14 } },
          y: { ticks: { callback: function (v) { return fmtBopUSD(v); } },
               grid: { color: 'rgba(0,0,0,0.05)' }, beginAtZero: true },
        },
      },
    });
  }

  function ch3Pullquote(bop) {
    var el = document.getElementById('ch3Pull');
    if (!el || !bop) return;
    var n = bop.quarters.length;
    var pt = bop.series.personal_transfers;
    var latest = pt[n - 1];
    var sum4 = 0, count = 0;
    for (var i = Math.max(0, n - 4); i < n; i++) {
      if (pt[i] != null) { sum4 += pt[i]; count++; }
    }
    el.innerHTML = 'Diaspora Zimbabweans sent home <strong>' +
      fmtBopUSD(latest) + '</strong> in ' + bop.quarters[n - 1] +
      '. Over the trailing four quarters, <strong>' + fmtBopUSD(sum4) +
      '</strong> in officially-recorded remittances flowed into the country.';
  }

  // ── CHAPTER 4 — Mining vs Agriculture ─────────────────────
  function ch4Render(gdp) {
    var canvas = document.getElementById('ch4Chart');
    if (!canvas) return;
    var ctx = canvas.getContext('2d');
    var agri = gdp.sectors['Agiculture, Hunting and Fishing and forestry'];
    var mining = gdp.sectors['Mining and quarrying'];

    new Chart(ctx, {
      type: 'line',
      data: {
        labels: gdp.quarters,
        datasets: [
          { label: 'Mining & quarrying', data: mining,
            borderColor: COLOR_AMBER, backgroundColor: COLOR_AMBER,
            tension: 0.25, pointRadius: 2, borderWidth: 2.5 },
          { label: 'Agriculture & forestry', data: agri,
            borderColor: COLOR_GREEN, backgroundColor: COLOR_GREEN,
            tension: 0.25, pointRadius: 2, borderWidth: 2.5 },
        ],
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: { position: 'bottom', labels: { boxWidth: 12, padding: 10 } },
          tooltip: { callbacks: { label: function (c) {
            return c.dataset.label + ': ' + fmtUSD(c.parsed.y); } } },
        },
        scales: {
          x: { grid: { display: false },
               ticks: { maxRotation: 45, autoSkip: true, maxTicksLimit: 14 } },
          y: { ticks: { callback: function (v) { return fmtUSD(v); } },
               grid: { color: 'rgba(0,0,0,0.05)' }, beginAtZero: true },
        },
      },
      plugins: gdp.break_index >= 0
        ? [breakLinePlugin(gdp.break_index, 'Re-based 2024 Q1')]
        : [],
    });
  }

  function ch4Pullquote(gdp) {
    var el = document.getElementById('ch4Pull');
    if (!el || !gdp) return;
    var lastIdx = gdp.quarters.length - 1;
    var quarter = gdp.quarters[lastIdx];
    var mining = gdp.sectors['Mining and quarrying'][lastIdx];
    var agri = gdp.sectors['Agiculture, Hunting and Fishing and forestry'][lastIdx];
    var diff = mining - agri;
    var bigger = mining > agri ? 'Mining' : 'Agriculture';
    el.innerHTML = 'In ' + quarter + ', mining produced <strong>' + fmtUSD(mining) +
      '</strong> and agriculture <strong>' + fmtUSD(agri) +
      '</strong> — <strong>' + bigger + '</strong> led by ' + fmtUSD(Math.abs(diff)) + '.';
  }

  // ── CHAPTER 5 — Services rising (stacked top 6) ──────────
  function ch5Render(gdp) {
    var canvas = document.getElementById('ch5Chart');
    if (!canvas) return;
    var ctx = canvas.getContext('2d');
    var top6 = gdp.sector_order.slice(0, 6);
    var datasets = top6.map(function (name, i) {
      var color = SECTOR_PALETTE[i % SECTOR_PALETTE.length];
      return {
        label: shortSectorName(name),
        data: gdp.sectors[name],
        borderColor: color,
        backgroundColor: hexA(color, 0.65),
        fill: true, tension: 0.25, pointRadius: 0, borderWidth: 1,
      };
    });
    new Chart(ctx, {
      type: 'line',
      data: { labels: gdp.quarters, datasets: datasets },
      options: {
        responsive: true, maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: { position: 'bottom', labels: { boxWidth: 10, padding: 8 } },
          tooltip: { callbacks: { label: function (c) {
            return c.dataset.label + ': ' + fmtUSD(c.parsed.y); } } },
        },
        scales: {
          x: { grid: { display: false }, stacked: true,
               ticks: { maxRotation: 45, autoSkip: true, maxTicksLimit: 14 } },
          y: { stacked: true, beginAtZero: true,
               ticks: { callback: function (v) { return fmtUSD(v); } },
               grid: { color: 'rgba(0,0,0,0.05)' } },
        },
      },
      plugins: gdp.break_index >= 0
        ? [breakLinePlugin(gdp.break_index, 'Re-based 2024 Q1')]
        : [],
    });
  }

  function ch5Pullquote(gdp) {
    var el = document.getElementById('ch5Pull');
    if (!el || !gdp) return;
    var lastIdx = gdp.quarters.length - 1;
    var quarter = gdp.quarters[lastIdx];
    var totalLatest = gdp.aggregates['GDP at Market Prices'][lastIdx];
    var top6 = gdp.sector_order.slice(0, 6);
    var top6Sum = top6.reduce(function (s, n) { return s + gdp.sectors[n][lastIdx]; }, 0);
    var share = totalLatest ? (top6Sum / totalLatest) * 100 : 0;
    el.innerHTML = 'The top six sectors together produced <strong>' + fmtUSD(top6Sum) +
      '</strong> in ' + quarter + ' — <strong>' + fmtPct(share, false) +
      '</strong> of all GDP. The other thirteen tracked sectors share what is left.';
  }

  // ── CHAPTER 6 — Current account + missing money ──────────
  function ch6Render(bop) {
    var canvas = document.getElementById('ch6Chart');
    if (!canvas) return;
    var ctx = canvas.getContext('2d');
    new Chart(ctx, {
      type: 'line',
      data: {
        labels: bop.quarters,
        datasets: [
          { label: 'Current account',
            data: bop.series.current_account,
            borderColor: COLOR_BLUE,
            backgroundColor: COLOR_FILL_BLUE,
            fill: 'origin', tension: 0.25, pointRadius: 2, borderWidth: 2 },
          { label: 'Net errors & omissions',
            data: bop.series.net_errors_omissions,
            borderColor: COLOR_ACCENT,
            backgroundColor: COLOR_ACCENT,
            fill: false, tension: 0.25, pointRadius: 2, borderWidth: 2,
            borderDash: [4, 3] },
        ],
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: { position: 'bottom', labels: { boxWidth: 12, padding: 10 } },
          tooltip: { callbacks: { label: function (c) {
            return c.dataset.label + ': ' + fmtBopUSD(c.parsed.y); } } },
        },
        scales: {
          x: { grid: { display: false },
               ticks: { maxRotation: 45, autoSkip: true, maxTicksLimit: 14 } },
          y: { ticks: { callback: function (v) { return fmtBopUSD(v); } },
               grid: { color: 'rgba(0,0,0,0.05)' } },
        },
      },
    });
  }

  function ch6Pullquote(bop) {
    var el = document.getElementById('ch6Pull');
    if (!el || !bop) return;
    // Walk back from the end to find the latest quarter with real
    // (non-null, non-zero) data for Net Errors & Omissions — ZimStat
    // ships a 0 placeholder for the latest quarter before it is final.
    var ne = bop.series.net_errors_omissions;
    var idx = ne.length - 1;
    while (idx > 0 && (ne[idx] == null || ne[idx] === 0)) idx--;
    var quarter = bop.quarters[idx];
    var ca = bop.series.current_account[idx];
    el.innerHTML = 'In ' + quarter + ', the official current account printed <strong>' +
      fmtBopUSD(ca) + '</strong>. The unrecorded balancing item — “Net Errors &amp; ' +
      'Omissions” — printed <strong>' + fmtBopUSD(ne[idx]) + '</strong>.';
  }

  // ── Break note + period controls (Chapter 1 only) ─────────
  function bindCh1Controls(gdp) {
    var breakNoteEl = document.getElementById('ch1BreakNote');
    if (breakNoteEl) breakNoteEl.textContent = gdp.break_note;

    var periodGroup = document.getElementById('ch1PeriodGroup');
    if (periodGroup) {
      periodGroup.addEventListener('click', function (e) {
        var btn = e.target.closest('.econ-pill');
        if (!btn) return;
        periodGroup.querySelectorAll('.econ-pill').forEach(function (b) {
          b.classList.remove('active');
        });
        btn.classList.add('active');
        ch1State.period = btn.getAttribute('data-period');
        ch1Render(gdp);
      });
    }
    var typeSel = document.getElementById('ch1ChartType');
    if (typeSel) {
      typeSel.addEventListener('change', function () {
        ch1State.chartType = typeSel.value;
        // Latest view is a single-quarter ranking — hide the period pill group.
        var pg = document.getElementById('ch1PeriodGroup');
        if (pg) {
          pg.style.opacity = ch1State.chartType === 'latest' ? 0.4 : 1;
          pg.style.pointerEvents = ch1State.chartType === 'latest' ? 'none' : '';
        }
        ch1Render(gdp);
      });
    }
    document.querySelectorAll('#ch1SectorTable .gdp-th-sortable').forEach(function (th) {
      th.addEventListener('click', function () {
        var col = th.getAttribute('data-sort');
        if (ch1State.tableSort.col === col) {
          ch1State.tableSort.dir = ch1State.tableSort.dir === 'asc' ? 'desc' : 'asc';
        } else {
          ch1State.tableSort.col = col;
          ch1State.tableSort.dir = col === 'name' ? 'asc' : 'desc';
        }
        ch1RenderTable(gdp);
      });
    });
    var search = document.getElementById('ch1SectorSearch');
    if (search) {
      search.addEventListener('input', function () {
        ch1State.tableFilter = search.value;
        ch1RenderTable(gdp);
      });
    }
  }

  // ── Bootstrapping ─────────────────────────────────────────
  function bail(msg) {
    var article = document.getElementById('econNarrative');
    if (article) {
      article.innerHTML = '<p style="text-align:center;color:#999;padding:60px 20px;' +
        'font-family:Inter,sans-serif;font-size:0.9em">' +
        'Economic data unavailable: ' + escapeHtml(msg) + '</p>';
    }
    console.warn('economy.js bail:', msg);
  }

  Promise.all([
    fetch('data/gdp-zimbabwe-quarterly.json', { cache: 'no-cache' }).then(function (r) {
      if (!r.ok) throw new Error('GDP HTTP ' + r.status);
      return r.json();
    }),
    fetch('data/zimstat-bop-quarterly.json', { cache: 'no-cache' }).then(function (r) {
      if (!r.ok) throw new Error('BoP HTTP ' + r.status);
      return r.json();
    }),
  ]).then(function (results) {
    var gdp = results[0];
    var bop = results[1];

    renderHero(gdp, bop);

    // Chapter 1 — GDP composition + table + pullquote
    ch1Pullquote(gdp);
    ch1Render(gdp);
    ch1RenderTable(gdp);
    bindCh1Controls(gdp);

    // Chapter 2 — trade gap
    ch2Pullquote(bop);
    ch2Render(bop);

    // Chapter 3 — remittances
    ch3Pullquote(bop);
    ch3Render(bop);

    // Chapter 4 — mining vs agri
    ch4Pullquote(gdp);
    ch4Render(gdp);

    // Chapter 5 — services rising
    ch5Pullquote(gdp);
    ch5Render(gdp);

    // Chapter 6 — current account + missing money
    ch6Pullquote(bop);
    ch6Render(bop);
  }).catch(function (err) {
    bail(err.message || String(err));
  });
})();
