/*
 * The Mutapa Times - Configuration
 * Single-page news aggregator: all Zimbabwe news, sorted by newest
 * Pulls from multiple Google News RSS feeds for broad coverage
 */
var MUTAPA_CONFIG = {
  CACHE_DURATION: 30 * 60 * 1000,
  RSS_API: "https://api.rss2json.com/v1/api.json?rss_url=",
  DATA_PATH: "data/"
};

// Multiple RSS feeds to pull from — broad, less selective, prioritizing recency
var MAIN_RSS_FEEDS = [
  "https://news.google.com/rss/search?q=Zimbabwe&hl=en&gl=US&ceid=US:en",
  "https://news.google.com/rss/search?q=Zimbabwe+news+today&hl=en&gl=US&ceid=US:en",
  "https://news.google.com/rss/search?q=Harare+OR+Bulawayo+OR+Mutare&hl=en&gl=US&ceid=US:en",
  "https://news.google.com/rss/search?q=Zimbabwe+politics+government+economy&hl=en&gl=US&ceid=US:en",
  "https://news.google.com/rss/search?q=site:zimlive.com+OR+site:newsday.co.zw+OR+site:herald.co.zw+OR+site:bulawayo24.com+OR+site:263chat.com&hl=en&gl=US&ceid=US:en",
  "https://news.google.com/rss/search?q=site:pindula.co.zw+OR+site:nehanda radio+OR+site:newzimbabwe.com+OR+site:thezimbabwemail.com&hl=en&gl=US&ceid=US:en"
];

// Sidebar feeds — more local-focused
var SIDEBAR_RSS_FEEDS = [
  "https://news.google.com/rss/search?q=Zimbabwe+local+news&hl=en&gl=US&ceid=US:en",
  "https://news.google.com/rss/search?q=Zimbabwe+business+sports+entertainment+health&hl=en&gl=US&ceid=US:en",
  "https://news.google.com/rss/search?q=Harare+Bulawayo+Gweru+Masvingo+Mutare+Chitungwiza&hl=en&gl=US&ceid=US:en"
];

// Spotlight feeds — reputable international sources only
var SPOTLIGHT_RSS_FEEDS = [
  "https://news.google.com/rss/search?q=Zimbabwe+site:bbc.com+OR+site:reuters.com+OR+site:nytimes.com+OR+site:theguardian.com+OR+site:aljazeera.com+OR+site:ft.com+OR+site:economist.com+OR+site:bloomberg.com+OR+site:apnews.com&hl=en&gl=US&ceid=US:en"
];

// Reputable sources for spotlight matching
var REPUTABLE_SOURCES = [
  "bbc", "reuters", "new york times", "nytimes", "the guardian", "guardian",
  "al jazeera", "aljazeera", "financial times", "ft.com", "the economist",
  "bloomberg", "associated press", "ap news", "apnews", "washington post",
  "cnn", "sky news", "the telegraph", "the independent", "france 24",
  "dw", "deutsche welle"
];

function isReputableSource(source) {
  if (!source) return false;
  var s = source.toLowerCase();
  for (var i = 0; i < REPUTABLE_SOURCES.length; i++) {
    if (s.indexOf(REPUTABLE_SOURCES[i]) !== -1) return true;
  }
  return false;
}

// Max age for spotlight articles (30 days — up to a month old)
var SPOTLIGHT_MAX_AGE_MS = 30 * 24 * 60 * 60 * 1000;

// Zimbabwe cities for weather
var WEATHER_CITIES = [
  { id: "harare", name: "Harare", lat: -17.83, lon: 31.05 },
  { id: "bulawayo", name: "Bulawayo", lat: -20.13, lon: 28.63 },
  { id: "mutare", name: "Mutare", lat: -18.97, lon: 32.67 },
  { id: "vicfalls", name: "Victoria Falls", lat: -17.93, lon: 25.83 },
  { id: "gweru", name: "Gweru", lat: -19.45, lon: 29.82 }
];

