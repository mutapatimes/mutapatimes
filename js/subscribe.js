/**
 * Subscribe page — countdown to next briefing + live preview from spotlight.json.
 *
 * Newsletter cron: Mon & Thu at 07:00 UTC (09:00 CAT).
 * We compute the next fire time in the user's local timezone and tick a live
 * countdown.
 */
(function () {
  // ── Countdown to next Monday or Thursday at 07:00 UTC ──────
  function nextBriefing() {
    var now = new Date();
    var nowMs = now.getTime();
    // Build candidate "next" times in UTC: 07:00 UTC on every Mon (1) and Thu (4)
    // for the next 14 days, pick the earliest one in the future.
    var candidates = [];
    for (var i = 0; i < 14; i++) {
      var d = new Date(Date.UTC(
        now.getUTCFullYear(),
        now.getUTCMonth(),
        now.getUTCDate() + i,
        7, 0, 0
      ));
      var dow = d.getUTCDay();  // 1 = Mon, 4 = Thu
      if ((dow === 1 || dow === 4) && d.getTime() > nowMs) {
        candidates.push(d);
      }
    }
    return candidates[0];
  }

  function pad(n) { return n < 10 ? '0' + n : '' + n; }

  function tickCountdown() {
    var target = nextBriefing();
    var whenEl = document.getElementById('subscribeCountdownWhen');
    var dEl = document.getElementById('cdDays');
    var hEl = document.getElementById('cdHours');
    var mEl = document.getElementById('cdMins');
    var sEl = document.getElementById('cdSecs');
    if (!target || !dEl || !hEl || !mEl || !sEl) return;

    if (whenEl) {
      var dayName = target.toLocaleDateString(undefined, { weekday: 'long' });
      var local = target.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' });
      whenEl.textContent = dayName + ' at ' + local + ' your time';
    }

    function update() {
      var diff = target.getTime() - Date.now();
      if (diff <= 0) {
        dEl.textContent = '0';
        hEl.textContent = '0';
        mEl.textContent = '00';
        sEl.textContent = '00';
        // Re-evaluate: the next briefing has just fired.
        target = nextBriefing();
        return;
      }
      var days = Math.floor(diff / 86400000);
      var hours = Math.floor((diff % 86400000) / 3600000);
      var mins = Math.floor((diff % 3600000) / 60000);
      var secs = Math.floor((diff % 60000) / 1000);
      dEl.textContent = days;
      hEl.textContent = hours;
      mEl.textContent = pad(mins);
      sEl.textContent = pad(secs);
    }
    update();
    setInterval(update, 1000);
  }

  // ── Live preview of latest spotlight + category headlines ──
  function escapeHtml(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;')
      .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  function renderPreviewItems(articles) {
    var list = document.getElementById('subscribePreviewList');
    if (!list) return;
    if (!articles || !articles.length) {
      list.innerHTML = '<p class="subscribe-preview-empty">No preview available right now.</p>';
      return;
    }
    list.innerHTML = articles.slice(0, 6).map(function (a, i) {
      var title = escapeHtml(a.title || '');
      var src = a.source;
      if (src && typeof src === 'object') src = src.name;
      src = escapeHtml(src || '');
      var img = a.image
        ? '<div class="subscribe-preview-img" style="background-image:url(\'' + escapeHtml(a.image) + '\')"></div>'
        : '<div class="subscribe-preview-img"></div>';
      return (
        '<div class="subscribe-preview-card">' +
          img +
          '<div class="subscribe-preview-body">' +
            '<p class="subscribe-preview-num">No. ' + pad(i + 1) + '</p>' +
            '<h4 class="subscribe-preview-h">' + title + '</h4>' +
            (src ? '<p class="subscribe-preview-src">' + src + '</p>' : '') +
          '</div>' +
        '</div>'
      );
    }).join('');
  }

  function loadPreview() {
    fetch('data/spotlight.json', { cache: 'no-cache' })
      .then(function (r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
      .then(function (d) {
        var arts = (d.articles || []).concat(d.more || []);
        renderPreviewItems(arts);
      })
      .catch(function (err) {
        var list = document.getElementById('subscribePreviewList');
        if (list) list.innerHTML = '<p class="subscribe-preview-empty">Preview temporarily unavailable.</p>';
        if (window.console) console.warn('Preview load failed', err);
      });
  }

  // ── Form success feedback ──────────────────────────────────
  function bindFormFeedback() {
    var forms = document.querySelectorAll('.subscribe-form');
    forms.forEach(function (form) {
      form.addEventListener('submit', function () {
        // Show inline success after a short delay (form posts to hidden iframe)
        setTimeout(function () {
          var btn = form.querySelector('.subscribe-form-btn');
          if (btn) {
            btn.textContent = '✓ Subscribed';
            btn.disabled = true;
          }
          var input = form.querySelector('.subscribe-form-input');
          if (input) input.value = '';
        }, 600);
      });
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () {
      tickCountdown();
      loadPreview();
      bindFormFeedback();
    });
  } else {
    tickCountdown();
    loadPreview();
    bindFormFeedback();
  }
})();
