/*
 * The Mutapa Times - Configuration
 * GNews-only data source (fetched by GitHub Action)
 * Fallback: Google News RSS via rss2json.com
 */
var MUTAPA_CONFIG = {
  CACHE_DURATION: 30 * 60 * 1000,
  RSS_API: "https://api.rss2json.com/v1/api.json?rss_url=",
  DATA_PATH: "data/"
};

var CATEGORIES = {
  business:      { label: "Business",      topic: "business",      rss: "https://news.google.com/rss/search?q=Zimbabwe+business+economy+finance&hl=en&gl=US&ceid=US:en" },
  technology:    { label: "Technology",     topic: "technology",    rss: "https://news.google.com/rss/search?q=Zimbabwe+technology+tech+digital&hl=en&gl=US&ceid=US:en" },
  entertainment: { label: "Entertainment",  topic: "entertainment", rss: "https://news.google.com/rss/search?q=Zimbabwe+entertainment+music+arts+culture&hl=en&gl=US&ceid=US:en" },
  sports:        { label: "Sports",         topic: "sports",        rss: "https://news.google.com/rss/search?q=Zimbabwe+sports+cricket+football+rugby&hl=en&gl=US&ceid=US:en" },
  science:       { label: "Science",        topic: "science",       rss: "https://news.google.com/rss/search?q=Zimbabwe+science+research+environment&hl=en&gl=US&ceid=US:en" },
  health:        { label: "Health",         topic: "health",        rss: "https://news.google.com/rss/search?q=Zimbabwe+health+medical&hl=en&gl=US&ceid=US:en" }
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
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Rime fog",
    51: "Light drizzle", 53: "Drizzle", 55: "Heavy drizzle",
    61: "Light rain", 63: "Rain", 65: "Heavy rain",
    71: "Light snow", 73: "Snow", 75: "Heavy snow",
    80: "Light showers", 81: "Showers", 82: "Heavy showers",
    95: "Thunderstorm", 96: "Thunderstorm", 99: "Thunderstorm"
  };
  return descriptions[code] || "Unknown";
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
    el.find(".weather-temp").text(Math.round(weather.temperature) + "\u00B0C");
    el.find(".weather-desc").text(getWeatherDescription(weather.weathercode));
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

// Reading time estimate from text length
function getReadingTime(text) {
  if (!text) return "1 min read";
  var words = text.split(/\s+/).length;
  var mins = Math.max(1, Math.ceil(words / 200));
  return mins + " min read";
}

// Format publish date
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
  var date = new Date();
  var startDate = new Date("2020-04-18");
  var volNum = Math.round((date.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24));
  var options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };

  $(".date").text(date.toLocaleDateString("en-US", options));
  $(".vol").text("Edition # " + volNum);
  fetchWeather();

  loadContent(feedKey);
}

// ============================================================
// Content loading: JSON first, RSS fallback
// ============================================================
function loadContent(feedKey) {
  var cacheKey = "content_" + feedKey;
  var cached = getCache(cacheKey);
  if (cached) {
    renderArticles(cached);
    return;
  }

  $.ajax({
    type: "GET",
    url: MUTAPA_CONFIG.DATA_PATH + feedKey + ".json",
    dataType: "json",
    success: function (data) {
      if (data && data.articles && data.articles.length > 0) {
        var articles = normalizeJsonArticles(data.articles);
        setCache(cacheKey, articles);
        renderArticles(articles);
      } else {
        loadFromRss(feedKey);
      }
    },
    error: function () {
      loadFromRss(feedKey);
    }
  });
}

function loadFromRss(feedKey) {
  var cacheKey = "content_" + feedKey;
  var cat = CATEGORIES[feedKey];
  var rssUrl = cat ? cat.rss : CATEGORIES.business.rss;

  $.ajax({
    type: "GET",
    url: MUTAPA_CONFIG.RSS_API + encodeURIComponent(rssUrl),
    success: function (data) {
      if (data && data.status === "ok" && data.items && data.items.length > 0) {
        var articles = normalizeRssArticles(data.items);
        setCache(cacheKey, articles);
        renderArticles(articles);
      } else {
        $("#news-grid").html('<p style="text-align:center;padding:40px;color:#999;">Unable to load news. Please try again later.</p>');
      }
    },
    error: function () {
      $("#news-grid").html('<p style="text-align:center;padding:40px;color:#999;">Unable to load news. Please try again later.</p>');
    }
  });
}

// ============================================================
// Normalize to standard: { title, url, description, image, source, publishedAt }
// ============================================================
function normalizeJsonArticles(articles) {
  var result = [];
  for (var i = 0; i < articles.length; i++) {
    var a = articles[i];
    result.push({
      title: a.title || "",
      url: a.url || a.link || "",
      description: getFullText(a.content, a.description),
      image: a.image || a.image_url || "",
      source: (a.source && a.source.name) ? a.source.name : (a.source_name || ""),
      publishedAt: a.publishedAt || a.pubDate || ""
    });
  }
  return result;
}

function normalizeRssArticles(items) {
  var result = [];
  for (var i = 0; i < items.length; i++) {
    var item = items[i];
    var parsed = extractSource(item.title || "");
    if (!parsed.headline) continue;
    var desc = stripHtml(getFullText(item.content, item.description));
    if (desc.length < 10) desc = "Click to read the full article.";
    var image = item.thumbnail || (item.enclosure && item.enclosure.link) || "";

    result.push({
      title: parsed.headline,
      url: item.link || "",
      description: desc,
      image: image,
      source: parsed.source,
      publishedAt: item.pubDate || ""
    });
  }
  return result;
}

// ============================================================
// Renderer: two-column card grid
// ============================================================
function renderArticles(articles) {
  var grid = $("#news-grid");
  if (!grid.length) return;
  grid.empty();

  if (!articles || articles.length === 0) {
    grid.html('<p style="text-align:center;padding:40px;color:#999;">No articles found at this time.</p>');
    return;
  }

  for (var i = 0; i < articles.length && i < 20; i++) {
    var a = articles[i];
    var readTime = getReadingTime(a.description);
    var pubDate = formatDate(a.publishedAt);

    var card = $('<div class="article-card">');
    var link = $('<a>').attr('href', a.url || '#').attr('target', '_blank');

    // Image
    if (a.image) {
      var imgEl = $('<img class="article-image">').attr('src', a.image);
      imgEl.on('error', function() { $(this).hide(); });
      link.append(imgEl);
    }

    // Headline
    link.append($('<h4 class="article-title">').text(a.title));

    // Meta line: source + date + reading time
    var meta = $('<p class="article-meta">');
    var parts = [];
    if (a.source) parts.push(a.source);
    if (pubDate) parts.push(pubDate);
    parts.push(readTime);
    meta.text(parts.join(" · "));
    link.append(meta);

    // Description
    var desc = a.description;
    if (desc && desc.length > 200) desc = desc.substring(0, 200) + "...";
    link.append($('<p class="article-desc">').text(desc));

    card.append(link);
    grid.append(card);
  }
}
