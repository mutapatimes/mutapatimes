#!/usr/bin/env python3
"""
Region registry: the single source of truth for multi-edition support.

The Mutapa Times runs one edition per country. Zimbabwe is the DEFAULT region
and lives at the site root (path == ""), so all existing URLs are unchanged.
Each additional country (South Africa, etc.) is a self-similar copy rooted at
/<path>/ (e.g. /za/), with its own data_dir, content_dir and output prefix.

Adding a country = add one entry here, then wire its data sources. The build
generators and fetch scripts take a --region flag and read everything they
need (queries, sources, keywords, cities, fx pairs, output paths) from here.

NOTE on Zimbabwe values: these mirror what is currently hardcoded in
fetch_news.py (CATEGORIES, ALL_RSS_FEEDS, _ZW_KEYWORDS, _ZW_SOURCES) and
build_city_pages.py (CITIES). Keep them in sync until those modules are
refactored to import from here (planned).
"""

BASE_URL = "https://mutapatimes.com"
DEFAULT_REGION = "zw"

# A region is only announced to search engines once it is signed off. Until
# then its pages carry a noindex robots tag and its sitemap is not referenced
# in robots.txt. Flip a region's "indexable" to True at go-live.


def _gnews(query, gl="US"):
    """Build a Google News RSS search URL for a query string."""
    return f"https://news.google.com/rss/search?q={query}&hl=en&gl={gl}&ceid={gl}:en"


