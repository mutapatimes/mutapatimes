#!/usr/bin/env node
/*
 * Password-protect a built preview page by encrypting its body.
 *
 * The output page holds the article as AES-256-GCM ciphertext. The key is
 * derived in the browser from the password with PBKDF2 (SHA-256, 300k
 * rounds), so without the password the page source contains no readable
 * article text, no title and no summary. Works on a static host.
 *
 *   node scripts/encrypt_preview.js <built.html> <password> <out.html>
 *
 * What is kept in the clear: the site's stylesheet and font links, the
 * favicon links and a generic <title>. Everything else from the head
 * (canonical, Open Graph, JSON-LD, analytics) is dropped so nothing leaks.
 */
'use strict';
const fs = require('fs');
const crypto = require('crypto');

const [,, src, password, out] = process.argv;
if (!src || !password || !out) {
  console.error('usage: encrypt_preview.js <built.html> <password> <out.html>');
  process.exit(1);
}

const html = fs.readFileSync(src, 'utf8');
const headInner = html.slice(html.indexOf('<head>') + 6, html.indexOf('</head>'));
const bodyOpen = html.indexOf('<body');
const bodyTagEnd = html.indexOf('>', bodyOpen) + 1;
const bodyClose = html.lastIndexOf('</body>');
const bodyTag = html.slice(bodyOpen, bodyTagEnd);
const bodyClass = (bodyTag.match(/class="([^"]*)"/) || [, ''])[1];
const bodyInner = html.slice(bodyTagEnd, bodyClose);

// Keep only presentation links from the head
const keepLinks = (headInner.match(/<link[^>]+>/g) || []).filter(l =>
  /rel="(stylesheet|preconnect|icon|apple-touch-icon|manifest)"/.test(l) ||
  /fonts\.googleapis\.com\/css/.test(l)
);

const payload = JSON.stringify({ cls: bodyClass, html: bodyInner });
const salt = crypto.randomBytes(16);
const iv = crypto.randomBytes(12);
const ITER = 300000;
const key = crypto.pbkdf2Sync(password, salt, ITER, 32, 'sha256');
const cipher = crypto.createCipheriv('aes-256-gcm', key, iv);
const ct = Buffer.concat([cipher.update(payload, 'utf8'), cipher.final(), cipher.getAuthTag()]);

const b64 = b => b.toString('base64');

const page = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex, nofollow, noarchive">
  <title>Private preview</title>
  ${keepLinks.join('\n  ')}
  <style>
    html.mt-gated { overflow: hidden; }
    #mtGate { position: fixed; inset: 0; z-index: 99999; background: #fafaf7; display: flex; align-items: center; justify-content: center; padding: 24px; font-family: Inter, system-ui, sans-serif; }
    #mtGate .g { width: 100%; max-width: 420px; background: #fff; border: 1px solid #d4d4d4; border-radius: 6px; padding: 36px 32px; }
    #mtGate h2 { font-family: "Playfair Display", Georgia, serif; font-weight: 700; font-size: 1.6rem; line-height: 1.15; margin: 0 0 16px; color: #121212; }
    #mtGate input { width: 100%; box-sizing: border-box; padding: 12px 14px; border: 1px solid #d4d4d4; border-radius: 4px; font: 400 16px/1.2 Inter, system-ui, sans-serif; background: #fff; color: #121212; }
    #mtGate input:focus { outline: 2px solid #c41e1e; outline-offset: 1px; }
    #mtGate button { margin-top: 10px; width: 100%; padding: 12px; background: #121212; color: #fff; border: 0; border-radius: 4px; font: 600 15px/1 Inter, system-ui, sans-serif; cursor: pointer; }
    #mtGate button:hover { background: #c41e1e; }
    #mtGate button[disabled] { opacity: 0.6; cursor: default; }
    #mtGate .err { color: #c41e1e; font-size: 0.85rem; min-height: 18px; margin: 8px 0 0; }
  </style>
</head>
<body>
  <div id="mtGate">
    <div class="g" role="dialog" aria-labelledby="mtGateTitle">
      <h2 id="mtGateTitle">Enter password</h2>
      <form id="mtGateForm" autocomplete="off">
        <input type="password" id="mtGatePw" aria-label="Password" placeholder="Password" autofocus>
        <p class="err" id="mtGateErr" role="alert"></p>
        <button type="submit" id="mtGateBtn">Enter</button>
      </form>
    </div>
  </div>
  <script id="mtPayload" type="application/json">${JSON.stringify({ v: 1, iter: ITER, salt: b64(salt), iv: b64(iv), ct: b64(ct) })}</script>
  <script>
  (function () {
    'use strict';
    var meta = JSON.parse(document.getElementById('mtPayload').textContent);
    var KEY = 'mtPreviewPw:' + location.pathname;
    var enc = new TextEncoder(), dec = new TextDecoder();
    function b64(s) { var b = atob(s), a = new Uint8Array(b.length); for (var i = 0; i < b.length; i++) a[i] = b.charCodeAt(i); return a; }

    function unlock(pw) {
      return crypto.subtle.importKey('raw', enc.encode(pw), 'PBKDF2', false, ['deriveKey'])
        .then(function (k) {
          return crypto.subtle.deriveKey(
            { name: 'PBKDF2', salt: b64(meta.salt), iterations: meta.iter, hash: 'SHA-256' },
            k, { name: 'AES-GCM', length: 256 }, false, ['decrypt']);
        })
        .then(function (key) { return crypto.subtle.decrypt({ name: 'AES-GCM', iv: b64(meta.iv) }, key, b64(meta.ct)); })
        .then(function (buf) { return JSON.parse(dec.decode(buf)); });
    }

    function render(p) {
      document.documentElement.classList.remove('mt-gated');
      document.body.className = p.cls || '';
      document.body.innerHTML = p.html;
      // Scripts inserted with innerHTML do not run; recreate them so the
      // page behaves exactly like the published article.
      var scripts = Array.prototype.slice.call(document.body.querySelectorAll('script'));
      scripts.forEach(function (old) {
        if ((old.type || '').indexOf('ld+json') !== -1) { old.remove(); return; }
        var s = document.createElement('script');
        Array.prototype.forEach.call(old.attributes, function (a) { s.setAttribute(a.name, a.value); });
        if (!old.src) s.textContent = old.textContent;
        old.parentNode.replaceChild(s, old);
      });
      if (location.hash) { try { var t = document.querySelector(location.hash); if (t) t.scrollIntoView(); } catch (e) {} }
    }

    var form = document.getElementById('mtGateForm');
    var input = document.getElementById('mtGatePw');
    var err = document.getElementById('mtGateErr');
    var btn = document.getElementById('mtGateBtn');
    document.documentElement.classList.add('mt-gated');

    function attempt(pw, silent) {
      btn.disabled = true;
      return unlock(pw).then(function (p) {
        try { sessionStorage.setItem(KEY, pw); } catch (e) {}
        render(p);
      }).catch(function () {
        btn.disabled = false;
        if (!silent) { err.textContent = 'Wrong password.'; input.value = ''; input.focus(); }
      });
    }

    form.addEventListener('submit', function (e) { e.preventDefault(); attempt(input.value, false); });
    window.mtUnlock = function (pw) { return attempt(pw, false); };

    var saved = null;
    try { saved = sessionStorage.getItem(KEY); } catch (e) {}
    if (saved) attempt(saved, true);
  })();
  </script>
</body>
</html>
`;

fs.writeFileSync(out, page);
console.log('wrote', out, '(' + Math.round(ct.length / 1024) + ' KB ciphertext, ' + ITER + ' PBKDF2 rounds)');
