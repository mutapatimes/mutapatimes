/*
 * The Mutapa Times - Articles
 * Fetches and renders original markdown articles from content/articles/
 * Used by articles.html (listing) and article.html (single view)
 */

(function () {
  var ARTICLES_INDEX = "content/articles/index.json";
  var ARTICLES_PATH = "content/articles/";

  // Simple frontmatter parser: splits --- delimited YAML header from markdown body
  function parseFrontmatter(raw) {
    var match = raw.match(/^---\s*\n([\s\S]*?)\n---\s*\n([\s\S]*)$/);
    if (!match) return { meta: {}, body: raw };
    var meta = {};
    var lines = match[1].split("\n");
    for (var i = 0; i < lines.length; i++) {
      var colon = lines[i].indexOf(":");
      if (colon === -1) continue;
      var key = lines[i].substring(0, colon).trim();
      var val = lines[i].substring(colon + 1).trim();
      // Strip surrounding quotes
      if ((val.charAt(0) === '"' && val.charAt(val.length - 1) === '"') ||
          (val.charAt(0) === "'" && val.charAt(val.length - 1) === "'")) {
        val = val.substring(1, val.length - 1);
      }
      meta[key] = val;
    }
    return { meta: meta, body: match[2] };
  }

  // Minimal markdown to HTML converter (handles common patterns)
  function markdownToHtml(md) {
    var html = md;
    // Headings
    html = html.replace(/^#### (.+)$/gm, "<h4>$1</h4>");
    html = html.replace(/^### (.+)$/gm, "<h3>$1</h3>");
    html = html.replace(/^## (.+)$/gm, "<h2>$1</h2>");
    html = html.replace(/^# (.+)$/gm, "<h1>$1</h1>");
    // Bold and italic
    html = html.replace(/\*\*\*(.+?)\*\*\*/g, "<strong><em>$1</em></strong>");
    html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
    html = html.replace(/\*(.+?)\*/g, "<em>$1</em>");
    // Images
    html = html.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '<img src="$2" alt="$1" class="article-body-img">');
    // Links
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
    // Unordered lists
    html = html.replace(/^- (.+)$/gm, "<li>$1</li>");
    html = html.replace(/((?:<li>.*<\/li>\n?)+)/g, "<ul>$1</ul>");
    // Horizontal rules
    html = html.replace(/^---$/gm, "<hr>");
    // Blockquotes
    html = html.replace(/^> (.+)$/gm, "<blockquote>$1</blockquote>");
    // Paragraphs: wrap remaining lines separated by blank lines
    html = html.replace(/\n\n+/g, "\n</p>\n<p>\n");
    html = "<p>\n" + html + "\n</p>";
    // Clean up empty paragraphs and paragraphs wrapping block elements
    html = html.replace(/<p>\s*<\/p>/g, "");
    html = html.replace(/<p>\s*(<h[1-4]>)/g, "$1");
    html = html.replace(/(<\/h[1-4]>)\s*<\/p>/g, "$1");
    html = html.replace(/<p>\s*(<ul>)/g, "$1");
    html = html.replace(/(<\/ul>)\s*<\/p>/g, "$1");
    html = html.replace(/<p>\s*(<blockquote>)/g, "$1");
    html = html.replace(/(<\/blockquote>)\s*<\/p>/g, "$1");
    html = html.replace(/<p>\s*(<hr>)\s*<\/p>/g, "$1");
    html = html.replace(/<p>\s*(<hr>)/g, "$1");
    return html;
  }

  // Format date for display
  function formatArticleDate(dateStr) {
    if (!dateStr) return "";
    var d = new Date(dateStr);
    if (isNaN(d.getTime())) return dateStr;
    var months = ["January", "February", "March", "April", "May", "June",
                  "July", "August", "September", "October", "November", "December"];
    return months[d.getMonth()] + " " + d.getDate() + ", " + d.getFullYear();
  }

  // Fetch JSON helper
  function fetchJSON(url, callback) {
    var xhr = new XMLHttpRequest();
    xhr.open("GET", url, true);
    xhr.onreadystatechange = function () {
      if (xhr.readyState === 4) {
        if (xhr.status === 200) {
          try { callback(null, JSON.parse(xhr.responseText)); }
          catch (e) { callback(e, null); }
        } else {
          callback(new Error("HTTP " + xhr.status), null);
        }
      }
    };
    xhr.send();
  }

  // Fetch raw text helper
  function fetchText(url, callback) {
    var xhr = new XMLHttpRequest();
    xhr.open("GET", url, true);
    xhr.onreadystatechange = function () {
      if (xhr.readyState === 4) {
        if (xhr.status === 200) {
          callback(null, xhr.responseText);
        } else {
          callback(new Error("HTTP " + xhr.status), null);
        }
      }
    };
    xhr.send();
  }

  // ---- Articles listing page (articles.html) ----
  function renderArticlesList() {
    var container = document.getElementById("articles-list");
    if (!container) return;

    fetchJSON(ARTICLES_INDEX, function (err, files) {
      if (err || !files || !files.length) {
        container.innerHTML = '<p class="articles-empty">No articles yet. Check back soon.</p>';
        return;
      }

      var pending = files.length;
      var articles = [];

      files.forEach(function (filename) {
        fetchText(ARTICLES_PATH + filename, function (err2, raw) {
          if (!err2 && raw) {
            var parsed = parseFrontmatter(raw);
            parsed.meta.filename = filename;
            parsed.meta.slug = filename.replace(/\.md$/, "");
            articles.push(parsed.meta);
          }
          pending--;
          if (pending === 0) {
            // Sort by date descending
            articles.sort(function (a, b) {
              return new Date(b.date || 0) - new Date(a.date || 0);
            });
            renderList(container, articles);
          }
        });
      });
    });
  }

  function renderList(container, articles) {
    var html = "";
    for (var i = 0; i < articles.length; i++) {
      var a = articles[i];
      var dateStr = formatArticleDate(a.date);
      var categoryHtml = a.category
        ? '<span class="article-card-category">' + escapeHtml(a.category) + '</span>'
        : '';
      html += '<a href="article.html?slug=' + encodeURIComponent(a.slug) + '" class="article-card">';
      if (a.image) {
        html += '<img src="' + escapeHtml(a.image) + '" alt="" class="article-card-img">';
      }
      html += '<div class="article-card-body">';
      html += categoryHtml;
      html += '<h3 class="article-card-title">' + escapeHtml(a.title || "Untitled") + '</h3>';
      html += '<p class="article-card-summary">' + escapeHtml(a.summary || "") + '</p>';
      html += '<div class="article-card-meta">';
      if (a.author) html += '<span>' + escapeHtml(a.author) + '</span>';
      if (dateStr) html += '<span>' + dateStr + '</span>';
      html += '</div>';
      html += '</div></a>';
    }
    container.innerHTML = html;
  }

  // ---- Single article view (article.html) ----
  function renderSingleArticle() {
    var container = document.getElementById("article-content");
    if (!container) return;

    var params = new URLSearchParams(window.location.search);
    var slug = params.get("slug");
    if (!slug) {
      container.innerHTML = '<p>Article not found. <a href="articles.html">Back to articles</a></p>';
      return;
    }

    var filename = slug + ".md";
    fetchText(ARTICLES_PATH + filename, function (err, raw) {
      if (err || !raw) {
        container.innerHTML = '<p>Article not found. <a href="articles.html">Back to articles</a></p>';
        return;
      }

      var parsed = parseFrontmatter(raw);
      var meta = parsed.meta;
      var bodyHtml = markdownToHtml(parsed.body);
      var dateStr = formatArticleDate(meta.date);

      // Update page title and meta
      document.title = (meta.title || "Article") + " | The Mutapa Times";
      var metaDesc = document.querySelector('meta[name="description"]');
      if (metaDesc) metaDesc.setAttribute("content", meta.summary || "");

      var html = '<div class="article-header">';
      if (meta.category) {
        html += '<span class="article-category-tag">' + escapeHtml(meta.category) + '</span>';
      }
      html += '<h1 class="article-title">' + escapeHtml(meta.title || "Untitled") + '</h1>';
      html += '<div class="article-meta">';
      if (meta.author) html += '<span class="article-author">By ' + escapeHtml(meta.author) + '</span>';
      if (dateStr) html += '<span class="article-date">' + dateStr + '</span>';
      html += '</div>';
      html += '</div>';

      if (meta.image) {
        html += '<img src="' + escapeHtml(meta.image) + '" alt="" class="article-hero-img">';
      }

      html += '<div class="article-body">' + bodyHtml + '</div>';
      html += '<div class="article-back"><a href="articles.html">&larr; All articles</a></div>';

      container.innerHTML = html;
    });
  }

  // Escape HTML entities
  function escapeHtml(str) {
    var div = document.createElement("div");
    div.appendChild(document.createTextNode(str));
    return div.innerHTML;
  }

  // Detect which page we're on and render accordingly
  if (document.getElementById("articles-list")) {
    renderArticlesList();
  } else if (document.getElementById("article-content")) {
    renderSingleArticle();
  }
})();
