/*
 * ZSE index history chart (1M / 3M / 6M / YTD / All).
 *
 * Reads /data/zse-history.json (accumulated one entry per trading day by
 * scripts/fetch_zse_market.py) and draws a self-contained inline-SVG line
 * chart into #zse-chart. No charting library, no new fonts — uses the site
 * design tokens (Playfair/Inter, --paper/--ink/--accent). Index selector +
 * range toggle. There is no public ZSE history feed, so the series builds
 * forward from each day's close; a graceful state shows while it is short.
 */
(function () {
  "use strict";
  var slot = document.getElementById("zse-chart");
  if (!slot) return;

  var DATA_URL = (window.MT_DATA_DIR ? "/" + window.MT_DATA_DIR : "/data") + "/zse-history.json";
  var RANGES = [["1M", 31], ["3M", 93], ["6M", 183], ["YTD", "ytd"], ["All", "all"]];
  var GREEN = "#1a7f37", RED = "#c41e1e";

  function esc(s) { return String(s == null ? "" : s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;"); }
  function commas(n, dp) {
    if (n == null || isNaN(n)) return "—";
    return Number(n).toLocaleString("en-GB", { minimumFractionDigits: dp || 2, maximumFractionDigits: dp || 2 });
  }
  function niceDate(iso) {
    if (!iso) return "";
    var p = iso.split("-"), mo = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
    return p.length === 3 ? Number(p[2]) + " " + mo[Number(p[1]) - 1] + " " + p[0] : iso;
  }
  function label(name) {
    return String(name || "").toLowerCase().replace(/\b([a-z0-9]+)\b/g, function (w) {
      var u = w.toUpperCase();
      if (u === "ZSE" || u === "ETF" || u === "ICT") return u;
      return w.charAt(0).toUpperCase() + w.slice(1);
    });
  }
  function daysBetween(a, b) { return Math.round((Date.parse(b) - Date.parse(a)) / 86400000); }
  function rangeVal(label) {
    for (var i = 0; i < RANGES.length; i++) if (RANGES[i][0] === label) return RANGES[i][1];
    return "all";
  }

  function style() {
    if (document.getElementById("zse-chart-style")) return;
    var s = document.createElement("style");
    s.id = "zse-chart-style";
    s.textContent = [
      ".zch{max-width:1100px;margin:8px auto 20px;padding:0 20px;font-family:'Inter',system-ui,sans-serif;color:var(--ink,#1a1a1a);}",
      ".zch-panel{border:1px solid rgba(0,0,0,.1);border-radius:12px;background:var(--paper,#fafaf7);padding:16px 18px;}",
      ".zch-top{display:flex;align-items:flex-end;justify-content:space-between;gap:12px;flex-wrap:wrap;margin-bottom:12px;}",
      ".zch-h{font-family:'Playfair Display',Georgia,serif;font-weight:800;font-size:1.15rem;margin:0 0 4px;}",
      ".zch-now{font-variant-numeric:tabular-nums;}",
      ".zch-now .v{font-family:'Playfair Display',Georgia,serif;font-weight:800;font-size:1.5rem;}",
      ".zch-now .c{font-weight:800;font-size:.85rem;margin-left:8px;}",
      ".up{color:#1a7f37;}.down{color:#c41e1e;}",
      ".zch-sel{font-family:inherit;font-size:.8rem;padding:5px 8px;border:1px solid rgba(0,0,0,.2);border-radius:7px;background:#fff;color:#1a1a1a;max-width:100%;}",
      ".zch-ranges{display:flex;gap:6px;flex-wrap:wrap;margin:10px 0 4px;}",
      ".zch-rb{font-family:inherit;font-size:.72rem;font-weight:700;letter-spacing:.02em;padding:5px 11px;border:1px solid rgba(0,0,0,.18);",
      "  border-radius:999px;background:transparent;color:var(--ink,#1a1a1a);cursor:pointer;opacity:.72;}",
      ".zch-rb.on{background:var(--accent,#c41e1e);border-color:var(--accent,#c41e1e);color:#fff;opacity:1;}",
      ".zch-svg{width:100%;height:auto;display:block;margin-top:8px;overflow:visible;}",
      ".zch-ax{font-size:.62rem;opacity:.55;font-variant-numeric:tabular-nums;}",
      ".zch-empty{padding:22px 4px;font-size:.86rem;opacity:.7;line-height:1.5;}",
      ".zch-note{font-size:.7rem;opacity:.5;margin:10px 0 0;}",
      "@media(prefers-color-scheme:dark){.zch-panel{border-color:rgba(255,255,255,.12);}",
      "  .zch-sel{background:#14201a;color:#f4ede0;border-color:rgba(255,255,255,.2);} .up{color:#4ade80;}",
      "  .zch-rb{border-color:rgba(255,255,255,.2);color:#f4ede0;}}"
    ].join("\n");
    document.head.appendChild(s);
  }

  var HIST = null, curIndex = "ALL SHARE", curRange = "6M";

  function allIndexNames(series) {
    var seen = {}, names = [];
    series.forEach(function (e) { Object.keys(e.idx || {}).forEach(function (k) { if (!seen[k]) { seen[k] = 1; names.push(k); } }); });
    // marquee names first
    var lead = ["ALL SHARE", "ZSE TOP 10", "ZSE TOP 15", "MID CAP INDEX", "SMALL CAP INDEX"];
    names.sort(function (a, b) {
      var ia = lead.indexOf(a), ib = lead.indexOf(b);
      return (ia < 0 ? 99 : ia) - (ib < 0 ? 99 : ib) || a.localeCompare(b);
    });
    return names;
  }

  function pointsFor(series, index, range) {
    var pts = [];
    series.forEach(function (e) {
      var v = e.idx && e.idx[index];
      if (v != null) pts.push({ d: e.d, v: Number(v) });
    });
    if (!pts.length) return pts;
    var last = pts[pts.length - 1].d;
    if (range === "all") return pts;
    if (range === "ytd") {
      var y = last.slice(0, 4);
      return pts.filter(function (p) { return p.d >= y + "-01-01"; });
    }
    return pts.filter(function (p) { return daysBetween(p.d, last) <= range; });
  }

  function svg(pts) {
    var W = 1000, H = 260, padL = 8, padR = 8, padT = 12, padB = 22;
    var vals = pts.map(function (p) { return p.v; });
    var min = Math.min.apply(null, vals), max = Math.max.apply(null, vals);
    if (min === max) { min -= 1; max += 1; }
    var n = pts.length;
    function x(i) { return padL + (n === 1 ? (W - padL - padR) / 2 : i * (W - padL - padR) / (n - 1)); }
    function y(v) { return padT + (max - v) * (H - padT - padB) / (max - min); }
    var line = pts.map(function (p, i) { return (i ? "L" : "M") + x(i).toFixed(1) + " " + y(p.v).toFixed(1); }).join(" ");
    var area = line + " L" + x(n - 1).toFixed(1) + " " + (H - padB) + " L" + x(0).toFixed(1) + " " + (H - padB) + " Z";
    var rising = pts[n - 1].v >= pts[0].v;
    var col = rising ? GREEN : RED;
    var dots = n <= 30 ? pts.map(function (p, i) {
      return '<circle cx="' + x(i).toFixed(1) + '" cy="' + y(p.v).toFixed(1) + '" r="' + (n === 1 ? 4 : 2.5) + '" fill="' + col + '"/>';
    }).join("") : "";
    return '<svg class="zch-svg" viewBox="0 0 ' + W + ' ' + H + '" preserveAspectRatio="none" role="img" aria-label="ZSE index history">' +
      '<defs><linearGradient id="zchg" x1="0" y1="0" x2="0" y2="1">' +
        '<stop offset="0" stop-color="' + col + '" stop-opacity="0.16"/>' +
        '<stop offset="1" stop-color="' + col + '" stop-opacity="0"/></linearGradient></defs>' +
      '<path d="' + area + '" fill="url(#zchg)"/>' +
      '<path d="' + line + '" fill="none" stroke="' + col + '" stroke-width="2.2" stroke-linejoin="round" stroke-linecap="round"/>' +
      dots +
      '<text class="zch-ax" x="' + padL + '" y="10">' + commas(max, 2) + '</text>' +
      '<text class="zch-ax" x="' + padL + '" y="' + (H - 6) + '">' + commas(min, 2) + '</text>' +
      '<text class="zch-ax" x="' + (W - padR) + '" y="' + (H - 6) + '" text-anchor="end">' + niceDate(pts[n - 1].d) + '</text>' +
      '<text class="zch-ax" x="' + padL + '" y="' + (H - 6) + '" dx="46">' + niceDate(pts[0].d) + '</text>' +
      '</svg>';
  }

  function draw() {
    var series = (HIST && HIST.series) || [];
    var pts = pointsFor(series, curIndex, rangeVal(curRange));
    var body = document.getElementById("zch-body");
    if (!body) return;
    if (pts.length < 2) {
      var one = pts.length === 1 ? pts[0] : null;
      body.innerHTML = '<div class="zch-empty"><strong>Building price history.</strong> ' +
        (one ? "So far one trading day is recorded (" + esc(niceDate(one.d)) + ", " + esc(label(curIndex)) +
          " " + esc(commas(one.v, 2)) + "). " : "") +
        "The line fills in after each trading day, so 1M, 3M, 6M, YTD and all-time views grow automatically. " +
        "There is no public ZSE history feed to backfill from.</div>";
      var nowEl = document.getElementById("zch-now");
      if (nowEl) nowEl.innerHTML = one ? '<span class="v">' + esc(commas(one.v, 2)) + "</span>" : "";
      return;
    }
    var first = pts[0].v, last = pts[pts.length - 1].v;
    var chg = first ? ((last - first) / first) * 100 : 0;
    var cls = chg > 0 ? "up" : (chg < 0 ? "down" : "");
    var nowEl2 = document.getElementById("zch-now");
    if (nowEl2) {
      nowEl2.innerHTML = '<span class="v">' + esc(commas(last, 2)) + '</span>' +
        '<span class="c ' + cls + '">' + (chg > 0 ? "+" : "") + chg.toFixed(2) + "% " + curRange + "</span>";
    }
    body.innerHTML = svg(pts);
  }

  function render() {
    style();
    var series = (HIST && HIST.series) || [];
    var names = allIndexNames(series);
    if (names.length && names.indexOf(curIndex) < 0) curIndex = names[0];
    var opts = names.map(function (nm) {
      return '<option value="' + esc(nm) + '"' + (nm === curIndex ? " selected" : "") + ">" + esc(label(nm)) + "</option>";
    }).join("");
    var rbtns = RANGES.map(function (r) {
      return '<button class="zch-rb' + (r[0] === curRange ? " on" : "") + '" data-r="' + r[0] + '">' + r[0] + "</button>";
    }).join("");
    slot.innerHTML =
      '<section class="zch"><div class="zch-panel">' +
        '<div class="zch-top">' +
          '<div><h3 class="zch-h">Index history</h3><div id="zch-now" class="zch-now"></div></div>' +
          '<select class="zch-sel" id="zch-sel" aria-label="Choose index">' + opts + '</select>' +
        '</div>' +
        '<div class="zch-ranges">' + rbtns + '</div>' +
        '<div id="zch-body"></div>' +
        '<p class="zch-note">End-of-day closes, accumulated from ' +
          (series.length ? esc(niceDate(series[0].d)) : "the first trading day") +
          '. Editorial reference, not investment advice.</p>' +
      '</div></section>';

    var sel = document.getElementById("zch-sel");
    if (sel) sel.addEventListener("change", function () { curIndex = sel.value; draw(); });
    Array.prototype.forEach.call(slot.querySelectorAll(".zch-rb"), function (b) {
      b.addEventListener("click", function () {
        curRange = b.getAttribute("data-r");
        Array.prototype.forEach.call(slot.querySelectorAll(".zch-rb"), function (x) { x.classList.toggle("on", x === b); });
        draw();
      });
    });
    draw();
  }

  var xhr = new XMLHttpRequest();
  xhr.open("GET", DATA_URL + "?t=" + Math.floor(Date.now() / 300000), true);
  xhr.onreadystatechange = function () {
    if (xhr.readyState !== 4) return;
    if (xhr.status < 200 || xhr.status >= 300) return;
    try { HIST = JSON.parse(xhr.responseText); render(); } catch (e) {}
  };
  xhr.send();
})();
