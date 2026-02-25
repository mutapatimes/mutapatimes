/*
 * The Mutapa Times - Configuration
 * Single-page news aggregator: all Zimbabwe news, sorted by newest
 * Pulls from multiple Google News RSS feeds for broad coverage
 */
var MUTAPA_CONFIG = {
  CACHE_DURATION: 30 * 60 * 1000,
  RSS_API: "https://api.rss2json.com/v1/api.json?rss_url=",
  DATA_PATH: "data/",
  GITHUB_REPO: "mutapatimes/mutapatimes",
  GITHUB_BRANCH: "main"
};

// Stored article data for category filtering
var _allMainArticles = [];
var _allSidebarArticles = [];
var _gnewsMoreArticles = [];
var _activeCategory = "all";
var _activeSort = "newest";
var _currentPage = 1;
var ARTICLES_PER_PAGE = 20;

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
  // The Mutapa Times (original content)
  "the mutapa times", "mutapa times",
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
  // Major Zimbabwean outlets
  "the herald", "herald", "heraldonline", "h-metro",
  "newsday", "the standard", "dailynews", "daily news",
  "bulawayo24", "263chat", "nehanda radio", "nehandaradio",
  "the zimbabwe mail", "zimbabwe mail", "zimetro",
  "chronicle", "manica post", "sunday mail",
  // Major digital news platforms
  "yahoo", "yahoo news",
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
  { tag: "Politics", words: ["politics", "political", "election", "parliament", "government", "minister", "president", "opposition", "zanu", "mdc", "party", "vote", "campaign", "diplomat", "embassy", "mnangagwa", "chamisa", "mugabe", "senator", "cabinet", "coalition"] },
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

// Max age for main/sidebar articles (7 days — prevents ancient articles from appearing)
var FEED_MAX_AGE_MS = 7 * 24 * 60 * 60 * 1000;

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

  // Sort control
  $("#sort-select").on("change", function() {
    _activeSort = $(this).val();
    sortArticles(_allMainArticles);
    _currentPage = 1;
    renderMainStories(_allMainArticles);
  });
}

// Sort articles based on active sort mode
// Featured CMS articles with a headline_position are always pinned to the top
function sortArticles(articles) {
  if (_activeSort === "verified") {
    articles.sort(function(a, b) {
      // Featured articles always first
      var aPin = a.featured ? (a.headlinePosition || 999) : Infinity;
      var bPin = b.featured ? (b.headlinePosition || 999) : Infinity;
      if (aPin !== bPin) return aPin - bPin;
      var aVerified = isReputableSource(a.source) ? 1 : 0;
      var bVerified = isReputableSource(b.source) ? 1 : 0;
      if (bVerified !== aVerified) return bVerified - aVerified;
      var dateA = a.publishedAt ? new Date(a.publishedAt).getTime() : 0;
      var dateB = b.publishedAt ? new Date(b.publishedAt).getTime() : 0;
      return dateB - dateA;
    });
  } else {
    // Default: newest first, but featured articles pinned to top
    articles.sort(function(a, b) {
      var aPin = a.featured ? (a.headlinePosition || 999) : Infinity;
      var bPin = b.featured ? (b.headlinePosition || 999) : Infinity;
      if (aPin !== bPin) return aPin - bPin;
      var dateA = a.publishedAt ? new Date(a.publishedAt).getTime() : 0;
      var dateB = b.publishedAt ? new Date(b.publishedAt).getTime() : 0;
      return dateB - dateA;
    });
  }
}

function filterByCategory(category) {
  _currentPage = 1;
  renderMainStories(_allMainArticles);

  var sidebarFiltered = _allSidebarArticles;
  if (category === "_verified") {
    sidebarFiltered = _allSidebarArticles.filter(function(a) { return isReputableSource(a.source); });
  } else if (category === "_local") {
    sidebarFiltered = _allSidebarArticles.filter(function(a) { return a.isLocal || isLocalZimSource(a.source); });
  } else if (category !== "all") {
    sidebarFiltered = _allSidebarArticles.filter(function(a) {
      return inferCategory(a.title) === category;
    });
  }
  renderSidebarStories(sidebarFiltered);
}

