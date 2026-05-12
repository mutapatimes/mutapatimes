#!/usr/bin/env python3
"""Generate RSS 2.0 feed (feed.xml) for The Mutapa Times.

Every item links to a page on mutapatimes.com (a /news/{slug}.html landing
page for spotlight/category articles, or /articles/{slug}.html for CMS-
authored articles). This is what Metricool's Autolist will repost, so each
item MUST drive traffic to us rather than to the source publisher.

Items older than MAX_ITEM_AGE_DAYS are filtered out so a stale Google News
resurface can't auto-publish through Autolists.
"""
import glob
import json
import os
import re
import sys
from datetime import datetime, timezone, timedelta
from email.utils import format_datetime
from xml.sax.saxutils import escape

# Reuse the canonical slug + landing-page URL logic from build_news_pages
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_news_pages import make_slug as news_make_slug  # noqa: E402
from twitter_mentions import all_mentions  # noqa: E402
from build_feed_cards import card_public_url as feed_card_url  # noqa: E402

BASE_URL = "https://mutapatimes.com"
FEED_URL = f"{BASE_URL}/feed.xml"
# Bumped from 50 → 500 so a high-cadence Metricool Autolist on Twitter
# (~20/day) has enough fresh inventory to never starve before the next
# fetch-news run refills the feed.
MAX_ITEMS = 500
MAX_ITEM_AGE_DAYS = 30  # Autolists shouldn't ever republish stale wires


def _parse_date(s):
    """Try to parse ISO 8601 or RFC 2822 into a tz-aware datetime.
    Handles fractional seconds ('2026-05-10T17:46:27.000Z') used by CMS
    timestamps — the previous strptime patterns silently dropped these,
    so every CMS article fell out of the feed."""
    if not s:
        return None
    s = s.strip()
    # ISO 8601 via fromisoformat — accepts most variants once we normalise
    # the trailing Z to a UTC offset.
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        pass
    # Fallbacks: strptime patterns for date-only or simple ISO forms
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(s, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    # RFC 2822 (e.g., "Wed, 23 Jan 2019 08:00:00 GMT") used by Google News RSS
    try:
        from email.utils import parsedate_to_datetime
        return parsedate_to_datetime(s)
    except (TypeError, ValueError):
        return None


def _is_fresh(dt):
    if dt is None:
        return False
    try:
        return (datetime.now(timezone.utc) - dt).days <= MAX_ITEM_AGE_DAYS
    except (TypeError, ValueError):
        return False


def _normalize_source(src):
    if isinstance(src, dict):
        return (src.get("name") or "").strip()
    return str(src or "").strip()


def collect_cms_articles(base):
    """Read CMS markdown articles and return list of dicts. Links point to
    /articles/{slug}.html on mutapatimes.com."""
    items = []
    articles_dir = os.path.join(base, "content", "articles")
    for md in glob.glob(os.path.join(articles_dir, "*.md")):
        slug = os.path.splitext(os.path.basename(md))[0]
        if slug == "index":
            continue
        with open(md, "r", encoding="utf-8") as f:
            text = f.read()
        m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)", text, re.DOTALL)
        if not m:
            continue
        fm, body = m.group(1), m.group(2)
        # Use [^\S\n] (space/tab but NOT newline) so an empty 'image: ' line
        # doesn't greedily swallow the newline and steal the next field's
        # value. Same defensive change for the other fields.
        title = re.search(r'^title:[^\S\n]*["\']?(.+?)["\']?[^\S\n]*$', fm, re.MULTILINE)
        date = re.search(r"^date:[^\S\n]*['\"]?(\S+)", fm, re.MULTILINE)
        summary = re.search(r'^summary:[^\S\n]*["\']?(.+?)["\']?[^\S\n]*$', fm, re.MULTILINE)
        category = re.search(r'^category:[^\S\n]*["\']?(.+?)["\']?[^\S\n]*$', fm, re.MULTILINE)
        author = re.search(r'^author:[^\S\n]*["\']?(.+?)["\']?[^\S\n]*$', fm, re.MULTILINE)
        image = re.search(r'^image:[^\S\n]*["\']?(.+?)["\']?[^\S\n]*$', fm, re.MULTILINE)
        dt = _parse_date(date.group(1)) if date else None
        if not _is_fresh(dt):
            continue
        link = f"{BASE_URL}/articles/{slug}"
        items.append({
            "title": title.group(1) if title else slug,
            "link": link,
            "description": (summary.group(1) if summary else body[:240].strip()),
            "pubDate": dt,
            "category": category.group(1) if category else "News",
            "author": author.group(1) if author else None,
            # Every feed item now points to the on-brand headline card we
            # render in build_feed_cards.py — Metricool autolists pick this
            # up as the post image, replacing scraped source thumbnails.
            "image": feed_card_url(link),
        })
    return items


def collect_news_landing_articles(base):
    """Read data/spotlight.json + data/{category}.json and emit one feed item
    per article, linking to the mutapatimes.com /news/{slug}.html landing
    page (NOT the source publisher's URL). Old articles are dropped."""
    items = []
    data_dir = os.path.join(base, "data")
    # Same set of feeds that build_news_pages reads + spotlight
    candidates = ["spotlight.json"] + [
        f"{cat}.json"
        for cat in ("business", "technology", "entertainment", "sports", "science", "health")
    ]
    seen_source_urls = set()
    for fname in candidates:
        path = os.path.join(data_dir, fname)
        if not os.path.exists(path):
            continue
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue
        if not isinstance(data, dict):
            continue
        for key in ("articles", "more"):
            for a in data.get(key) or []:
                if not isinstance(a, dict):
                    continue
                source_url = (a.get("url") or "").strip()
                title = (a.get("title") or "").strip()
                if not source_url or not title:
                    continue
                if source_url in seen_source_urls:
                    continue
                seen_source_urls.add(source_url)
                dt = _parse_date(a.get("publishedAt") or a.get("published_at") or "")
                if not _is_fresh(dt):
                    continue
                source_name = _normalize_source(a.get("source"))
                # Build the canonical mutapatimes.com landing URL — matches
                # what build_news_pages.py renders for the same article.
                landing = (
                    f"{BASE_URL}/news/"
                    f"{news_make_slug({'title': title, 'url': source_url, 'publishedAt': a.get('publishedAt') or ''})}"
                )
                desc = (a.get("description") or "").strip()
                # Add inline attribution so Autolist posts credit the source
                # while still linking to us. (Metricool's Autolist template
                # variables — ${title}, ${description}, ${link} — pull from
                # these three.)
                if source_name and source_name.lower() not in desc.lower():
                    desc = f"{desc} (via {source_name})" if desc else f"{title} — via {source_name}"
                items.append({
                    "title": title,
                    "link": landing,
                    "description": desc,
                    "pubDate": dt,
                    "category": fname.replace(".json", "").title() if fname != "spotlight.json" else "News",
                    "author": source_name or None,
                    # On-brand card image — same renderer as build_metricool_csv
                    # produces, keyed by the landing URL hash so the same
                    # article always gets the same card.
                    "image": feed_card_url(landing),
                })
    return items


