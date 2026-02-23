/**
 * Email gate — friends & family beta wall.
 * Shows content for 3 seconds, then blurs it and slides in the gate.
 * Header stays visible above the overlay.
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
      '<h1 class="gate-logo">THE MUTAPA TIMES</h1>' +
      '<p class="gate-tagline">Zimbabwe outside-in.</p>' +
      '<hr class="gate-rule">' +
      '<h2 class="gate-headline">Coming Soon</h2>' +
      '<p class="gate-copy">' +
        'I\u2019m building Zimbabwe\u2019s sharpest news briefing \u2014 curated headlines ' +
        'from the world\u2019s most trusted newsrooms, original reporting, and market intelligence, all in one place.' +
      '</p>' +
      '<ul class="gate-perks">' +
        '<li>Curated Zimbabwe news from BBC, Reuters, Bloomberg &amp; more</li>' +
        '<li>Original articles &amp; exclusive analysis</li>' +
        '<li>Live economic data &amp; market indicators</li>' +
        '<li>Notable Zimbabwean leaders &amp; executives directory</li>' +
      '</ul>' +
      '<p class="gate-cta-label">Enter your email to get early access:</p>' +
      '<form class="gate-form" id="gate-form">' +
        '<input type="email" class="gate-input" id="gate-email" placeholder="you@example.com" required autocomplete="email" aria-label="Email address">' +
        '<button type="submit" class="gate-btn">Get Early Access</button>' +
      '</form>' +
      '<p class="gate-fine">Currently testing with friends &amp; family. No spam \u2014 just news that matters.</p>' +
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
