/*
 * The Mutapa Times — Push Notification Subscription
 * Non-intrusive opt-in for breaking Zimbabwe news alerts.
 * Requires Firebase project config to be set below.
 */
(function() {
  'use strict';

  // Firebase config — replace with your actual project values
  var FIREBASE_CONFIG = {
    apiKey: '',
    authDomain: '',
    projectId: '',
    messagingSenderId: '',
    appId: ''
  };

  // VAPID public key from Firebase Cloud Messaging settings
  var VAPID_KEY = '';

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

  function shouldShow() {
    if (!('serviceWorker' in navigator)) return false;
    if (!('Notification' in window)) return false;
    if (Notification.permission === 'denied') return false;
    if (Notification.permission === 'granted' && isAlreadySubscribed()) return false;
    if (isAlreadySubscribed()) return false;
    if (wasDismissedRecently()) return false;
    if (!isConfigured()) return false;
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
        initFirebase(banner);
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
    messaging.getToken({ vapidKey: VAPID_KEY }).then(function(token) {
      if (token) {
        localStorage.setItem(SUBSCRIBED_KEY, '1');
        localStorage.setItem('mutapa_fcm_token', token);
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

    // Show after delay OR after scrolling past threshold
    var timer = setTimeout(showOnce, SHOW_DELAY_MS);

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