function getWeatherDescription(code) {
  var descriptions = {
    0: { text: "Clear sky", emoji: "\u2600\ufe0f" },
    1: { text: "Mainly clear", emoji: "\ud83c\udf24\ufe0f" },
    2: { text: "Partly cloudy", emoji: "\u26c5" },
    3: { text: "Overcast", emoji: "\u2601\ufe0f" },
    45: { text: "Fog", emoji: "\ud83c\udf2b\ufe0f" },
    48: { text: "Rime fog", emoji: "\ud83c\udf2b\ufe0f" },
    51: { text: "Light drizzle", emoji: "\ud83c\udf26\ufe0f" },
    53: { text: "Drizzle", emoji: "\ud83c\udf27\ufe0f" },
    55: { text: "Heavy drizzle", emoji: "\ud83c\udf27\ufe0f" },
    61: { text: "Light rain", emoji: "\ud83c\udf26\ufe0f" },
    63: { text: "Rain", emoji: "\ud83c\udf27\ufe0f" },
    65: { text: "Heavy rain", emoji: "\ud83c\udf27\ufe0f" },
    71: { text: "Light snow", emoji: "\ud83c\udf28\ufe0f" },
    73: { text: "Snow", emoji: "\u2744\ufe0f" },
    75: { text: "Heavy snow", emoji: "\u2744\ufe0f" },
    80: { text: "Light showers", emoji: "\ud83c\udf26\ufe0f" },
    81: { text: "Showers", emoji: "\ud83c\udf27\ufe0f" },
    82: { text: "Heavy showers", emoji: "\u26c8\ufe0f" },
    95: { text: "Thunderstorm", emoji: "\u26a1" },
    96: { text: "Thunderstorm", emoji: "\u26a1" },
    99: { text: "Thunderstorm", emoji: "\u26a1" }
  };
  return descriptions[code] || { text: "Unknown", emoji: "\ud83c\udf21\ufe0f" };
}

// LocalStorage cache helpers
function getCache(key) {
  try {
    var cached = localStorage.getItem("mutapa_" + key);
    if (cached) {
      var parsed = JSON.parse(cached);
      if (Date.now() - parsed.timestamp < MUTAPA_CONFIG.CACHE_DURATION) {
        return parsed.data;
      }
      localStorage.removeItem("mutapa_" + key);
    }
  } catch (e) {}
  return null;
}

function setCache(key, data) {
  try {
    localStorage.setItem("mutapa_" + key, JSON.stringify({
      timestamp: Date.now(),
      data: data
    }));
  } catch (e) {}
}

// Weather
function fetchWeather() {
  WEATHER_CITIES.forEach(function (city) {
    var cacheKey = "weather_" + city.id;
    var cached = getCache(cacheKey);
    if (cached) { displayCityWeather(city.id, cached); return; }
    $.ajax({
      type: "GET",
      url: "https://api.open-meteo.com/v1/forecast?latitude=" + city.lat +
        "&longitude=" + city.lon + "&current_weather=true&timezone=Africa/Harare",
      success: function (data) {
        if (data && data.current_weather) {
          setCache(cacheKey, data.current_weather);
          displayCityWeather(city.id, data.current_weather);
        }
      }
    });
  });
}

function displayCityWeather(cityId, weather) {
  var el = $("#weather-" + cityId);
  if (el.length) {
    var w = getWeatherDescription(weather.weathercode);
    el.find(".weather-emoji").text(w.emoji);
    el.find(".weather-temp").text(Math.round(weather.temperature) + "\u00B0C");
    el.find(".weather-desc").text(w.text);
  }
}

// Helpers
function extractSource(title) {
  var lastDash = title.lastIndexOf(" - ");
  if (lastDash > 0 && lastDash > title.length * 0.3) {
    return { headline: title.substring(0, lastDash), source: title.substring(lastDash + 3) };
  }
  return { headline: title, source: "" };
}

function stripHtml(html) {
  var tmp = document.createElement("div");
  tmp.innerHTML = html;
  return tmp.textContent || tmp.innerText || "";
}

function cleanText(text) {
  if (!text) return "";
  return text.replace(/\s*\[\d+ chars\]\s*$/, '').trim();
}

function getFullText(content, description) {
  var c = cleanText(content);
  var d = cleanText(description);
  return c.length >= d.length ? c : d;
}

function getReadingTime(text) {
  if (!text) return "";
  var totalChars = text.length;
  var match = text.match(/\[(\d+)\s*chars?\]\s*$/);
  if (match) {
    totalChars = parseInt(match[1], 10);
  } else if (totalChars < 500) {
    return "";
  }
  var words = Math.round(totalChars / 6);
  var mins = Math.max(1, Math.ceil(words / 200));
  return mins + " min read";
}

