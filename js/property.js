/* Property page interactivity — The Mutapa Times */
(function () {
  'use strict';

  if (typeof PROPERTY_DATA === 'undefined') return;
  var D = PROPERTY_DATA;
  var chart = null;

  /* ── Helpers ── */
  function fmt(n) {
    if (n == null || n === 0 || n === '0' || n === '-') return '-';
    return '$' + Number(n).toLocaleString('en-US');
  }
  function pctBadge(pct, dir) {
    var p = Number(pct) || 0;
    var d = Number(dir) || 0;
    if (p === 0 && d === 0) return '<span class="prop-pct flat">0.0%</span>';
    var cls = d > 0 ? 'up' : (d < 0 ? 'down' : 'flat');
    var arrow = d > 0 ? ' &#9650;' : (d < 0 ? ' &#9660;' : '');
    return '<span class="prop-pct ' + cls + '">' + p.toFixed(1) + '%' + arrow + '</span>';
  }

  /* ── Colour palette ── */
  var COLORS = [
    '#c41e1e', '#2e7d42', '#5a6e8a', '#c8a96e',
    '#1d9bf0', '#e65100', '#6a1b9a', '#00838f'
  ];

  /* ── Init ── */
  function init() {
    buildMovers();
    buildViewedBars();
    populateSelects();
    buildChart();
    buildTable();
    buildCatTable();
    buildHistoryTable();
    bindEvents();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  /* ── Biggest movers ── */
  function buildMovers() {
    var el = document.getElementById('moversGrid');
    if (!el) return;
    var html = '';
    D.biggestPriceChanges.forEach(function (m) {
      html += '<div class="prop-mover-card">' +
        '<div class="prop-mover-name">' + m.name + '</div>' +
        '<div class="prop-mover-pct ' + m.dir + '">' + m.pct + '% ' +
        (m.dir === 'up' ? '&#9650;' : '&#9660;') + '</div></div>';
    });
    el.innerHTML = html;
  }

  /* ── Most-viewed horizontal bars ── */
  function buildViewedBars() {
    var regEl = document.getElementById('viewedRegions');
    var catEl = document.getElementById('viewedCategories');
    if (regEl) regEl.innerHTML = barHTML(D.mostViewedRegions);
    if (catEl) catEl.innerHTML = barHTML(D.mostViewedCategories);
  }
  function barHTML(items) {
    var max = Math.max.apply(null, items.map(function (i) { return i.pct; }));
    var html = '';
    items.forEach(function (item) {
      var w = Math.round((item.pct / max) * 100);
      html += '<div class="prop-bar-row">' +
        '<span class="prop-bar-label">' + item.name + '</span>' +
        '<div class="prop-bar-track"><div class="prop-bar-fill" style="width:' + w + '%"></div></div>' +
        '<span class="prop-bar-value">' + item.pct + '%</span></div>';
    });
    return html;
  }

  /* ── Populate selects ── */
  function populateSelects() {
    var yearSel = document.getElementById('tableYear');
    var regionSel = document.getElementById('chartRegion');
    var historySel = document.getElementById('historyRegion');

    D.years.forEach(function (y) {
      yearSel.innerHTML += '<option value="' + y + '">' + y + '</option>';
    });

    D.regions.forEach(function (r) {
      regionSel.innerHTML += '<option value="' + r + '">' + r + '</option>';
      historySel.innerHTML += '<option value="' + r + '">' + r + '</option>';
    });
  }

  /* ── Chart ── */
  function buildChart() {
    var ctx = document.getElementById('propertyChart');
    if (!ctx || typeof Chart === 'undefined') return;

    var labels = D.years.slice().reverse();
    var datasets = getChartDatasets();

    chart = new Chart(ctx, {
      type: 'line',
      data: { labels: labels, datasets: datasets },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: {
            display: true,
            position: 'bottom',
            labels: {
              font: { family: 'Inter, system-ui, sans-serif', size: 11 },
              usePointStyle: true,
              padding: 16
            }
          },
          tooltip: {
            backgroundColor: '#1a1a1a',
            titleFont: { family: 'Inter, system-ui, sans-serif', size: 12, weight: '600' },
            bodyFont: { family: 'Inter, system-ui, sans-serif', size: 11 },
            padding: 12,
            callbacks: {
              label: function (ctx) {
                return ctx.dataset.label + ': ' + fmt(ctx.parsed.y);
              }
            }
          }
        },
        scales: {
          y: {
            beginAtZero: false,
            grid: { color: 'rgba(0,0,0,0.06)' },
            ticks: {
              font: { family: 'Inter, system-ui, sans-serif', size: 10 },
              callback: function (val) { return fmt(val); }
            }
          },
          x: {
            grid: { display: false },
            ticks: { font: { family: 'Inter, system-ui, sans-serif', size: 10 } }
          }
        }
      }
    });
  }

  function getChartDatasets() {
    var metric = document.getElementById('chartMetric').value;
    var view = document.getElementById('chartView').value;
    var labels = D.years.slice().reverse();
    var datasets = [];

    if (view === 'market') {
      var data = labels.map(function (y) { return D.market[y][metric]; });
      datasets.push({
        label: 'Overall Market',
        data: data,
        borderColor: COLORS[0],
        backgroundColor: COLORS[0] + '18',
        fill: true,
        tension: 0.3,
        pointRadius: 4,
        pointHoverRadius: 6,
        borderWidth: 2
      });
    } else if (view === 'categories') {
      D.categories.forEach(function (cat, ci) {
        var data = labels.map(function (y) {
          var d = D.categoryData[y][cat];
          return d ? d[metric] : 0;
        });
        datasets.push({
          label: cat,
          data: data,
          borderColor: COLORS[ci],
          backgroundColor: COLORS[ci] + '10',
          tension: 0.3,
          pointRadius: 3,
          pointHoverRadius: 5,
          borderWidth: 2
        });
      });
    } else if (view === 'region') {
      var region = document.getElementById('chartRegion').value;
      var data = labels.map(function (y) {
        var d = D.regionData[y][region];
        return d ? d[metric] : 0;
      });
      datasets.push({
        label: region,
        data: data,
        borderColor: COLORS[0],
        backgroundColor: COLORS[0] + '18',
        fill: true,
        tension: 0.3,
        pointRadius: 4,
        pointHoverRadius: 6,
        borderWidth: 2
      });
    }

    return datasets;
  }

  function updateChart() {
    if (!chart) return;
    var datasets = getChartDatasets();
    chart.data.datasets = datasets;
    chart.update();
  }

  /* ── Region data table ── */
  function buildTable() {
    var yearEl = document.getElementById('tableYear');
    var typeEl = document.getElementById('tableType');
    var searchEl = document.getElementById('propSearch');
    var tbody = document.getElementById('propTableBody');
    if (!tbody || !yearEl || !typeEl) return;

    var year = yearEl.value || D.years[0];
    var type = typeEl.value || 'sale';
    var search = (searchEl ? searchEl.value : '').toLowerCase();

    var regionData = D.regionData[year];
    if (!regionData) return;

    var rows = [];
    D.regions.forEach(function (r) {
      if (search && r.toLowerCase().indexOf(search) === -1) return;
      var d = regionData[r];
      if (!d) return;
      var price = type === 'sale' ? d.sale : d.rent;
      var pct = type === 'sale' ? d.salePct : d.rentPct;
      var dir = type === 'sale' ? d.saleDir : d.rentDir;
      rows.push({ name: r, price: Number(price), pct: pct, dir: dir });
    });

    // Sort
    var sortKey = tbody.getAttribute('data-sort') || 'name';
    var sortDir = tbody.getAttribute('data-dir') || 'asc';
    rows.sort(function (a, b) {
      if (sortKey === 'name') return sortDir === 'asc' ? a.name.localeCompare(b.name) : b.name.localeCompare(a.name);
      if (sortKey === 'price') return sortDir === 'asc' ? a.price - b.price : b.price - a.price;
      if (sortKey === 'change') return sortDir === 'asc' ? a.pct - b.pct : b.pct - a.pct;
      return 0;
    });

    var html = '';
    rows.forEach(function (r) {
      html += '<tr>' +
        '<td class="prop-td-name">' + r.name + '</td>' +
        '<td>' + fmt(r.price) + '</td>' +
        '<td>' + pctBadge(r.pct, r.dir) + '</td></tr>';
    });
    if (rows.length === 0) {
      html = '<tr><td colspan="3" style="text-align:center;color:#999;padding:24px;">No results found</td></tr>';
    }
    tbody.innerHTML = html;
  }

  /* ── Category table ── */
  function buildCatTable() {
    var yearEl = document.getElementById('tableYear');
    var tbody = document.getElementById('catTableBody');
    if (!tbody || !yearEl) return;
    var year = yearEl.value || D.years[0];
    var catData = D.categoryData[year];
    if (!catData) return;

    var html = '';
    D.categories.forEach(function (cat) {
      var d = catData[cat];
      if (!d) return;
      html += '<tr>' +
        '<td class="prop-td-name">' + cat + '</td>' +
        '<td>' + fmt(d.sale) + '</td>' +
        '<td>' + pctBadge(d.salePct, d.saleDir) + '</td>' +
        '<td>' + fmt(d.rent) + '</td>' +
        '<td>' + pctBadge(d.rentPct, d.rentDir) + '</td></tr>';
    });
    tbody.innerHTML = html;
  }

  /* ── History table ── */
  function buildHistoryTable() {
    var region = document.getElementById('historyRegion').value;
    var tbody = document.getElementById('historyTableBody');
    if (!tbody) return;

    var html = '';
    D.years.forEach(function (y) {
      var d;
      if (region === 'market') {
        d = D.market[y];
      } else {
        d = D.regionData[y][region];
      }
      if (!d) return;
      html += '<tr>' +
        '<td><strong>' + y + '</strong></td>' +
        '<td>' + fmt(d.sale) + '</td>' +
        '<td>' + pctBadge(d.salePct, d.saleDir) + '</td>' +
        '<td>' + fmt(d.rent) + '</td>' +
        '<td>' + pctBadge(d.rentPct, d.rentDir) + '</td></tr>';
    });
    tbody.innerHTML = html;
  }

  /* ── Events ── */
  function bindEvents() {
    var chartMetric = document.getElementById('chartMetric');
    var chartView = document.getElementById('chartView');
    var chartRegion = document.getElementById('chartRegion');
    var tableYear = document.getElementById('tableYear');
    var tableType = document.getElementById('tableType');
    var propSearch = document.getElementById('propSearch');
    var historyRegion = document.getElementById('historyRegion');

    chartMetric.addEventListener('change', updateChart);
    chartView.addEventListener('change', function () {
      chartRegion.style.display = chartView.value === 'region' ? '' : 'none';
      updateChart();
    });
    chartRegion.addEventListener('change', updateChart);

    tableYear.addEventListener('change', function () {
      buildTable();
      buildCatTable();
    });
    tableType.addEventListener('change', buildTable);

    var searchTimer;
    propSearch.addEventListener('input', function () {
      clearTimeout(searchTimer);
      searchTimer = setTimeout(buildTable, 200);
    });

    historyRegion.addEventListener('change', buildHistoryTable);

    // Column sort
    document.querySelectorAll('.prop-th-sortable').forEach(function (th) {
      th.addEventListener('click', function () {
        var tbody = document.getElementById('propTableBody');
        var key = th.getAttribute('data-sort');
        var current = tbody.getAttribute('data-sort');
        var dir = (current === key && tbody.getAttribute('data-dir') === 'asc') ? 'desc' : 'asc';
        tbody.setAttribute('data-sort', key);
        tbody.setAttribute('data-dir', dir);

        // Update sort icons
        document.querySelectorAll('.prop-th-sortable').forEach(function (h) {
          h.classList.remove('sorted-asc', 'sorted-desc');
        });
        th.classList.add(dir === 'asc' ? 'sorted-asc' : 'sorted-desc');

        buildTable();
      });
    });
  }

})();
