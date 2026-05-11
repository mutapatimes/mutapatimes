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

BASE_URL = "https://www.mutapatimes.com"
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
        link = f"{BASE_URL}/articles/{slug}.html"
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
                    f"{news_make_slug({'title': title, 'url': source_url, 'publishedAt': a.get('publishedAt') or ''})}.html"
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
            # media:content + enclosure — Metricool's Autolist picks up
            # whichever it understands. Both are commonly supported.
            image = (
                f'      <media:content url="{escape(item["image"])}" medium="image"/>\n'
                f'      <enclosure url="{escape(item["image"])}" type="image/jpeg" length="0"/>\n'
            )
        # Append @mentions to the title so the Metricool Autolist tweet
        # template — ${title}\n\n${link}\n\n#Zimbabwe — naturally includes
        # them. Source publisher mention (e.g. @Reuters) + up to 2 entity
        # mentions (e.g. @CyrilRamaphosa @ZANUPF_Official). Capped so we
        # leave room for the URL (23 chars) and #Zimbabwe inside X's 280.
        title_text = item["title"]
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
            f"      <description>{escape(item.get('description', ''))}</description>\n"
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
        f"      <url>{BASE_URL}/img/logo.png</url>\n"
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
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y-%m-%d")
    pretty_date = now.strftime("%-d %b %Y") if hasattr(now, "strftime") else date_str
    link = f"{BASE_URL}/fx.html?d={date_str}"
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

    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y-%m-%d")
    pretty_date = now.strftime("%-d %b") if hasattr(now, "strftime") else date_str

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
    link = f"{BASE_URL}/weather.html?d={date_str}"
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

    now_utc = datetime.now(timezone.utc)
    cat = now_utc.astimezone(timezone(timedelta(hours=2)))
    date_str = cat.strftime("%Y-%m-%d")
    link = f"{BASE_URL}/economy.html?d={date_str}"
    image = f"{BASE_URL}/img/cards/economy-snapshot.png?v={date_str}"

    return {
        "title": chapter["rss_title"],
        "link": link,
        "description": chapter["rss_desc"],
        "pubDate": now_utc,
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


if __name__ == "__main__":
    main()
