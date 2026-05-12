/**
 * The Mutapa Times — Economy narrative.
 *
 * Loads two ZimStat datasets in parallel:
 *   - data/gdp-zimbabwe-quarterly.json   (quarterly GDP by sector)
 *   - data/zimstat-bop-quarterly.json    (quarterly Balance of Payments)
 *
 * All data viz is rendered with Google Charts (corechart package).
 * Zero italics anywhere. Two fonts only: Playfair Display for the
 * page headlines (handled in CSS) and Inter for everything else,
 * which Google Charts inherits via fontName option.
 */
(function () {
  if (typeof google === 'undefined' || !google.charts) {
    console.warn('Google Charts loader not present — economy page will show the narrative only.');
    return;
  }

  // ── Brand palette ─────────────────────────────────────────
  var COLOR_ACCENT  = '#c41e1e';
  var COLOR_GREEN   = '#1a7f37';
  var COLOR_BLUE    = '#1f6feb';
  var COLOR_AMBER   = '#bf8700';
  var COLOR_INK     = '#1a1a1a';
  var COLOR_MUTED   = '#5f5c54';
  var COLOR_LIGHT   = '#a0a0a0';
  var COLOR_RULE    = '#e6e6e6';

  var SECTOR_PALETTE = [
    '#c41e1e', '#1f6feb', '#1a7f37', '#bf8700', '#8957e5', '#0a7e8c',
    '#6639ba', '#cf222e', '#0550ae', '#9a6700', '#116329', '#a01818',
    '#3f3f8c', '#7d4900', '#0969da', '#2da44e', '#bf8700', '#5d3a9b',
    '#a40e26', '#cf222e',
  ];

  // ── Google Charts base options applied to every chart ────
  // Inter everywhere, restrained gridlines, no chrome.
  function baseOptions(overrides) {
    var opts = {
      fontName: 'Inter',
      fontSize: 12,
      backgroundColor: { fill: 'transparent' },
      chartArea: { left: 80, top: 24, right: 28, bottom: 64,
                   width: '88%', height: '76%' },
      legend: {
        position: 'bottom',
        alignment: 'start',
        textStyle: { color: COLOR_INK, fontName: 'Inter', fontSize: 12 },
      },
      tooltip: {
        textStyle: { fontName: 'Inter', fontSize: 12, color: COLOR_INK },
        showColorCode: true,
      },
      hAxis: {
        textStyle: { color: COLOR_MUTED, fontName: 'Inter', fontSize: 11 },
        gridlines: { color: 'transparent' },
        baselineColor: COLOR_RULE,
      },
      vAxis: {
        textStyle: { color: COLOR_MUTED, fontName: 'Inter', fontSize: 11 },
        gridlines: { color: COLOR_RULE, count: 5 },
        minorGridlines: { color: 'transparent' },
        baselineColor: COLOR_RULE,
        format: 'short',
      },
      colors: [COLOR_ACCENT, COLOR_BLUE, COLOR_GREEN, COLOR_AMBER,
               '#8957e5', '#0a7e8c'],
    };
    return Object.assign(opts, overrides || {});
  }

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
  function fmtBopUSD(mn) { return mn == null ? '—' : fmtUSD(mn * 1e6); }
  function fmtPct(n, signed) {
    if (n == null || isNaN(n)) return '—';
    return (n >= 0 && signed ? '+' : '') + n.toFixed(1) + '%';
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

  // ── Hero stat tiles ──────────────────────────────────────
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
      var nq = bop.quarters.length;
      var bopQ = bop.quarters[nq - 1];
      var ca = bop.series.current_account[nq - 1];
      tiles.push({
        label: 'Current account',
        value: fmtBopUSD(ca),
        sub: bopQ + ' &middot; RBZ Balance of Payments',
        meta: ca == null ? '' :
          '<span class="econ-stat-delta ' + (ca >= 0 ? 'up' : 'down') + '">' +
          (ca >= 0 ? '▲ surplus' : '▼ deficit') + '</span>',
      });
      var sum4 = 0;
      for (var i = Math.max(0, nq - 4); i < nq; i++) {
        var v = bop.series.personal_transfers[i];
        if (v != null) sum4 += v;
      }
      tiles.push({
        label: 'Diaspora remittances (4q)',
        value: fmtBopUSD(sum4),
        sub: 'Trailing four quarters &middot; RBZ',
        meta: '',
      });
    }
    // Use the unified .page-hero-stat vocabulary so this slot looks the
    // same on every section page (economy, fx, property, jobs).
    el.innerHTML = tiles.map(function (t) {
      return '<div class="page-hero-stat">' +
        '<p class="page-hero-stat-label">' + t.label + '</p>' +
        '<p class="page-hero-stat-value">' + escapeHtml(t.value) + '</p>' +
        '<p class="page-hero-stat-sub">' + t.sub + '</p>' +
        (t.meta ? '<p class="page-hero-stat-sub">' + t.meta + '</p>' : '') +
        '</div>';
    }).join('');
  }

  // ── Window resize → redraw all known charts ──────────────
  var registeredCharts = [];
  function registerRedraw(fn) {
    registeredCharts.push(fn);
  }
  var resizeTimer = null;
  window.addEventListener('resize', function () {
    if (resizeTimer) clearTimeout(resizeTimer);
    resizeTimer = setTimeout(function () {
      registeredCharts.forEach(function (fn) { try { fn(); } catch (e) {} });
    }, 180);
  });

  // ── CHAPTER 1 — GDP composition ──────────────────────────
  var ch1State = { period: 'last4', chartType: 'latest', tableFilter: '',
                   tableSort: { col: 'value', dir: 'desc' } };

  function ch1Slice(gdp) {
    var n = gdp.quarters.length;
    var b = gdp.break_index;
    if (ch1State.period === 'last4') return { start: Math.max(0, n - 4), end: n };
    if (ch1State.period === 'post')  return { start: b, end: n };
    return { start: 0, end: n };
  }

  function ch1Render(gdp) {
    var div = document.getElementById('ch1Chart');
    if (!div) return;

    if (ch1State.chartType === 'latest') {
      var lastIdx = gdp.quarters.length - 1;
      var pairs = gdp.sector_order.map(function (n) {
        return { name: n, val: gdp.sectors[n][lastIdx] };
      }).sort(function (a, b) { return b.val - a.val; });

      var rows = [['Sector', gdp.quarters[lastIdx],
                   { role: 'style' },
                   { role: 'annotation' }]];
      pairs.forEach(function (p, i) {
        rows.push([
          shortSectorName(p.name),
          p.val,
          i === 0 ? COLOR_ACCENT : '#c8c4b8',
          fmtUSD(p.val),
        ]);
      });
      var data = google.visualization.arrayToDataTable(rows);

      var chart = new google.visualization.BarChart(div);
      chart.draw(data, baseOptions({
        chartArea: { left: 160, top: 8, right: 80, bottom: 36, width: '70%', height: '88%' },
        legend: { position: 'none' },
        hAxis: {
          textStyle: { color: COLOR_MUTED, fontName: 'Inter', fontSize: 11 },
          gridlines: { color: COLOR_RULE, count: 5 },
          baselineColor: COLOR_RULE,
          format: 'short',
        },
        vAxis: {
          textStyle: { color: COLOR_INK, fontName: 'Inter', fontSize: 12 },
          gridlines: { color: 'transparent' },
          baselineColor: COLOR_RULE,
        },
        annotations: {
          alwaysOutside: true,
          textStyle: { fontName: 'Inter', fontSize: 11, color: COLOR_INK, bold: true },
        },
        bar: { groupWidth: '78%' },
      }));
    } else {
      // stacked or line
      var slice = ch1Slice(gdp);
      var top6 = gdp.sector_order.slice(0, 6);
      var labels = gdp.quarters.slice(slice.start, slice.end);
      var header = ['Quarter'].concat(top6.map(shortSectorName));
      var rows2 = [header];
      labels.forEach(function (q, i) {
        var row = [q];
        top6.forEach(function (name) {
          row.push(gdp.sectors[name][slice.start + i]);
        });
        rows2.push(row);
      });
      var data2 = google.visualization.arrayToDataTable(rows2);

      var isStacked = ch1State.chartType === 'stacked';
      var ChartCtor = isStacked
        ? google.visualization.AreaChart
        : google.visualization.LineChart;
      var chart2 = new ChartCtor(div);
      chart2.draw(data2, baseOptions({
        isStacked: isStacked,
        areaOpacity: 0.85,
        lineWidth: 2,
        pointSize: 0,
        colors: SECTOR_PALETTE.slice(0, 6),
        vAxis: {
          textStyle: { color: COLOR_MUTED, fontName: 'Inter', fontSize: 11 },
          gridlines: { color: COLOR_RULE, count: 5 },
          baselineColor: COLOR_RULE,
          format: 'short',
          minValue: 0,
        },
      }));
    }
  }

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
    var el = document.getElementById('ch1Pull');
    if (!el || !gdp) return;
    var lastIdx = gdp.quarters.length - 1;
    var quarter = gdp.quarters[lastIdx];
    var totalLatest = gdp.aggregates['GDP at Market Prices'][lastIdx];
    var top = null;
    gdp.sector_order.forEach(function (n) {
      var v = gdp.sectors[n][lastIdx];
      if (!top || v > top.val) top = { name: n, val: v };
    });
    var share = top && totalLatest ? (top.val / totalLatest) * 100 : 0;
    el.innerHTML = shortSectorName(top.name) + ' contributed <strong>' +
      fmtUSD(top.val) + '</strong> in ' + quarter + ', or <strong>' +
      fmtPct(share, false) + '</strong> of Zimbabwe&rsquo;s total GDP.';
  }

  // ── CHAPTER 2 — Trade gap (LineChart + shaded gap) ───────
  function ch2Render(bop) {
    var div = document.getElementById('ch2Chart');
    if (!div) return;
    var rows = [['Quarter', 'Exports of goods', 'Imports of goods']];
    bop.quarters.forEach(function (q, i) {
      rows.push([q,
                 (bop.series.exports_goods[i] || 0) * 1e6,
                 (bop.series.imports_goods[i] || 0) * 1e6]);
    });
    var data = google.visualization.arrayToDataTable(rows);
    var chart = new google.visualization.AreaChart(div);
    chart.draw(data, baseOptions({
      colors: [COLOR_GREEN, COLOR_ACCENT],
      areaOpacity: 0.15,
      lineWidth: 2.5,
      pointSize: 0,
      isStacked: false,
      legend: { position: 'bottom', alignment: 'start',
                textStyle: { color: COLOR_INK, fontName: 'Inter', fontSize: 12 } },
    }));
  }

  function ch2Pullquote(bop) {
    var el = document.getElementById('ch2Pull');
    if (!el || !bop) return;
    var n = bop.quarters.length;
    var exp = bop.series.exports_goods[n - 1];
    var imp = bop.series.imports_goods[n - 1];
    var gap = imp - exp;
    var kind = gap < 0 ? 'trade surplus' : 'trade deficit';
    el.innerHTML = 'In ' + bop.quarters[n - 1] + ', Zimbabwe exported <strong>' +
      fmtBopUSD(exp) + '</strong> and imported <strong>' + fmtBopUSD(imp) +
      '</strong> &mdash; a <strong>' + fmtBopUSD(Math.abs(gap)) + ' ' + kind + '</strong>.';
  }

  // ── CHAPTER 3 — Remittances (ColumnChart) ────────────────
  function ch3Render(bop) {
    var div = document.getElementById('ch3Chart');
    if (!div) return;
    var rows = [['Quarter', 'Personal transfers', { role: 'style' }]];
    var n = bop.quarters.length;
    bop.quarters.forEach(function (q, i) {
      var color = i >= n - 4 ? COLOR_GREEN : '#7eb98a';
      rows.push([q, (bop.series.personal_transfers[i] || 0) * 1e6, color]);
    });
    var data = google.visualization.arrayToDataTable(rows);
    var chart = new google.visualization.ColumnChart(div);
    chart.draw(data, baseOptions({
      legend: { position: 'none' },
      bar: { groupWidth: '70%' },
      hAxis: {
        textStyle: { color: COLOR_MUTED, fontName: 'Inter', fontSize: 11 },
        gridlines: { color: 'transparent' },
        baselineColor: COLOR_RULE,
        showTextEvery: 4,
      },
    }));
  }

  function ch3Pullquote(bop) {
    var el = document.getElementById('ch3Pull');
    if (!el || !bop) return;
    var n = bop.quarters.length;
    var pt = bop.series.personal_transfers;
    var latest = pt[n - 1];
    var sum4 = 0;
    for (var i = Math.max(0, n - 4); i < n; i++) if (pt[i] != null) sum4 += pt[i];
    el.innerHTML = 'Diaspora Zimbabweans sent home <strong>' + fmtBopUSD(latest) +
      '</strong> in ' + bop.quarters[n - 1] + '. Over the trailing four quarters: <strong>' +
      fmtBopUSD(sum4) + '</strong>.';
  }

  // ── CHAPTER 4 — Mining vs Agriculture (LineChart) ────────
  function ch4Render(gdp) {
    var div = document.getElementById('ch4Chart');
    if (!div) return;
    var rows = [['Quarter', 'Mining', 'Agriculture']];
    gdp.quarters.forEach(function (q, i) {
      rows.push([
        q,
        gdp.sectors['Mining and quarrying'][i],
        gdp.sectors['Agiculture, Hunting and Fishing and forestry'][i],
      ]);
    });
    var data = google.visualization.arrayToDataTable(rows);
    var chart = new google.visualization.LineChart(div);
    chart.draw(data, baseOptions({
      colors: [COLOR_AMBER, COLOR_GREEN],
      lineWidth: 2.5,
      pointSize: 3,
      pointShape: 'circle',
      curveType: 'function',
    }));
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
      '</strong> and agriculture <strong>' + fmtUSD(agri) + '</strong>. <strong>' +
      bigger + '</strong> led by ' + fmtUSD(Math.abs(diff)) + '.';
  }

  // ── CHAPTER 5 — Services rising (stacked area) ───────────
  function ch5Render(gdp) {
    var div = document.getElementById('ch5Chart');
    if (!div) return;
    var top6 = gdp.sector_order.slice(0, 6);
    var rows = [['Quarter'].concat(top6.map(shortSectorName))];
    gdp.quarters.forEach(function (q, i) {
      var row = [q];
      top6.forEach(function (name) { row.push(gdp.sectors[name][i]); });
      rows.push(row);
    });
    var data = google.visualization.arrayToDataTable(rows);
    var chart = new google.visualization.AreaChart(div);
    chart.draw(data, baseOptions({
      isStacked: true,
      areaOpacity: 0.88,
      lineWidth: 0.5,
      pointSize: 0,
      colors: SECTOR_PALETTE.slice(0, 6),
      legend: { position: 'bottom', maxLines: 2,
                textStyle: { color: COLOR_INK, fontName: 'Inter', fontSize: 11 } },
      vAxis: {
        textStyle: { color: COLOR_MUTED, fontName: 'Inter', fontSize: 11 },
        gridlines: { color: COLOR_RULE, count: 5 },
        baselineColor: COLOR_RULE,
        format: 'short',
        minValue: 0,
      },
    }));
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
      '</strong> in ' + quarter + ' &mdash; <strong>' + fmtPct(share, false) +
      '</strong> of all GDP.';
  }

  // ── CHAPTER 6 — Current account + NE&O overlay ───────────
  function ch6Render(bop) {
    var div = document.getElementById('ch6Chart');
    if (!div) return;
    var rows = [['Quarter', 'Current account', 'Net errors & omissions']];
    bop.quarters.forEach(function (q, i) {
      rows.push([
        q,
        (bop.series.current_account[i] || 0) * 1e6,
        bop.series.net_errors_omissions[i] == null
          ? null
          : bop.series.net_errors_omissions[i] * 1e6,
      ]);
    });
    var data = google.visualization.arrayToDataTable(rows);
    var chart = new google.visualization.LineChart(div);
    chart.draw(data, baseOptions({
      colors: [COLOR_BLUE, COLOR_ACCENT],
      lineWidth: 2.5,
      pointSize: 3,
      series: { 1: { lineDashStyle: [4, 3] } },
      curveType: 'function',
    }));
  }

  function ch6Pullquote(bop) {
    var el = document.getElementById('ch6Pull');
    if (!el || !bop) return;
    var ne = bop.series.net_errors_omissions;
    var idx = ne.length - 1;
    while (idx > 0 && (ne[idx] == null || ne[idx] === 0)) idx--;
    var quarter = bop.quarters[idx];
    var ca = bop.series.current_account[idx];
    el.innerHTML = 'In ' + quarter + ', the official current account printed <strong>' +
      fmtBopUSD(ca) + '</strong>. The unrecorded balancing item printed <strong>' +
      fmtBopUSD(ne[idx]) + '</strong>.';
  }

  // ── Chapter 1 controls ────────────────────────────────────
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

  // ── Bootstrap ─────────────────────────────────────────────
  function bail(msg) {
    var article = document.getElementById('econNarrative');
    if (article) {
      article.innerHTML = '<p style="text-align:center;color:#999;padding:60px 20px;' +
        'font-family:Inter,sans-serif;font-size:0.9em">' +
        'Economic data unavailable: ' + escapeHtml(msg) + '</p>';
    }
    console.warn('economy.js bail:', msg);
  }

  function drawAll(gdp, bop) {
    renderHero(gdp, bop);

    ch1Pullquote(gdp); ch1Render(gdp); ch1RenderTable(gdp); bindCh1Controls(gdp);
    ch2Pullquote(bop); ch2Render(bop);
    ch3Pullquote(bop); ch3Render(bop);
    ch4Pullquote(gdp); ch4Render(gdp);
    ch5Pullquote(gdp); ch5Render(gdp);
    ch6Pullquote(bop); ch6Render(bop);

    // Register redraw callbacks for window resize.
    registerRedraw(function () { ch1Render(gdp); });
    registerRedraw(function () { ch2Render(bop); });
    registerRedraw(function () { ch3Render(bop); });
    registerRedraw(function () { ch4Render(gdp); });
    registerRedraw(function () { ch5Render(gdp); });
    registerRedraw(function () { ch6Render(bop); });
  }

  google.charts.load('current', { packages: ['corechart', 'bar'] });
  google.charts.setOnLoadCallback(function () {
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
      drawAll(results[0], results[1]);
    }).catch(function (err) {
      bail(err.message || String(err));
    });
  });
})();
