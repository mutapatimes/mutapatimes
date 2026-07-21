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
  function tableEl(rows, full) {
    var t = el("table", "sport-table" + (full ? " sport-table--full" : ""));
    var thead = el("thead");
    var hr = el("tr");
    ["#", "Team", "P", "W", "D", "L", "GD", "Pts"].forEach(function (h, i) {
      var th = el("th", null, h);
      if (i >= 2 && i <= 6) th.className = "num opt";       // P/W/D/L/GD hide on narrow
      if (i === 7) th.className = "num pts";
      if (i === 1) th.className = "team";
      hr.appendChild(th);
    });
    thead.appendChild(hr); t.appendChild(thead);
    var tb = el("tbody");
    rows.forEach(function (r) {
      var tr = el("tr");
      tr.appendChild(el("td", "rank", r.rank));
      var team = el("td", "team");
      var inner = el("div", "team-inner");   // flex lives here, NOT on the <td>
      if (r.badge) {
        var img = el("img", "badge"); img.src = r.badge; img.alt = ""; img.loading = "lazy";
        img.width = 18; img.height = 18; inner.appendChild(img);
      }
      inner.appendChild(el("span", "team-name", r.team || ""));
      team.appendChild(inner);
      tr.appendChild(team);
      [["played", 0], ["win", 0], ["draw", 0], ["loss", 0]].forEach(function (k) {
        tr.appendChild(el("td", "num opt", r[k[0]]));
      });
      var gd = (r.gd === null || r.gd === undefined) ? "" : (r.gd > 0 ? "+" + r.gd : r.gd);
      tr.appendChild(el("td", "num opt", gd));
      tr.appendChild(el("td", "num pts", r.points));
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
            body.appendChild(tableEl(d.table.slice(0, 5), false));
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
        app.appendChild(tableEl(d.table, true));
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

  var page = app.getAttribute("data-page");
  if (page === "league") renderLeague(app.getAttribute("data-slug"));
  else renderHub(app.getAttribute("data-lead") || "");
})();
