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

  // Push notifications (breaking-news alerts). Token goes to your push backend.
  try {
    var PN = P.PushNotifications;
    if (PN) {
      PN.requestPermissions().then(function (res) {
        if (res && res.receive === "granted") PN.register();
      });
      PN.addListener("registration", function (token) {
        // TODO: POST token.value to the push backend to enable targeted alerts.
        try { console.log("[push] APNs token", token && token.value); } catch (e) {}
      });
      PN.addListener("pushNotificationActionPerformed", function (action) {
        var data = action && action.notification && action.notification.data;
        if (data && data.url) window.location.href = data.url; // deep-link into the article
      });
    }
  } catch (e) {}
})();
