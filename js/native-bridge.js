/* The Mutapa Times — Capacitor native bridge.
 * Loaded on the live site; only activates inside the iOS/Android app shell.
 * Hides the splash, styles the status bar, and registers push notifications. */
(function () {
  var Cap = window.Capacitor;
  if (!Cap || typeof Cap.isNativePlatform !== "function" || !Cap.isNativePlatform()) return;
  var P = Cap.Plugins || {};

  // Hide the native splash once the page is interactive.
  function hideSplash() { try { P.SplashScreen && P.SplashScreen.hide(); } catch (e) {} }
  if (document.readyState === "complete") hideSplash();
  else window.addEventListener("load", hideSplash);

  // Status bar to match the dark masthead.
  try { P.StatusBar && P.StatusBar.setStyle({ style: "DARK" }); } catch (e) {}

  // The cookie-consent banner's copy is written for the website ("this
  // site") and is baked as static HTML into every page, so it reads wrong
  // inside the app shell. Reword it here instead of hand-editing every page.
  try {
    var consentP = document.querySelector("#cookieConsent p");
    if (consentP) {
      consentP.innerHTML = consentP.innerHTML
        .replace("This site uses cookies", "This app uses cookies")
        .replace("continuing to use this site", "continuing to use this app");
    }
  } catch (e) {}

  // ── Haptics ──────────────────────────────────────────────────────────
  // Light tap feedback on any button/link. Cheap, and it's the difference
  // between the UI *looking* native (CSS-styled to match) and *feeling*
  // native, which a reviewer notices within seconds of tapping around.
  var Haptics = P.Haptics;
  function tapFeedback() {
    if (!Haptics) return;
    try { Haptics.impact({ style: "LIGHT" }); } catch (e) {}
  }
  if (Haptics) {
    document.addEventListener("touchend", function (e) {
      if (e.target.closest && e.target.closest("a, button")) tapFeedback();
    }, { passive: true });
  }

  // ── Native share sheet ───────────────────────────────────────────────
  // The site's primary share affordance is a WhatsApp-only button that
  // opens wa.me in a new tab -- inside the app's WKWebView that's a dead
  // end (no tab to open). Swap it for the real iOS share sheet, which
  // WKWebView supports natively via the Web Share API and which includes
  // WhatsApp as one of several options anyway.
  document.addEventListener("click", function (e) {
    var btn = e.target.closest && e.target.closest(".whatsapp-btn");
    if (!btn || !navigator.share) return;
    e.preventDefault();
    e.stopPropagation();
    tapFeedback();
    var url = btn.getAttribute("data-share-url") || window.location.href;
    var title = btn.getAttribute("data-share-title") || document.title;
    navigator.share({ title: title, url: url }).catch(function () {});
  }, true);

  // ── Push notifications (breaking-news alerts) ───────────────────────────
  // Primary: OneSignal (one service for both APNs + FCM, with a send
  // dashboard). Paste your OneSignal App ID below once the app is created.
  var ONESIGNAL_APP_ID = "51b70688-864b-4290-8b9a-74033eb41296"; // <-- replace with the real App ID

  function deepLink(url) { if (url) window.location.href = url; }

  if (window.OneSignal && ONESIGNAL_APP_ID && ONESIGNAL_APP_ID.indexOf("YOUR_") !== 0) {
    try {
      window.OneSignal.initialize(ONESIGNAL_APP_ID);
      // Ask the OS for permission (shows the native prompt on first launch).
      window.OneSignal.Notifications.requestPermission(true);
      // Tapping a notification with an "url" in its additional data opens it.
      window.OneSignal.Notifications.addEventListener("click", function (e) {
        var d = (e && e.notification && e.notification.additionalData) || {};
        deepLink(d.url);
      });
    } catch (e) { try { console.log("[push] OneSignal init error", e); } catch (_) {} }
  } else {
    // Fallback: the raw Capacitor push plugin (registers with APNs/FCM; you
    // then need your own sender). Used only until OneSignal is configured.
    try {
      var PN = P.PushNotifications;
      if (PN) {
        PN.requestPermissions().then(function (res) {
          if (res && res.receive === "granted") PN.register();
        });
        PN.addListener("registration", function (token) {
          try { console.log("[push] device token", token && token.value); } catch (e) {}
        });
        PN.addListener("pushNotificationActionPerformed", function (action) {
          var data = action && action.notification && action.notification.data;
          deepLink(data && data.url);
        });
      }
    } catch (e) {}
  }
})();
