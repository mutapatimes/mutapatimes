/**
 * Email gate — early access wall.
 * Shows content for 3 seconds, then blurs it and slides in the gate.
 * On mobile: bottom sheet covering 3/4 of screen.
 * On desktop: centered card.
 */
(function () {
  var STORAGE_KEY = "mutapa_gate_email";

  if (localStorage.getItem(STORAGE_KEY)) return; // already admitted

  // Build overlay (hidden initially — fades in after 3s)
  var overlay = document.createElement("div");
  overlay.id = "gate-overlay";
  overlay.style.opacity = "0";
  overlay.style.pointerEvents = "none";
  overlay.innerHTML =
    '<div class="gate-card">' +
      '<div class="gate-badge">Early Access</div>' +
      '<h2 class="gate-headline">Coming Soon</h2>' +
      '<p class="gate-copy">' +
        'Zimbabwe\u2019s sharpest news briefing \u2014 trusted sources, original reporting, and market intelligence in one place.' +
      '</p>' +
      '<form class="gate-form" id="gate-form">' +
        '<input type="email" class="gate-input" id="gate-email" placeholder="you@example.com" required autocomplete="email" aria-label="Email address">' +
        '<button type="submit" class="gate-btn">Get Access</button>' +
      '</form>' +
      '<p class="gate-fine">Currently testing with friends &amp; family.</p>' +
    '</div>';

  document.body.appendChild(overlay);

  // After 3 seconds: blur content, show overlay
  setTimeout(function () {
    document.body.classList.add("gate-active");
    overlay.style.opacity = "1";
    overlay.style.pointerEvents = "";
  }, 3000);

  // Handle submit
  document.getElementById("gate-form").addEventListener("submit", function (e) {
    e.preventDefault();
    var email = document.getElementById("gate-email").value.trim();
    if (!email) return;

    localStorage.setItem(STORAGE_KEY, email);

    // Fade out & unblur
    overlay.style.opacity = "0";
    overlay.style.pointerEvents = "none";
    document.body.classList.remove("gate-active");
    setTimeout(function () {
      overlay.parentNode.removeChild(overlay);
    }, 500);
  });
})();