def _swap_apostrophes(s):
    """Metricool's autolist preview HTML-escapes ASCII apostrophes to
    &#39; — visible as literal '&#39;' in tweet/post previews. Swap them
    for U+2019 (typographically-correct right single quotation mark)
    which Metricool leaves alone. Applies to titles + descriptions only."""
    if not s:
        return s
    return s.replace("'", "’")


_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")


_HASHTAG_TOPIC_MAP = {
    "Business": ["#Business", "#ZimbabweEconomy"],
    "Economy":  ["#Economy", "#ZimbabweEconomy"],
    "Policy":   ["#Policy", "#ZimbabwePolicy"],
    "Tech":     ["#Tech", "#AfricaTech"],
    "Health":   ["#Health", "#ZimbabweHealth"],
    "Sport":    ["#Sport", "#ZimbabweSport"],
    "Culture":  ["#Culture", "#ZimbabweCulture"],
    "Environment": ["#Climate", "#Environment"],
    "Education": ["#Education", "#ZimbabweEducation"],
    "Jobs":     ["#Jobs", "#ZimbabweJobs", "#Hiring"],
    "Property": ["#Property", "#ZimbabweProperty", "#RealEstate"],
    "FX":       ["#FX", "#ZimbabweFX", "#SendMoneyToZimbabwe"],
    "Weather":  ["#Weather", "#ZimbabweWeather"],
}

def _hashtags_for(category, title=""):
    """Produce a small editorial-grade hashtag set per item: always
    #Zimbabwe, a category tag, plus a couple of topic-specific tags.
    Used by Metricool's RSS autolist via the description field."""
    tags = ["#Zimbabwe"]
    cat = (category or "").strip()
    extras = _HASHTAG_TOPIC_MAP.get(cat, [])
    for t in extras:
        if t not in tags:
            tags.append(t)
    if "#ZimbabweNews" not in tags:
        tags.append("#ZimbabweNews")
    # De-dupe, cap at 5
    return " ".join(tags[:5])


def _strip_emails(s):
    """Source descriptions sometimes embed reporter contact addresses
    ('By X. Y. xy@herald.co.zw') — they look spammy when the feed is
    re-posted to social. Drop them and collapse the surrounding whitespace."""
    if not s:
        return s
    s = _EMAIL_RE.sub("", s)
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\s+([,.;:])", r"\1", s)
    return s.strip()


def build_rss(items):
    """Build RSS 2.0 XML string."""
    now = format_datetime(datetime.now(timezone.utc))
    items.sort(
        key=lambda x: x.get("pubDate") or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )
    items = items[:MAX_ITEMS]

    entries = []
    for item in items:
        pub = format_datetime(item["pubDate"]) if item.get("pubDate") else now
        cat = (
            f"      <category>{escape(item.get('category', 'News'))}</category>\n"
            if item.get("category") else ""
        )
        author = (
            f"      <dc:creator>{escape(item.get('author') or 'The Mutapa Times')}</dc:creator>\n"
            if item.get("author") else ""
        )
        image = ""
        if item.get("image"):
            img_url = item["image"]
            # Pick the correct MIME — Metricool (and many RSS scrapers)
            # skip enclosures whose declared type doesn't match the actual
            # file. Our cards are PNG; some legacy thumbnails are JPG.
            lower = img_url.lower()
            if lower.endswith(".png"):
                mime = "image/png"
            elif lower.endswith(".webp"):
                mime = "image/webp"
            elif lower.endswith(".gif"):
                mime = "image/gif"
            else:
                mime = "image/jpeg"
            # media:content + media:thumbnail + enclosure. Different
            # scrapers use different tags; emitting all three maximises the
            # chance the autolist preview gets an image.
            image = (
                f'      <media:content url="{escape(img_url)}" medium="image" type="{mime}"/>\n'
                f'      <media:thumbnail url="{escape(img_url)}"/>\n'
                f'      <enclosure url="{escape(img_url)}" type="{mime}" length="200000"/>\n'
            )
        # Append @mentions to the title so the Metricool Autolist tweet
        # template — ${title}\n\n${link}\n\n#Zimbabwe — naturally includes
        # them. Source publisher mention (e.g. @Reuters) + up to 2 entity
        # mentions (e.g. @CyrilRamaphosa @ZANUPF_Official). Capped so we
        # leave room for the URL (23 chars) and #Zimbabwe inside X's 280.
        title_text = _swap_apostrophes(item["title"])
        mentions = all_mentions(
            title_text, item.get("description", ""), item.get("author") or "",
        )
        if mentions:
            budget = 280 - 23 - len("\n\n") - len("\n\n#Zimbabwe") - len(title_text) - 1
            joined = []
            for m in mentions:
                cost = len(m) + 1  # leading space
                if cost > budget:
                    break
                joined.append(m)
                budget -= cost
            if joined:
                title_text = f"{title_text} {' '.join(joined)}"
        entries.append(
            "    <item>\n"
            f"      <title>{escape(title_text)}</title>\n"
            f"      <link>{escape(item['link'])}</link>\n"
            f"      <description>{escape(_swap_apostrophes(_strip_emails(item.get('description', ''))) + ' ' + _hashtags_for(item.get('category', ''), item.get('title', '')))}</description>\n"
            f"      <pubDate>{pub}</pubDate>\n"
            f'      <guid isPermaLink="true">{escape(item["link"])}</guid>\n'
            f"{cat}{author}{image}"
            "    </item>"
        )

    body = "\n".join(entries) + ("\n" if entries else "")
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0"\n'
        '     xmlns:atom="http://www.w3.org/2005/Atom"\n'
        '     xmlns:dc="http://purl.org/dc/elements/1.1/"\n'
        '     xmlns:media="http://search.yahoo.com/mrss/">\n'
        "  <channel>\n"
        "    <title>The Mutapa Times</title>\n"
        f"    <link>{BASE_URL}</link>\n"
        "    <description>Business and intelligence newspaper delivering curated Zimbabwean news from foreign press for the diaspora.</description>\n"
        "    <language>en</language>\n"
        f"    <lastBuildDate>{now}</lastBuildDate>\n"
        f'    <atom:link href="{FEED_URL}" rel="self" type="application/rss+xml"/>\n'
        "    <image>\n"
        "      <title>The Mutapa Times</title>\n"
        f"      <url>{BASE_URL}/img/brand/mark-512.png</url>\n"
        f"      <link>{BASE_URL}</link>\n"
        "    </image>\n"
        "    <copyright>Copyright 2020-2026 The Mutapa Times</copyright>\n"
        "    <managingEditor>news@mutapatimes.com (The Mutapa Times)</managingEditor>\n"
        "    <webMaster>news@mutapatimes.com (The Mutapa Times)</webMaster>\n"
        f"{body}"
        "  </channel>\n"
        "</rss>\n"
    )


