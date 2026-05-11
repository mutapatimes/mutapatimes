/**
 * Live FX rates renderer + multi-currency converter.
 * Reads data/fx-rates.json (refreshed every ~2h by GitHub Actions) and
 * paints the hero, converter, and USD cross-rates table on /fx.html.
 * All cross-rates are derived from the USD-base payload so the page has
 * one source of truth and no per-pair rounding drift.
 */
(function () {
  var DATA_URL = 'data/fx-rates.json';

  // Display metadata for each currency we support. Order also drives the
  // converter input order — keep ZWG + USD at the top of mind.
  var CURRENCY_META = {
    USD: { name: 'US Dollar',           symbol: '$',  flag: '🇺🇸' },
    ZWG: { name: 'Zim Gold',            symbol: 'ZG', flag: '🇿🇼' },
    ZAR: { name: 'SA Rand',             symbol: 'R',  flag: '🇿🇦' },
    GBP: { name: 'British Pound',       symbol: '£',  flag: '🇬🇧' },
    EUR: { name: 'Euro',                symbol: '€',  flag: '🇪🇺' },
    BWP: { name: 'Botswana Pula',       symbol: 'P',  flag: '🇧🇼' },
    MZN: { name: 'Mozambique Metical',  symbol: 'MT', flag: '🇲🇿' },
    ZMW: { name: 'Zambian Kwacha',      symbol: 'K',  flag: '🇿🇲' },
    AUD: { name: 'Australian Dollar',   symbol: 'A$', flag: '🇦🇺' },
    CAD: { name: 'Canadian Dollar',     symbol: 'C$', flag: '🇨🇦' },
    CNY: { name: 'Chinese Yuan',        symbol: '¥',  flag: '🇨🇳' },
    AED: { name: 'UAE Dirham',          symbol: 'AED',flag: '🇦🇪' },
  };

  // Currencies shown in the converter (smaller, focused set).
  var CONVERTER_ORDER = ['USD', 'ZWG', 'GBP', 'ZAR', 'EUR', 'BWP'];

  var heroEl     = document.getElementById('fxHero');
  var metaEl     = document.getElementById('fxMeta');
  var convEl     = document.getElementById('fxConverterGrid');
  var tableEl    = document.getElementById('fxTableBody');
  var sendAmtEl  = document.getElementById('fxSendAmount');
  var sendCurEl  = document.getElementById('fxSendCurrency');
  var sendResEl  = document.getElementById('fxSendResults');
  if (!heroEl) return;

  function escapeHtml(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function fmt(n, decimals) {
    if (n == null || isNaN(n)) return '—';
    decimals = decimals == null ? (n >= 100 ? 2 : 4) : decimals;
    return Number(n).toLocaleString('en-US', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    });
  }

  function relativeAge(iso) {
    if (!iso) return '';
    var then = new Date(iso).getTime();
    if (isNaN(then)) return '';
    var diffMin = Math.round((Date.now() - then) / 60000);
    if (diffMin < 1) return 'just now';
    if (diffMin < 60) return diffMin + ' min ago';
    var diffHr = Math.round(diffMin / 60);
    if (diffHr < 24) return diffHr + ' hr ago';
    var diffDay = Math.round(diffHr / 24);
    return diffDay + ' day' + (diffDay === 1 ? '' : 's') + ' ago';
  }

  function renderHero(rates) {
    var zwg = rates.ZWG;
    if (zwg == null) {
      heroEl.innerHTML = '<p class="fx-hero-loading">ZWG rate unavailable.</p>';
      return;
    }
    heroEl.innerHTML =
      '<div class="fx-hero-card">' +
        '<p class="fx-hero-label">Today\'s Official Interbank Rate</p>' +
        '<p class="fx-hero-big">' +
          '<span class="fx-hero-from">1 USD</span>' +
          '<span class="fx-hero-eq">=</span>' +
          '<span class="fx-hero-to">' + fmt(zwg, 4) + ' ZWG</span>' +
        '</p>' +
        '<p class="fx-hero-sub">Zim Gold &middot; Reserve Bank of Zimbabwe official rate (composite)</p>' +
      '</div>';
  }

  function renderConverter(rates) {
    // Build inputs for each currency in CONVERTER_ORDER. Skip currencies
    // missing from the payload so we never render an unusable field.
    var fields = CONVERTER_ORDER.filter(function (c) { return rates[c] != null; });
    convEl.innerHTML = fields.map(function (code) {
      var meta = CURRENCY_META[code] || { name: code, symbol: '', flag: '' };
      return (
        '<label class="fx-conv-field">' +
          '<span class="fx-conv-lbl">' +
            '<span class="fx-conv-flag">' + meta.flag + '</span> ' +
            code + ' <span class="fx-conv-name">' + escapeHtml(meta.name) + '</span>' +
          '</span>' +
          '<input type="number" inputmode="decimal" step="0.01" min="0" ' +
            'class="fx-conv-input" data-code="' + code + '" value="" placeholder="0">' +
        '</label>'
      );
    }).join('');

    // Wire two-way binding
    var inputs = convEl.querySelectorAll('.fx-conv-input');
    function broadcast(source) {
      var srcCode = source.getAttribute('data-code');
      var raw = parseFloat(source.value);
      if (isNaN(raw) || raw < 0) {
        inputs.forEach(function (el) { if (el !== source) el.value = ''; });
        return;
      }
      // Convert source amount → USD → each target currency.
      var srcRate = rates[srcCode];
      if (!srcRate) return;
      var usdAmount = srcCode === 'USD' ? raw : raw / srcRate;
      inputs.forEach(function (el) {
        if (el === source) return;
        var code = el.getAttribute('data-code');
        var rate = rates[code];
        if (rate == null) { el.value = ''; return; }
        var v = usdAmount * rate;
        el.value = v.toLocaleString('en-US', {
          minimumFractionDigits: 2,
          maximumFractionDigits: code === 'USD' || code === 'GBP' || code === 'EUR' ? 2 : 4,
          useGrouping: false,
        });
      });
    }
    inputs.forEach(function (el) {
      el.addEventListener('input', function () { broadcast(el); });
    });
    // Seed with 1 USD to make the page feel alive on first load
    var seed = convEl.querySelector('.fx-conv-input[data-code="USD"]');
    if (seed) { seed.value = '1'; broadcast(seed); }
  }

  function renderTable(rates) {
    // Sort by USD value DESC so big-number currencies (ZWG, ZMW, MZN)
    // are at the top — reads as "how much weakness vs the dollar".
    var rows = Object.keys(rates)
      .filter(function (c) { return c !== 'USD'; })
      .map(function (c) {
        var meta = CURRENCY_META[c] || { name: c, flag: '' };
        return {
          code: c,
          name: meta.name,
          flag: meta.flag,
          perUsd: rates[c],
          inverse: 1 / rates[c],
        };
      })
      .sort(function (a, b) { return b.perUsd - a.perUsd; });

    tableEl.innerHTML = rows.map(function (r) {
      return (
        '<tr>' +
          '<td><span class="fx-flag">' + r.flag + '</span> ' + escapeHtml(r.name) + '</td>' +
          '<td class="fx-code">' + r.code + '</td>' +
          '<td class="fx-num">' + fmt(r.perUsd, r.perUsd >= 100 ? 2 : 4) + '</td>' +
          '<td class="fx-num fx-num--muted">$' + fmt(r.inverse, 4) + '</td>' +
        '</tr>'
      );
    }).join('');
  }

  // ── Send-money calculator ───────────────────────────────
  // Math: given mid-market rate (open.er-api.com, which is what Wise also
  // quotes), each provider's recipient amount is:
  //   net_send = max(0, send_amount - fee)
  //   provider_usd_per_send = (1 / rates[send_currency]) * (1 - margin_pct/100)
  //   recipient_usd = net_send * provider_usd_per_send
  // Sorted by recipient_usd DESC so the best deal sits at the top.
  function appendSendUrlParams(url, sendCur, sendAmt) {
    if (!url) return url;
    var sep = url.indexOf('?') === -1 ? '?' : '&';
    return url + sep +
      'utm_source=mutapatimes&utm_medium=fx_calculator' +
      '&amount=' + encodeURIComponent(sendAmt) +
      '&source=' + encodeURIComponent(sendCur);
  }

  function fmtMoney(n, decimals) {
    if (n == null || isNaN(n) || !isFinite(n)) return '—';
    return Number(n).toLocaleString('en-US', {
      minimumFractionDigits: decimals == null ? 2 : decimals,
      maximumFractionDigits: decimals == null ? 2 : decimals,
    });
  }

  function renderSendResults(rates, providersData) {
    if (!sendResEl) return;
    var amount = parseFloat(sendAmtEl && sendAmtEl.value);
    var sendCur = sendCurEl && sendCurEl.value;
    if (!amount || amount <= 0 || !sendCur) {
      sendResEl.innerHTML = '<p class="fx-loading">Enter an amount to compare providers.</p>';
      return;
    }
    var corridor = (providersData && providersData.corridors || {})[sendCur];
    if (!corridor) {
      sendResEl.innerHTML = '<p class="fx-loading">No providers configured for that corridor yet.</p>';
      return;
    }
    var midRate = rates[sendCur];
    if (!midRate || !isFinite(midRate)) {
      sendResEl.innerHTML = '<p class="fx-loading">FX rate for ' + escapeHtml(sendCur) + ' is unavailable right now.</p>';
      return;
    }
    var mid_usd_per_send = 1 / midRate; // 1 unit of send currency in USD at mid-market

    var rows = corridor.providers.map(function (p) {
      var net = Math.max(0, amount - (p.fee || 0));
      var providerRate = mid_usd_per_send * (1 - (p.fx_margin_pct || 0) / 100);
      var recipient = net * providerRate;
      return {
        id: p.id,
        name: p.name,
        margin: p.fx_margin_pct || 0,
        fee: p.fee || 0,
        rate: providerRate,
        recipient: recipient,
        payout: p.payout || '',
        speed: p.speed || '',
        url: p.url || '',
        notes: p.notes || '',
      };
    }).sort(function (a, b) { return b.recipient - a.recipient; });

    // Best row gets a "Best value" badge
    var best = rows.length ? rows[0].recipient : 0;

    var rowsHtml = rows.map(function (r, i) {
      var isBest = i === 0 && rows.length > 1;
      var delta = best > 0 ? ((r.recipient - best) / best) * 100 : 0;
      var deltaHtml = isBest
        ? '<span class="fx-send-best">Best</span>'
        : '<span class="fx-send-delta">' + (delta >= 0 ? '+' : '') + delta.toFixed(2) + '%</span>';
      var feeHtml = r.fee ? sendCur + ' ' + fmtMoney(r.fee, 2) : 'No fee';
      return (
        '<a class="fx-send-row" href="' + escapeHtml(appendSendUrlParams(r.url, sendCur, amount)) +
        '" target="_blank" rel="noopener">' +
          '<div class="fx-send-provider">' +
            '<span class="fx-send-name">' + escapeHtml(r.name) + '</span>' +
            (r.notes ? '<span class="fx-send-note">' + escapeHtml(r.notes) + '</span>' : '') +
          '</div>' +
          '<div class="fx-send-amount">' +
            '<span class="fx-send-recipient">$' + fmtMoney(r.recipient, 2) + '</span>' +
            '<span class="fx-send-recipient-lbl">recipient gets (USD)</span>' +
          '</div>' +
          '<div class="fx-send-meta">' +
            '<span>FX margin ' + r.margin.toFixed(1) + '%</span>' +
            '<span>Fee ' + escapeHtml(feeHtml) + '</span>' +
            (r.payout ? '<span>' + escapeHtml(r.payout) + '</span>' : '') +
            (r.speed ? '<span>' + escapeHtml(r.speed) + '</span>' : '') +
          '</div>' +
          '<div class="fx-send-badge">' + deltaHtml + '<span class="fx-send-cta">Send →</span></div>' +
        '</a>'
      );
    }).join('');

    sendResEl.innerHTML = rowsHtml || '<p class="fx-loading">No matching providers.</p>';
  }

  function wireSendCalculator(rates, providersData) {
    if (!sendAmtEl || !sendCurEl || !sendResEl) return;
    var refresh = function () { renderSendResults(rates, providersData); };
    var debouncer;
    sendAmtEl.addEventListener('input', function () {
      clearTimeout(debouncer);
      debouncer = setTimeout(refresh, 150);
    });
    sendCurEl.addEventListener('change', refresh);
    refresh();
  }

  function render(data) {
    var rates = (data && data.rates) || {};
    if (!rates.ZWG && !rates.USD) {
      heroEl.innerHTML = '<p class="fx-hero-loading">Rates unavailable. Check back soon.</p>';
      return;
    }
    renderHero(rates);
    renderConverter(rates);
    renderTable(rates);
    if (metaEl) {
      var age = relativeAge(data.fetched_at);
      var asOf = data.as_of ? ' &middot; ECB ref: ' + escapeHtml(data.as_of) : '';
      metaEl.innerHTML = (age ? 'Updated ' + age : '') + asOf;
    }

    // Fetch the provider config and wire up the send-money calculator.
    fetch('data/remittance-providers.json', { cache: 'no-cache' })
      .then(function (r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
      .then(function (providersData) { wireSendCalculator(rates, providersData); })
      .catch(function (err) {
        if (sendResEl) {
          sendResEl.innerHTML = '<p class="fx-loading">Provider data temporarily unavailable.</p>';
        }
        if (window.console) console.warn('Remittance provider fetch failed:', err);
      });
  }

  fetch(DATA_URL, { cache: 'no-cache' })
    .then(function (r) {
      if (!r.ok) throw new Error('HTTP ' + r.status);
      return r.json();
    })
    .then(render)
    .catch(function (err) {
      heroEl.innerHTML = '<p class="fx-hero-loading">Rates temporarily unavailable.</p>';
      if (window.console) console.warn('FX fetch failed:', err);
    });
})();
