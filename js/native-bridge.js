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
