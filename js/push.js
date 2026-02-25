/*
 * The Mutapa Times — Push Notification Subscription
 * Non-intrusive opt-in for breaking Zimbabwe news alerts.
 * Requires Firebase project config to be set below.
 */
(function() {
  'use strict';

  var FIREBASE_CONFIG = {
    apiKey: 'AIzaSyBpNRGC_BbDrvSHSwFIX91Pc0sKavUmkTc',
    authDomain: 'mutapa-times.firebaseapp.com',
    projectId: 'mutapa-times',
    storageBucket: 'mutapa-times.firebasestorage.app',
    messagingSenderId: '346417036009',
    appId: '1:346417036009:web:004b77c399f830654a4e78',
    measurementId: 'G-3TVRM7E0GC'
  };

  // VAPID public key from Firebase Cloud Messaging settings
  var VAPID_KEY = 'BH48fgsoLTsqyu-JH2E_oPatyr12f585pf_wtO9xnZccC6Pjt5glObY4V-8WL3eD6Uwvy22P2E2kpwM8hn1OlNg';

  var DISMISS_KEY = 'mutapa_push_dismissed';
  var SUBSCRIBED_KEY = 'mutapa_push_subscribed';
  var DISMISS_DAYS = 30;
  var SHOW_DELAY_MS = 30000; // 30 seconds
  var SCROLL_THRESHOLD = 0.5; // 50% of page

  function isConfigured() {
    return FIREBASE_CONFIG.apiKey && VAPID_KEY;
  }

  function isAlreadySubscribed() {
    return localStorage.getItem(SUBSCRIBED_KEY) === '1';
  }

  function wasDismissedRecently() {
    var ts = parseInt(localStorage.getItem(DISMISS_KEY) || '0', 10);
    if (!ts) return false;
    var elapsed = Date.now() - ts;
    return elapsed < DISMISS_DAYS * 24 * 60 * 60 * 1000;
  }

  // Allow ?push=reset in URL to clear push state and re-show banner
  function checkPushReset() {
    try {
      var params = new URLSearchParams(window.location.search);
      if (params.get('push') === 'reset') {
        localStorage.removeItem(DISMISS_KEY);
        localStorage.removeItem(SUBSCRIBED_KEY);
        localStorage.removeItem('mutapa_fcm_token');
        return true;
      }
    } catch (e) {}
    return false;
  }

  function shouldShow() {
    if (!('serviceWorker' in navigator)) return false;
    if (!('Notification' in window)) return false;
    if (!isConfigured()) return false;
    var wasReset = checkPushReset();
    if (Notification.permission === 'denied') return false;
    if (!wasReset && Notification.permission === 'granted' && isAlreadySubscribed()) return false;
    if (!wasReset && isAlreadySubscribed()) return false;
    if (!wasReset && wasDismissedRecently()) return false;
    return true;
  }

  function createBanner() {
    var banner = document.createElement('div');
    banner.className = 'push-banner';
    banner.id = 'pushBanner';
    banner.innerHTML =
      '<p class="push-banner-text">Get breaking Zimbabwe news alerts?</p>' +
      '<div class="push-banner-actions">' +
        '<button class="push-banner-btn push-banner-enable" id="pushEnable">Enable</button>' +
        '<button class="push-banner-btn push-banner-dismiss" id="pushDismiss">Not now</button>' +
      '</div>';
    document.body.appendChild(banner);

    document.getElementById('pushDismiss').addEventListener('click', function() {
      localStorage.setItem(DISMISS_KEY, String(Date.now()));
      banner.classList.add('push-banner-hidden');
      setTimeout(function() { banner.remove(); }, 400);
    });

    document.getElementById('pushEnable').addEventListener('click', function() {
      subscribe(banner);
    });

    // Trigger entrance animation
    requestAnimationFrame(function() {
      banner.classList.add('push-banner-visible');
    });
  }

  function subscribe(banner) {
    Notification.requestPermission().then(function(permission) {
      if (permission !== 'granted') {
        banner.classList.add('push-banner-hidden');
        setTimeout(function() { banner.remove(); }, 400);
        return;
      }
      loadFirebaseAndSubscribe(banner);
    });
  }

  function loadFirebaseAndSubscribe(banner) {
    // Load Firebase SDKs dynamically
    var appScript = document.createElement('script');
    appScript.src = 'https://www.gstatic.com/firebasejs/10.14.0/firebase-app-compat.js';
    appScript.onload = function() {
      var msgScript = document.createElement('script');
      msgScript.src = 'https://www.gstatic.com/firebasejs/10.14.0/firebase-messaging-compat.js';
      msgScript.onload = function() {
        var fsScript = document.createElement('script');
        fsScript.src = 'https://www.gstatic.com/firebasejs/10.14.0/firebase-firestore-compat.js';
        fsScript.onload = function() {
          initFirebase(banner);
        };
        document.head.appendChild(fsScript);
      };
      document.head.appendChild(msgScript);
    };
    document.head.appendChild(appScript);
  }

  function initFirebase(banner) {
    if (!firebase.apps.length) {
      firebase.initializeApp(FIREBASE_CONFIG);
    }
    var messaging = firebase.messaging();
    var db = firebase.firestore();
    messaging.getToken({ vapidKey: VAPID_KEY }).then(function(token) {
      if (token) {
        localStorage.setItem(SUBSCRIBED_KEY, '1');
        localStorage.setItem('mutapa_fcm_token', token);
        // Save token to Firestore for server-side push delivery
        db.collection('push_tokens').doc(token).set({
          token: token,
          created: firebase.firestore.FieldValue.serverTimestamp()
        }).catch(function(e) {
          console.warn('Failed to save push token:', e);
        });
        // Update banner to success state
        banner.innerHTML = '<p class="push-banner-text">News alerts enabled!</p>';
        setTimeout(function() {
          banner.classList.add('push-banner-hidden');
          setTimeout(function() { banner.remove(); }, 400);
        }, 2000);
      }
    }).catch(function(err) {
      console.warn('Push subscription failed:', err);
      banner.classList.add('push-banner-hidden');
      setTimeout(function() { banner.remove(); }, 400);
    });
  }

  function init() {
    if (!shouldShow()) return;

    var shown = false;
    function showOnce() {
      if (shown) return;
      shown = true;
      createBanner();
    }

    // Show immediately if reset, otherwise after delay or scroll
    var isReset = window.location.search.indexOf('push=reset') !== -1;
    var timer = setTimeout(showOnce, isReset ? 500 : SHOW_DELAY_MS);

    window.addEventListener('scroll', function onScroll() {
      var scrolled = window.scrollY / (document.body.scrollHeight - window.innerHeight);
      if (scrolled >= SCROLL_THRESHOLD) {
        clearTimeout(timer);
        showOnce();
        window.removeEventListener('scroll', onScroll);
      }
    });
  }

  // Wait for DOM
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
