/* Password gate for the ZB demo subsite.
 * Sales-demo grade: keeps the link out of casual hands and out of
 * search engines. Not real auth — password is in the JS. Rotate by
 * editing DEMO_PASSWORD below. */
(function () {
  'use strict';
  var DEMO_PASSWORD = 'diaspora2026';
  var STORAGE_KEY = 'zbDemoUnlocked2026';

  function unlocked() {
    try { return sessionStorage.getItem(STORAGE_KEY) === '1'; }
    catch (e) { return false; }
  }
  function markUnlocked() {
    try { sessionStorage.setItem(STORAGE_KEY, '1'); } catch (e) {}
  }

  function injectGateStyles() {
    if (document.getElementById('zbGateStyles')) return;
    var s = document.createElement('style');
    s.id = 'zbGateStyles';
    s.textContent =
      '#zbGate{position:fixed;inset:0;z-index:99999;background:#fff;' +
        'display:flex;align-items:center;justify-content:center;' +
        'font-family:Inter,system-ui,sans-serif}' +
      '#zbGate .gate-card{max-width:420px;padding:40px 32px;text-align:center;' +
        'background:#faf3e0;border-top:6px solid #7bba1f;' +
        'box-shadow:0 10px 40px rgba(0,0,0,0.08)}' +
      '#zbGate h2{font-family:"Playfair Display",Georgia,serif;font-weight:700;' +
        'font-size:26px;margin:0 0 6px;color:#1a1a1a}' +
      '#zbGate .gate-sub{color:#5a5447;font-size:14px;margin:0 0 24px;line-height:1.5}' +
      '#zbGate input{width:100%;padding:12px 14px;border:1px solid #d4ccba;' +
        'font:400 16px/1.2 Inter,sans-serif;background:#fff;border-radius:4px}' +
      '#zbGate input:focus{outline:2px solid #7bba1f;outline-offset:1px}' +
      '#zbGate button{margin-top:12px;width:100%;padding:12px;background:#1a1a1a;' +
        'color:#fff;border:0;font:600 14px/1 Inter,sans-serif;letter-spacing:0.04em;' +
        'text-transform:uppercase;cursor:pointer;border-radius:4px}' +
      '#zbGate button:hover{background:#4f7c10}' +
      '#zbGate .gate-err{color:#c0392b;font-size:13px;margin:8px 0 0;min-height:18px}' +
      '#zbGate .gate-tag{margin-top:24px;font-size:11px;letter-spacing:0.1em;' +
        'text-transform:uppercase;color:#5a5447}';
    document.head.appendChild(s);
  }

  function buildGate() {
    injectGateStyles();
    var gate = document.createElement('div');
    gate.id = 'zbGate';
    gate.innerHTML =
      '<div class="gate-card" role="dialog" aria-labelledby="zbGateTitle">' +
        '<h2 id="zbGateTitle">Confidential preview</h2>' +
        '<p class="gate-sub">This is a private advertising demo prepared for ZB Financial Holdings by <em>The Mutapa Times</em>. Enter the access code shared with you to view.</p>' +
        '<form id="zbGateForm" autocomplete="off">' +
          '<input type="password" id="zbGateInput" placeholder="Access code" aria-label="Access code" autofocus>' +
          '<p class="gate-err" id="zbGateErr" role="alert"></p>' +
          '<button type="submit">Unlock preview</button>' +
        '</form>' +
        '<p class="gate-tag">The Mutapa Times · Sponsored content demo</p>' +
      '</div>';
    document.body.appendChild(gate);

    var form = gate.querySelector('#zbGateForm');
    var input = gate.querySelector('#zbGateInput');
    var err = gate.querySelector('#zbGateErr');
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      if (input.value === DEMO_PASSWORD) {
        markUnlocked();
        gate.remove();
      } else {
        err.textContent = 'Incorrect code. Please try again or contact The Mutapa Times.';
        input.value = '';
        input.focus();
      }
    });
  }

  if (!unlocked()) {
    if (document.body) buildGate();
    else document.addEventListener('DOMContentLoaded', buildGate);
  }
})();