function formatDate(dateStr) {
  if (!dateStr) return "";
  try {
    var d = new Date(dateStr);
    if (isNaN(d.getTime())) return "";
    var now = new Date();
    var diffMs = now - d;
    var diffHrs = Math.floor(diffMs / (1000 * 60 * 60));
    if (diffHrs < 1) return "Just now";
    if (diffHrs < 24) return diffHrs + "h ago";
    var diffDays = Math.floor(diffHrs / 24);
    if (diffDays === 1) return "Yesterday";
    if (diffDays < 7) return diffDays + " days ago";
    var options = { month: 'short', day: 'numeric', year: 'numeric' };
    return d.toLocaleDateString("en-US", options);
  } catch (e) {
    return "";
  }
}

// ============================================================
// Main entry point
// ============================================================
function fetchNews() {
  var date = new Date();
  var startDate = new Date("2020-04-18");
  var volNum = Math.round((date.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24));
  var options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };

  $(".date").text(date.toLocaleDateString("en-US", options));
  $(".vol").text("Edition # " + volNum);
  fetchWeather();

  // Duplicate weather cities for infinite ticker scroll
  var ticker = document.querySelector('.weather-ticker');
  if (ticker) {
    var items = ticker.innerHTML;
    ticker.innerHTML = items + items;
  }

  // Init editorial images (sidebar portrait + landscape)
  initEditorialImages();

  // Load all stories from multiple RSS feeds
  loadMainStories();
  loadSpotlightStories();
  loadSidebarStories();
}

// ============================================================
// MAIN STORIES — multiple RSS feeds combined, sorted by newest
// ============================================================
function loadMainStories() {
  var cacheKey = "main_all";
  var cached = getCache(cacheKey);
  if (cached) {
    renderMainStories(cached);
    return;
  }

  var allArticles = [];
  var completed = 0;
  var total = MAIN_RSS_FEEDS.length;

  MAIN_RSS_FEEDS.forEach(function(rssUrl) {
    $.ajax({
      type: "GET",
      url: MUTAPA_CONFIG.RSS_API + encodeURIComponent(rssUrl),
      success: function (data) {
        if (data && data.status === "ok" && data.items && data.items.length > 0) {
          var articles = normalizeRssArticles(data.items);
          allArticles = allArticles.concat(articles);
        }
      },
      complete: function() {
        completed++;
        if (completed === total) {
          // All feeds loaded — deduplicate, filter, sort
          allArticles = deduplicateArticles(allArticles);
          allArticles = allArticles.filter(function(a) { return isRecentArticle(a.publishedAt); });
          allArticles.sort(function(a, b) {
            var dateA = a.publishedAt ? new Date(a.publishedAt).getTime() : 0;
            var dateB = b.publishedAt ? new Date(b.publishedAt).getTime() : 0;
            return dateB - dateA;
          });
          setCache(cacheKey, allArticles);
          renderMainStories(allArticles);
        }
      }
    });
  });
}

// ============================================================
// SIDEBAR — additional feeds, broader coverage
// ============================================================
function loadSidebarStories() {
  var cacheKey = "sidebar_all";
  var cached = getCache(cacheKey);
  if (cached) {
    renderSidebarStories(cached);
    return;
  }

  var allArticles = [];
  var completed = 0;
  var total = SIDEBAR_RSS_FEEDS.length;

  SIDEBAR_RSS_FEEDS.forEach(function(rssUrl) {
    $.ajax({
      type: "GET",
      url: MUTAPA_CONFIG.RSS_API + encodeURIComponent(rssUrl),
      success: function (data) {
        if (data && data.status === "ok" && data.items && data.items.length > 0) {
          var articles = normalizeRssArticles(data.items);
          allArticles = allArticles.concat(articles);
        }
      },
      complete: function() {
        completed++;
        if (completed === total) {
          allArticles = deduplicateArticles(allArticles);
          // Sort sidebar by newest too for recency
          allArticles.sort(function(a, b) {
            var dateA = a.publishedAt ? new Date(a.publishedAt).getTime() : 0;
            var dateB = b.publishedAt ? new Date(b.publishedAt).getTime() : 0;
            return dateB - dateA;
          });
          setCache(cacheKey, allArticles);
          renderSidebarStories(allArticles);
        }
      }
    });
  });
}