def _norm_title(s):
    """Lowercase + collapse non-alphanumerics so 'Foo!' and 'Foo' match."""
    return re.sub(r"[^a-z0-9]+", "", (s or "").lower())


def _cat_day_start_utc():
    """Return today's 00:00 CAT (UTC+2) expressed as a UTC datetime.
    Daily-rotating feeds (FX, weather, economy, jobs) anchor their
    pubDate here so the feed is bit-identical across the multiple
    cron runs that happen within a single CAT day. Without this,
    every cron run emits a fresh pubDate and Metricool's autolist
    re-imports the same item as 'new', producing duplicates."""
    cat = datetime.now(timezone(timedelta(hours=2)))
    cat_midnight = cat.replace(hour=0, minute=0, second=0, microsecond=0)
    return cat_midnight.astimezone(timezone.utc)


def build_fx_snapshot_item(base):
    """Build one RSS item for today's FX snapshot card, if the data file
    exists. The link is date-tagged so Metricool's autolist (which dedupes
    by URL) treats each day as a new post — without that, the snapshot
    would post once and never again."""
    fx_path = os.path.join(base, "data", "fx-rates.json")
    prov_path = os.path.join(base, "data", "remittance-providers.json")
    if not os.path.exists(fx_path):
        return None
    try:
        fx = json.load(open(fx_path))
    except (json.JSONDecodeError, OSError):
        return None
    rates = fx.get("rates") or {}
    zwg = rates.get("ZWG")
    if zwg is None:
        return None

    # Compute the best-from-UK provider as the headline hook for the
    # tweet/post body (matches the card visual).
    best_uk_name = None
    best_uk_amount = None
    if os.path.exists(prov_path):
        try:
            providers = json.load(open(prov_path))
            uk_route = (providers.get("routes") or {}).get("GBP") or {}
            mid_usd_per_gbp = 1 / rates["GBP"] if rates.get("GBP") else None
            if mid_usd_per_gbp:
                best = None
                for p in uk_route.get("providers", []):
                    net = max(0, 100 - p.get("fee", 0))
                    recv = net * mid_usd_per_gbp * (1 - p.get("fx_margin_pct", 0) / 100)
                    if best is None or recv > best[1]:
                        best = (p["name"], recv)
                if best:
                    best_uk_name, best_uk_amount = best
        except (json.JSONDecodeError, OSError, KeyError):
            pass

    # Date-tagged URL → unique per day so autolist re-posts daily.
    # pubDate anchored to start-of-CAT-day so reruns within the day are
    # bit-identical (avoids Metricool re-importing the same post).
    now = _cat_day_start_utc()
    cat_today = datetime.now(timezone(timedelta(hours=2)))
    date_str = cat_today.strftime("%Y-%m-%d")
    pretty_date = cat_today.strftime("%-d %b %Y")
    link = f"{BASE_URL}/fx?d={date_str}"
    image = f"{BASE_URL}/img/cards/fx-snapshot.png?v={date_str}"

    title_bits = [f"Zim FX snapshot {pretty_date}: 1 USD = {zwg:.2f} ZWG"]
    if best_uk_name and best_uk_amount:
        title_bits.append(f"best from UK £100 → ${best_uk_amount:.2f} via {best_uk_name}")
    title = " · ".join(title_bits)

    # Metricool's preview layer HTML-escapes apostrophes to &#39; in the
    # post body, so avoid them entirely. Use straight phrasing instead of
    # contractions and "today's".
    desc_lines = [
        f"Official interbank rate today — 1 USD = {zwg:.4f} ZWG.",
    ]
    if best_uk_name and best_uk_amount:
        desc_lines.append(
            f"Sending £100 from the UK: {best_uk_name} lands ${best_uk_amount:.2f}, best of "
            f"{len((providers.get('routes') or {}).get('GBP', {}).get('providers', []))} providers."
        )
    desc_lines.append("Compare every country at mutapatimes.com/fx")

    return {
        "title": title,
        "link": link,
        "description": " ".join(desc_lines),
        "pubDate": now,
        "category": "FX",
        "author": "The Mutapa Times",
        "image": image,
    }


