/*
 * Quote-share for The Mutapa Times.
 *
 * Highlight any sentence in an article body → a small "Share this quote"
 * button fades in near the selection. Tap it and we render a butter
 * 1080×1080 share card on a hidden canvas (brand wordmark + the quote
 * in Playfair + attribution), then call the native share sheet with the
 * resulting PNG file. Desktop fallback: download the PNG and copy a
 * deep-link URL to clipboard.
 *
 * Targets `.article-body`, `.news-landing`, `.econ-narrative`, or any
 * element with `data-quote-shareable`. No external dependencies.
 */
(function () {
  "use strict";

  var SELECTORS = ".article-body, .news-landing, .econ-narrative, [data-quote-shareable]";
  var MIN_SELECTION_LENGTH = 12;
  var MAX_QUOTE_LENGTH = 280;   // anything longer gets ellipsised in the card

  // Brand tokens
  var BG = "#F5E8C8";
  var INK = "#1A1A1A";
  var ACCENT = "#C41E1E";
  var MUTED = "#666";
  var SERIF = "'Playfair Display', Georgia, serif";
  var SANS = "'Inter', system-ui, -apple-system, sans-serif";

  // ---- Bootstrap ----
  function articleRoot() {
    return document.querySelector(SELECTORS);
  }

  function init() {
    if (!articleRoot()) return;

    var btn = makeButton();
    document.body.appendChild(btn);

    var toast = makeToast();
    document.body.appendChild(toast);

    var hideTimer = null;
    function hide() { btn.style.display = "none"; }
    function showAt(rect) {
      btn.style.display = "inline-flex";
      var top = window.scrollY + rect.top - btn.offsetHeight - 12;
      var left = window.scrollX + rect.left + rect.width / 2 - btn.offsetWidth / 2;
      // Keep it inside the viewport on small screens
      var minLeft = window.scrollX + 12;
      var maxLeft = window.scrollX + document.documentElement.clientWidth - btn.offsetWidth - 12;
      btn.style.top = top + "px";
      btn.style.left = Math.max(minLeft, Math.min(maxLeft, left)) + "px";
    }

    function update() {
      var root = articleRoot();
      if (!root) return hide();
      var sel = window.getSelection();
      if (!sel || sel.isCollapsed) return hide();
      var text = sel.toString().trim();
      if (text.length < MIN_SELECTION_LENGTH) return hide();
      // Confirm selection is inside our article root
      var range = sel.getRangeAt(0);
      var container = range.commonAncestorContainer;
      if (container.nodeType === 3) container = container.parentNode;
      if (!root.contains(container)) return hide();
      var rect = range.getBoundingClientRect();
      if (!rect || rect.width === 0) return hide();
      showAt(rect);
    }

    // Selection changes (covers keyboard + mouse + touch)
    document.addEventListener("selectionchange", function () {
      // Debounce so we don't recompute on every tick of a drag
      if (hideTimer) clearTimeout(hideTimer);
      hideTimer = setTimeout(update, 80);
    });
    // Recompute on scroll/resize so the button tracks the selection
    window.addEventListener("scroll", update, { passive: true });
    window.addEventListener("resize", update);

    btn.addEventListener("mousedown", function (e) { e.preventDefault(); }); // don't lose selection
    btn.addEventListener("touchstart", function (e) { e.preventDefault(); }, { passive: false });
    btn.addEventListener("click", function (e) {
      e.preventDefault();
      var text = (window.getSelection() && window.getSelection().toString().trim()) || "";
      if (text.length < MIN_SELECTION_LENGTH) return;
      shareQuote(text, toast);
    });
  }

  // ---- DOM bits ----
  function makeButton() {
    var btn = document.createElement("button");
    btn.type = "button";
    btn.className = "quote-share-btn";
    btn.setAttribute("aria-label", "Share this quote");
    btn.innerHTML =
      '<svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor" aria-hidden="true">' +
        '<path d="M7 10a3 3 0 1 1 0-6 3 3 0 0 1 0 6zm10 9a3 3 0 1 1 0 6 3 3 0 0 1 0-6zm0-13a3 3 0 1 1 0-6 3 3 0 0 1 0 6zm-7.6 9.06l5.2 3.1M14.6 6.84l-5.2 3.1"/>' +
        '<circle cx="7" cy="12" r="3"/><circle cx="17" cy="5" r="3"/><circle cx="17" cy="19" r="3"/>' +
        '<line x1="8.59" y1="13.51" x2="15.42" y2="17.49" stroke="currentColor" stroke-width="1.5"/>' +
        '<line x1="15.41" y1="6.51" x2="8.59" y2="10.49" stroke="currentColor" stroke-width="1.5"/>' +
      '</svg>' +
      '<span>Share this quote</span>';
    return btn;
  }

  function makeToast() {
    var t = document.createElement("div");
    t.className = "quote-share-toast";
    t.setAttribute("role", "status");
    return t;
  }

  function showToast(toast, text) {
    toast.textContent = text;
    toast.classList.add("is-visible");
    setTimeout(function () { toast.classList.remove("is-visible"); }, 2400);
  }

  // ---- Canvas card rendering ----
  function wrapLines(ctx, text, maxWidth) {
    // Greedy word wrap — works well for editorial-length quotes.
    var words = text.split(/\s+/);
    var lines = [];
    var cur = "";
    for (var i = 0; i < words.length; i++) {
      var test = cur ? cur + " " + words[i] : words[i];
      if (ctx.measureText(test).width <= maxWidth || !cur) {
        cur = test;
      } else {
        lines.push(cur);
        cur = words[i];
      }
    }
    if (cur) lines.push(cur);
    return lines;
  }

  function pickQuoteFontSize(ctx, text, maxWidth, maxLines) {
    // Step the font size down until the quote fits in maxLines.
    for (var size = 64; size >= 32; size -= 2) {
      ctx.font = "700 " + size + "px " + SERIF;
      var lines = wrapLines(ctx, text, maxWidth);
      if (lines.length <= maxLines) return { size: size, lines: lines };
    }
    ctx.font = "700 32px " + SERIF;
    var truncated = text.slice(0, MAX_QUOTE_LENGTH).replace(/\s+\S*$/, "") + "…";
    return { size: 32, lines: wrapLines(ctx, truncated, maxWidth) };
  }

  function renderCard(quote, sourceLine) {
    var canvas = document.createElement("canvas");
    canvas.width = 1080;
    canvas.height = 1080;
    var ctx = canvas.getContext("2d");

    // Butter background
    ctx.fillStyle = BG;
    ctx.fillRect(0, 0, 1080, 1080);

    var pad = 88;

    // ---- Top: brand mark + accent rule ----
    ctx.fillStyle = INK;
    ctx.font = "900 38px " + SERIF;
    ctx.textBaseline = "top";
    ctx.fillText("THE MUTAPA TIMES", pad, pad);
    ctx.fillStyle = ACCENT;
    ctx.fillRect(pad, pad + 50, 92, 4);
    ctx.fillStyle = MUTED;
    ctx.font = "700 14px " + SANS;
    ctx.fillText("ZIMBABWE OUTSIDE-IN", pad, pad + 70);

    // ---- Eyebrow ----
    ctx.fillStyle = ACCENT;
    ctx.font = "700 16px " + SANS;
    ctx.fillText("QUOTED", pad, pad + 150);

    // ---- Quote — big serif, smart curly quotes ----
    var pretty = "“" + quote.replace(/^["'“‘]+|["'”’]+$/g, "") + "”";
    var maxLines = 7;
    var maxWidth = 1080 - pad * 2;
    var picked = pickQuoteFontSize(ctx, pretty, maxWidth, maxLines);
    ctx.fillStyle = INK;
    ctx.font = "700 " + picked.size + "px " + SERIF;
    var lineHeight = Math.round(picked.size * 1.25);
    var quoteY = pad + 200;
    for (var i = 0; i < picked.lines.length; i++) {
      ctx.fillText(picked.lines[i], pad, quoteY + i * lineHeight);
    }

    // ---- Bottom: attribution + URL ----
    ctx.fillStyle = ACCENT;
    ctx.fillRect(pad, 1080 - pad - 100, 60, 3);

    ctx.fillStyle = INK;
    ctx.font = "700 22px " + SANS;
    ctx.fillText(sourceLine || "The Mutapa Times", pad, 1080 - pad - 80);

    ctx.fillStyle = MUTED;
    ctx.font = "600 18px " + SANS;
    ctx.fillText("mutapatimes.com", pad, 1080 - pad - 48);

    return canvas;
  }

  // ---- Share ----
  function gatherSource() {
    var title = document.title.split("|")[0].trim();
    var meta = document.querySelector('meta[name="author"]');
    var author = meta ? meta.getAttribute("content") : "";
    // Try to pull source from the news-landing header
    var sourceEl = document.querySelector(".news-source-line strong, .article-author");
    if (sourceEl && sourceEl.textContent.trim()) {
      return "via " + sourceEl.textContent.trim().replace(/^By\s+/i, "");
    }
    if (author) return "via " + author;
    return title ? "from “" + title + "”" : "";
  }

  function canShareFiles(file) {
    if (!navigator.share) return false;
    if (!navigator.canShare) return false;
    try { return navigator.canShare({ files: [file] }); }
    catch (e) { return false; }
  }

  function shareQuote(text, toast) {
    // Wait for fonts so canvas paints with Playfair/Inter, not Times/Arial.
    var fontsReady = (document.fonts && document.fonts.ready) || Promise.resolve();
    fontsReady.then(function () {
      var source = gatherSource();
      var canvas = renderCard(text, source);
      canvas.toBlob(function (blob) {
        if (!blob) return;
        var file = new File([blob], "mutapa-quote.png", { type: "image/png" });
        var url = window.location.href.split("#")[0];
        // Append a Text Fragment so recipients land at the highlighted line.
        var fragmentUrl = url + "#:~:text=" + encodeURIComponent(text.slice(0, 200));
        var shareText = "“" + text + "” — The Mutapa Times";

        if (canShareFiles(file)) {
          navigator.share({
            files: [file],
            text: shareText,
            url: fragmentUrl,
          }).catch(function () {});
          return;
        }
        // Fallback path: download the PNG and copy the deep link
        var dl = document.createElement("a");
        dl.href = URL.createObjectURL(blob);
        dl.download = "mutapa-quote.png";
        document.body.appendChild(dl);
        dl.click();
        document.body.removeChild(dl);
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(fragmentUrl).catch(function () {});
        }
        if (toast) showToast(toast, "Quote saved — link copied to clipboard");
        // Clear the selection so the button hides
        try { window.getSelection().removeAllRanges(); } catch (e) {}
      }, "image/png");
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
