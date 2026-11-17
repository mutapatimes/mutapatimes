/*
 * Access-code gate for private preview pages (/preview/*).
 *
 * Keeps a shared link out of casual hands. Not real authentication: the
 * code is in the page. Use it for pre-publication previews sent to a
 * subject or a partner, together with a noindex meta tag.
 *
 * Usage, in the page head or before </body>:
 *   <script defer src="/js/preview-gate.js"
 *           data-password="..." data-title="Private preview"
 *           data-note="Prepared for X by The Mutapa Times."></script>
 */
(function () {
  'use strict';
  var me = document.currentScript;
  if (!me) return;
  var PASSWORD = me.getAttribute('data-password') || '';
  var TITLE = me.getAttribute('data-title') || 'Enter password';
  var NOTE = me.getAttribute('data-note') || '';
  var KEY = 'mtPreviewUnlocked:' + (location.pathname || '');
  if (!PASSWORD) return;

  function unlocked() {
    try { return sessionStorage.getItem(KEY) === '1'; } catch (e) { return false; }
  }
  function remember() {
    try { sessionStorage.setItem(KEY, '1'); } catch (e) {}
  }

  function styles() {
    var s = document.createElement('style');
    s.textContent =
      'html.mt-gated{overflow:hidden}' +
      '#mtGate{position:fixed;inset:0;z-index:99999;background:#fafaf7;display:flex;align-items:center;justify-content:center;padding:24px;font-family:Inter,system-ui,sans-serif}' +
      '#mtGate .g{width:100%;max-width:420px;background:#fff;border:1px solid #d4d4d4;border-radius:6px;padding:36px 32px}' +
      '#mtGate .brand{font-family:"Playfair Display",Georgia,serif;font-size:1.1rem;margin:0 0 22px;color:#121212}' +
      '#mtGate h2{font-family:"Playfair Display",Georgia,serif;font-weight:700;font-size:1.6rem;line-height:1.15;margin:0 0 8px;color:#121212}' +
      '#mtGate p{font-size:0.92rem;line-height:1.5;color:#333;margin:0 0 20px}' +
      '#mtGate input{width:100%;box-sizing:border-box;padding:12px 14px;border:1px solid #d4d4d4;border-radius:4px;font:400 16px/1.2 Inter,system-ui,sans-serif;background:#fff;color:#121212}' +
      '#mtGate input:focus{outline:2px solid #c41e1e;outline-offset:1px}' +
      '#mtGate button{margin-top:10px;width:100%;padding:12px;background:#121212;color:#fff;border:0;border-radius:4px;font:600 15px/1 Inter,system-ui,sans-serif;cursor:pointer}' +
      '#mtGate button:hover{background:#c41e1e}' +
      '#mtGate .err{color:#c41e1e;font-size:0.85rem;min-height:18px;margin:8px 0 0}';
    document.head.appendChild(s);
  }

  function build() {
    styles();
    document.documentElement.classList.add('mt-gated');
    var gate = document.createElement('div');
    gate.id = 'mtGate';
    gate.innerHTML =
      '<div class="g" role="dialog" aria-labelledby="mtGateTitle">' +
        '<h2 id="mtGateTitle"></h2>' +
        (NOTE ? '<p class="note"></p>' : '') +
        '<form autocomplete="off">' +
          '<input type="password" aria-label="Password" placeholder="Password" autofocus>' +
          '<p class="err" role="alert"></p>' +
          '<button type="submit">Enter</button>' +
        '</form>' +
      '</div>';
    gate.querySelector('h2').textContent = TITLE;
    if (NOTE) gate.querySelector('.note').textContent = NOTE;
    document.body.appendChild(gate);
    var input = gate.querySelector('input');
    var err = gate.querySelector('.err');
    gate.querySelector('form').addEventListener('submit', function (e) {
      e.preventDefault();
      if (input.value === PASSWORD) {
        remember();
        document.documentElement.classList.remove('mt-gated');
        gate.remove();
      } else {
        err.textContent = 'Wrong password.';
        input.value = '';
        input.focus();
      }
    });
  }

  if (unlocked()) return;
  if (document.body) build(); else document.addEventListener('DOMContentLoaded', build);
})();
