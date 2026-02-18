/*
 * The Mutapa Times - Configuration
 * All stories sourced from Google News RSS via rss2json.com
 * Main stories: sorted by newest, with ranking numbers
 * Sidebar: additional headlines, generic order
 */
var MUTAPA_CONFIG = {
  CACHE_DURATION: 30 * 60 * 1000,
  RSS_API: "https://api.rss2json.com/v1/api.json?rss_url=",
  DATA_PATH: "data/"
};

var CATEGORIES = {
  business:      { label: "Business",      topic: "business",      rss: "https://news.google.com/rss/search?q=Zimbabwe+business+economy+finance+trade&hl=en&gl=US&ceid=US:en" },
  technology:    { label: "Technology",     topic: "technology",    rss: "https://news.google.com/rss/search?q=Zimbabwe+technology+tech+digital+innovation&hl=en&gl=US&ceid=US:en" },
  entertainment: { label: "Entertainment",  topic: "entertainment", rss: "https://news.google.com/rss/search?q=Zimbabwe+entertainment+music+arts+culture+film&hl=en&gl=US&ceid=US:en" },
  sports:        { label: "Sports",         topic: "sports",        rss: "https://news.google.com/rss/search?q=Zimbabwe+sports+cricket+football+rugby+athletics&hl=en&gl=US&ceid=US:en" },
  science:       { label: "Science",        topic: "science",       rss: "https://news.google.com/rss/search?q=Zimbabwe+science+research+environment+wildlife&hl=en&gl=US&ceid=US:en" },
  health:        { label: "Health",         topic: "health",        rss: "https://news.google.com/rss/search?q=Zimbabwe+health+medical+hospital+disease&hl=en&gl=US&ceid=US:en" }
};

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

// Reading time estimate — only shown when we have real data
function getReadingTime(text) {
  if (!text) return "";
  var totalChars = text.length;
  // GNews truncates content with "[xxx chars]" — use full char count
  var match = text.match(/\[(\d+)\s*chars?\]\s*$/);
  if (match) {
    totalChars = parseInt(match[1], 10);
  } else if (totalChars < 500) {
    // Short snippet (RSS) — not enough data to estimate read time
    return "";
  }
  // Average word length ~5 chars + space = ~6 chars per word
  var words = Math.round(totalChars / 6);
  var mins = Math.max(1, Math.ceil(words / 200));
  return mins + " min read";
}

// Format publish date — relative
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
function fetchNews(feedKey) {
  _activeCategory = feedKey;
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

  // Load main stories from Google News RSS (sorted by newest)
  loadMainStories(feedKey);
  // Load sidebar stories from Google News RSS (generic order)
  loadSidebarStories(feedKey);
}

// ============================================================
// MAIN STORIES — Google News RSS, sorted by newest
// ============================================================
function loadMainStories(feedKey) {
  var cacheKey = "main_" + feedKey;
  var cached = getCache(cacheKey);
  if (cached) {
    renderMainStories(cached);
    return;
  }

  var cat = CATEGORIES[feedKey];
  var rssUrl = cat ? cat.rss : CATEGORIES.business.rss;

  $.ajax({
    type: "GET",
    url: MUTAPA_CONFIG.RSS_API + encodeURIComponent(rssUrl),
    success: function (data) {
      if (data && data.status === "ok" && data.items && data.items.length > 0) {
        var articles = normalizeRssArticles(data.items);
        // Filter to recent articles only
        articles = articles.filter(function(a) { return isRecentArticle(a.publishedAt); });
        // Sort by date — newest first
        articles.sort(function(a, b) {
          var dateA = a.publishedAt ? new Date(a.publishedAt).getTime() : 0;
          var dateB = b.publishedAt ? new Date(b.publishedAt).getTime() : 0;
          return dateB - dateA;
        });
        setCache(cacheKey, articles);
        renderMainStories(articles);
      } else {
        $("#main-stories").html('<p class="loading-msg">No stories available at this time.</p>');
      }
    },
    error: function () {
      $("#main-stories").html('<p class="loading-msg">Unable to load stories. Please try again later.</p>');
    }
  });
}

// ============================================================
// SIDEBAR — Google News RSS (generic order, not sorted by date)
// ============================================================
var SIDEBAR_RSS = {
  business:      "https://news.google.com/rss/search?q=Zimbabwe+economy+trade+investment&hl=en&gl=US&ceid=US:en",
  technology:    "https://news.google.com/rss/search?q=Zimbabwe+tech+startup+digital&hl=en&gl=US&ceid=US:en",
  entertainment: "https://news.google.com/rss/search?q=Zimbabwe+culture+music+film+art&hl=en&gl=US&ceid=US:en",
  sports:        "https://news.google.com/rss/search?q=Zimbabwe+cricket+rugby+football+athletics&hl=en&gl=US&ceid=US:en",
  science:       "https://news.google.com/rss/search?q=Zimbabwe+environment+wildlife+conservation&hl=en&gl=US&ceid=US:en",
  health:        "https://news.google.com/rss/search?q=Zimbabwe+medical+disease+healthcare&hl=en&gl=US&ceid=US:en"
};

