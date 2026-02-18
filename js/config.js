/*
 * The Mutapa Times - Configuration
 * Primary: Static JSON from GNews/NewsData.io (fetched by GitHub Action)
 * Fallback: Google News RSS via rss2json.com (client-side, no key needed)
 */
var MUTAPA_CONFIG = {
  CACHE_DURATION: 30 * 60 * 1000, // 30 minutes
  RSS_API: "https://api.rss2json.com/v1/api.json?rss_url=",
  DATA_PATH: "data/"
};

// Google News RSS feed URLs (fallback when JSON data unavailable)
var NEWS_FEEDS = {
  home: "https://news.google.com/rss/search?q=Zimbabwe+economy+finance+trade&hl=en&gl=US&ceid=US:en",
  property: "https://news.google.com/rss/search?q=Zimbabwe+property+real+estate+housing+land&hl=en&gl=US&ceid=US:en",
  health: "https://news.google.com/rss/search?q=Zimbabwe+health+medical&hl=en&gl=US&ceid=US:en",
  arts: "https://news.google.com/rss/search?q=Zimbabwe+arts+culture+entertainment+music&hl=en&gl=US&ceid=US:en"
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

// Clean up GNews truncation markers like "... [2105 chars]"
function cleanText(text) {
  if (!text) return "";
  return text.replace(/\s*\[\d+ chars\]\s*$/, '').trim();
}

// Get the longest available text, cleaned up
function getFullText(content, description) {
  var c = cleanText(content);
  var d = cleanText(description);
  return c.length >= d.length ? c : d;
}

// ============================================================
// Main entry point
// ============================================================
function fetchNews(feedKey, cacheKey, pageNum) {
  var date = new Date();
  var startDate = new Date("2020-04-18");
  var volNum = Math.round((date.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24));
  var options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };

  $(".date").text(date.toLocaleDateString("en-US", options));
  $(".vol").text("Edition # " + volNum + " | Page " + pageNum);
  fetchWeather();

  // Try JSON data first (from GitHub Action), fall back to RSS
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

  // Try static JSON from GitHub Action (has images from API)
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
  var rssUrl = NEWS_FEEDS[feedKey] || NEWS_FEEDS.home;

  $.ajax({
    type: "GET",
    url: MUTAPA_CONFIG.RSS_API + encodeURIComponent(rssUrl),
    success: function (data) {
      if (data && data.status === "ok" && data.items && data.items.length > 0) {
        var articles = normalizeRssArticles(data.items);
        setCache(cacheKey, articles);
        renderArticles(articles);
      } else {
        $(".storyTitle1").text("Unable to load news");
        $(".story1").text("Please try again later.");
      }
    },
    error: function () {
      $(".storyTitle1").text("Unable to load news");
      $(".story1").text("Please try again later.");
    }
  });
}

// ============================================================
// Normalize different API formats to one standard format
// Standard: { title, url, description, image, source }
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
      source: (a.source && a.source.name) ? a.source.name : (a.source_name || "")
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
      source: parsed.source
    });
  }
  return result;
}

// ============================================================
// Unified renderer: articles[] → main grid + extra stories
// ============================================================

// Set image from API - only show real images, hide if none available
function setArticleImage(selector, imageUrl) {
  var el = $(selector);
  if (!el.length) return;

  if (imageUrl) {
    el.attr("src", imageUrl);
    el.show();
    el.off("error").on("error", function() {
      $(this).off("error");
      $(this).hide();
    });
  } else {
    el.hide();
  }
}

function renderArticles(articles) {
  if (!articles || articles.length === 0) {
    $(".storyTitle1").text("No articles found at this time");
    return;
  }

  // First 7 → main grid
  var gridMax = Math.min(articles.length, 7);
  for (var i = 0; i < gridMax; i++) {
    var a = articles[i];
    var num = i + 1;

    if (num <= 3) {
      setArticleImage(".image" + num, a.image);
    }
    $(".storyTitle" + num).text(a.title);
    $(".story" + num).text(a.description);
    $(".by" + num).text(a.source ? "Source: " + a.source : "");
    $(".a" + num).attr("href", a.url);
  }

  // Remaining → extra stories (2-column grid via CSS)
  if (articles.length > 7) {
    var container = $("#extra-stories-list");
    if (container.length) {
      for (var j = 7; j < articles.length && j < 22; j++) {
        var ex = articles[j];
        var div = $('<div class="extra-story-item">');
        var link = $('<a>').attr('href', ex.url || '#').attr('target', '_blank');
        var title = $('<h5 class="extra-story-title">').text(ex.title);
        var source = $('<p class="extra-story-source">').text(ex.source ? 'Source: ' + ex.source : '');
        link.append(title).append(source);
        div.append(link);
        container.append(div);
      }
      $("#extra-stories").show();
    }
  }
}
