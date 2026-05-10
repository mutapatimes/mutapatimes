/**
 * GDP-by-sector dashboard (ZimStat quarterly).
 * State machine: period × chartType × series, plus a sortable sector table.
 *
 * Period:    all | post | pre | last4
 * ChartType: line | stacked | latest
 * Series:    total | top | all   (ignored when chartType = "latest")
 */
(function () {
  var DATA_URL = 'data/gdp-zimbabwe-quarterly.json';
  var canvas = document.getElementById('gdpChart');
  if (!canvas) return;

  var rangeLabel = document.getElementById('gdpRangeLabel');
  var breakNoteEl = document.getElementById('gdpBreakNote');
  var highlightsEl = document.getElementById('gdpHighlights');
  var periodGroup = document.getElementById('gdpPeriodGroup');
  var chartTypeSel = document.getElementById('gdpChartType');
  var seriesSel = document.getElementById('gdpSeries');
  var seriesGroup = document.getElementById('gdpSeriesGroup');
  var tableQuarterEl = document.getElementById('gdpTableQuarter');
  var tableBody = document.getElementById('gdpSectorTableBody');
  var tableHeaders = document.querySelectorAll('.gdp-th-sortable');
  var sectorSearch = document.getElementById('gdpSectorSearch');

  var PALETTE = [
    '#c0392b', '#1f6feb', '#2da44e', '#bf8700', '#8957e5',
    '#0969da', '#1a7f37', '#9a6700', '#6639ba', '#a40e26',
    '#0550ae', '#116329', '#cf222e', '#0a7e8c', '#7d4900',
    '#3f3f8c', '#a01818', '#1f6feb', '#2da44e', '#bf8700',
  ];

  var state = {
    period: 'all',
    chartType: 'line',
    series: 'total',
    tableSort: { col: 'value', dir: 'desc' },
    tableFilter: '',
  };

  var data = null;
  var chart = null;

  // ── Formatters ────────────────────────────────────────────
  function fmtUSD(n) {
    if (n == null || isNaN(n)) return '—';
    if (n >= 1e9) return '$' + (n / 1e9).toFixed(1) + 'B';
    if (n >= 1e6) return '$' + (n / 1e6).toFixed(1) + 'M';
    if (n >= 1e3) return '$' + (n / 1e3).toFixed(0) + 'K';
    return '$' + Math.round(n);
  }

  function fmtPct(n, signed) {
    if (n == null || isNaN(n)) return '—';
    var s = (n >= 0 && signed ? '+' : '') + n.toFixed(1) + '%';
    return s;
  }

  // ── Period filter — returns { start, end, breakIdx } ──────
  function periodSlice() {
    var n = data.quarters.length;
    var b = data.break_index;
    if (state.period === 'pre') return { start: 0, end: b, breakIdx: -1 };
    if (state.period === 'post') return { start: b, end: n, breakIdx: -1 };
    if (state.period === 'last4') return { start: Math.max(0, n - 4), end: n, breakIdx: -1 };
    // all
    return { start: 0, end: n, breakIdx: b };
  }

  function sliceArr(arr, start, end) { return arr.slice(start, end); }

  // ── Series picking ────────────────────────────────────────
  function seriesNames() {
    if (state.series === 'top') return data.sector_order.slice(0, 6);
    if (state.series === 'all') return data.sector_order.slice();
    return [];  // total — handled specially
  }

  // ── Build datasets ────────────────────────────────────────
  function lineDatasets(slice) {
    var datasets = [];
    var breakOffset = slice.breakIdx >= 0 ? slice.breakIdx - slice.start : -1;

    function addSeries(name, values, color, width) {
      var arr = sliceArr(values, slice.start, slice.end);
      if (breakOffset > 0 && breakOffset < arr.length) {
        // Two-segment with visual gap at the break
        var pre = arr.map(function (v, i) { return i < breakOffset ? v : null; });
        var post = arr.map(function (v, i) { return i >= breakOffset ? v : null; });
        datasets.push({
          label: name + ' (pre-2024)',
          data: pre,
          borderColor: color, backgroundColor: color,
          borderWidth: width, tension: 0.25,
          pointRadius: 2, pointHoverRadius: 5, spanGaps: false,
        });
        datasets.push({
          label: name + ' (post-2024)',
          data: post,
          borderColor: color, backgroundColor: color,
          borderWidth: width, tension: 0.25,
          pointRadius: 2, pointHoverRadius: 5, spanGaps: false,
        });
      } else {
        datasets.push({
          label: name,
          data: arr,
          borderColor: color, backgroundColor: color,
          borderWidth: width, tension: 0.25,
          pointRadius: 2, pointHoverRadius: 5,
        });
      }
    }

    if (state.series === 'total') {
      addSeries('GDP at Market Prices', data.aggregates['GDP at Market Prices'], '#c0392b', 3);
    } else {
      var names = seriesNames();
      names.forEach(function (n, i) {
        addSeries(n, data.sectors[n], PALETTE[i % PALETTE.length], 2);
      });
    }
    return datasets;
  }

  function stackedDatasets(slice) {
    // Stacked area uses the same series list as line, but fills under each.
    var names = state.series === 'total'
      ? data.sector_order.slice(0, 6)  // total doesn't make sense stacked → use top 6
      : seriesNames();

    return names.map(function (name, i) {
      var color = PALETTE[i % PALETTE.length];
      return {
        label: name,
        data: sliceArr(data.sectors[name], slice.start, slice.end),
        borderColor: color,
        backgroundColor: hexA(color, 0.6),
        fill: true,
        tension: 0.2,
        pointRadius: 0,
        pointHoverRadius: 4,
      };
    });
  }

  function hexA(hex, alpha) {
    var h = hex.replace('#', '');
    var r = parseInt(h.substring(0, 2), 16);
    var g = parseInt(h.substring(2, 4), 16);
    var b = parseInt(h.substring(4, 6), 16);
    return 'rgba(' + r + ',' + g + ',' + b + ',' + alpha + ')';
  }

  // ── Chart rendering ───────────────────────────────────────
  function destroyChart() { if (chart) { chart.destroy(); chart = null; } }

  function renderLineOrStacked() {
    var slice = periodSlice();
    var labels = data.quarters.slice(slice.start, slice.end);
    var datasets = state.chartType === 'stacked'
      ? stackedDatasets(slice)
      : lineDatasets(slice);
    var isStacked = state.chartType === 'stacked';
    var ctx = canvas.getContext('2d');

    chart = new Chart(ctx, {
      type: 'line',
      data: { labels: labels, datasets: datasets },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: {
            position: 'bottom',
            onClick: function (e, item, legend) {
              // Toggle paired pre/post halves together
              var ci = legend.chart;
              var name = item.text;
              ci.data.datasets.forEach(function (ds, idx) {
                var ns = ds.label.replace(' (pre-2024)', '').replace(' (post-2024)', '');
                if (ns === name) {
                  var meta = ci.getDatasetMeta(idx);
                  meta.hidden = meta.hidden === null ? !ci.data.datasets[idx].hidden : null;
                }
              });
              ci.update();
            },
            labels: {
              boxWidth: 10, boxHeight: 10, padding: 8,
              font: { size: 10, family: 'Inter, sans-serif' },
              generateLabels: function (chart) {
                var orig = Chart.defaults.plugins.legend.labels.generateLabels(chart);
                return orig
                  .filter(function (l) { return l.text.indexOf('(post-2024)') === -1; })
                  .map(function (l) { l.text = l.text.replace(' (pre-2024)', ''); return l; });
              },
            },
          },
          tooltip: {
            callbacks: {
              label: function (ctx) {
                var name = ctx.dataset.label
                  .replace(' (pre-2024)', '').replace(' (post-2024)', '');
                return name + ': ' + fmtUSD(ctx.parsed.y);
              },
            },
          },
        },
        scales: {
          x: {
            ticks: {
              font: { size: 10, family: 'Inter, sans-serif' },
              maxRotation: 45, minRotation: 45,
              autoSkip: true, maxTicksLimit: 14,
            },
            grid: { display: false },
            stacked: isStacked,
          },
          y: {
            ticks: {
              font: { size: 10, family: 'Inter, sans-serif' },
              callback: function (v) { return fmtUSD(v); },
            },
            grid: { color: 'rgba(0,0,0,0.05)' },
            beginAtZero: true,
            stacked: isStacked,
          },
        },
      },
      plugins: slice.breakIdx >= 0
        ? [breakLinePlugin(slice.breakIdx - slice.start)]
        : [],
    });
  }

  function renderLatest() {
    // Horizontal bar chart of all sectors for the latest quarter, ranked.
    var lastIdx = data.quarters.length - 1;
    var quarter = data.quarters[lastIdx];
    var sectors = data.sector_order.slice();
    var values = sectors.map(function (n) { return data.sectors[n][lastIdx]; });

    // Sort descending
    var paired = sectors.map(function (n, i) {
      return { name: n, val: values[i] };
    }).sort(function (a, b) { return b.val - a.val; });

    var labels = paired.map(function (p) { return shortName(p.name); });
    var vals = paired.map(function (p) { return p.val; });

    var ctx = canvas.getContext('2d');
    chart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          label: quarter,
          data: vals,
          backgroundColor: PALETTE[0],
          borderColor: PALETTE[0],
          borderWidth: 0,
        }],
      },
      options: {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: function (ctx) { return fmtUSD(ctx.parsed.x); },
              title: function (items) { return items[0].label; },
            },
          },
        },
        scales: {
          x: {
            ticks: {
              font: { size: 10, family: 'Inter, sans-serif' },
              callback: function (v) { return fmtUSD(v); },
            },
            grid: { color: 'rgba(0,0,0,0.05)' },
            beginAtZero: true,
          },
          y: {
            ticks: { font: { size: 10, family: 'Inter, sans-serif' } },
            grid: { display: false },
          },
        },
      },
    });
  }

  function renderChart() {
    destroyChart();
    if (state.chartType === 'latest') {
      renderLatest();
    } else {
      renderLineOrStacked();
    }
  }

  /* Vertical break-line plugin (only used for line/stacked across the break). */
  function breakLinePlugin(localBreakIdx) {
    return {
      id: 'breakLine',
      afterDatasetsDraw: function (chart) {
        var ctx = chart.ctx;
        var x = chart.scales.x;
        var y = chart.scales.y;
        var xLeft = x.getPixelForValue(localBreakIdx - 1);
        var xRight = x.getPixelForValue(localBreakIdx);
        var px = (xLeft + xRight) / 2;

        ctx.save();
        ctx.strokeStyle = 'rgba(192,57,43,0.6)';
        ctx.lineWidth = 1.5;
        ctx.setLineDash([5, 4]);
        ctx.beginPath();
        ctx.moveTo(px, y.top);
        ctx.lineTo(px, y.bottom);
        ctx.stroke();
        ctx.setLineDash([]);

        ctx.fillStyle = 'rgba(192,57,43,0.9)';
        ctx.font = '600 10px Inter, sans-serif';
        ctx.textAlign = 'left';
        ctx.fillText('Series re-based', px + 4, y.top + 12);
        ctx.fillText('(2024 Q1)', px + 4, y.top + 24);
        ctx.restore();
      },
    };
  }

  // ── Sector name shortening for chart axes ─────────────────
  function shortName(name) {
    var map = {
      'Wholesale and retail trade; repair of motor vehicles and motorcycles': 'Wholesale & retail',
      'Public administration and defence; compulsory social security': 'Public admin & defence',
      'Activities of Households as Employers Producing Activities of Households for own use': 'Household employers',
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

  // ── Highlight cards ───────────────────────────────────────
  function renderHighlights() {
    var lastIdx = data.quarters.length - 1;
    var quarter = data.quarters[lastIdx];
    var totalLatest = data.aggregates['GDP at Market Prices'][lastIdx];
    var totalYearAgo = data.aggregates['GDP at Market Prices'][lastIdx - 4];
    var yoy = totalYearAgo ? ((totalLatest - totalYearAgo) / totalYearAgo) * 100 : null;

    // Top sector by latest-quarter value
    var topName = null, topVal = -Infinity;
    data.sector_order.forEach(function (n) {
      var v = data.sectors[n][lastIdx];
      if (v > topVal) { topVal = v; topName = n; }
    });

    var sectorCount = data.sector_order.length;

    var yoyClass = yoy == null ? '' : (yoy >= 0 ? 'gdp-highlight-up' : 'gdp-highlight-down');
    var yoyArrow = yoy == null ? '' : (yoy >= 0 ? '▲' : '▼');

    highlightsEl.innerHTML =
      card('Latest GDP', fmtUSD(totalLatest), quarter) +
      card('YoY change',
           '<span class="' + yoyClass + '">' + yoyArrow + ' ' + fmtPct(Math.abs(yoy || 0), false) + '</span>',
           'vs ' + (data.quarters[lastIdx - 4] || 'a year ago')) +
      card('Top sector', shortName(topName), fmtUSD(topVal) + ' &middot; ' + quarter) +
      card('Sectors tracked', sectorCount, 'across the economy');
  }

  function card(label, value, sub) {
    return '<div class="gdp-highlight-card">' +
      '<p class="gdp-highlight-label">' + label + '</p>' +
      '<p class="gdp-highlight-value">' + value + '</p>' +
      '<p class="gdp-highlight-sub">' + sub + '</p>' +
      '</div>';
  }

  // ── Sector ranking table ──────────────────────────────────
  function buildSectorRows() {
    var lastIdx = data.quarters.length - 1;
    var quarter = data.quarters[lastIdx];
    var totalLatest = data.aggregates['GDP at Market Prices'][lastIdx];
    if (tableQuarterEl) tableQuarterEl.textContent = quarter;

    var rows = data.sector_order.map(function (name) {
      var val = data.sectors[name][lastIdx];
      var yearAgo = data.sectors[name][lastIdx - 4];
      var yoy = yearAgo ? ((val - yearAgo) / yearAgo) * 100 : null;
      var share = totalLatest ? (val / totalLatest) * 100 : 0;
      return { name: name, value: val, share: share, yoy: yoy };
    });
    return rows;
  }

  function renderTable() {
    var rows = buildSectorRows();
    var q = state.tableFilter.toLowerCase();
    if (q) {
      rows = rows.filter(function (r) {
        return r.name.toLowerCase().indexOf(q) !== -1;
      });
    }
    var sortCol = state.tableSort.col;
    var dir = state.tableSort.dir === 'asc' ? 1 : -1;
    rows.sort(function (a, b) {
      var av, bv;
      if (sortCol === 'name') { av = a.name; bv = b.name; }
      else if (sortCol === 'rank') { av = b.value; bv = a.value; } // rank ↔ value desc
      else { av = a[sortCol] == null ? -Infinity : a[sortCol]; bv = b[sortCol] == null ? -Infinity : b[sortCol]; }
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

    // Update header sort indicators
    tableHeaders.forEach(function (th) {
      th.classList.remove('sorted-asc', 'sorted-desc');
      if (th.getAttribute('data-sort') === state.tableSort.col) {
        th.classList.add(state.tableSort.dir === 'asc' ? 'sorted-asc' : 'sorted-desc');
      }
    });
  }

  function escapeHtml(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  // ── Event bindings ────────────────────────────────────────
  function bindEvents() {
    if (periodGroup) {
      periodGroup.addEventListener('click', function (e) {
        var btn = e.target.closest('.gdp-pill');
        if (!btn) return;
        periodGroup.querySelectorAll('.gdp-pill').forEach(function (b) { b.classList.remove('active'); });
        btn.classList.add('active');
        state.period = btn.getAttribute('data-period');
        renderChart();
      });
    }
    if (chartTypeSel) {
      chartTypeSel.addEventListener('change', function () {
        state.chartType = chartTypeSel.value;
        // Hide series selector for 'latest' view (it's a single-quarter snapshot)
        if (seriesGroup) {
          seriesGroup.style.opacity = state.chartType === 'latest' ? '0.4' : '1';
          seriesGroup.style.pointerEvents = state.chartType === 'latest' ? 'none' : '';
        }
        renderChart();
      });
    }
    if (seriesSel) {
      seriesSel.addEventListener('change', function () {
        state.series = seriesSel.value;
        renderChart();
      });
    }
    tableHeaders.forEach(function (th) {
      th.addEventListener('click', function () {
        var col = th.getAttribute('data-sort');
        if (state.tableSort.col === col) {
          state.tableSort.dir = state.tableSort.dir === 'asc' ? 'desc' : 'asc';
        } else {
          state.tableSort.col = col;
          state.tableSort.dir = (col === 'name') ? 'asc' : 'desc';
        }
        renderTable();
      });
    });
    if (sectorSearch) {
      sectorSearch.addEventListener('input', function () {
        state.tableFilter = sectorSearch.value;
        renderTable();
      });
    }
  }

  // ── Init ──────────────────────────────────────────────────
  function init(loaded) {
    data = loaded;
    if (rangeLabel) {
      rangeLabel.textContent = data.quarters[0] + ' to ' + data.quarters[data.quarters.length - 1];
    }
    if (breakNoteEl) {
      breakNoteEl.textContent = data.break_note;
    }
    renderHighlights();
    renderTable();
    bindEvents();
    renderChart();
  }

  fetch(DATA_URL, { cache: 'no-cache' })
    .then(function (r) {
      if (!r.ok) throw new Error('HTTP ' + r.status);
      return r.json();
    })
    .then(init)
    .catch(function (err) {
      var section = document.getElementById('gdpSection');
      if (section) {
        section.innerHTML = '<p style="text-align:center;color:#999;padding:40px 0;font-family:Inter,sans-serif;font-size:0.85em">GDP data unavailable.</p>';
      }
      if (window.console) console.warn('GDP data fetch failed:', err);
    });
})();
