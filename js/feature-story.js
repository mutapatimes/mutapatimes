/*
 * The Mutapa Times — Feature Story of the Week.
 *
 * Reads /data/feature-story.json (written by scripts/build_feature_story.py)
 * and injects the promoted card into any element with id starting with
 * 'feature-story-slot' on the page. Silent no-op if no active feature.
 */
(function () {
  'use strict';
  var mtUrl = window.mtUrl || function (p) { return p; };

  function esc(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  function fmtDate(iso) {
    if (!iso) return '';
    try {
      var d = new Date(iso);
      if (isNaN(d.getTime())) return '';
      var months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
      return months[d.getMonth()] + ' ' + d.getDate() + ', ' + d.getFullYear();
    } catch (e) { return ''; }
  }

  // Sponsored takeover: full-bleed image card with the partner named in
  // the eyebrow. Used only on the main homepage slot; compact slots keep
  // the editorial card so article pages never carry the takeover.
  function renderTakeover(feature) {
    var href = feature.url || mtUrl('/articles/' + feature.slug);
    var partner = feature.partner || '';
    var label = (feature.partner_label || 'In partnership with') + ' ' + partner;
    var cat = feature.category ? esc(feature.category).toUpperCase() : '';
    var tag = feature.takeover_tagline ? esc(feature.takeover_tagline) : '';
    var read = feature.read_minutes ? '<span>' + esc(String(feature.read_minutes)) + ' min read</span>' : '';
    var img = feature.image
      ? '<img class="feature-takeover-img" src="' + esc(feature.image) + '" alt="" loading="eager">'
      : '';
    return (
      '<aside class="feature-story-banner feature-story-banner--takeover">' +
        '<div class="feature-takeover-eyebrow">' +
          '<span>' + esc(label) + '</span>' +
          (feature.partner_url ? '<a class="feature-takeover-partner" href="' + esc(feature.partner_url) + '" target="_blank" rel="noopener sponsored">Visit the hotel</a>' : '') +
        '</div>' +
        '<a class="feature-takeover-card" href="' + esc(href) + '">' +
          img +
          '<div class="feature-takeover-shade"></div>' +
          '<div class="feature-takeover-body">' +
            (tag || cat ? '<span class="feature-takeover-tag">' + (tag || cat) + '</span>' : '') +
            '<h2 class="feature-takeover-title">' + esc(feature.title || '') + '</h2>' +
            '<p class="feature-takeover-summary">' + esc((feature.summary || '').slice(0, 220)) + '</p>' +
            '<div class="feature-takeover-meta">' +
              (feature.author ? '<span>' + esc(feature.author) + '</span>' : '') +
              read +
              '<span class="feature-takeover-cta">Read the review</span>' +
            '</div>' +
          '</div>' +
        '</a>' +
      '</aside>'
    );
  }

  function render(feature, opts) {
    opts = opts || {};
    var isCompact = !!opts.compact;
    if (feature.takeover && feature.partner && !isCompact) return renderTakeover(feature);
    var label = opts.label || 'Feature Story of the Week';
    var img = feature.image
      ? '<div class="feature-story-image"><img src="' + esc(feature.image) + '" alt="' + esc(feature.title || '') + '" loading="lazy"></div>'
      : '';
    var cat = feature.category ? esc(feature.category).toUpperCase() : '';
    var longRead = feature.longform ? ' · LONG READ' : '';
    var read = (feature.longform && feature.read_minutes)
      ? '<span>' + esc(String(feature.read_minutes)) + ' min read</span>'
      : '';
    var dateStr = fmtDate(feature.date);
    var href = feature.url || mtUrl('/articles/' + feature.slug);
    return (
      '<aside class="feature-story-banner' + (isCompact ? ' feature-story-banner--compact' : '') + '">' +
        '<div class="feature-story-eyebrow">' + esc(label) + '</div>' +
        '<a class="feature-story-card" href="' + esc(href) + '">' +
          img +
          '<div class="feature-story-body">' +
            (cat ? '<span class="feature-story-category">' + cat + longRead + '</span>' : '') +
            '<h2 class="feature-story-title">' + esc(feature.title || '') + '</h2>' +
            '<p class="feature-story-summary">' + esc((feature.summary || '').slice(0, 260)) + '</p>' +
            '<div class="feature-story-meta">' +
              (feature.author ? '<span><strong>' + esc(feature.author) + '</strong></span>' : '') +
              (dateStr ? '<span>' + dateStr + '</span>' : '') +
              read +
            '</div>' +
          '</div>' +
        '</a>' +
      '</aside>'
    );
  }

  function loadAndRender() {
    var slots = document.querySelectorAll('[id^="feature-story-slot"]');
    if (!slots.length) return;
    var url = mtUrl('/data/feature-story.json');
    var xhr = new XMLHttpRequest();
    xhr.open('GET', url, true);
    xhr.onreadystatechange = function () {
      if (xhr.readyState !== 4) return;
      if (xhr.status < 200 || xhr.status >= 300) return;
      var feature;
      try { feature = JSON.parse(xhr.responseText); } catch (e) { return; }
      if (!feature || !feature.slug) return;
      for (var i = 0; i < slots.length; i++) {
        // Don't show the feature rail on the feature article's own page.
        var current = slots[i].getAttribute('data-current-slug');
        if (current && current === feature.slug) continue;
        var compact = slots[i].id !== 'feature-story-slot';
        var label = compact ? 'This week we recommend' : 'Feature Story of the Week';
        slots[i].innerHTML = render(feature, { compact: compact, label: label });
      }
    };
    xhr.send();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', loadAndRender);
  } else {
    loadAndRender();
  }
})();
