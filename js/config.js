/*
 * The Mutapa Times - Configuration
 * Main stories: GNews API via static JSON (fetched hourly by GitHub Action)
 * Extra stories: Google News RSS via rss2json.com (client-side, no key needed)
 */
var MUTAPA_CONFIG = {
  CACHE_DURATION: 30 * 60 * 1000, // 30 minutes
  RSS_API: "https://api.rss2json.com/v1/api.json?rss_url=",
  DATA_PATH: "data/"
};

// Google News RSS feed URLs for extra stories
var NEWS_FEEDS = {
  home: "https://news.google.com/rss/search?q=Zimbabwe+business+economy&hl=en&gl=US&ceid=US:en",
  business: "https://news.google.com/rss/search?q=Zimbabwe+business+economy&hl=en&gl=US&ceid=US:en",
  politics: "https://news.google.com/rss/search?q=Zimbabwe+politics+government&hl=en&gl=US&ceid=US:en",
  health: "https://news.google.com/rss/search?q=Zimbabwe+health&hl=en&gl=US&ceid=US:en",
  arts: "https://news.google.com/rss/search?q=Zimbabwe+arts+culture+music&hl=en&gl=US&ceid=US:en",
  sport: "https://news.google.com/rss/search?q=Zimbabwe+sport+cricket+football+rugby&hl=en&gl=US&ceid=US:en"
};

// Zimbabwe cities for weather
var WEATHER_CITIES = [
  { id: "harare", name: "Harare", lat: -17.83, lon: 31.05 },
  { id: "bulawayo", name: "Bulawayo", lat: -20.13, lon: 28.63 },
  { id: "mutare", name: "Mutare", lat: -18.97, lon: 32.67 },
  { id: "vicfalls", name: "Victoria Falls", lat: -17.93, lon: 25.83 },
  { id: "gweru", name: "Gweru", lat: -19.45, lon: 29.82 }
];

// WMO weather code descriptions
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

