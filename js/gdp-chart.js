/**
 * Quarterly GDP-by-sector chart (ZimStat data).
 * Renders data/gdp-zimbabwe-quarterly.json as a Chart.js line chart with
 * a visible discontinuity at the 2024 Q1 series re-base.
 */
(function () {
  var DATA_URL = 'data/gdp-zimbabwe-quarterly.json';
  var canvas = document.getElementById('gdpChart');
  if (!canvas) return;

  var rangeLabel = document.getElementById('gdpRangeLabel');
  var breakNoteEl = document.getElementById('gdpBreakNote');
  var toggleEl = document.getElementById('gdpViewToggle');

  // 12-color palette for sector lines (excluding the headline accent red).
  var PALETTE = [
    '#1f6feb', '#2da44e', '#bf8700', '#8957e5', '#cf222e',
    '#0969da', '#1a7f37', '#9a6700', '#6639ba', '#a40e26',
    '#0550ae', '#116329',
  ];

  var chart = null;
  var data = null;

  function fmtUSD(n) {
    if (n >= 1e9) return '$' + (n / 1e9).toFixed(1) + 'B';
    if (n >= 1e6) return '$' + (n / 1e6).toFixed(1) + 'M';
    if (n >= 1e3) return '$' + (n / 1e3).toFixed(0) + 'K';
    return '$' + Math.round(n);
  }

  function splitAtBreak(values, breakIdx) {
    /* Return two arrays — one for pre-break (with nulls after), one for post.
     * This makes Chart.js draw the break as a gap rather than a connected line. */
    var pre = values.map(function (v, i) { return i < breakIdx ? v : null; });
    var post = values.map(function (v, i) { return i >= breakIdx ? v : null; });
    return { pre: pre, post: post };
  }

  function buildDatasets(view) {
    var breakIdx = data.break_index;
    var datasets = [];

    function pair(label, values, color, width) {
      var split = splitAtBreak(values, breakIdx);
      datasets.push({
        label: label + ' (pre-2024)',
        data: split.pre,
        borderColor: color,
        backgroundColor: color,
        borderWidth: width,
        tension: 0.25,
        pointRadius: 2,
        pointHoverRadius: 5,
        spanGaps: false,
      });
      datasets.push({
        label: label + ' (post-2024)',
        data: split.post,
        borderColor: color,
        backgroundColor: color,
        borderWidth: width,
        borderDash: [],
        tension: 0.25,
        pointRadius: 2,
        pointHoverRadius: 5,
        spanGaps: false,
      });
    }

    if (view === 'total') {
      var total = data.aggregates['GDP at Market Prices'];
      pair('GDP at Market Prices', total, '#c0392b', 3);
    } else if (view === 'top') {
      var top = data.sector_order.slice(0, 6);
      top.forEach(function (name, i) {
        pair(name, data.sectors[name], PALETTE[i % PALETTE.length], 2);
      });
    } else {
      // all sectors
      data.sector_order.forEach(function (name, i) {
        pair(name, data.sectors[name], PALETTE[i % PALETTE.length], 1.5);
      });
    }

    return datasets;
  }

  function render(view) {
    if (chart) chart.destroy();

    var ctx = canvas.getContext('2d');
    var breakIdx = data.break_index;

    chart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: data.quarters,
        datasets: buildDatasets(view),
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: {
            position: 'bottom',
            onClick: function (e, item, legend) {
              // Toggle BOTH pre/post halves of the clicked series together.
              var ci = legend.chart;
              var name = item.text;
              ci.data.datasets.forEach(function (ds, idx) {
                var dsName = ds.label
                  .replace(' (pre-2024)', '')
                  .replace(' (post-2024)', '');
                if (dsName === name) {
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
                  .map(function (l) {
                    l.text = l.text.replace(' (pre-2024)', '');
                    return l;
                  });
              },
            },
          },
          tooltip: {
            callbacks: {
              title: function (items) { return items[0].label; },
              label: function (ctx) {
                var name = ctx.dataset.label
                  .replace(' (pre-2024)', '')
                  .replace(' (post-2024)', '');
                return name + ': ' + fmtUSD(ctx.parsed.y);
              },
            },
          },
          // Vertical line at the break — drawn via a custom plugin (see below)
        },
        scales: {
          x: {
            ticks: {
              font: { size: 10, family: 'Inter, sans-serif' },
              maxRotation: 45, minRotation: 45,
              autoSkip: true, maxTicksLimit: 14,
            },
            grid: { display: false },
          },
          y: {
            ticks: {
              font: { size: 10, family: 'Inter, sans-serif' },
              callback: function (v) { return fmtUSD(v); },
            },
            grid: { color: 'rgba(0,0,0,0.05)' },
            beginAtZero: true,
          },
        },
      },
      plugins: [breakLinePlugin(breakIdx)],
    });
  }

  /* Custom plugin: draw a dashed vertical line at the break index with a label. */
  function breakLinePlugin(breakIdx) {
    return {
      id: 'breakLine',
      afterDatasetsDraw: function (chart) {
        if (breakIdx < 0) return;
        var ctx = chart.ctx;
        var xScale = chart.scales.x;
        var yScale = chart.scales.y;
        // Position halfway between (breakIdx-1) and breakIdx on the axis
        var xLeft = xScale.getPixelForValue(breakIdx - 1);
        var xRight = xScale.getPixelForValue(breakIdx);
        var x = (xLeft + xRight) / 2;

        ctx.save();
        ctx.strokeStyle = 'rgba(192,57,43,0.6)';
        ctx.lineWidth = 1.5;
        ctx.setLineDash([5, 4]);
        ctx.beginPath();
        ctx.moveTo(x, yScale.top);
        ctx.lineTo(x, yScale.bottom);
        ctx.stroke();
        ctx.setLineDash([]);

        ctx.fillStyle = 'rgba(192,57,43,0.9)';
        ctx.font = '600 10px Inter, sans-serif';
        ctx.textAlign = 'left';
        ctx.fillText('Series re-based', x + 4, yScale.top + 12);
        ctx.fillText('(2024 Q1)', x + 4, yScale.top + 24);
        ctx.restore();
      },
    };
  }

  function bindToggle() {
    if (!toggleEl) return;
    toggleEl.addEventListener('click', function (e) {
      var btn = e.target.closest('.gdp-toggle-btn');
      if (!btn) return;
      toggleEl.querySelectorAll('.gdp-toggle-btn').forEach(function (b) {
        b.classList.remove('active');
      });
      btn.classList.add('active');
      render(btn.getAttribute('data-view'));
    });
  }

  function init(loaded) {
    data = loaded;
    if (rangeLabel) {
      rangeLabel.textContent = data.quarters[0] + ' to ' + data.quarters[data.quarters.length - 1];
    }
    if (breakNoteEl) {
      breakNoteEl.textContent = data.break_note;
    }
    bindToggle();
    render('total');
  }

  fetch(DATA_URL, { cache: 'no-cache' })
    .then(function (r) {
      if (!r.ok) throw new Error('HTTP ' + r.status);
      return r.json();
    })
    .then(init)
    .catch(function (err) {
      var wrap = canvas.parentElement;
      if (wrap) wrap.innerHTML = '<p style="text-align:center;color:#999;padding:40px 0;font-family:Inter,sans-serif;font-size:0.85em">GDP data unavailable.</p>';
      if (window.console) console.warn('GDP chart fetch failed:', err);
    });
})();
