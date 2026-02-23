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

// Stored article data for category filtering
var _allMainArticles = [];
var _allSidebarArticles = [];
var _activeCategory = "all";

// Multiple RSS feeds to pull from — broad, less selective, prioritizing recency
var MAIN_RSS_FEEDS = [
  "https://news.google.com/rss/search?q=Zimbabwe&hl=en&gl=US&ceid=US:en",
  "https://news.google.com/rss/search?q=Zimbabwe+news+today&hl=en&gl=US&ceid=US:en",
  "https://news.google.com/rss/search?q=Harare+OR+Bulawayo+OR+Mutare&hl=en&gl=US&ceid=US:en",
  "https://news.google.com/rss/search?q=Zimbabwe+politics+government+economy&hl=en&gl=US&ceid=US:en",
  "https://news.google.com/rss/search?q=Zimbabwe+health+education+sport+crime&hl=en&gl=US&ceid=US:en",
  "https://news.google.com/rss/search?q=Zimbabwe+mining+agriculture+tourism&hl=en&gl=US&ceid=US:en",
  "https://news.google.com/rss/search?q=site:zimlive.com+OR+site:newsday.co.zw+OR+site:herald.co.zw+OR+site:bulawayo24.com+OR+site:263chat.com&hl=en&gl=US&ceid=US:en",
  "https://news.google.com/rss/search?q=site:pindula.co.zw+OR+site:nehanda radio+OR+site:newzimbabwe.com+OR+site:thezimbabwemail.com&hl=en&gl=US&ceid=US:en"
];

// Sidebar feeds — more local-focused
var SIDEBAR_RSS_FEEDS = [
  "https://news.google.com/rss/search?q=Zimbabwe+local+news&hl=en&gl=US&ceid=US:en",
  "https://news.google.com/rss/search?q=Zimbabwe+business+sports+entertainment+health&hl=en&gl=US&ceid=US:en",
  "https://news.google.com/rss/search?q=Harare+Bulawayo+Gweru+Masvingo+Mutare+Chitungwiza&hl=en&gl=US&ceid=US:en",
  "https://news.google.com/rss/search?q=Zimbabwe+crime+court+police&hl=en&gl=US&ceid=US:en",
  "https://news.google.com/rss/search?q=Zimbabwe+culture+music+festival+education&hl=en&gl=US&ceid=US:en"
];

// Spotlight feeds — multiple targeted searches to ensure enough reputable results
var SPOTLIGHT_RSS_FEEDS = [
  "https://news.google.com/rss/search?q=Zimbabwe+site:bbc.com+OR+site:reuters.com+OR+site:nytimes.com+OR+site:theguardian.com+OR+site:aljazeera.com+OR+site:bloomberg.com+OR+site:apnews.com+OR+site:cnn.com&hl=en&gl=US&ceid=US:en",
  "https://news.google.com/rss/search?q=Zimbabwe+site:voanews.com+OR+site:africanews.com+OR+site:france24.com+OR+site:dw.com+OR+site:news24.com+OR+site:dailymaverick.co.za+OR+site:allafrica.com&hl=en&gl=US&ceid=US:en",
  "https://news.google.com/rss/search?q=%22Southern+Africa%22+OR+SADC+OR+Zimbabwe+site:reuters.com+OR+site:bbc.com+OR+site:theguardian.com+OR+site:aljazeera.com&hl=en&gl=US&ceid=US:en"
];

// Reputable sources for spotlight matching
var REPUTABLE_SOURCES = [
  // Major international wire services & broadcasters
  "bbc", "reuters", "new york times", "nytimes", "the guardian", "guardian",
  "al jazeera", "aljazeera", "financial times", "ft.com", "the economist",
  "bloomberg", "associated press", "ap news", "apnews", "washington post",
  "cnn", "sky news", "the telegraph", "the independent", "france 24",
  "dw", "deutsche welle", "npr", "pbs", "abc news", "time magazine",
  "foreign policy", "the conversation",
  // International outlets with strong Africa desks
  "voa", "voice of america", "rfi", "africanews",
  // Reputable African outlets
  "allafrica", "all africa", "daily maverick", "mail & guardian",
  "news24", "the east african", "sabc", "nation africa", "the citizen",
  "eyewitness news", "iol", "timeslive", "sunday times",
  // Asia-Pacific
  "south china morning post", "scmp"
];

function isReputableSource(source) {
  if (!source) return false;
  var s = source.toLowerCase();
  for (var i = 0; i < REPUTABLE_SOURCES.length; i++) {
    if (s.indexOf(REPUTABLE_SOURCES[i]) !== -1) return true;
  }
  return false;
}

// Infer article category from headline keywords
// Primary categories (business, politics, policy, tech) listed first — editorial focus
var CATEGORY_RULES = [
  { tag: "Business", words: ["economy", "economic", "business", "trade", "inflation", "currency", "dollar", "market", "stock", "bank", "finance", "investment", "gdp", "revenue", "profit", "company", "mining", "export", "import", "tax", "budget", "debt", "imf", "reserve", "industry", "commerce", "entrepreneur"] },
  { tag: "Politics", words: ["politics", "political", "election", "parliament", "government", "minister", "president", "opposition", "zanu", "mdc", "party", "vote", "campaign", "diplomat", "embassy", "mnangagwa", "chamisa", "senator", "cabinet", "coalition"] },
  { tag: "Policy", words: ["policy", "regulation", "reform", "legislation", "bill", "amendment", "sanctions", "sadc", "african union", "treaty", "compliance", "governance", "mandate", "directive", "statutory"] },
  { tag: "Tech", words: ["technology", "digital", "internet", "mobile", "app", "startup", "cyber", "software", "ai ", "telecom", "econet", "telecash", "fintech", "innovation"] },
  { tag: "Health", words: ["health", "hospital", "disease", "covid", "cholera", "malaria", "medical", "doctor", "vaccine", "outbreak", "patient", "clinic", "drug", "treatment", "who", "death toll", "epidemic"] },
  { tag: "Crime", words: ["arrest", "police", "court", "murder", "crime", "prison", "jail", "suspect", "charged", "robbery", "fraud", "corruption", "trial", "convicted", "shooting", "stolen", "detained", "bail"] },
  { tag: "Sport", words: ["cricket", "football", "soccer", "rugby", "match", "score", "championship", "tournament", "athlete", "stadium", "coach", "team", "league", "olympic", "fifa", "icc", "qualifier", "wicket", "goal"] },
  { tag: "Culture", words: ["music", "film", "artist", "culture", "festival", "concert", "album", "entertainment", "award", "celebrity", "dance", "theatre", "theater"] },
  { tag: "Environment", words: ["climate", "drought", "flood", "wildlife", "conservation", "environment", "cyclone", "rainfall", "dam", "water crisis", "deforestation", "national park", "safari", "poach"] },
  { tag: "Education", words: ["school", "university", "student", "teacher", "education", "exam", "graduate", "scholarship", "literacy"] }
];

// Primary categories — editorial focus areas for the business & intelligence service
var PRIMARY_CATEGORIES = ["Business", "Politics", "Policy", "Tech"];

function inferCategory(title) {
  if (!title) return "";
  var t = " " + title.toLowerCase() + " ";
  for (var i = 0; i < CATEGORY_RULES.length; i++) {
    var rule = CATEGORY_RULES[i];
    for (var j = 0; j < rule.words.length; j++) {
      if (t.indexOf(rule.words[j]) !== -1) return rule.tag;
    }
  }
  return "";
}

