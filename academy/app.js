/* Mutapa Times Academy - engine.
   Renders the course from window.COURSE. Progress, XP, streak and prefs
   are saved in localStorage, so the whole app works with no backend.
   Exercise types: mcq, multi, order, write, match, categorize, fillblank,
   swipe, highlight. Optional GRADE_ENDPOINT adds AI feedback on writing. */

(function () {
  "use strict";

  var GRADE_ENDPOINT = ""; // e.g. "https://academy-grade.NAME.workers.dev"
  var CERT_ENDPOINT = "";  // e.g. "https://academy-certificate.NAME.workers.dev" (enables emailing)
  var PASS_MARK = 70;      // percent of graded questions needed for the certificate
  var STORE_KEY = "mt_academy_v1";
  var XP_PER_EXERCISE = 10;
  var XP_LESSON_BONUS = 50;
  var REDUCE = !!(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches);

  var COURSE = window.COURSE;
  var view = document.getElementById("view");
  var xpChip = document.getElementById("xpChip");
  var streakChip = document.getElementById("streakChip");
  var soundBtn = document.getElementById("soundBtn");

  // ---------- storage ----------
  function load() {
    try { var s = JSON.parse(localStorage.getItem(STORE_KEY)); if (s && typeof s === "object") return s; } catch (e) {}
    return { xp: 0, streak: { count: 0, last: "" }, lessons: {}, sound: true, results: {}, name: "" };
  }
  function save() { try { localStorage.setItem(STORE_KEY, JSON.stringify(state)); } catch (e) {} }
  var state = load();
  if (typeof state.sound !== "boolean") state.sound = true;
  if (!state.results) state.results = {};
  if (typeof state.name !== "string") state.name = "";

  // ---------- sound (Web Audio, synthesized, no files) ----------
  var Sound = (function () {
    var ctx = null;
    function ac() { if (!ctx) { try { ctx = new (window.AudioContext || window.webkitAudioContext)(); } catch (e) {} } return ctx; }
    function tone(freq, start, dur, type, peak) {
      var c = ac(); if (!c) return;
      var o = c.createOscillator(), g = c.createGain();
      o.type = type || "sine"; o.frequency.value = freq;
      var t = c.currentTime + start;
      g.gain.setValueAtTime(0.0001, t);
      g.gain.exponentialRampToValueAtTime(peak || 0.18, t + 0.012);
      g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
      o.connect(g); g.connect(c.destination);
      o.start(t); o.stop(t + dur + 0.02);
    }
    function play(name) {
      if (!state.sound) return;
      var c = ac(); if (!c) return; if (c.state === "suspended") c.resume();
      if (name === "correct") { tone(660, 0, 0.12, "sine", 0.16); tone(990, 0.09, 0.16, "sine", 0.16); }
      else if (name === "wrong") { tone(180, 0, 0.18, "square", 0.12); tone(120, 0.08, 0.2, "square", 0.1); }
      else if (name === "tap") { tone(420, 0, 0.05, "sine", 0.08); }
      else if (name === "xp") { tone(880, 0, 0.07, "triangle", 0.12); }
      else if (name === "complete") { [523, 659, 784, 1047].forEach(function (f, i) { tone(f, i * 0.11, 0.22, "sine", 0.16); }); }
    }
    return { play: play };
  })();

  function buzz(ms) { if (navigator.vibrate) { try { navigator.vibrate(ms); } catch (e) {} } }

  // ---------- dates / streak ----------
  function today() { var d = new Date(); return d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0"); }
  function daysBetween(a, b) { var pa = a.split("-"), pb = b.split("-"); return Math.round((Date.UTC(+pb[0], pb[1] - 1, +pb[2]) - Date.UTC(+pa[0], pa[1] - 1, +pa[2])) / 86400000); }
  function touchStreak() { var t = today(), last = state.streak.last; if (last === t) return; if (last && daysBetween(last, t) === 1) state.streak.count += 1; else state.streak.count = 1; state.streak.last = t; }

  // ---------- helpers ----------
  function allLessons() { var out = []; COURSE.units.forEach(function (u) { u.lessons.forEach(function (l) { out.push(l); }); }); return out; }
  function lessonState(id) { return state.lessons[id] || (state.lessons[id] = { done: false, exercises: {} }); }
  function courseProgress() { var t = allLessons().length, d = 0; allLessons().forEach(function (l) { if (lessonState(l.id).done) d++; }); return { done: d, total: t, pct: t ? Math.round(d / t * 100) : 0 }; }
  function computeScore() { var c = 0, t = 0; for (var lid in state.results) { var r = state.results[lid]; for (var i in r) { if (r[i].type === "write") continue; t++; if (r[i].ok) c++; } } return { correct: c, total: t, pct: t ? Math.round(c / t * 100) : 0 }; }
  function certEligible() { var p = courseProgress(), s = computeScore(); return p.total > 0 && p.done === p.total && s.total > 0 && s.pct >= PASS_MARK; }
  function el(tag, cls, text) { var e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }
  function clear(n) { while (n.firstChild) n.removeChild(n.firstChild); }
  function go(hash) { location.hash = hash; }
  function shuffle(a) { a = a.slice(); for (var i = a.length - 1; i > 0; i--) { var j = Math.floor(Math.random() * (i + 1)), t = a[i]; a[i] = a[j]; a[j] = t; } return a; }
  function shuffleNonIdentity(a) { var s = shuffle(a); if (a.length > 1 && s.every(function (v, i) { return v === a[i]; })) { var t = s[0]; s[0] = s[1]; s[1] = t; } return s; }
  function sameSet(a, b) { if (a.length !== b.length) return false; var sa = a.slice().sort(), sb = b.slice().sort(); for (var i = 0; i < sa.length; i++) if (sa[i] !== sb[i]) return false; return true; }
  function words(s) { s = (s || "").trim(); return s ? s.split(/\s+/).length : 0; }

  // ---------- animations ----------
  function floatXP(n) {
    Sound.play("xp");
    if (REDUCE || !xpChip) return;
    var f = el("span", "ac-xpfloat", "+" + n);
    var r = xpChip.getBoundingClientRect();
    f.style.left = (r.left + r.width / 2) + "px"; f.style.top = (r.top + 4) + "px";
    document.body.appendChild(f);
    setTimeout(function () { f.remove(); }, 1100);
    xpChip.classList.remove("pulse"); void xpChip.offsetWidth; xpChip.classList.add("pulse");
  }
  function confetti() {
    if (REDUCE) return;
    var colors = ["#c41e1e", "#1a7f44", "#121212", "#e6b800", "#2b6cb0"];
    var box = el("div", "ac-confetti");
    for (var i = 0; i < 44; i++) {
      var p = el("i");
      p.style.left = Math.random() * 100 + "%";
      p.style.background = colors[i % colors.length];
      p.style.animationDelay = (Math.random() * 0.25) + "s";
      p.style.transform = "rotate(" + (Math.random() * 360) + "deg)";
      box.appendChild(p);
    }
    document.body.appendChild(box);
    setTimeout(function () { box.remove(); }, 1800);
  }
  function flash(node, ok) {
    if (REDUCE || !node) return;
    node.classList.remove("ac-anim-pop", "ac-anim-shake"); void node.offsetWidth;
    node.classList.add(ok ? "ac-anim-pop" : "ac-anim-shake");
  }

  // ---------- chips / sound toggle ----------
  function renderChips() {
    if (xpChip) xpChip.textContent = state.xp + " XP";
    if (streakChip) { var c = state.streak.count; streakChip.textContent = (c > 0 ? c : 0) + (c === 1 ? " day" : " days"); streakChip.classList.toggle("is-live", c > 0 && state.streak.last === today()); }
  }
  function renderSoundBtn() { if (soundBtn) { soundBtn.textContent = state.sound ? "🔊" : "🔇"; soundBtn.setAttribute("aria-label", state.sound ? "Sound on" : "Sound off"); } }
  if (soundBtn) soundBtn.addEventListener("click", function () { state.sound = !state.sound; save(); renderSoundBtn(); if (state.sound) Sound.play("tap"); });
  renderSoundBtn();

  // ---------- home / lesson map (winding path) ----------
  function renderHome() {
    clear(view); renderChips();
    var prog = courseProgress();

    var head = el("div", "ac-home-head");
    head.appendChild(el("p", "ac-eyebrow", "Mutapa Times Academy"));
    head.appendChild(el("h1", "ac-h1", "Learn to report Zimbabwe"));
    head.appendChild(el("p", "ac-lead", COURSE.blurb));
    view.appendChild(head);

    var pwrap = el("div", "ac-overall");
    var bar = el("div", "ac-progress"); var fill = el("i"); bar.appendChild(fill);
    pwrap.appendChild(bar); pwrap.appendChild(el("p", "ac-overall-txt", prog.done + " of " + prog.total + " lessons complete"));
    view.appendChild(pwrap);
    setTimeout(function () { fill.style.width = prog.pct + "%"; }, 60);

    if (prog.total > 0 && prog.done === prog.total) {
      var sc = computeScore();
      var cert = el("div", "ac-certcard");
      if (sc.pct >= PASS_MARK) {
        cert.classList.add("pass");
        cert.appendChild(el("p", "ac-cert-eyebrow", "Course complete"));
        cert.appendChild(el("h2", null, "You passed with " + sc.pct + "%"));
        cert.appendChild(el("p", null, "You have earned your Mutapa Times Academy certificate."));
        var cb = el("button", "ac-btn ac-btn--lg", "Claim your certificate");
        cb.addEventListener("click", function () { Sound.play("complete"); go("#/certificate"); });
        cert.appendChild(cb);
      } else {
        cert.appendChild(el("p", "ac-cert-eyebrow", "Almost there"));
        cert.appendChild(el("h2", null, "You scored " + sc.pct + "%"));
        cert.appendChild(el("p", null, "You need " + PASS_MARK + "% to earn the certificate. Replay any lesson to raise your score."));
      }
      view.appendChild(cert);
    }

    var next = firstUnfinished();
    if (next) {
      var cont = el("button", "ac-btn ac-btn--lg", (prog.done ? "Continue: " : "Start: ") + next.title);
      cont.addEventListener("click", function () { Sound.play("tap"); go("#/lesson/" + next.id); });
      var ca = el("div", "ac-actions"); ca.appendChild(cont); view.appendChild(ca);
    }

    COURSE.units.forEach(function (u) {
      var unit = el("section", "ac-unit");
      var uh = el("div", "ac-unit-head");
      uh.appendChild(el("span", "ac-unit-dot"));
      uh.appendChild(el("h2", "ac-unit-title", u.title));
      unit.appendChild(uh);
      if (u.summary) unit.appendChild(el("p", "ac-unit-sum", u.summary));
      var track = el("div", "ac-track");
      u.lessons.forEach(function (l, i) {
        var ls = lessonState(l.id);
        var isCurrent = next && l.id === next.id;
        var wrap = el("div", "ac-node-wrap pos" + (i % 4));
        var node = el("button", "ac-node" + (ls.done ? " is-done" : "") + (isCurrent ? " is-current" : ""));
        node.type = "button";
        node.innerHTML = "<span class='ac-node-face'>" + (ls.done ? "✓" : (i + 1)) + "</span>";
        node.appendChild(el("span", "ac-node-label", l.title));
        node.addEventListener("click", function () { Sound.play("tap"); go("#/lesson/" + l.id); });
        wrap.appendChild(node);
        track.appendChild(wrap);
      });
      unit.appendChild(track);
      view.appendChild(unit);
    });
    window.scrollTo(0, 0);
  }
  function firstUnfinished() { var ls = allLessons(); for (var i = 0; i < ls.length; i++) if (!lessonState(ls[i].id).done) return ls[i]; return ls[ls.length - 1] || null; }
  function firstUnfinishedAfter(id) { var ls = allLessons(), seen = false; for (var i = 0; i < ls.length; i++) { if (seen && !lessonState(ls[i].id).done) return ls[i]; if (ls[i].id === id) seen = true; } return null; }
  function findLesson(id) { var ls = allLessons(); for (var i = 0; i < ls.length; i++) if (ls[i].id === id) return ls[i]; return null; }

  // ---------- lesson player ----------
  function renderLesson(id) {
    var lesson = findLesson(id);
    if (!lesson) { go("#/"); return; }
    clear(view); renderChips();

    var top = el("div", "ac-lessontop");
    var back = el("button", "ac-back", "← All lessons");
    back.addEventListener("click", function () { Sound.play("tap"); go("#/"); });
    top.appendChild(back);
    view.appendChild(top);

    view.appendChild(el("p", "ac-eyebrow", lesson.title));
    view.appendChild(el("h1", "ac-h1", lesson.intro));

    lesson.cards.forEach(function (c, i) {
      var card = el("section", "ac-card ac-reveal");
      card.style.animationDelay = (i * 0.06) + "s";
      card.appendChild(el("p", "ac-kicker", "Read"));
      card.appendChild(el("h2", null, c.h));
      c.body.forEach(function (p) { card.appendChild(el("p", null, p)); });
      view.appendChild(card);
    });

    var exHost = el("section", "ac-card ac-exhost");
    view.appendChild(exHost);

    var startWrap = el("div", "ac-actions");
    var startBtn = el("button", "ac-btn ac-btn--lg", "Start the exercises (" + lesson.exercises.length + ")");
    startWrap.appendChild(startBtn);
    exHost.appendChild(startWrap);

    var idx = 0;
    startBtn.addEventListener("click", function () { Sound.play("tap"); runExercise(); });

    function runExercise() {
      clear(exHost);
      if (idx >= lesson.exercises.length) return complete();
      var ex = lesson.exercises[idx];

      var dots = el("div", "ac-dots");
      for (var d = 0; d < lesson.exercises.length; d++) dots.appendChild(el("span", "ac-dot" + (d < idx ? " done" : d === idx ? " active" : "")));
      exHost.appendChild(dots);

      var panel = el("div", "ac-panel ac-slidein");
      exHost.appendChild(panel);
      panel.appendChild(el("p", "ac-kicker", "Exercise " + (idx + 1) + " of " + lesson.exercises.length));

      var done = function () { lessonState(lesson.id).exercises[idx] = true; save(); };
      var rec = function (ok) { if (!state.results[lesson.id]) state.results[lesson.id] = {}; state.results[lesson.id][idx] = { ok: !!ok, type: ex.type }; save(); };
      var nextStep = function () { idx++; runExercise(); };
      var R = RENDERERS[ex.type];
      if (R) R(panel, ex, done, nextStep, rec); else nextStep();
      exHost.scrollIntoView({ behavior: "smooth", block: "start" });
    }

    function complete() {
      clear(exHost);
      var ls = lessonState(lesson.id);
      var gained = 0;
      if (!ls.done) { ls.done = true; gained = lesson.exercises.length * XP_PER_EXERCISE + XP_LESSON_BONUS; state.xp += gained; touchStreak(); save(); }
      renderChips();
      Sound.play("complete"); confetti();
      var done = el("div", "ac-done-inline ac-anim-pop");
      done.appendChild(el("p", "mark", "M·T"));
      done.appendChild(el("h2", null, "Lesson complete"));
      done.appendChild(el("p", null, gained ? ("You earned " + gained + " XP. Your progress and streak are saved.") : "Revisited and still sharp. Progress is saved."));
      var acts = el("div", "ac-actions");
      var nxt = firstUnfinishedAfter(lesson.id);
      if (nxt) { var nb = el("button", "ac-btn", "Next: " + nxt.title); nb.addEventListener("click", function () { Sound.play("tap"); go("#/lesson/" + nxt.id); }); acts.appendChild(nb); }
      var hb = el("button", "ac-btn ac-btn--ghost", "Back to map"); hb.addEventListener("click", function () { Sound.play("tap"); go("#/"); }); acts.appendChild(hb);
      done.appendChild(acts); exHost.appendChild(done);
      exHost.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }

  // ---------- shared feedback ----------
  function feedback(host, ok, explain, onContinue, opts) {
    opts = opts || {};
    if (ok) { Sound.play("correct"); } else { Sound.play("wrong"); buzz(60); }
    var ex = el("p", "ac-explain " + (ok ? "good" : "bad"));
    ex.textContent = (opts.label || (ok ? "Correct. " : "Not quite. ")) + (explain || "");
    host.appendChild(ex); flash(ex, ok);
    var acts = el("div", "ac-actions");
    var cont = el("button", "ac-btn", "Continue"); cont.addEventListener("click", function () { Sound.play("tap"); onContinue(); });
    acts.appendChild(cont); host.appendChild(acts);
  }

  // ---------- exercise renderers ----------
  var RENDERERS = {};

  RENDERERS.mcq = RENDERERS.multi = function (host, ex, done, next, rec) {
    var multi = ex.type === "multi";
    host.appendChild(el("p", "ac-q", ex.q + (multi ? "  (select all that apply)" : "")));
    var opts = el("div", "ac-opts"), picked = {}, locked = false;
    ex.options.forEach(function (text, i) {
      var b = el("button", "ac-opt"); b.type = "button"; b.textContent = text;
      b.addEventListener("click", function () {
        if (locked) return; Sound.play("tap");
        if (multi) { picked[i] = !picked[i]; b.classList.toggle("is-picked", picked[i]); }
        else grade([i]);
      });
      opts.appendChild(b);
    });
    host.appendChild(opts);
    if (multi) {
      var acts = el("div", "ac-actions");
      var check = el("button", "ac-btn", "Check");
      check.addEventListener("click", function () { var sel = Object.keys(picked).filter(function (k) { return picked[k]; }).map(Number); if (sel.length) grade(sel); });
      acts.appendChild(check); host.appendChild(acts);
    }
    function grade(sel) {
      locked = true;
      var correct = multi ? ex.answers.slice() : [ex.answer];
      var btns = opts.querySelectorAll(".ac-opt");
      btns.forEach(function (b) { b.disabled = true; });
      correct.forEach(function (i) { btns[i].classList.add("is-correct"); });
      sel.forEach(function (i) { if (correct.indexOf(i) === -1) btns[i].classList.add("is-wrong"); });
      var ok = sameSet(sel, correct);
      done(); rec(ok); feedback(host, ok, ex.explain, next);
    }
  };

  RENDERERS.order = function (host, ex, done, next, rec) {
    host.appendChild(el("p", "ac-q", ex.q + "  (use the arrows to reorder)"));
    var order = shuffleNonIdentity(ex.items.map(function (t, i) { return i; }));
    var list = el("div", "ac-order"); host.appendChild(list);
    function paint() {
      clear(list);
      order.forEach(function (orig, pos) {
        var row = el("div", "ac-order-row");
        var ctrl = el("div", "ac-order-ctrl");
        var up = el("button", "ac-arrow", "↑"); up.type = "button"; up.disabled = pos === 0;
        var dn = el("button", "ac-arrow", "↓"); dn.type = "button"; dn.disabled = pos === order.length - 1;
        up.addEventListener("click", function () { Sound.play("tap"); swap(pos, pos - 1); });
        dn.addEventListener("click", function () { Sound.play("tap"); swap(pos, pos + 1); });
        ctrl.appendChild(up); ctrl.appendChild(dn); row.appendChild(ctrl);
        row.appendChild(el("span", "ac-order-txt", ex.items[orig])); list.appendChild(row);
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
      list.querySelectorAll(".ac-order-row").forEach(function (r, pos) { r.classList.add(order[pos] === pos ? "is-correct" : "is-wrong"); });
      done(); rec(ok); feedback(host, ok, ex.explain, next);
    });
    acts.appendChild(check); host.appendChild(acts);
  };

  RENDERERS.match = function (host, ex, done, next, rec) {
    host.appendChild(el("p", "ac-q", ex.q + "  (tap a term, then its match)"));
    var grid = el("div", "ac-match"); host.appendChild(grid);
    var left = el("div", "ac-match-col"), right = el("div", "ac-match-col");
    grid.appendChild(left); grid.appendChild(right);
    var lefts = ex.pairs.map(function (p, i) { return { t: p.a, i: i }; });
    var rights = shuffle(ex.pairs.map(function (p, i) { return { t: p.b, i: i }; }));
    var sel = null, matched = 0, wrong = 0;
    function mkBtn(item, col) {
      var b = el("button", "ac-chip"); b.type = "button"; b.textContent = item.t; b.dataset.i = item.i; b.dataset.col = col;
      b.addEventListener("click", function () {
        if (b.classList.contains("is-matched")) return; Sound.play("tap");
        if (!sel) { clearSel(); sel = b; b.classList.add("is-sel"); return; }
        if (sel === b) { b.classList.remove("is-sel"); sel = null; return; }
        if (sel.dataset.col === b.dataset.col) { clearSel(); sel = b; b.classList.add("is-sel"); return; }
        if (sel.dataset.i === b.dataset.i) {
          sel.classList.remove("is-sel"); sel.classList.add("is-matched"); b.classList.add("is-matched");
          sel = null; matched++; Sound.play("correct");
          if (matched === ex.pairs.length) { done(); rec(wrong === 0); feedback(host, wrong === 0, ex.explain, next, { label: wrong === 0 ? "All matched. " : "Matched, with a few misses. " }); }
        } else { wrong++; flash(b, false); flash(sel, false); Sound.play("wrong"); buzz(50); var s = sel; sel = null; s.classList.remove("is-sel"); }
      });
      return b;
    }
    function clearSel() { grid.querySelectorAll(".is-sel").forEach(function (n) { n.classList.remove("is-sel"); }); }
    lefts.forEach(function (it) { left.appendChild(mkBtn(it, "L")); });
    rights.forEach(function (it) { right.appendChild(mkBtn(it, "R")); });
  };

  RENDERERS.categorize = function (host, ex, done, next, rec) {
    host.appendChild(el("p", "ac-q", ex.q + (ex.instruction ? "" : "  (tap an item, then a category)")));
    if (ex.instruction) host.appendChild(el("p", "ac-sub", ex.instruction));
    var pool = el("div", "ac-pool"); host.appendChild(pool);
    var sel = null;
    var items = shuffle(ex.items.map(function (it, i) { return { it: it, i: i }; }));
    items.forEach(function (o) {
      var c = el("button", "ac-chip"); c.type = "button"; c.textContent = o.it.text; c.dataset.bucket = o.it.bucket; c.dataset.placed = "";
      c.addEventListener("click", function () { if (c.dataset.locked) return; Sound.play("tap"); if (sel) sel.classList.remove("is-sel"); sel = c; c.classList.add("is-sel"); });
      pool.appendChild(c);
    });
    var buckets = el("div", "ac-buckets"); host.appendChild(buckets);
    ex.buckets.forEach(function (bk) {
      var col = el("div", "ac-bucket");
      col.appendChild(el("p", "ac-bucket-h", bk.label));
      var drop = el("div", "ac-bucket-drop"); col.appendChild(drop);
      drop.addEventListener("click", function () { if (!sel) return; Sound.play("tap"); sel.dataset.placed = bk.id; drop.appendChild(sel); sel.classList.remove("is-sel"); sel = null; });
      buckets.appendChild(col);
    });
    var acts = el("div", "ac-actions");
    var check = el("button", "ac-btn", "Check");
    check.addEventListener("click", function () {
      var all = host.querySelectorAll(".ac-pool .ac-chip, .ac-bucket-drop .ac-chip");
      var ok = true;
      all.forEach(function (c) {
        c.dataset.locked = "1"; c.classList.remove("is-sel");
        var right = c.dataset.placed === c.dataset.bucket;
        c.classList.add(right ? "is-correct" : "is-wrong"); if (!right) ok = false;
      });
      check.disabled = true; done(); rec(ok); feedback(host, ok, ex.explain, next);
    });
    acts.appendChild(check); host.appendChild(acts);
  };

  RENDERERS.fillblank = function (host, ex, done, next, rec) {
    host.appendChild(el("p", "ac-q", ex.q + "  (tap words to fill the gaps)"));
    var parts = ex.text.split("___");
    var line = el("p", "ac-cloze"); host.appendChild(line);
    var slots = [];
    parts.forEach(function (txt, i) {
      line.appendChild(document.createTextNode(txt));
      if (i < parts.length - 1) {
        var s = el("button", "ac-slot", "____"); s.type = "button"; s.dataset.word = "";
        s.addEventListener("click", function () { if (s.dataset.locked) return; if (s.dataset.word) { Sound.play("tap"); returnChip(s); } });
        line.appendChild(s); slots.push(s);
      }
    });
    var bank = el("div", "ac-bank"); host.appendChild(bank);
    shuffle(ex.bank.slice()).forEach(function (w) {
      var chip = el("button", "ac-chip", w); chip.type = "button"; chip.dataset.word = w;
      chip.addEventListener("click", function () {
        if (chip.classList.contains("is-used") || chip.dataset.locked) return; Sound.play("tap");
        var slot = slots.filter(function (s) { return !s.dataset.word; })[0]; if (!slot) return;
        slot.dataset.word = w; slot.textContent = w; slot.classList.add("filled"); slot.dataset.chip = w; chip.classList.add("is-used");
      });
      bank.appendChild(chip);
    });
    function returnChip(slot) {
      var w = slot.dataset.word; slot.dataset.word = ""; slot.textContent = "____"; slot.classList.remove("filled");
      bank.querySelectorAll(".ac-chip").forEach(function (c) { if (c.dataset.word === w && c.classList.contains("is-used")) c.classList.remove("is-used"); });
    }
    var acts = el("div", "ac-actions");
    var check = el("button", "ac-btn", "Check");
    check.addEventListener("click", function () {
      var ok = true;
      slots.forEach(function (s, i) { s.dataset.locked = "1"; var right = s.dataset.word === ex.answer[i]; s.classList.add(right ? "is-correct" : "is-wrong"); if (!right) ok = false; });
      bank.querySelectorAll(".ac-chip").forEach(function (c) { c.dataset.locked = "1"; });
      check.disabled = true; done(); rec(ok); feedback(host, ok, ex.explain, next);
    });
    acts.appendChild(check); host.appendChild(acts);
  };

  RENDERERS.swipe = function (host, ex, done, next, rec) {
    host.appendChild(el("p", "ac-q", ex.q));
    var stage = el("div", "ac-swipe"); host.appendChild(stage);
    var card = el("div", "ac-swipe-card"); stage.appendChild(card);
    var counter = el("p", "ac-swipe-count"); host.appendChild(counter);
    var btns = el("div", "ac-swipe-btns");
    var lb = el("button", "ac-btn ac-btn--ghost", "← " + ex.leftLabel);
    var rb = el("button", "ac-btn", ex.rightLabel + " →");
    btns.appendChild(lb); btns.appendChild(rb); host.appendChild(btns);
    var i = 0, correct = 0;
    var deck = shuffle(ex.cards.slice());
    function show() {
      if (i >= deck.length) {
        btns.style.display = "none"; stage.style.display = "none"; counter.textContent = "";
        var ok = correct === deck.length;
        done(); rec(ok); feedback(host, ok, ex.explain, next, { label: "You got " + correct + " of " + deck.length + ". " });
        return;
      }
      counter.textContent = (i + 1) + " of " + deck.length;
      card.classList.remove("in"); void card.offsetWidth; card.classList.add("in");
      card.textContent = deck[i].text;
    }
    function answer(side) {
      var ok = deck[i].side === side;
      if (ok) { correct++; Sound.play("correct"); } else { Sound.play("wrong"); buzz(40); }
      if (!REDUCE) { card.classList.add(side === "left" ? "fly-left" : "fly-right"); }
      card.classList.add(ok ? "ok" : "no");
      setTimeout(function () { card.className = "ac-swipe-card"; i++; show(); }, REDUCE ? 0 : 260);
    }
    lb.addEventListener("click", function () { answer("left"); });
    rb.addEventListener("click", function () { answer("right"); });
    show();
  };

  RENDERERS.highlight = function (host, ex, done, next, rec) {
    host.appendChild(el("p", "ac-q", ex.q));
    if (ex.instruction) host.appendChild(el("p", "ac-sub", ex.instruction));
    var wrap = el("p", "ac-tokens"); host.appendChild(wrap);
    var picked = {};
    ex.tokens.forEach(function (tok, i) {
      var t = el("button", "ac-token", tok); t.type = "button";
      t.addEventListener("click", function () { if (t.dataset.locked) return; Sound.play("tap"); picked[i] = !picked[i]; t.classList.toggle("is-sel", picked[i]); });
      wrap.appendChild(t); wrap.appendChild(document.createTextNode(" "));
    });
    var acts = el("div", "ac-actions");
    var check = el("button", "ac-btn", "Check");
    check.addEventListener("click", function () {
      var sel = Object.keys(picked).filter(function (k) { return picked[k]; }).map(Number);
      var ok = sameSet(sel, ex.targets);
      wrap.querySelectorAll(".ac-token").forEach(function (t, i) {
        t.dataset.locked = "1";
        if (ex.targets.indexOf(i) !== -1) t.classList.add("is-correct");
        else if (picked[i]) t.classList.add("is-wrong");
      });
      check.disabled = true; done(); rec(ok); feedback(host, ok, ex.explain, next);
    });
    acts.appendChild(check); host.appendChild(acts);
  };

  RENDERERS.write = function (host, ex, done, next, rec) {
    host.appendChild(el("p", "ac-q", ex.q));
    if (ex.brief) { var brief = el("div", "ac-brief"); ex.brief.forEach(function (p) { brief.appendChild(el("p", null, p)); }); host.appendChild(brief); }
    var ta = el("textarea", "ac-input"); ta.setAttribute("maxlength", "900"); ta.placeholder = "Write your answer..."; host.appendChild(ta);
    var count = el("p", "ac-count", "0 words"); host.appendChild(count);
    ta.addEventListener("input", function () { var n = words(ta.value); count.textContent = n + (n === 1 ? " word" : " words"); });
    var acts = el("div", "ac-actions");
    var submit = el("button", "ac-btn", GRADE_ENDPOINT ? "Get feedback" : "Reveal model answer");
    var status = el("span", "ac-status"); acts.appendChild(submit); acts.appendChild(status); host.appendChild(acts);
    submit.addEventListener("click", function () {
      if (words(ta.value) < 4) { status.innerHTML = '<span class="ac-err">Write a full answer first.</span>'; return; }
      ta.disabled = true; submit.disabled = true; Sound.play("tap");
      if (GRADE_ENDPOINT && ex.exerciseId) {
        status.innerHTML = '<span class="ac-spin">Your editor is reading...</span>';
        fetch(GRADE_ENDPOINT, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ exerciseId: ex.exerciseId, answer: ta.value.trim() }) })
          .then(function (r) { if (!r.ok) throw 0; return r.json(); })
          .then(function (d) { status.textContent = ""; aiResult(d); })
          .catch(function () { status.textContent = ""; selfCheck(); });
      } else selfCheck();
    });
    function aiResult(d) {
      var box = el("div", "ac-result"); var score = Math.max(0, Math.min(100, parseInt(d.score, 10) || 0));
      var row = el("div", "ac-score " + (score >= 70 ? "pass" : "revise")); row.appendChild(el("b", null, String(score))); row.appendChild(el("span", null, d.verdict || "")); box.appendChild(row);
      if (d.strengths && d.strengths.length) box.appendChild(fbList("What worked", d.strengths));
      if (d.improvements && d.improvements.length) box.appendChild(fbList("Sharpen this", d.improvements));
      if (d.model_answer) box.appendChild(model(d.model_answer));
      host.appendChild(box); Sound.play(score >= 70 ? "correct" : "wrong"); finish();
    }
    function selfCheck() {
      var box = el("div", "ac-result"); box.appendChild(el("h3", "ac-selfhead", "Now mark your own work"));
      if (ex.checklist) { var ul = el("div", "ac-checklist"); ex.checklist.forEach(function (q) { var lab = el("label", "ac-check"); var cb = document.createElement("input"); cb.type = "checkbox"; cb.addEventListener("change", function () { if (cb.checked) Sound.play("tap"); }); lab.appendChild(cb); lab.appendChild(el("span", null, q)); ul.appendChild(lab); }); box.appendChild(ul); }
      if (ex.model) box.appendChild(model(ex.model));
      host.appendChild(box); Sound.play("correct"); finish();
    }
    function model(text) { var d = document.createElement("details"); d.className = "ac-model"; d.open = true; var s = document.createElement("summary"); s.textContent = "An editor's version"; d.appendChild(s); d.appendChild(el("p", null, text)); return d; }
    function fbList(title, items) { var w = el("div", "ac-fb"); w.appendChild(el("h3", null, title)); var ul = el("ul"); items.forEach(function (t) { ul.appendChild(el("li", null, t)); }); w.appendChild(ul); return w; }
    function finish() { done(); var a2 = el("div", "ac-actions"); var c = el("button", "ac-btn", "Continue"); c.addEventListener("click", function () { Sound.play("tap"); next(); }); a2.appendChild(c); host.appendChild(a2); }
  };

  // ---------- certificate ----------
  var MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
  function dateStr() { var d = new Date(); return d.getDate() + " " + MONTHS[d.getMonth()] + " " + d.getFullYear(); }
  function certId(name) { var s = (name || "") + "|" + dateStr(), h = 0; for (var i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) >>> 0; return "MTA-" + h.toString(36).toUpperCase().slice(0, 8); }

  function renderCertificate() {
    if (!certEligible()) { go("#/"); return; }
    clear(view); renderChips();
    var sc = computeScore();

    var top = el("div", "ac-lessontop"); var back = el("button", "ac-back", "← Back");
    back.addEventListener("click", function () { Sound.play("tap"); go("#/"); }); top.appendChild(back); view.appendChild(top);
    view.appendChild(el("p", "ac-eyebrow", "Your certificate"));
    view.appendChild(el("h1", "ac-h1", "Congratulations"));

    var form = el("div", "ac-cert-form");
    form.appendChild(el("label", "ac-cert-label", "Your full name (as it should appear)"));
    var ni = document.createElement("input"); ni.type = "text"; ni.className = "ac-cert-input"; ni.value = state.name || ""; ni.placeholder = "e.g. Tendai Kuwanda"; ni.maxLength = 60;
    form.appendChild(ni); view.appendChild(form);

    var certWrap = el("div"); view.appendChild(certWrap);
    function paint() {
      clear(certWrap);
      var name = (ni.value || "").trim() || "Your Name";
      var cert = el("div", "ac-cert");
      cert.appendChild(el("p", "ac-cert-mark", "M·T"));
      cert.appendChild(el("p", "ac-cert-org", "The Mutapa Times Academy"));
      cert.appendChild(el("p", "ac-cert-csub", "Certificate of Completion"));
      cert.appendChild(el("p", "ac-cert-pre", "This certifies that"));
      cert.appendChild(el("p", "ac-cert-name", name));
      cert.appendChild(el("p", "ac-cert-cbody", "has completed the Mutapa Times Academy course in journalism for Zimbabwe and the diaspora, passing with a score of " + sc.pct + "%."));
      var meta = el("div", "ac-cert-meta");
      meta.appendChild(el("span", null, "Awarded " + dateStr()));
      meta.appendChild(el("span", null, "ID " + certId(name)));
      cert.appendChild(meta);
      certWrap.appendChild(cert);
    }
    ni.addEventListener("input", function () { state.name = ni.value; save(); paint(); });
    paint();

    var acts = el("div", "ac-actions");
    var dl = el("button", "ac-btn", "Download / Print");
    dl.addEventListener("click", function () { Sound.play("tap"); window.print(); });
    acts.appendChild(dl); view.appendChild(acts);

    var ew = el("div", "ac-cert-email");
    ew.appendChild(el("h3", "ac-selfhead", "Email me my certificate"));
    var ei = document.createElement("input"); ei.type = "email"; ei.className = "ac-cert-input"; ei.placeholder = "you@email.com";
    ew.appendChild(ei);
    var ea = el("div", "ac-actions"); var eb = el("button", "ac-btn", "Send to my email"); var est = el("span", "ac-status");
    ea.appendChild(eb); ea.appendChild(est); ew.appendChild(ea); view.appendChild(ew);
    eb.addEventListener("click", function () {
      var name = (ni.value || "").trim(), email = (ei.value || "").trim();
      if (name.length < 2) { est.innerHTML = '<span class="ac-err">Enter your name first.</span>'; return; }
      if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) { est.innerHTML = '<span class="ac-err">Enter a valid email.</span>'; return; }
      if (!CERT_ENDPOINT) { est.innerHTML = '<span class="ac-err">Email delivery is not set up yet. Use Download / Print to save your certificate.</span>'; return; }
      eb.disabled = true; est.innerHTML = '<span class="ac-spin">Sending...</span>';
      fetch(CERT_ENDPOINT, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ name: name, email: email, score: sc.pct, date: dateStr(), id: certId(name) }) })
        .then(function (r) { if (!r.ok) throw 0; return r.json(); })
        .then(function () { est.innerHTML = '<span class="ac-ok">Sent. Check your inbox.</span>'; Sound.play("complete"); })
        .catch(function () { eb.disabled = false; est.innerHTML = '<span class="ac-err">Could not send. Try Download / Print instead.</span>'; });
    });
    window.scrollTo(0, 0);
  }

  // ---------- router ----------
  function route() { var h = location.hash || "#/"; if (h.indexOf("#/certificate") === 0) return renderCertificate(); var m = h.match(/^#\/lesson\/(.+)$/); if (m) renderLesson(decodeURIComponent(m[1])); else renderHome(); }
  window.addEventListener("hashchange", route);
  route();
})();
