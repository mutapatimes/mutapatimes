/**
 * Email gate — friends & family beta wall.
 * Stores email in localStorage so returning readers pass through.
 */
(function () {
  var STORAGE_KEY = "mutapa_gate_email";

  if (localStorage.getItem(STORAGE_KEY)) return; // already admitted

  // Block scrolling
  document.documentElement.style.overflow = "hidden";

  // Build overlay
  var overlay = document.createElement("div");
  overlay.id = "gate-overlay";
  overlay.innerHTML =
    '<div class="gate-card">' +
      '<div class="gate-badge">Friends &amp; Family Beta</div>' +
      '<h1 class="gate-logo">THE MUTAPA TIMES</h1>' +
      '<p class="gate-tagline">Zimbabwe outside-in.</p>' +
      '<hr class="gate-rule">' +
      '<h2 class="gate-headline">Coming Soon</h2>' +
      '<p class="gate-copy">' +
        'We\u2019re building Zimbabwe\u2019s sharpest news briefing \u2014 curated headlines from the world\u2019s ' +
        'most trusted newsrooms, original reporting, and market intelligence, delivered in one place.' +
      '</p>' +
      '<ul class="gate-perks">' +
        '<li>Daily briefing of Zimbabwe news from BBC, Reuters, Bloomberg &amp; more</li>' +
        '<li>Original articles &amp; exclusive analysis</li>' +
        '<li>Live economic data &amp; market indicators</li>' +
        '<li>Notable Zimbabwean leaders &amp; executives directory</li>' +
      '</ul>' +
      '<p class="gate-cta-label">Enter your email to get early access:</p>' +
      '<form class="gate-form" id="gate-form">' +
        '<input type="email" class="gate-input" id="gate-email" placeholder="you@example.com" required autocomplete="email" aria-label="Email address">' +
        '<button type="submit" class="gate-btn">Get Early Access</button>' +
      '</form>' +
      '<p class="gate-fine">Invite-only. No spam \u2014 just news that matters.</p>' +
    '</div>';

  document.body.appendChild(overlay);

  // Handle submit
  document.getElementById("gate-form").addEventListener("submit", function (e) {
    e.preventDefault();
    var email = document.getElementById("gate-email").value.trim();
    if (!email) return;

    localStorage.setItem(STORAGE_KEY, email);

    // Fade out
    overlay.style.opacity = "0";
    document.documentElement.style.overflow = "";
    setTimeout(function () {
      overlay.parentNode.removeChild(overlay);
    }, 400);
  });
})();