// ============================================================
// Normalize & deduplicate articles
// ============================================================

// Known Zimbabwean news sources
var LOCAL_ZIM_SOURCES = [
  "the zimbabwe mail", "zimbabwe situation", "nehanda radio", "bulawayo24",
  "new zimbabwe", "newzimbabwe", "263chat", "the herald", "herald online",
  "heraldonline", "chronicle", "newsday", "daily news", "zimmorning post",
  "zim morning post", "zimbabwe independent", "the standard", "zimlive",
  "pindula", "techzim", "zbcnews", "zbc news", "zimdiaspora",
  "kubatana", "the insider", "cite", "myzimbabwe",
  "zimbo jam", "zimbabwe broadcasting", "radio dialogue",
  "zimfieldguide", "iharare", "hmetro", "h-metro", "b-metro",
  "manica post", "southern eye", "zimpapers", "zimbabwe today",
  "the patriot", "kwayedza", "umthunywa", "zimmorningpost",
  "zimetro", "the zimbabwean", "zimbabwe observer", "zim eye",
  "zimeye", "mbare times", "harare live", "harare news",
  "zvishavane news", "masvingo star", "the mirror"
];

function isLocalZimSource(source) {
  if (!source) return false;
  var s = source.toLowerCase();
  for (var i = 0; i < LOCAL_ZIM_SOURCES.length; i++) {
    if (s.indexOf(LOCAL_ZIM_SOURCES[i]) !== -1) return true;
  }
  return false;
}

// Max age for headlines (14 days — tighter for recency)
var MAX_ARTICLE_AGE_MS = 14 * 24 * 60 * 60 * 1000;

function isRecentArticle(dateStr) {
  if (!dateStr) return false;
  try {
    var d = new Date(dateStr);
    if (isNaN(d.getTime())) return false;
    return (Date.now() - d.getTime()) < MAX_ARTICLE_AGE_MS;
  } catch (e) {
    return false;
  }
}

function extractDescriptionFromHtml(html) {
  if (!html) return "";
  // Google News RSS wraps actual snippets in <font> tags or after <br> tags
  // Try to extract text after the last </a> tag which is often the real snippet
  var afterLinks = html.replace(/<a[^>]*>.*?<\/a>/gi, '').replace(/<ol>.*?<\/ol>/gi, '');
  var stripped = stripHtml(afterLinks).trim();
  // Also try the full stripped version
  var full = stripHtml(html).trim();
  // Return the longer meaningful one
  return stripped.length > full.length * 0.3 ? stripped : full;
}

function isTitleRepeat(title, desc) {
  if (!title || !desc) return true;
  var t = title.toLowerCase().replace(/[^a-z0-9]/g, '');
  var d = desc.toLowerCase().replace(/[^a-z0-9]/g, '');
  // Only filter if extremely short or nearly identical to title
  if (d.length < 15) return true;
  if (t === d) return true;
  if (t.length > 0 && d.length > 0 && t.indexOf(d) !== -1) return true;
  return false;
}

function normalizeRssArticles(items) {
  var result = [];
  for (var i = 0; i < items.length; i++) {
    var item = items[i];
    var parsed = extractSource(item.title || "");
    if (!parsed.headline) continue;

    // Try to get a real description, not just a headline repeat
    var rawDesc = getFullText(item.content, item.description);
    var desc = extractDescriptionFromHtml(rawDesc);
    if (isTitleRepeat(parsed.headline, desc)) desc = "";

    result.push({
      title: parsed.headline,
      url: item.link || "",
      description: desc,
      source: parsed.source,
      publishedAt: item.pubDate || "",
      isLocal: isLocalZimSource(parsed.source)
    });
  }
  return result;
}

// Deduplicate by title similarity
function deduplicateArticles(articles) {
  var seen = {};
  var result = [];
  for (var i = 0; i < articles.length; i++) {
    var key = articles[i].title.toLowerCase().replace(/[^a-z0-9]/g, '').substring(0, 60);
    if (!seen[key]) {
      seen[key] = true;
      result.push(articles[i]);
    }
  }
  return result;
}

