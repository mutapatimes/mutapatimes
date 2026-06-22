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

# Brevo signup form the newsletter sign-up boxes POST to. Each Brevo form is tied
# to one contact list, so a per-region form == a per-region subscriber list. The
# Zimbabwe form is the default; give a region its own form URL here to capture
# its subscribers into its own list.
_ZW_NEWSLETTER_FORM = "https://e8bb9c12.sibforms.com/serve/MUIFANhyo5KAv45zGQtXk46aajtYgiqbLYvK0dXstXNkrCWwsrDeJG7IjtjBOM4LZfCQpFxjgq1NguOQm0ZMtALVI-9f2BYGEwxlGoGnDBiTqyPNvC7vR6D1lPLC4UWJqvOevKNHiUd0f5-o093A3UQ7iNImM7AC4as67y6Jo4WrQKPW8qEiHVivLeAnaT1wNM2xeUW1a6EmaLlvJg=="

# A region is only announced to search engines once it is signed off. Until
# then its pages carry a noindex robots tag and its sitemap is not referenced
# in robots.txt. Flip a region's "indexable" to True at go-live.


def _gnews(query, gl="US"):
    """Build a Google News RSS search URL for a query string."""
    return f"https://news.google.com/rss/search?q={query}&hl=en&gl={gl}&ceid={gl}:en"


# City desks (referenced by REGIONS below). These carry the full per-city copy
# used by scripts/build_city_pages.py (lat/lon, headline, SEO context + keywords,
# article matchers). Other consumers (nav, sitemap) read only slug/name.
_ZW_CITIES = [
    {
        "slug": "harare",
        "name": "Harare",
        "title_short": "Harare",
        "lat": -17.8252, "lon": 31.0335,
        "headline": "Harare news, today.",
        "context": (
            "Harare is the capital and largest city of Zimbabwe, "
            "headquarters of the Reserve Bank of Zimbabwe, the "
            "Zimbabwe Stock Exchange, every major bank and most "
            "listed industrial groups. The Mutapa Times tracks "
            "Harare daily — economy, business, politics, infrastructure, "
            "culture, sport — aggregating reports from local "
            "Zimbabwean newsrooms and international wire services."
        ),
        "keywords_extra": [
            "Harare news", "Harare news today", "Harare news latest",
            "latest Harare news", "Harare business news", "Harare weather",
            "Harare politics", "Harare Zimbabwe news",
            "news Harare", "Harare today",
        ],
        "matchers": [r"\bharare\b"],
    },
    {
        "slug": "bulawayo",
        "name": "Bulawayo",
        "title_short": "Bulawayo",
        "lat": -20.1539, "lon": 28.5880,
        "headline": "Bulawayo news, today.",
        "context": (
            "Bulawayo is Zimbabwe's second city, the historic capital of "
            "Matabeleland and the country's industrial heartland. The "
            "Mutapa Times covers Bulawayo daily — manufacturing, the "
            "Zimbabwe International Trade Fair, urban infrastructure, "
            "the National Railways of Zimbabwe HQ, Highlanders FC, and "
            "the cultural calendar — pulling from local newsrooms "
            "and international wires."
        ),
        "keywords_extra": [
            "Bulawayo news", "Bulawayo news today", "Bulawayo news latest",
            "latest Bulawayo news", "Bulawayo business news",
            "Bulawayo weather", "Matabeleland news", "Bulawayo Zimbabwe news",
            "news Bulawayo", "Bulawayo today",
        ],
        "matchers": [r"\bbulawayo\b"],
    },
    {
        "slug": "mutare",
        "name": "Mutare",
        "title_short": "Mutare",
        "lat": -18.9707, "lon": 32.6731,
        "headline": "Mutare news, today.",
        "context": (
            "Mutare is the largest city in eastern Zimbabwe, the gateway "
            "to the Eastern Highlands and the headquarters of major "
            "agribusiness and tea-growing operations. The Mutapa Times "
            "tracks Mutare daily — Manicaland politics, border trade with "
            "Mozambique, timber and citrus exports, tourism in Nyanga "
            "and Vumba, and the cultural calendar — aggregating reports "
            "from local Zimbabwean newsrooms and international wires."
        ),
        "keywords_extra": [
            "Mutare news", "Mutare news today", "Mutare news latest",
            "latest Mutare news", "Mutare business news", "Mutare weather",
            "Manicaland news", "Mutare Zimbabwe news",
            "news Mutare", "Mutare today", "Nyanga news", "Vumba news",
        ],
        "matchers": [r"\bmutare\b", r"\bmanicaland\b"],
    },
    {
        "slug": "gweru",
        "name": "Gweru",
        "title_short": "Gweru",
        "lat": -19.4570, "lon": 29.8170,
        "headline": "Gweru news, today.",
        "context": (
            "Gweru is the capital of the Midlands province, a key "
            "industrial, education and military town in central "
            "Zimbabwe. The Mutapa Times covers Gweru daily — Midlands "
            "State University, the ZNA Officers' Academy, ferrochrome "
            "and steel, urban affairs, and the cultural calendar — "
            "pulling from local newsrooms and international wires."
        ),
        "keywords_extra": [
            "Gweru news", "Gweru news today", "Gweru news latest",
            "latest Gweru news", "Gweru business news", "Gweru weather",
            "Midlands news", "Gweru Zimbabwe news",
            "news Gweru", "Gweru today",
        ],
        "matchers": [r"\bgweru\b", r"\bmidlands\b"],
    },
    {
        "slug": "masvingo",
        "name": "Masvingo",
        "title_short": "Masvingo",
        "lat": -20.0744, "lon": 30.8328,
        "headline": "Masvingo news, today.",
        "context": (
            "Masvingo is Zimbabwe's oldest colonial-era town and home "
            "to the Great Zimbabwe National Monument — the medieval "
            "stone city that gave the country its name. The Mutapa Times "
            "tracks Masvingo daily — Great Zimbabwe heritage news, "
            "Lake Mutirikwi, agriculture in the Lowveld, Masvingo "
            "Polytechnic, and the cultural calendar — aggregating "
            "reports from local newsrooms and international wires."
        ),
        "keywords_extra": [
            "Masvingo news", "Masvingo news today", "Masvingo news latest",
            "latest Masvingo news", "Masvingo business news",
            "Masvingo weather", "Great Zimbabwe news", "Lowveld news",
            "Masvingo Zimbabwe news",
            "news Masvingo", "Masvingo today",
        ],
        "matchers": [r"\bmasvingo\b", r"\bgreat zimbabwe\b"],
    },
    {
        "slug": "victoria-falls",
        "name": "Victoria Falls",
        "title_short": "Vic Falls",
        "lat": -17.9244, "lon": 25.8572,
        "headline": "Victoria Falls news, today.",
        "context": (
            "Victoria Falls is Zimbabwe's premier tourist town and "
            "home to the Victoria Falls Stock Exchange (VFEX). The "
            "Mutapa Times covers Vic Falls daily — Mosi-oa-Tunya "
            "conservation, the VFEX, hospitality and safari operators, "
            "Hwange National Park, and the SADC tourism corridor — "
            "aggregating reports from local newsrooms and international wires."
        ),
        "keywords_extra": [
            "Victoria Falls news", "Vic Falls news", "Victoria Falls news today",
            "Victoria Falls news latest", "latest Vic Falls news",
            "Victoria Falls weather", "Mosi-oa-Tunya news",
            "VFEX news", "Hwange news", "tourism news Zimbabwe",
            "news Victoria Falls", "Vic Falls today",
        ],
        "matchers": [r"\bvictoria falls\b", r"\bvic[\s-]?falls\b",
                     r"\bmosi[\s-]?oa[\s-]?tunya\b", r"\bhwange\b", r"\bvfex\b"],
    },
]

