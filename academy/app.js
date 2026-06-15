/* Mutapa Times Academy - engine.
   Renders the course from window.COURSE. Progress, XP, streak and prefs
   are saved in localStorage, so the whole app works with no backend.
   Exercise types: mcq, multi, order, write, match, categorize, fillblank,
   swipe, highlight. Optional GRADE_ENDPOINT adds AI feedback on writing. */

(function () {
  "use strict";

  var GRADE_ENDPOINT = "https://academy-grade.mutapatimes.workers.dev"; // AI writing feedback (Gemini)
  var CERT_ENDPOINT = "https://academy-certificate.mutapatimes.workers.dev";  // certificate + article submission email
  var PASS_MARK = 70;      // percent of graded questions across the course needed for the certificate
  var LESSON_PASS = 80;    // percent needed to complete (and unlock past) a single lesson
  // Review mode (set by /academy/review/): everything unlocked, no gates,
  // explanations always shown, progress kept under a separate key.
  var REVIEW = !!window.MT_ACADEMY_REVIEW;
  var STORE_KEY = REVIEW ? "mt_academy_review" : "mt_academy_v1";
  var XP_PER_EXERCISE = 10;
  var XP_LESSON_BONUS = 50;
  var REDUCE = !!(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches);
  var examMode = false; // true during checkpoint lessons: no per-question explanations

  // Paywall + cross-device resume. The course needs an access token, issued at
  // /academy/welcome/ after payment or after redeeming an access code. Progress
  // is also synced to the server (keyed to the token) so a learner can stop and
  // resume on any device. Review mode bypasses all of this.
  var PAY_ENDPOINT = "https://academy-pay.mutapatimes.workers.dev";
  var REQUIRE_ACCESS = true;
  var ACCESS = { email: "", token: "" };
  if (!REVIEW) {
    try { ACCESS.email = localStorage.getItem("mt_academy_email") || ""; ACCESS.token = localStorage.getItem("mt_academy_token") || ""; } catch (e) {}
    if (REQUIRE_ACCESS && (!ACCESS.token || !ACCESS.email)) { location.replace("/academy/welcome/"); return; }
  }

  var COURSE = window.COURSE;
  var view = document.getElementById("view");

  // ---------- lesson imagery ----------
  var IMGBASE = "/img/uploads/image_bank_academy/";
  var IMG_MAP = {
    "the-interview": "interview-microphone.jpg",
    "reporting-from-distance": "interview-phones.jpg",
    "finding-sources": "checking-story.jpg",
    "verification": "checking-story.jpg",
    "newsroom-roles": "busy-newsroom.jpg",
    "story-flow": "busy-newsroom.jpg",
    "outlet-types": "newspaper.jpg",
    "newsroom-of-one": "substack-writing.jpg",
    "revenue-models": "revenue.jpg",
    "news-business-today": "newsprinting.jpg",
    "paywalls": "revenue.jpg",
    "inclusive-revenue": "reading-newspaper.jpg",
    "ownership-influence": "newspaper.jpg",
    "fact-checking": "checking-story.jpg",
    "copy-checking": "writing-reading-checking.jpg",
    "structure": "newsprinting.jpg",
    "the-lede": "generic-writing-2.jpg",
    "writing-clearly": "generic-typing-keyboard.jpg",
    "editing-yourself": "writing-reading-checking.jpg",
    "digital-age": "editing-images.jpg",
    "personal-brand": "generic-typing-keyboard.jpg",
    "freelance-portfolio": "writing-laptop-portrait.jpg",
    "substack-newsletter": "newsletter.jpg",
    "journalism-cv": "jobapplication.jpg",
    "cover-letter": "jobapplication.jpg",
    "cv-mistakes": "jobapplication.jpg",
    "region-north": "archive-library-research.jpg",
    "region-west": "newspaper.jpg",
    "region-east": "interview-phones.jpg",
    "region-central": "archive-library-research.jpg",
    "region-southern": "harare.jpg",
    "africa-narrative": "africa.jpg",
    "beyond-bleeds": "africa.jpg",
    "sources-agenda": "investigative-data.jpg",
    "pan-african": "africa.jpg"
  };
  var IMG_POOL = [
    "generic-writing-1.jpg", "generic-research.jpg", "generic-typing-keyboard.jpg",
    "generic-writing-2.jpg", "generic-writing-alone.jpg", "generic-journalist-writing-1.jpg",
    "student-park-laptop.jpg", "head-inside-book.jpg", "generic-journalist-writing-2.jpg",
    "generic-writing-portrait.jpg", "table-ipad-newspaper.jpg"
  ];
  function lessonImage(lesson) {
    if (IMG_MAP[lesson.id]) return IMGBASE + IMG_MAP[lesson.id];
    var li = allLessons(), pos = 0;
    for (var k = 0; k < li.length; k++) { if (li[k].id === lesson.id) { pos = k; break; } }
    return IMGBASE + IMG_POOL[pos % IMG_POOL.length];
  }

  // ---------- reading-card diagrams (CSS/HTML only) ----------
  function renderChart(ch) {
    var fig = el("figure", "ac-chart ac-chart--" + ch.type);
    if (ch.title) fig.appendChild(el("figcaption", "ac-chart-title", ch.title));
    if (ch.type === "flow") {
      var row = el("div", "ac-flow");
      (ch.items || []).forEach(function (it, i) {
        row.appendChild(el("span", "ac-flow-step", it));
        if (i < ch.items.length - 1) row.appendChild(el("span", "ac-flow-arrow", "→"));
      });
      fig.appendChild(row);
    } else if (ch.type === "hierarchy") {
      (ch.levels || []).forEach(function (lvl) {
        var r = el("div", "ac-hier-row");
        lvl.forEach(function (n) { r.appendChild(el("span", "ac-hier-node", n)); });
        fig.appendChild(r);
      });
    } else if (ch.type === "bars") {
      (ch.items || []).forEach(function (it) {
        var r = el("div", "ac-bar-row");
        r.appendChild(el("span", "ac-bar-label", it.label));
        var track = el("div", "ac-bar-track");
        var fill = el("div", "ac-bar-fill");
        fill.style.width = Math.max(3, Math.min(100, it.value)) + "%";
        fill.appendChild(el("span", "ac-bar-val", (it.display != null ? it.display : it.value + "%")));
        track.appendChild(fill); r.appendChild(track);
        fig.appendChild(r);
      });
    } else if (ch.type === "pyramid") {
      var n = (ch.items || []).length;
      ch.items.forEach(function (it, i) {
        var seg = el("div", "ac-pyr-seg", it);
        seg.style.width = (100 - i * (n > 1 ? 52 / (n - 1) : 0)) + "%";
        fig.appendChild(seg);
      });
    } else if (ch.type === "pillars") {
      var pr = el("div", "ac-pillars");
      (ch.items || []).forEach(function (it, i) {
        var col = el("div", "ac-pillar");
        col.appendChild(el("span", "ac-pillar-n", String(i + 1)));
        col.appendChild(el("span", "ac-pillar-t", it));
        pr.appendChild(col);
      });
      fig.appendChild(pr);
    }
    return fig;
  }

  var xpChip = document.getElementById("xpChip");
  var streakChip = document.getElementById("streakChip");
  var soundBtn = document.getElementById("soundBtn");

  // ---------- storage ----------
  function load() {
    try { var s = JSON.parse(localStorage.getItem(STORE_KEY)); if (s && typeof s === "object") return s; } catch (e) {}
    return { xp: 0, streak: { count: 0, last: "" }, lessons: {}, sound: true, results: {}, name: "", updatedTs: 0 };
  }
  function saveLocal() { try { localStorage.setItem(STORE_KEY, JSON.stringify(state)); } catch (e) {} }
  function save() { state.updatedTs = Date.now(); saveLocal(); schedulePush(); }
  var state = load();

  // ---------- cross-device progress sync ----------
  var pushTimer = null;
  function schedulePush() {
    if (REVIEW || !REQUIRE_ACCESS || !ACCESS.token) return;
    if (pushTimer) clearTimeout(pushTimer);
    pushTimer = setTimeout(pushProgress, 1500);
  }
  function adoptServer(progress, ts) {
    if (!progress || typeof progress !== "object") return;
    state = progress;
    if (typeof state.sound !== "boolean") state.sound = true;
    if (!state.results) state.results = {};
    if (typeof state.name !== "string") state.name = "";
    state.updatedTs = ts || state.updatedTs || 0;
    saveLocal(); renderChips(); renderSoundBtn(); route();
  }
  function pushProgress() {
    if (REVIEW || !ACCESS.token) return;
    try {
      fetch(PAY_ENDPOINT, { method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "progress-put", email: ACCESS.email, token: ACCESS.token, updatedTs: state.updatedTs || Date.now(), progress: state }) })
        .then(function (r) { return r.ok ? r.json() : null; })
        .then(function (d) { if (d && d.newer && d.progress) adoptServer(d.progress, d.updatedTs); })
        .catch(function () {});
    } catch (e) {}
  }
  function pullProgress() {
    if (REVIEW || !ACCESS.token) return;
    try {
      fetch(PAY_ENDPOINT, { method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "progress-get", email: ACCESS.email, token: ACCESS.token }) })
        .then(function (r) {
          if (r.status === 401) { // token no longer valid: send them back to unlock
            try { localStorage.removeItem("mt_academy_token"); localStorage.removeItem("mt_academy_access"); } catch (e) {}
            location.replace("/academy/welcome/"); return null;
          }
          return r.ok ? r.json() : null;
        })
        .then(function (d) { if (d && d.progress && (d.updatedTs || 0) > (state.updatedTs || 0)) adoptServer(d.progress, d.updatedTs); })
        .catch(function () {});
    } catch (e) {}
  }
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
  function lessonGradedTotal(lesson) { return lesson.exercises.filter(function (e) { return e.type !== "write"; }).length; }
  function lessonScore(lesson) { var r = state.results[lesson.id] || {}, correct = 0; for (var i in r) { if (r[i].type !== "write" && r[i].ok) correct++; } var total = lessonGradedTotal(lesson); return total ? Math.round(correct / total * 100) : 100; }
  function isUnlocked(id) { if (REVIEW) return true; var ls = allLessons(); for (var i = 0; i < ls.length; i++) { if (ls[i].id === id) return i === 0 || lessonState(ls[i - 1].id).done; } return false; }
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

  // ---------- exam timer ----------
  var examTimer = null;
  function clearExamTimer() {
    if (examTimer) { clearInterval(examTimer); examTimer = null; }
    var b = document.getElementById("ac-exambar"); if (b) b.remove();
    document.body.classList.remove("ac-exam-running");
  }
  function leaveExam() { clearExamTimer(); document.body.classList.remove("ac-exam"); }
  function startExamTimer(seconds, onExpire) {
    clearExamTimer();
    var bar = el("div", "ac-exambar"); bar.id = "ac-exambar";
    bar.appendChild(el("span", "ac-exam-dot"));
    bar.appendChild(document.createTextNode("Exam in progress"));
    var b = el("b"); b.id = "ac-timerval"; bar.appendChild(b);
    document.body.appendChild(bar); document.body.classList.add("ac-exam-running");
    var t = seconds;
    function fmt(x) { var m = Math.floor(x / 60), s = x % 60; return m + ":" + String(s).padStart(2, "0"); }
    function tick() {
      var bv = document.getElementById("ac-timerval");
      if (bv) { bv.textContent = " " + fmt(t); bv.classList.toggle("low", t <= 30); }
      if (t <= 0) { clearExamTimer(); onExpire(); return; }
      t--;
    }
    tick(); examTimer = setInterval(tick, 1000);
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
    leaveExam();
    clear(view); renderChips();
    var prog = courseProgress();

    var head = el("div", "ac-home-head");
    head.appendChild(el("p", "ac-eyebrow", "Mutapa Times Academy"));
    head.appendChild(el("h1", "ac-h1", "Learn to report Africa"));
    head.appendChild(el("p", "ac-lead", COURSE.blurb));
    view.appendChild(head);

    var pwrap = el("div", "ac-overall");
    var bar = el("div", "ac-progress"); var fill = el("i"); bar.appendChild(fill);
    pwrap.appendChild(bar); pwrap.appendChild(el("p", "ac-overall-txt", prog.done + " of " + prog.total + " lessons complete"));
    view.appendChild(pwrap);
    setTimeout(function () { fill.style.width = prog.pct + "%"; }, 60);

    var readCta = el("button", "ac-readroom-cta");
    readCta.appendChild(el("span", "ac-readroom-k", "Reading Room"));
    readCta.appendChild(el("span", "ac-readroom-t", "Read and analyse this week's Mutapa Times articles"));
    readCta.addEventListener("click", function () { Sound.play("tap"); go("#/read"); });
    view.appendChild(readCta);

    if (prog.total > 0 && prog.done === prog.total) {
      var sc = computeScore();
      var cert = el("div", "ac-certcard");
      if (sc.pct >= PASS_MARK) {
        notifyCompletion();
        cert.classList.add("pass");
        cert.appendChild(el("p", "ac-cert-eyebrow", "Course complete"));
        cert.appendChild(el("h2", null, "You passed with " + sc.pct + "%"));
        cert.appendChild(el("p", null, "You have earned your Mutapa Times Academy certificate."));
        var cb = el("button", "ac-btn ac-btn--lg", "Claim your certificate");
        cb.addEventListener("click", function () { Sound.play("complete"); go("#/certificate"); });
        cert.appendChild(cb);
        var sb = el("button", "ac-btn ac-btn--ghost", "Submit your first article");
        sb.addEventListener("click", function () { Sound.play("tap"); go("#/submit"); });
        cert.appendChild(sb);
        var cvb = el("button", "ac-btn ac-btn--ghost", "Build your CV");
        cvb.addEventListener("click", function () { Sound.play("tap"); go("#/cv"); });
        cert.appendChild(cvb);
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
        var unlocked = isUnlocked(l.id);
        var wrap = el("div", "ac-node-wrap pos" + (i % 4));
        var cls = "ac-node" + (ls.done ? " is-done" : "") + (isCurrent ? " is-current" : "") + (l.checkpoint ? " is-checkpoint" : "") + (!unlocked && !ls.done ? " is-locked" : "");
        var node = el("button", cls); node.type = "button";
        var face = el("span", "ac-node-face", ls.done ? "✓" : (!unlocked ? "🔒" : (l.checkpoint ? "★" : String(i + 1))));
        node.appendChild(face);
        node.appendChild(el("span", "ac-node-label", (l.checkpoint ? "Checkpoint: " : "") + l.title));
        node.addEventListener("click", function () {
          if (!unlocked) { Sound.play("wrong"); flash(node, false); return; }
          Sound.play("tap"); go("#/lesson/" + l.id);
        });
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
    if (!isUnlocked(id)) { go("#/"); return; }
    // examMode hides explanations (real exams only). isExam drives the
    // exam look and feel (dark theme, briefing, timer) and is mirrored in
    // review so tutors see the real experience.
    examMode = !!lesson.checkpoint && !REVIEW;
    var isExam = !!lesson.checkpoint;
    clearExamTimer(); document.body.classList.toggle("ac-exam", isExam);
    clear(view); renderChips(); window.scrollTo(0, 0);

    var top = el("div", "ac-lessontop");
    var back = el("button", "ac-back", "← All lessons");
    back.addEventListener("click", function () { Sound.play("tap"); go("#/"); });
    top.appendChild(back);
    view.appendChild(top);

    view.appendChild(el("p", "ac-eyebrow", (lesson.checkpoint ? "Checkpoint · " : "") + lesson.title));
    view.appendChild(el("h1", "ac-h1", lesson.intro));

    if (!lesson.checkpoint) {
      var fig = el("figure", "ac-hero-img");
      var im = document.createElement("img");
      im.src = lessonImage(lesson); im.alt = ""; im.loading = "lazy";
      fig.appendChild(im); view.appendChild(fig);
    }

    // A written answer needs far longer than a tap question, so budget more
    // time for any write exercise (e.g. the in-exam 500-word CCBA story).
    var examSeconds = Math.max(120, lesson.exercises.reduce(function (s, ex) {
      return s + (ex.type === "write" ? (ex.long ? 720 : 240) : 45);
    }, 0));
    var examExpired = false;

    if (isExam) {
      var rules = el("div", "ac-exam-rules");
      rules.appendChild(el("h2", null, lesson.id === "final-exam" ? "This is the final step." : "Checkpoint exam"));
      rules.appendChild(el("p", null, lesson.id === "final-exam"
        ? "Everything you have learned comes down to this. Pass, and you complete the Mutapa Times Academy."
        : "A serious test of this unit. Treat it like the real thing."));
      var writeCount = lesson.exercises.filter(function (e) { return e.type === "write"; }).length;
      var qCount = lesson.exercises.length - writeCount;
      var ul = document.createElement("ul");
      [qCount + " questions" + (writeCount ? ", plus a written task an editor will assess" : ""),
        "About " + Math.ceil(examSeconds / 60) + " minutes, timed",
        "80% to pass (the written task is feedback only, not scored)",
        "No explanations until the end",
        "The clock starts the moment you begin"].forEach(function (t) { ul.appendChild(el("li", null, t)); });
      rules.appendChild(ul);
      view.appendChild(rules);

      var eg = el("div", "ac-exam-eg");
      eg.appendChild(el("p", "tag", "Example question, not scored"));
      eg.appendChild(el("p", "ac-q", "Which of these is news rather than PR?"));
      var egopts = el("div", "ac-opts");
      [["A company calling itself proud and world-class", false],
       ["A sourced report that a state firm's losses widened", true],
       ["A call to back our cause today", false]].forEach(function (o) {
        var b = el("button", "ac-opt" + (o[1] ? " is-correct" : "")); b.type = "button"; b.disabled = true; b.textContent = o[0]; egopts.appendChild(b);
      });
      eg.appendChild(egopts);
      eg.appendChild(el("p", "ac-explain good", "The middle one is news: it reports what happened, with a source. The real exam looks like this, but with no answers shown."));
      view.appendChild(eg);
    } else {
      lesson.cards.forEach(function (c, i) {
        var card = el("section", "ac-card ac-reveal");
        card.style.animationDelay = (i * 0.06) + "s";
        card.appendChild(el("p", "ac-kicker", "Read"));
        card.appendChild(el("h2", null, c.h));
        c.body.forEach(function (p) { card.appendChild(el("p", null, p)); });
        if (c.chart) card.appendChild(renderChart(c.chart));
        if (c.link && c.link.href) {
          var a = document.createElement("a");
          a.className = "ac-card-link"; a.href = c.link.href; a.target = "_blank"; a.rel = "noopener noreferrer";
          a.textContent = (c.link.label || "Read more") + " ↗";
          card.appendChild(a);
        }
        view.appendChild(card);
      });
    }

    var exHost = el("section", "ac-card ac-exhost");
    view.appendChild(exHost);

    if (!isExam) exHost.appendChild(el("p", "ac-readhint", "Read the section above first. Then start when you are ready."));
    var startWrap = el("div", "ac-actions");
    var startBtn = el("button", "ac-btn ac-btn--lg", isExam ? "Begin the exam" : ("Start the exercises (" + lesson.exercises.length + ")"));
    startWrap.appendChild(startBtn);
    exHost.appendChild(startWrap);

    var idx = 0;
    startBtn.addEventListener("click", function () {
      Sound.play("tap");
      if (isExam) startExamTimer(examSeconds, function () { examExpired = true; idx = lesson.exercises.length; runExercise(); });
      runExercise();
    });

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
      clear(exHost); clearExamTimer();
      var ls = lessonState(lesson.id);
      var pct = lessonScore(lesson);
      var passed = REVIEW || ls.done || pct >= LESSON_PASS;
      if (!passed) {
        save(); Sound.play("wrong");
        var fail = el("div", "ac-done-inline");
        fail.appendChild(el("h2", null, examExpired ? "Time is up" : "Not passed yet"));
        fail.appendChild(el("p", null, (examExpired ? "The clock ran out. " : "") + "You scored " + pct + "%. You need " + LESSON_PASS + "% to complete this " + (lesson.checkpoint ? "checkpoint" : "lesson") + ". Review the material and try again."));
        var fa = el("div", "ac-actions");
        var rt = el("button", "ac-btn", "Retry"); rt.addEventListener("click", function () { Sound.play("tap"); renderLesson(lesson.id); });
        var bk = el("button", "ac-btn ac-btn--ghost", "Back to map"); bk.addEventListener("click", function () { Sound.play("tap"); go("#/"); });
        fa.appendChild(rt); fa.appendChild(bk); fail.appendChild(fa); exHost.appendChild(fail);
        exHost.scrollIntoView({ behavior: "smooth", block: "start" }); return;
      }
      var gained = 0;
      if (!ls.done) { ls.done = true; gained = lesson.exercises.length * XP_PER_EXERCISE + XP_LESSON_BONUS; state.xp += gained; touchStreak(); save(); }
      renderChips();
      Sound.play("complete"); confetti();
      var done = el("div", "ac-done-inline ac-anim-pop");
      done.appendChild(el("p", "mark", "M·T"));
      done.appendChild(el("h2", null, lesson.checkpoint ? "Checkpoint passed" : "Lesson complete"));
      done.appendChild(el("p", null, (gained ? ("You earned " + gained + " XP. ") : "Revisited and still sharp. ") + "Score " + pct + "%."));
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
    if (!examMode) {
      var ex = el("p", "ac-explain " + (ok ? "good" : "bad"));
      ex.textContent = (opts.label || (ok ? "Correct. " : "Not quite. ")) + (explain || "");
      host.appendChild(ex); flash(ex, ok);
    }
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

  // Match: for each term, pick its match from a dropdown. Deterministic and
  // reliable on touch and desktop (the old tap-one-then-the-other mechanic was
  // fiddly), and the answers are graded together with a Check.
  RENDERERS.match = function (host, ex, done, next, rec) {
    host.appendChild(el("p", "ac-q", ex.q));
    host.appendChild(el("p", "ac-sub", ex.instruction || "Choose the correct match for each item, then check."));
    var options = shuffle(ex.pairs.map(function (p, i) { return { label: p.b, i: i }; }));
    var rows = el("div", "ac-match2"); host.appendChild(rows);
    var selects = [], check;
    ex.pairs.forEach(function (p, i) {
      var row = el("div", "ac-match2-row");
      row.appendChild(el("div", "ac-match2-term", p.a));
      var wrap = el("div", "ac-match2-pick");
      var sel = document.createElement("select"); sel.className = "ac-match2-select";
      var def = document.createElement("option"); def.value = ""; def.textContent = "Choose the match..."; def.disabled = true; def.selected = true;
      sel.appendChild(def);
      options.forEach(function (o) { var opt = document.createElement("option"); opt.value = String(o.i); opt.textContent = o.label; sel.appendChild(opt); });
      sel.dataset.correct = String(i);
      sel.addEventListener("change", function () { Sound.play("tap"); if (selects.every(function (s) { return s.value !== ""; })) check.disabled = false; });
      selects.push(sel); wrap.appendChild(sel); row.appendChild(wrap); rows.appendChild(row);
    });
    var acts = el("div", "ac-actions");
    check = el("button", "ac-btn", "Check"); check.disabled = true;
    check.addEventListener("click", function () {
      var ok = true;
      selects.forEach(function (s, ri) {
        s.disabled = true;
        var right = s.value === s.dataset.correct;
        var row = s.parentNode.parentNode;
        row.classList.add(right ? "is-correct" : "is-wrong");
        if (!right) { ok = false; row.appendChild(el("p", "ac-match2-fix", "Correct match: " + ex.pairs[ri].b)); }
      });
      check.disabled = true; done(); rec(ok); feedback(host, ok, ex.explain, next, { label: ok ? "All matched. " : "Some misses, see the corrections. " });
    });
    acts.appendChild(check); host.appendChild(acts);
  };

  RENDERERS.categorize = function (host, ex, done, next, rec) {
    host.appendChild(el("p", "ac-q", ex.q));
    host.appendChild(el("p", "ac-sub", ex.instruction || "Choose a category for each item."));
    var items = shuffle(ex.items.slice());
    var choices = items.map(function () { return null; });
    var rows = el("div", "ac-cat"); host.appendChild(rows);
    var check;

    items.forEach(function (it, ri) {
      var row = el("div", "ac-cat-row");
      row.appendChild(el("div", "ac-cat-text", it.text));
      var opts = el("div", "ac-cat-opts");
      ex.buckets.forEach(function (bk) {
        var b = el("button", "ac-cat-btn"); b.type = "button"; b.textContent = bk.label; b.dataset.bucket = bk.id;
        b.addEventListener("click", function () {
          if (row.dataset.locked) return; Sound.play("tap");
          choices[ri] = bk.id;
          opts.querySelectorAll(".ac-cat-btn").forEach(function (x) { x.classList.remove("is-sel"); });
          b.classList.add("is-sel");
          if (choices.every(Boolean)) check.disabled = false;
        });
        opts.appendChild(b);
      });
      row.appendChild(opts);
      rows.appendChild(row);
    });

    var acts = el("div", "ac-actions");
    check = el("button", "ac-btn", "Check"); check.disabled = true;
    check.addEventListener("click", function () {
      var ok = true;
      rows.querySelectorAll(".ac-cat-row").forEach(function (row, ri) {
        row.dataset.locked = "1";
        var correctBucket = items[ri].bucket;
        if (choices[ri] !== correctBucket) ok = false;
        row.querySelectorAll(".ac-cat-btn").forEach(function (b) {
          b.disabled = true; b.classList.remove("is-sel");
          if (b.dataset.bucket === correctBucket) b.classList.add("is-correct");
          else if (b.dataset.bucket === choices[ri]) b.classList.add("is-wrong");
        });
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

  // Complete a chart: a flow/pyramid/stack diagram with blanks to fill from a bank.
  RENDERERS.chartfill = function (host, ex, done, next, rec) {
    host.appendChild(el("p", "ac-q", ex.q));
    host.appendChild(el("p", "ac-sub", ex.instruction || "Tap a label to drop it into the next gap. Tap a filled gap to clear it."));
    var ctype = ex.chartType || "flow";
    var chart = el("div", "ac-cf ac-cf--" + ctype);
    var n = ex.slots.length, blanks = [], locked = false, bank;
    ex.slots.forEach(function (s, i) {
      var seg = el("div", "ac-cf-seg");
      if (ctype === "pyramid") seg.style.width = (100 - i * (n > 1 ? 52 / (n - 1) : 0)) + "%";
      if (s === "___" || s === "" || s == null) {
        seg.classList.add("ac-cf-blank"); seg.dataset.fill = "";
        seg.addEventListener("click", function () {
          if (locked || !seg.dataset.fill) return;
          Sound.play("tap"); var lbl = seg.dataset.fill;
          seg.dataset.fill = ""; seg.textContent = ""; seg.classList.remove("ac-cf-filled");
          addChip(lbl); updateCheck();
        });
        blanks.push(seg);
      } else { seg.classList.add("ac-cf-given"); seg.textContent = s; }
      chart.appendChild(seg);
      if (ctype === "flow" && i < n - 1) chart.appendChild(el("span", "ac-cf-arrow", "→"));
    });
    host.appendChild(chart);
    bank = el("div", "ac-cf-bank"); host.appendChild(bank);
    function addChip(lbl) {
      var c = el("button", "ac-cf-chip", lbl); c.type = "button";
      c.addEventListener("click", function () {
        if (locked) return;
        for (var i = 0; i < blanks.length; i++) {
          if (!blanks[i].dataset.fill) { Sound.play("tap"); blanks[i].dataset.fill = lbl; blanks[i].textContent = lbl; blanks[i].classList.add("ac-cf-filled"); c.remove(); updateCheck(); return; }
        }
      });
      bank.appendChild(c);
    }
    shuffle(ex.bank.slice()).forEach(addChip);
    var acts = el("div", "ac-actions");
    var check = el("button", "ac-btn", "Check"); check.disabled = true;
    function updateCheck() { check.disabled = !blanks.every(function (b) { return b.dataset.fill; }); }
    check.addEventListener("click", function () {
      locked = true; var ok = true;
      blanks.forEach(function (b, i) { var right = b.dataset.fill === ex.answer[i]; b.classList.add(right ? "is-correct" : "is-wrong"); if (!right) ok = false; });
      bank.querySelectorAll(".ac-cf-chip").forEach(function (c) { c.disabled = true; });
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
    var minWords = ex.minWords || 4;
    var ta = el("textarea", "ac-input" + (ex.long ? " ac-input--long" : "")); ta.setAttribute("maxlength", ex.long ? "4000" : "900");
    ta.placeholder = ex.long ? "Write your story here..." : "Write your answer..."; host.appendChild(ta);
    var target = ex.long ? " / about 500 words" : "";
    var count = el("p", "ac-count", "0 words" + target); host.appendChild(count);
    ta.addEventListener("input", function () { var n = words(ta.value); count.textContent = n + (n === 1 ? " word" : " words") + target; });
    var acts = el("div", "ac-actions");
    var submit = el("button", "ac-btn", GRADE_ENDPOINT ? "Get feedback" : "Reveal model answer");
    var status = el("span", "ac-status"); acts.appendChild(submit); acts.appendChild(status); host.appendChild(acts);
    submit.addEventListener("click", function () {
      if (words(ta.value) < minWords) { status.innerHTML = '<span class="ac-err">' + (ex.long ? "Write a fuller answer first (aim for around 500 words)." : "Write a full answer first.") + '</span>'; return; }
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
    function model(text) { var d = document.createElement("details"); d.className = "ac-model"; d.open = true; var s = document.createElement("summary"); s.textContent = "An editor's version"; d.appendChild(s); String(text).split("\n").forEach(function (p) { p = p.trim(); if (p) d.appendChild(el("p", null, p)); }); return d; }
    function fbList(title, items) { var w = el("div", "ac-fb"); w.appendChild(el("h3", null, title)); var ul = el("ul"); items.forEach(function (t) { ul.appendChild(el("li", null, t)); }); w.appendChild(ul); return w; }
    function finish() { done(); var a2 = el("div", "ac-actions"); var c = el("button", "ac-btn", "Continue"); c.addEventListener("click", function () { Sound.play("tap"); next(); }); a2.appendChild(c); host.appendChild(a2); }
  };

  // ---------- certificate ----------
  var MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
  function dateStr() { var d = new Date(); return d.getDate() + " " + MONTHS[d.getMonth()] + " " + d.getFullYear(); }
  function certId(name) { var s = (name || "") + "|" + dateStr(), h = 0; for (var i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) >>> 0; return "MTA-" + h.toString(36).toUpperCase().slice(0, 8); }
  // Graduation stamp ("Month Year"), captured once and reused on the CV.
  function gradDate() {
    var d = "";
    try { d = localStorage.getItem("mt_academy_grad") || ""; } catch (e) {}
    if (!d) { var x = new Date(); d = MONTHS[x.getMonth()] + " " + x.getFullYear(); try { localStorage.setItem("mt_academy_grad", d); } catch (e) {} }
    return d;
  }

  // Tell the comms worker the learner has finished, so it sends the pitch
  // invitation and starts the monthly reminders. Fires at most once.
  function notifyCompletion() {
    if (REVIEW || !CERT_ENDPOINT) return;
    try { if (localStorage.getItem("mt_academy_completed") === "1") return; } catch (e) {}
    var email = "", nm = state.name || "";
    try { email = localStorage.getItem("mt_academy_email") || ""; if (!nm) nm = localStorage.getItem("mt_academy_name") || ""; } catch (e) {}
    if (!email || !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email) || nm.length < 2) return;
    try {
      fetch(CERT_ENDPOINT, { method: "POST", keepalive: true, headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ kind: "complete", name: nm, email: email }) })
        .then(function (r) { if (r && r.ok) { try { localStorage.setItem("mt_academy_completed", "1"); } catch (e) {} } })
        .catch(function () {});
    } catch (e) {}
  }

  function renderCertificate() {
    if (!certEligible()) { go("#/"); return; }
    leaveExam();
    clear(view); renderChips();
    notifyCompletion();
    var sc = computeScore();
    var serverCred = { id: "", date: dateStr() };
    try { serverCred.id = localStorage.getItem("mt_academy_cert_id") || ""; } catch (e) {}
    function credId() { return serverCred.id || certId(((typeof ni !== "undefined" && ni && ni.value) || "").trim() || "Your Name"); }

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
      meta.appendChild(el("span", null, "Awarded " + serverCred.date));
      meta.appendChild(el("span", null, "ID " + credId()));
      cert.appendChild(meta);
      cert.appendChild(el("p", "ac-cert-verify", "Verify at mutapatimes.com/academy/verify  ·  ID " + credId()));
      certWrap.appendChild(cert);
    }
    ni.addEventListener("input", function () { state.name = ni.value; save(); paint(); });
    ni.addEventListener("change", function () { registerCred(); });
    paint();

    var acts = el("div", "ac-actions");
    var dl = el("button", "ac-btn", "Download / Print");
    dl.addEventListener("click", function () { Sound.play("tap"); window.print(); });
    var liBtn = el("a", "ac-btn ac-btn--ghost", "Add to LinkedIn"); liBtn.target = "_blank"; liBtn.rel = "noopener noreferrer";
    var vBtn = el("a", "ac-btn ac-btn--ghost", "Verify certificate"); vBtn.target = "_blank"; vBtn.rel = "noopener noreferrer";
    acts.appendChild(dl); acts.appendChild(liBtn); acts.appendChild(vBtn); view.appendChild(acts);
    function updateShareLinks() {
      var id = credId();
      var verifyUrl = "https://mutapatimes.com/academy/verify/?id=" + encodeURIComponent(id);
      vBtn.href = verifyUrl;
      var now = new Date();
      liBtn.href = "https://www.linkedin.com/profile/add?startTask=CERTIFICATION_NAME"
        + "&name=" + encodeURIComponent("Professional Certificate in Journalism")
        + "&organizationName=" + encodeURIComponent("The Mutapa Times Academy")
        + "&issueYear=" + now.getFullYear() + "&issueMonth=" + (now.getMonth() + 1)
        + "&certUrl=" + encodeURIComponent(verifyUrl)
        + "&certId=" + encodeURIComponent(id);
    }
    function registerCred() {
      if (REVIEW || !PAY_ENDPOINT || !ACCESS.token || !ACCESS.email) return;
      var nm = (ni.value || "").trim(); if (nm.length < 2) return;
      fetch(PAY_ENDPOINT, { method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "cert-issue", email: ACCESS.email, token: ACCESS.token, name: nm, score: sc.pct, date: dateStr() }) })
        .then(function (r) { return r.ok ? r.json() : null; })
        .then(function (d) { if (d && d.id) { serverCred.id = d.id; if (d.date) serverCred.date = d.date; try { localStorage.setItem("mt_academy_cert_id", d.id); } catch (e) {} paint(); updateShareLinks(); } })
        .catch(function () {});
    }
    updateShareLinks(); registerCred();

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
      fetch(CERT_ENDPOINT, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ name: name, email: email, score: sc.pct, date: serverCred.date, id: credId() }) })
        .then(function (r) { if (!r.ok) throw 0; return r.json(); })
        .then(function () { est.innerHTML = '<span class="ac-ok">Sent. Check your inbox.</span>'; Sound.play("complete"); try { localStorage.setItem("mt_academy_email", email); localStorage.setItem("mt_academy_name", name); } catch (e) {} notifyCompletion(); })
        .catch(function () { eb.disabled = false; est.innerHTML = '<span class="ac-err">Could not send. Try Download / Print instead.</span>'; });
    });

    var bridge = el("div", "ac-capstone-cta");
    bridge.appendChild(el("p", "ac-cert-eyebrow", "One last step, for a real byline"));
    bridge.appendChild(el("h3", null, "Submit your first article"));
    bridge.appendChild(el("p", null, "Now put it into practice. Write a complete article of your own choice, get instant feedback from a Mutapa Times editor, and submit it for review. The strongest pieces can be published with your byline."));
    var sb = el("button", "ac-btn ac-btn--lg", "Write and submit your article");
    sb.addEventListener("click", function () { Sound.play("tap"); go("#/submit"); });
    var sa = el("div", "ac-actions"); sa.appendChild(sb); bridge.appendChild(sa);
    view.appendChild(bridge);

    var cvcta = el("div", "ac-capstone-cta");
    cvcta.appendChild(el("p", "ac-cert-eyebrow", "For your job hunt"));
    cvcta.appendChild(el("h3", null, "Build your CV"));
    cvcta.appendChild(el("p", null, "Create a clean, professional CV with your Mutapa Times Academy qualification and final mark already included, then download it as a PDF."));
    var cvb = el("button", "ac-btn ac-btn--lg", "Build your CV");
    cvb.addEventListener("click", function () { Sound.play("tap"); go("#/cv"); });
    var cva = el("div", "ac-actions"); cva.appendChild(cvb); cvcta.appendChild(cva);
    view.appendChild(cvcta);

    window.scrollTo(0, 0);
  }

  // ---------- CV builder ----------
  function loadCV() {
    var d = null;
    try { d = JSON.parse(localStorage.getItem("mt_academy_cv")); } catch (e) {}
    if (!d || typeof d !== "object") d = {};
    ["name", "title", "email", "phone", "location", "links", "summary", "skills"].forEach(function (k) { if (typeof d[k] !== "string") d[k] = ""; });
    if (!Array.isArray(d.experience)) d.experience = [{ role: "", org: "", dates: "", detail: "" }];
    if (!Array.isArray(d.education)) d.education = [];
    return d;
  }
  function saveCV(d) { try { localStorage.setItem("mt_academy_cv", JSON.stringify(d)); } catch (e) {} }

  function renderCV() {
    if (!REVIEW && !certEligible()) { go("#/"); return; }
    leaveExam(); clear(view); renderChips();
    var sc = computeScore();
    var grad = gradDate();
    var cv = loadCV();
    try {
      if (!cv.name) cv.name = state.name || localStorage.getItem("mt_academy_name") || "";
      if (!cv.email) cv.email = localStorage.getItem("mt_academy_email") || "";
    } catch (e) {}

    var top = el("div", "ac-lessontop"); var back = el("button", "ac-back", "← Back");
    back.addEventListener("click", function () { Sound.play("tap"); go("#/"); }); top.appendChild(back); view.appendChild(top);
    view.appendChild(el("p", "ac-eyebrow", "Your CV"));
    view.appendChild(el("h1", "ac-h1", "Build your CV"));
    var intro = el("div", "ac-brief ac-cv-intro");
    intro.appendChild(el("p", null, "Fill in your details on the left and watch your CV build on the right. Your Mutapa Times Academy qualification and final mark are added automatically. When you are happy, download it as a PDF."));
    view.appendChild(intro);

    var wrap = el("div", "ac-cv");
    var formCol = el("div", "ac-cv-form");
    var prevCol = el("div", "ac-cv-preview");
    wrap.appendChild(formCol); wrap.appendChild(prevCol);
    view.appendChild(wrap);

    function persist() { saveCV(cv); paint(); }
    function lbl(t) { return el("label", "ac-cv-label", t); }
    function inp(val, ph, on) { var i = document.createElement("input"); i.type = "text"; i.className = "ac-cert-input"; i.value = val || ""; i.placeholder = ph || ""; i.addEventListener("input", function () { on(i.value); }); return i; }
    function area(val, ph, on) { var t = el("textarea", "ac-input"); t.value = val || ""; t.placeholder = ph || ""; t.addEventListener("input", function () { on(t.value); }); return t; }
    function fieldRow(labelText, node) { var w = el("div", "ac-cv-field"); w.appendChild(lbl(labelText)); w.appendChild(node); return w; }

    function renderForm() {
      clear(formCol);

      var s1 = el("section", "ac-cv-sec");
      s1.appendChild(el("h2", "ac-cv-sech", "Your details"));
      s1.appendChild(fieldRow("Full name", inp(cv.name, "e.g. Tendai Kuwanda", function (v) { cv.name = v; persist(); })));
      s1.appendChild(fieldRow("Professional title", inp(cv.title, "e.g. Journalist and content writer", function (v) { cv.title = v; persist(); })));
      s1.appendChild(fieldRow("Email", inp(cv.email, "you@email.com", function (v) { cv.email = v; persist(); })));
      s1.appendChild(fieldRow("Phone", inp(cv.phone, "e.g. +263 ...", function (v) { cv.phone = v; persist(); })));
      s1.appendChild(fieldRow("Location", inp(cv.location, "e.g. Harare, Zimbabwe", function (v) { cv.location = v; persist(); })));
      s1.appendChild(fieldRow("Links (LinkedIn, portfolio)", inp(cv.links, "e.g. linkedin.com/in/yourname", function (v) { cv.links = v; persist(); })));
      formCol.appendChild(s1);

      var s2 = el("section", "ac-cv-sec");
      s2.appendChild(el("h2", "ac-cv-sech", "Professional summary"));
      s2.appendChild(area(cv.summary, "Two or three sentences about who you are and what you do.", function (v) { cv.summary = v; persist(); }));
      formCol.appendChild(s2);

      var s3 = el("section", "ac-cv-sec");
      s3.appendChild(el("h2", "ac-cv-sech", "Work experience"));
      cv.experience.forEach(function (it, i) {
        var row = el("div", "ac-cv-entry");
        row.appendChild(fieldRow("Role", inp(it.role, "e.g. Contributor", function (v) { it.role = v; persist(); })));
        row.appendChild(fieldRow("Organisation", inp(it.org, "e.g. The Mutapa Times", function (v) { it.org = v; persist(); })));
        row.appendChild(fieldRow("Dates", inp(it.dates, "e.g. 2025 to present", function (v) { it.dates = v; persist(); })));
        row.appendChild(fieldRow("What you did", area(it.detail, "One or two lines on your impact.", function (v) { it.detail = v; persist(); })));
        var del = el("button", "ac-cv-del", "Remove"); del.type = "button";
        del.addEventListener("click", function () { cv.experience.splice(i, 1); saveCV(cv); renderForm(); paint(); });
        row.appendChild(del); s3.appendChild(row);
      });
      var addE = el("button", "ac-cv-add", "+ Add role"); addE.type = "button";
      addE.addEventListener("click", function () { cv.experience.push({ role: "", org: "", dates: "", detail: "" }); saveCV(cv); renderForm(); paint(); });
      s3.appendChild(addE); formCol.appendChild(s3);

      var s4 = el("section", "ac-cv-sec");
      s4.appendChild(el("h2", "ac-cv-sech", "Education"));
      var locked = el("div", "ac-cv-locked");
      locked.appendChild(el("p", "ac-cv-locked-h", "The Mutapa Times Academy"));
      locked.appendChild(el("p", "ac-cv-locked-b", "Professional Certificate in Journalism · Graded " + sc.pct + "% · " + grad));
      locked.appendChild(el("p", "ac-cv-locked-note", "Added to every graduate's CV automatically"));
      s4.appendChild(locked);
      cv.education.forEach(function (it, i) {
        var row = el("div", "ac-cv-entry");
        row.appendChild(fieldRow("Qualification", inp(it.qual, "e.g. BSc in Media Studies", function (v) { it.qual = v; persist(); })));
        row.appendChild(fieldRow("School or university", inp(it.school, "e.g. University of Zimbabwe", function (v) { it.school = v; persist(); })));
        row.appendChild(fieldRow("Dates", inp(it.dates, "e.g. 2018 to 2021", function (v) { it.dates = v; persist(); })));
        var del = el("button", "ac-cv-del", "Remove"); del.type = "button";
        del.addEventListener("click", function () { cv.education.splice(i, 1); saveCV(cv); renderForm(); paint(); });
        row.appendChild(del); s4.appendChild(row);
      });
      var addEd = el("button", "ac-cv-add", "+ Add education"); addEd.type = "button";
      addEd.addEventListener("click", function () { cv.education.push({ qual: "", school: "", dates: "" }); saveCV(cv); renderForm(); paint(); });
      s4.appendChild(addEd); formCol.appendChild(s4);

      var s5 = el("section", "ac-cv-sec");
      s5.appendChild(el("h2", "ac-cv-sech", "Skills"));
      s5.appendChild(area(cv.skills, "Comma separated, e.g. Reporting, interviewing, fact-checking, SEO.", function (v) { cv.skills = v; persist(); }));
      formCol.appendChild(s5);

      var acts = el("div", "ac-actions");
      var dl = el("button", "ac-btn ac-btn--lg", "Download / Save as PDF");
      dl.addEventListener("click", function () { Sound.play("tap"); window.print(); });
      acts.appendChild(dl); formCol.appendChild(acts);
      formCol.appendChild(el("p", "ac-cv-hint", "In the print dialog, choose 'Save as PDF' as the destination."));
    }

    function entryHead(roleText, dates) {
      var head = el("div", "cvd-entry-head");
      head.appendChild(el("span", "cvd-entry-role", roleText));
      if (dates) head.appendChild(el("span", "cvd-entry-dates", dates));
      return head;
    }
    function paint() {
      clear(prevCol);
      var doc = el("div", "ac-cv-doc");
      doc.appendChild(el("h1", "cvd-name", (cv.name || "Your Name")));
      if (cv.title) doc.appendChild(el("p", "cvd-title", cv.title));
      var contact = [cv.email, cv.phone, cv.location, cv.links].filter(function (x) { return x && x.trim(); }).join("   ·   ");
      if (contact) doc.appendChild(el("p", "cvd-contact", contact));

      if (cv.summary && cv.summary.trim()) {
        var se = el("div", "cvd-section"); se.appendChild(el("h2", "cvd-sech", "Profile")); se.appendChild(el("p", "cvd-text", cv.summary)); doc.appendChild(se);
      }

      var exp = cv.experience.filter(function (it) { return it.role || it.org || it.detail || it.dates; });
      if (exp.length) {
        var s = el("div", "cvd-section"); s.appendChild(el("h2", "cvd-sech", "Experience"));
        exp.forEach(function (it) {
          var e = el("div", "cvd-entry");
          e.appendChild(entryHead((it.role || "") + (it.org ? ", " + it.org : ""), it.dates));
          if (it.detail) e.appendChild(el("p", "cvd-entry-detail", it.detail));
          s.appendChild(e);
        });
        doc.appendChild(s);
      }

      var edS = el("div", "cvd-section"); edS.appendChild(el("h2", "cvd-sech", "Education"));
      var ac = el("div", "cvd-entry cvd-academy");
      ac.appendChild(entryHead("Professional Certificate in Journalism, The Mutapa Times Academy", grad));
      ac.appendChild(el("p", "cvd-entry-detail", "Completed with a final mark of " + sc.pct + "%."));
      edS.appendChild(ac);
      cv.education.filter(function (it) { return it.qual || it.school || it.dates; }).forEach(function (it) {
        var e = el("div", "cvd-entry");
        e.appendChild(entryHead((it.qual || "") + (it.school ? ", " + it.school : ""), it.dates));
        edS.appendChild(e);
      });
      doc.appendChild(edS);

      if (cv.skills && cv.skills.trim()) {
        var sk = el("div", "cvd-section"); sk.appendChild(el("h2", "cvd-sech", "Skills")); sk.appendChild(el("p", "cvd-skills", cv.skills)); doc.appendChild(sk);
      }
      prevCol.appendChild(doc);
    }

    renderForm(); paint();
    window.scrollTo(0, 0);
  }

  // ---------- Reading Room: analyse recent original articles ----------
  function renderReading() {
    leaveExam(); clear(view); renderChips();
    var top = el("div", "ac-lessontop"); var back = el("button", "ac-back", "← All lessons");
    back.addEventListener("click", function () { Sound.play("tap"); go("#/"); }); top.appendChild(back); view.appendChild(top);
    view.appendChild(el("p", "ac-eyebrow", "Reading Room"));
    view.appendChild(el("h1", "ac-h1", "Read and analyse the news"));
    var lead = el("div", "ac-brief");
    lead.appendChild(el("p", null, "A journalist reads constantly. Each time you visit you will find the two most recent original Mutapa Times articles. Read them both, then analyse them. This is the single best habit for becoming a sharper reporter."));
    lead.appendChild(el("p", null, "Then share what you read with your own take, and tag @mutapatimes. Reporters are most active on text-first platforms like X, Threads and Reddit, so post there and reply to other journalists. Every article you share earns you a reward."));
    view.appendChild(lead);
    var doneN = state.readCount || 0;
    if (doneN > 0) view.appendChild(el("p", "ac-read-count", "You have completed " + doneN + (doneN === 1 ? " analysis" : " analyses") + " so far. Keep going."));
    var shN = state.shareCount || 0;
    if (shN > 0) view.appendChild(el("p", "ac-read-count", "You have shared " + shN + (shN === 1 ? " article" : " articles") + ". Keep building your presence."));

    var host = el("div"); host.appendChild(el("p", "ac-readhint", "Loading the latest articles...")); view.appendChild(host);

    fetch("/academy/reading.json", { cache: "no-store" })
      .then(function (r) { if (!r.ok) throw 0; return r.json(); })
      .then(function (d) { render((d && d.articles) || []); })
      .catch(function () { clear(host); host.appendChild(el("p", "ac-err", "Could not load the latest articles. Read them directly at mutapatimes.com and try again later.")); });

    function model(text, summaryText) {
      var d = document.createElement("details"); d.className = "ac-model"; d.open = true;
      var s = document.createElement("summary"); s.textContent = summaryText || "What a strong analysis notices"; d.appendChild(s);
      String(text).split("\n").forEach(function (p) { p = p.trim(); if (p) d.appendChild(el("p", null, p)); });
      return d;
    }
    function fbList(t, items) { var w = el("div", "ac-fb"); w.appendChild(el("h3", null, t)); var ul = el("ul"); items.forEach(function (x) { ul.appendChild(el("li", null, x)); }); w.appendChild(ul); return w; }

    // Reward a share, once per article, with a little XP.
    function rewardShare(slug, msgNode) {
      if (REVIEW) { if (msgNode) msgNode.textContent = "Shared."; return; }
      state.shared = state.shared || {};
      if (!state.shared[slug]) {
        state.shared[slug] = true;
        state.shareCount = (state.shareCount || 0) + 1;
        state.xp = (state.xp || 0) + 15;
        save(); renderChips(); floatXP(15);
        if (msgNode) msgNode.textContent = "Nice. +15 XP for sharing. Now go reply to a journalist on the thread.";
      } else if (msgNode) {
        msgNode.textContent = "Shared again. Thanks for spreading good journalism.";
      }
    }

    function shareBlock(a) {
      var url = "https://mutapatimes.com" + a.url;
      var wrap = document.createElement("details"); wrap.className = "ac-share";
      var sum = document.createElement("summary"); sum.className = "ac-share-sum"; sum.textContent = "Share your take"; wrap.appendChild(sum);
      var ta = el("textarea", "ac-input ac-share-text"); ta.setAttribute("maxlength", "400");
      ta.value = "My take: [add your thought here]. \"" + a.title + "\" via @mutapatimes " + url;
      wrap.appendChild(ta);
      wrap.appendChild(el("p", "ac-share-tip", "Tag @mutapatimes, then reply to a reporter on the thread. On X, Threads and Reddit that is how relationships, sources and jobs start."));
      var btns = el("div", "ac-share-btns");
      var rew = el("p", "ac-share-reward");
      function openShare(buildUrl) { var u = buildUrl(ta.value.trim()); var w = window.open(u, "_blank", "noopener,noreferrer"); if (w) w.opener = null; rewardShare(a.slug, rew); }
      function btn(label, fn) { var b = el("button", "ac-share-btn", label); b.type = "button"; b.addEventListener("click", function () { Sound.play("tap"); fn(); }); return b; }
      btns.appendChild(btn("Post on X", function () { openShare(function (t) { return "https://twitter.com/intent/tweet?text=" + encodeURIComponent(t); }); }));
      btns.appendChild(btn("Threads", function () { openShare(function (t) { return "https://www.threads.net/intent/post?text=" + encodeURIComponent(t); }); }));
      btns.appendChild(btn("Reddit", function () { openShare(function () { return "https://www.reddit.com/submit?url=" + encodeURIComponent(url) + "&title=" + encodeURIComponent(a.title); }); }));
      btns.appendChild(btn("Copy text", function () {
        var txt = ta.value.trim();
        try { if (navigator.clipboard) navigator.clipboard.writeText(txt); } catch (e) {}
        rewardShare(a.slug, rew);
      }));
      wrap.appendChild(btns); wrap.appendChild(rew);
      return wrap;
    }

    function render(articles) {
      clear(host);
      if (!articles.length) { host.appendChild(el("p", null, "No articles are available right now. Please check back soon.")); return; }
      var pair = articles.slice(0, 2);

      var grid = el("div", "ac-read-grid");
      pair.forEach(function (a, i) {
        var card = el("article", "ac-read-card");
        card.appendChild(el("span", "ac-read-tag", (a.category || "News") + " · Article " + (i + 1)));
        card.appendChild(el("h2", "ac-read-title", a.title));
        if (a.summary) card.appendChild(el("p", "ac-read-sum", a.summary));
        var link = document.createElement("a"); link.className = "ac-card-link"; link.href = a.url; link.target = "_blank"; link.rel = "noopener noreferrer"; link.textContent = "Read the full article ↗";
        card.appendChild(link);
        card.appendChild(shareBlock(a));
        grid.appendChild(card);
      });
      host.appendChild(grid);

      var task = el("section", "ac-card");
      task.appendChild(el("p", "ac-kicker", "As you read, look for"));
      var ul = el("div", "ac-checklist");
      ["The lede: the single most important point, and how each piece opens.",
        "The sources: who is quoted, and whether they are independent.",
        "The angle: the framing the writer has chosen.",
        "What is missing: other voices, data or context you would add.",
        "The news value: why it matters, and to whom."].forEach(function (q) {
        var lab = el("label", "ac-check"); var cb = document.createElement("input"); cb.type = "checkbox";
        cb.addEventListener("change", function () { if (cb.checked) Sound.play("tap"); });
        lab.appendChild(cb); lab.appendChild(el("span", null, q)); ul.appendChild(lab);
      });
      task.appendChild(ul);

      task.appendChild(el("p", "ac-q", "Now write your analysis"));
      var brief = el("div", "ac-brief");
      brief.appendChild(el("p", null, "In about 150 words, analyse the two articles together: identify each lede and angle, assess the sources and balance, note what is missing, and say how the two pieces differ in approach."));
      task.appendChild(brief);
      var ta = el("textarea", "ac-input ac-input--long"); ta.setAttribute("maxlength", "3000"); ta.placeholder = "Write your analysis..."; task.appendChild(ta);
      var count = el("p", "ac-count", "0 words"); task.appendChild(count);
      ta.addEventListener("input", function () { var n = words(ta.value); count.textContent = n + (n === 1 ? " word" : " words"); });

      var acts = el("div", "ac-actions");
      var sub = el("button", "ac-btn ac-btn--lg", GRADE_ENDPOINT ? "Get feedback" : "Reveal what to look for");
      var status = el("span", "ac-status"); acts.appendChild(sub); acts.appendChild(status); task.appendChild(acts);
      host.appendChild(task);

      function logDone() { state.readCount = (state.readCount || 0) + 1; save(); }
      function finish() { var a2 = el("div", "ac-actions"); var c = el("button", "ac-btn", "Back to course"); c.addEventListener("click", function () { Sound.play("tap"); go("#/"); }); a2.appendChild(c); task.appendChild(a2); }
      function aiBox(dd) {
        var box = el("div", "ac-result"); var score = Math.max(0, Math.min(100, parseInt(dd.score, 10) || 0));
        var row = el("div", "ac-score " + (score >= 70 ? "pass" : "revise")); row.appendChild(el("b", null, String(score))); row.appendChild(el("span", null, dd.verdict || "")); box.appendChild(row);
        if (dd.strengths && dd.strengths.length) box.appendChild(fbList("What worked", dd.strengths));
        if (dd.improvements && dd.improvements.length) box.appendChild(fbList("Sharpen this", dd.improvements));
        if (dd.model_answer) box.appendChild(model(dd.model_answer));
        task.appendChild(box); Sound.play(score >= 70 ? "correct" : "wrong");
      }

      sub.addEventListener("click", function () {
        if (words(ta.value) < 30) { status.innerHTML = '<span class="ac-err">Write a fuller analysis first (aim for about 150 words).</span>'; return; }
        ta.disabled = true; sub.disabled = true; Sound.play("tap");
        if (!GRADE_ENDPOINT) {
          var box = el("div", "ac-result");
          box.appendChild(model("A strong analysis names each article's lede and angle, says who is quoted and whether the sourcing is balanced, points to what is missing (other voices, data, context), explains why the story matters, and compares how the two pieces frame their subjects differently."));
          task.appendChild(box); logDone(); finish(); return;
        }
        status.innerHTML = '<span class="ac-spin">Your tutor is reading...</span>';
        var titles = pair.map(function (a, i) { return (i === 0 ? "A: " : "B: ") + a.title; }).join("  |  ");
        var sums = pair.map(function (a, i) { return (i === 0 ? "A: " : "B: ") + (a.summary || ""); }).join("  ||  ");
        fetch(GRADE_ENDPOINT, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ kind: "analysis", title: titles, summary: sums, answer: ta.value.trim() }) })
          .then(function (r) { if (!r.ok) throw 0; return r.json(); })
          .then(function (dd) { status.textContent = ""; aiBox(dd); logDone(); finish(); })
          .catch(function () { status.textContent = ""; var box = el("div", "ac-result"); box.appendChild(el("h3", "ac-selfhead", "Could not reach your tutor")); box.appendChild(el("p", null, "Mark your own work against the checklist above, then continue.")); task.appendChild(box); logDone(); finish(); });
      });
    }
    window.scrollTo(0, 0);
  }

  // ---------- final capstone: submit a real article ----------
  function renderSubmission() {
    if (!REVIEW && !certEligible()) { go("#/"); return; }
    leaveExam();
    clear(view); renderChips();

    var top = el("div", "ac-lessontop"); var back = el("button", "ac-back", "← Back");
    back.addEventListener("click", function () { Sound.play("tap"); go("#/certificate"); }); top.appendChild(back); view.appendChild(top);
    view.appendChild(el("p", "ac-eyebrow", "Final capstone · Your first byline"));
    view.appendChild(el("h1", "ac-h1", "Submit an article for review"));

    var lead = el("div", "ac-brief");
    lead.appendChild(el("p", null, "Choose any real story you can report and write it as a complete Mutapa Times article. Fill in every field below, then get instant feedback from an editor before you submit."));
    lead.appendChild(el("p", null, "You can revise and re-check as many times as you like. When you submit, your article goes to the Mutapa Times editors for review. The strongest pieces are published with your byline."));
    view.appendChild(lead);

    var savedEmail = "";
    try { savedEmail = localStorage.getItem("mt_academy_email") || ""; } catch (e) {}

    var form = el("div", "ac-subform");
    function field(labelText, hint, node) {
      var w = el("div", "ac-field");
      w.appendChild(el("label", "ac-cert-label", labelText));
      if (hint) w.appendChild(el("p", "ac-field-hint", hint));
      w.appendChild(node); form.appendChild(w); return node;
    }
    function input(ph, val, max) { var i = document.createElement("input"); i.type = "text"; i.className = "ac-cert-input"; i.placeholder = ph; if (val) i.value = val; if (max) i.maxLength = max; return i; }
    function area(ph, max, longCls) { var t = el("textarea", "ac-input" + (longCls ? " ac-input--long" : "")); t.placeholder = ph; if (max) t.setAttribute("maxlength", String(max)); return t; }

    var nameI = field("Your name (the byline credit)", "How your name should appear on the article.", input("e.g. Tendai Kuwanda", state.name || "", 60));
    var emailI = field("Your email", "So the editors can reply to you.", input("you@email.com", savedEmail, 120));
    var imageI = field("Image link", "Paste a URL to your photo or illustration. Use an image you have the right to publish.", input("https://...", "", 400));
    var capI = field("Image caption and credit", "What the image shows, and who took it.", input("e.g. Vendors at Mbare market. Photo: Your Name", "", 200));
    var headI = field("Headline", "Accurate, specific and active. Say what happened.", input("Your headline", "", 160));
    var sumI = field("Summary (standfirst)", "One or two sentences that set up the story.", area("A short summary that draws the reader in.", 400));
    var bodyI = field("The article", "Aim for around 400 to 700 words. Lead with the news, attribute claims, add context and balance.", area("Write your full article here...", 9000, true));
    var bioI = field("Your bio", "One or two sentences about you, as it would run under the article.", area("e.g. Tendai Kuwanda is a graduate of the Mutapa Times Academy reporting on...", 400));
    view.appendChild(form);

    var bcount = el("p", "ac-count", "0 words"); view.appendChild(bcount);
    bodyI.addEventListener("input", function () { var n = words(bodyI.value); bcount.textContent = n + (n === 1 ? " word" : " words"); });

    var fbBox = el("div"); view.appendChild(fbBox);

    var acts = el("div", "ac-actions");
    var fbBtn = el("button", "ac-btn ac-btn--lg", GRADE_ENDPOINT ? "Get editor feedback" : "Check my work");
    var subBtn = el("button", "ac-btn ac-btn--ghost", "Submit to the editors"); subBtn.disabled = true;
    var status = el("span", "ac-status");
    acts.appendChild(fbBtn); acts.appendChild(subBtn); acts.appendChild(status); view.appendChild(acts);

    function payload() {
      return {
        name: (nameI.value || "").trim(), byline: (nameI.value || "").trim(),
        email: (emailI.value || "").trim(),
        imageUrl: (imageI.value || "").trim(), imageCaption: (capI.value || "").trim(),
        headline: (headI.value || "").trim(), summary: (sumI.value || "").trim(),
        body: (bodyI.value || "").trim(), bio: (bioI.value || "").trim()
      };
    }
    function ready() {
      var p = payload();
      if (p.headline.length < 3) { status.innerHTML = '<span class="ac-err">Add a headline.</span>'; return null; }
      if (words(p.body) < 120) { status.innerHTML = '<span class="ac-err">Write a fuller article first (aim for 400 words or more).</span>'; return null; }
      status.textContent = ""; return p;
    }

    fbBtn.addEventListener("click", function () {
      var p = ready(); if (!p) return;
      Sound.play("tap");
      if (!GRADE_ENDPOINT) { clear(fbBox); fbBox.appendChild(selfCheckBox()); subBtn.disabled = false; return; }
      fbBtn.disabled = true; status.innerHTML = '<span class="ac-spin">Your editor is reading...</span>';
      p.kind = "submission"; p.imageDesc = p.imageCaption;
      fetch(GRADE_ENDPOINT, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(p) })
        .then(function (r) { if (!r.ok) throw 0; return r.json(); })
        .then(function (d) { status.textContent = ""; fbBtn.disabled = false; fbBtn.textContent = "Re-check after editing"; clear(fbBox); fbBox.appendChild(submissionFeedback(d)); subBtn.disabled = false; Sound.play(d.score >= 70 ? "correct" : "wrong"); fbBox.scrollIntoView({ behavior: "smooth", block: "start" }); })
        .catch(function () { status.textContent = ""; fbBtn.disabled = false; clear(fbBox); fbBox.appendChild(selfCheckBox()); subBtn.disabled = false; });
    });

    subBtn.addEventListener("click", function () {
      var p = ready(); if (!p) return;
      if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(p.email)) { status.innerHTML = '<span class="ac-err">Enter a valid email so the editors can reply.</span>'; return; }
      if (p.name.length < 2) { status.innerHTML = '<span class="ac-err">Add your name for the byline.</span>'; return; }
      try { localStorage.setItem("mt_academy_email", p.email); } catch (e) {}
      if (!CERT_ENDPOINT) { status.innerHTML = '<span class="ac-ok">Saved. Submission delivery is not set up yet, so email your article to news@mutapatimes.com.</span>'; return; }
      subBtn.disabled = true; status.innerHTML = '<span class="ac-spin">Sending to the editors...</span>';
      p.kind = "submission";
      fetch(CERT_ENDPOINT, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(p) })
        .then(function (r) { if (!r.ok) throw 0; return r.json(); })
        .then(function () { Sound.play("complete"); confetti(); submitted(); })
        .catch(function () { subBtn.disabled = false; status.innerHTML = '<span class="ac-err">Could not send. Please email your article to news@mutapatimes.com.</span>'; });
    });

    function submitted() {
      clear(view);
      var done = el("div", "ac-done-inline ac-anim-pop");
      done.appendChild(el("p", "mark", "M·T"));
      done.appendChild(el("h2", null, "Submitted. Well done."));
      done.appendChild(el("p", null, "Your article is with the Mutapa Times editors. If it is selected, we will be in touch about publishing it with your byline. Either way, you can list this work in your portfolio."));
      var a = el("div", "ac-actions");
      var h = el("button", "ac-btn", "Back to your certificate"); h.addEventListener("click", function () { Sound.play("tap"); go("#/certificate"); });
      a.appendChild(h); done.appendChild(a); view.appendChild(done);
      window.scrollTo(0, 0);
    }

    function submissionFeedback(d) {
      var box = el("div", "ac-result");
      var score = Math.max(0, Math.min(100, parseInt(d.score, 10) || 0));
      var row = el("div", "ac-score " + (score >= 70 ? "pass" : "revise"));
      row.appendChild(el("b", null, String(score)));
      row.appendChild(el("span", null, d.verdict || ""));
      box.appendChild(row);
      box.appendChild(el("p", "ac-pubtag " + (d.publishable ? "ok" : "no"), d.publishable ? "An editor could run this with light edits." : "Not ready to publish yet. Revise and re-check."));
      if (d.strengths && d.strengths.length) box.appendChild(fbList("What worked", d.strengths));
      if (d.improvements && d.improvements.length) box.appendChild(fbList("Sharpen this", d.improvements));
      var s = d.sections || {};
      var notes = [["Headline", s.headline], ["Summary", s.summary], ["Article", s.body], ["Bio", s.bio]].filter(function (x) { return x[1]; });
      if (notes.length) {
        var sec = el("div", "ac-fb"); sec.appendChild(el("h3", null, "Section by section"));
        var ul = el("ul"); notes.forEach(function (x) { var li = el("li"); li.appendChild(el("b", null, x[0] + ": ")); li.appendChild(document.createTextNode(x[1])); ul.appendChild(li); }); sec.appendChild(ul);
        box.appendChild(sec);
      }
      return box;
    }
    function selfCheckBox() {
      var box = el("div", "ac-result");
      box.appendChild(el("h3", "ac-selfhead", "Mark your own work before submitting"));
      var ul = el("div", "ac-checklist");
      ["Does the headline say what actually happened, accurately?",
       "Does the article lead with the news, not background or spin?",
       "Is every claim attributed to a source, and every figure checked?",
       "Have you sought more than one voice, and added context?",
       "Is it clean, plain English with no em dashes?"].forEach(function (q) {
        var lab = el("label", "ac-check"); var cb = document.createElement("input"); cb.type = "checkbox";
        cb.addEventListener("change", function () { if (cb.checked) Sound.play("tap"); });
        lab.appendChild(cb); lab.appendChild(el("span", null, q)); ul.appendChild(lab);
      });
      box.appendChild(ul);
      return box;
    }
    function fbList(title, items) { var w = el("div", "ac-fb"); w.appendChild(el("h3", null, title)); var ul = el("ul"); items.forEach(function (t) { ul.appendChild(el("li", null, t)); }); w.appendChild(ul); return w; }

    window.scrollTo(0, 0);
  }

  // ---------- router ----------
  function route() { var h = location.hash || "#/"; if (h.indexOf("#/read") === 0) return renderReading(); if (h.indexOf("#/cv") === 0) return renderCV(); if (h.indexOf("#/submit") === 0) return renderSubmission(); if (h.indexOf("#/certificate") === 0) return renderCertificate(); var m = h.match(/^#\/lesson\/(.+)$/); if (m) renderLesson(decodeURIComponent(m[1])); else renderHome(); }
  window.addEventListener("hashchange", route);
  route();
  pullProgress();
})();