REGIONS = {
    # ─────────────────────────────── ZIMBABWE (default, root) ───────────────
    "zw": {
        "code": "zw",
        "name": "Zimbabwe",
        "demonym": "Zimbabwean",
        "path": "",                 # served at the site root
        "hreflang": "en-ZW",
        "indexable": True,          # live edition — indexed by search engines
        "data_dir": "data",
        "content_dir": "content",
        "category_queries": {
            "business": [_gnews("Zimbabwe+business+OR+Zimbabwe+economy+OR+Zimbabwe+finance+OR+Zimbabwe+investment+OR+Zimbabwe+mining")],
            "policy": [_gnews("Zimbabwe+policy+OR+Zimbabwe+regulation+OR+Zimbabwe+law+OR+Zimbabwe+reform+OR+Zimbabwe+sanctions+OR+Zimbabwe+SADC")],
            "technology": [_gnews("Zimbabwe+technology+OR+Zimbabwe+tech+OR+Zimbabwe+digital+OR+Zimbabwe+startup+OR+Zimbabwe+telecoms")],
            "health": [_gnews("Zimbabwe+health+OR+Zimbabwe+medical+OR+Zimbabwe+hospital")],
            "entertainment": [_gnews("Zimbabwe+entertainment+OR+Zimbabwe+music+OR+Zimbabwe+arts+OR+Zimbabwe+culture")],
            "sports": [_gnews("Zimbabwe+sports+OR+Zimbabwe+cricket+OR+Zimbabwe+football+OR+Zimbabwe+rugby")],
            "science": [_gnews("Zimbabwe+science+OR+Zimbabwe+research+OR+Zimbabwe+environment+OR+Zimbabwe+wildlife")],
        },
        "keywords": [
            "zimbabwe", "harare", "bulawayo", "mutare", "gweru", "masvingo",
            "chitungwiza", "kwekwe", "kadoma", "chegutu", "chinhoyi", "bindura",
            "mnangagwa", "zanu", "zanupf", "mdc", "chamisa", "chiwenga", "mugabe",
            "zim", "zimra", "rbz", "zimdollar", "zig", "ziggold",
            "sadc", "southern africa",
            "nyamandlovu", "hwange", "kariba", "victoria falls", "great zimbabwe",
            "mthuli ncube", "mushayavanhu",
        ],
        "sources": [
            "herald", "newsday", "zimbabwe mail", "bulawayo24", "263chat",
            "pindula", "nehanda", "newzimbabwe", "zimlive", "chronicle",
            "b-metro", "the standard", "daily news", "zbcnews", "cite",
            "the mutapa times",
        ],
        # Spotlight / API-cascade tuning. ZW values mirror the in-file
        # defaults in fetch_news.py exactly (fetch_news uses its own literals
        # for the default region, so these are documentation/parity copies).
        "spotlight_query": "Zimbabwe",
        "api_country": "zw",
        "gnews_queries": [
            "Zimbabwe business economy finance investment",
            "Zimbabwe politics government policy reform",
            "Zimbabwe technology digital",
            "Zimbabwe",
            'Zimbabwe OR "Southern Africa" OR SADC',
        ],
        "spotlight_rss": [
            "https://news.google.com/rss/search?q=Zimbabwe+site:bbc.com+OR+site:reuters.com+OR+site:nytimes.com+OR+site:theguardian.com+OR+site:aljazeera.com+OR+site:bloomberg.com+OR+site:apnews.com+OR+site:cnn.com&hl=en&gl=US&ceid=US:en",
            "https://news.google.com/rss/search?q=Zimbabwe+site:voanews.com+OR+site:africanews.com+OR+site:france24.com+OR+site:dw.com+OR+site:news24.com+OR+site:dailymaverick.co.za+OR+site:allafrica.com&hl=en&gl=US&ceid=US:en",
            'https://news.google.com/rss/search?q="Southern+Africa"+OR+SADC+OR+Zimbabwe+site:reuters.com+OR+site:bbc.com+OR+site:theguardian.com+OR+site:aljazeera.com&hl=en&gl=US&ceid=US:en',
        ],
        "all_rss_feeds": [
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
        ],
        "cities": [
            {"slug": "harare", "name": "Harare", "matchers": [r"\bharare\b"]},
            {"slug": "bulawayo", "name": "Bulawayo", "matchers": [r"\bbulawayo\b"]},
            {"slug": "mutare", "name": "Mutare", "matchers": [r"\bmutare\b"]},
            {"slug": "gweru", "name": "Gweru", "matchers": [r"\bgweru\b"]},
            {"slug": "masvingo", "name": "Masvingo", "matchers": [r"\bmasvingo\b"]},
            {"slug": "victoria-falls", "name": "Victoria Falls", "matchers": [r"victoria falls"]},
        ],
        "currency": "USD",
        "fx_base": "USD",
        "markets_index": "ZSE",
        "weather_locations": ["Harare", "Bulawayo", "Mutare", "Gweru", "Masvingo", "Victoria Falls"],
        "jobs_source": "vacancymail.co.zw",
        # Nav/footer sections that actually exist for this edition. Links to
        # anything NOT listed here are dropped, so a region never shows a dead
        # /za/fx etc. Add verticals to a region's list as they go live.
        "live_sections": ["news", "economy", "fx", "markets", "property",
                          "jobs", "articles", "originals", "weather", "cities"],
    },

    # ─────────────────────────────── SOUTH AFRICA (/za) ─────────────────────
    "za": {
        "code": "za",
        "name": "South Africa",
        "demonym": "South African",
        "path": "za",               # served at /za/
        "hreflang": "en-ZA",
        "indexable": False,         # PRE-LAUNCH: noindex until Phase 3 sign-off
        "data_dir": "data/za",
        "content_dir": "content/za",
        "category_queries": {
            "business": [_gnews("South+Africa+business+OR+South+Africa+economy+OR+JSE+OR+rand+OR+South+Africa+mining", gl="ZA")],
            "policy": [_gnews("South+Africa+policy+OR+South+Africa+regulation+OR+South+Africa+law+OR+South+Africa+reform+OR+SARB", gl="ZA")],
            "technology": [_gnews("South+Africa+technology+OR+South+Africa+tech+OR+South+Africa+startup+OR+South+Africa+fintech+OR+South+Africa+telecoms", gl="ZA")],
            "health": [_gnews("South+Africa+health+OR+South+Africa+medical+OR+South+Africa+hospital", gl="ZA")],
            "entertainment": [_gnews("South+Africa+entertainment+OR+South+Africa+music+OR+South+Africa+arts+OR+South+Africa+culture", gl="ZA")],
            "sports": [_gnews("South+Africa+sport+OR+Springboks+OR+Proteas+OR+PSL+OR+Bafana", gl="ZA")],
            "science": [_gnews("South+Africa+science+OR+South+Africa+research+OR+South+Africa+environment+OR+South+Africa+wildlife", gl="ZA")],
        },
        "keywords": [
            "south africa", "johannesburg", "joburg", "cape town", "durban",
            "pretoria", "tshwane", "gqeberha", "port elizabeth", "bloemfontein",
            "soweto", "ekurhuleni", "polokwane", "nelspruit", "kimberley",
            "ramaphosa", "anc", "da ", "eff", "sarb", "jse", "rand", "zar",
            "sars", "eskom", "load shedding", "godongwana", "kganyago",
            "western cape", "gauteng", "kwazulu", "limpopo", "mpumalanga",
        ],
        "sources": [
            "news24", "daily maverick", "businessday", "business day", "times live",
            "timeslive", "moneyweb", "iol", "sowetan", "the citizen", "mail & guardian",
            "ewn", "eyewitness news", "fin24", "businesstech", "the conversation",
            "the mutapa times",
        ],
        "spotlight_query": "South Africa",
        "api_country": "za",
        "gnews_queries": [
            "South Africa business economy finance investment",
            "South Africa policy government regulation reform",
            "South Africa technology digital fintech",
            "South Africa",
            'South Africa OR JSE OR rand OR SARB',
        ],
        "spotlight_rss": [
            "https://news.google.com/rss/search?q=South+Africa+site:bbc.com+OR+site:reuters.com+OR+site:nytimes.com+OR+site:theguardian.com+OR+site:aljazeera.com+OR+site:bloomberg.com+OR+site:apnews.com+OR+site:cnn.com&hl=en&gl=ZA&ceid=ZA:en",
            "https://news.google.com/rss/search?q=South+Africa+site:news24.com+OR+site:dailymaverick.co.za+OR+site:businesslive.co.za+OR+site:timeslive.co.za+OR+site:mg.co.za+OR+site:moneyweb.co.za+OR+site:ewn.co.za&hl=en&gl=ZA&ceid=ZA:en",
            "https://news.google.com/rss/search?q=South+Africa+site:reuters.com+OR+site:bbc.com+OR+site:theguardian.com+OR+site:aljazeera.com&hl=en&gl=ZA&ceid=ZA:en",
        ],
        "all_rss_feeds": [
            "https://news.google.com/rss/search?q=South+Africa&hl=en&gl=ZA&ceid=ZA:en",
            "https://news.google.com/rss/search?q=South+Africa+news+today&hl=en&gl=ZA&ceid=ZA:en",
            "https://news.google.com/rss/search?q=Johannesburg+OR+Cape+Town+OR+Durban&hl=en&gl=ZA&ceid=ZA:en",
            "https://news.google.com/rss/search?q=South+Africa+politics+government+economy&hl=en&gl=ZA&ceid=ZA:en",
            "https://news.google.com/rss/search?q=site:news24.com+OR+site:timeslive.co.za+OR+site:iol.co.za+OR+site:sowetanlive.co.za+OR+site:citizen.co.za&hl=en&gl=ZA&ceid=ZA:en",
            "https://news.google.com/rss/search?q=site:dailymaverick.co.za+OR+site:businesslive.co.za+OR+site:moneyweb.co.za+OR+site:mg.co.za&hl=en&gl=ZA&ceid=ZA:en",
            "https://news.google.com/rss/search?q=South+Africa+local+news&hl=en&gl=ZA&ceid=ZA:en",
            "https://news.google.com/rss/search?q=South+Africa+business+sports+entertainment+health&hl=en&gl=ZA&ceid=ZA:en",
            "https://news.google.com/rss/search?q=Johannesburg+Cape+Town+Durban+Pretoria+Gqeberha+Bloemfontein&hl=en&gl=ZA&ceid=ZA:en",
            "https://news.google.com/rss/search?q=South+Africa+site:bbc.com+OR+site:reuters.com+OR+site:nytimes.com+OR+site:theguardian.com+OR+site:aljazeera.com+OR+site:ft.com+OR+site:economist.com+OR+site:bloomberg.com+OR+site:apnews.com&hl=en&gl=ZA&ceid=ZA:en",
        ],
        "cities": [
            {"slug": "johannesburg", "name": "Johannesburg", "matchers": [r"\bjohannesburg\b", r"\bjoburg\b", r"\bjo'burg\b"]},
            {"slug": "cape-town", "name": "Cape Town", "matchers": [r"cape town"]},
            {"slug": "durban", "name": "Durban", "matchers": [r"\bdurban\b"]},
            {"slug": "pretoria", "name": "Pretoria", "matchers": [r"\bpretoria\b", r"\btshwane\b"]},
            {"slug": "gqeberha", "name": "Gqeberha", "matchers": [r"\bgqeberha\b", r"port elizabeth"]},
        ],
        "currency": "ZAR",
        "fx_base": "ZAR",
        "markets_index": "JSE",
        "weather_locations": ["Johannesburg", "Cape Town", "Durban", "Pretoria", "Gqeberha", "Bloemfontein"],
        "jobs_source": "",          # TODO: pick a South African jobs board (vacancymail is ZW-only)
        # PRE-LAUNCH: only the news edition is live. Verticals (economy/fx/
        # markets/property/jobs/weather/originals) join this list in Phase 4
        # as their SA data sources are wired, and light up across the nav.
        "live_sections": ["news", "articles", "cities"],
    },
}


