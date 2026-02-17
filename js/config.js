/*
 * The Mutapa Times - Configuration
 *
 * SETUP: Get your free API key at https://gnews.io
 * Then replace YOUR_API_KEY_HERE below with your key.
 */
var MUTAPA_CONFIG = {
  GNEWS_API_KEY: "65a557d301d31bfc563f971e515eceb5",
  CACHE_DURATION: 30 * 60 * 1000 // 30 minutes
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

// Show message when API key is not configured
function showApiKeyMessage() {
  $(".storyTitle1").text("Welcome to The Mutapa Times");
  $(".story1").html(
    'To get started, sign up for a free API key at ' +
    '<a href="https://gnews.io" target="_blank">gnews.io</a> ' +
    'and add it to <code>js/config.js</code>'
  );
}

// Shared news fetching function
function fetchNews(searchQuery, cacheKey, pageNum, insertDataFn) {
  var apiKey = MUTAPA_CONFIG.GNEWS_API_KEY;
  var date = new Date();
  var startDate = new Date("2020-04-18");
  var volNum = Math.round((date.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24));
  var options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };

  $(".date").text(date.toLocaleDateString("en-US", options));
  $(".vol").text("Edition # " + volNum + " | Page " + pageNum);

  fetchWeather();

  if (apiKey === "YOUR_API_KEY_HERE") {
    showApiKeyMessage();
    return;
  }

  var cached = getCache(cacheKey);
  if (cached) {
    insertDataFn(cached);
    return;
  }

  $.ajax({
    type: "GET",
    url: "https://gnews.io/api/v4/search?q=" + encodeURIComponent(searchQuery) +
      "&lang=en&max=10&apikey=" + apiKey,
    success: function (data) {
      setCache(cacheKey, data);
      insertDataFn(data);
    },
    error: function () {
      $(".storyTitle1").text("Unable to load news");
      $(".story1").text("Please check your API key or try again later.");
    }
  });
}

// Standard article renderer used by all pages
function renderArticles(data) {
  var count = 1;
  if (!data.articles || data.articles.length === 0) {
    $(".storyTitle1").text("No articles found at this time");
    return;
  }
  for (var i = 0; i < data.articles.length && count <= 7; i++) {
    var news = data.articles[i];
    if (news.description) {
      if (count < 4 && news.image) {
        $(".image" + count).attr("src", news.image);
      }
      $(".storyTitle" + count).text(news.title);
      $(".story" + count).text(news.description);
      $(".by" + count).text("Source: " + news.source.name);
      $(".a" + count).attr("href", news.url);
      count++;
    }
  }
}