// Max age for spotlight articles (30 days — reputable sources only)
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
  var words = Math.round(totalChars / 5);
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
    var diffMins = Math.floor(diffMs / (1000 * 60));
    var diffHrs = Math.floor(diffMs / (1000 * 60 * 60));
    if (diffMins < 5) return "Just now";
    if (diffMins < 60) return diffMins + "m ago";
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

function isBreakingRecent(dateStr) {
  if (!dateStr) return false;
  try {
    var d = new Date(dateStr);
    if (isNaN(d.getTime())) return false;
    return (Date.now() - d.getTime()) < 60 * 60 * 1000; // < 1 hour
  } catch (e) { return false; }
}

// ============================================================
// Main entry point
// ============================================================
function fetchNews() {
  var date = new Date();
  var options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };

  $(".date").text(date.toLocaleDateString("en-US", options));
  var timeStr = date.toLocaleTimeString("en-US", { hour: '2-digit', minute: '2-digit' });
  $(".vol").text("Updated " + timeStr);

  // Zimbabwe time in header
  updateZimbabweTime();
  setInterval(updateZimbabweTime, 60000);

  fetchWeather();

  // Duplicate weather cities for infinite ticker scroll
  var ticker = document.querySelector('.weather-ticker');
  if (ticker) {
    var items = ticker.innerHTML;
    ticker.innerHTML = items + items;
  }

  // Init editorial images (sidebar portrait + landscape)
  initEditorialImages();

  // Personalisation touches (proverb, location, on this day)
  initPersonalisation();

  // Load AI descriptions first, then start loading stories
  loadAiDescriptions(function() {
    loadMainStories();
    loadSpotlightStories();
    loadSidebarStories();
  });

  // Category filter chip clicks
  $(".category-filter").on("click", ".category-chip", function() {
    $(".category-chip").removeClass("active");
    $(this).addClass("active");
    _activeCategory = $(this).data("category");
    filterByCategory(_activeCategory);
  });
}

function filterByCategory(category) {
  var mainFiltered = _allMainArticles;
  var sidebarFiltered = _allSidebarArticles;

  if (category !== "all") {
    mainFiltered = _allMainArticles.filter(function(a) {
      return inferCategory(a.title) === category;
    });
    sidebarFiltered = _allSidebarArticles.filter(function(a) {
      return inferCategory(a.title) === category;
    });
  }

  renderMainStories(mainFiltered);
  renderSidebarStories(sidebarFiltered);
}

// ============================================================
// MAIN STORIES — multiple RSS feeds combined, sorted by newest
// ============================================================
function loadMainStories() {
  var cacheKey = "main_all";
  var cached = getCache(cacheKey);
  if (cached) {
    _allMainArticles = cached;
    renderMainStories(cached);
    return;
  }

  var allArticles = [];
  var completed = 0;
  var total = MAIN_RSS_FEEDS.length;

  var _mainTimeout = setTimeout(function() {
    if (document.querySelector('#main-stories .loading-msg')) {
      document.querySelector('#main-stories').innerHTML =
        '<p class="loading-msg">We couldn\u2019t load stories right now. Please refresh the page to try again.</p>';
    }
  }, 15000);

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
          clearTimeout(_mainTimeout);
          // All feeds loaded — deduplicate, filter by date, remove topic dupes, sort
          allArticles = deduplicateArticles(allArticles);
          allArticles = allArticles.filter(function(a) { return isRecentArticle(a.publishedAt); });
          allArticles = deduplicateByTopic(allArticles, 0.4);
          allArticles.sort(function(a, b) {
            var aVerified = isReputableSource(a.source) ? 1 : 0;
            var bVerified = isReputableSource(b.source) ? 1 : 0;
            if (bVerified !== aVerified) return bVerified - aVerified;
            var dateA = a.publishedAt ? new Date(a.publishedAt).getTime() : 0;
            var dateB = b.publishedAt ? new Date(b.publishedAt).getTime() : 0;
            return dateB - dateA;
          });
          setCache(cacheKey, allArticles);
          _allMainArticles = allArticles;
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
    _allSidebarArticles = cached;
    renderSidebarStories(cached);
    return;
  }

  var allArticles = [];
  var completed = 0;
  var total = SIDEBAR_RSS_FEEDS.length;

  var _sidebarTimeout = setTimeout(function() {
    if (document.querySelector('#sidebar-stories .loading-msg')) {
      document.querySelector('#sidebar-stories').innerHTML =
        '<p class="loading-msg">Unable to load additional stories. Please refresh to try again.</p>';
    }
  }, 15000);

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
          clearTimeout(_sidebarTimeout);
          allArticles = deduplicateArticles(allArticles);
          // Filter — Live on the Ground allows up to 2 years of local stories
          allArticles = allArticles.filter(function(a) {
            if (!a.publishedAt) return false;
            try {
              var d = new Date(a.publishedAt);
              if (isNaN(d.getTime())) return false;
              return (Date.now() - d.getTime()) < SIDEBAR_MAX_AGE_MS;
            } catch (e) { return false; }
          });
          // Sort sidebar: verified sources first, then by recency
          allArticles.sort(function(a, b) {
            var aVerified = isReputableSource(a.source) ? 1 : 0;
            var bVerified = isReputableSource(b.source) ? 1 : 0;
            if (bVerified !== aVerified) return bVerified - aVerified;
            var dateA = a.publishedAt ? new Date(a.publishedAt).getTime() : 0;
            var dateB = b.publishedAt ? new Date(b.publishedAt).getTime() : 0;
            return dateB - dateA;
          });
          setCache(cacheKey, allArticles);
          _allSidebarArticles = allArticles;
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
  "heraldonline", "chronicle", "newsday", "daily news",
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

// Max age for main feed headlines (14 days — tighter for recency)
var MAX_ARTICLE_AGE_MS = 14 * 24 * 60 * 60 * 1000;

// Max age for Live on the Ground / sidebar (14 days — keep content fresh)
var SIDEBAR_MAX_AGE_MS = 14 * 24 * 60 * 60 * 1000;