// Fetch and display weather for all Zimbabwe cities
function fetchWeather() {
  WEATHER_CITIES.forEach(function (city) {
    var cacheKey = "weather_" + city.id;
    var cached = getCache(cacheKey);
    if (cached) {
      displayCityWeather(city.id, cached);
      return;
    }
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

// Extract source name from Google News title format "Headline - Source Name"
function extractSource(title) {
  var lastDash = title.lastIndexOf(" - ");
  if (lastDash > 0 && lastDash > title.length * 0.3) {
    return {
      headline: title.substring(0, lastDash),
      source: title.substring(lastDash + 3)
    };
  }
  return { headline: title, source: "" };
}

// Strip HTML tags from a string
function stripHtml(html) {
  var tmp = document.createElement("div");
  tmp.innerHTML = html;
  return tmp.textContent || tmp.innerText || "";
}

// Simple hash for deterministic placeholder images
function hashCode(str) {
  var hash = 0;
  for (var i = 0; i < str.length; i++) {
    hash = ((hash << 5) - hash) + str.charCodeAt(i);
    hash |= 0;
  }
  return Math.abs(hash);
}

// ============================================================
// Main entry point - called by each page's JS
// ============================================================
function fetchNews(feedKey, cacheKey, pageNum) {
  var date = new Date();
  var startDate = new Date("2020-04-18");
  var volNum = Math.round((date.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24));
  var options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };

  $(".date").text(date.toLocaleDateString("en-US", options));
  $(".vol").text("Edition # " + volNum + " | Page " + pageNum);

  fetchWeather();

  // Load GNews static data for main grid (with images)
  loadGnewsData(feedKey);

  // Load Google News RSS for extra stories below
  loadExtraStories(feedKey);
}

// ============================================================
// GNews static JSON (main grid with images)
// ============================================================
function loadGnewsData(feedKey) {
  var cacheKey = "gnews_" + feedKey;
  var cached = getCache(cacheKey);
  if (cached) {
    renderGnewsArticles(cached);
    return;
  }

  $.ajax({
    type: "GET",
    url: MUTAPA_CONFIG.DATA_PATH + feedKey + ".json",
    dataType: "json",
    success: function (data) {
      if (data && data.articles && data.articles.length > 0) {
        setCache(cacheKey, data);
        renderGnewsArticles(data);
      } else {
        loadRssFallback(feedKey);
      }
    },
    error: function () {
      loadRssFallback(feedKey);
    }
  });
}

// Fallback: if GNews data isn't available yet, use RSS for main grid
function loadRssFallback(feedKey) {
  var cacheKey = "rss_main_" + feedKey;
  var cached = getCache(cacheKey);
  if (cached) {
    renderRssArticles(cached);
    return;
  }

  var rssUrl = NEWS_FEEDS[feedKey] || NEWS_FEEDS.home;
  $.ajax({
    type: "GET",
    url: MUTAPA_CONFIG.RSS_API + encodeURIComponent(rssUrl),
    success: function (data) {
      if (data && data.status === "ok") {
        setCache(cacheKey, data);
        renderRssArticles(data);
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
// Google News RSS (extra stories section)
// ============================================================
function loadExtraStories(feedKey) {
  var cacheKey = "rss_extra_" + feedKey;
  var cached = getCache(cacheKey);
  if (cached) {
    renderExtraStories(cached);
    return;
  }

  var rssUrl = NEWS_FEEDS[feedKey] || NEWS_FEEDS.home;
  $.ajax({
    type: "GET",
    url: MUTAPA_CONFIG.RSS_API + encodeURIComponent(rssUrl),
    success: function (data) {
      if (data && data.status === "ok") {
        setCache(cacheKey, data);
        renderExtraStories(data);
      }
    }
  });
}

// ============================================================
// Renderers
// ============================================================

// Render GNews articles into the main newspaper grid (with images)
function renderGnewsArticles(data) {
  if (!data.articles || data.articles.length === 0) {
    $(".storyTitle1").text("No articles found at this time");
    return;
  }

  var count = 1;
  for (var i = 0; i < data.articles.length && count <= 7; i++) {
    var article = data.articles[i];
    var headline = article.title || "";
    // Use full content first, fall back to description
    var desc = article.content || article.description || "";
    var image = article.image || "";
    var source = article.source ? article.source.name : "";
    var url = article.url || "";

    if (headline) {
      if (count < 4) {
        if (image) {
          $(".image" + count).attr("src", image);
          // Add error handler for broken images
          $(".image" + count).on("error", function() {
            var seed = "mutapa-" + hashCode(headline);
            $(this).attr("src", "https://picsum.photos/seed/" + seed + "/600/400");
            $(this).off("error");
          });
        } else {
          var seed = "mutapa-" + hashCode(headline);
          $(".image" + count).attr("src", "https://picsum.photos/seed/" + seed + "/600/400");
        }
      }
      $(".storyTitle" + count).text(headline);
      $(".story" + count).text(desc);
      $(".by" + count).text(source ? "Source: " + source : "");
      $(".a" + count).attr("href", url);
      count++;
    }
  }
}

// Render RSS articles into the main grid (fallback when GNews data unavailable)
function renderRssArticles(data) {
  var count = 1;
  if (!data.items || data.items.length === 0) {
    $(".storyTitle1").text("No articles found at this time");
    return;
  }
  for (var i = 0; i < data.items.length && count <= 7; i++) {
    var item = data.items[i];
    var parsed = extractSource(item.title || "");
    var desc = stripHtml(item.content || item.description || "");
    if (desc.length < 10) {
      desc = "Click to read the full article.";
    }
    var image = item.thumbnail || (item.enclosure && item.enclosure.link) || "";

    if (parsed.headline) {
      if (count < 4) {
        if (image) {
          $(".image" + count).attr("src", image);
          $(".image" + count).on("error", function() {
            var seed = "mutapa-" + hashCode(parsed.headline);
            $(this).attr("src", "https://picsum.photos/seed/" + seed + "/600/400");
            $(this).off("error");
          });
        } else {
          var seed = "mutapa-" + hashCode(parsed.headline);
          $(".image" + count).attr("src", "https://picsum.photos/seed/" + seed + "/600/400");
        }
      }
      $(".storyTitle" + count).text(parsed.headline);
      $(".story" + count).text(desc);
      $(".by" + count).text(parsed.source ? "Source: " + parsed.source : "");
      $(".a" + count).attr("href", item.link);
      count++;
    }
  }
}

// Render extra stories from RSS below the main grid
function renderExtraStories(data) {
  var container = $("#extra-stories-list");
  if (!container.length || !data.items || data.items.length === 0) return;

  // Collect main grid headlines for deduplication
  var mainHeadlines = [];
  for (var j = 1; j <= 7; j++) {
    var h = $(".storyTitle" + j).text().toLowerCase().trim();
    if (h && h.length > 5) mainHeadlines.push(h.substring(0, 40));
  }

  var count = 0;
  for (var i = 0; i < data.items.length && count < 15; i++) {
    var item = data.items[i];
    var parsed = extractSource(item.title || "");
    if (!parsed.headline) continue;

    // Skip if headline overlaps with a main grid article
    var lower = parsed.headline.toLowerCase().trim();
    var isDupe = false;
    for (var k = 0; k < mainHeadlines.length; k++) {
      if (lower.indexOf(mainHeadlines[k]) !== -1 || mainHeadlines[k].indexOf(lower.substring(0, 40)) !== -1) {
        isDupe = true;
        break;
      }
    }
    if (isDupe) continue;

    var div = $('<div class="extra-story-item">');
    var link = $('<a>').attr('href', item.link || '#').attr('target', '_blank');
    var title = $('<h5 class="extra-story-title">').text(parsed.headline);
    var source = $('<p class="extra-story-source">').text(parsed.source ? 'Source: ' + parsed.source : '');
    link.append(title).append(source);
    div.append(link);
    container.append(div);
    count++;
  }

  if (count > 0) {
    $("#extra-stories").show();
  }
}