// ============================================================
// CMS ARTICLES — load original articles published via CMS
// ============================================================
function loadCmsArticles(callback) {
  var apiUrl = "https://api.github.com/repos/" + MUTAPA_CONFIG.GITHUB_REPO +
    "/contents/content/articles?ref=" + MUTAPA_CONFIG.GITHUB_BRANCH;
  var rawBase = "https://raw.githubusercontent.com/" + MUTAPA_CONFIG.GITHUB_REPO +
    "/" + MUTAPA_CONFIG.GITHUB_BRANCH + "/content/articles/";

  $.ajax({
    type: "GET",
    url: apiUrl,
    dataType: "json",
    timeout: 8000,
    success: function(entries) {
      if (!entries || !entries.length) { callback([]); return; }

      var mdFiles = [];
      for (var i = 0; i < entries.length; i++) {
        if (entries[i].name && /\.md$/.test(entries[i].name)) {
          mdFiles.push(entries[i].name);
        }
      }
      if (!mdFiles.length) { callback([]); return; }

      var pending = mdFiles.length;
      var articles = [];

      mdFiles.forEach(function(filename) {
        $.ajax({
          type: "GET",
          url: rawBase + filename,
          dataType: "text",
          timeout: 8000,
          success: function(raw) {
            var parsed = parseCmsFrontmatter(raw);
            if (parsed.meta.title) {
              var isWire = parsed.meta.source_type === "wire" || !!parsed.meta.source_url;
              articles.push({
                title: parsed.meta.title,
                url: "article.html?slug=" + encodeURIComponent(filename.replace(/\.md$/, "")),
                description: parsed.meta.summary || "",
                source: isWire ? (parsed.meta.author || "Wire") : "The Mutapa Times",
                publishedAt: parsed.meta.date || "",
                isLocal: false,
                isCmsArticle: !isWire,
                hasCmsPage: true,
                featured: parsed.meta.featured === true || parsed.meta.featured === "true",
                headlinePosition: parseInt(parsed.meta.headline_position, 10) || 0
              });
            }
          },
          complete: function() {
            pending--;
            if (pending === 0) callback(articles);
          }
        });
      });
    },
    error: function() {
      // Fallback: try local index.json
      $.ajax({
        type: "GET",
        url: "content/articles/index.json",
        dataType: "json",
        timeout: 5000,
        success: function(files) {
          if (!files || !files.length) { callback([]); return; }
          var pending = files.length;
          var articles = [];
          files.forEach(function(filename) {
            $.ajax({
              type: "GET",
              url: "content/articles/" + filename,
              dataType: "text",
              timeout: 5000,
              success: function(raw) {
                var parsed = parseCmsFrontmatter(raw);
                if (parsed.meta.title) {
                  var isWire = parsed.meta.source_type === "wire" || !!parsed.meta.source_url;
                  articles.push({
                    title: parsed.meta.title,
                    url: "article.html?slug=" + encodeURIComponent(filename.replace(/\.md$/, "")),
                    description: parsed.meta.summary || "",
                    source: isWire ? (parsed.meta.author || "Wire") : "The Mutapa Times",
                    publishedAt: parsed.meta.date || "",
                    isLocal: false,
                    isCmsArticle: !isWire,
                    hasCmsPage: true,
                    featured: parsed.meta.featured === true || parsed.meta.featured === "true",
                    headlinePosition: parseInt(parsed.meta.headline_position, 10) || 0
                  });
                }
              },
              complete: function() {
                pending--;
                if (pending === 0) callback(articles);
              }
            });
          });
        },
        error: function() { callback([]); }
      });
    }
  });
}

