/* sport.js — renders the /sport section from data/sport/*.json.
 *
 * Static site: a scheduled job (scripts/fetch_sport.py) writes the JSON; this
 * renders it client-side. Two page modes, chosen by #sport-app[data-page]:
 *   hub    → scores strip + a card per league (mini table + link)
 *   league → full table + results + fixtures for one league (data-slug)
 * Data is shared across editions (same /data/sport), so no region prefix.
 */
(function () {
  "use strict";
  var BASE = "/data/sport";
  var app = document.getElementById("sport-app");
  if (!app) return;

  function el(tag, cls, txt) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (txt != null) e.textContent = txt;
    return e;
  }
  function getJSON(url) {
    return fetch(url, { cache: "no-store" }).then(function (r) {
      if (!r.ok) throw new Error(r.status);
      return r.json();
    });
  }
  function fmtScore(v) { return (v === null || v === undefined || v === "") ? "" : v; }
  function ago(iso) {
    if (!iso) return "";
    var t = new Date(iso).getTime();
    if (isNaN(t)) return "";
    var m = Math.round((Date.now() - t) / 60000);
    if (m < 1) return "just now";
    if (m < 60) return m + " min ago";
    var h = Math.round(m / 60);
    if (h < 24) return h + "h ago";
    return Math.round(h / 24) + "d ago";
  }

  // ── standings table ───────────────────────────────────────────────────
  // Column sets. Mini (hub cards) drops W/D/L/GD so the club name gets room;
  // full (league page) shows everything, with W/D/L/GD hidden on phones (.opt).
  var COLS_FULL = [
    { label: "#", key: "rank", cls: "rank" },
    { label: "Team", key: "team", cls: "team" },
    { label: "P", key: "played", cls: "num opt" },
    { label: "W", key: "win", cls: "num opt" },
    { label: "D", key: "draw", cls: "num opt" },
    { label: "L", key: "loss", cls: "num opt" },
    { label: "GD", key: "gd", cls: "num opt" },
    { label: "Pts", key: "points", cls: "num pts" }
  ];
  var COLS_MINI = [
    { label: "#", key: "rank", cls: "rank" },
    { label: "Team", key: "team", cls: "team" },
    { label: "P", key: "played", cls: "num" },
    { label: "Pts", key: "points", cls: "num pts" }
  ];

  function teamCell(r) {
    var td = el("td", "team");
    var inner = el("div", "team-inner");   // flex lives here, NOT on the <td>
    if (r.badge) {
      var img = el("img", "badge"); img.src = r.badge; img.alt = ""; img.loading = "lazy";
      img.width = 18; img.height = 18; inner.appendChild(img);
    }
    inner.appendChild(el("span", "team-name", r.team || ""));
    td.appendChild(inner);
    return td;
  }

  function tableEl(rows, mode) {
    var cols = mode === "mini" ? COLS_MINI : COLS_FULL;
    var t = el("table", "sport-table sport-table--" + (mode || "full"));
    var thead = el("thead"), hr = el("tr");
    cols.forEach(function (c) { hr.appendChild(el("th", c.cls, c.label)); });
    thead.appendChild(hr); t.appendChild(thead);
    var tb = el("tbody");
    rows.forEach(function (r) {
      var tr = el("tr");
      cols.forEach(function (c) {
        if (c.key === "team") { tr.appendChild(teamCell(r)); return; }
        var v = r[c.key];
        if (c.key === "gd") v = (v === null || v === undefined) ? "" : (v > 0 ? "+" + v : v);
        tr.appendChild(el("td", c.cls, v));
      });
      tb.appendChild(tr);
    });
    t.appendChild(tb);
    return t;
  }

  function matchRow(m, withDate) {
    var row = el("div", "sport-match");
    if (withDate) row.appendChild(el("span", "sport-match-date", m.date || ""));
    row.appendChild(el("span", "sport-match-home", m.home || ""));
    var sc = (m.hs === null || m.hs === undefined || m.hs === "")
      ? (m.time || "v")
      : (fmtScore(m.hs) + " - " + fmtScore(m.as));
    row.appendChild(el("span", "sport-match-score", sc));
    row.appendChild(el("span", "sport-match-away", m.away || ""));
    return row;
  }

  function cappedNote() {
    var p = el("p", "sport-capped");
    p.textContent = "Live top 5 shown. Full table coming soon.";
    return p;
  }

  // ── hub ───────────────────────────────────────────────────────────────
  function renderHub(lead) {
    getJSON(BASE + "/index.json").then(function (idx) {
      var leagues = (idx.leagues || []).slice();
      if (lead) leagues.sort(function (a, b) {
        return (a.slug === lead ? -1 : 0) - (b.slug === lead ? -1 : 0);
      });
      app.innerHTML = "";
      var strip = el("div", "sport-strip");
      strip.appendChild(el("span", "sport-strip-label", "Latest"));
      app.appendChild(strip);
      var grid = el("div", "sport-grid");
      app.appendChild(grid);
      leagues.forEach(function (lg) {
        var card = el("article", "sport-card");
        var head = el("a", "sport-card-head"); head.href = "/sport/" + lg.slug;
        head.appendChild(el("span", "sport-card-flag", lg.flag || ""));
        var ht = el("span", "sport-card-titles");
        ht.appendChild(el("strong", null, lg.name));
        ht.appendChild(el("span", "sport-card-sub", lg.country + (lg.season ? " · " + lg.season : "")));
        head.appendChild(ht);
        card.appendChild(head);
        var body = el("div", "sport-card-body");
        body.appendChild(el("p", "sport-loading", "Loading…"));
        card.appendChild(body);
        var foot = el("a", "sport-card-more"); foot.href = "/sport/" + lg.slug;
        foot.textContent = "Full table, results & fixtures →";
        card.appendChild(foot);
        grid.appendChild(card);

        getJSON(BASE + "/" + lg.slug + ".json").then(function (d) {
          body.innerHTML = "";
          if (d.table && d.table.length) {
            body.appendChild(tableEl(d.table.slice(0, 5), "mini"));
            if (d.capped) body.appendChild(cappedNote());
          } else {
            body.appendChild(el("p", "sport-empty", "Standings updating…"));
          }
          (d.results || []).slice(0, 3).forEach(function (m) {
            strip.appendChild(chip(lg, m));
          });
        }).catch(function () {
          body.innerHTML = ""; body.appendChild(el("p", "sport-empty", "Data updating…"));
        });
      });
    }).catch(function () {
      app.innerHTML = ""; app.appendChild(el("p", "sport-empty", "Sport data is updating. Check back shortly."));
    });
  }
  function chip(lg, m) {
    var c = el("a", "sport-chip"); c.href = "/sport/" + lg.slug;
    c.appendChild(el("span", "sport-chip-league", (lg.flag || "") + " " + (lg.short || "")));
    var sc = (m.hs === null || m.hs === undefined || m.hs === "") ? "v" : (m.hs + "-" + m.as);
    c.appendChild(el("span", "sport-chip-teams", (m.home || "") + " " + sc + " " + (m.away || "")));
    return c;
  }

  // ── league ─────────────────────────────────────────────────────────────
  function renderLeague(slug) {
    getJSON(BASE + "/" + slug + ".json").then(function (d) {
      app.innerHTML = "";
      var meta = el("p", "sport-league-meta");
      meta.textContent = (d.country || "") + (d.season ? " · " + d.season : "") +
        (d.updated ? " · updated " + ago(d.updated) : "");
      app.appendChild(meta);

      if (d.table && d.table.length) {
        app.appendChild(tableEl(d.table, "full"));
        if (d.capped) app.appendChild(cappedNote());
      } else {
        app.appendChild(el("p", "sport-empty", "Standings updating…"));
      }

      var cols = el("div", "sport-cols");
      var resCol = el("section", "sport-col");
      resCol.appendChild(el("h2", "sport-col-h", "Recent results"));
      if ((d.results || []).length) d.results.forEach(function (m) { resCol.appendChild(matchRow(m, true)); });
      else resCol.appendChild(el("p", "sport-empty", "No recent results."));
      cols.appendChild(resCol);

      var fixCol = el("section", "sport-col");
      fixCol.appendChild(el("h2", "sport-col-h", "Upcoming fixtures"));
      if ((d.fixtures || []).length) d.fixtures.forEach(function (m) { fixCol.appendChild(matchRow(m, true)); });
      else fixCol.appendChild(el("p", "sport-empty", "No fixtures listed yet."));
      cols.appendChild(fixCol);
      app.appendChild(cols);
    }).catch(function () {
      app.innerHTML = ""; app.appendChild(el("p", "sport-empty", "This league's data is updating. Check back shortly."));
    });
  }

  // ── editorial (Kundai Kaycee columns + sport reads) ─────────────────────
  function fmtDate(iso) {
    var d = new Date(iso);
    if (isNaN(d)) return "";
    return d.toLocaleDateString("en-GB", { day: "numeric", month: "short" });
  }
  function edMeta(a) {
    var meta = el("p", "sport-ed-meta");
    meta.textContent = (a.author || "") + (a.date ? " · " + fmtDate(a.date) : "");
    return meta;
  }
  function edTag(a, heroFallback) {
    if (a.is_column) return el("span", "sport-ed-tag", "Column");
    if (heroFallback) return el("span", "sport-ed-tag sport-ed-tag--muted", "Featured");
    return null;
  }
  function edCard(a) {
    var card = el("a", "sport-ed-card"); card.href = a.url;
    if (a.card_image) {
      var im = el("img", "sport-ed-img"); im.src = a.card_image; im.alt = "";
      im.loading = "lazy"; im.onerror = function () { this.style.display = "none"; };
      card.appendChild(im);
    }
    var b = el("div", "sport-ed-body");
    var tag = edTag(a, false); if (tag) b.appendChild(tag);
    b.appendChild(el("h3", "sport-ed-h", a.title || ""));
    b.appendChild(edMeta(a));
    card.appendChild(b);
    return card;
  }
  function edHero(a) {
    var h = el("a", "sport-ed-hero"); h.href = a.url;
    if (a.card_image) {
      var im = el("img", "sport-ed-hero-img"); im.src = a.card_image; im.alt = "";
      im.loading = "lazy";
      im.onerror = function () { h.classList.add("no-img"); this.style.display = "none"; };
      h.appendChild(im);
    } else { h.classList.add("no-img"); }
    var b = el("div", "sport-ed-hero-body");
    b.appendChild(edTag(a, true));
    b.appendChild(el("h3", "sport-ed-hero-h", a.title || ""));
    b.appendChild(edMeta(a));
    h.appendChild(b);
    return h;
  }
  function renderEditorial() {
    var host = document.getElementById("sport-editorial");
    if (!host) return;
    getJSON(BASE + "/editorial.json").then(function (d) {
      var items = d.items || [];
      host.innerHTML = "";
      var head = el("div", "sport-ed-head");
      head.appendChild(el("h2", "sport-ed-title", "From the Sport Desk"));
      head.appendChild(el("p", "sport-ed-by", "Opinion and analysis by Kundai Kaycee"));
      host.appendChild(head);
      if (!items.length) {
        host.appendChild(el("p", "sport-empty", "Columns from the sport desk are coming soon."));
        return;
      }
      host.appendChild(edHero(items[0]));                 // lead story
      var rest = items.slice(1, 7);                       // then a tidy two-column list
      if (rest.length) {
        var grid = el("div", "sport-ed-grid");
        rest.forEach(function (a) { grid.appendChild(edCard(a)); });
        host.appendChild(grid);
      }
    }).catch(function () { /* section stays empty on error */ });
  }

  var page = app.getAttribute("data-page");
  if (page === "league") renderLeague(app.getAttribute("data-slug"));
  else renderHub(app.getAttribute("data-lead") || "");
  renderEditorial();
})();
