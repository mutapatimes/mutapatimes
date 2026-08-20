/*
 * Site-wide ZSE ticker tape.
 *
 * Inserts a slim scrolling market strip as the first element of <body>
 * (above the masthead), on every page that loads this script. Reads
 * /data/zse-market-activity.json (indices + movers, real daily % change);
 * falls back to /data/zse-ticker.json. Self-contained: injects its own
 * styles, links to /zse, pauses on hover, respects reduced motion. Hidden
 * entirely if no data is available.
 */
(function () {
  "use strict";
  if (document.getElementById("mt-ticker")) return;

  var dataDir = window.MT_DATA_DIR ? "/" + window.MT_DATA_DIR : "/data";
  var mtUrl = window.mtUrl || function (p) { return p; };

  function esc(s) {
    return String(s == null ? "" : s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }
  function num(n, dp) {
    if (n == null || n === "" || isNaN(n)) return null;
    return Number(n).toLocaleString("en-GB", { minimumFractionDigits: dp || 2, maximumFractionDigits: dp || 2 });
  }
  function pctTxt(v) {
    if (v == null || v === "" || isNaN(v)) return "";
    v = Number(v);
    return (v > 0 ? "+" : "") + v.toFixed(2) + "%";
  }
  function cls(v) { v = Number(v); return v > 0 ? "up" : (v < 0 ? "down" : "flat"); }
  function arr(v) { v = Number(v); return v > 0 ? "▲" : (v < 0 ? "▼" : "·"); }

  function style() {
    if (document.getElementById("mt-ticker-style")) return;
    var s = document.createElement("style");
    s.id = "mt-ticker-style";
    s.textContent = [
      "#mt-ticker{background:#141414;color:#f5e8c8;overflow:hidden;position:relative;",
      "  border-bottom:1px solid rgba(245,232,200,.14);font-family:'Inter',system-ui,sans-serif;",
      "  height:34px;display:flex;align-items:center;",
      // Clears the iOS status bar/notch when this page loads inside the
      // native app's edge-to-edge WKWebView (viewport-fit=cover). Resolves
      // to 0 in a normal browser, so this is always safe to include.
      "  padding-top:env(safe-area-inset-top,0px);box-sizing:content-box;}",
      "#mt-ticker .mt-tk-tag{flex:0 0 auto;z-index:2;background:#c41e1e;color:#fff;font-weight:800;",
      "  font-size:.62rem;letter-spacing:.12em;text-transform:uppercase;padding:0 12px;height:34px;",
      "  display:flex;align-items:center;text-decoration:none;}",
      "#mt-ticker .mt-tk-tag:after{content:'';position:absolute;}",
      "#mt-ticker .mt-tk-view{position:relative;flex:1 1 auto;overflow:hidden;height:34px;",
      "  -webkit-mask-image:linear-gradient(90deg,transparent,#000 24px,#000 calc(100% - 24px),transparent);",
      "  mask-image:linear-gradient(90deg,transparent,#000 24px,#000 calc(100% - 24px),transparent);}",
      "#mt-ticker .mt-tk-track{position:absolute;top:0;left:0;display:flex;align-items:center;height:34px;",
      "  white-space:nowrap;will-change:transform;animation:mt-tk-scroll 60s linear infinite;}",
      "#mt-ticker:hover .mt-tk-track{animation-play-state:paused;}",
      "#mt-ticker a.mt-tk-item{display:inline-flex;gap:6px;align-items:baseline;padding:0 16px;",
      "  text-decoration:none;color:#f5e8c8;font-size:.78rem;border-right:1px solid rgba(245,232,200,.1);}",
      "#mt-ticker .mt-tk-nm{opacity:.72;font-weight:600;letter-spacing:.01em;}",
      "#mt-ticker .mt-tk-vl{font-variant-numeric:tabular-nums;font-weight:600;}",
      "#mt-ticker .mt-tk-ch{font-weight:700;font-variant-numeric:tabular-nums;}",
      "#mt-ticker .up{color:#4ade80;}#mt-ticker .down{color:#ff6b6b;}#mt-ticker .flat{opacity:.6;}",
      "@keyframes mt-tk-scroll{from{transform:translateX(0);}to{transform:translateX(-50%);}}",
      "@media(prefers-reduced-motion:reduce){#mt-ticker .mt-tk-track{animation:none;}",
      "  #mt-ticker .mt-tk-view{overflow-x:auto;}}"
    ].join("");
    document.head.appendChild(s);
  }

  function itemHtml(name, value, changePct) {
    var ch = (changePct === "" || changePct == null) ? "" :
      '<span class="mt-tk-ch ' + cls(changePct) + '">' + arr(changePct) + " " + esc(pctTxt(changePct)) + "</span>";
    var vl = value == null ? "" : '<span class="mt-tk-vl">' + esc(value) + "</span>";
    return '<a class="mt-tk-item" href="' + mtUrl("/zse") + '">' +
      '<span class="mt-tk-nm">' + esc(name) + "</span>" + vl + ch + "</a>";
  }

  function fromActivity(d) {
    var out = [];
    (d.indices || []).forEach(function (x) {
      out.push(itemHtml(x.name, num(x.value), x.change_pct));
    });
    (d.gainers || []).slice(0, 3).forEach(function (m) {
      out.push(itemHtml(m.symbol || m.name, num(m.price), m.change_pct));
    });
    (d.losers || []).slice(0, 3).forEach(function (m) {
      out.push(itemHtml(m.symbol || m.name, num(m.price), m.change_pct));
    });
    return out;
  }

  function fromTicker(d) {
    return (d.tickers || []).map(function (t) {
      return itemHtml(t.company, num(t.price), t.day_change || "");
    });
  }

  var lastSig = null;

  function mount(items, asOf, sig) {
    if (!items.length || sig === lastSig) return;
    lastSig = sig;
    style();
    var seq = items.join("");
    var track = '<div class="mt-tk-view"><div class="mt-tk-track">' + seq + seq + "</div></div>";
    var tag = '<a class="mt-tk-tag" href="' + mtUrl("/zse") + '" title="ZSE at the close' +
      (asOf ? " · " + esc(asOf) + " · end of day" : "") + '">ZSE</a>';
    var bar = document.getElementById("mt-ticker");
    if (bar) {
      bar.innerHTML = tag + track;   // refresh in place
    } else {
      bar = document.createElement("div");
      bar.id = "mt-ticker";
      bar.setAttribute("aria-label", "ZSE market ticker (end of day)");
      bar.innerHTML = tag + track;
      document.body.insertBefore(bar, document.body.firstChild);
    }
  }

  // Coarse 5-minute cache-bust: everyone in the same window shares one
  // cached response, but stale data never lingers longer than that.
  function bust(u) { return u + (u.indexOf("?") < 0 ? "?" : "&") + "t=" + Math.floor(Date.now() / 300000); }

  function get(url, cb) {
    var x = new XMLHttpRequest();
    x.open("GET", bust(url), true);
    x.onreadystatechange = function () {
      if (x.readyState !== 4) return;
      if (x.status >= 200 && x.status < 300) {
        try { cb(JSON.parse(x.responseText)); return; } catch (e) {}
      }
      cb(null);
    };
    x.send();
  }

  function load() {
    get(dataDir + "/zse-market-activity.json", function (d) {
      if (d && ((d.indices && d.indices.length) || (d.gainers && d.gainers.length))) {
        mount(fromActivity(d), d.as_of, (d.fetched_at || "") + "|" + (d.as_of || ""));
        return;
      }
      get(dataDir + "/zse-ticker.json", function (t) {
        if (t) mount(fromTicker(t), null, t.fetched_at || "ticker");
      });
    });
  }

  load();
  // Auto-refresh so a left-open tab picks up the new close without a reload.
  setInterval(load, 5 * 60 * 1000);
})();