def get_region(code):
    """Return the region config for a code, defaulting to Zimbabwe."""
    return REGIONS.get((code or DEFAULT_REGION).lower(), REGIONS[DEFAULT_REGION])


def region_path_prefix(code):
    """URL prefix for a region: "" for the root (Zimbabwe), "/za" for others."""
    p = get_region(code)["path"]
    return f"/{p}" if p else ""


def region_url(code, path="/"):
    """Absolute URL for a path within a region's edition."""
    prefix = region_path_prefix(code)
    if not path.startswith("/"):
        path = "/" + path
    return f"{BASE_URL}{prefix}{path}"


def region_has_section(code, name):
    """True if a nav/footer section is live for a region. When a region omits
    live_sections entirely (or the registry is unavailable) everything is
    treated as live, preserving the default-region behaviour."""
    live = get_region(code).get("live_sections")
    return True if not live else (name in live)


def region_is_indexable(code):
    """True if a region should be indexed by search engines (signed off)."""
    return bool(get_region(code).get("indexable", True))


def region_robots(code, base="index, follow"):
    """Robots meta value for a region: the given base when indexable, else the
    same directives with index -> noindex (pre-launch editions stay out of the
    index while keeping max-image-preview etc.)."""
    if region_is_indexable(code):
        return base
    out = []
    for p in (x.strip() for x in base.split(",")):
        pl = p.lower()
        out.append("noindex" if pl in ("index", "all", "noindex") else p)
    if not any(x.lower() == "noindex" for x in out):
        out.insert(0, "noindex")
    return ", ".join(out)


def all_region_codes():
    return list(REGIONS.keys())


if __name__ == "__main__":
    import json
    for code, r in REGIONS.items():
        print(f"{code}: {r['name']}  path={r['path'] or '(root)'}  "
              f"cities={[c['slug'] for c in r['cities']]}  "
              f"data_dir={r['data_dir']}  prefix={region_path_prefix(code)}")
    print("\nexample za article URL:", region_url("za", "/articles/foo.html"))
    print("example zw article URL:", region_url("zw", "/articles/foo.html"))
