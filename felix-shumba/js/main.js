/* ============================================================
   Felix Shumba — Portfolio JavaScript
   Lightbox, gallery filtering, mobile navigation
   ============================================================ */

(function () {
  'use strict';

  // --- Mobile Navigation ---
  var toggle = document.querySelector('.fs-nav-toggle');
  var header = document.querySelector('.fs-header');

  if (toggle && header) {
    toggle.addEventListener('click', function () {
      var isOpen = header.classList.toggle('fs-nav-open');
      toggle.setAttribute('aria-expanded', isOpen);
    });

    // Close on link click
    var overlayLinks = header.querySelectorAll('.fs-mobile-overlay a');
    overlayLinks.forEach(function (link) {
      link.addEventListener('click', function () {
        header.classList.remove('fs-nav-open');
        toggle.setAttribute('aria-expanded', 'false');
      });
    });
  }

  // --- Gallery Filtering ---
  var filterButtons = document.querySelectorAll('.fs-filter-btn');
  var workItems = document.querySelectorAll('.fs-work-item');

  filterButtons.forEach(function (btn) {
    btn.addEventListener('click', function () {
      var filter = btn.getAttribute('data-filter');

      // Update active button
      filterButtons.forEach(function (b) { b.classList.remove('fs-filter-active'); });
      btn.classList.add('fs-filter-active');

      // Show/hide items
      workItems.forEach(function (item) {
        if (filter === 'all' || item.getAttribute('data-medium') === filter) {
          item.classList.remove('fs-hidden');
        } else {
          item.classList.add('fs-hidden');
        }
      });
    });
  });

  // --- Lightbox ---
  var lightbox = document.getElementById('lightbox');
  if (!lightbox) return;

  var lightboxImg = lightbox.querySelector('.fs-lightbox-img');
  var lightboxTitle = lightbox.querySelector('.fs-lightbox-title');
  var lightboxDetails = lightbox.querySelector('.fs-lightbox-details');
  var closeBtn = lightbox.querySelector('.fs-lightbox-close');
  var prevBtn = lightbox.querySelector('.fs-lightbox-prev');
  var nextBtn = lightbox.querySelector('.fs-lightbox-next');

  var workLinks = document.querySelectorAll('.fs-work-link');
  var currentIndex = 0;

  function getVisibleLinks() {
    return Array.from(document.querySelectorAll('.fs-work-item:not(.fs-hidden) .fs-work-link'));
  }

  function openLightbox(index) {
    var visible = getVisibleLinks();
    if (index < 0 || index >= visible.length) return;

    currentIndex = index;
    var link = visible[index];
    var img = link.querySelector('img');

    lightboxImg.src = img.src;
    lightboxImg.alt = img.alt;
    lightboxTitle.textContent = link.getAttribute('data-title');

    var year = link.getAttribute('data-year');
    var medium = link.getAttribute('data-medium-text');
    var dims = link.getAttribute('data-dimensions');
    lightboxDetails.textContent = year + ', ' + medium + ', ' + dims;

    lightbox.classList.add('fs-lightbox-open');
    document.body.style.overflow = 'hidden';
    closeBtn.focus();
  }

  function closeLightbox() {
    lightbox.classList.remove('fs-lightbox-open');
    document.body.style.overflow = '';
  }

  function showPrev() {
    var visible = getVisibleLinks();
    currentIndex = (currentIndex - 1 + visible.length) % visible.length;
    openLightbox(currentIndex);
  }

  function showNext() {
    var visible = getVisibleLinks();
    currentIndex = (currentIndex + 1) % visible.length;
    openLightbox(currentIndex);
  }

  // Bind click on each work link
  workLinks.forEach(function (link) {
    link.addEventListener('click', function (e) {
      e.preventDefault();
      var visible = getVisibleLinks();
      var idx = visible.indexOf(link);
      if (idx !== -1) openLightbox(idx);
    });
  });

  // Close button
  closeBtn.addEventListener('click', closeLightbox);

  // Click outside image to close
  lightbox.addEventListener('click', function (e) {
    if (e.target === lightbox) closeLightbox();
  });

  // Navigation arrows
  prevBtn.addEventListener('click', function (e) {
    e.stopPropagation();
    showPrev();
  });

  nextBtn.addEventListener('click', function (e) {
    e.stopPropagation();
    showNext();
  });

  // Keyboard controls
  document.addEventListener('keydown', function (e) {
    if (!lightbox.classList.contains('fs-lightbox-open')) return;

    if (e.key === 'Escape') closeLightbox();
    if (e.key === 'ArrowLeft') showPrev();
    if (e.key === 'ArrowRight') showNext();
  });

  // Close mobile nav on Escape
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && header && header.classList.contains('fs-nav-open')) {
      header.classList.remove('fs-nav-open');
      toggle.setAttribute('aria-expanded', 'false');
    }
  });
})();
