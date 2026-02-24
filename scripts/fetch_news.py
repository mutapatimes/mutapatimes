#!/usr/bin/env python3
"""
Fetch Zimbabwe news from Google News RSS for all categories.
Replaces GNews API (unreliable free tier) with free, unlimited RSS.
Optionally generates AI descriptions via Gemini free tier.
"""
import json
import os
import re
import sys
import time
import urllib.request
import urllib.error
import urllib.parse
import xml.etree.ElementTree as ET

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
GNEWS_API_KEY = os.environ.get("GNEWS_API_KEY", "")
NEWSDATA_API_KEY = os.environ.get("NEWSDATA_API_KEY", "")
NEWSAPI_API_KEY = os.environ.get("NEWSAPI_API_KEY", "")
MEDIASTACK_API_KEY = os.environ.get("MEDIASTACK_API_KEY", "")
PERIGON_API_KEY = os.environ.get("PERIGON_API_KEY", "")
DATA_DIR = "data"

# Minimum articles from cascade before stopping early
MIN_SPOTLIGHT_ARTICLES = 10

# Category-specific Google News RSS feeds (replace GNews API)
# Primary categories listed first — these are the editorial focus
CATEGORIES = {
    "business": [
        "https://news.google.com/rss/search?q=Zimbabwe+business+OR+Zimbabwe+economy+OR+Zimbabwe+finance+OR+Zimbabwe+investment+OR+Zimbabwe+mining&hl=en&gl=US&ceid=US:en",
    ],
    "politics": [
        "https://news.google.com/rss/search?q=Zimbabwe+politics+OR+Zimbabwe+government+OR+Zimbabwe+ZANU+OR+Zimbabwe+election+OR+Zimbabwe+parliament+OR+Zimbabwe+Mnangagwa&hl=en&gl=US&ceid=US:en",
    ],
    "policy": [
        "https://news.google.com/rss/search?q=Zimbabwe+policy+OR+Zimbabwe+regulation+OR+Zimbabwe+law+OR+Zimbabwe+reform+OR+Zimbabwe+sanctions+OR+Zimbabwe+SADC&hl=en&gl=US&ceid=US:en",
    ],
    "technology": [
        "https://news.google.com/rss/search?q=Zimbabwe+technology+OR+Zimbabwe+tech+OR+Zimbabwe+digital+OR+Zimbabwe+startup+OR+Zimbabwe+telecoms&hl=en&gl=US&ceid=US:en",
    ],
    "health": [
        "https://news.google.com/rss/search?q=Zimbabwe+health+OR+Zimbabwe+medical+OR+Zimbabwe+hospital&hl=en&gl=US&ceid=US:en",
    ],
    "entertainment": [
        "https://news.google.com/rss/search?q=Zimbabwe+entertainment+OR+Zimbabwe+music+OR+Zimbabwe+arts+OR+Zimbabwe+culture&hl=en&gl=US&ceid=US:en",
    ],
    "sports": [
        "https://news.google.com/rss/search?q=Zimbabwe+sports+OR+Zimbabwe+cricket+OR+Zimbabwe+football+OR+Zimbabwe+rugby&hl=en&gl=US&ceid=US:en",
    ],
    "science": [
        "https://news.google.com/rss/search?q=Zimbabwe+science+OR+Zimbabwe+research+OR+Zimbabwe+environment+OR+Zimbabwe+wildlife&hl=en&gl=US&ceid=US:en",
    ],
}

