/*
 * The Mutapa Times - Configuration
 * Uses Google News RSS feeds via rss2json.com - no API key needed!
 */
var MUTAPA_CONFIG = {
  CACHE_DURATION: 30 * 60 * 1000, // 30 minutes
  RSS_API: "https://api.rss2json.com/v1/api.json?rss_url="
};

// Google News RSS feed URLs for each category
var NEWS_FEEDS = {
  home: "https://news.google.com/rss/search?q=Zimbabwe&hl=en&gl=US&ceid=US:en",
  business: "https://news.google.com/rss/search?q=Zimbabwe+business+economy&hl=en&gl=US&ceid=US:en",
  politics: "https://news.google.com/rss/search?q=Zimbabwe+politics+government&hl=en&gl=US&ceid=US:en",
  health: "https://news.google.com/rss/search?q=Zimbabwe+health&hl=en&gl=US&ceid=US:en"
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

// Shared news fetching function using Google News RSS via rss2json
function fetchNews(feedKey, cacheKey, pageNum, insertDataFn) {
  var date = new Date();
  var startDate = new Date("2020-04-18");
  var volNum = Math.round((date.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24));
  var options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };

  $(".date").text(date.toLocaleDateString("en-US", options));
  $(".vol").text("Edition # " + volNum + " | Page " + pageNum);

  fetchWeather();

  var cached = getCache(cacheKey);
  if (cached) {
    insertDataFn(cached);
    return;
  }

  var rssUrl = NEWS_FEEDS[feedKey] || NEWS_FEEDS.home;

  $.ajax({
    type: "GET",
    url: MUTAPA_CONFIG.RSS_API + encodeURIComponent(rssUrl),
    success: function (data) {
      if (data && data.status === "ok") {
        setCache(cacheKey, data);
        insertDataFn(data);
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

// Standard article renderer used by all pages
function renderArticles(data) {
  var count = 1;
  if (!data.items || data.items.length === 0) {
    $(".storyTitle1").text("No articles found at this time");
    return;
  }
  for (var i = 0; i < data.items.length && count <= 7; i++) {
    var item = data.items[i];
    var parsed = extractSource(item.title || "");
    var desc = stripHtml(item.description || item.content || "");
    // Clean up Google News description format
    if (desc.length < 10) {
      desc = "Click to read the full article.";
    }
    var image = item.thumbnail || (item.enclosure && item.enclosure.link) || "";

    if (parsed.headline) {
      if (count < 4 && image) {
        $(".image" + count).attr("src", image);
      }
      $(".storyTitle" + count).text(parsed.headline);
      $(".story" + count).text(desc);
      $(".by" + count).text(parsed.source ? "Source: " + parsed.source : "");
      $(".a" + count).attr("href", item.link);
      count++;
    }
  }
}