// Topic-level deduplication — avoids two articles about the same subject
var STOP_WORDS = ["the","a","an","in","on","at","to","for","of","and","or","is","are","was","were","be","been","has","have","had","do","does","did","will","would","could","should","may","might","can","shall","not","no","but","if","so","by","from","with","as","its","it","this","that","than","then","their","they","them","he","she","his","her","we","our","us","you","your","who","what","which","when","where","how","all","each","every","both","few","more","most","some","any","new","old","over","after","before","about","up","out","says","said","also","just","into","back"];

function getTopicWords(title) {
  return title.toLowerCase().replace(/[^a-z0-9\s]/g, '').split(/\s+/).filter(function(w) {
    return w.length > 2 && STOP_WORDS.indexOf(w) === -1;
  });
}

function topicOverlap(wordsA, wordsB) {
  if (wordsA.length === 0 || wordsB.length === 0) return 0;
  var shared = 0;
  for (var i = 0; i < wordsA.length; i++) {
    if (wordsB.indexOf(wordsA[i]) !== -1) shared++;
  }
  var smaller = Math.min(wordsA.length, wordsB.length);
  return shared / smaller;
}

function deduplicateByTopic(articles) {
  var result = [];
  var topicCache = [];
  for (var i = 0; i < articles.length; i++) {
    var words = getTopicWords(articles[i].title);
    var isDupe = false;
    for (var j = 0; j < topicCache.length; j++) {
      if (topicOverlap(words, topicCache[j]) > 0.4) {
        isDupe = true;
        break;
      }
    }
    if (!isDupe) {
      result.push(articles[i]);
      topicCache.push(words);
    }
  }
  return result;
}

// Break images between news stories — with captions
var BREAK_IMAGES = [
  { src: "break-1.jpg", caption: "Business and intelligence, building the Zimbabwe of tomorrow" },
  { src: "break-2.jpg", caption: "Staying connected and informed, powering Africa\u2019s future" },
  { src: "break-3.jpg", caption: "Enterprise and ambition, the spirit of a nation rising" },
  { src: "break-4.jpg", caption: "Bridging distance and diaspora, one story at a time" }
];

var _breakIdx = 0;

function getNextBreakImage() {
  var item = BREAK_IMAGES[_breakIdx % BREAK_IMAGES.length];
  _breakIdx++;
  return item;
}

function getRandomQuoteImage() {
  var idx = Math.floor(Math.random() * BREAK_IMAGES.length);
  return "img/" + BREAK_IMAGES[idx].src;
}

function initEditorialImages() {
  // Only set random images for elements that don't already have a src
  var portrait = document.querySelector(".editorial-portrait-img");
  if (portrait && !portrait.getAttribute("src")) {
    portrait.src = getRandomQuoteImage();
    portrait.onerror = function() { this.style.display = "none"; };
  }
  var landscape = document.querySelector(".editorial-landscape-img");
  if (landscape && !landscape.getAttribute("src")) {
    landscape.src = getRandomQuoteImage();
    landscape.onerror = function() { this.style.display = "none"; };
  }
  // Proverb background image
  var proverbImg = document.querySelector(".proverb-bg-img");
  if (proverbImg && !proverbImg.getAttribute("src")) {
    proverbImg.src = getRandomQuoteImage();
    proverbImg.onerror = function() { this.style.display = "none"; };
  }
}

// ============================================================
// Share button — uses native Web Share API, clipboard fallback
// ============================================================
var SHARE_ICON_SVG = '<svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"/><polyline points="16 6 12 2 8 6"/><line x1="12" y1="2" x2="12" y2="15"/></svg>';

function createShareBtn(title, url) {
  var btn = $('<button class="share-btn" title="Share this article">').html(SHARE_ICON_SVG);
  btn.on('click', function(e) {
    e.preventDefault();
    e.stopPropagation();
    var shareData = {
      title: title,
      text: title + ' — via The Mutapa Times',
      url: url
    };
    if (navigator.share) {
      navigator.share(shareData).catch(function() {});
    } else {
      // Clipboard fallback for desktop
      var temp = document.createElement('textarea');
      temp.value = url;
      document.body.appendChild(temp);
      temp.select();
      document.execCommand('copy');
      document.body.removeChild(temp);
      var original = btn.html();
      btn.text('Copied!');
      setTimeout(function() { btn.html(original); }, 1500);
    }
  });
  return btn;
}

