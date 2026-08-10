/*
 * VFEX scrolling market strip — same visual language as the site-wide ZSE
 * ticker (js/ticker-tape.js), but scoped: mounts into #vfex-ticker wherever
 * that element exists (currently /markets.html) rather than injecting itself
 * fixed at the top of every page. VFEX doesn't have a dedicated directory
 * page the way /zse/ does, so this stays local to the markets page instead
 * of joining the global ticker.
 *
 * Reads /data/vfex-market-activity.json (index + movers, real daily %
 * change). Hidden entirely if no data is available.
 */
(function () {
  "use strict";
  var mount = document.getElementById("vfex-ticker");
  if (!mount) return;

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
    if (document.getElementById("vfex-tk-style")) return;
    var s = document.createElement("style");
    s.id = "vfex-tk-style";
    s.textContent = [
      "#vfex-ticker .vfex-tk-bar{background:#141414;color:#f5e8c8;overflow:hidden;position:relative;",
      "  border-radius:8px;font-family:'Inter',system-ui,sans-serif;height:34px;display:flex;align-items:center;}",
      "#vfex-ticker .vfex-tk-tag{flex:0 0 auto;background:#c41e1e;color:#fff;font-weight:800;",
      "  font-size:.62rem;letter-spacing:.12em;text-transform:uppercase;padding:0 12px;height:34px;",
      "  display:flex;align-items:center;}",
      "#vfex-ticker .vfex-tk-view{position:relative;flex:1 1 auto;overflow:hidden;height:34px;",
      "  -webkit-mask-image:linear-gradient(90deg,transparent,#000 24px,#000 calc(100% - 24px),transparent);",
      "  mask-image:linear-gradient(90deg,transparent,#000 24px,#000 calc(100% - 24px),transparent);}",
      "#vfex-ticker .vfex-tk-track{position:absolute;top:0;left:0;display:flex;align-items:center;height:34px;",
      "  white-space:nowrap;will-change:transform;animation:vfex-tk-scroll 45s linear infinite;}",
      "#vfex-ticker .vfex-tk-bar:hover .vfex-tk-track{animation-play-state:paused;}",
      "#vfex-ticker .vfex-tk-item{display:inline-flex;gap:6px;align-items:baseline;padding:0 16px;",
      "  font-size:.78rem;border-right:1px solid rgba(245,232,200,.1);}",
      "#vfex-ticker .vfex-tk-nm{opacity:.72;font-weight:600;letter-spacing:.01em;}",
      "#vfex-ticker .vfex-tk-vl{font-variant-numeric:tabular-nums;font-weight:600;}",
      "#vfex-ticker .vfex-tk-ch{font-weight:700;font-variant-numeric:tabular-nums;}",
      "#vfex-ticker .up{color:#4ade80;}#vfex-ticker .down{color:#ff6b6b;}#vfex-ticker .flat{opacity:.6;}",
      "@keyframes vfex-tk-scroll{from{transform:translateX(0);}to{transform:translateX(-50%);}}",
      "@media(prefers-reduced-motion:reduce){#vfex-ticker .vfex-tk-track{animation:none;}",
      "  #vfex-ticker .vfex-tk-view{overflow-x:auto;}}"
    ].join("");
    document.head.appendChild(s);
  }

  function itemHtml(name, value, changePct) {
    var ch = (changePct === "" || changePct == null) ? "" :
      '<span class="vfex-tk-ch ' + cls(changePct) + '">' + arr(changePct) + " " + esc(pctTxt(changePct)) + "</span>";
    var vl = value == null ? "" : '<span class="vfex-tk-vl">' + esc(value) + "</span>";
    return '<span class="vfex-tk-item">' +
      '<span class="vfex-tk-nm">' + esc(name) + "</span>" + vl + ch + "</span>";
  }

  function fromActivity(d) {
    var out = [];
    (d.indices || []).forEach(function (x) {
      out.push(itemHtml(x.name, num(x.value), x.change_pct));
    });
    (d.gainers || []).forEach(function (m) {
      out.push(itemHtml(m.symbol || m.name, num(m.price), m.change_pct));
    });
    (d.losers || []).forEach(function (m) {
      out.push(itemHtml(m.symbol || m.name, num(m.price), m.change_pct));
    });
    return out;
  }

  function render(items, asOf) {
    style();
    var seq = items.join("");
    var track = '<div class="vfex-tk-view"><div class="vfex-tk-track">' + seq + seq + "</div></div>";
    var tag = '<span class="vfex-tk-tag" title="VFEX at the close' +
      (asOf ? " · " + esc(asOf) + " · end of day" : "") + '">VFEX</span>';
    mount.innerHTML = '<div class="vfex-tk-bar" aria-label="VFEX market ticker (end of day)">' + tag + track + "</div>";
  }

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

  var lastSig = null;
  function load() {
    get(dataDir + "/vfex-market-activity.json", function (d) {
      if (!d || (!(d.indices && d.indices.length) && !(d.gainers && d.gainers.length))) return;
      var sig = (d.fetched_at || "") + "|" + (d.as_of || "");
      if (sig === lastSig) return;
      lastSig = sig;
      render(fromActivity(d), d.as_of);
    });
  }

  load();
  setInterval(load, 5 * 60 * 1000);
})();
