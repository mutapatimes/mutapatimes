/*
 * /markets page hydration — renders pan-African indices + ZSE table
 * from JSON datasets on load. Daily-close data only.
 */
(function () {
  'use strict';

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

  fetch('/data/markets-indices.json', { cache: 'no-store' })
    .then(function (r) { return r.ok ? r.json() : null; })
    .then(function (d) { if (d) renderIndices(d); })
    .catch(function () {});

  fetch('/data/zse-ticker.json', { cache: 'no-store' })
    .then(function (r) { return r.ok ? r.json() : null; })
    .then(function (d) { if (d) renderZse(d); })
    .catch(function () {});
})();