// ============================================================
// RENDER: Main stories — text + ranking number (alternating sides)
// ============================================================
function renderMainStories(articles) {
  var container = $("#main-stories");
  if (!container.length) return;
  container.empty();

  if (!articles || articles.length === 0) {
    container.html('<p class="loading-msg">No articles found.</p>');
    return;
  }

  // Show last-updated timestamp
  var now = new Date();
  var timeStr = now.toLocaleTimeString("en-US", { hour: '2-digit', minute: '2-digit' });
  container.append($('<p class="feed-updated">').text("Last updated " + timeStr));

  for (var i = 0; i < articles.length && i < 15; i++) {
    var a = articles[i];
    var rank = i + 1;
    var readTime = getReadingTime(a.description);
    var pubDate = formatDate(a.publishedAt);

    var posClass = (rank % 2 === 1) ? "rank-right" : "rank-left";
    var card = $('<div class="main-article">').addClass(posClass);
    if (rank === 1) card.addClass("rank-featured");

    var link = $('<a>').attr('href', a.url || '#').attr('target', '_blank');

    var textCol = $('<div class="main-article-text">');
    textCol.append($('<h3 class="main-article-title">').text(a.title));

    var meta = $('<p class="main-article-meta">');
    if (a.source) {
      meta.append($('<span>').text(a.source));
      if (isReputableSource(a.source)) {
        meta.append($('<span class="verified-badge" title="Verified source">').html('&#10003;'));
      }
    }
    var extras = [];
    if (pubDate) extras.push(pubDate);
    if (readTime) extras.push(readTime);
    if (extras.length) {
      meta.append(document.createTextNode(" \u00b7 " + extras.join(" \u00b7 ")));
    }
    if (a.isLocal) {
      meta.append($('<span class="press-marker local-press">').text("Local"));
    } else if (a.source) {
      meta.append($('<span class="press-marker foreign-press">').text("Foreign"));
    }
    meta.append(createShareBtn(a.title, a.url));
    textCol.append(meta);

    var desc = a.description;
    if (desc && desc.length > 250) desc = desc.substring(0, 250) + "...";
    if (desc) textCol.append($('<p class="main-article-desc">').text(desc));

    link.append(textCol);

    var rankCol = $('<div class="main-article-rank">');
    rankCol.append($('<span class="rank-number">').text(rank));
    link.append(rankCol);

    card.append(link);
    container.append(card);

    // Insert break image with caption after every 2 articles
    if (rank % 2 === 0 && rank < 15) {
      var breakData = getNextBreakImage();
      var ph = $('<div class="break-section">');
      var imgWrap = $('<div class="break-img-wrap">');
      var img = $('<img class="break-img">').attr('src', 'img/' + breakData.src).attr('alt', 'The Mutapa Times').attr('loading', 'lazy');
      img.on('error', function() { $(this).closest('.break-section').hide(); });
      imgWrap.append(img);
      imgWrap.append($('<span class="break-brand">').text("The Mutapa Times"));
      ph.append(imgWrap);
      ph.append($('<p class="break-caption">').text(breakData.caption));
      container.append(ph);
    }
  }

  // Subscribe banner — render full-width after the content-layout grid
  var contentLayout = $(".content-layout");
  if (contentLayout.length) {
    var subscribe = $('<div class="subscribe-banner">');
    subscribe.append($('<h3 class="subscribe-title">').text("Essential intelligence for the Zimbabwean diaspora."));
    subscribe.append($('<p class="subscribe-text">').text("Curated news, economic data, and analysis from foreign press \u2014 delivered to your inbox. Join readers in over 30 countries."));
    var form = $('<div class="subscribe-form">');
    form.append($('<input class="subscribe-input" type="email" placeholder="Enter your email address">'));
    form.append($('<button class="subscribe-btn">').text("Subscribe"));
    subscribe.append(form);
    subscribe.append($('<p class="subscribe-fine">').text("By subscribing you agree to our Terms & Conditions. You may unsubscribe at any time."));
    contentLayout.after(subscribe);
  }
}

