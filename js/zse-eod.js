/*
 * ZSE end-of-day Market Activity card.
 *
 * Renders /data/zse-market-activity.json (written weekdays by
 * scripts/fetch_zse_market.py from the ZSE public market-data API) into any
 * element with id "zse-eod". Self-contained: injects its own styles using the
 * site's design tokens, so it drops onto the /zse hub and /economy page alike.
 */
(function () {
  "use strict";
  var slot = document.getElementById("zse-eod");
  if (!slot) return;

  var DATA_URL = (window.MT_DATA_DIR ? "/" + window.MT_DATA_DIR : "/data") + "/zse-market-activity.json";

  function esc(s) {
    return String(s == null ? "" : s).replace(/&/g, "&amp;").replace(/</g, "&lt;")
      .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }
  function commas(n, dp) {
    if (n == null || isNaN(n)) return "—";
    return Number(n).toLocaleString("en-GB", { minimumFractionDigits: dp || 0, maximumFractionDigits: dp || 0 });
  }
  function big(n) { // 107711087205 -> "107.71bn"
    if (n == null || isNaN(n)) return "—";
    n = Number(n);
    if (n >= 1e9) return (n / 1e9).toFixed(2) + "bn";
    if (n >= 1e6) return (n / 1e6).toFixed(2) + "m";
    return commas(n, 0);
  }
  function pct(p) {
    if (p == null || isNaN(p)) return "";
    var v = Number(p);
    return (v > 0 ? "+" : "") + v.toFixed(2) + "%";
  }
  function dir(p) { return p > 0 ? "up" : (p < 0 ? "down" : "flat"); }
  function arrow(d) { return d === "up" ? "▲" : (d === "down" ? "▼" : "■"); }
  function niceDate(iso) {
    if (!iso) return "";
    var p = iso.split("-");
    if (p.length !== 3) return iso;
    var mo = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
    return Number(p[2]) + " " + mo[Number(p[1]) - 1] + " " + p[0];
  }

  function style() {
    if (document.getElementById("zse-eod-style")) return;
    var s = document.createElement("style");
    s.id = "zse-eod-style";
    s.textContent = [
      ".zeod{max-width:1100px;margin:18px auto 8px;padding:0 20px;font-family:'Inter',system-ui,sans-serif;color:var(--ink,#1a1a1a);}",
      ".zeod-head{display:flex;align-items:baseline;justify-content:space-between;gap:12px;border-top:3px solid var(--accent,#c41e1e);padding-top:10px;flex-wrap:wrap;}",
      ".zeod-h{font-family:'Playfair Display',Georgia,serif;font-weight:800;font-size:clamp(1.3rem,2.6vw,1.7rem);margin:0;}",
      ".zeod-asof{font-size:.8rem;opacity:.62;font-weight:600;letter-spacing:.02em;}",
      ".zeod-kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:14px 0 4px;}",
      ".zeod-kpi{border:1px solid rgba(0,0,0,.12);border-radius:10px;padding:12px 14px;background:var(--paper,#fafaf7);}",
      ".zeod-kpi .lbl{font-size:.62rem;text-transform:uppercase;letter-spacing:.08em;opacity:.6;font-weight:700;}",
      ".zeod-kpi .val{font-family:'Playfair Display',Georgia,serif;font-weight:800;font-size:1.35rem;margin-top:3px;line-height:1.05;font-variant-numeric:tabular-nums;}",
      ".zeod-kpi .sub{font-size:.72rem;font-weight:700;margin-top:2px;}",
      ".up{color:#1a7f37;}.down{color:#c41e1e;}.flat{opacity:.6;}",
      ".zeod-grid{display:grid;grid-template-columns:1.3fr 1fr;gap:18px;margin-top:16px;}",
      ".zeod-col-h{font-size:.66rem;text-transform:uppercase;letter-spacing:.08em;font-weight:800;opacity:.6;margin:0 0 8px;}",
      ".zeod-idx{display:grid;grid-template-columns:1fr auto auto;gap:2px 10px;font-size:.86rem;}",
      ".zeod-idx .nm{padding:4px 0;border-top:1px solid rgba(0,0,0,.06);}",
      ".zeod-idx .vv{padding:4px 0;border-top:1px solid rgba(0,0,0,.06);text-align:right;font-variant-numeric:tabular-nums;}",
      ".zeod-idx .cc{padding:4px 0;border-top:1px solid rgba(0,0,0,.06);text-align:right;font-weight:700;font-variant-numeric:tabular-nums;white-space:nowrap;}",
      ".zeod-ml{display:grid;grid-template-columns:1fr;gap:14px;}",
      ".zeod-mv{font-size:.84rem;}",
      ".zeod-mv .row{display:flex;justify-content:space-between;gap:8px;padding:4px 0;border-top:1px solid rgba(0,0,0,.06);}",
      ".zeod-mv .sym{font-weight:700;}.zeod-mv .ch{font-weight:700;font-variant-numeric:tabular-nums;}",
      ".zeod-notices{margin-top:16px;}",
      ".zeod-notices a{display:block;text-decoration:none;color:var(--ink,#1a1a1a);padding:6px 0;border-top:1px solid rgba(0,0,0,.06);font-size:.86rem;}",
      ".zeod-notices a:hover{color:var(--accent,#c41e1e);}",
      ".zeod-notices .nd{font-size:.68rem;opacity:.55;font-weight:700;letter-spacing:.03em;}",
      ".zeod-note{font-size:.72rem;opacity:.55;margin:14px 0 2px;border-left:2px solid var(--accent,#c41e1e);padding-left:8px;}",
      "@media(max-width:720px){.zeod-kpis{grid-template-columns:repeat(2,1fr);}.zeod-grid{grid-template-columns:1fr;}}",
      "@media(prefers-color-scheme:dark){.zeod-kpi,.zeod-idx .nm,.zeod-idx .vv,.zeod-idx .cc,.zeod-mv .row,.zeod-notices a{border-color:rgba(255,255,255,.12);} .up{color:#4ade80;}}"
    ].join("\n");
    document.head.appendChild(s);
  }

  function allShare(d) {
    for (var i = 0; i < (d.indices || []).length; i++) {
      if ((d.indices[i].name || "").toUpperCase() === "ALL SHARE") return d.indices[i];
    }
    return null;
  }

  function moverRows(list) {
    return (list || []).map(function (m) {
      var d = dir(m.change_pct);
      return '<div class="row"><span class="sym">' + esc(m.symbol || m.name) + '</span>' +
        '<span class="ch ' + d + '">' + esc(pct(m.change_pct)) + '</span></div>';
    }).join("");
  }

  function render(d) {
    style();
    var a = d.activity || {};
    var as = allShare(d);
    var idxRows = (d.indices || []).map(function (x) {
      return '<span class="nm">' + esc(x.name) + '</span>' +
        '<span class="vv">' + esc(commas(x.value, 2)) + '</span>' +
        '<span class="cc ' + esc(x.direction) + '">' + esc(arrow(x.direction)) + " " + esc(pct(x.change_pct)) + '</span>';
    }).join("");
    var notices = (d.notices || []).slice(0, 6).map(function (n) {
      var href = n.url ? ' href="' + esc(n.url) + '" target="_blank" rel="noopener"' : "";
      return "<a" + href + '><span class="nd">' + esc(niceDate(n.date)) +
        (n.category ? " · " + esc(n.category) : "") + '</span>' + esc(n.title) + "</a>";
    }).join("");

    slot.innerHTML =
      '<section class="zeod" aria-label="ZSE end of day">' +
        '<div class="zeod-head"><h2 class="zeod-h">ZSE at the close</h2>' +
          '<span class="zeod-asof">' + esc(niceDate(d.as_of)) + ' · ' + esc(d.currency || "ZWG") + '</span></div>' +
        '<div class="zeod-kpis">' +
          '<div class="zeod-kpi"><div class="lbl">Trades</div><div class="val">' + esc(commas(a.trades, 0)) + '</div></div>' +
          '<div class="zeod-kpi"><div class="lbl">Turnover</div><div class="val">' + esc(commas(a.turnover, 0)) + '</div></div>' +
          '<div class="zeod-kpi"><div class="lbl">Market cap</div><div class="val">' + esc(big(a.market_cap)) + '</div></div>' +
          '<div class="zeod-kpi"><div class="lbl">All Share</div><div class="val">' + (as ? esc(commas(as.value, 2)) : "—") +
            '</div>' + (as ? '<div class="sub ' + esc(as.direction) + '">' + esc(arrow(as.direction) + " " + pct(as.change_pct)) + '</div>' : "") + '</div>' +
        '</div>' +
        '<div class="zeod-grid">' +
          '<div><p class="zeod-col-h">Indices</p><div class="zeod-idx">' + idxRows + '</div></div>' +
          '<div><p class="zeod-col-h">Movers</p><div class="zeod-ml">' +
            '<div class="zeod-mv"><p class="zeod-col-h">Gainers</p>' + moverRows(d.gainers) + '</div>' +
            '<div class="zeod-mv"><p class="zeod-col-h">Losers</p>' + moverRows(d.losers) + '</div>' +
          '</div></div>' +
        '</div>' +
        (notices ? '<div class="zeod-notices"><p class="zeod-col-h">ZSE announcements &amp; notices</p>' + notices + '</div>' : "") +
        '<p class="zeod-note">Source: Zimbabwe Stock Exchange, end of day. Figures in ' + esc(d.currency || "ZWG") +
          '. Editorial reference, not investment advice.</p>' +
      '</section>';
  }

  var lastSig = null;
  // Coarse 5-minute cache-bust so the close refreshes promptly without
  // hammering the origin (everyone in the same window shares one response).
  function bust(u) { return u + (u.indexOf("?") < 0 ? "?" : "&") + "t=" + Math.floor(Date.now() / 300000); }

  function load() {
    var xhr = new XMLHttpRequest();
    xhr.open("GET", bust(DATA_URL), true);
    xhr.onreadystatechange = function () {
      if (xhr.readyState !== 4) return;
      if (xhr.status < 200 || xhr.status >= 300) return;
      try {
        var d = JSON.parse(xhr.responseText);
        var sig = (d.fetched_at || "") + "|" + (d.as_of || "");
        if (sig !== lastSig) { lastSig = sig; render(d); }
      } catch (e) {}
    };
    xhr.send();
  }

  load();
  // Live-update a left-open tab when a fresh close lands.
  setInterval(load, 5 * 60 * 1000);
})();