# All RSS feeds for description generation (same as config.js)
ALL_RSS_FEEDS = [
    "https://news.google.com/rss/search?q=Zimbabwe&hl=en&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=Zimbabwe+news+today&hl=en&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=Harare+OR+Bulawayo+OR+Mutare&hl=en&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=Zimbabwe+politics+government+economy&hl=en&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=site:zimlive.com+OR+site:newsday.co.zw+OR+site:herald.co.zw+OR+site:bulawayo24.com+OR+site:263chat.com&hl=en&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=site:pindula.co.zw+OR+site:nehanda+radio+OR+site:newzimbabwe.com+OR+site:thezimbabwemail.com&hl=en&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=Zimbabwe+local+news&hl=en&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=Zimbabwe+business+sports+entertainment+health&hl=en&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=Harare+Bulawayo+Gweru+Masvingo+Mutare+Chitungwiza&hl=en&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=Zimbabwe+site:bbc.com+OR+site:reuters.com+OR+site:nytimes.com+OR+site:theguardian.com+OR+site:aljazeera.com+OR+site:ft.com+OR+site:economist.com+OR+site:bloomberg.com+OR+site:apnews.com&hl=en&gl=US&ceid=US:en",
]

MAX_NEW_DESCRIPTIONS = 10  # Cap per run to stay within Gemini free-tier rate limits