// ============================================================
// SPOTLIGHT — reputable international sources
// ============================================================
function loadSpotlightStories() {
  var cacheKey = "spotlight_all";
  var cached = getCache(cacheKey);
  if (cached) {
    renderSpotlightStories(cached);
    return;
  }

  var allArticles = [];
  var completed = 0;
  var total = SPOTLIGHT_RSS_FEEDS.length;

  SPOTLIGHT_RSS_FEEDS.forEach(function(rssUrl) {
    $.ajax({
      type: "GET",
      url: MUTAPA_CONFIG.RSS_API + encodeURIComponent(rssUrl),
      success: function (data) {
        if (data && data.status === "ok" && data.items && data.items.length > 0) {
          var articles = normalizeRssArticles(data.items);
          allArticles = allArticles.concat(articles);
        }
      },
      complete: function() {
        completed++;
        if (completed === total) {
          // Filter to reputable sources only, up to 30 days old
          allArticles = allArticles.filter(function(a) {
            if (!a.publishedAt) return false;
            try {
              var d = new Date(a.publishedAt);
              if (isNaN(d.getTime())) return false;
              return (Date.now() - d.getTime()) < SPOTLIGHT_MAX_AGE_MS && isReputableSource(a.source);
            } catch (e) { return false; }
          });
          allArticles = deduplicateByTopic(allArticles);
          allArticles.sort(function(a, b) {
            var dateA = a.publishedAt ? new Date(a.publishedAt).getTime() : 0;
            var dateB = b.publishedAt ? new Date(b.publishedAt).getTime() : 0;
            return dateB - dateA;
          });
          setCache(cacheKey, allArticles);
          renderSpotlightStories(allArticles);
        }
      }
    });
  });
}

function renderSpotlightStories(articles) {
  var container = $("#spotlight-stories");
  if (!container.length) return;
  container.empty();

  if (!articles || articles.length === 0) {
    container.html('<p class="loading-msg" style="color: rgba(255,255,255,0.6);">No spotlight stories available.</p>');
    return;
  }

  for (var i = 0; i < articles.length && i < 3; i++) {
    var a = articles[i];
    var pubDate = formatDate(a.publishedAt);

    var item = $('<div class="spotlight-item">');
    var link = $('<a>').attr('href', a.url || '#').attr('target', '_blank');

    link.append($('<h4 class="spotlight-title">').text(a.title));

    var meta = $('<p class="spotlight-meta">');
    if (a.source) {
      meta.append($('<span class="verified-source">').text(a.source));
      meta.append($('<span class="verified-badge" title="Verified source">').html('&#10003;'));
    }
    if (pubDate) {
      if (a.source) meta.append(document.createTextNode(" \u00b7 "));
      meta.append(document.createTextNode(pubDate));
    }
    meta.append(createShareBtn(a.title, a.url));
    link.append(meta);

    item.append(link);
    container.append(item);
  }
}

// ============================================================
// RENDER: Sidebar — text-only stacked headlines
// ============================================================
function renderSidebarStories(articles) {
  var container = $("#sidebar-stories");
  if (!container.length) return;
  container.empty();

  if (!articles || articles.length === 0) {
    container.html('<p class="loading-msg">No stories available.</p>');
    return;
  }

  for (var i = 0; i < articles.length && i < 20; i++) {
    var a = articles[i];
    var pubDate = formatDate(a.publishedAt);

    var item = $('<div class="sidebar-item">');
    var link = $('<a>').attr('href', a.url || '#').attr('target', '_blank');

    link.append($('<h4 class="sidebar-title">').text(a.title));

    var meta = $('<p class="sidebar-meta">');
    if (a.source) {
      meta.append($('<span>').text(a.source));
      if (isReputableSource(a.source)) {
        meta.append($('<span class="verified-badge verified-badge-sm" title="Verified source">').html('&#10003;'));
      }
    }
    if (pubDate) {
      meta.append(document.createTextNode(" \u00b7 " + pubDate));
    }
    if (a.isLocal) {
      meta.append($('<span class="press-marker local-press">').text("Local"));
    } else if (a.source) {
      meta.append($('<span class="press-marker foreign-press">').text("Foreign"));
    }
    meta.append(createShareBtn(a.title, a.url));
    link.append(meta);

    item.append(link);
    container.append(item);
  }
}
