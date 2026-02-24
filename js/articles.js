/*
 * The Mutapa Times - Articles
 * Fetches and renders original markdown articles from content/articles/
 * Used by articles.html (listing) and article.html (single view)
 */

(function () {
  var GITHUB_REPO = "mutapatimes/mutapatimes";
  var GITHUB_BRANCH = "main";
  var ARTICLES_API = "https://api.github.com/repos/" + GITHUB_REPO + "/contents/content/articles?ref=" + GITHUB_BRANCH;
  var ARTICLES_RAW = "https://raw.githubusercontent.com/" + GITHUB_REPO + "/" + GITHUB_BRANCH + "/content/articles/";
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

    // Use GitHub API to auto-discover articles (no manual index needed)
    fetchJSON(ARTICLES_API, function (err, entries) {
      if (err || !entries || !entries.length) {
        // Fallback: try local path for dev/preview
        fetchLocalArticles(container);
        return;
      }

      // Filter to .md files only (skip index.json etc.)
      var mdFiles = [];
      for (var i = 0; i < entries.length; i++) {
        if (entries[i].name && entries[i].name.match(/\.md$/)) {
          mdFiles.push(entries[i].name);
        }
      }

      if (!mdFiles.length) {
        container.innerHTML = '<p class="articles-empty">No articles yet. Check back soon.</p>';
        return;
      }

      var pending = mdFiles.length;
      var articles = [];

      mdFiles.forEach(function (filename) {
        fetchText(ARTICLES_RAW + filename, function (err2, raw) {
          if (!err2 && raw) {
            var parsed = parseFrontmatter(raw);
            parsed.meta.filename = filename;
            parsed.meta.slug = filename.replace(/\.md$/, "");
            articles.push(parsed.meta);
          }
          pending--;
          if (pending === 0) {
            articles.sort(function (a, b) {
              return new Date(b.date || 0) - new Date(a.date || 0);
            });
            renderList(container, articles);
          }
        });
      });
    });
  }

  // Fallback for local/preview: try loading from local index.json
  function fetchLocalArticles(container) {
    fetchJSON("content/articles/index.json", function (err, files) {
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
      var isWire = a.source_type === "wire";
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
    // Try remote raw content first, fall back to local path
    fetchText(ARTICLES_RAW + filename, function (err, raw) {
      if (err || !raw) {
        fetchText(ARTICLES_PATH + filename, function (err2, raw2) {
          if (err2 || !raw2) {
            container.innerHTML = '<p>Article not found. <a href="articles.html">Back to articles</a></p>';
            return;
          }
          displayArticle(container, raw2);
        });
        return;
      }
      displayArticle(container, raw);
    });
  }

  var BASE_URL = "https://www.mutapatimes.com";

  // Update OG and Twitter meta tags dynamically
  function updateMetaTags(meta) {
    var slug = new URLSearchParams(window.location.search).get("slug") || "";
    var pageUrl = BASE_URL + "/article.html?slug=" + encodeURIComponent(slug);
    var title = (meta.title || "Article") + " | The Mutapa Times";
    var desc = meta.summary || "";
    var imgUrl = meta.image || BASE_URL + "/img/banner.png";

    // Update canonical
    var canonical = document.querySelector('link[rel="canonical"]');
    if (canonical) canonical.setAttribute("href", pageUrl);

    // OG tags
    var ogMap = {
      "og:title": meta.title || "Article",
      "og:description": desc,
      "og:image": imgUrl,
      "og:url": pageUrl
    };
    for (var prop in ogMap) {
      var el = document.querySelector('meta[property="' + prop + '"]');
      if (el) el.setAttribute("content", ogMap[prop]);
    }

    // Twitter tags
    var twMap = {
      "twitter:title": meta.title || "Article",
      "twitter:description": desc,
      "twitter:image": imgUrl
    };
    for (var name in twMap) {
      var el2 = document.querySelector('meta[name="' + name + '"]');
      if (el2) el2.setAttribute("content", twMap[name]);
    }
  }

  // Inject NewsArticle schema.org JSON-LD
  function injectArticleSchema(meta) {
    var slug = new URLSearchParams(window.location.search).get("slug") || "";
    var schema = {
      "@context": "https://schema.org",
      "@type": "NewsArticle",
      "headline": meta.title || "",
      "description": meta.summary || "",
      "url": BASE_URL + "/article.html?slug=" + encodeURIComponent(slug),
      "mainEntityOfPage": {
        "@type": "WebPage",
        "@id": BASE_URL + "/article.html?slug=" + encodeURIComponent(slug)
      },
      "publisher": {
        "@type": "Organization",
        "name": "The Mutapa Times",
        "logo": {
          "@type": "ImageObject",
          "url": BASE_URL + "/img/logo.png"
        }
      },
      "inLanguage": "en"
    };

    if (meta.image) {
      schema.image = { "@type": "ImageObject", "url": meta.image };
    }
    if (meta.author) {
      schema.author = { "@type": "Person", "name": meta.author };
    }
    if (meta.date) {
      var d = new Date(meta.date);
      if (!isNaN(d.getTime())) {
        schema.datePublished = d.toISOString();
        schema.dateModified = d.toISOString();
      }
    }
    if (meta.category) {
      schema.articleSection = meta.category;
    }

    var script = document.createElement("script");
    script.type = "application/ld+json";
    script.textContent = JSON.stringify(schema);
    document.head.appendChild(script);

    // Breadcrumb schema
    var breadcrumb = {
      "@context": "https://schema.org",
      "@type": "BreadcrumbList",
      "itemListElement": [
        { "@type": "ListItem", "position": 1, "name": "Home", "item": BASE_URL + "/" },
        { "@type": "ListItem", "position": 2, "name": "Articles", "item": BASE_URL + "/articles.html" },
        { "@type": "ListItem", "position": 3, "name": meta.title || "Article", "item": BASE_URL + "/article.html?slug=" + encodeURIComponent(slug) }
      ]
    };
    var script2 = document.createElement("script");
    script2.type = "application/ld+json";
    script2.textContent = JSON.stringify(breadcrumb);
    document.head.appendChild(script2);
  }

  // Build share buttons HTML for articles
  function articleShareButtons(meta) {
    var slug = new URLSearchParams(window.location.search).get("slug") || "";
    var url = encodeURIComponent(BASE_URL + "/article.html?slug=" + encodeURIComponent(slug));
    var text = encodeURIComponent((meta.title || "Article") + " - The Mutapa Times");
    return '<div class="article-share">'
      + '<span class="article-share-label">Share this article</span>'
      + '<div class="share-group">'
      + '<a href="https://twitter.com/intent/tweet?url=' + url + '&text=' + text + '&via=mutapatimes" target="_blank" rel="noopener" class="share-btn" title="Share on X">'
      + '<svg viewBox="0 0 24 24" width="14" height="14"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" fill="currentColor"/></svg>'
      + '</a>'
      + '<a href="https://www.facebook.com/sharer/sharer.php?u=' + url + '" target="_blank" rel="noopener" class="share-btn" title="Share on Facebook">'
      + '<svg viewBox="0 0 24 24" width="14" height="14"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z" fill="currentColor"/></svg>'
      + '</a>'
      + '<a href="https://www.linkedin.com/sharing/share-offsite/?url=' + url + '" target="_blank" rel="noopener" class="share-btn" title="Share on LinkedIn">'
      + '<svg viewBox="0 0 24 24" width="14" height="14"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" fill="currentColor"/></svg>'
      + '</a>'
      + '<a href="https://api.whatsapp.com/send?text=' + text + '%20' + url + '" target="_blank" rel="noopener" class="whatsapp-btn" title="Share on WhatsApp">'
      + '<svg viewBox="0 0 24 24" width="14" height="14"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z" fill="currentColor"/></svg>'
      + '</a>'
      + '</div></div>';
  }

  function displayArticle(container, raw) {

      var parsed = parseFrontmatter(raw);
      var meta = parsed.meta;
      var bodyHtml = markdownToHtml(parsed.body);
      var dateStr = formatArticleDate(meta.date);

      // Update page title and meta
      document.title = (meta.title || "Article") + " | The Mutapa Times";
      var metaDesc = document.querySelector('meta[name="description"]');
      if (metaDesc) metaDesc.setAttribute("content", meta.summary || "");

      // Update OG/Twitter meta tags and inject schema
      updateMetaTags(meta);
      injectArticleSchema(meta);

      var html = '<nav class="article-breadcrumb" aria-label="Breadcrumb">'
        + '<a href="index.html">Home</a> <span aria-hidden="true">/</span> '
        + '<a href="articles.html">Articles</a> <span aria-hidden="true">/</span> '
        + '<span>' + escapeHtml(meta.title || "Article") + '</span>'
        + '</nav>';
      html += '<div class="article-header">';
      if (meta.category) {
        html += '<span class="article-category-tag">' + escapeHtml(meta.category) + '</span>';
      }
      html += '<h1 class="article-title">' + escapeHtml(meta.title || "Untitled") + '</h1>';
      html += '<div class="article-meta">';
      if (meta.author) html += '<span class="article-author">By ' + escapeHtml(meta.author) + '</span>';
      if (dateStr) html += '<time class="article-date" datetime="' + (meta.date || '') + '">' + dateStr + '</time>';
      html += '</div>';
      html += '</div>';

      if (meta.image) {
        html += '<img src="' + escapeHtml(meta.image) + '" alt="' + escapeHtml(meta.title || '') + '" class="article-hero-img">';
      }

      html += '<div class="article-body">' + bodyHtml + '</div>';
      html += articleShareButtons(meta);
      html += '<div class="article-back"><a href="articles.html">&larr; All articles</a></div>';

      container.innerHTML = html;
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