function parseCmsFrontmatter(raw) {
  var match = raw.match(/^---\s*\n([\s\S]*?)\n---\s*\n([\s\S]*)$/);
  if (!match) return { meta: {}, body: raw };
  var meta = {};
  var lines = match[1].split("\n");
  for (var i = 0; i < lines.length; i++) {
    var colon = lines[i].indexOf(":");
    if (colon === -1) continue;
    var key = lines[i].substring(0, colon).trim();
    var val = lines[i].substring(colon + 1).trim();
    if ((val.charAt(0) === '"' && val.charAt(val.length - 1) === '"') ||
        (val.charAt(0) === "'" && val.charAt(val.length - 1) === "'")) {
      val = val.substring(1, val.length - 1);
    }
    meta[key] = val;
  }
  return { meta: meta, body: match[2] };
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
  var archiveLoaded = false;
  var rssComplete = false;
  var cmsLoaded = false;

  var _mainTimeout = setTimeout(function() {
    if (document.querySelector('#main-stories .loading-msg')) {
      document.querySelector('#main-stories').innerHTML =
        '<p class="loading-msg">We couldn\u2019t load stories right now. Please refresh the page to try again.</p>';
    }
  }, 15000);

  function finalizeMainStories() {
    if (!rssComplete || !archiveLoaded || !cmsLoaded) return;
    clearTimeout(_mainTimeout);
    allArticles = deduplicateArticles(allArticles);
    allArticles = allArticles.filter(function(a) {
      // CMS/featured articles bypass age filter — they are editorially managed
      if (a.isCmsArticle || a.featured) return true;
      return isValidArticle(a.publishedAt);
    });
    allArticles = deduplicateByTopic(allArticles, 0.4);
    sortArticles(allArticles);
    setCache(cacheKey, allArticles);
    _allMainArticles = allArticles;
    _currentPage = 1;
    renderMainStories(allArticles);
  }

  // Load archived articles from data/archive.json
  $.ajax({
    type: "GET",
    url: MUTAPA_CONFIG.DATA_PATH + "archive.json",
    dataType: "json",
    success: function(data) {
      if (data && data.articles) {
        var archived = data.articles.map(function(a) {
          // Normalize source format (archive may store {name:...} objects)
          var srcName = a.source;
          if (typeof a.source === 'object' && a.source !== null) {
            srcName = a.source.name || '';
          }
          return {
            title: a.title || '',
            url: a.url || '',
            description: a.description || '',
            publishedAt: a.publishedAt || '',
            source: srcName,
            isLocal: false
          };
        });
        allArticles = allArticles.concat(archived);
      }
    },
    complete: function() {
      archiveLoaded = true;
      finalizeMainStories();
    }
  });

  // Load CMS articles (original content published via Sveltia CMS)
  // Prepend so CMS articles appear first and win deduplication over RSS duplicates
  loadCmsArticles(function(cmsArticles) {
    if (cmsArticles && cmsArticles.length) {
      allArticles = cmsArticles.concat(allArticles);
    }
    cmsLoaded = true;
    finalizeMainStories();
  });

  // Load live RSS feeds in parallel
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
          rssComplete = true;
          finalizeMainStories();
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
          allArticles = allArticles.filter(function(a) { return isValidArticle(a.publishedAt); });
          // Sort sidebar by recency
          allArticles.sort(function(a, b) {
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

// Date validation — reject articles older than FEED_MAX_AGE_MS or with unparseable dates
function isValidArticle(dateStr) {
  if (!dateStr) return false;
  try {
    var d = new Date(dateStr);
    if (isNaN(d.getTime())) return false;
    // Hard floor: reject anything before 2024 to block archival content
    if (d.getFullYear() < 2024) return false;
    // Reject articles older than the feed max age (7 days)
    return (Date.now() - d.getTime()) < FEED_MAX_AGE_MS;
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

// Deduplicate by title similarity — CMS articles (with local pages) always win
function deduplicateArticles(articles) {
  var seen = {};     // key -> index in result
  var result = [];
  for (var i = 0; i < articles.length; i++) {
    var key = articles[i].title.toLowerCase().replace(/[^a-z0-9]/g, '').substring(0, 60);
    if (seen[key] === undefined) {
      seen[key] = result.length;
      result.push(articles[i]);
    } else if (articles[i].hasCmsPage && !result[seen[key]].hasCmsPage) {
      // Replace external duplicate with the CMS version that has a local page
      result[seen[key]] = articles[i];
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
    // Never remove CMS articles — they were intentionally published
    if (articles[i].hasCmsPage) {
      result.push(articles[i]);
      topicCache.push(getTopicWords(articles[i].title));
      continue;
    }
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

function addUtm(url, medium) {
  if (!url) return url;
  var sep = url.indexOf('?') === -1 ? '?' : '&';
  return url + sep + 'utm_source=mutapatimes&utm_medium=' + (medium || 'share') + '&utm_campaign=reader_share';
}

function createShareBtn(title, url) {
  var btn = $('<button class="share-btn" title="Share this article">').html(SHARE_ICON_SVG);
  btn.on('click', function(e) {
    e.preventDefault();
    e.stopPropagation();
    var trackedUrl = addUtm(url, 'share');
    var shareText = title + '\n\n' + trackedUrl + '\n\nvia The Mutapa Times \u2014 Zimbabwe news from 100+ sources \ud83c\uddff\ud83c\uddfc\nhttps://www.mutapatimes.com?utm_source=mutapatimes&utm_medium=share&utm_campaign=reader_share';
    var shareData = {
      title: title + ' | The Mutapa Times',
      text: shareText,
      url: trackedUrl
    };
    if (navigator.share) {
      navigator.share(shareData).catch(function(err) {
        if (err.name !== 'AbortError') console.warn('Share failed:', err);
      });
    } else {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(shareText);
      } else {
        var temp = document.createElement('textarea');
        temp.value = shareText;
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
    var trackedUrl = addUtm(url, 'whatsapp');
    var text = encodeURIComponent(title + '\n\n' + trackedUrl + '\n\nvia The Mutapa Times \u2014 Zimbabwe news from 100+ sources \ud83c\uddff\ud83c\uddfc\nhttps://www.mutapatimes.com?utm_source=mutapatimes&utm_medium=whatsapp&utm_campaign=reader_share');
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

    // Portrait format — dark card with skyline image fade
    var W = 1080, H = 1350;
    var canvas = document.createElement('canvas');
    canvas.width = W;
    canvas.height = H;
    var ctx = canvas.getContext('2d');
    var pad = 64;
    var contentWidth = W - pad * 2;

    // ─── Dark background ───
    ctx.fillStyle = '#0f1a12';
    ctx.fillRect(0, 0, W, H);

    // ─── Skyline image at top with gradient fade ───
    var skyH = 420;
    if (skylineImg) {
      var sRatio = skylineImg.naturalWidth / skylineImg.naturalHeight;
      var sW = W, sH = W / sRatio;
      if (sH < skyH) { sH = skyH; sW = skyH * sRatio; }
      var sX = (W - sW) / 2, sY = 0;
      ctx.drawImage(skylineImg, sX, sY, sW, sH);
      // Gradient fade from image into dark bg
      var fadeGrd = ctx.createLinearGradient(0, skyH * 0.3, 0, skyH);
      fadeGrd.addColorStop(0, 'rgba(15,26,18,0)');
      fadeGrd.addColorStop(1, 'rgba(15,26,18,1)');
      ctx.fillStyle = fadeGrd;
      ctx.fillRect(0, 0, W, skyH);
    }

    // ─── Masthead overlay on image ───
    ctx.textBaseline = 'top';
    ctx.fillStyle = 'rgba(255,255,255,0.95)';
    ctx.font = '900 68px "Playfair Display", Georgia, serif';
    var mastheadText = 'THE MUTAPA TIMES';
    var mastheadW = ctx.measureText(mastheadText).width;
    ctx.fillText(mastheadText, (W - mastheadW) / 2, 32);

    // Thin rule under masthead
    ctx.fillStyle = 'rgba(255,255,255,0.3)';
    ctx.fillRect(pad, 116, contentWidth, 1);

    // ─── Category / Source pill ───
    var y = skyH + 30;
    ctx.font = '600 15px "Inter", "Helvetica Neue", sans-serif';
    ctx.fillStyle = 'rgba(255,255,255,0.5)';
    var labelParts = [];
    if (articleData.isLocal) labelParts.push('LOCAL');
    else if (articleData.source) labelParts.push('FOREIGN');
    if (articleData.category) labelParts.push(articleData.category.toUpperCase());
    if (labelParts.length) {
      ctx.fillText(labelParts.join('  \u2022  '), pad, y);
      y += 36;
    }

    // ─── Headline — large, white, serif ───
    var titleLen = (articleData.title || '').length;
    var headlineSize = titleLen > 120 ? 38 : (titleLen > 80 ? 44 : (titleLen > 50 ? 50 : 58));
    var headlineLineH = Math.round(headlineSize * 1.3);
    ctx.font = '700 ' + headlineSize + 'px "Playfair Display", Georgia, serif';
    ctx.fillStyle = '#ffffff';
    y = shareCardWrapText(ctx, articleData.title || '', pad, y, contentWidth, headlineLineH, H - 340, 5);
    y += 24;

    // ─── Source + date line ───
    ctx.font = '500 18px "Inter", "Helvetica Neue", sans-serif';
    ctx.fillStyle = 'rgba(255,255,255,0.6)';
    var metaParts = [];
    if (articleData.source) metaParts.push(articleData.source);
    var pubDate = formatDate(articleData.publishedAt);
    if (pubDate) metaParts.push(pubDate);
    if (metaParts.length) {
      ctx.fillText(metaParts.join('  \u00b7  '), pad, y);
      y += 40;
    }

    // ─── Article image (if available) ───
    if (articleImg) {
      var artImgW = contentWidth;
      var artImgH = Math.round(artImgW * 0.5);
      var maxImgH = H - y - 240;
      if (artImgH > maxImgH) artImgH = maxImgH;
      if (artImgH > 100) {
        ctx.save();
        // Rounded corners
        var r = 8;
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
    var footerY = H - 160;
    if (articleData.description && y < footerY - 60) {
      ctx.font = '400 20px "Inter", "Helvetica Neue", sans-serif';
      ctx.fillStyle = 'rgba(255,255,255,0.55)';
      ctx.textBaseline = 'top';
      var desc = articleData.description;
      if (desc.length > 180) desc = desc.substring(0, 177) + '...';
      y = shareCardWrapText(ctx, desc, pad, y, contentWidth, 30, footerY - 20, 3);
    }

    // ─── Footer area ───
    ctx.fillStyle = 'rgba(255,255,255,0.15)';
    ctx.fillRect(pad, footerY, contentWidth, 1);
    footerY += 24;

    // Domain
    ctx.font = '700 22px "Inter", "Helvetica Neue", sans-serif';
    ctx.fillStyle = '#ffffff';
    ctx.textBaseline = 'top';
    ctx.fillText('mutapatimes.com', pad, footerY);

    // "Read more" CTA pill — brand green
    var ctaText = 'Read more';
    ctx.font = '600 15px "Inter", "Helvetica Neue", sans-serif';
    var ctaW = ctx.measureText(ctaText).width + 32;
    var ctaH = 34;
    var ctaX = W - pad - ctaW;
    var ctaY = footerY - 2;
    var ctaR = 4;
    ctx.fillStyle = '#2e7d42';
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
    ctx.fillStyle = '#ffffff';
    ctx.textBaseline = 'middle';
    ctx.fillText(ctaText, ctaX + 16, ctaY + ctaH / 2 + 1);

    // Tagline
    ctx.textBaseline = 'top';
    ctx.font = '400 16px "Helvetica Neue", Arial, sans-serif';
    ctx.fillStyle = 'rgba(255,255,255,0.35)';
    ctx.fillText('Business & intelligence \u2014 Zimbabwe, outside-in', pad, footerY + 48);

    // Convert to blob
    return new Promise(function(resolve) {
      canvas.toBlob(function(blob) { resolve(blob); }, 'image/png');
    });
  });
}

function createImageShareBtn(articleData) {
  var btn = $('<button class="image-share-btn" title="Share">').html(SHARE_ICON_SVG);
  btn.on('click', function(e) {
    e.preventDefault();
    e.stopPropagation();

    var original = btn.html();
    btn.text('\u2026');

    generateShareImage(articleData).then(function(blob) {
      var shareText = articleData.title + '\n\n\ud83d\udd17 ' + (articleData.url || 'https://www.mutapatimes.com') + '\n\n\ud83c\uddff\ud83c\uddfc Stay informed on Zimbabwe \u2014 follow @MutapaTimes for daily news, analysis & more.\n\ud83d\udcf0 https://www.mutapatimes.com';

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
  group.append(createWhatsAppBtn(title, url));
  // Share icon = image card by default
  if (articleData) {
    group.append(createImageShareBtn(articleData));
  } else {
    group.append(createShareBtn(title, url));
  }
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

  // Apply category filter
  if (_activeCategory === "_verified") {
    filtered = filtered.filter(function(a) { return isReputableSource(a.source); });
  } else if (_activeCategory === "_local") {
    filtered = filtered.filter(function(a) { return a.isLocal || isLocalZimSource(a.source); });
  } else if (_activeCategory !== "all") {
    filtered = filtered.filter(function(a) {
      return inferCategory(a.title) === _activeCategory;
    });
  }

  // Pagination
  var totalArticles = filtered.length;
  var totalPages = Math.ceil(totalArticles / ARTICLES_PER_PAGE);
  if (_currentPage > totalPages) _currentPage = totalPages;
  if (_currentPage < 1) _currentPage = 1;
  var startIdx = (_currentPage - 1) * ARTICLES_PER_PAGE;
  var endIdx = Math.min(startIdx + ARTICLES_PER_PAGE, totalArticles);
  var pageArticles = filtered.slice(startIdx, endIdx);

  for (var i = 0; i < pageArticles.length; i++) {
    var a = pageArticles[i];
    var rank = i + 1;
    var readTime = getReadingTime(a.description);
    var pubDate = formatDate(a.publishedAt);
    var isJustNow = isBreakingRecent(a.publishedAt);

    var card = $('<article class="main-article">');
    if (rank === 1 && _currentPage === 1) card.addClass("rank-featured");

    var link = $('<a>').attr('href', a.url || '#');
    if (!a.isCmsArticle) link.attr('target', '_blank').attr('rel', 'noopener nofollow');

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
    if (a.isCmsArticle) {
      tagRow.append($('<span class="press-marker original-press">').text("Original"));
    } else if (a.isLocal) {
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

    // Insert break image with caption after every 4 articles (page 1 only)
    if (_currentPage === 1 && rank % 4 === 0 && rank < 16) {
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

  // Pagination controls
  if (totalPages > 1) {
    var pager = $('<div class="pagination">');
    var info = $('<span class="pagination-info">').text(
      "Page " + _currentPage + " of " + totalPages + " (" + totalArticles + " articles)"
    );
    pager.append(info);

    var controls = $('<div class="pagination-controls">');
    if (_currentPage > 1) {
      var prevBtn = $('<button class="pagination-btn">').html("&laquo; Previous");
      prevBtn.on("click", function() {
        _currentPage--;
        renderMainStories(_allMainArticles);
        $("html, body").animate({ scrollTop: container.offset().top - 80 }, 300);
      });
      controls.append(prevBtn);
    }

    // Page number buttons (show up to 5 around current)
    var startPage = Math.max(1, _currentPage - 2);
    var endPage = Math.min(totalPages, startPage + 4);
    if (endPage - startPage < 4) startPage = Math.max(1, endPage - 4);
    for (var p = startPage; p <= endPage; p++) {
      var pageBtn = $('<button class="pagination-btn pagination-num">').text(p);
      if (p === _currentPage) pageBtn.addClass("active");
      pageBtn.data("page", p);
      pageBtn.on("click", function() {
        _currentPage = $(this).data("page");
        renderMainStories(_allMainArticles);
        $("html, body").animate({ scrollTop: container.offset().top - 80 }, 300);
      });
      controls.append(pageBtn);
    }

    if (_currentPage < totalPages) {
      var nextBtn = $('<button class="pagination-btn">').html("Next &raquo;");
      nextBtn.on("click", function() {
        _currentPage++;
        renderMainStories(_allMainArticles);
        $("html, body").animate({ scrollTop: container.offset().top - 80 }, 300);
      });
      controls.append(nextBtn);
    }
    pager.append(controls);
    container.append(pager);
  }

  // Inject structured data for SEO
  injectArticleSchema(pageArticles, 'main');

  // Subscribe banner — full-height CTA after weather (only once)
  if ($(".subscribe-banner").length) return;
  var BREVO_FORM_URL = "https://e8bb9c12.sibforms.com/serve/MUIFANhyo5KAv45zGQtXk46aajtYgiqbLYvK0dXstXNkrCWwsrDeJG7IjtjBOM4LZfCQpFxjgq1NguOQm0ZMtALVI-9f2BYGEwxlGoGnDBiTqyPNvC7vR6D1lPLC4UWJqvOevKNHiUd0f5-o093A3UQ7iNImM7AC4as67y6Jo4WrQKPW8qEiHVivLeAnaT1wNM2xeUW1a6EmaLlvJg==";
  var contentLayout = $(".content-layout");
  if (contentLayout.length) {
    // Hidden iframe for cross-origin form
    var iframeName = "brevo-subscribe-frame";
    $("body").append($('<iframe>').attr({ name: iframeName, style: "display:none;width:0;height:0;border:0;" }));

    // Build the full-height subscribe section
    var subscribe = $('<section class="subscribe-banner">');

    // Left column — copy + form
    var leftCol = $('<div class="subscribe-col-left">');
    leftCol.append($('<p class="subscribe-label">').text("The Mutapa Times Newsletter"));
    leftCol.append($('<h2 class="subscribe-title">').text("Essential intelligence for the Zimbabwean diaspora."));
    leftCol.append($('<p class="subscribe-text">').text("Curated foreign press coverage, economic data, and original analysis\u2014delivered three times a week to readers in over 30 countries."));

    // Value prop pills
    var pills = $('<div class="subscribe-pills">');
    var pillData = [
      { icon: "\ud83c\udf0d", text: "Foreign press coverage" },
      { icon: "\ud83d\udcc8", text: "Live market data" },
      { icon: "\ud83d\udcdd", text: "Original analysis" },
      { icon: "\u26a1", text: "3\u00d7 per week" }
    ];
    pillData.forEach(function(p) {
      pills.append($('<span class="subscribe-pill">').html('<span class="subscribe-pill-icon">' + p.icon + '</span> ' + p.text));
    });
    leftCol.append(pills);

    // Form
    var form = $('<form class="subscribe-form">');
    if (BREVO_FORM_URL) {
      form.attr({ method: "POST", action: BREVO_FORM_URL, target: iframeName });
    }
    form.append($('<input class="subscribe-input" type="email" name="EMAIL" placeholder="Enter your email address" required autocomplete="email">'));
    form.append($('<button class="subscribe-btn" type="submit">').text("Subscribe \u2014 It\u2019s Free"));
    leftCol.append(form);

    var statusMsg = $('<p class="subscribe-status">').hide();
    leftCol.append(statusMsg);
    leftCol.append($('<p class="subscribe-fine">').html('Free forever \u00b7 No spam \u00b7 Unsubscribe anytime \u00b7 <a href="terms.html">Terms</a>'));

    // Right column — interactive infographic
    var rightCol = $('<div class="subscribe-col-right">');
    rightCol.append(
      '<div class="subscribe-infographic">' +
        '<div class="subscribe-ig-header">The Mutapa Times in Numbers</div>' +
        '<div class="subscribe-ig-grid">' +
          '<div class="subscribe-ig-card" data-ig="articles">' +
            '<div class="subscribe-ig-value"><span class="subscribe-ig-counter" data-target="0">-</span></div>' +
            '<div class="subscribe-ig-label">Articles on site</div>' +
            '<div class="subscribe-ig-bar"><div class="subscribe-ig-bar-fill" data-fill="85"></div></div>' +
          '</div>' +
          '<div class="subscribe-ig-card" data-ig="people">' +
            '<div class="subscribe-ig-value"><span class="subscribe-ig-counter" data-target="0">-</span></div>' +
            '<div class="subscribe-ig-label">People in directory</div>' +
            '<div class="subscribe-ig-bar"><div class="subscribe-ig-bar-fill" data-fill="60"></div></div>' +
          '</div>' +
          '<div class="subscribe-ig-card" data-ig="sources">' +
            '<div class="subscribe-ig-value"><span class="subscribe-ig-counter" data-target="0">-</span>+</div>' +
            '<div class="subscribe-ig-label">Global sources</div>' +
            '<div class="subscribe-ig-bar"><div class="subscribe-ig-bar-fill" data-fill="70"></div></div>' +
          '</div>' +
          '<div class="subscribe-ig-card" data-ig="updates">' +
            '<div class="subscribe-ig-value">Every <span class="subscribe-ig-pulse">3h</span></div>' +
            '<div class="subscribe-ig-label">Headlines refreshed</div>' +
            '<div class="subscribe-ig-live"><span class="subscribe-ig-live-dot"></span> Live</div>' +
          '</div>' +
        '</div>' +
        '<p class="subscribe-ig-footnote">Data updates automatically from our intelligence feeds</p>' +
      '</div>'
    );

    subscribe.append(leftCol).append(rightCol);

    // Place after weather
    var weatherSection = $(".weather-section");
    if (weatherSection.length) {
      weatherSection.after(subscribe);
    } else {
      contentLayout.after(subscribe);
    }

    // Populate infographic with real site data
    setTimeout(function() {
      // Total articles — use _allMainArticles array
      var articleCount = (typeof _allMainArticles !== 'undefined') ? _allMainArticles.length : 0;
      if (articleCount > 0) {
        subscribe.find('[data-ig="articles"] .subscribe-ig-counter').attr('data-target', articleCount);
      }

      // People count — fetch from cache or count via API
      var peopleCache = null;
      try { peopleCache = JSON.parse(localStorage.getItem("mutapa_people_cache")); } catch(e) {}
      if (peopleCache && peopleCache.data && peopleCache.data.length) {
        subscribe.find('[data-ig="people"] .subscribe-ig-counter').attr('data-target', peopleCache.data.length);
      } else {
        // Fallback: count from the people page if cached data not available
        $.getJSON("data/archive.json").done(function(d) {
          // Just use a reasonable estimate from archive
        });
      }

      // Unique sources — count across all loaded articles
      var sources = {};
      if (typeof _allMainArticles !== 'undefined') {
        _allMainArticles.forEach(function(a) {
          var s = a.source || (a.source && a.source.name);
          if (typeof s === 'object' && s.name) s = s.name;
          if (s) sources[s] = true;
        });
      }
      $(".storyBlock .storySource, .story-source, .headline-source").each(function() {
        var s = $(this).text().trim();
        if (s) sources[s] = true;
      });
      var srcCount = Object.keys(sources).length;
      if (srcCount > 0) {
        subscribe.find('[data-ig="sources"] .subscribe-ig-counter').attr('data-target', srcCount);
      }

      // Animate counters on scroll into view
      var animated = false;
      function animateCounters() {
        if (animated) return;
        var bannerTop = subscribe[0].getBoundingClientRect().top;
        if (bannerTop < window.innerHeight + 100) {
          animated = true;
          subscribe.find('.subscribe-ig-counter').each(function() {
            var el = $(this);
            var target = parseInt(el.attr('data-target'), 10);
            if (!target || target <= 0) return;
            var duration = 1600;
            var start = 0;
            var startTime = null;
            function step(ts) {
              if (!startTime) startTime = ts;
              var progress = Math.min((ts - startTime) / duration, 1);
              // Ease-out cubic
              var eased = 1 - Math.pow(1 - progress, 3);
              var current = Math.round(start + (target - start) * eased);
              el.text(current);
              if (progress < 1) requestAnimationFrame(step);
            }
            requestAnimationFrame(step);
          });

          // Animate bars
          subscribe.find('.subscribe-ig-bar-fill').each(function() {
            var el = $(this);
            var fill = el.data('fill') || 50;
            el.css('width', fill + '%');
          });

          $(window).off('scroll.igAnim');
        }
      }
      $(window).on('scroll.igAnim', animateCounters);
      animateCounters(); // check immediately in case already in view
    }, 2500);

    // Form submission handler
    form.on("submit", function(e) {
      var emailVal = form.find('input[name="EMAIL"]').val();
      if (!emailVal) { e.preventDefault(); return; }
      if (!BREVO_FORM_URL) {
        e.preventDefault();
        statusMsg.text("Subscriptions coming soon.").css("color", "#6b6b6b").show();
        return;
      }
      var btn = form.find('button');
      btn.prop('disabled', true).text("Subscribing\u2026");
      statusMsg.text("Subscribing\u2026").css("color", "#6b6b6b").show();
      setTimeout(function() {
        statusMsg.text("Welcome to the Mutapa Times.").css("color", "#00897b");
        form.find("input").val("");
        btn.prop('disabled', false).text("Subscribe \u2014 It\u2019s Free");
      }, 2000);
    });
  }
}

// ============================================================
// SPOTLIGHT — GNews data with RSS fallback
// ============================================================
var GNEWS_CATEGORIES = ["business", "technology", "entertainment", "sports", "science", "health"];

// Check if all spotlight articles are stale (older than 48 hours)
function spotlightIsStale(articles) {
  var maxAge = 7 * 24 * 60 * 60 * 1000; // 7 days — international outlets don't cover Zimbabwe daily
  for (var i = 0; i < articles.length; i++) {
    var pub = articles[i].publishedAt;
    if (pub) {
      try {
        var d = new Date(pub);
        if (!isNaN(d.getTime()) && (Date.now() - d.getTime()) < maxAge) {
          return false; // at least one article is fresh
        }
      } catch (e) {}
    }
  }
  return true; // all articles are stale or have no date
}

function loadSpotlightStories() {
  var cacheKey = "spotlight_all";
  var cached = getCache(cacheKey);
  if (cached && !spotlightIsStale(cached)) {
    renderSpotlightStories(cached);
    return;
  }

  // Load pre-fetched spotlight articles (GNews API / RSS — includes images + descriptions)
  $.ajax({
    type: "GET",
    url: MUTAPA_CONFIG.DATA_PATH + "spotlight.json",
    dataType: "json",
    success: function(data) {
      if (data && data.articles && data.articles.length > 0 && !spotlightIsStale(data.articles)) {
        setCache(cacheKey, data.articles);
        // Populate verified GNews extras before rendering so spotlight can use them
        if (data.more && data.more.length > 0) {
          _gnewsMoreArticles = data.more.filter(function(a) { return a.cms || isReputableSource(a.source); });
        }
        renderSpotlightStories(data.articles);
      } else {
        // Data file missing, empty, or stale — fall back to live RSS
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
        '<p class="loading-msg">Spotlight stories are temporarily unavailable.</p>';
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
          // Reputable sources first; if under 3, allow unverified business articles
          var reputable = allArticles.filter(function(a) { return isReputableSource(a.source); });
          var merged = reputable.slice(0, 3);
          if (merged.length < 3) {
            var business = allArticles.filter(function(a) {
              return !isReputableSource(a.source) && inferCategory(a.title) === "Business";
            });
            merged = merged.concat(business.slice(0, 3 - merged.length));
          }
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
    container.html('<p class="loading-msg">No spotlight stories available.</p>');
    return;
  }

  // Reputable sources first; if under 3, allow unverified business articles
  var reputable = articles.filter(function(a) { return isReputableSource(a.source); });
  var rest = articles.filter(function(a) { return !isReputableSource(a.source) && inferCategory(a.title) === "Business"; });
  articles = reputable.concat(rest).slice(0, 3);
  if (articles.length === 0) {
    container.html('<p class="loading-msg">No spotlight stories available.</p>');
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

  // Render green spotlight items: CMS-promoted articles first, then regular extras
  var cmsExtras = _gnewsMoreArticles.filter(function(a) {
    return a.cms && a.url && !_spotlightUrls[a.url];
  });
  var gnewsExtras = _gnewsMoreArticles.filter(function(a) {
    return !a.cms && a.url && !_spotlightUrls[a.url];
  }).slice(0, 2);
  var greenItems = cmsExtras.concat(gnewsExtras);

  for (var j = 0; j < greenItems.length; j++) {
    var g = greenItems[j];
    if (g.url) _spotlightUrls[g.url] = true;
    var gDate = formatDate(g.publishedAt);
    var gItem = $('<article class="spotlight-item spotlight-gnews">');
    var gLink = $('<a>').attr('href', g.url || '#');
    // CMS articles are internal links; external articles open in new tab
    if (!g.cms) {
      gLink.attr('target', '_blank').attr('rel', 'noopener nofollow');
    }
    if (g.image) {
      gLink.append($('<img class="spotlight-img">').attr('src', g.image).attr('alt', g.title || ''));
    }
    var gText = $('<div class="spotlight-text">');
    gText.append($('<h4 class="spotlight-title">').text(g.title));
    var gDesc = g.description;
    if (gDesc && gDesc.length > 200) gDesc = gDesc.substring(0, 200) + "...";
    if (gDesc) gText.append($('<p class="spotlight-desc">').text(gDesc));
    var gMeta = $('<p class="spotlight-meta">');
    if (g.source) {
      gMeta.append($('<span class="verified-source">').text(g.source));
      gMeta.append($('<span class="verified-badge" title="Verified source">').html('&#10003;'));
    }
    if (gDate) {
      if (g.source) gMeta.append(document.createTextNode(" \u00b7 "));
      var gTimeEl = $('<time>').text(gDate);
      try { var gDt = new Date(g.publishedAt); if (!isNaN(gDt.getTime())) gTimeEl.attr('datetime', gDt.toISOString()); } catch (e) {}
      gMeta.append(gTimeEl);
    }
    gMeta.append(createShareGroup(g.title, g.url, {
      title: g.title, source: g.source, description: gDesc,
      url: g.url, category: '', isLocal: g.cms || false,
      publishedAt: g.publishedAt, image: g.image || ''
    }));
    gText.append(gMeta);
    gLink.append(gText);
    gItem.append(gLink);
    container.append(gItem);
  }

  // Inject structured data for SEO
  injectArticleSchema(articles, 'spotlight');

  // Load CMS spotlight articles live (fallback if not yet in spotlight.json)
  if (!cmsExtras.length) {
    loadCmsSpotlightArticles(container);
  }
}

// ============================================================
// CMS Spotlight: fetch articles with spotlight: true from GitHub
// ============================================================
function loadCmsSpotlightArticles(container) {
  if (!container || !container.length) return;

  var cacheKey = "cms_spotlight_cache";
  var cached = getCache(cacheKey);
  if (cached && cached.length) {
    appendCmsSpotlightItems(container, cached);
    return;
  }

  var apiUrl = "https://api.github.com/repos/" + MUTAPA_CONFIG.GITHUB_REPO
    + "/contents/content/articles?ref=" + MUTAPA_CONFIG.GITHUB_BRANCH;

  $.getJSON(apiUrl, function(entries) {
    if (!entries || !entries.length) return;
    var mdFiles = [];
    for (var i = 0; i < entries.length; i++) {
      if (entries[i].name && /\.md$/.test(entries[i].name)) {
        mdFiles.push(entries[i].name);
      }
    }
    if (!mdFiles.length) return;

    var pending = mdFiles.length;
    var spotlightItems = [];
    var rawBase = "https://raw.githubusercontent.com/" + MUTAPA_CONFIG.GITHUB_REPO
      + "/" + MUTAPA_CONFIG.GITHUB_BRANCH + "/content/articles/";

    for (var j = 0; j < mdFiles.length; j++) {
      (function(filename) {
        $.ajax({
          type: "GET",
          url: rawBase + filename,
          dataType: "text",
          success: function(raw) {
            var match = raw.match(/^---\s*\n([\s\S]*?)\n---\s*\n/);
            if (!match) return;
            var lines = match[1].split('\n');
            var meta = {};
            for (var k = 0; k < lines.length; k++) {
              var ci = lines[k].indexOf(':');
              if (ci === -1) continue;
              var key = lines[k].substring(0, ci).trim();
              var val = lines[k].substring(ci + 1).trim();
              if ((val.charAt(0) === '"' && val.charAt(val.length - 1) === '"') ||
                  (val.charAt(0) === "'" && val.charAt(val.length - 1) === "'")) {
                val = val.substring(1, val.length - 1);
              }
              meta[key] = val;
            }
            if (meta.spotlight && meta.spotlight.toLowerCase() === 'true') {
              var slug = filename.replace(/\.md$/, '');
              spotlightItems.push({
                title: meta.title || '',
                description: meta.summary || '',
                url: 'article.html?slug=' + encodeURIComponent(slug),
                image: meta.image || '',
                publishedAt: meta.date || '',
                source: 'The Mutapa Times',
                cms: true
              });
            }
          },
          complete: function() {
            pending--;
            if (pending === 0 && spotlightItems.length > 0) {
              setCache(cacheKey, spotlightItems);
              appendCmsSpotlightItems(container, spotlightItems);
            }
          }
        });
      })(mdFiles[j]);
    }
  });
}

function appendCmsSpotlightItems(container, articles) {
  for (var i = 0; i < articles.length; i++) {
    var a = articles[i];
    if (_spotlightUrls[a.url]) continue;
    _spotlightUrls[a.url] = true;

    var aDate = formatDate(a.publishedAt);
    var aItem = $('<article class="spotlight-item spotlight-gnews">');
    var aLink = $('<a>').attr('href', a.url || '#');
    if (a.image) {
      aLink.append($('<img class="spotlight-img">').attr('src', a.image).attr('alt', a.title || ''));
    }
    var aText = $('<div class="spotlight-text">');
    aText.append($('<h4 class="spotlight-title">').text(a.title));
    var aDesc = a.description;
    if (aDesc && aDesc.length > 200) aDesc = aDesc.substring(0, 200) + "...";
    if (aDesc) aText.append($('<p class="spotlight-desc">').text(aDesc));
    var aMeta = $('<p class="spotlight-meta">');
    if (a.source) {
      aMeta.append($('<span class="verified-source">').text(a.source));
      aMeta.append($('<span class="verified-badge" title="Verified source">').html('&#10003;'));
    }
    if (aDate) {
      if (a.source) aMeta.append(document.createTextNode(" \u00b7 "));
      var aTimeEl = $('<time>').text(aDate);
      try { var aDt = new Date(a.publishedAt); if (!isNaN(aDt.getTime())) aTimeEl.attr('datetime', aDt.toISOString()); } catch (e) {}
      aMeta.append(aTimeEl);
    }
    aMeta.append(createShareGroup(a.title, a.url, {
      title: a.title, source: a.source, description: aDesc,
      url: a.url, category: '', isLocal: true,
      publishedAt: a.publishedAt, image: a.image || ''
    }));
    aText.append(aMeta);
    aLink.append(aText);
    aItem.append(aLink);
    // Insert CMS items before the first regular green item
    var firstGnews = container.find('.spotlight-gnews').first();
    if (firstGnews.length && !firstGnews.data('cms')) {
      aItem.data('cms', true);
      firstGnews.before(aItem);
    } else {
      aItem.data('cms', true);
      container.append(aItem);
    }
  }
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
