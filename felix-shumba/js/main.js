/* ============================================================
   Felix Shumba — Portfolio JavaScript
   Slider, lightbox, gallery filtering, mobile navigation,
   contact form
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

    var overlayLinks = header.querySelectorAll('.fs-mobile-overlay a');
    overlayLinks.forEach(function (link) {
      link.addEventListener('click', function () {
        header.classList.remove('fs-nav-open');
        toggle.setAttribute('aria-expanded', 'false');
      });
    });
  }

  // --- Transparent Header Scroll ---
  var transparentHeader = document.querySelector('.fs-header-transparent');
  if (transparentHeader) {
    function onScroll() {
      if (window.scrollY > 80) {
        transparentHeader.classList.add('fs-header-scrolled');
      } else {
        transparentHeader.classList.remove('fs-header-scrolled');
      }
    }
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }

  // --- Hero Slider ---
  var slider = document.querySelector('.fs-slider');
  if (slider) {
    var slides = slider.querySelectorAll('.fs-slide');
    var prevBtn = slider.querySelector('.fs-slider-prev');
    var nextBtn = slider.querySelector('.fs-slider-next');
    var dotsContainer = slider.querySelector('.fs-slider-dots');
    var progressBar = slider.querySelector('.fs-slider-progress-bar');
    var current = 0;
    var total = slides.length;
    var interval = 6000; // 6 seconds per slide
    var timer = null;

    // Create dots
    for (var i = 0; i < total; i++) {
      var dot = document.createElement('button');
      dot.className = 'fs-slider-dot' + (i === 0 ? ' fs-dot-active' : '');
      dot.setAttribute('role', 'tab');
      dot.setAttribute('aria-label', 'Slide ' + (i + 1));
      dot.setAttribute('data-slide', i);
      dotsContainer.appendChild(dot);
    }
    var dots = dotsContainer.querySelectorAll('.fs-slider-dot');

    function goTo(index) {
      slides[current].classList.remove('fs-slide-active');
      dots[current].classList.remove('fs-dot-active');
      current = (index + total) % total;
      slides[current].classList.add('fs-slide-active');
      dots[current].classList.add('fs-dot-active');
      startProgress();
    }

    function startProgress() {
      progressBar.classList.remove('fs-progress-animate');
      progressBar.style.width = '0%';
      // Force reflow
      void progressBar.offsetWidth;
      progressBar.style.transitionDuration = interval + 'ms';
      progressBar.classList.add('fs-progress-animate');
    }

    function startAutoplay() {
      stopAutoplay();
      startProgress();
      timer = setInterval(function () {
        goTo(current + 1);
      }, interval);
    }

    function stopAutoplay() {
      if (timer) clearInterval(timer);
    }

    prevBtn.addEventListener('click', function () {
      goTo(current - 1);
      startAutoplay();
    });

    nextBtn.addEventListener('click', function () {
      goTo(current + 1);
      startAutoplay();
    });

    dots.forEach(function (dot) {
      dot.addEventListener('click', function () {
        goTo(parseInt(dot.getAttribute('data-slide'), 10));
        startAutoplay();
      });
    });

    // Keyboard
    document.addEventListener('keydown', function (e) {
      if (!slider.closest('.fs-main')) return;
      if (document.querySelector('.fs-lightbox-open')) return;
      if (e.key === 'ArrowLeft') { goTo(current - 1); startAutoplay(); }
      if (e.key === 'ArrowRight') { goTo(current + 1); startAutoplay(); }
    });

    // Pause on hover
    slider.addEventListener('mouseenter', stopAutoplay);
    slider.addEventListener('mouseleave', startAutoplay);

    // Start
    startAutoplay();
  }

  // --- Gallery Filtering ---
  var filterButtons = document.querySelectorAll('.fs-filter-btn');
  var workItems = document.querySelectorAll('.fs-work-item');

  filterButtons.forEach(function (btn) {
    btn.addEventListener('click', function () {
      var filter = btn.getAttribute('data-filter');

      filterButtons.forEach(function (b) { b.classList.remove('fs-filter-active'); });
      btn.classList.add('fs-filter-active');

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
  if (lightbox) {
    var lightboxImg = lightbox.querySelector('.fs-lightbox-img');
    var lightboxTitle = lightbox.querySelector('.fs-lightbox-title');
    var lightboxDetails = lightbox.querySelector('.fs-lightbox-details');
    var lbCloseBtn = lightbox.querySelector('.fs-lightbox-close');
    var lbPrevBtn = lightbox.querySelector('.fs-lightbox-prev');
    var lbNextBtn = lightbox.querySelector('.fs-lightbox-next');
    var workLinks = document.querySelectorAll('.fs-work-link');
    var lbIndex = 0;

    function getVisibleLinks() {
      return Array.from(document.querySelectorAll('.fs-work-item:not(.fs-hidden) .fs-work-link'));
    }

    function openLightbox(index) {
      var visible = getVisibleLinks();
      if (index < 0 || index >= visible.length) return;
      lbIndex = index;
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
      lbCloseBtn.focus();
    }

    function closeLightbox() {
      lightbox.classList.remove('fs-lightbox-open');
      document.body.style.overflow = '';
    }

    function lbPrev() {
      var visible = getVisibleLinks();
      lbIndex = (lbIndex - 1 + visible.length) % visible.length;
      openLightbox(lbIndex);
    }

    function lbNext() {
      var visible = getVisibleLinks();
      lbIndex = (lbIndex + 1) % visible.length;
      openLightbox(lbIndex);
    }

    workLinks.forEach(function (link) {
      link.addEventListener('click', function (e) {
        e.preventDefault();
        var visible = getVisibleLinks();
        var idx = visible.indexOf(link);
        if (idx !== -1) openLightbox(idx);
      });
    });

    lbCloseBtn.addEventListener('click', closeLightbox);

    lightbox.addEventListener('click', function (e) {
      if (e.target === lightbox) closeLightbox();
    });

    lbPrevBtn.addEventListener('click', function (e) {
      e.stopPropagation();
      lbPrev();
    });

    lbNextBtn.addEventListener('click', function (e) {
      e.stopPropagation();
      lbNext();
    });

    document.addEventListener('keydown', function (e) {
      if (!lightbox.classList.contains('fs-lightbox-open')) return;
      if (e.key === 'Escape') closeLightbox();
      if (e.key === 'ArrowLeft') lbPrev();
      if (e.key === 'ArrowRight') lbNext();
    });
  }

  // --- Contact Form ---
  var contactForm = document.getElementById('contactForm');
  if (contactForm) {
    var formStatus = document.getElementById('formStatus');

    contactForm.addEventListener('submit', function (e) {
      e.preventDefault();

      var name = contactForm.querySelector('#contact-name');
      var email = contactForm.querySelector('#contact-email');
      var message = contactForm.querySelector('#contact-message');

      // Basic validation
      if (!name.value.trim() || !email.value.trim() || !message.value.trim()) {
        formStatus.textContent = 'Please fill in all required fields.';
        formStatus.className = 'fs-form-status fs-status-error';
        return;
      }

      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value)) {
        formStatus.textContent = 'Please enter a valid email address.';
        formStatus.className = 'fs-form-status fs-status-error';
        return;
      }

      // Simulate submission (replace with real endpoint like Formspree)
      formStatus.textContent = 'Sending...';
      formStatus.className = 'fs-form-status';

      setTimeout(function () {
        formStatus.textContent = 'Thank you for your message. We will be in touch shortly.';
        formStatus.className = 'fs-form-status fs-status-success';
        contactForm.reset();
      }, 800);
    });
  }

  // --- Close mobile nav on Escape (global) ---
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && header && header.classList.contains('fs-nav-open')) {
      header.classList.remove('fs-nav-open');
      toggle.setAttribute('aria-expanded', 'false');
    }
  });
})();
