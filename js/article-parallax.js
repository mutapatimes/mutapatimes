/*
 * Article full-bleed parallax — drives the vertical translate on any
 * .article-fullbleed-media inside a .article-fullbleed-frame, as a
 * function of the frame's position in the viewport. rAF-throttled.
 * Bails out for prefers-reduced-motion users (CSS handles the static
 * fallback).
 */
(function () {
  'use strict';

  var reduceMotion = window.matchMedia &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (reduceMotion) return;

  var frames = [].slice.call(
    document.querySelectorAll('.article-fullbleed-frame')
  );
  if (!frames.length) return;

  // Cache references and the parallax magnitude (px of travel).
  var items = frames.map(function (frame) {
    var media = frame.querySelector('.article-fullbleed-media');
    return { frame: frame, media: media, travel: 80 };  // ±80px
  });

  var ticking = false;
  function onScroll() {
    if (ticking) return;
    ticking = true;
    window.requestAnimationFrame(update);
  }
  function update() {
    var vh = window.innerHeight || document.documentElement.clientHeight;
    items.forEach(function (it) {
      if (!it.media) return;
      var rect = it.frame.getBoundingClientRect();
      if (rect.bottom < 0 || rect.top > vh) return;  // off-screen
      // progress 0 when frame's top is at the bottom of the viewport,
      // 1 when frame's bottom is at the top. Maps to [-travel, +travel].
      var progress = (vh - rect.top) / (vh + rect.height);
      progress = Math.max(0, Math.min(1, progress));
      var y = (progress - 0.5) * 2 * it.travel;  // -travel..+travel
      it.media.style.transform = 'translate3d(0, ' + y.toFixed(1) + 'px, 0)';
    });
    ticking = false;
  }

  window.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('resize', onScroll, { passive: true });
  // Kick once on load so already-visible frames get the right offset.
  update();
})();