function isRecentArticle(dateStr) {
  if (!dateStr) return false;
  try {
    var d = new Date(dateStr);
    if (isNaN(d.getTime())) return false;
    // Hard floor: nothing before 2025
    if (d.getFullYear() < 2025) return false; // hard floor — no archival content
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

// AI-generated descriptions lookup (loaded from data/rss_descriptions.json)
var _aiDescriptions = {};

// Track spotlight article URLs to avoid repeating them in main/sidebar feeds
var _spotlightUrls = {};

function loadAiDescriptions(callback) {
  $.ajax({
    type: "GET",
    url: MUTAPA_CONFIG.DATA_PATH + "rss_descriptions.json",
    dataType: "json",
    success: function(data) {
      if (data && typeof data === "object") {
        _aiDescriptions = data;
      }
    },
    complete: function() {
      // Always fire callback — stories load even if descriptions file fails
      if (callback) callback();
    }
  });
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

    // Fall back to AI-generated description if available
    var url = item.link || "";
    if (!desc && url && _aiDescriptions[url]) {
      desc = _aiDescriptions[url];
    }

    result.push({
      title: parsed.headline,
      url: url,
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
  }).map(function(w) {
    // Basic stemming to catch "detained/detention", "arrested/arrest", etc.
    return w.replace(/(tion|sion|ment|ness|ity|ies|ing|ated|ised|ized|ened|ered|ling|ally|ful|less|able|ible|ous|ive|ant|ent|ure)$/, '')
            .replace(/(ed|er|ly|es|al|en)$/, '')
            .replace(/s$/, '');
  }).filter(function(w) { return w.length > 2; });
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

function deduplicateByTopic(articles, threshold) {
  var thresh = threshold || 0.4;
  var result = [];
  var topicCache = [];
  for (var i = 0; i < articles.length; i++) {
    var words = getTopicWords(articles[i].title);
    var isDupe = false;
    for (var j = 0; j < topicCache.length; j++) {
      if (topicOverlap(words, topicCache[j]) > thresh) {
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
  { src: "break-1.jpg", caption: "Business, intelligence \u2014 building the Zimbabwe of tomorrow" },
  { src: "break-2.jpg", caption: "Staying connected, staying informed \u2014 powering Zimbabwe\u2019s future" },
  { src: "break-3.jpg", caption: "Enterprise, ambition \u2014 the spirit of a nation rising" },
  { src: "break-4.jpg", caption: "Bridging distance, bridging diaspora \u2014 one story at a time" }
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
    var shareText = title + '\n\n\ud83c\uddff\ud83c\uddfc Stay informed on Zimbabwe \u2014 follow @MutapaTimes for daily news, analysis & more.\n\ud83d\udcf0 https://www.mutapatimes.com';
    var shareData = {
      title: title + ' | The Mutapa Times',
      text: shareText,
      url: url
    };
    if (navigator.share) {
      navigator.share(shareData).catch(function(err) {
        if (err.name !== 'AbortError') console.warn('Share failed:', err);
      });
    } else {
      // Clipboard fallback — copy full formatted text
      var clipText = title + '\n' + url + '\n\n\ud83c\uddff\ud83c\uddfc Stay informed on Zimbabwe \u2014 follow @MutapaTimes for daily news, analysis & more.\n\ud83d\udcf0 https://www.mutapatimes.com';
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(clipText);
      } else {
        var temp = document.createElement('textarea');
        temp.value = clipText;
        document.body.appendChild(temp);
        temp.select();
        document.execCommand('copy');
        document.body.removeChild(temp);
      }
      var original = btn.html();
      btn.text('Copied!');
      setTimeout(function() { btn.html(original); }, 1500);
    }
  });
  return btn;
}

var WHATSAPP_ICON_SVG = '<svg viewBox="0 0 24 24" width="12" height="12" fill="currentColor"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>';

var IMAGE_SHARE_ICON_SVG = '<svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>';

function createWhatsAppBtn(title, url) {
  var btn = $('<button class="whatsapp-btn" title="Share on WhatsApp">').html(WHATSAPP_ICON_SVG);
  btn.on('click', function(e) {
    e.preventDefault();
    e.stopPropagation();
    var text = encodeURIComponent(title + '\n\n\ud83d\udd17 ' + url + '\n\n\ud83c\uddff\ud83c\uddfc Stay informed on Zimbabwe \u2014 follow @MutapaTimes for daily news, analysis & more.\n\ud83d\udcf0 https://www.mutapatimes.com');
    window.open('https://wa.me/?text=' + text, '_blank');
  });
  return btn;
}

// ============================================================
// Share-as-image — canvas-rendered branded share card
// ============================================================

function shareCardWrapText(ctx, text, x, y, maxWidth, lineHeight, maxY, maxLines) {
  // Handle explicit line breaks first, then word-wrap each paragraph
  var paragraphs = text.replace(/\r\n/g, '\n').split('\n');
  var lines = 0;
  maxLines = maxLines || 99;

  for (var p = 0; p < paragraphs.length; p++) {
    var words = paragraphs[p].split(' ').filter(function(w) { return w.length > 0; });
    if (words.length === 0) {
      // Empty line — add half-height spacing
      y += Math.round(lineHeight * 0.6);
      continue;
    }
    var line = '';
    for (var i = 0; i < words.length; i++) {
      var test = line + (line ? ' ' : '') + words[i];
      if (ctx.measureText(test).width > maxWidth && line) {
        lines++;
        if (maxY && y + lineHeight > maxY) {
          ctx.fillText(line.replace(/\s+$/, '') + '\u2026', x, y);
          return y + lineHeight;
        }
        if (lines >= maxLines) {
          ctx.fillText(line.replace(/\s+$/, '') + '\u2026', x, y);
          return y + lineHeight;
        }
        ctx.fillText(line, x, y);
        line = words[i];
        y += lineHeight;
      } else {
        line = test;
      }
    }
    if (line) {
      ctx.fillText(line, x, y);
      y += lineHeight;
      lines++;
    }
  }
  return y;
}

function shareCardDrawPill(ctx, x, y, text, bgColor, textColor) {
  ctx.font = '700 13px "Helvetica Neue", Arial, sans-serif';
  var tw = ctx.measureText(text).width;
  var padX = 10, padY = 4, h = 22, r = 4;
  var w = tw + padX * 2;
  // Rounded rect
  ctx.fillStyle = bgColor;
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.lineTo(x + w - r, y);
  ctx.quadraticCurveTo(x + w, y, x + w, y + r);
  ctx.lineTo(x + w, y + h - r);
  ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
  ctx.lineTo(x + r, y + h);
  ctx.quadraticCurveTo(x, y + h, x, y + h - r);
  ctx.lineTo(x, y + r);
  ctx.quadraticCurveTo(x, y, x + r, y);
  ctx.closePath();
  ctx.fill();
  // Text
  ctx.fillStyle = textColor;
  ctx.textBaseline = 'middle';
  ctx.fillText(text, x + padX, y + h / 2 + 1);
  return w + 10; // return width used + gap
}

function downloadBlob(blob, filename) {
  var url = URL.createObjectURL(blob);
  var a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  setTimeout(function() { URL.revokeObjectURL(url); }, 5000);
}

function generateShareImage(articleData) {
  var fontsReady = (document.fonts && document.fonts.ready) ? document.fonts.ready : Promise.resolve();

  // Pre-load: Harare skyline (always) + article image (if available)
  var skylinePromise = new Promise(function(resolve) {
    var img = new Image();
    img.crossOrigin = 'anonymous';
    img.onload = function() { resolve(img); };
    img.onerror = function() { resolve(null); };
    img.src = 'img/banner.png';
  });
  var articleImgPromise = new Promise(function(resolve) {
    if (articleData.image) {
      var img = new Image();
      img.crossOrigin = 'anonymous';
      img.onload = function() { resolve(img); };
      img.onerror = function() { resolve(null); };
      img.src = articleData.image;
    } else {
      resolve(null);
    }
  });

  return Promise.all([fontsReady, skylinePromise, articleImgPromise]).then(function(results) {
    var skylineImg = results[1];
    var articleImg = results[2];

    // Portrait format — tall card like Guardian/Semafor examples
    var W = 1080, H = 1350;
    var canvas = document.createElement('canvas');
    canvas.width = W;
    canvas.height = H;
    var ctx = canvas.getContext('2d');
    var pad = 64;

    // ─── Full background: dark charcoal ───
    ctx.fillStyle = '#1a1a1a';
    ctx.fillRect(0, 0, W, H);

    // ─── Harare skyline at top with gradient fade ───
    var imgH = 400;
    if (skylineImg) {
      var srcRatio = skylineImg.naturalWidth / skylineImg.naturalHeight;
      var drawW = W;
      var drawH = W / srcRatio;
      var drawY = 0;
      if (drawH < imgH) {
        drawH = imgH;
        drawW = imgH * srcRatio;
      }
      var drawX = (W - drawW) / 2;
      ctx.drawImage(skylineImg, drawX, drawY, drawW, drawH);

      // Warm overlay tint
      ctx.fillStyle = 'rgba(26, 26, 26, 0.25)';
      ctx.fillRect(0, 0, W, imgH);

      // Gradient fade into dark background
      var grad = ctx.createLinearGradient(0, imgH - 160, 0, imgH);
      grad.addColorStop(0, 'rgba(26, 26, 26, 0)');
      grad.addColorStop(1, '#1a1a1a');
      ctx.fillStyle = grad;
      ctx.fillRect(0, imgH - 160, W, 160);
    }

    // ─── Masthead: "THE MUTAPA TIMES" — big, top-left over the image ───
    ctx.textBaseline = 'top';
    ctx.fillStyle = '#ffffff';
    ctx.font = '700 52px "Playfair Display", Georgia, serif';
    ctx.fillText('THE MUTAPA TIMES', pad, 48);

    // Gold accent line under masthead
    ctx.fillStyle = '#c8a96e';
    ctx.fillRect(pad, 116, 80, 3);

    // ─── Category / Local-Foreign pill ───
    var y = imgH + 24;
    var contentWidth = W - pad * 2;
    var pillX = pad;
    if (articleData.isLocal) {
      pillX += shareCardDrawPill(ctx, pillX, y, 'LOCAL', '#00897b', '#ffffff');
    } else if (articleData.source) {
      pillX += shareCardDrawPill(ctx, pillX, y, 'FOREIGN', 'rgba(255,255,255,0.15)', 'rgba(255,255,255,0.7)');
    }
    if (articleData.category) {
      shareCardDrawPill(ctx, pillX, y, articleData.category.toUpperCase(), '#1a5632', '#ffffff');
    }
    if (articleData.isLocal || articleData.source || articleData.category) {
      y += 44;
    }

    // ─── Headline — large, white, serif ───
    var titleLen = (articleData.title || '').length;
    var headlineSize = titleLen > 120 ? 36 : (titleLen > 80 ? 40 : (titleLen > 50 ? 46 : 52));
    var headlineLineH = Math.round(headlineSize * 1.4);
    ctx.font = '700 ' + headlineSize + 'px "Playfair Display", Georgia, serif';
    ctx.fillStyle = '#ffffff';
    y = shareCardWrapText(ctx, articleData.title || '', pad, y, contentWidth, headlineLineH, H - 300, 5);
    y += 24;

    // ─── Source + date line ───
    ctx.font = '500 18px "Helvetica Neue", Arial, sans-serif';
    ctx.fillStyle = '#c8a96e';
    var metaParts = [];
    if (articleData.source) metaParts.push(articleData.source);
    var pubDate = formatDate(articleData.publishedAt);
    if (pubDate) metaParts.push(pubDate);
    if (metaParts.length) {
      ctx.fillText(metaParts.join('  \u00b7  '), pad, y);
      y += 40;
    }

    // ─── Article image (from GNews) ───
    if (articleImg) {
      var artImgW = contentWidth;
      var artImgH = Math.round(artImgW * 0.52);
      var maxImgH = H - y - 240; // leave room for footer
      if (artImgH > maxImgH) artImgH = maxImgH;
      if (artImgH > 100) {
        var r = 8;
        ctx.save();
        ctx.beginPath();
        ctx.moveTo(pad + r, y);
        ctx.lineTo(pad + artImgW - r, y);
        ctx.quadraticCurveTo(pad + artImgW, y, pad + artImgW, y + r);
        ctx.lineTo(pad + artImgW, y + artImgH - r);
        ctx.quadraticCurveTo(pad + artImgW, y + artImgH, pad + artImgW - r, y + artImgH);
        ctx.lineTo(pad + r, y + artImgH);
        ctx.quadraticCurveTo(pad, y + artImgH, pad, y + artImgH - r);
        ctx.lineTo(pad, y + r);
        ctx.quadraticCurveTo(pad, y, pad + r, y);
        ctx.closePath();
        ctx.clip();
        var aRatio = articleImg.naturalWidth / articleImg.naturalHeight;
        var adW = artImgW, adH = artImgW / aRatio;
        if (adH < artImgH) { adH = artImgH; adW = artImgH * aRatio; }
        var adX = pad + (artImgW - adW) / 2;
        var adY = y + (artImgH - adH) / 2;
        ctx.drawImage(articleImg, adX, adY, adW, adH);
        ctx.restore();
        y += artImgH + 24;
      }
    }

    // ─── Description snippet ───
    var footerY = H - 150;
    if (articleData.description && y < footerY - 60) {
      ctx.font = '400 20px "Helvetica Neue", Arial, sans-serif';
      ctx.fillStyle = 'rgba(255, 255, 255, 0.6)';
      ctx.textBaseline = 'top';
      var desc = articleData.description;
      if (desc.length > 180) desc = desc.substring(0, 177) + '...';
      y = shareCardWrapText(ctx, desc, pad, y, contentWidth, 30, footerY - 20, 3);
    }

    // ─── Footer area: CTA + branding ───
    // Subtle separator line
    ctx.fillStyle = 'rgba(200, 169, 110, 0.3)';
    ctx.fillRect(pad, footerY, contentWidth, 1);
    footerY += 30;

    // Domain
    ctx.font = '700 22px "Helvetica Neue", Arial, sans-serif';
    ctx.fillStyle = '#ffffff';
    ctx.textBaseline = 'top';
    ctx.fillText('mutapatimes.com', pad, footerY);

    // "Sign up for free" CTA pill
    var ctaText = 'Sign up for free';
    ctx.font = '700 16px "Helvetica Neue", Arial, sans-serif';
    var ctaW = ctx.measureText(ctaText).width + 32;
    var ctaH = 36;
    var ctaX = W - pad - ctaW;
    var ctaY = footerY - 4;
    var ctaR = 18;
    ctx.fillStyle = '#c8a96e';
    ctx.beginPath();
    ctx.moveTo(ctaX + ctaR, ctaY);
    ctx.lineTo(ctaX + ctaW - ctaR, ctaY);
    ctx.quadraticCurveTo(ctaX + ctaW, ctaY, ctaX + ctaW, ctaY + ctaR);
    ctx.lineTo(ctaX + ctaW, ctaY + ctaH - ctaR);
    ctx.quadraticCurveTo(ctaX + ctaW, ctaY + ctaH, ctaX + ctaW - ctaR, ctaY + ctaH);
    ctx.lineTo(ctaX + ctaR, ctaY + ctaH);
    ctx.quadraticCurveTo(ctaX, ctaY + ctaH, ctaX, ctaY + ctaH - ctaR);
    ctx.lineTo(ctaX, ctaY + ctaR);
    ctx.quadraticCurveTo(ctaX, ctaY, ctaX + ctaR, ctaY);
    ctx.closePath();
    ctx.fill();
    ctx.fillStyle = '#1a1a1a';
    ctx.textBaseline = 'middle';
    ctx.fillText(ctaText, ctaX + 16, ctaY + ctaH / 2 + 1);

    // Tagline below — with breathing room
    ctx.textBaseline = 'top';
    ctx.font = '400 16px "Helvetica Neue", Arial, sans-serif';
    ctx.fillStyle = 'rgba(255,255,255,0.4)';
    ctx.fillText('Business & intelligence \u2014 Zimbabwe, outside-in', pad, footerY + 44);

    // Convert to blob
    return new Promise(function(resolve) {
      canvas.toBlob(function(blob) { resolve(blob); }, 'image/png');
    });
  });
}

function createImageShareBtn(articleData) {
  var btn = $('<button class="image-share-btn" title="Share as image">').html(IMAGE_SHARE_ICON_SVG);
  btn.on('click', function(e) {
    e.preventDefault();
    e.stopPropagation();

    var original = btn.html();
    btn.text('\u2026');

    generateShareImage(articleData).then(function(blob) {
      var shareText = articleData.title + '\n\n\ud83c\uddff\ud83c\uddfc Stay informed on Zimbabwe \u2014 follow @MutapaTimes for daily news, analysis & more.\n\ud83d\udcf0 https://www.mutapatimes.com';

      // Try Web Share API with files
      if (navigator.canShare) {
        var file = new File([blob], 'mutapatimes-headline.png', { type: 'image/png' });
        var shareData = {
          title: articleData.title + ' | The Mutapa Times',
          text: shareText,
          files: [file]
        };
        try {
          if (navigator.canShare(shareData)) {
            navigator.share(shareData).catch(function(err) {
              if (err.name !== 'AbortError') downloadBlob(blob, 'mutapatimes-headline.png');
            }).finally(function() { btn.html(original); });
            return;
          }
        } catch (ex) { /* canShare threw — fall through to download */ }
      }

      // Fallback: download image + copy text to clipboard
      downloadBlob(blob, 'mutapatimes-headline.png');
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(shareText);
      }
      btn.html(original);
    }).catch(function() {
      btn.html(original);
    });
  });
  return btn;
}

function createShareGroup(title, url, articleData) {
  var group = $('<span class="share-group">');
  group.append(createShareBtn(title, url));
  group.append(createWhatsAppBtn(title, url));
  if (articleData) group.append(createImageShareBtn(articleData));
  return group;
}

// ============================================================
// RENDER: Main stories — single column layout
// ============================================================
function renderMainStories(articles) {
  var container = $("#main-stories");
  if (!container.length) return;
  container.empty();

  if (!articles || articles.length === 0) {
    container.html('<p class="loading-msg">No articles found.</p>');
    return;
  }

  // Filter out articles already shown in spotlight
  var filtered = articles.filter(function(a) {
    return !a.url || !_spotlightUrls[a.url];
  });

  for (var i = 0; i < filtered.length && i < 25; i++) {
    var a = filtered[i];
    var rank = i + 1;
    var readTime = getReadingTime(a.description);
    var pubDate = formatDate(a.publishedAt);
    var isJustNow = isBreakingRecent(a.publishedAt);

    var card = $('<article class="main-article">');
    if (rank === 1) card.addClass("rank-featured");

    var link = $('<a>').attr('href', a.url || '#').attr('target', '_blank').attr('rel', 'noopener nofollow');

    var textCol = $('<div class="main-article-text">');
    textCol.append($('<h3 class="main-article-title">').text(a.title));

    // Line 1: source, time, read time
    var meta = $('<p class="main-article-meta">');
    if (a.source) {
      meta.append($('<span>').text(a.source));
      if (isReputableSource(a.source)) {
        meta.append($('<span class="verified-badge" title="Verified source">').html('&#10003;'));
      }
    }
    if (isJustNow) {
      meta.append(document.createTextNode(" \u00b7 "));
      meta.append($('<span class="just-now-badge">').html('&#9679; JUST NOW'));
    } else if (pubDate) {
      meta.append(document.createTextNode(" \u00b7 "));
      var timeEl = $('<time>').text(pubDate);
      try {
        var dt = new Date(a.publishedAt);
        if (!isNaN(dt.getTime())) timeEl.attr('datetime', dt.toISOString());
      } catch (e) {}
      meta.append(timeEl);
    }
    if (readTime) {
      meta.append(document.createTextNode(" \u00b7 " + readTime));
    }
    textCol.append(meta);

    // Line 2: tags + badges, then share (bottom-right for thumb access)
    var tagRow = $('<div class="main-article-tags">');
    if (a.isLocal) {
      tagRow.append($('<span class="press-marker local-press">').text("Local"));
    } else if (a.source) {
      tagRow.append($('<span class="press-marker foreign-press">').text("Foreign"));
    }
    var category = inferCategory(a.title);
    if (category) {
      tagRow.append($('<span class="category-tag">').text(category));
    }
    var desc = a.description;
    if (desc && desc.length > 250) desc = desc.substring(0, 250) + "...";
    tagRow.append(createShareGroup(a.title, a.url, {
      title: a.title, source: a.source, description: desc,
      url: a.url, category: category, isLocal: a.isLocal,
      publishedAt: a.publishedAt, image: a.image || ''
    }));
    textCol.append(tagRow);
    if (desc) textCol.append($('<p class="main-article-desc">').text(desc));

    link.append(textCol);
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

  // Inject structured data for SEO
  injectArticleSchema(filtered, 'main');

  // Subscribe banner — render full-width after the content-layout grid
  // Form POSTs to Brevo hosted form via hidden iframe (bypasses CORS).
  // Replace BREVO_FORM_URL below with your actual Brevo form action URL
  // (e.g. "https://XXXXX.sibforms.com/serve/YYYYY") after creating the
  // form in the Brevo dashboard under Contacts > Forms > Sign-up.
  var BREVO_FORM_URL = "https://e8bb9c12.sibforms.com/serve/MUIFANhyo5KAv45zGQtXk46aajtYgiqbLYvK0dXstXNkrCWwsrDeJG7IjtjBOM4LZfCQpFxjgq1NguOQm0ZMtALVI-9f2BYGEwxlGoGnDBiTqyPNvC7vR6D1lPLC4UWJqvOevKNHiUd0f5-o093A3UQ7iNImM7AC4as67y6Jo4WrQKPW8qEiHVivLeAnaT1wNM2xeUW1a6EmaLlvJg==";
  var contentLayout = $(".content-layout");
  if (contentLayout.length) {
    // Create hidden iframe target for cross-origin form submission
    var iframeName = "brevo-subscribe-frame";
    var iframe = $('<iframe>').attr({
      name: iframeName,
      style: "display:none;width:0;height:0;border:0;"
    });
    $("body").append(iframe);

    var subscribe = $('<div class="subscribe-banner">');
    subscribe.append($('<h3 class="subscribe-title">').text("Essential intelligence for the Zimbabwean diaspora."));
    subscribe.append($('<p class="subscribe-text">').text("Curated news, economic data, and analysis from foreign press \u2014 delivered to your inbox. Join readers in over 30 countries."));
    var form = $('<form class="subscribe-form">');
    if (BREVO_FORM_URL) {
      form.attr({ method: "POST", action: BREVO_FORM_URL, target: iframeName });
    }
    form.append($('<input class="subscribe-input" type="email" name="EMAIL" placeholder="Enter your email address" required autocomplete="email">'));
    form.append($('<button class="subscribe-btn" type="submit">').text("Subscribe"));
    subscribe.append(form);
    var statusMsg = $('<p class="subscribe-status">').hide();
    subscribe.append(statusMsg);
    subscribe.append($('<p class="subscribe-fine">').html('By subscribing you agree to our <a href="terms.html">Terms &amp; Conditions</a>. You may unsubscribe at any time.'));
    contentLayout.after(subscribe);

    // Handle subscribe form submission
    form.on("submit", function(e) {
      var emailVal = form.find('input[name="EMAIL"]').val();
      if (!emailVal) {
        e.preventDefault();
        return;
      }
      if (!BREVO_FORM_URL) {
        e.preventDefault();
        statusMsg.text("Subscriptions coming soon.").css("color", "#6b6b6b").show();
        return;
      }
      // Form submits to hidden iframe — show success after short delay
      var btn = form.find('button');
      btn.prop('disabled', true).text("Subscribing\u2026");
      statusMsg.text("Subscribing\u2026").css("color", "#6b6b6b").show();

      setTimeout(function() {
        statusMsg.text("Thank you for subscribing!").css("color", "#00897b");
        form.find("input").val("");
        btn.prop('disabled', false).text("Subscribe");
      }, 2000);
    });
  }
}

// ============================================================
// SPOTLIGHT — GNews data with RSS fallback
// ============================================================
var GNEWS_CATEGORIES = ["business", "technology", "entertainment", "sports", "science", "health"];

function loadSpotlightStories() {
  var cacheKey = "spotlight_all";
  var cached = getCache(cacheKey);
  if (cached) {
    renderSpotlightStories(cached);
    return;
  }

  // Load pre-fetched spotlight articles (GNews API — includes images + descriptions)
  $.ajax({
    type: "GET",
    url: MUTAPA_CONFIG.DATA_PATH + "spotlight.json",
    dataType: "json",
    success: function(data) {
      if (data && data.articles && data.articles.length > 0) {
        setCache(cacheKey, data.articles);
        renderSpotlightStories(data.articles);
        // Render remaining GNews articles below spotlight
        if (data.more && data.more.length > 0) {
          renderGnewsMore(data.more);
        }
      } else {
        loadSpotlightFromRSS();
      }
    },
    error: function() {
      loadSpotlightFromRSS();
    }
  });
}

function loadSpotlightFromRSS() {
  var cacheKey = "spotlight_all";
  var allArticles = [];
  var completed = 0;
  var total = SPOTLIGHT_RSS_FEEDS.length;

  var _spotlightTimeout = setTimeout(function() {
    if (document.querySelector('#spotlight-stories .loading-msg')) {
      document.querySelector('#spotlight-stories').innerHTML =
        '<p class="loading-msg" style="color: rgba(255,255,255,0.6);">Spotlight stories are temporarily unavailable.</p>';
    }
  }, 15000);

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
          clearTimeout(_spotlightTimeout);
          // Filter to recent articles only
          allArticles = allArticles.filter(function(a) {
            if (!a.publishedAt) return false;
            try {
              var d = new Date(a.publishedAt);
              if (isNaN(d.getTime())) return false;
              if (d.getFullYear() < 2025) return false; // hard floor — no archival content
              return (Date.now() - d.getTime()) < SPOTLIGHT_MAX_AGE_MS;
            } catch (e) { return false; }
          });
          allArticles = deduplicateByTopic(allArticles, 0.25);
          allArticles.sort(function(a, b) {
            var dateA = a.publishedAt ? new Date(a.publishedAt).getTime() : 0;
            var dateB = b.publishedAt ? new Date(b.publishedAt).getTime() : 0;
            return dateB - dateA;
          });
          // Reputable sources only — no fallback to unvetted sources
          var merged = allArticles.filter(function(a) { return isReputableSource(a.source); }).slice(0, 3);
          setCache(cacheKey, merged);
          renderSpotlightStories(merged);
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

  // Reputable sources only — strip out any non-reputable articles
  articles = articles.filter(function(a) { return isReputableSource(a.source); });
  if (articles.length === 0) {
    container.html('<p class="loading-msg" style="color: rgba(255,255,255,0.6);">No spotlight stories available.</p>');
    return;
  }

  // Track spotlight URLs so main/sidebar feeds can skip duplicates
  _spotlightUrls = {};
  for (var i = 0; i < articles.length && i < 3; i++) {
    if (articles[i].url) _spotlightUrls[articles[i].url] = true;
  }

  for (var i = 0; i < articles.length && i < 3; i++) {
    var a = articles[i];
    var pubDate = formatDate(a.publishedAt);

    var item = $('<article class="spotlight-item">');
    var link = $('<a>').attr('href', a.url || '#').attr('target', '_blank').attr('rel', 'noopener nofollow');

    // Article image
    if (a.image) {
      var img = $('<img class="spotlight-img">').attr('src', a.image).attr('alt', a.title || '');
      link.append(img);
    }

    // Text content wrapped for 2-col layout
    var textWrap = $('<div class="spotlight-text">');
    textWrap.append($('<h4 class="spotlight-title">').text(a.title));

    var desc = a.description;
    if (desc && desc.length > 200) desc = desc.substring(0, 200) + "...";
    if (desc) textWrap.append($('<p class="spotlight-desc">').text(desc));

    var meta = $('<p class="spotlight-meta">');
    if (a.source) {
      meta.append($('<span class="verified-source">').text(a.source));
      meta.append($('<span class="verified-badge" title="Verified source">').html('&#10003;'));
    }
    if (pubDate) {
      if (a.source) meta.append(document.createTextNode(" \u00b7 "));
      var timeEl = $('<time>').text(pubDate);
      try {
        var dt = new Date(a.publishedAt);
        if (!isNaN(dt.getTime())) timeEl.attr('datetime', dt.toISOString());
      } catch (e) {}
      meta.append(timeEl);
    }
    meta.append(createShareGroup(a.title, a.url, {
      title: a.title, source: a.source, description: desc,
      url: a.url, category: '', isLocal: false,
      publishedAt: a.publishedAt, image: a.image || ''
    }));
    textWrap.append(meta);

    link.append(textWrap);
    item.append(link);
    container.append(item);
  }

  // Inject structured data for SEO
  injectArticleSchema(articles, 'spotlight');
}

// ============================================================
// RENDER: GNews More — secondary articles below spotlight
// ============================================================
function renderGnewsMore(articles) {
  var container = $("#gnews-more");
  if (!container.length) return;
  container.empty();

  if (!articles || articles.length === 0) return;

  // Filter out any already shown in spotlight
  var filtered = articles.filter(function(a) {
    return !a.url || !_spotlightUrls[a.url];
  });
  if (filtered.length === 0) return;

  for (var i = 0; i < filtered.length && i < 10; i++) {
    var a = filtered[i];
    var pubDate = formatDate(a.publishedAt);
    var readTime = getReadingTime(a.description);

    var card = $('<article class="gnews-more-item">');
    var link = $('<a>').attr('href', a.url || '#').attr('target', '_blank').attr('rel', 'noopener nofollow');

    // Article image (GNews provides images)
    if (a.image) {
      var imgWrap = $('<div class="gnews-more-img-wrap">');
      var img = $('<img class="gnews-more-img">').attr('src', a.image).attr('alt', a.title || '').attr('loading', 'lazy');
      img.on('error', function() { $(this).parent().hide(); });
      imgWrap.append(img);
      link.append(imgWrap);
    }

    var textCol = $('<div class="gnews-more-text">');
    textCol.append($('<h4 class="gnews-more-title">').text(a.title));

    var desc = a.description;
    if (desc && desc.length > 160) desc = desc.substring(0, 160) + "...";
    if (desc) textCol.append($('<p class="gnews-more-desc">').text(desc));

    var meta = $('<p class="gnews-more-meta">');
    if (a.source) {
      meta.append($('<span>').text(a.source));
    }
    if (pubDate) {
      if (a.source) meta.append(document.createTextNode(" \u00b7 "));
      var timeEl = $('<time>').text(pubDate);
      try {
        var dt = new Date(a.publishedAt);
        if (!isNaN(dt.getTime())) timeEl.attr('datetime', dt.toISOString());
      } catch (e) {}
      meta.append(timeEl);
    }
    if (readTime) {
      meta.append(document.createTextNode(" \u00b7 " + readTime));
    }
    meta.append(createShareGroup(a.title, a.url, {
      title: a.title, source: a.source, description: desc,
      url: a.url, category: inferCategory(a.title), isLocal: false,
      publishedAt: a.publishedAt, image: a.image || ''
    }));
    textCol.append(meta);

    link.append(textCol);
    card.append(link);
    container.append(card);
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

  // "Live on the Ground" — local Zimbabwean sources only, no spotlight dupes
  var filtered = articles.filter(function(a) {
    if (a.url && _spotlightUrls[a.url]) return false;
    return a.isLocal;
  });

  for (var i = 0; i < filtered.length && i < 30; i++) {
    var a = filtered[i];
    var pubDate = formatDate(a.publishedAt);
    var sidebarJustNow = isBreakingRecent(a.publishedAt);

    var item = $('<article class="sidebar-item">');
    var link = $('<a>').attr('href', a.url || '#').attr('target', '_blank').attr('rel', 'noopener nofollow');

    link.append($('<h4 class="sidebar-title">').text(a.title));

    var desc = a.description;
    if (desc && desc.length > 150) desc = desc.substring(0, 150) + "...";
    if (desc) link.append($('<p class="sidebar-desc">').text(desc));

    var meta = $('<p class="sidebar-meta">');
    // All Live on the Ground articles tagged as LOCAL
    meta.append($('<span class="press-marker local-press">').text("Local"));
    if (a.source) {
      meta.append($('<span>').text(a.source));
      if (isReputableSource(a.source)) {
        meta.append($('<span class="verified-badge verified-badge-sm" title="Verified source">').html('&#10003;'));
      }
    }
    if (sidebarJustNow) {
      meta.append(document.createTextNode(" \u00b7 "));
      meta.append($('<span class="just-now-badge">').html('&#9679; JUST NOW'));
    } else if (pubDate) {
      meta.append(document.createTextNode(" \u00b7 "));
      var timeEl = $('<time>').text(pubDate);
      try {
        var dt = new Date(a.publishedAt);
        if (!isNaN(dt.getTime())) timeEl.attr('datetime', dt.toISOString());
      } catch (e) {}
      meta.append(timeEl);
    }
    meta.append(createShareGroup(a.title, a.url, {
      title: a.title, source: a.source, description: desc,
      url: a.url, category: '', isLocal: a.isLocal,
      publishedAt: a.publishedAt, image: a.image || ''
    }));
    link.append(meta);

    item.append(link);
    container.append(item);
  }

  // Inject structured data for SEO
  injectArticleSchema(filtered, 'sidebar');
}

// ============================================================
// PERSONALISATION TOUCHES
// ============================================================

// Zimbabwe time (CAT) in header
function getZimTimeOfDay() {
  var h = parseInt(new Date().toLocaleTimeString("en-GB", {
    hour: "2-digit", timeZone: "Africa/Harare"
  }), 10);
  if (h >= 5 && h < 12) return "Morning";
  if (h >= 12 && h < 17) return "Afternoon";
  if (h >= 17 && h < 21) return "Evening";
  return "Night";
}

function updateZimbabweTime() {
  try {
    var now = new Date();
    var zimTime = now.toLocaleTimeString("en-US", {
      hour: "2-digit", minute: "2-digit",
      timeZone: "Africa/Harare"
    });
    $(".price").text(zimTime + " Zimbabwe");

    // Live cam time
    var camEl = document.getElementById("live-cam-time");
    if (camEl) {
      camEl.textContent = zimTime + " \u00b7 " + getZimTimeOfDay() + " in Zimbabwe";
    }
  } catch (e) {}
}

// --- Shona Proverbs ---
var SHONA_PROVERBS = [
  { shona: "Chara chimwe hachitswanyi inda.", english: "One finger cannot crush a louse." },
  { shona: "Kudzidza hakuperi.", english: "Learning never ends." },
  { shona: "Rume rimwe harikombi churu.", english: "One man cannot surround an anthill." },
  { shona: "Chirere chigokurerawo.", english: "Raise a child and it will raise you too." },
  { shona: "Rina manyanga hariputirwi.", english: "That which has horns cannot be wrapped." },
  { shona: "Chisi hachieri chisingabudi rimwe.", english: "A day of rest doesn't end without another dawning." },
  { shona: "Mugoni wepwere ndeasinayo.", english: "The one who knows how to raise children is one who has none." },
  { shona: "Kufa kwendega kufa kusingachemerwe.", english: "To die alone is to die without being mourned." },
  { shona: "Mwana asingachemi anofira mumbereko.", english: "A child who does not cry dies on its mother's back." },
  { shona: "Kugarira nhaka kuona bvute.", english: "To inherit is to see the dust settle." },
  { shona: "Gudo guru peta muswe vadiki vakutye.", english: "Great baboon, curl your tail so the little ones may fear you." },
  { shona: "Kuziva mbuya huudzwa.", english: "To know grandmother is to be told about her." },
  { shona: "Chakafukidza dzimba matenga.", english: "What covers houses is the roof." },
  { shona: "Zviri muvanhu hazvienzani.", english: "What is in people is not equal." },
  { shona: "Murombo munhu.", english: "A poor person is still a person." },
  { shona: "Zano pangwa une rako.", english: "Accept advice, but keep your own counsel." },
  { shona: "Mvura ngainaye; hapana anodzivisa.", english: "Let the rain fall; no one can stop it." },
  { shona: "Nzara haina hama.", english: "Hunger has no relatives." },
  { shona: "Chitsva chiri murutsoka.", english: "What is new is underfoot." },
  { shona: "Dura rinokanganwa gejo.", english: "The granary forgets the hoe." },
  { shona: "Nhamo yeumwe hairambirwi sadza.", english: "Another's troubles don't stop you from eating." },
  { shona: "Gonzo redziva harityi mvura.", english: "A rat of the river does not fear water." },
  { shona: "Harisi zuva rimwe guru rakasakara.", english: "The great baobab did not grow in a single day." },
  { shona: "Kure kwegava ndokusina mugariri.", english: "The distance of the vulture is because no one stays there." },
  { shona: "Kutsva kwendebvu varume vanodzimurana.", english: "When a beard catches fire, men help each other put it out." },
  { shona: "Atsemhira zuva anochembera.", english: "One who races with the sun grows old." },
  { shona: "Chinonzi mhosva kana matakadya.", english: "What is called a crime depends on whether you have eaten." },
  { shona: "Mbudzi kudya mufenje haina mhosva.", english: "When a goat eats a baboon's food, there is no crime." },
  { shona: "Shiri huru haigarire dendere rimwe.", english: "A great bird does not sit in one nest." },
  { shona: "Chinono chinogara chiuru.", english: "The small and steady accumulates a thousand." }
];

function initShonaProverb() {
  var el = document.getElementById("shona-proverb");
  if (!el) return;
  var dayIndex = Math.floor(Date.now() / 86400000) % SHONA_PROVERBS.length;
  var p = SHONA_PROVERBS[dayIndex];
  el.innerHTML =
    '<span class="shona-proverb-label">Tsumo of the Day</span>' +
    '<p class="shona-proverb-text">\u201c' + p.shona + '\u201d</p>' +
    '<p class="shona-proverb-translation">' + p.english + '</p>';
}

// --- Reader Location + Distance from Zimbabwe ---
var LOCATION_CACHE_KEY = "reader_location_24h";

function haversineKm(lat1, lon1, lat2, lon2) {
  var R = 6371;
  var dLat = (lat2 - lat1) * Math.PI / 180;
  var dLon = (lon2 - lon1) * Math.PI / 180;
  var a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
    Math.sin(dLon / 2) * Math.sin(dLon / 2);
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

function initReaderLocation() {
  var el = document.getElementById("reader-location");
  if (!el) return;
  try {
    var raw = localStorage.getItem("mutapa_" + LOCATION_CACHE_KEY);
    if (raw) {
      var parsed = JSON.parse(raw);
      if (Date.now() - parsed.timestamp < 24 * 60 * 60 * 1000) {
        displayReaderLocation(parsed.data);
        return;
      }
    }
  } catch (e) {}
  $.ajax({
    url: "https://ipapi.co/json/",
    type: "GET",
    dataType: "json",
    timeout: 5000,
    success: function(data) {
      if (data && data.city && data.country_name) {
        var loc = {
          city: data.city,
          country: data.country_name,
          lat: data.latitude,
          lon: data.longitude
        };
        try {
          localStorage.setItem("mutapa_" + LOCATION_CACHE_KEY, JSON.stringify({
            timestamp: Date.now(),
            data: loc
          }));
        } catch (e) {}
        displayReaderLocation(loc);
      }
    }
  });
}

function nearestZimCity(lat, lon) {
  var closest = null;
  var minDist = Infinity;
  WEATHER_CITIES.forEach(function(city) {
    var d = haversineKm(lat, lon, city.lat, city.lon);
    if (d < minDist) { minDist = d; closest = city; }
  });
  return { name: closest.name, dist: Math.round(minDist) };
}

function displayReaderLocation(loc) {
  var el = document.getElementById("reader-location");
  if (!el) return;
  var text = 'Reading from <span class="notranslate">' + loc.country + '</span>';
  if (loc.lat && loc.lon) {
    var nearest = nearestZimCity(loc.lat, loc.lon);
    if (nearest.dist > 100) {
      text += ' · ' + nearest.dist.toLocaleString() + ' km from ' + nearest.name;
    }
  }
  el.innerHTML = '<p class="reader-location-text">' + text + '</p>';
}

// --- On This Day in Zimbabwe ---
var ZIM_ON_THIS_DAY = {
  "01-01": { year: 2009, text: "Zimbabwe adopted the multi-currency system, effectively abandoning the hyperinflated Zimbabwean dollar." },
  "01-21": { year: 2009, text: "Morgan Tsvangirai was sworn in as Prime Minister under the Global Political Agreement." },
  "02-01": { year: 2009, text: "The Government of National Unity officially began between ZANU-PF and the MDC formations." },
  "02-20": { year: 1959, text: "The Southern Rhodesian African National Congress was banned by colonial authorities." },
  "02-21": { year: 2000, text: "Zimbabweans voted in a constitutional referendum, rejecting a government-proposed draft." },
  "03-08": { year: 2013, text: "A new Constitution was overwhelmingly approved by referendum with over 94% voting yes." },
  "03-28": { year: 1980, text: "Robert Mugabe was sworn in as the first Prime Minister of independent Zimbabwe." },
  "04-05": { year: 1966, text: "Two ZANLA guerrillas fell at Chinhoyi in what became the first battle of the liberation war." },
  "04-17": { year: 1980, text: "The British flag was lowered for the last time in Salisbury as Zimbabwe's independence was proclaimed at midnight." },
  "04-18": { year: 1980, text: "Zimbabwe Independence Day \u2014 the nation formally gained independence from the United Kingdom." },
  "04-28": { year: 1980, text: "Zimbabwe was admitted as the 153rd member of the United Nations." },
  "05-25": { year: 1963, text: "The Organisation of African Unity was founded in Addis Ababa; Zimbabwe would join after independence." },
  "06-14": { year: 2008, text: "Morgan Tsvangirai withdrew from the presidential runoff election citing escalating violence." },
  "06-27": { year: 2008, text: "The controversial presidential runoff election took place despite widespread international condemnation." },
  "07-31": { year: 2013, text: "Zimbabwe held harmonised elections; ZANU-PF won a two-thirds parliamentary majority." },
  "08-01": { year: 2018, text: "Post-election protests in Harare turned violent, with the military deployed to the streets." },
  "08-11": { year: 1980, text: "Zimbabwe competed in its first Olympic Games as an independent nation, winning gold in women's hockey in Moscow." },
  "08-12": { year: 1980, text: "Heroes' Day was declared a national holiday to honour those who fought in the liberation struggle." },
  "08-13": { year: 1980, text: "Defence Forces Day was established the day after Heroes' Day." },
  "09-07": { year: 2019, text: "Former President Robert Mugabe died in Singapore at the age of 95." },
  "09-15": { year: 2008, text: "The Global Political Agreement was signed between ZANU-PF and the MDC formations." },
  "10-01": { year: 2016, text: "Zimbabweans launched the #ThisFlag movement, one of the largest citizen-led protests in decades." },
  "11-15": { year: 2017, text: "The Zimbabwe Defence Forces intervened, placing President Mugabe under house arrest in Operation Restore Legacy." },
  "11-18": { year: 2017, text: "Massive peaceful demonstrations in Harare and across Zimbabwe called for President Mugabe to step down." },
  "11-21": { year: 2017, text: "Robert Mugabe resigned as President after 37 years in power." },
  "11-24": { year: 2017, text: "Emmerson Mnangagwa was sworn in as the third President of Zimbabwe." },
  "12-22": { year: 1987, text: "The Unity Accord was signed between ZANU-PF and PF-ZAPU, ending the Gukurahundi conflict and establishing Unity Day." }
};

function initOnThisDay() {
  var el = document.getElementById("on-this-day");
  if (!el) return;
  var now = new Date();
  var mm = String(now.getMonth() + 1).padStart(2, "0");
  var dd = String(now.getDate()).padStart(2, "0");
  var key = mm + "-" + dd;
  var entry = ZIM_ON_THIS_DAY[key];
  if (!entry) { el.style.display = "none"; return; }
  el.style.display = "block";
  el.innerHTML =
    '<span class="on-this-day-label">On This Day</span>' +
    '<p class="on-this-day-text">In ' + entry.year + ': ' + entry.text + '</p>';
}

// ============================================================
// SEO: Inject per-article NewsArticle JSON-LD structured data
// ============================================================
function injectArticleSchema(articles, sectionName) {
  if (!articles || articles.length === 0) return;

  var limit = sectionName === 'spotlight' ? 3 : (sectionName === 'sidebar' ? 30 : 25);
  var schemaItems = [];

  for (var i = 0; i < Math.min(articles.length, limit); i++) {
    var a = articles[i];
    if (!a.title || !a.url) continue;

    var item = {
      "@type": "NewsArticle",
      "headline": a.title.substring(0, 110),
      "url": a.url,
      "mainEntityOfPage": a.url
    };

    if (a.publishedAt) {
      try {
        var d = new Date(a.publishedAt);
        if (!isNaN(d.getTime())) item["datePublished"] = d.toISOString();
      } catch (e) {}
    }
    if (a.source) {
      item["publisher"] = { "@type": "Organization", "name": a.source };
      item["author"] = { "@type": "Organization", "name": a.source };
    }
    if (a.description) {
      item["description"] = a.description.substring(0, 200);
    }
    if (a.image) {
      item["image"] = a.image;
    }

    schemaItems.push({
      "@type": "ListItem",
      "position": i + 1,
      "item": item
    });
  }

  if (schemaItems.length === 0) return;

  var listName = sectionName === 'spotlight' ? "Spotlight Stories" :
                 (sectionName === 'sidebar' ? "Local Zimbabwe News" : "Latest Zimbabwe Headlines");

  var schema = {
    "@context": "https://schema.org",
    "@type": "ItemList",
    "name": listName,
    "itemListElement": schemaItems
  };

  // Remove previously injected schema for this section
  var existingId = 'mutapa-schema-' + sectionName;
  var existing = document.getElementById(existingId);
  if (existing) existing.parentNode.removeChild(existing);

  var script = document.createElement('script');
  script.type = 'application/ld+json';
  script.id = existingId;
  script.textContent = JSON.stringify(schema);
  document.head.appendChild(script);
}

// --- Init all personalisation ---
function initPersonalisation() {
  initShonaProverb();
  initOnThisDay();
  initReaderLocation();
}
