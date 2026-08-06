/*
 * ZSE end-of-day Market Activity card.
 *
 * Renders /data/zse-market-activity.json (written weekdays by
 * scripts/fetch_zse_market.py from the ZSE public market-data API) into any
 * element with id "zse-eod". Self-contained: injects its own styles using the
 * site's design tokens (Playfair/Inter, --paper/--ink/--accent), so it drops
 * onto the /zse hub and /economy page alike. Auto-refreshes open tabs.
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
  function big(n) {
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
  function dir(p) { p = Number(p); return p > 0 ? "up" : (p < 0 ? "down" : "flat"); }
  function arrow(d) { return d === "up" ? "▲" : (d === "down" ? "▼" : "—"); }
  function niceDate(iso) {
    if (!iso) return "";
    var p = iso.split("-");
    if (p.length !== 3) return iso;
    var mo = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
    return Number(p[2]) + " " + mo[Number(p[1]) - 1] + " " + p[0];
  }
  // Source indices are ALL CAPS; title-case them but keep ZSE/ETF/ICT acronyms.
  function label(name) {
    var keep = { ZSE: 1, ETF: 1, TOP: 0 };
    return String(name || "").toLowerCase().replace(/\b([a-z0-9]+)\b/g, function (w) {
      var u = w.toUpperCase();
      if (u === "ZSE" || u === "ETF" || u === "ICT") return u;
      return w.charAt(0).toUpperCase() + w.slice(1);
    });
  }

  function style() {
    if (document.getElementById("zse-eod-style")) return;
    var s = document.createElement("style");
    s.id = "zse-eod-style";
    s.textContent = [
      ".zeod{max-width:1100px;margin:20px auto 10px;padding:0 20px;font-family:'Inter',system-ui,sans-serif;color:var(--ink,#1a1a1a);}",
      /* header */
      ".zeod-head{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;border-top:3px solid var(--accent,#c41e1e);padding-top:12px;margin-bottom:16px;}",
      ".zeod-h{font-family:'Playfair Display',Georgia,serif;font-weight:800;font-size:clamp(1.35rem,2.7vw,1.8rem);margin:0;line-height:1;}",
      ".zeod-asof{display:flex;align-items:center;gap:8px;font-size:.8rem;opacity:.7;font-weight:600;}",
      ".zeod-eod{display:inline-block;font-size:.6rem;font-weight:800;letter-spacing:.09em;text-transform:uppercase;color:var(--accent,#c41e1e);border:1px solid currentColor;border-radius:999px;padding:2px 8px;opacity:.9;}",
      /* KPI tiles */
      ".zeod-kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:20px;}",
      ".zeod-kpi{border:1px solid rgba(0,0,0,.12);border-radius:12px;padding:14px 16px;background:var(--paper,#fafaf7);transition:border-color .15s ease,box-shadow .15s ease,transform .15s ease;}",
      ".zeod-kpi:hover{border-color:var(--accent,#c41e1e);box-shadow:0 6px 22px rgba(0,0,0,.06);transform:translateY(-1px);}",
      ".zeod-kpi .lbl{font-size:.6rem;text-transform:uppercase;letter-spacing:.1em;opacity:.55;font-weight:800;}",
      ".zeod-kpi .val{font-family:'Playfair Display',Georgia,serif;font-weight:800;font-size:1.5rem;margin-top:5px;line-height:1;font-variant-numeric:tabular-nums;}",
      ".zeod-kpi .sub{font-size:.74rem;font-weight:800;margin-top:4px;font-variant-numeric:tabular-nums;}",
      ".up{color:#1a7f37;}.down{color:#c41e1e;}.flat{opacity:.5;}",
      /* layout */
      ".zeod-grid{display:grid;grid-template-columns:1.6fr 1fr;gap:22px;align-items:start;}",
      ".zeod-panel{border:1px solid rgba(0,0,0,.1);border-radius:12px;background:var(--paper,#fafaf7);padding:14px 16px 6px;margin-bottom:18px;transition:border-color .15s ease,box-shadow .15s ease;}",
      ".zeod-panel:hover{border-color:var(--accent,#c41e1e);box-shadow:0 6px 22px rgba(0,0,0,.06);}",
      ".zeod-ph{font-size:.62rem;text-transform:uppercase;letter-spacing:.1em;font-weight:800;opacity:.55;margin:0 0 8px;}",
      /* indices — two responsive columns of aligned rows */
      ".zeod-idx{display:grid;grid-template-columns:1fr 1fr;gap:0 28px;}",
      ".zeod-idx .r{display:grid;grid-template-columns:1fr auto 4.6rem;align-items:baseline;gap:8px;padding:7px 0;border-top:1px solid rgba(0,0,0,.07);}",
      ".zeod-idx .r:first-child,.zeod-idx .r:nth-child(2){border-top:0;}",
      ".zeod-idx .n{font-size:.82rem;line-height:1.2;opacity:.82;}",
      ".zeod-idx .v{font-size:.86rem;font-weight:600;text-align:right;font-variant-numeric:tabular-nums;}",
      ".zeod-idx .c{font-size:.82rem;font-weight:700;text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap;}",
      /* movers */
      ".zeod-mv{list-style:none;margin:0;padding:0;}",
      ".zeod-mv li{display:flex;align-items:baseline;justify-content:space-between;gap:10px;padding:7px 0;border-top:1px solid rgba(0,0,0,.07);}",
      ".zeod-mv li:first-child{border-top:0;}",
      ".zeod-mv .s{font-weight:700;font-size:.9rem;letter-spacing:.01em;}",
      ".zeod-mv .p{font-size:.72rem;opacity:.55;margin-left:6px;font-weight:500;font-variant-numeric:tabular-nums;}",
      ".zeod-mv .c{font-weight:800;font-size:.9rem;font-variant-numeric:tabular-nums;white-space:nowrap;}",
      /* notices */
      ".zeod-notices a{display:block;text-decoration:none;color:var(--ink,#1a1a1a);padding:9px 0;border-top:1px solid rgba(0,0,0,.07);}",
      ".zeod-notices a:first-of-type{border-top:0;}",
      ".zeod-notices a:hover .nt{color:var(--accent,#c41e1e);}",
      ".zeod-notices .nd{display:block;font-size:.62rem;text-transform:uppercase;letter-spacing:.06em;opacity:.5;font-weight:800;margin-bottom:3px;}",
      ".zeod-notices .nt{display:block;font-size:.9rem;line-height:1.35;}",
      ".zeod-note{font-size:.72rem;opacity:.5;margin:14px 0 2px;border-left:2px solid var(--accent,#c41e1e);padding-left:9px;}",
      /* responsive */
      "@media(max-width:820px){.zeod-grid{grid-template-columns:1fr;}}",
      "@media(max-width:620px){.zeod-kpis{grid-template-columns:repeat(2,1fr);}.zeod-idx{grid-template-columns:1fr;}}",
      "@media(prefers-color-scheme:dark){.zeod-kpi,.zeod-panel{border-color:rgba(255,255,255,.12);}",
      "  .zeod-idx .r,.zeod-mv li,.zeod-notices a{border-color:rgba(255,255,255,.1);} .up{color:#4ade80;}}"
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
    if (!list || !list.length) return '<li class="flat" style="opacity:.5">No data</li>';
    return list.map(function (m) {
      var d = dir(m.change_pct);
      var price = m.price != null ? '<span class="p">' + esc(commas(m.price, 2)) + "</span>" : "";
      return '<li><span class="s">' + esc(m.symbol || m.name) + price + "</span>" +
        '<span class="c ' + d + '">' + arrow(d) + " " + esc(pct(m.change_pct)) + "</span></li>";
    }).join("");
  }

  function render(d) {
    style();
    var a = d.activity || {};
    var as = allShare(d);

    var idxRows = (d.indices || []).map(function (x) {
      return '<div class="r"><span class="n">' + esc(label(x.name)) + '</span>' +
        '<span class="v">' + esc(commas(x.value, 2)) + '</span>' +
        '<span class="c ' + esc(x.direction) + '">' + arrow(x.direction) + " " + esc(pct(x.change_pct)) + "</span></div>";
    }).join("");

    var notices = (d.notices || []).slice(0, 6).map(function (n) {
      var meta = niceDate(n.date) + (n.category ? " · " + n.category : "");
      var open = n.url ? '<a href="' + esc(n.url) + '" target="_blank" rel="noopener">' : "<a>";
      return open + '<span class="nd">' + esc(meta) + '</span><span class="nt">' + esc(n.title) + "</span></a>";
    }).join("");

    slot.innerHTML =
      '<section class="zeod" aria-label="ZSE end of day">' +
        '<div class="zeod-head"><h2 class="zeod-h">ZSE at the close</h2>' +
          '<span class="zeod-asof">' + esc(niceDate(d.as_of)) + ' · ' + esc(d.currency || "ZWG") +
            ' <span class="zeod-eod">End of day</span></span></div>' +
        '<div class="zeod-kpis">' +
          '<div class="zeod-kpi"><div class="lbl">Trades</div><div class="val">' + esc(commas(a.trades, 0)) + '</div></div>' +
          '<div class="zeod-kpi"><div class="lbl">Turnover</div><div class="val">' + esc(commas(a.turnover, 0)) + '</div></div>' +
          '<div class="zeod-kpi"><div class="lbl">Market cap</div><div class="val">' + esc(big(a.market_cap)) + '</div></div>' +
          '<div class="zeod-kpi"><div class="lbl">All Share</div><div class="val">' + (as ? esc(commas(as.value, 2)) : "—") +
            '</div>' + (as ? '<div class="sub ' + esc(as.direction) + '">' + arrow(as.direction) + " " + esc(pct(as.change_pct)) + '</div>' : "") + '</div>' +
        '</div>' +
        '<div class="zeod-grid">' +
          '<div class="zeod-panel"><p class="zeod-ph">Indices</p><div class="zeod-idx">' + idxRows + '</div></div>' +
          '<div class="zeod-side">' +
            '<div class="zeod-panel"><p class="zeod-ph">Top gainers</p><ol class="zeod-mv">' + moverRows(d.gainers) + '</ol></div>' +
            '<div class="zeod-panel"><p class="zeod-ph">Top losers</p><ol class="zeod-mv">' + moverRows(d.losers) + '</ol></div>' +
          '</div>' +
        '</div>' +
        (notices ? '<div class="zeod-panel zeod-notices"><p class="zeod-ph">Announcements &amp; notices</p>' + notices + '</div>' : "") +
        '<p class="zeod-note">Source: Zimbabwe Stock Exchange, end of day. Figures in ' + esc(d.currency || "ZWG") +
          '. Editorial reference, not investment advice.</p>' +
      '</section>';
  }

  var lastSig = null;
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
  setInterval(load, 5 * 60 * 1000);
})();
