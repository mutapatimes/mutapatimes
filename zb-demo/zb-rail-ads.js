/* Inject ZB-branded story-rail chips into the demo's stories rail.
 * Waits for /js/stories.js to populate the rail, then prepends three
 * ad chips that mimic the structure of native .story-thumb elements
 * so they style identically — but tag each with an "AD" badge so
 * they're clearly labelled.
 *
 * Clicking an ad chip opens the ZB Diaspora Hub in a new tab. We do
 * not hook into the in-page story viewer because ad-as-viewer would
 * conflate sponsored content with editorial slides. */
(function () {
  'use strict';

  var ADS = [
    {
      label: 'Diaspora Account',
      image: '/img/uploads/zb_bank_demo_site/DIASPORA_CURRENT_ACCOUNT.png',
      url: 'https://www.zb.co.zw/diaspora-hub'
    },
    {
      label: 'Build at home',
      image: '/img/uploads/zb_bank_demo_site/Homebuilding_zb_bank.png',
      url: 'https://www.zb.co.zw/diaspora-hub'
    },
    {
      label: 'Funeral Cover',
      image: '/img/uploads/zb_bank_demo_site/FUNERAL_ZB_BANK.png',
      url: 'https://www.zb.co.zw/diaspora-hub'
    }
  ];

  function chip(ad) {
    var a = document.createElement('a');
    a.className = 'story-thumb is-unviewed zb-rail-ad';
    a.href = ad.url;
    a.target = '_blank';
    a.rel = 'noopener sponsored';
    a.setAttribute('aria-label', 'Advertisement: ' + ad.label);
    a.innerHTML =
      '<span class="story-chip-glow">' +
        '<span class="story-chip" style="background-image:url(\'' + ad.image + '\')">' +
          '<span class="story-chip-label">' + ad.label + '</span>' +
        '</span>' +
      '</span>';
    return a;
  }

  function injectIfReady() {
    var inner = document.querySelector('#stories-rail .stories-rail-inner');
    if (!inner) return false;
    if (inner.querySelector('.zb-rail-ad')) return true;
    var frag = document.createDocumentFragment();
    ADS.forEach(function (ad) { frag.appendChild(chip(ad)); });
    inner.insertBefore(frag, inner.firstChild);
    return true;
  }

  function watchAndInject() {
    if (injectIfReady()) return;
    // Stories rail is built async after fetching content/articles/index.json;
    // retry until it shows up, then stop.
    var tries = 0;
    var t = setInterval(function () {
      if (injectIfReady() || ++tries > 40) clearInterval(t);
    }, 250);
    // Also watch for mutations — covers the case where stories.js rebuilds.
    var rail = document.getElementById('stories-rail');
    if (rail && window.MutationObserver) {
      new MutationObserver(function () { injectIfReady(); })
        .observe(rail, { childList: true, subtree: true });
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', watchAndInject);
  } else {
    watchAndInject();
  }
})();
