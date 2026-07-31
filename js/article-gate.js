/*
 * Article subscriber gate.
 *
 * Opt-in per article: build_static_pages adds data-paywall="1" (and an
 * optional data-paywall-at="20" scroll trigger percentage) to the
 * <article> element when frontmatter sets `paywall: true`.
 *
 * Behaviour: once the reader scrolls past the trigger point, the whole
 * page is frosted (backdrop blur) and a "Subscriber exclusive — subscribe
 * to continue" card takes over, locking scroll. Submitting the email
 * (Brevo, same list as the rest of the site) unlocks the article and
 * remembers the reader via localStorage so they are never gated again.
 */
(function () {
  "use strict";

  var art = document.querySelector('article[data-paywall="1"]');
  if (!art) return;

  var KEY = "mt_sub_unlocked";
  try { if (localStorage.getItem(KEY) === "1") return; } catch (e) {}

  // Brevo hosted form endpoint — same list used across the site.
  var BREVO = "https://e8bb9c12.sibforms.com/serve/MUIFANhyo5KAv45zGQtXk46aajtYgiqbLYvK0dXstXNkrCWwsrDeJG7IjtjBOM4LZfCQpFxjgq1NguOQm0ZMtALVI-9f2BYGEwxlGoGnDBiTqyPNvC7vR6D1lPLC4UWJqvOevKNHiUd0f5-o093A3UQ7iNImM7AC4as67y6Jo4WrQKPW8qEiHVivLeAnaT1wNM2xeUW1a6EmaLlvJg==";

  var atPct = (parseFloat(art.getAttribute("data-paywall-at") || "20") || 20) / 100;
  var triggered = false;

  function injectStyle() {
    if (document.getElementById("mt-gate-style")) return;
    var s = document.createElement("style");
    s.id = "mt-gate-style";
    s.textContent = [
      "html.mt-gated, body.mt-gated { overflow: hidden !important; }",
      ".mt-gate { position: fixed; inset: 0; z-index: 100000; display: flex;",
      "  align-items: center; justify-content: center; padding: 24px;",
      "  background: rgba(12,20,16,0.45);",
      "  -webkit-backdrop-filter: blur(11px); backdrop-filter: blur(11px);",
      "  animation: mtGateIn .25s ease; }",
      "@keyframes mtGateIn { from { opacity: 0; } to { opacity: 1; } }",
      ".mt-gate-card { width: 100%; max-width: 440px; background: var(--paper, #fafaf7);",
      "  color: var(--ink, #1a1a1a); border-radius: 14px; padding: 34px 30px 30px;",
      "  box-shadow: 0 24px 70px rgba(0,0,0,.4); text-align: left;",
      "  font-family: 'Inter', system-ui, sans-serif; border: 1px solid rgba(0,0,0,.08); }",
      ".mt-gate-eyebrow { font-size: .68rem; font-weight: 800; letter-spacing: .14em;",
      "  text-transform: uppercase; color: var(--accent, #c41e1e); margin: 0 0 12px; }",
      ".mt-gate-title { font-family: 'Playfair Display', Georgia, serif; font-weight: 800;",
      "  font-size: 1.7rem; line-height: 1.12; margin: 0 0 10px; color: var(--ink, #1a1a1a); }",
      ".mt-gate-copy { font-size: .95rem; line-height: 1.55; margin: 0 0 18px; opacity: .82; }",
      ".mt-gate-form { display: flex; flex-direction: column; gap: 10px; }",
      ".mt-gate-input { width: 100%; box-sizing: border-box; padding: 13px 14px; font-size: 1rem;",
      "  border: 1px solid rgba(0,0,0,.25); border-radius: 8px; background: #fff; color: #1a1a1a;",
      "  font-family: inherit; }",
      ".mt-gate-btn { width: 100%; padding: 13px 16px; font-size: 1rem; font-weight: 700;",
      "  color: #fff; background: var(--accent, #c41e1e); border: 0; border-radius: 8px;",
      "  cursor: pointer; font-family: inherit; letter-spacing: .01em; }",
      ".mt-gate-btn:hover { filter: brightness(1.06); }",
      ".mt-gate-fine { font-size: .72rem; opacity: .68; margin: 14px 0 0; line-height: 1.5; }",
      ".mt-gate-fine a { color: var(--accent, #c41e1e); text-decoration: underline; text-underline-offset: 2px; }",
      "@media (prefers-color-scheme: dark) { .mt-gate-card { border-color: rgba(255,255,255,.12); }",
      "  .mt-gate-input { background: #14201a; color: #f4ede0; border-color: rgba(255,255,255,.2); } }"
    ].join("\n");
    document.head.appendChild(s);
  }

  function unlock() {
    document.documentElement.classList.remove("mt-gated");
    document.body.classList.remove("mt-gated");
    var ov = document.querySelector(".mt-gate");
    if (ov) ov.parentNode.removeChild(ov);
    window.removeEventListener("scroll", onScroll);
  }

  function buildOverlay() {
    var ov = document.createElement("div");
    ov.className = "mt-gate";
    ov.setAttribute("role", "dialog");
    ov.setAttribute("aria-modal", "true");
    ov.setAttribute("aria-label", "Subscribe to continue reading");
    ov.innerHTML =
      '<div class="mt-gate-card">' +
        '<p class="mt-gate-eyebrow">Subscriber exclusive</p>' +
        '<h2 class="mt-gate-title">Subscribe to continue reading</h2>' +
        '<p class="mt-gate-copy">This interview is a Mutapa Times subscriber exclusive. ' +
          'Enter your email to keep reading, free.</p>' +
        '<form class="mt-gate-form" method="POST" action="' + BREVO + '" target="mt-gate-frame">' +
          '<input class="mt-gate-input" type="email" name="EMAIL" required ' +
            'autocomplete="email" placeholder="you@example.com" aria-label="Email address">' +
          '<button class="mt-gate-btn" type="submit">Subscribe &amp; continue reading</button>' +
        '</form>' +
        '<p class="mt-gate-fine">Free forever. Unsubscribe anytime. We handle your email in line with our ' +
          '<a href="/privacy" target="_blank" rel="noopener">Privacy Policy</a>.</p>' +
        '<iframe name="mt-gate-frame" title="Subscription confirmation" style="display:none" aria-hidden="true"></iframe>' +
      '</div>';
    document.body.appendChild(ov);

    var form = ov.querySelector("form");
    form.addEventListener("submit", function () {
      // Brevo posts into the hidden iframe; unlock optimistically and
      // remember the reader so the gate never returns.
      try { localStorage.setItem(KEY, "1"); } catch (e) {}
      setTimeout(unlock, 700);
    });
    setTimeout(function () {
      var inp = ov.querySelector(".mt-gate-input");
      if (inp) inp.focus();
    }, 60);
  }

  function gate() {
    if (triggered) return;
    triggered = true;
    injectStyle();
    document.documentElement.classList.add("mt-gated");
    document.body.classList.add("mt-gated");
    buildOverlay();
  }

  function onScroll() {
    var st = window.pageYOffset || document.documentElement.scrollTop || 0;
    var docH = (document.documentElement.scrollHeight || 0) - window.innerHeight;
    if (docH <= 0) return;
    if (st / docH >= atPct) gate();
  }

  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();
})();