def fetch_url(url):
    """Fetch raw bytes from URL."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "MutapaTimes/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read()
    except Exception as e:
        print(f"    fetch error: {e}")
        return None


def parse_rss_feed(xml_bytes):
    """Parse Google News RSS XML into article dicts matching GNews format."""
    articles = []
    try:
        root = ET.fromstring(xml_bytes)
        for item in root.iter("item"):
            title_el = item.find("title")
            link_el = item.find("link")
            pub_el = item.find("pubDate")
            if title_el is None or link_el is None:
                continue

            raw_title = title_el.text or ""
            # Google News format: "Headline - Source Name"
            parts = raw_title.rsplit(" - ", 1)
            headline = parts[0].strip()
            source_name = parts[1].strip() if len(parts) > 1 else ""
            url = (link_el.text or "").strip()
            pub_date = (pub_el.text or "").strip() if pub_el is not None else ""

            if headline and url:
                articles.append({
                    "title": headline,
                    "url": url,
                    "description": "",
                    "publishedAt": pub_date,
                    "source": {"name": source_name, "url": ""},
                })
    except ET.ParseError as e:
        print(f"    XML parse error: {e}")
    return articles


def normalize_title(title):
    """Lowercase, strip punctuation/whitespace for comparison."""
    t = title.lower().strip()
    t = re.sub(r"[^\w\s]", "", t)          # strip punctuation
    t = re.sub(r"\s+", " ", t).strip()      # collapse whitespace
    return t


def titles_are_similar(t1, t2, threshold=0.65):
    """Check if two titles are about the same story using word overlap (Jaccard)."""
    w1 = set(normalize_title(t1).split())
    w2 = set(normalize_title(t2).split())
    if not w1 or not w2:
        return False
    # Also catch substring matches (wire stories with minor edits)
    n1, n2 = normalize_title(t1), normalize_title(t2)
    if n1 in n2 or n2 in n1:
        return True
    intersection = w1 & w2
    union = w1 | w2
    return len(intersection) / len(union) >= threshold


def deduplicate(articles, limit=10):
    """Deduplicate by URL AND title similarity, sort by date descending, return top N."""
    seen_urls = set()
    unique = []
    for a in articles:
        url = a.get("url", "")
        title = a.get("title", "")
        # Skip exact URL dupes
        if url and url in seen_urls:
            continue
        # Skip if a very similar headline already accepted
        if title and any(titles_are_similar(title, u.get("title", "")) for u in unique):
            continue
        if url:
            seen_urls.add(url)
        unique.append(a)
    unique.sort(key=lambda a: a.get("publishedAt", ""), reverse=True)
    return unique[:limit]


# Keywords that indicate an article is about Zimbabwe / relevant region
_ZW_KEYWORDS = [
    "zimbabwe", "harare", "bulawayo", "mutare", "gweru", "masvingo",
    "chitungwiza", "kwekwe", "kadoma", "chegutu", "chinhoyi", "bindura",
    "mnangagwa", "zanu", "zanupf", "mdc", "chamisa", "chiwenga",
    "zim", "zimra", "rbz", "zimdollar", "zig", "ziggold",
    "sadc", "southern africa",
    "nyamandlovu", "hwange", "kariba", "victoria falls", "great zimbabwe",
    "mthuli ncube", "mushayavanhu",
]

# Zimbabwean publishers — articles from these sources pass without keyword check
_ZW_SOURCES = [
    "herald", "newsday", "zimbabwe mail", "bulawayo24", "263chat",
    "pindula", "nehanda", "newzimbabwe", "zimlive", "chronicle",
    "b-metro", "the standard", "daily news", "zbcnews", "cite",
    "the mutapa times",
]


def is_zw_relevant(article):
    """Check if an article is about Zimbabwe (keyword in title/desc or from a ZW source)."""
    source = (article.get("source", "") or "").lower()
    if any(s in source for s in _ZW_SOURCES):
        return True
    text = ((article.get("title", "") or "") + " " + (article.get("description", "") or "")).lower()
    return any(kw in text for kw in _ZW_KEYWORDS)


def generate_description(title, content=""):
    """Generate a 1-2 sentence summary using Gemini free tier with rate limiting."""
    if not GEMINI_API_KEY:
        return ""

    source_text = content[:1500] if content else title
    prompt = (
        "You are a Financial Times sub-editor writing a brief for the digest. "
        "Paraphrase the headline below into a 1-2 sentence summary (under 200 characters). "
        "Tone: authoritative, concise, matter-of-fact. No editorialising. "
        "Preserve the core meaning — do not add, speculate, or omit key facts. "
        "Do not start with 'This article' or 'The article'. "
        "Just state what happened or what is happening.\n\n"
        f"Headline: {title}\n"
        f"Context: {source_text}"
    )

    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": 100, "temperature": 0.2}
    }).encode("utf-8")

    try:
        req = urllib.request.Request(
            f"{GEMINI_URL}?key={GEMINI_API_KEY}",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            text = result["candidates"][0]["content"]["parts"][0]["text"].strip()
            text = text.strip('"\'')
            # Rate limit: wait 5s between calls (free tier ~15 RPM)
            time.sleep(5)
            return text[:250] if len(text) > 250 else text
    except urllib.error.HTTPError as e:
        if e.code == 429:
            # Don't retry — just skip this article and slow down for the next one
            print(f"    Rate limited, skipping: {title[:50]}")
            time.sleep(10)
        else:
            print(f"    Gemini error: {e}")
    except Exception as e:
        print(f"    Gemini error: {e}")
    return ""


def fetch_category(name, feed_urls):
    """Fetch Zimbabwe articles for a category via Google News RSS."""
    print(f"\n=== {name.upper()} ===")

    all_articles = []
    for feed_url in feed_urls:
        xml_data = fetch_url(feed_url)
        if xml_data:
            all_articles.extend(parse_rss_feed(xml_data))

    if not all_articles:
        print(f"  FAIL: {name} — no articles found")
        # Write empty so file exists
        outpath = os.path.join(DATA_DIR, f"{name}.json")
        with open(outpath, "w") as f:
            json.dump({"articles": []}, f)
        return False

    articles = deduplicate(all_articles)

    outpath = os.path.join(DATA_DIR, f"{name}.json")
    with open(outpath, "w") as f:
        json.dump({"articles": articles}, f)
    print(f"  OK: {name} — {len(articles)} articles saved")
    return articles or []


def fetch_rss_descriptions():
    """Generate AI descriptions for main/sidebar RSS articles."""
    if not GEMINI_API_KEY:
        print("\n=== RSS DESCRIPTIONS ===")
        print("  SKIP: GEMINI_API_KEY not set")
        return

    print("\n=== RSS DESCRIPTIONS ===")

    # Load existing lookup to avoid re-generating
    lookup_path = os.path.join(DATA_DIR, "rss_descriptions.json")
    existing = {}
    if os.path.exists(lookup_path):
        try:
            with open(lookup_path) as f:
                existing = json.load(f)
        except (json.JSONDecodeError, IOError):
            existing = {}

    # Collect unique articles from all RSS feeds
    all_articles = {}
    for feed_url in ALL_RSS_FEEDS:
        xml_data = fetch_url(feed_url)
        if xml_data:
            for a in parse_rss_feed(xml_data):
                if a["url"] not in all_articles:
                    all_articles[a["url"]] = a["title"]

    print(f"  Found {len(all_articles)} unique RSS articles")

    # Generate descriptions for new articles (capped)
    new_count = 0
    descriptions = {}
    for url, title in all_articles.items():
        if url in existing and existing[url]:
            descriptions[url] = existing[url]
            continue
        if new_count >= MAX_NEW_DESCRIPTIONS:
            continue
        generated = generate_description(title)
        if generated:
            descriptions[url] = generated
            new_count += 1
            print(f"    AI desc: {title[:50]}...")

    with open(lookup_path, "w") as f:
        json.dump(descriptions, f)
    print(f"  OK: {len(descriptions)} descriptions ({new_count} new)")


def get_cms_spotlight_articles():
    """Scan content/articles/*.md for articles with spotlight: true in frontmatter."""
    import glob as glob_mod
    articles = []
    for filepath in sorted(glob_mod.glob("content/articles/*.md")):
        try:
            with open(filepath) as f:
                content = f.read()
        except IOError:
            continue

        match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
        if not match:
            continue

        meta = {}
        for line in match.group(1).split('\n'):
            idx = line.find(':')
            if idx == -1:
                continue
            key = line[:idx].strip()
            val = line[idx + 1:].strip().strip('"').strip("'")
            meta[key] = val

        if meta.get('spotlight', '').lower() != 'true':
            continue

        slug = os.path.basename(filepath).replace('.md', '')
        articles.append({
            "title": meta.get('title', ''),
            "description": meta.get('summary', ''),
            "url": "article.html?slug=" + slug,
            "image": meta.get('image', ''),
            "publishedAt": meta.get('date', ''),
            "source": "The Mutapa Times",
            "cms": True,
        })
        print(f"  CMS spotlight: {meta.get('title', filepath)}")
    return articles


### ---------------------------------------------------------------------------
### Spotlight API fetchers — each returns list[dict] in standard schema or []
### Schema: {title, description, url, image, publishedAt, source}
### ---------------------------------------------------------------------------

def fetch_from_gnews():
    """Fetch Zimbabwe articles from GNews API (5 queries, up to 100 articles)."""
    if not GNEWS_API_KEY:
        print("  GNews: API key not set, skipping")
        return []

    reputable_domains = [
        "bbc.com", "bbc.co.uk", "reuters.com", "nytimes.com",
        "theguardian.com", "aljazeera.com", "ft.com", "economist.com",
        "bloomberg.com", "apnews.com", "washingtonpost.com", "cnn.com",
        "news.sky.com", "telegraph.co.uk", "independent.co.uk",
        "france24.com", "dw.com", "npr.org", "pbs.org", "abcnews.go.com",
        "time.com", "foreignpolicy.com", "theconversation.com",
        "voanews.com", "rfi.fr", "africanews.com",
        "allafrica.com", "dailymaverick.co.za", "mg.co.za",
        "news24.com", "theeastafrican.co.ke", "sabc.co.za",
        "nation.africa", "citizen.co.za", "ewn.co.za",
        "iol.co.za", "timeslive.co.za",
    ]

    queries = [
        urllib.parse.quote("Zimbabwe business economy finance investment"),
        urllib.parse.quote("Zimbabwe politics government policy reform"),
        urllib.parse.quote("Zimbabwe technology digital"),
        "Zimbabwe",
        urllib.parse.quote('Zimbabwe OR "Southern Africa" OR SADC'),
    ]

    raw_articles = []
    for q in queries:
        url = (
            f"https://gnews.io/api/v4/search?q={q}&lang=en&max=20"
            f"&apikey={GNEWS_API_KEY}"
        )
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "MutapaTimes/1.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            batch = data.get("articles", [])
            raw_articles.extend(batch)
            print(f"  GNews: {len(batch)} articles for query: {q[:40]}...")
        except urllib.error.HTTPError as e:
            if e.code == 429:
                print("  GNews: rate limited (429), stopping queries")
                break
            print(f"  GNews: HTTP error {e.code}")
        except Exception as e:
            print(f"  GNews: error: {e}")

    if not raw_articles:
        print("  GNews: returned 0 articles")
        return []

    print(f"\n  --- All {len(raw_articles)} raw headlines from GNews ---")
    for i, a in enumerate(raw_articles):
        src = a.get("source", {}).get("name", "?")
        title = a.get("title", "")[:100]
        print(f"  [{i+1:2d}] {src:<30s} | {title}")
    print("  ---\n")

    # Normalise and sort reputable sources first
    reputable = []
    others = []
    for a in raw_articles:
        item = {
            "title": a.get("title", ""),
            "description": a.get("description", ""),
            "url": a.get("url", ""),
            "image": a.get("image", ""),
            "publishedAt": a.get("publishedAt", ""),
            "source": a.get("source", {}).get("name", ""),
        }
        source_url = a.get("source", {}).get("url", "")
        if any(d in source_url for d in reputable_domains):
            reputable.append(item)
        else:
            others.append(item)
    return reputable + others


def fetch_from_newsdata():
    """Fetch Zimbabwe articles from Newsdata.io (1 query, up to 50 articles)."""
    if not NEWSDATA_API_KEY:
        print("  Newsdata.io: API key not set, skipping")
        return []

    url = (
        f"https://newsdata.io/api/1/latest?country=zw&language=en"
        f"&q=Zimbabwe&apikey={NEWSDATA_API_KEY}"
    )
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "MutapaTimes/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 429:
            print("  Newsdata.io: rate limited (429)")
        else:
            print(f"  Newsdata.io: HTTP error {e.code}")
        return []
    except Exception as e:
        print(f"  Newsdata.io: error: {e}")
        return []

    results = data.get("results", [])
    if not results:
        print("  Newsdata.io: returned 0 articles")
        return []

    normalized = []
    for a in results:
        normalized.append({
            "title": a.get("title", "") or "",
            "description": a.get("description", "") or "",
            "url": a.get("link", "") or "",
            "image": a.get("image_url", "") or "",
            "publishedAt": a.get("pubDate", "") or "",
            "source": a.get("source_name", "") or a.get("source_id", "") or "",
        })
    print(f"  Newsdata.io: {len(normalized)} articles fetched")
    return normalized


def fetch_from_newsapi():
    """Fetch Zimbabwe articles from NewsAPI.org (1 query, up to 50 articles)."""
    if not NEWSAPI_API_KEY:
        print("  NewsAPI.org: API key not set, skipping")
        return []

    url = (
        f"https://newsapi.org/v2/everything?q=Zimbabwe&language=en"
        f"&sortBy=publishedAt&pageSize=50&apiKey={NEWSAPI_API_KEY}"
    )
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "MutapaTimes/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 429:
            print("  NewsAPI.org: rate limited (429)")
        elif e.code == 426:
            print("  NewsAPI.org: requires paid plan for this endpoint")
        else:
            print(f"  NewsAPI.org: HTTP error {e.code}")
        return []
    except Exception as e:
        print(f"  NewsAPI.org: error: {e}")
        return []

    if data.get("status") != "ok":
        print(f"  NewsAPI.org: status={data.get('status')}, message={data.get('message', '')}")
        return []

    raw_articles = data.get("articles", [])
    if not raw_articles:
        print("  NewsAPI.org: returned 0 articles")
        return []

    normalized = []
    for a in raw_articles:
        title = a.get("title", "") or ""
        if title == "[Removed]":
            continue
        source_obj = a.get("source", {}) or {}
        normalized.append({
            "title": title,
            "description": a.get("description", "") or "",
            "url": a.get("url", "") or "",
            "image": a.get("urlToImage", "") or "",
            "publishedAt": a.get("publishedAt", "") or "",
            "source": source_obj.get("name", "") or "",
        })
    print(f"  NewsAPI.org: {len(normalized)} articles fetched")
    return normalized


def fetch_from_mediastack():
    """Fetch Zimbabwe articles from Mediastack (1 query). NOTE: 100 requests/month."""
    if not MEDIASTACK_API_KEY:
        print("  Mediastack: API key not set, skipping")
        return []

    # Mediastack free tier uses HTTP only (no HTTPS)
    url = (
        f"http://api.mediastack.com/v1/news?access_key={MEDIASTACK_API_KEY}"
        f"&countries=zw&languages=en&limit=50"
    )
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "MutapaTimes/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 429:
            print("  Mediastack: rate limited (429)")
        else:
            print(f"  Mediastack: HTTP error {e.code}")
        return []
    except Exception as e:
        print(f"  Mediastack: error: {e}")
        return []

    if "error" in data:
        print(f"  Mediastack: API error: {data['error'].get('message', '')}")
        return []

    raw_articles = data.get("data", [])
    if not raw_articles:
        print("  Mediastack: returned 0 articles")
        return []

    normalized = []
    for a in raw_articles:
        normalized.append({
            "title": a.get("title", "") or "",
            "description": a.get("description", "") or "",
            "url": a.get("url", "") or "",
            "image": a.get("image", "") or "",
            "publishedAt": a.get("published_at", "") or "",
            "source": a.get("source", "") or "",
        })
    print(f"  Mediastack: {len(normalized)} articles fetched")
    return normalized


def fetch_from_perigon():
    """Fetch Zimbabwe articles from Perigon (1 query). NOTE: 150 requests/month."""
    if not PERIGON_API_KEY:
        print("  Perigon: API key not set, skipping")
        return []

    url = (
        f"https://api.goperigon.com/v1/all?q=Zimbabwe&language=en"
        f"&sortBy=date&size=50&apiKey={PERIGON_API_KEY}"
    )
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "MutapaTimes/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 429:
            print("  Perigon: rate limited (429)")
        else:
            print(f"  Perigon: HTTP error {e.code}")
        return []
    except Exception as e:
        print(f"  Perigon: error: {e}")
        return []

    raw_articles = data.get("articles", [])
    if not raw_articles:
        print("  Perigon: returned 0 articles")
        return []

    normalized = []
    for a in raw_articles:
        source_obj = a.get("source", {}) or {}
        normalized.append({
            "title": a.get("title", "") or "",
            "description": a.get("description", "") or "",
            "url": a.get("url", "") or "",
            "image": a.get("imageUrl", "") or "",
            "publishedAt": a.get("pubDate", "") or "",
            "source": source_obj.get("domain", "") or "",
        })
    print(f"  Perigon: {len(normalized)} articles fetched")
    return normalized


def fetch_from_rss():
    """Fetch spotlight articles from Google News RSS. Always works (no API key)."""
    print("  RSS fallback: fetching from Google News RSS...")
    spotlight_rss = [
        "https://news.google.com/rss/search?q=Zimbabwe+site:bbc.com+OR+site:reuters.com+OR+site:nytimes.com+OR+site:theguardian.com+OR+site:aljazeera.com+OR+site:bloomberg.com+OR+site:apnews.com+OR+site:cnn.com&hl=en&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=Zimbabwe+site:voanews.com+OR+site:africanews.com+OR+site:france24.com+OR+site:dw.com+OR+site:news24.com+OR+site:dailymaverick.co.za+OR+site:allafrica.com&hl=en&gl=US&ceid=US:en",
        'https://news.google.com/rss/search?q="Southern+Africa"+OR+SADC+OR+Zimbabwe+site:reuters.com+OR+site:bbc.com+OR+site:theguardian.com+OR+site:aljazeera.com&hl=en&gl=US&ceid=US:en',
    ]
    articles = []
    for rss_url in spotlight_rss:
        raw = fetch_url(rss_url)
        if raw:
            parsed = parse_rss_feed(raw)
            for a in parsed:
                src_name = a.get("source", {}).get("name", "") if isinstance(a.get("source"), dict) else a.get("source", "")
                articles.append({
                    "title": a.get("title", ""),
                    "description": a.get("description", ""),
                    "url": a.get("url", ""),
                    "image": "",
                    "publishedAt": a.get("publishedAt", ""),
                    "source": src_name,
                })
    print(f"  RSS fallback: {len(articles)} articles collected")
    return articles


def fetch_spotlight():
    """Fetch spotlight articles using multi-API cascade with RSS fallback."""
    print("\n=== SPOTLIGHT ===")

    # Reputable source keywords for filtering
    reputable_kw = [
        "bbc", "reuters", "nytimes", "new york times", "guardian", "al jazeera",
        "bloomberg", "ap news", "associated press", "financial times", "economist",
        "cnn", "washington post", "sky news", "france 24", "dw", "deutsche welle",
        "npr", "pbs", "abc news", "time magazine", "foreign policy", "the conversation",
        "voa", "voice of america", "rfi", "africanews",
        "allafrica", "daily maverick", "mail & guardian", "news24", "the east african",
        "sabc", "nation africa", "the citizen", "eyewitness news", "iol", "timeslive",
        "sunday times",
    ]

    # --- API Cascade: try each source until we have enough articles ---
    # Daily-limited APIs first, then monthly-limited, then RSS (always works)
    api_cascade = [
        (fetch_from_gnews,      "GNews"),
        (fetch_from_newsdata,   "Newsdata.io"),
        (fetch_from_newsapi,    "NewsAPI.org"),
        (fetch_from_mediastack, "Mediastack"),
        (fetch_from_perigon,    "Perigon"),
        (fetch_from_rss,        "RSS fallback"),
    ]

    articles = []
    source_used = "none"

    for fetcher, name in api_cascade:
        result = fetcher()
        if result:
            # Filter out non-Zimbabwe articles (game trailers, foreign sports, etc.)
            before = len(result)
            result = [a for a in result if is_zw_relevant(a)]
            if before != len(result):
                print(f"  >> {name}: {before - len(result)} non-Zimbabwe articles filtered out")
            articles.extend(result)
            if not source_used or source_used == "none":
                source_used = name
            else:
                source_used += f" + {name}"
            print(f"  >> {name}: {len(result)} articles (total: {len(articles)})")
            if len(articles) >= MIN_SPOTLIGHT_ARTICLES:
                print(f"  >> Sufficient articles ({len(articles)}) — skipping remaining APIs")
                break

    if not articles:
        print("  FAIL: no articles from any API or RSS — writing empty spotlight")
        outpath = os.path.join(DATA_DIR, "spotlight.json")
        with open(outpath, "w") as f:
            json.dump({"articles": [], "more": []}, f)
        return

    # Load existing spotlight to preserve stories that are still fresh
    outpath = os.path.join(DATA_DIR, "spotlight.json")
    existing = []
    if os.path.exists(outpath):
        try:
            with open(outpath) as f:
                existing = json.load(f).get("articles", [])
        except (json.JSONDecodeError, IOError):
            existing = []

    # Merge: new articles first, then existing ones (deduped by URL + title similarity)
    seen_urls = set()
    merged = []
    for a in articles + existing:
        url = a.get("url", "")
        title = a.get("title", "")
        if url in seen_urls:
            continue
        if title and any(titles_are_similar(title, m.get("title", "")) for m in merged):
            continue
        seen_urls.add(url)
        # Drop articles older than 7 days
        pub = a.get("publishedAt", "")
        if pub:
            try:
                from datetime import datetime, timezone
                dt = datetime.fromisoformat(pub.replace("Z", "+00:00"))
                age_days = (datetime.now(timezone.utc) - dt).days
                if age_days > 7:
                    continue
            except Exception:
                pass
        merged.append(a)

    # Sort by date (newest first)
    merged.sort(key=lambda a: a.get("publishedAt", ""), reverse=True)

    reputable_merged = [a for a in merged if any(d in a.get("source", "").lower() for d in reputable_kw)]
    others_merged = []
    for a in merged:
        if a in reputable_merged:
            continue
        if any(titles_are_similar(a.get("title", ""), r.get("title", "")) for r in reputable_merged):
            continue
        others_merged.append(a)

    print(f"  Reputable matches: {len(reputable_merged)}, Non-reputable: {len(others_merged)}")
    for a in reputable_merged[:10]:
        print(f"    PASS: {a.get('source', '?'):<30s} | {a.get('title', '')[:80]}")

    # Reputable sources for main spotlight; overflow reputable + non-reputable for green section
    spotlight = reputable_merged[:3]
    overflow_reputable = reputable_merged[3:18]  # extra reputable articles beyond top 3
    more = others_merged[:15] if others_merged else overflow_reputable[:15]

    # Inject CMS-promoted articles into the green spotlight section
    cms_spotlight = get_cms_spotlight_articles()
    if cms_spotlight:
        cms_urls = {c["url"] for c in cms_spotlight}
        more = cms_spotlight + [a for a in more if a.get("url") not in cms_urls]

    if not spotlight:
        print("  WARN: no reputable articles found — spotlight will be empty")

    with open(outpath, "w") as f:
        json.dump({"articles": spotlight, "more": more}, f)
    print(f"  OK: {len(spotlight)} spotlight + {len(more)} more ({source_used})")


def update_archive(new_articles):
    """Append new articles to archive.json, deduplicating by URL and title similarity."""
    archive_path = os.path.join(DATA_DIR, "archive.json")
    existing = []
    if os.path.exists(archive_path):
        try:
            with open(archive_path) as f:
                existing = json.load(f).get("articles", [])
        except (json.JSONDecodeError, IOError):
            existing = []

    # Build URL index of existing archive
    seen_urls = {a.get("url", "") for a in existing if a.get("url")}

    added = 0
    for a in new_articles:
        url = a.get("url", "")
        title = a.get("title", "")
        if not url or url in seen_urls:
            continue
        # Skip near-duplicate headlines already in archive
        if title and any(titles_are_similar(title, e.get("title", "")) for e in existing[-200:]):
            continue
        seen_urls.add(url)
        existing.append(a)
        added += 1

    # Sort by date descending
    existing.sort(key=lambda a: a.get("publishedAt", ""), reverse=True)

    with open(archive_path, "w") as f:
        json.dump({"articles": existing}, f)
    print(f"\n=== ARCHIVE ===")
    print(f"  Added {added} new articles, total archive: {len(existing)}")


def main():
    os.makedirs(DATA_DIR, exist_ok=True)

    # Fetch category articles from Google News RSS
    all_new = []
    for name, feeds in CATEGORIES.items():
        result = fetch_category(name, feeds)
        if result:
            all_new.extend(result)

    # Fetch spotlight articles from GNews API (1 call, includes images + descriptions)
    fetch_spotlight()

    # Append all new articles to persistent archive
    update_archive(all_new)

    print("\nDone.")


if __name__ == "__main__":
    main()
