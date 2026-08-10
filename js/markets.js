/*
 * /markets page hydration — renders pan-African indices + ZSE table
 * from JSON datasets on load. Daily-close data only.
 */
(function () {
  'use strict';
  var mtUrl = window.mtUrl || function (p) { return p; };

  function el(tag, attrs, children) {
    var n = document.createElement(tag);
    if (attrs) for (var k in attrs) {
      if (k === 'class') n.className = attrs[k];
      else if (k === 'text') n.textContent = attrs[k];
      else if (k === 'html') n.innerHTML = attrs[k];
      else n.setAttribute(k, attrs[k]);
    }
    if (children) children.forEach(function (c) { if (c) n.appendChild(c); });
    return n;
  }

  function changeClass(s) {
    var clean = String(s || '').replace(/\s+/g, '').replace(/^\+/, '');
    var n = parseFloat(clean);
    if (isNaN(n) || n === 0) return 'markets-flat';
    return n > 0 ? 'markets-up' : 'markets-down';
  }
  function formatChange(s) {
    var t = String(s || '').trim();
    if (!t || t === '-') return '·';
    var n = parseFloat(t.replace(/\s+/g, '').replace(/^\+/, ''));
    if (isNaN(n)) return t;
    var sign = n > 0 ? '+' : '';
    return sign + n.toFixed(2) + '%';
  }

  // ── Pan-African indices ──────────────────────────────────────
  function renderIndices(data) {
    var wrap = document.getElementById('marketsIndices');
    if (!wrap) return;
    wrap.innerHTML = '';
    (data.indices || []).forEach(function (idx) {
      var card = el('article', { class: 'markets-card' });
      card.appendChild(el('p', { class: 'markets-card-country', text: idx.country }));
      card.appendChild(el('h3', { class: 'markets-card-label', text: idx.label }));
      card.appendChild(el('p', { class: 'markets-card-value', text: idx.value }));
      var rowParts = [];
      if (idx.day_change) {
        rowParts.push(
          '<span class="markets-chip ' + changeClass(idx.day_change) + '">1D ' + formatChange(idx.day_change) + '</span>'
        );
      }
      if (idx.ytd) {
        rowParts.push(
          '<span class="markets-chip ' + changeClass(idx.ytd) + '">YTD ' + formatChange(idx.ytd) + '</span>'
        );
      }
      card.appendChild(el('p', { class: 'markets-card-changes', html: rowParts.join(' ') }));
      card.appendChild(el('p', { class: 'markets-card-ccy', text: idx.ccy }));
      wrap.appendChild(card);
    });
    if (!wrap.children.length) {
      wrap.appendChild(el('p', { class: 'loading-msg', text: 'Market data unavailable.' }));
    }
  }

  // ── Commodities ─────────────────────────────────────────────
  function renderCommodities(data) {
    var wrap = document.getElementById('marketsCommodities');
    if (!wrap) return;
    wrap.innerHTML = '';
    (data.commodities || []).forEach(function (c) {
      var card = el('article', { class: 'markets-card markets-card--commodity' });
      card.appendChild(el('p', { class: 'markets-card-country', text: c.tag || '' }));
      card.appendChild(el('h3', { class: 'markets-card-label', text: c.label }));
      card.appendChild(el('p', { class: 'markets-card-value', text: c.value }));
      var rowParts = [];
      if (c.day_change) {
        rowParts.push(
          '<span class="markets-chip ' + changeClass(c.day_change) + '">1D ' + formatChange(c.day_change) + '</span>'
        );
      }
      if (c.ytd) {
        rowParts.push(
          '<span class="markets-chip ' + changeClass(c.ytd) + '">YTD ' + formatChange(c.ytd) + '</span>'
        );
      }
      card.appendChild(el('p', { class: 'markets-card-changes', html: rowParts.join(' ') }));
      card.appendChild(el('p', { class: 'markets-card-ccy', text: c.unit || '' }));
      if (c.zim_note) {
        card.appendChild(el('p', { class: 'markets-card-zimnote', text: c.zim_note }));
      }
      wrap.appendChild(card);
    });
    if (!wrap.children.length) {
      wrap.appendChild(el('p', { class: 'loading-msg', text: 'Commodity data unavailable.' }));
    }
  }

  // ── ZSE table ────────────────────────────────────────────────
  function renderZse(data) {
    var tbody = document.getElementById('marketsZseRows');
    if (!tbody) return;
    tbody.innerHTML = '';
    (data.tickers || []).forEach(function (t) {
      var tr = el('tr');
      var company = el('td', { class: 'markets-table-co', text: (t.company || '').replace(/Zimbabwe$/i, '').trim() });
      tr.appendChild(company);
      tr.appendChild(el('td', { class: 'markets-table-sector', text: t.sector || '' }));
      tr.appendChild(el('td', { class: 'markets-right', text: t.price || '' }));
      var dCls = changeClass(t.day_change);
      var ytdCls = changeClass(t.ytd);
      tr.appendChild(el('td', { class: 'markets-right ' + dCls, text: formatChange(t.day_change) }));
      tr.appendChild(el('td', { class: 'markets-right ' + ytdCls, text: formatChange(t.ytd) }));
      tr.appendChild(el('td', { class: 'markets-right', text: t.mcap_b ? String(t.mcap_b) : '—' }));
      tbody.appendChild(tr);
    });
    if (!tbody.children.length) {
      tbody.appendChild(el('tr', null, [
        el('td', { class: 'loading-msg', colspan: '6', text: 'ZSE data unavailable.' }),
      ]));
    }
  }

  // ── VFEX stats + movers ─────────────────────────────────────
  function commas(n, dp) {
    if (n == null || isNaN(n)) return '—';
    return Number(n).toLocaleString('en-GB', { minimumFractionDigits: dp || 0, maximumFractionDigits: dp || 0 });
  }
  function big(n) {
    if (n == null || isNaN(n)) return '—';
    n = Number(n);
    if (n >= 1e9) return (n / 1e9).toFixed(2) + 'bn';
    if (n >= 1e6) return (n / 1e6).toFixed(2) + 'm';
    return commas(n, 0);
  }
  function allShareIndex(data) {
    return (data.indices || [])[0] || null;
  }
  function renderVfexStats(data) {
    var wrap = document.getElementById('marketsVfexStats');
    if (!wrap) return;
    var a = data.activity || {};
    var as = allShareIndex(data);
    wrap.innerHTML = '';
    var tiles = [
      ['Trades', commas(a.trades, 0), null],
      ['Turnover', 'US$' + commas(a.turnover, 0), null],
      ['Market cap', 'US$' + big(a.market_cap), null],
      ['VFEX All Share', as ? commas(as.value, 2) : '—', as ? { pct: as.change_pct, dir: as.direction } : null],
    ];
    tiles.forEach(function (t) {
      var card = el('div', { class: 'markets-vfex-kpi' });
      card.appendChild(el('div', { class: 'lbl', text: t[0] }));
      card.appendChild(el('div', { class: 'val', text: t[1] }));
      if (t[2]) {
        card.appendChild(el('div', { class: 'sub ' + changeClass(t[2].pct),
          text: (t[2].dir === 'up' ? '▲ ' : t[2].dir === 'down' ? '▼ ' : '· ') + formatChange(t[2].pct) }));
      }
      wrap.appendChild(card);
    });
  }
  function renderVfexMovers(data) {
    var tbody = document.getElementById('marketsVfexRows');
    if (!tbody) return;
    tbody.innerHTML = '';
    var rows = (data.gainers || []).concat(data.losers || []);
    rows.forEach(function (m) {
      var tr = el('tr');
      tr.appendChild(el('td', { class: 'markets-table-co', text: m.name || '' }));
      tr.appendChild(el('td', { class: 'markets-table-sector', text: m.symbol || '' }));
      tr.appendChild(el('td', { class: 'markets-right', text: m.price != null ? 'US$' + commas(m.price, 2) : '—' }));
      tr.appendChild(el('td', { class: 'markets-right ' + changeClass(m.change_pct), text: formatChange(m.change_pct) }));
      tbody.appendChild(tr);
    });
    if (!tbody.children.length) {
      tbody.appendChild(el('tr', null, [
        el('td', { class: 'loading-msg', colspan: '4', text: 'VFEX data unavailable.' }),
      ]));
    }
  }
  function renderVfexNotices(data) {
    var wrap = document.getElementById('marketsVfexNotices');
    if (!wrap) return;
    var notices = (data.notices || []).slice(0, 3);
    if (!notices.length) return;
    wrap.innerHTML = '';
    notices.forEach(function (n) {
      var row = el('a', { class: 'markets-vfex-notice', href: n.url || '#', target: '_blank', rel: 'noopener' });
      row.appendChild(el('span', { class: 'markets-vfex-notice-date', text: n.date || '' }));
      row.appendChild(el('span', { class: 'markets-vfex-notice-title', text: n.title || '' }));
      wrap.appendChild(row);
    });
  }
  function renderVfexAsOf(data) {
    var el2 = document.getElementById('marketsVfexAsOf');
    if (el2 && data.as_of) el2.textContent = 'Last close: ' + data.as_of;
  }

  fetch(mtUrl('/data/markets-indices.json'), { cache: 'no-store' })
    .then(function (r) { return r.ok ? r.json() : null; })
    .then(function (d) { if (d) renderIndices(d); })
    .catch(function () {});

  fetch(mtUrl('/data/commodities.json'), { cache: 'no-store' })
    .then(function (r) { return r.ok ? r.json() : null; })
    .then(function (d) { if (d) renderCommodities(d); })
    .catch(function () {});

  fetch(mtUrl('/data/zse-ticker.json'), { cache: 'no-store' })
    .then(function (r) { return r.ok ? r.json() : null; })
    .then(function (d) { if (d) renderZse(d); })
    .catch(function () {});

  fetch(mtUrl('/data/vfex-market-activity.json'), { cache: 'no-store' })
    .then(function (r) { return r.ok ? r.json() : null; })
    .then(function (d) {
      if (!d) return;
      renderVfexStats(d);
      renderVfexMovers(d);
      renderVfexNotices(d);
      renderVfexAsOf(d);
    })
    .catch(function () {});
})();
