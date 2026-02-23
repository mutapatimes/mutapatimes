/**
 * Email gate — early access wall.
 * Shows content for 3 seconds, then blurs it and slides in the gate.
 * Submits email to Brevo via hidden iframe, same as the subscribe banner.
 */
(function () {
  var STORAGE_KEY = "mutapa_gate_email";
  var BREVO_FORM_URL = "https://e8bb9c12.sibforms.com/serve/MUIFANhyo5KAv45zGQtXk46aajtYgiqbLYvK0dXstXNkrCWwsrDeJG7IjtjBOM4LZfCQpFxjgq1NguOQm0ZMtALVI-9f2BYGEwxlGoGnDBiTqyPNvC7vR6D1lPLC4UWJqvOevKNHiUd0f5-o093A3UQ7iNImM7AC4as67y6Jo4WrQKPW8qEiHVivLeAnaT1wNM2xeUW1a6EmaLlvJg==";

  if (localStorage.getItem(STORAGE_KEY)) return; // already admitted

  // Hidden iframe for cross-origin Brevo form submission
  var iframe = document.createElement("iframe");
  iframe.name = "brevo-gate-frame";
  iframe.style.cssText = "display:none;width:0;height:0;border:0;";
  document.body.appendChild(iframe);

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
      '<form class="gate-form" id="gate-form" method="POST" action="' + BREVO_FORM_URL + '" target="brevo-gate-frame">' +
        '<input type="email" class="gate-input" id="gate-email" name="EMAIL" placeholder="you@example.com" required autocomplete="email" aria-label="Email address">' +
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

  // Handle submit — let the form POST to Brevo, then dismiss
  document.getElementById("gate-form").addEventListener("submit", function () {
    var email = document.getElementById("gate-email").value.trim();
    if (!email) return;

    localStorage.setItem(STORAGE_KEY, email);

    // Small delay so the form POST fires before we remove the DOM
    setTimeout(function () {
      overlay.style.opacity = "0";
      overlay.style.pointerEvents = "none";
      document.body.classList.remove("gate-active");
      setTimeout(function () {
        overlay.parentNode.removeChild(overlay);
      }, 500);
    }, 300);
  });
})();
