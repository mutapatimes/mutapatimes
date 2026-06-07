/*
 * Interactive timeline for longform articles. Enhances any
 * <section class="az-timeline" data-timeline> block: collapsible
 * milestones, scroll-reveal, an active-marker highlight and an accent
 * progress line that fills as you scroll through it. No-ops (and the
 * timeline stays fully readable) if this script never runs.
 */
(function () {
  'use strict';

  var timelines = document.querySelectorAll('[data-timeline]');
  if (!timelines.length) return;

  var REDUCED = window.matchMedia &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  Array.prototype.forEach.call(timelines, function (tl) {
    tl.classList.add('js-on');
    var list = tl.querySelector('.az-tl');
    var items = Array.prototype.slice.call(tl.querySelectorAll('.az-tl-item'));
    if (!list || !items.length) return;

    // Accent progress line that grows to the lowest revealed marker.
    var fill = document.createElement('div');
    fill.className = 'az-tl-fill';
    list.appendChild(fill);

    // Collapse each milestone; clicking toggles it open.
    items.forEach(function (item, i) {
      var card = item.querySelector('.az-tl-card');
      if (!card) return;
      card.setAttribute('aria-expanded', 'false');
      card.addEventListener('click', function () {
        var open = card.getAttribute('aria-expanded') === 'true';
        card.setAttribute('aria-expanded', open ? 'false' : 'true');
      });
    });

    // Open the final milestone by default — it is the payoff.
    var last = items[items.length - 1].querySelector('.az-tl-card');
    if (last) last.setAttribute('aria-expanded', 'true');

    function updateFill() {
      var active = items.filter(function (it) { return it.classList.contains('is-active'); });
      var ref = active.length ? active[active.length - 1] : null;
      if (!ref) { fill.style.height = '0px'; return; }
      var marker = ref.querySelector('.az-tl-marker');
      var listTop = list.getBoundingClientRect().top;
      var mTop = marker.getBoundingClientRect().top;
      fill.style.height = Math.max(0, (mTop - listTop) + 16) + 'px';
    }

    if (REDUCED || !('IntersectionObserver' in window)) {
      items.forEach(function (it) { it.classList.add('is-visible', 'is-active'); });
      updateFill();
      return;
    }

    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) {
          e.target.classList.add('is-visible', 'is-active');
        } else {
          e.target.classList.remove('is-active');
        }
      });
      updateFill();
    }, { rootMargin: '-25% 0px -45% 0px' });
    items.forEach(function (it) { io.observe(it); });
    window.addEventListener('scroll', updateFill, { passive: true });
  });
})();