_ZA_CITIES = [
    {
        "slug": "johannesburg",
        "name": "Johannesburg",
        "title_short": "Joburg",
        "lat": -26.2041, "lon": 28.0473,
        "headline": "Johannesburg news, today.",
        "context": (
            "Johannesburg is South Africa's largest city and economic "
            "engine, home to the Johannesburg Stock Exchange, the head "
            "offices of most listed banks and mining houses, and the "
            "Constitutional Court. The Mutapa Times tracks Johannesburg "
            "daily — markets, business, City of Joburg affairs, "
            "infrastructure and culture — aggregating reports from South "
            "African newsrooms and international wire services."
        ),
        "keywords_extra": [
            "Johannesburg news", "Johannesburg news today", "Joburg news",
            "latest Johannesburg news", "Johannesburg business news",
            "Johannesburg weather", "Gauteng news", "JSE news",
            "news Johannesburg", "Joburg today",
        ],
        "matchers": [r"\bjohannesburg\b", r"\bjoburg\b", r"\bjo'burg\b", r"\bsandton\b", r"\bsoweto\b"],
    },
    {
        "slug": "cape-town",
        "name": "Cape Town",
        "title_short": "Cape Town",
        "lat": -33.9249, "lon": 18.4241,
        "headline": "Cape Town news, today.",
        "context": (
            "Cape Town is South Africa's legislative capital and the seat "
            "of Parliament, a major tourism, tech and financial-services "
            "hub on the Western Cape. The Mutapa Times covers Cape Town "
            "daily — Parliament, the V&A Waterfront economy, the startup "
            "and energy sectors, City affairs and the cultural calendar — "
            "pulling from South African newsrooms and international wires."
        ),
        "keywords_extra": [
            "Cape Town news", "Cape Town news today", "latest Cape Town news",
            "Cape Town business news", "Cape Town weather", "Western Cape news",
            "Parliament news", "news Cape Town", "Cape Town today",
        ],
        "matchers": [r"\bcape town\b", r"\bwestern cape\b"],
    },
    {
        "slug": "durban",
        "name": "Durban",
        "title_short": "Durban",
        "lat": -29.8587, "lon": 31.0218,
        "headline": "Durban news, today.",
        "context": (
            "Durban is South Africa's busiest port city and the commercial "
            "heart of KwaZulu-Natal. The Mutapa Times tracks Durban daily — "
            "the port and logistics economy, manufacturing, eThekwini "
            "affairs, tourism along the Golden Mile, and the cultural "
            "calendar — aggregating South African newsrooms and "
            "international wires."
        ),
        "keywords_extra": [
            "Durban news", "Durban news today", "latest Durban news",
            "Durban business news", "Durban weather", "KwaZulu-Natal news",
            "eThekwini news", "news Durban", "Durban today",
        ],
        "matchers": [r"\bdurban\b", r"\bethekwini\b", r"\bkwazulu", r"\bkzn\b"],
    },
    {
        "slug": "pretoria",
        "name": "Pretoria",
        "title_short": "Pretoria",
        "lat": -25.7479, "lon": 28.2293,
        "headline": "Pretoria news, today.",
        "context": (
            "Pretoria is South Africa's administrative capital, seat of "
            "the executive and the diplomatic corps in the City of "
            "Tshwane. The Mutapa Times covers Pretoria daily — national "
            "government and policy, the Union Buildings, the Reserve Bank, "
            "universities and the cultural calendar — pulling from South "
            "African newsrooms and international wires."
        ),
        "keywords_extra": [
            "Pretoria news", "Pretoria news today", "latest Pretoria news",
            "Pretoria business news", "Pretoria weather", "Tshwane news",
            "government news South Africa", "news Pretoria", "Pretoria today",
        ],
        "matchers": [r"\bpretoria\b", r"\btshwane\b"],
    },
    {
        "slug": "gqeberha",
        "name": "Gqeberha",
        "title_short": "Gqeberha",
        "lat": -33.9608, "lon": 25.6022,
        "headline": "Gqeberha news, today.",
        "context": (
            "Gqeberha, formerly Port Elizabeth, is the industrial and "
            "automotive hub of the Eastern Cape and a key deep-water port. "
            "The Mutapa Times tracks Gqeberha daily — the motor industry, "
            "Nelson Mandela Bay affairs, the port economy, tourism along "
            "the coast, and the cultural calendar — aggregating South "
            "African newsrooms and international wires."
        ),
        "keywords_extra": [
            "Gqeberha news", "Port Elizabeth news", "Gqeberha news today",
            "latest Gqeberha news", "Gqeberha business news",
            "Gqeberha weather", "Eastern Cape news", "Nelson Mandela Bay news",
            "news Gqeberha", "Gqeberha today",
        ],
        "matchers": [r"\bgqeberha\b", r"port elizabeth", r"nelson mandela bay"],
    },
]


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
        "newsletter_form_url": _ZW_NEWSLETTER_FORM,
        "brevo_list_id": 2,        # Brevo contact list this edition sends to
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
        "cities": _ZW_CITIES,
        "demonym_plural": "Zimbabweans",
        "city_local_sources": "Bulawayo24, NewZimbabwe.com, The Herald, The Standard, NewsDay, ZimLive, 263Chat",
        "scene_report_html": '<a href="/articles/2026-05-14-second-nature-manyonga-venice-biennale-pavilion-of-zimbabwe.html" class="nav-drawer-scene-report">Scene Report</a>',
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
        "newsletter_form_url": "https://e8bb9c12.sibforms.com/serve/MUIFAG7VVccFkFF2xK48g6M774UnwvBuprOAvKgs289BnjHnSDTVGcO_BcZZau9wwBHBaNCwxfMfaOexCI0hHwRCP6jZhokdH9rVTZ2lbN_YbPP5UFl3zBlXAA6flC_ywqPKgAo__IPOpxxeQtTTw1ZyF_PbV7D6zhsOz-7PAVxDrcOknsZgkXsryDojw3ssFGhXB1ITtMj5_KYVng==",
        "brevo_list_id": 6,        # South Africa Brevo contact list

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
            "south africa", "south african", "johannesburg", "joburg", "cape town", "durban",
            "pretoria", "tshwane", "gqeberha", "port elizabeth", "bloemfontein",
            "soweto", "ekurhuleni", "polokwane", "nelspruit", "kimberley",
            "ramaphosa", "anc", "da ", "eff", "sarb", "jse", "rand", "zar",
            "sars", "eskom", "load shedding", "godongwana", "kganyago",
            "western cape", "gauteng", "kwazulu", "limpopo", "mpumalanga",
            "free state", "north west", "northern cape", "eastern cape",
            # Sport (so legitimate SA sport headlines pass the title check)
            "springbok", "springboks", "boks", "proteas", "bafana", "banyana",
            "kaizer chiefs", "orlando pirates", "mamelodi sundowns", "psl",
            "comrades marathon",
            # Institutions / figures
            "saps", "sassa", "transnet", "prasa", "nersa", "telkom",
            "malema", "steenhuisen", "zuma", "mkhwanazi", "mbeki",
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
        # Client-side homepage feed split (consumed by js/region.js, which is
        # GENERATED from this file by scripts/build_region_js.py). "spotlight"
        # is omitted because it equals spotlight_rss above; the generator reuses
        # that. These are browser query sets, distinct from all_rss_feeds.
        "browser_feeds": {
            "main": [
                "https://news.google.com/rss/search?q=South+Africa&hl=en&gl=ZA&ceid=ZA:en",
                "https://news.google.com/rss/search?q=South+Africa+news+today&hl=en&gl=ZA&ceid=ZA:en",
                "https://news.google.com/rss/search?q=Johannesburg+OR+Cape+Town+OR+Durban&hl=en&gl=ZA&ceid=ZA:en",
                "https://news.google.com/rss/search?q=South+Africa+politics+government+economy&hl=en&gl=ZA&ceid=ZA:en",
                "https://news.google.com/rss/search?q=South+Africa+health+education+sport&hl=en&gl=ZA&ceid=ZA:en",
                "https://news.google.com/rss/search?q=South+Africa+mining+business+tourism&hl=en&gl=ZA&ceid=ZA:en",
                "https://news.google.com/rss/search?q=site:news24.com+OR+site:timeslive.co.za+OR+site:iol.co.za+OR+site:sowetanlive.co.za+OR+site:citizen.co.za&hl=en&gl=ZA&ceid=ZA:en",
                "https://news.google.com/rss/search?q=site:dailymaverick.co.za+OR+site:businesslive.co.za+OR+site:moneyweb.co.za+OR+site:mg.co.za&hl=en&gl=ZA&ceid=ZA:en",
            ],
            "sidebar": [
                "https://news.google.com/rss/search?q=South+Africa+local+news&hl=en&gl=ZA&ceid=ZA:en",
                "https://news.google.com/rss/search?q=South+Africa+business+sports+entertainment+health&hl=en&gl=ZA&ceid=ZA:en",
                "https://news.google.com/rss/search?q=Johannesburg+Cape+Town+Durban+Pretoria+Gqeberha+Bloemfontein&hl=en&gl=ZA&ceid=ZA:en",
                "https://news.google.com/rss/search?q=Gauteng+OR+Western+Cape+OR+KwaZulu-Natal+OR+Limpopo&hl=en&gl=ZA&ceid=ZA:en",
                "https://news.google.com/rss/search?q=South+Africa+culture+music+festival+education&hl=en&gl=ZA&ceid=ZA:en",
            ],
        },
        # Local newsrooms for the browser "Local" filter (curated subset of
        # `sources`; drops aggregators like "the conversation" and our own brand).
        "browser_local": [
            "news24", "daily maverick", "businessday", "business day", "times live",
            "timeslive", "moneyweb", "iol", "sowetan", "the citizen",
            "mail & guardian", "ewn", "eyewitness news", "fin24", "businesstech",
        ],
        "cities": _ZA_CITIES,
        "demonym_plural": "South Africans",
        "city_local_sources": "News24, Daily Maverick, BusinessDay, TimesLIVE, Moneyweb, IOL, EWN",
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


def region_newsletter_form(code):
    """Brevo signup form URL for a region (defaults to Zimbabwe's form/list).
    A per-region form routes that edition's sign-ups into its own list."""
    return get_region(code).get("newsletter_form_url") or _ZW_NEWSLETTER_FORM


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
