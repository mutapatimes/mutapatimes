/* Mutapa Times Academy — engine.
   Renders the course from window.COURSE. Progress, XP and streak are
   saved in localStorage, so the whole app works with no backend.
   Optional: set GRADE_ENDPOINT to a deployed grading Worker to add AI
   feedback on write exercises; if blank, they fall back to self-check. */

(function () {
  "use strict";

  var GRADE_ENDPOINT = ""; // e.g. "https://academy-grade.NAME.workers.dev"
  var STORE_KEY = "mt_academy_v1";
  var XP_PER_EXERCISE = 10;
  var XP_LESSON_BONUS = 50;

  var COURSE = window.COURSE;
  var view = document.getElementById("view");
  var xpChip = document.getElementById("xpChip");
  var streakChip = document.getElementById("streakChip");

  // ---------- storage ----------
  function load() {
    try {
      var s = JSON.parse(localStorage.getItem(STORE_KEY));
      if (s && typeof s === "object") return s;
    } catch (e) {}
    return { xp: 0, streak: { count: 0, last: "" }, lessons: {} };
  }
  function save() { try { localStorage.setItem(STORE_KEY, JSON.stringify(state)); } catch (e) {} }
  var state = load();

  function today() {
    var d = new Date();
    return d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0");
  }
  function daysBetween(a, b) {
    var pa = a.split("-"), pb = b.split("-");
    var da = Date.UTC(+pa[0], pa[1] - 1, +pa[2]);
    var db = Date.UTC(+pb[0], pb[1] - 1, +pb[2]);
    return Math.round((db - da) / 86400000);
  }
  function touchStreak() {
    var t = today();
    var last = state.streak.last;
    if (last === t) return;
    if (last && daysBetween(last, t) === 1) state.streak.count += 1;
    else state.streak.count = 1;
    state.streak.last = t;
  }

  // ---------- helpers ----------
  function allLessons() {
    var out = [];
    COURSE.units.forEach(function (u) { u.lessons.forEach(function (l) { out.push(l); }); });
    return out;
  }
  function lessonState(id) { return state.lessons[id] || (state.lessons[id] = { done: false, exercises: {} }); }
  function courseProgress() {
    var total = allLessons().length, done = 0;
    allLessons().forEach(function (l) { if (lessonState(l.id).done) done++; });
    return { done: done, total: total, pct: total ? Math.round(done / total * 100) : 0 };
  }
  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }
  function clear(n) { while (n.firstChild) n.removeChild(n.firstChild); }
  function go(hash) { location.hash = hash; }

  function renderChips() {
    xpChip.textContent = state.xp + " XP";
    var c = state.streak.count;
    streakChip.textContent = (c > 0 ? c : 0) + (c === 1 ? " day" : " days");
    streakChip.classList.toggle("is-live", c > 0 && state.streak.last === today());
  }

  // ---------- home / lesson map ----------
  function renderHome() {
    clear(view);
    renderChips();
    var prog = courseProgress();

    var head = el("div", "ac-home-head");
    head.appendChild(el("p", "ac-eyebrow", "Mutapa Times Academy"));
    head.appendChild(el("h1", "ac-h1", "Learn to report Zimbabwe"));
    head.appendChild(el("p", "ac-lead", COURSE.blurb));
    view.appendChild(head);

    // overall progress
    var pwrap = el("div", "ac-overall");
    var bar = el("div", "ac-progress"); var fill = el("i"); fill.style.width = prog.pct + "%"; bar.appendChild(fill);
    pwrap.appendChild(bar);
    pwrap.appendChild(el("p", "ac-overall-txt", prog.done + " of " + prog.total + " lessons complete"));
    view.appendChild(pwrap);

    // continue button
    var next = firstUnfinished();
    if (next) {
      var cont = el("button", "ac-btn", (prog.done ? "Continue: " : "Start: ") + next.title);
      cont.addEventListener("click", function () { go("#/lesson/" + next.id); });
      var ca = el("div", "ac-actions"); ca.appendChild(cont); view.appendChild(ca);
    }

    // units and lessons
    COURSE.units.forEach(function (u) {
      var unit = el("section", "ac-unit");
      unit.appendChild(el("h2", "ac-unit-title", u.title));
      if (u.summary) unit.appendChild(el("p", "ac-unit-sum", u.summary));
      var grid = el("div", "ac-lessons");
      u.lessons.forEach(function (l) {
        var ls = lessonState(l.id);
        var card = el("button", "ac-lessoncard" + (ls.done ? " is-done" : ""));
        card.type = "button";
        var badge = el("span", "ac-lc-badge", ls.done ? "✓" : String(l.minutes) + "m");
        card.appendChild(badge);
        var body = el("span", "ac-lc-body");
        body.appendChild(el("span", "ac-lc-title", l.title));
        body.appendChild(el("span", "ac-lc-intro", l.intro));
        card.appendChild(body);
        card.addEventListener("click", function () { go("#/lesson/" + l.id); });
        grid.appendChild(card);
      });
      unit.appendChild(grid);
      view.appendChild(unit);
    });

    window.scrollTo(0, 0);
  }

  function firstUnfinished() {
    var ls = allLessons();
    for (var i = 0; i < ls.length; i++) { if (!lessonState(ls[i].id).done) return ls[i]; }
    return ls[ls.length - 1] || null;
  }
  function findLesson(id) {
    var ls = allLessons();
    for (var i = 0; i < ls.length; i++) { if (ls[i].id === id) return ls[i]; }
    return null;
  }

  // ---------- lesson player ----------
  function renderLesson(id) {
    var lesson = findLesson(id);
    if (!lesson) { go("#/"); return; }
    clear(view); renderChips();

    var top = el("div", "ac-lessontop");
    var back = el("button", "ac-back", "← All lessons");
    back.addEventListener("click", function () { go("#/"); });
    top.appendChild(back);
    view.appendChild(top);

    view.appendChild(el("p", "ac-eyebrow", lesson.title));
    view.appendChild(el("h1", "ac-h1", lesson.intro));

    // reading cards
    lesson.cards.forEach(function (c) {
      var card = el("section", "ac-card");
      card.appendChild(el("p", "ac-kicker", "Read"));
      card.appendChild(el("h2", null, c.h));
      c.body.forEach(function (p) { card.appendChild(el("p", null, p)); });
      view.appendChild(card);
    });

    // exercise area
    var exHost = el("section", "ac-card ac-exhost");
    view.appendChild(exHost);

    var startWrap = el("div", "ac-actions");
    var startBtn = el("button", "ac-btn", "Start the exercises (" + lesson.exercises.length + ")");
    startWrap.appendChild(startBtn);
    exHost.appendChild(startWrap);

    var idx = 0;
    startBtn.addEventListener("click", function () { runExercise(); });

    function runExercise() {
      clear(exHost);
      if (idx >= lesson.exercises.length) { return complete(); }
      var ex = lesson.exercises[idx];
      exHost.appendChild(el("p", "ac-kicker", "Exercise " + (idx + 1) + " of " + lesson.exercises.length));
      var done = function () { lessonState(lesson.id).exercises[idx] = true; save(); };
      var nextStep = function () { idx++; runExercise(); };
      if (ex.type === "mcq" || ex.type === "multi") renderChoice(exHost, ex, done, nextStep);
      else if (ex.type === "order") renderOrder(exHost, ex, done, nextStep);
      else if (ex.type === "write") renderWrite(exHost, ex, done, nextStep);
      else nextStep();
      exHost.scrollIntoView({ behavior: "smooth", block: "start" });
    }

    function complete() {
      clear(exHost);
      var ls = lessonState(lesson.id);
      if (!ls.done) {
        ls.done = true;
        state.xp += lesson.exercises.length * XP_PER_EXERCISE + XP_LESSON_BONUS;
        touchStreak();
        save();
      }
      renderChips();
      var done = el("div", "ac-done-inline");
      done.appendChild(el("p", "mark", "M·T"));
      done.appendChild(el("h2", null, "Lesson complete"));
      done.appendChild(el("p", null, "Nice work. Your progress and streak are saved on this device."));
      var acts = el("div", "ac-actions");
      var nxt = firstUnfinishedAfter(lesson.id);
      if (nxt) {
        var nb = el("button", "ac-btn", "Next: " + nxt.title);
        nb.addEventListener("click", function () { go("#/lesson/" + nxt.id); });
        acts.appendChild(nb);
      }
      var hb = el("button", "ac-btn ac-btn--ghost", "Back to map");
      hb.addEventListener("click", function () { go("#/"); });
      acts.appendChild(hb);
      done.appendChild(acts);
      exHost.appendChild(done);
      exHost.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }

  function firstUnfinishedAfter(id) {
    var ls = allLessons(), seen = false;
    for (var i = 0; i < ls.length; i++) {
      if (seen && !lessonState(ls[i].id).done) return ls[i];
      if (ls[i].id === id) seen = true;
    }
    return null;
  }

  // ---------- exercise renderers ----------
  function feedbackBlock(host, ok, explain, onContinue) {
    var ex = el("p", "ac-explain " + (ok ? "good" : "bad"));
    ex.textContent = (ok ? "Correct. " : "Not quite. ") + (explain || "");
    host.appendChild(ex);
    var acts = el("div", "ac-actions");
    var cont = el("button", "ac-btn", "Continue");
    cont.addEventListener("click", onContinue);
    acts.appendChild(cont);
    host.appendChild(acts);
  }

  function renderChoice(host, ex, done, next) {
    var multi = ex.type === "multi";
    host.appendChild(el("p", "ac-q", ex.q + (multi ? "  (select all that apply)" : "")));
    var opts = el("div", "ac-opts");
    var picked = {};
    var locked = false;
    ex.options.forEach(function (text, i) {
      var b = el("button", "ac-opt"); b.type = "button"; b.textContent = text;
      b.addEventListener("click", function () {
        if (locked) return;
        if (multi) { picked[i] = !picked[i]; b.classList.toggle("is-picked", picked[i]); }
        else { grade([i]); }
      });
      opts.appendChild(b);
    });
    host.appendChild(opts);

    if (multi) {
      var acts = el("div", "ac-actions");
      var check = el("button", "ac-btn", "Check");
      check.addEventListener("click", function () {
        var sel = Object.keys(picked).filter(function (k) { return picked[k]; }).map(Number);
        if (!sel.length) return;
        grade(sel);
      });
      acts.appendChild(check);
      host.appendChild(acts);
    }

    function grade(selected) {
      locked = true;
      var correct = multi ? ex.answers.slice() : [ex.answer];
      var btns = opts.querySelectorAll(".ac-opt");
      btns.forEach(function (b) { b.disabled = true; });
      correct.forEach(function (i) { btns[i].classList.add("is-correct"); });
      selected.forEach(function (i) { if (correct.indexOf(i) === -1) btns[i].classList.add("is-wrong"); });
      var ok = sameSet(selected, correct);
      done();
      feedbackBlock(host, ok, ex.explain, next);
    }
  }
  function sameSet(a, b) {
    if (a.length !== b.length) return false;
    var sa = a.slice().sort(), sb = b.slice().sort();
    for (var i = 0; i < sa.length; i++) if (sa[i] !== sb[i]) return false;
    return true;
  }

  function renderOrder(host, ex, done, next) {
    host.appendChild(el("p", "ac-q", ex.q + "  (use the arrows to reorder)"));
    var order = shuffle(ex.items.map(function (t, i) { return i; }));
    var list = el("div", "ac-order");
    host.appendChild(list);
    function paint() {
      clear(list);
      order.forEach(function (origIdx, pos) {
        var row = el("div", "ac-order-row");
        var ctrl = el("div", "ac-order-ctrl");
        var up = el("button", "ac-arrow", "↑"); up.type = "button"; up.disabled = pos === 0;
        var dn = el("button", "ac-arrow", "↓"); dn.type = "button"; dn.disabled = pos === order.length - 1;
        up.addEventListener("click", function () { swap(pos, pos - 1); });
        dn.addEventListener("click", function () { swap(pos, pos + 1); });
        ctrl.appendChild(up); ctrl.appendChild(dn);
        row.appendChild(ctrl);
        row.appendChild(el("span", "ac-order-txt", ex.items[origIdx]));
        list.appendChild(row);
      });
    }
    function swap(i, j) { var t = order[i]; order[i] = order[j]; order[j] = t; paint(); }
    paint();
    var acts = el("div", "ac-actions");
    var check = el("button", "ac-btn", "Check order");
    check.addEventListener("click", function () {
      var ok = order.every(function (v, i) { return v === i; });
      check.disabled = true;
      list.querySelectorAll(".ac-arrow").forEach(function (a) { a.disabled = true; });
      list.querySelectorAll(".ac-order-row").forEach(function (r, pos) {
        r.classList.add(order[pos] === pos ? "is-correct" : "is-wrong");
      });
      done();
      feedbackBlock(host, ok, ex.explain, next);
    });
    acts.appendChild(check);
    host.appendChild(acts);
  }
  function shuffle(a) {
    a = a.slice();
    for (var i = a.length - 1; i > 0; i--) { var j = Math.floor(Math.random() * (i + 1)); var t = a[i]; a[i] = a[j]; a[j] = t; }
    // guard against the rare already-sorted shuffle so it is never a no-op
    if (a.every(function (v, i) { return v === i; }) && a.length > 1) { var t0 = a[0]; a[0] = a[1]; a[1] = t0; }
    return a;
  }

  function renderWrite(host, ex, done, next) {
    host.appendChild(el("p", "ac-q", ex.q));
    if (ex.brief) {
      var brief = el("div", "ac-brief");
      ex.brief.forEach(function (p) { brief.appendChild(el("p", null, p)); });
      host.appendChild(brief);
    }
    var ta = el("textarea", "ac-input"); ta.setAttribute("maxlength", "900"); ta.placeholder = "Write your answer...";
    host.appendChild(ta);
    var count = el("p", "ac-count", "0 words"); host.appendChild(count);
    ta.addEventListener("input", function () {
      var n = words(ta.value); count.textContent = n + (n === 1 ? " word" : " words");
    });

    var acts = el("div", "ac-actions");
    var submit = el("button", "ac-btn", GRADE_ENDPOINT ? "Get feedback" : "Reveal model answer");
    var status = el("span", "ac-status");
    acts.appendChild(submit); acts.appendChild(status);
    host.appendChild(acts);

    submit.addEventListener("click", function () {
      if (words(ta.value) < 4) { status.innerHTML = '<span class="ac-err">Write a full answer first.</span>'; return; }
      ta.disabled = true; submit.disabled = true;
      if (GRADE_ENDPOINT && ex.exerciseId) {
        status.innerHTML = '<span class="ac-spin">Your editor is reading...</span>';
        fetch(GRADE_ENDPOINT, {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ exerciseId: ex.exerciseId, answer: ta.value.trim() })
        }).then(function (r) { if (!r.ok) throw 0; return r.json(); })
          .then(function (d) { status.textContent = ""; aiResult(d); })
          .catch(function () { status.textContent = ""; selfCheck(); });
      } else {
        selfCheck();
      }
    });

    function aiResult(d) {
      var box = el("div", "ac-result");
      var score = Math.max(0, Math.min(100, parseInt(d.score, 10) || 0));
      var row = el("div", "ac-score " + (score >= 70 ? "pass" : "revise"));
      row.appendChild(el("b", null, String(score)));
      row.appendChild(el("span", null, d.verdict || ""));
      box.appendChild(row);
      if (d.strengths && d.strengths.length) box.appendChild(fbList("What worked", d.strengths));
      if (d.improvements && d.improvements.length) box.appendChild(fbList("Sharpen this", d.improvements));
      if (d.model_answer) box.appendChild(model(d.model_answer));
      host.appendChild(box);
      finish();
    }

    function selfCheck() {
      var box = el("div", "ac-result");
      box.appendChild(el("h3", "ac-selfhead", "Now mark your own work"));
      if (ex.checklist) {
        var ul = el("div", "ac-checklist");
        ex.checklist.forEach(function (q, i) {
          var lab = el("label", "ac-check");
          var cb = document.createElement("input"); cb.type = "checkbox";
          lab.appendChild(cb); lab.appendChild(el("span", null, q));
          ul.appendChild(lab);
        });
        box.appendChild(ul);
      }
      if (ex.model) box.appendChild(model(ex.model));
      host.appendChild(box);
      finish();
    }

    function model(text) {
      var d = document.createElement("details"); d.className = "ac-model"; d.open = true;
      var s = document.createElement("summary"); s.textContent = "An editor's version";
      d.appendChild(s); d.appendChild(el("p", null, text));
      return d;
    }
    function fbList(title, items) {
      var w = el("div", "ac-fb"); w.appendChild(el("h3", null, title));
      var ul = el("ul"); items.forEach(function (t) { ul.appendChild(el("li", null, t)); });
      w.appendChild(ul); return w;
    }
    function finish() {
      done();
      var a2 = el("div", "ac-actions");
      var c = el("button", "ac-btn", "Continue"); c.addEventListener("click", next);
      a2.appendChild(c); host.appendChild(a2);
    }
  }
  function words(s) { s = (s || "").trim(); return s ? s.split(/\s+/).length : 0; }

  // ---------- router ----------
  function route() {
    var h = location.hash || "#/";
    var m = h.match(/^#\/lesson\/(.+)$/);
    if (m) renderLesson(decodeURIComponent(m[1]));
    else renderHome();
  }
  window.addEventListener("hashchange", route);
  route();
})();
