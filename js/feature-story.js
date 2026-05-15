/*
 * The Mutapa Times — Feature Story of the Week.
 *
 * Reads /data/feature-story.json (written by scripts/build_feature_story.py)
 * and injects the promoted card into any element with id starting with
 * 'feature-story-slot' on the page. Silent no-op if no active feature.
 */
(function () {
  'use strict';

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

  function render(feature, opts) {
    opts = opts || {};
    var isCompact = !!opts.compact;
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
    var href = feature.url || ('/articles/' + feature.slug);
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
    var url = '/data/feature-story.json';
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
