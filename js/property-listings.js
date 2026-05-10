/**
 * Live property listings — renders data/property-listings.json
 * (scraped from property.co.zw every 6h by GitHub Actions).
 */
(function () {
  var DATA_URL = 'data/property-listings.json';
  var DISPLAY_COUNT = 12;
  var grid = document.getElementById('listingsGrid');
  var meta = document.getElementById('listingsMeta');
  if (!grid) return;

  function escapeHtml(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function relativeAge(iso) {
    if (!iso) return '';
    var then = new Date(iso).getTime();
    if (isNaN(then)) return '';
    var diffMin = Math.round((Date.now() - then) / 60000);
    if (diffMin < 1) return 'updated just now';
    if (diffMin < 60) return 'updated ' + diffMin + ' min ago';
    var diffHr = Math.round(diffMin / 60);
    if (diffHr < 24) return 'updated ' + diffHr + ' hr ago';
    var diffDay = Math.round(diffHr / 24);
    return 'updated ' + diffDay + ' day' + (diffDay === 1 ? '' : 's') + ' ago';
  }

  function renderCard(l) {
    var amenities = '';
    if (l.beds) amenities += '<span>' + escapeHtml(l.beds) + ' bed</span>';
    if (l.baths) amenities += '<span>' + escapeHtml(l.baths) + ' bath</span>';

    var img = l.image
      ? '<div class="prop-listing-image" style="background-image:url(\'' +
        escapeHtml(l.image) + '\')"></div>'
      : '<div class="prop-listing-image"></div>';

    return (
      '<a class="prop-listing-card" href="' + escapeHtml(l.url) +
      '" target="_blank" rel="noopener">' +
        img +
        '<div class="prop-listing-body">' +
          (l.price ? '<p class="prop-listing-price">' + escapeHtml(l.price) + '</p>' : '') +
          '<p class="prop-listing-title">' + escapeHtml(l.title) + '</p>' +
          (l.location ? '<p class="prop-listing-location">' + escapeHtml(l.location) + '</p>' : '') +
          (amenities ? '<div class="prop-listing-amenities">' + amenities + '</div>' : '') +
        '</div>' +
      '</a>'
    );
  }

  function render(data) {
    var listings = (data && data.listings) || [];
    if (!listings.length) {
      grid.innerHTML = '<p class="prop-listings-error">No listings available right now. Check back soon.</p>';
      return;
    }
    var slice = listings.slice(0, DISPLAY_COUNT);
    grid.innerHTML = slice.map(renderCard).join('');
    if (meta && data.fetched_at) {
      meta.textContent = relativeAge(data.fetched_at);
    }
  }

  fetch(DATA_URL, { cache: 'no-cache' })
    .then(function (r) {
      if (!r.ok) throw new Error('HTTP ' + r.status);
      return r.json();
    })
    .then(render)
    .catch(function (err) {
      grid.innerHTML = '<p class="prop-listings-error">Listings unavailable. <a href="https://www.property.co.zw/houses-for-sale" target="_blank" rel="noopener">View on property.co.zw</a></p>';
      if (window.console) console.warn('Property listings fetch failed:', err);
    });
})();