function loadSidebarStories(feedKey) {
  var cacheKey = "sidebar_" + feedKey;
  var cached = getCache(cacheKey);
  if (cached) {
    renderSidebarStories(cached);
    return;
  }

  var rssUrl = SIDEBAR_RSS[feedKey] || SIDEBAR_RSS.business;

  $.ajax({
    type: "GET",
    url: MUTAPA_CONFIG.RSS_API + encodeURIComponent(rssUrl),
    success: function (data) {
      if (data && data.status === "ok" && data.items && data.items.length > 0) {
        var articles = normalizeRssArticles(data.items);
        // No date sorting — keep generic RSS order
        setCache(cacheKey, articles);
        renderSidebarStories(articles);
      } else {
        $("#sidebar-stories").html('<p class="loading-msg">No additional stories.</p>');
      }
    },
    error: function () {
      $("#sidebar-stories").html('<p class="loading-msg">Unable to load stories.</p>');
    }
  });
}

// ============================================================
// Normalize articles
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
  "the patriot", "kwayedza", "umthunywa", "zimmorningpost"
];

function isLocalZimSource(source) {
  if (!source) return false;
  var s = source.toLowerCase();
  for (var i = 0; i < LOCAL_ZIM_SOURCES.length; i++) {
    if (s.indexOf(LOCAL_ZIM_SOURCES[i]) !== -1) return true;
  }
  return false;
}

// Max age for main headlines (30 days)
var MAX_ARTICLE_AGE_MS = 30 * 24 * 60 * 60 * 1000;

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

function normalizeRssArticles(items) {
  var result = [];
  for (var i = 0; i < items.length; i++) {
    var item = items[i];
    var parsed = extractSource(item.title || "");
    if (!parsed.headline) continue;
    var desc = stripHtml(getFullText(item.content, item.description));
    if (desc.length < 10) desc = "";

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

var _activeCategory = "business";

// Editorial images for sidebar portrait and inline placeholders
// Add image filenames to this array (placed in img/ folder)
var EDITORIAL_IMAGES = [
  "editorial-1.jpg",
  "editorial-2.jpg",
  "editorial-3.jpg",
  "editorial-4.jpg",
  "editorial-5.jpg"
];

function getRandomEditorialImage() {
  var idx = Math.floor(Math.random() * EDITORIAL_IMAGES.length);
  return "img/" + EDITORIAL_IMAGES[idx];
}

function initEditorialImages() {
  // Sidebar portrait image
  var portrait = document.querySelector(".editorial-portrait-img");
  if (portrait) {
    portrait.src = getRandomEditorialImage();
    portrait.onerror = function() { this.style.display = "none"; };
  }

  // Landscape image between ticker and content
  var landscape = document.querySelector(".editorial-landscape-img");
  if (landscape) {
    landscape.src = getRandomEditorialImage();
    landscape.onerror = function() { this.style.display = "none"; };
  }
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

  for (var i = 0; i < articles.length && i < 10; i++) {
    var a = articles[i];
    var rank = i + 1;
    var readTime = getReadingTime(a.description);
    var pubDate = formatDate(a.publishedAt);

    // Alternating: odd ranks (1,3,5...) on right, even (2,4,6...) on left
    var posClass = (rank % 2 === 1) ? "rank-right" : "rank-left";
    var card = $('<div class="main-article">').addClass(posClass);
    if (rank === 1) card.addClass("rank-featured");

    var link = $('<a>').attr('href', a.url || '#').attr('target', '_blank');

    // Text column
    var textCol = $('<div class="main-article-text">');
    textCol.append($('<h3 class="main-article-title">').text(a.title));

    var meta = $('<p class="main-article-meta">');
    var parts = [];
    if (a.source) parts.push(a.source);
    if (pubDate) parts.push(pubDate);
    if (readTime) parts.push(readTime);
    meta.text(parts.join(" \u00b7 "));
    // Press type marker
    if (a.isLocal) {
      meta.append($('<span class="press-marker local-press">').text("Local"));
    } else if (a.source) {
      meta.append($('<span class="press-marker foreign-press">').text("Foreign"));
    }
    textCol.append(meta);

    var desc = a.description;
    if (desc && desc.length > 250) desc = desc.substring(0, 250) + "...";
    if (desc) textCol.append($('<p class="main-article-desc">').text(desc));

    link.append(textCol);

    // Ranking number column (replaces image)
    var rankCol = $('<div class="main-article-rank">');
    rankCol.append($('<span class="rank-number">').text(rank));
    link.append(rankCol);

    card.append(link);
    container.append(card);

    // Insert editorial images after articles 3 and 7
    if (rank === 3 || rank === 7) {
      var ph = $('<div class="editorial-inline-wrap">');
      var img = $('<img class="editorial-inline-img">').attr('src', getRandomEditorialImage()).attr('alt', 'The Mutapa Times');
      img.on('error', function() { $(this).parent().hide(); });
      ph.append(img);
      container.append(ph);
    }
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

  for (var i = 0; i < articles.length && i < 15; i++) {
    var a = articles[i];
    var pubDate = formatDate(a.publishedAt);

    var item = $('<div class="sidebar-item">');
    var link = $('<a>').attr('href', a.url || '#').attr('target', '_blank');

    link.append($('<h4 class="sidebar-title">').text(a.title));

    var meta = $('<p class="sidebar-meta">');
    var parts = [];
    if (a.source) parts.push(a.source);
    if (pubDate) parts.push(pubDate);
    meta.text(parts.join(" \u00b7 "));
    if (a.isLocal) {
      meta.append($('<span class="press-marker local-press">').text("Local"));
    } else if (a.source) {
      meta.append($('<span class="press-marker foreign-press">').text("Foreign"));
    }
    link.append(meta);

    item.append(link);
    container.append(item);
  }
}
