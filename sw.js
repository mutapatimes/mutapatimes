/*
 * The Mutapa Times — Service Worker
 * Bump CACHE_VERSION on every deploy that changes cached files.
 */
var CACHE_VERSION = 'mutapa-v3';
var DATA_CACHE   = 'mutapa-data-v1';
var IMG_CACHE    = 'mutapa-img-v1';

var APP_SHELL = [
  '/',
  '/index.html',
  '/article.html',
  '/articles.html',
  '/economy.html',
  '/people.html',
  '/person.html',
  '/businesses.html',
  '/business.html',
  '/who.html',
  '/what.html',
  '/why.html',
  '/how.html',
  '/terms.html',
  '/offline.html',
  '/css/normalize.css',
  '/css/main.css',
  '/js/vendor/modernizr-3.8.0.min.js',
  '/js/plugins.js',
  '/js/config.js',
  '/js/main.js',
  '/js/gate.js',
  '/js/articles.js',
  '/js/person.js',
  '/js/business.js',
  '/js/businesses.js',
  '/js/people.js',
  '/site.webmanifest',
  '/img/android-icon-192x192.png',
  '/img/favicon-32x32.png',
  '/img/favicon-96x96.png'
];

var EXTERNAL_NETWORK_ONLY = [
  'googletagmanager.com',
  'google-analytics.com',
  'contentsquare.net',
  'api.rss2json.com',
  'api.open-meteo.com',
  's3.tradingview.com',
  'query.wikidata.org',
  'translate.google.com'
];

// Install — pre-cache app shell
self.addEventListener('install', function(event) {
  event.waitUntil(
    caches.open(CACHE_VERSION).then(function(cache) {
      return cache.addAll(APP_SHELL);
    }).then(function() {
      return self.skipWaiting();
    })
  );
});

// Activate — clean old caches
self.addEventListener('activate', function(event) {
  var keep = [CACHE_VERSION, DATA_CACHE, IMG_CACHE];
  event.waitUntil(
    caches.keys().then(function(names) {
      return Promise.all(
        names.filter(function(n) { return keep.indexOf(n) === -1; })
             .map(function(n) { return caches.delete(n); })
      );
    }).then(function() {
      return self.clients.claim();
    })
  );
});

// Fetch — tiered routing
self.addEventListener('fetch', function(event) {
  var url = new URL(event.request.url);

  // Network Only: analytics & external APIs
  for (var i = 0; i < EXTERNAL_NETWORK_ONLY.length; i++) {
    if (url.hostname.indexOf(EXTERNAL_NETWORK_ONLY[i]) !== -1) {
      return; // let browser handle natively
    }
  }

  // Network First: data JSON files
  if (url.pathname.indexOf('/data/') === 0 && url.pathname.indexOf('.json') !== -1) {
    event.respondWith(networkFirstData(event.request));
    return;
  }

  // Stale While Revalidate: images
  if (url.pathname.indexOf('/img/') === 0 || /\.(png|jpg|jpeg|gif|webp|svg|ico)$/i.test(url.pathname)) {
    event.respondWith(staleWhileRevalidateImg(event.request));
    return;
  }

  // Cache First: app shell (HTML, CSS, JS)
  event.respondWith(cacheFirstShell(event.request));
});

function networkFirstData(request) {
  return fetch(request).then(function(response) {
    if (response && response.ok) {
      var clone = response.clone();
      caches.open(DATA_CACHE).then(function(cache) {
        cache.put(request, clone);
      });
    }
    return response;
  }).catch(function() {
    return caches.match(request);
  });
}

function staleWhileRevalidateImg(request) {
  return caches.open(IMG_CACHE).then(function(cache) {
    return cache.match(request).then(function(cached) {
      var fetched = fetch(request).then(function(response) {
        if (response && response.ok) {
          cache.put(request, response.clone());
          // Evict oldest if cache exceeds 100 entries
          cache.keys().then(function(keys) {
            if (keys.length > 100) cache.delete(keys[0]);
          });
        }
        return response;
      }).catch(function() {
        return cached;
      });
      return cached || fetched;
    });
  });
}

function cacheFirstShell(request) {
  return caches.match(request).then(function(cached) {
    if (cached) return cached;
    return fetch(request).then(function(response) {
      if (response && response.ok) {
        var clone = response.clone();
        caches.open(CACHE_VERSION).then(function(cache) {
          cache.put(request, clone);
        });
      }
      return response;
    });
  }).catch(function() {
    // Offline fallback for navigation requests
    if (request.mode === 'navigate') {
      return caches.match('/offline.html');
    }
  });
}

// Push notification handler
self.addEventListener('push', function(event) {
  var data = {};
  if (event.data) {
    try { data = event.data.json(); } catch (e) { data = { title: event.data.text() }; }
  }
  var title = (data.notification && data.notification.title) || data.title || 'The Mutapa Times';
  var options = {
    body: (data.notification && data.notification.body) || data.body || '',
    icon: '/img/android-icon-192x192.png',
    badge: '/img/favicon-96x96.png',
    data: { url: (data.data && data.data.url) || '/' },
    tag: 'mutapa-news',
    renotify: true
  };
  event.waitUntil(self.registration.showNotification(title, options));
});

// Notification click — open article URL
self.addEventListener('notificationclick', function(event) {
  event.notification.close();
  var url = (event.notification.data && event.notification.data.url) || '/';
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then(function(list) {
      for (var i = 0; i < list.length; i++) {
        if (list[i].url.indexOf(url) !== -1 && 'focus' in list[i]) {
          return list[i].focus();
        }
      }
      return clients.openWindow(url);
    })
  );
});