def build_weather_snapshot_item(base):
    """Build today's weather item for the dedicated /weather-feed.xml.
    Same date-tagged-URL trick as the FX snapshot so the autolist
    treats every CAT-day as a new post."""
    weather_path = os.path.join(base, "data", "weather.json")
    if not os.path.exists(weather_path):
        return None
    try:
        weather = json.load(open(weather_path))
    except (json.JSONDecodeError, OSError):
        return None
    cities = weather.get("cities") or []
    if not cities:
        return None

    # Headline city for the title hook (Harare if present, else first).
    headline_city = next((c for c in cities if c.get("city") == "Harare"), cities[0])

    # Today's tsumo (mirrors the card + newsletter rotation).
    try:
        sys.path.insert(0, os.path.join(base, "scripts"))
        from send_newsletter import SHONA_PROVERBS as _PROVERBS  # noqa: E402
        import time as _time
        day_index = int(_time.time() // 86400) % len(_PROVERBS)
        tsumo = _PROVERBS[day_index]
    except Exception:
        tsumo = None

    # pubDate anchored to start-of-CAT-day so reruns within the day are
    # bit-identical and Metricool does not re-import the same post.
    now = _cat_day_start_utc()
    cat_today = datetime.now(timezone(timedelta(hours=2)))
    date_str = cat_today.strftime("%Y-%m-%d")
    pretty_date = cat_today.strftime("%-d %b")

    title = (
        f"Zim weather {pretty_date}: {headline_city['city']} "
        f"{headline_city.get('label', '').lower() or 'today'} · high "
        f"{round(headline_city['high'])}° / low {round(headline_city['low'])}°"
    )

    # Description: short city summaries + today's tsumo at the end.
    city_lines = []
    for c in cities:
        if c.get("high") is None or c.get("low") is None:
            continue
        city_lines.append(
            f"{c['city']}: high {round(c['high'])}°, low {round(c['low'])}° "
            f"({c.get('label', '').lower()})"
        )
    desc = " · ".join(city_lines)
    if tsumo:
        desc += f"  Tsumo yezuva: {tsumo['shona']} ({tsumo['english']})"

    # Date-tagged weather.html so Metricool's URL dedupe treats each day
    # as a new post, AND so the landing page Metricool scrapes for OG
    # metadata serves the weather card (not fx.html's FX card).
    link = f"{BASE_URL}/weather?d={date_str}"
    image = f"{BASE_URL}/img/cards/weather-snapshot.png?v={date_str}"

    return {
        "title": title,
        "link": link,
        "description": desc,
        "pubDate": now,
        "category": "Weather",
        "author": "The Mutapa Times",
        "image": image,
    }


def write_weather_feed(base):
    """Write /weather-feed.xml as a single-item feed for a dedicated
    Metricool autolist (own template, own daily cadence)."""
    item = build_weather_snapshot_item(base)
    if not item:
        print("  weather-feed.xml SKIPPED — data/weather.json missing or empty")
        return False

    rss = build_rss([item])
    rss = rss.replace(
        "<title>The Mutapa Times</title>",
        "<title>The Mutapa Times — Daily Zimbabwe Weather + Tsumo</title>",
        1,
    ).replace(
        f'<atom:link href="{FEED_URL}"',
        f'<atom:link href="{BASE_URL}/weather-feed.xml"',
        1,
    ).replace(
        "<description>Business and intelligence newspaper delivering curated Zimbabwean news from foreign press for the diaspora.</description>",
        "<description>Daily weather forecast for Zimbabwe's main cities plus the Tsumo yezuva (proverb of the day). One item per day, dedicated for the Mutapa Times weather autolist.</description>",
        1,
    )

    out = os.path.join(base, "weather-feed.xml")
    with open(out, "w", encoding="utf-8") as f:
        f.write(rss)
    print(f"  weather-feed.xml written ({item['title'][:80]}…)")
    return True


def write_fx_feed(base):
    """Write a dedicated fx-feed.xml containing only today's FX snapshot
    item. Lets the user configure a SEPARATE Metricool autolist for FX
    with its own template + cadence, without mixing into the high-volume
    news feed."""
    fx_item = build_fx_snapshot_item(base)
    if not fx_item:
        print("  fx-feed.xml SKIPPED — data/fx-rates.json missing or empty")
        return False

    # Re-use build_rss with a single-item list; channel-level metadata
    # carries through. The autolist will see a 1-item feed where the URL
    # changes once per CAT day, so it posts exactly once a day.
    rss = build_rss([fx_item])
    # Patch the channel title + atom:self for the dedicated feed.
    rss = rss.replace(
        "<title>The Mutapa Times</title>",
        "<title>The Mutapa Times — Daily Zimbabwe FX Snapshot</title>",
        1,
    ).replace(
        f'<atom:link href="{FEED_URL}"',
        f'<atom:link href="{BASE_URL}/fx-feed.xml"',
        1,
    ).replace(
        "<description>Business and intelligence newspaper delivering curated Zimbabwean news from foreign press for the diaspora.</description>",
        "<description>Daily Zimbabwe FX snapshot — official USD/ZWG rate plus the best money-transfer provider for each diaspora country. One item per day, dedicated for the Mutapa Times FX autolist.</description>",
        1,
    )

    out = os.path.join(base, "fx-feed.xml")
    with open(out, "w", encoding="utf-8") as f:
        f.write(rss)
    print(f"  fx-feed.xml written ({fx_item['title'][:80]}…)")
    return True


# ─────────────────────────────────────────────────────────────
# Economy feed — daily rotating one-stat card. The day-of-year
# rotation is computed in lockstep with build_economy_card.py via
# scripts/economy_chapters.py — a 31-chapter rotation that ensures
# no fact repeats within any 30-day window.
# ─────────────────────────────────────────────────────────────
def build_economy_snapshot_item(base):
    """Build today's one-item entry for /economy-feed.xml. Date-tagged URL
    so Metricool's URL dedupe treats every CAT day as a fresh post."""
    # Import lazily — economy_chapters reads from data/ which may not
    # exist on a fresh checkout before fetch_news has run.
    try:
        sys.path.insert(0, os.path.join(base, "scripts"))
        from economy_chapters import pick_chapter_for_today
    except ImportError as e:
        print(f"  economy-feed.xml SKIPPED — chapter module import failed: {e}")
        return None

    gdp_path = os.path.join(base, "data", "gdp-zimbabwe-quarterly.json")
    bop_path = os.path.join(base, "data", "zimstat-bop-quarterly.json")
    if not (os.path.exists(gdp_path) and os.path.exists(bop_path)):
        return None

    try:
        idx, day_name, chapter = pick_chapter_for_today()
    except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
        print(f"  economy-feed.xml SKIPPED — chapter build failed: {e}")
        return None

    if not chapter.get("rss_title") or not chapter.get("rss_desc"):
        return None

    # pubDate anchored to start-of-CAT-day so reruns within the day are
    # bit-identical and Metricool does not re-import the same post.
    pub = _cat_day_start_utc()
    cat = datetime.now(timezone(timedelta(hours=2)))
    date_str = cat.strftime("%Y-%m-%d")
    link = f"{BASE_URL}/economy?d={date_str}"
    image = f"{BASE_URL}/img/cards/economy-snapshot.png?v={date_str}"

    return {
        "title": chapter["rss_title"],
        "link": link,
        "description": chapter["rss_desc"],
        "pubDate": pub,
        "category": "Economy",
        "author": "The Mutapa Times",
        "image": image,
    }


def write_economy_feed(base):
    """Write /economy-feed.xml as a single-item daily feed for the
    dedicated Mutapa Times economy autolist."""
    item = build_economy_snapshot_item(base)
    if not item:
        print("  economy-feed.xml SKIPPED — GDP or BoP data missing")
        return False

    rss = build_rss([item])
    rss = rss.replace(
        "<title>The Mutapa Times</title>",
        "<title>The Mutapa Times — Daily Zimbabwe Economy</title>",
        1,
    ).replace(
        f'<atom:link href="{FEED_URL}"',
        f'<atom:link href="{BASE_URL}/economy-feed.xml"',
        1,
    ).replace(
        "<description>Business and intelligence newspaper delivering curated Zimbabwean news from foreign press for the diaspora.</description>",
        "<description>Daily Zimbabwe economy briefing — one analytical infographic per day rotating through GDP, trade, remittances, mining, services, and the unrecorded balance. All data from ZimStat and the Reserve Bank of Zimbabwe.</description>",
        1,
    )

    out = os.path.join(base, "economy-feed.xml")
    with open(out, "w", encoding="utf-8") as f:
        f.write(rss)
    print(f"  economy-feed.xml written ({item['title'][:80]}…)")
    return True


# ─────────────────────────────────────────────────────────────
# Business + economics feed — strictly Zimbabwe business, finance,
# investment, mining and trade news. Pulls from data/business.json
# and CMS articles tagged Business. Each item ships with the brand
# headline card so the Metricool autolist posts on-brand previews.
#
# Politics, election coverage, celebrity gossip and similar are kept
# OUT — even when they slip into the upstream "Business" tag — via a
# small deny-list of title keywords.
# ─────────────────────────────────────────────────────────────
BUSINESS_LANDING_FILES = ("business.json",)
BUSINESS_CMS_CATEGORIES = {"business"}

# Upstream CMS sources tag a lot of crime + politics as "Business",
# so the category alone is not a reliable filter. We require a positive
# business/economics keyword match AND no negative-signal match.
BUSINESS_POSITIVE_KEYWORDS = (
    # mining & commodities
    "mining", "mine ", "miner", "mineral", "lithium", "gold", "platinum",
    "diamond", "tobacco", "cotton", "iron ore", "chrome", "nickel", "coal",
    # macro / currency
    "inflation", "currency", "exchange rate", "zwg", "zig", "usd ",
    "rbz", "reserve bank", "central bank", "monetary policy",
    # markets
    "stock", "shares", "zse", "vfex", "ipo", "listing", "delisting",
    "share price",
    # capital
    "investment", "investor", "funding", "capital", "raise", "private equity",
    "venture capital", "fundraise",
    # corporate
    "company", " firm ", "corporation", "earnings", "profit", "loss-making",
    "revenue", "results", "dividend", "pvt ltd", "(private)",
    # macro
    "economy", "economic", "gdp", "growth rate", "recession",
    "budget", "fiscal", "tax", "treasury", "deficit", "surplus",
    # trade
    "exports", "imports", "trade ", "tariff", "balance of payments",
    # banking / debt
    "loan", "credit", "mortgage", "bond ", "debt restructur",
    "creditor", "default",
    # institutions
    "imf", "world bank", "afdb", "afreximbank", "boz", "sadc trade",
    # energy / utility prices
    "gas price", "fuel price", "electricity tariff", "petrol price",
    "energy sector",
    # industrial
    "factory", "plant", "manufactur", "industrial", "production line",
    # deals
    "acquisition", "merger", "partnership", "joint venture",
    "memorandum of understanding",
    # workforce
    "entrepreneur", "startup", "sme ",
    # agriculture (business angle)
    "harvest", "tobacco auction", "agricultur",
    # property / construction
    "real estate", "construction", "infrastructure",
    # commerce
    "retail", "wholesale", "supplier", "distributor",
    # remittances
    "remittance",
)

NEGATIVE_SIGNALS = (
    # crime
    "stab", "stabb", "murder", "killed", "killing",
    "fatal", " dead", "death", "deaths", "deadly",
    "arrest of", "jailed", "imprison", "prison",
    "sentence", "sentenced", "rape", "raped", "paedophile",
    "brawl", "assault", "robbery", "burglary", "kidnap",
    # disasters
    "collapse leaves",
    # politics
    "coup", " election", "ballot",
    "regime", "dictator", "opposition party", "ruling party",
    # personal
    "wedding", "divorce", "celebrity", "scandal",
    "elite detachment", "first lady", "mnangagwa family",
    # geopolitics noise
    "iran", "putin", "biden", "trump", " gaza ", "ceasefire",
    "war crime", "global conflicts", "joint commission",
    "diplomatic relations", "security scare",
    # local govt / civic minutiae
    "burial", "cemetery", "funeral",
    # filler / opinion
    "kid president",
)


def _looks_business(title, description=""):
    """Return True if the title/description has at least one positive
    business signal AND no negative signal. Used as a defensive filter
    on top of the upstream category tag."""
    blob = f"{title or ''}  {description or ''}".lower()
    if any(neg in blob for neg in NEGATIVE_SIGNALS):
        return False
    return any(pos in blob for pos in BUSINESS_POSITIVE_KEYWORDS)


def collect_business_landing_articles(base):
    """Same shape as collect_news_landing_articles but limited to
    the business + policy categories."""
    items = []
    data_dir = os.path.join(base, "data")
    seen_source_urls = set()
    for fname in BUSINESS_LANDING_FILES:
        path = os.path.join(data_dir, fname)
        if not os.path.exists(path):
            continue
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue
        if not isinstance(data, dict):
            continue
        cat_label = fname.replace(".json", "").title()
        for key in ("articles", "more"):
            for a in data.get(key) or []:
                if not isinstance(a, dict):
                    continue
                source_url = (a.get("url") or "").strip()
                title = (a.get("title") or "").strip()
                if not source_url or not title:
                    continue
                if source_url in seen_source_urls:
                    continue
                seen_source_urls.add(source_url)
                dt = _parse_date(a.get("publishedAt") or a.get("published_at") or "")
                if not _is_fresh(dt):
                    continue
                desc = (a.get("description") or "").strip()
                if not _looks_business(title, desc):
                    continue
                source_name = _normalize_source(a.get("source"))
                landing = (
                    f"{BASE_URL}/news/"
                    f"{news_make_slug({'title': title, 'url': source_url, 'publishedAt': a.get('publishedAt') or ''})}"
                )
                if source_name and source_name.lower() not in desc.lower():
                    desc = f"{desc} (via {source_name})" if desc else f"{title} — via {source_name}"
                items.append({
                    "title": title,
                    "link": landing,
                    "description": desc,
                    "pubDate": dt,
                    "category": cat_label,
                    "author": source_name or None,
                    "image": feed_card_url(landing),
                })
    return items


def collect_business_cms_articles(base):
    """CMS articles whose frontmatter category is Business. A deny-list
    of political/celebrity title keywords filters mistagged upstream
    content (which is common in Zimbabwe news sources)."""
    out = []
    for item in collect_cms_articles(base):
        cat = (item.get("category") or "").strip().lower()
        if cat not in BUSINESS_CMS_CATEGORIES:
            continue
        if not _looks_business(item.get("title", ""), item.get("description", "")):
            continue
        out.append(item)
    return out


def write_business_feed(base):
    """Write /business-feed.xml — a strictly Zimbabwe business and
    economic-policy feed for a dedicated Metricool autolist. Every
    item links to a mutapatimes.com landing page; every item carries
    the brand headline card as enclosure + media:content, so social
    previews are on-brand regardless of source."""
    cms_items = collect_business_cms_articles(base)
    landing_items = collect_business_landing_articles(base)
    # CMS first so its richer body wins on title-collision dedupe.
    raw = cms_items + landing_items
    seen_links = set()
    seen_titles = set()
    unique = []
    for item in raw:
        link = item["link"]
        t_norm = _norm_title(item.get("title", ""))
        if link in seen_links or (t_norm and t_norm in seen_titles):
            continue
        seen_links.add(link)
        if t_norm:
            seen_titles.add(t_norm)
        unique.append(item)

    if not unique:
        print("  business-feed.xml SKIPPED — no eligible business/policy items")
        return False

    rss = build_rss(unique)
    rss = rss.replace(
        "<title>The Mutapa Times</title>",
        "<title>The Mutapa Times — Zimbabwe Business &amp; Economic Policy</title>",
        1,
    ).replace(
        f'<atom:link href="{FEED_URL}"',
        f'<atom:link href="{BASE_URL}/business-feed.xml"',
        1,
    ).replace(
        "<description>Business and intelligence newspaper delivering curated Zimbabwean news from foreign press for the diaspora.</description>",
        "<description>Strictly Zimbabwe business, finance, mining, investment and economic-policy stories — curated from foreign press and policy press. Each item ships with a branded headline card for social autolists.</description>",
        1,
    )

    out = os.path.join(base, "business-feed.xml")
    with open(out, "w", encoding="utf-8") as f:
        f.write(rss)
    print(f"  business-feed.xml written ({len(unique)} items)")
    return True


# ─────────────────────────────────────────────────────────────
# Jobs feed — Zimbabwe vacancies + Mutapa Times internships, one
# RSS item per active listing. Cards rendered by build_job_cards.py.
# ─────────────────────────────────────────────────────────────
def collect_job_items(base):
    """Build feed items from data/jobs.json. Includes the three
    first-party Mutapa Times internships at the top of the inventory
    so they always get airtime on the autolist."""
    items = []

    # Mutapa Times internships — first-party, always on
    internships = [
        ("Social Intern",
         "Help grow our social channels. Pitch fresh formats and ideas. "
         "Fully remote, 3 days/week, 3 months. Rolling intake.",
         "My social handles / portfolio links:"),
        ("Editor Intern",
         "Pitch, draft and edit original explainers. Bring fresh editorial "
         "angles. Fully remote, 3 days/week, 3 months. Rolling intake.",
         "Three writing samples (links or attached):"),
        ("Data Intern",
         "Turn Zimbabwe public data into clear visual stories. Bring new "
         "data ideas. Fully remote, 3 days/week, 3 months. Rolling intake.",
         "A repo, notebook or dataset I am proud of:"),
    ]
    pub = _cat_day_start_utc()
    for role, summary, _samples in internships:
        slug_role = role.lower().replace(" ", "-")
        landing = f"{BASE_URL}/jobs#{slug_role}"
        items.append({
            "title": f"{role} — The Mutapa Times (Remote · 3 days/week · 3 months)",
            "link": landing,
            "description": summary,
            "pubDate": pub,
            "category": "Internship",
            "author": "The Mutapa Times",
            "image": f"{BASE_URL}/img/cards/jobs/internship-{slug_role}.png",
        })

    # Live aggregated vacancies
    jobs_path = os.path.join(base, "data", "jobs.json")
    if os.path.exists(jobs_path):
        try:
            data = json.load(open(jobs_path))
        except (json.JSONDecodeError, OSError):
            data = None
        if data:
            for j in (data.get("jobs") or []):
                url = (j.get("url") or "").strip()
                title = (j.get("title") or "").strip()
                if not url or not title:
                    continue
                # Per-job card URL — same MD5-hash scheme as build_job_cards.py
                url_hash = re.sub(r"[^0-9a-f]", "", _md5_hex(url))[:12]
                card_url = f"{BASE_URL}/img/cards/jobs/{url_hash}.png"
                meta_bits = []
                for k in ("location", "type", "salary"):
                    v = (j.get(k) or "").strip()
                    if v:
                        meta_bits.append(v)
                desc = (j.get("summary") or "").strip()
                if meta_bits:
                    desc = (desc + "  " if desc else "") + " · ".join(meta_bits)
                if j.get("source"):
                    desc = f"{desc}  (via {j['source']})"
                items.append({
                    "title": (j.get("company") + " — " + title) if j.get("company") else title,
                    "link": url,
                    "description": desc,
                    "pubDate": pub,   # Anchored: feed stable within a CAT day
                    "category": "Jobs",
                    "author": j.get("company") or j.get("source") or None,
                    "image": card_url,
                })
    return items


def _md5_hex(s):
    import hashlib as _h
    return _h.md5((s or "").encode("utf-8")).hexdigest()


def write_jobs_feed(base):
    """Write /jobs-feed.xml — Zimbabwe vacancies + Mutapa Times
    internships, each with a branded card image."""
    items = collect_job_items(base)
    if not items:
        print("  jobs-feed.xml SKIPPED — no jobs available")
        return False

    rss = build_rss(items)
    rss = rss.replace(
        "<title>The Mutapa Times</title>",
        "<title>The Mutapa Times — Zimbabwe Jobs &amp; Internships</title>",
        1,
    ).replace(
        f'<atom:link href="{FEED_URL}"',
        f'<atom:link href="{BASE_URL}/jobs-feed.xml"',
        1,
    ).replace(
        "<description>Business and intelligence newspaper delivering curated Zimbabwean news from foreign press for the diaspora.</description>",
        "<description>Live Zimbabwe vacancies plus the three rolling Mutapa Times internships (Social, Editor, Data). Each item ships with a branded card image for the social autolist.</description>",
        1,
    )

    out = os.path.join(base, "jobs-feed.xml")
    with open(out, "w", encoding="utf-8") as f:
        f.write(rss)
    print(f"  jobs-feed.xml written ({len(items)} items)")
    return True


# ─────────────────────────────────────────────────────────────
# Properties feed — Zimbabwe property listings with hybrid
# photo+brand-strip cards. Continuous RSS so each new listing flows
# through the autolist (IG feed + IG story + Twitter) automatically.
# ─────────────────────────────────────────────────────────────
def collect_property_items(base):
    """One feed item per active listing in data/property-listings.json.
    Each item carries its branded hybrid card image (photo + price + specs)."""
    items = []
    p = os.path.join(base, "data", "property-listings.json")
    if not os.path.exists(p):
        return items
    try:
        data = json.load(open(p))
    except (json.JSONDecodeError, OSError):
        return items

    # Stable per-day pubDate so cron reruns are bit-identical
    pub = _cat_day_start_utc()

    for L in (data.get("listings") or []):
        url = (L.get("url") or "").strip()
        title = (L.get("title") or "").strip()
        if not url or not title:
            continue

        # Per-listing card URL — same MD5-hash scheme as build_property_cards.py
        url_hash = _md5_hex(url)[:12]
        card_url = f"{BASE_URL}/img/cards/properties/{url_hash}.png"

        price = (L.get("price") or "Price on request").strip()
        location = (L.get("location") or "Zimbabwe").strip()
        beds = L.get("beds")
        baths = L.get("baths")
        meta_bits = []
        if beds:
            meta_bits.append(f"{beds} bed" + ("s" if str(beds) != "1" else ""))
        if baths:
            meta_bits.append(f"{baths} bath" + ("s" if str(baths) != "1" else ""))
        meta = ", ".join(meta_bits)
        desc_parts = [f"{price} — {location}"]
        if meta:
            desc_parts.append(meta)
        desc_parts.append(title)
        desc_parts.append("Browse all listings at mutapatimes.com/property")
        description = ". ".join(desc_parts)

        items.append({
            "title": f"{price} — {title} ({location})",
            "link": url,
            "description": description,
            "pubDate": pub,
            "category": "Property",
            "author": (L.get("source") or "Property.co.zw"),
            "image": card_url,
        })
    return items


def write_properties_feed(base):
    """Write /properties-feed.xml — Zimbabwe property listings, each
    with a hybrid photo+brand-strip card. Designed for a Metricool
    autolist that posts to IG feed, IG story, and Twitter."""
    items = collect_property_items(base)
    if not items:
        print("  properties-feed.xml SKIPPED — no listings available")
        return False

    rss = build_rss(items)
    rss = rss.replace(
        "<title>The Mutapa Times</title>",
        "<title>The Mutapa Times — Zimbabwe Property Listings</title>",
        1,
    ).replace(
        f'<atom:link href="{FEED_URL}"',
        f'<atom:link href="{BASE_URL}/properties-feed.xml"',
        1,
    ).replace(
        "<description>Business and intelligence newspaper delivering curated Zimbabwean news from foreign press for the diaspora.</description>",
        "<description>Live Zimbabwe property listings with branded hybrid cards — photo on top, price and specs on the brand strip. One item per active listing for the Mutapa Times properties autolist.</description>",
        1,
    )

    out = os.path.join(base, "properties-feed.xml")
    with open(out, "w", encoding="utf-8") as f:
        f.write(rss)
    print(f"  properties-feed.xml written ({len(items)} items)")
    return True


# ─────────────────────────────────────────────────────────────
# Stories feed — mixed business + property + jobs, each item shipping
# a 1080×1920 Instagram-Story-format card with a "Read more on Mutapa
# Times" CTA. Designed for a Metricool autolist that posts to IG/FB
# Stories specifically. Packed — up to 60 items, interleaved by date.
# ─────────────────────────────────────────────────────────────
STORY_CARDS_DIR = "img/cards/stories"


def _story_card_url(canonical_url):
    """Match build_story_cards.card_public_url — md5(url)[:12] + .png."""
    h = re.sub(r"[^0-9a-f]", "", _md5_hex(canonical_url))[:12]
    return f"{BASE_URL}/img/cards/stories/{h}.png"


def _story_landing_url(destination):
    """Each feed item links to /stories/{md5}.html — a dedicated
    landing page whose og:image is the 9:16 story card. Metricool's
    autolist preview scrapes og:image from the link target, so this
    indirection is what makes the card actually appear in the preview."""
    h = re.sub(r"[^0-9a-f]", "", _md5_hex(destination))[:12]
    return f"{BASE_URL}/stories/{h}.html"


def collect_stories_items(base):
    """Mix business CMS articles + jobs + property listings into one
    packed feed. Each item carries the 9:16 story-card image as
    enclosure + media:content/thumbnail AND links to a Metricool-
    optimised landing page where the card is the og:image."""
    items = []
    pub_now = _cat_day_start_utc()

    # 1) Business / Policy / Tech / Economy / Environment CMS articles
    idx_path = os.path.join(base, "content", "articles", "index.json")
    if os.path.exists(idx_path):
        try:
            entries = json.load(open(idx_path))
        except (json.JSONDecodeError, OSError):
            entries = []
        keep = {"Business", "Policy", "Tech", "Economy", "Environment"}
        for e in entries:
            if not isinstance(e, dict):
                continue
            slug = e.get("slug")
            cat = (e.get("category") or "").strip()
            title = (e.get("title") or "").strip()
            if not slug or not title or cat not in keep:
                continue
            destination = f"{BASE_URL}/articles/{slug}"
            desc = (e.get("summary") or "").strip()
            author = (e.get("author") or "").strip()
            if author and author.lower() not in desc.lower():
                desc = (desc + " " if desc else "") + f"via {author}"
            dt = _parse_date(e.get("date", "")) if "_parse_date" in globals() else None
            items.append({
                "title": title,
                "link": _story_landing_url(destination),
                "description": desc,
                "pubDate": dt or pub_now,
                "category": cat,
                "author": author or None,
                "image": _story_card_url(destination),
            })

    # 2) External jobs + internships — point feed link at our landing,
    #    keep the destination URL as the card's hash key.
    jobs_items = collect_job_items(base)
    for j in jobs_items:
        destination = j["link"]
        j2 = dict(j)
        j2["link"] = _story_landing_url(destination)
        j2["image"] = _story_card_url(destination)
        j2["category"] = "Jobs"
        items.append(j2)

    # 3) Property listings — same pattern
    prop_items = collect_property_items(base)
    for p in prop_items:
        destination = p["link"]
        p2 = dict(p)
        p2["link"] = _story_landing_url(destination)
        p2["image"] = _story_card_url(destination)
        p2["category"] = "Property"
        items.append(p2)

    # Sort newest first, cap to 60 (packed but not unbounded)
    items.sort(key=lambda x: x.get("pubDate") or pub_now, reverse=True)
    return items[:60]


def write_stories_feed(base):
    """Write /stories-feed.xml — the mixed business + property + jobs
    Instagram-Story autolist feed. Each item carries a 9:16 story
    card with a 'Read more on Mutapa Times' CTA baked in."""
    items = collect_stories_items(base)
    if not items:
        print("  stories-feed.xml SKIPPED — no items available")
        return False

    rss = build_rss(items)
    rss = rss.replace(
        "<title>The Mutapa Times</title>",
        "<title>The Mutapa Times — Zimbabwe Stories</title>",
        1,
    ).replace(
        f'<atom:link href="{FEED_URL}"',
        f'<atom:link href="{BASE_URL}/stories-feed.xml"',
        1,
    ).replace(
        "<description>Business and intelligence newspaper delivering curated Zimbabwean news from foreign press for the diaspora.</description>",
        "<description>Packed Instagram-Story autolist — business, property, jobs and internships in one feed. Each item ships with a 1080×1920 story card and a 'Read more on Mutapa Times' CTA.</description>",
        1,
    )

    out = os.path.join(base, "stories-feed.xml")
    with open(out, "w", encoding="utf-8") as f:
        f.write(rss)
    print(f"  stories-feed.xml written ({len(items)} items, mixed business + property + jobs)")
    return True


# ─────────────────────────────────────────────────────────────
# Link-in-bio grid — data/bio-grid.json drives /links.html, the
# Linktree-style page we put in the Instagram bio. Pulls the latest
# items from every feed source so a visitor can find the card image
# they saw on the Instagram grid and tap through to read it.
# ─────────────────────────────────────────────────────────────
def _bio_tile(item, kind):
    """Reduce a full feed item to the minimal payload the bio grid
    page needs — image, link, title, category. Drop pubDate as
    Python datetime so the JSON is serialisable."""
    pub = item.get("pubDate")
    pub_iso = pub.isoformat() if pub else None
    return {
        "kind": kind,                        # news, economy, fx, weather, jobs, property
        "title": item.get("title", ""),
        "link": item.get("link", ""),
        "image": item.get("image", ""),
        "pubDate": pub_iso,
        "category": item.get("category", ""),
    }


def write_bio_grid(base):
    """Write data/bio-grid.json — a unified, sorted feed for the
    link-in-bio landing page (/links.html)."""
    tiles = []

    # 1. Daily dedicated cards (FX, weather, economy) — pin these up top
    for builder, kind in (
        (build_economy_snapshot_item, "economy"),
        (build_fx_snapshot_item, "fx"),
        (build_weather_snapshot_item, "weather"),
    ):
        try:
            it = builder(base)
        except Exception:
            it = None
        if it:
            tiles.append(_bio_tile(it, kind))

    # 2. News (CMS + news landing) — the bulk of the IG grid
    seen = set()
    for it in collect_cms_articles(base) + collect_news_landing_articles(base):
        link = it.get("link") or ""
        if not link or link in seen:
            continue
        seen.add(link)
        tiles.append(_bio_tile(it, "news"))

    # 3. Jobs + Properties — surface the latest of each so visitors
    # can tap from a job/property card on IG to the source
    for it in collect_job_items(base):
        link = it.get("link") or ""
        if link in seen:
            continue
        seen.add(link)
        tiles.append(_bio_tile(it, "jobs"))

    for it in collect_property_items(base):
        link = it.get("link") or ""
        if link in seen:
            continue
        seen.add(link)
        tiles.append(_bio_tile(it, "property"))

    # Newest first; daily snapshots already at the top because their
    # pubDate is anchored to today's CAT midnight.
    tiles.sort(
        key=lambda t: t.get("pubDate") or "",
        reverse=True,
    )

    # Cap at 60 so the bio page loads quickly. The IG grid only
    # shows ~12-30 recent posts anyway; 60 is plenty of depth.
    tiles = tiles[:60]

    payload = {
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "count": len(tiles),
        "tiles": tiles,
    }
    out = os.path.join(base, "data", "bio-grid.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    print(f"  data/bio-grid.json written ({len(tiles)} tiles)")
    return True


def main():
    base = os.path.join(os.path.dirname(__file__), "..")
    # CMS first so its /articles/{slug}.html link wins over the /news/{slug}.html
    # landing variant when the same story appears in both (the CMS page has
    # the full body text — better for SEO and reader experience).
    items = collect_cms_articles(base) + collect_news_landing_articles(base)
    seen_links = set()
    seen_titles = set()
    unique = []
    for item in items:
        link = item["link"]
        t_norm = _norm_title(item.get("title", ""))
        if link in seen_links or (t_norm and t_norm in seen_titles):
            continue
        seen_links.add(link)
        if t_norm:
            seen_titles.add(t_norm)
        unique.append(item)

    rss = build_rss(unique)
    out = os.path.join(base, "feed.xml")
    with open(out, "w", encoding="utf-8") as f:
        f.write(rss)
    print(f"feed.xml written with {min(len(unique), MAX_ITEMS)} items "
          f"(linking to mutapatimes.com; <={MAX_ITEM_AGE_DAYS}d old)")

    # Separate single-item feeds for the dedicated autolists
    write_fx_feed(base)
    write_weather_feed(base)
    write_economy_feed(base)
    write_business_feed(base)
    write_jobs_feed(base)
    write_properties_feed(base)
    write_stories_feed(base)
    write_bio_grid(base)


if __name__ == "__main__":
    main()
