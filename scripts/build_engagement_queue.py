#!/usr/bin/env python3
"""
Build a daily engagement plan that focuses 10 minutes of manual work on
the highest-ROI actions for a 0-followers brand account: replying to
high-traffic Zim Twitter accounts, quote-tweeting with our angle, and
following adjacent influencers.

Reads the curated handle list from data/influencer-list.json and pulls
recent tweets via Nitter RSS (no paid X API). Falls back gracefully if
all Nitter mirrors are down. Outputs data/engagement-plan.md committed
to the repo so the user opens it from their phone each morning.

NEVER auto-posts. All replies are SUGGESTIONS the user copy/pastes
manually from the brand account.
"""
import datetime as dt
import html as html_mod
import json
import os
import random
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

DATA_DIR = "data"
INFLUENCER_FILE = os.path.join(DATA_DIR, "influencer-list.json")
SPOTLIGHT_FILE = os.path.join(DATA_DIR, "spotlight.json")
OUTPUT_FILE = os.path.join(DATA_DIR, "engagement-plan.md")

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.0-flash:generateContent"
)

# Nitter mirrors — public RSS endpoints. Try in order; many go up/down.
NITTER_MIRRORS = [
    "https://nitter.net",
    "https://nitter.privacydev.net",
    "https://nitter.poast.org",
    "https://nitter.mint.lgbt",
    "https://nitter.cz",
]
USER_AGENT = (
    "Mozilla/5.0 (compatible; MutapaTimesEngagementBot/1.0; "
    "+https://www.mutapatimes.com)"
)

# Reuse the news-page slug helper so quote-tweet links point to a real
# /news/{slug}.html landing page on mutapatimes.com.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_news_pages import landing_url as mutapa_landing_url  # noqa: E402


# ── Nitter RSS fetching ───────────────────────────────────────
def fetch_recent_tweets(handle, max_age_hours=24, max_count=8):
    """Return list of {url, text, ts} for a handle's last 24h of tweets.
    Tries each Nitter mirror in turn; returns [] if all fail."""
    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=max_age_hours)
    for mirror in NITTER_MIRRORS:
        url = f"{mirror}/{handle}/rss"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=15) as resp:
                xml_text = resp.read().decode("utf-8", errors="replace")
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError):
            continue
        except Exception:
            continue
        # Parse RSS
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError:
            continue
        items = root.findall(".//item")
        out = []
        for it in items[:max_count]:
            link = (it.findtext("link") or "").strip()
            title = (it.findtext("title") or "").strip()
            pub = (it.findtext("pubDate") or "").strip()
            try:
                ts = dt.datetime.strptime(pub, "%a, %d %b %Y %H:%M:%S %Z")
                ts = ts.replace(tzinfo=dt.timezone.utc)
            except ValueError:
                ts = dt.datetime.now(dt.timezone.utc)
            if ts < cutoff:
                continue
            # Convert nitter URL back to twitter.com URL for the user to click
            tw_link = re.sub(r"https?://[^/]+/", "https://twitter.com/", link)
            tw_link = re.sub(r"#m$", "", tw_link)
            out.append({"url": tw_link, "text": html_mod.unescape(title), "ts": ts})
        if out:
            return out
    return []


# ── Gemini-drafted reply prompts ──────────────────────────────
def gemini_reply_draft(tweet_text, handle, name):
    """Ask Gemini for a one-sentence reply that adds value (not flattery)."""
    if not GEMINI_API_KEY:
        return ""
    prompt = (
        "You are advising on a one-sentence reply to a tweet, posted from "
        f"@mutapatimes (Zimbabwe news brand) to @{handle} ({name}).\n\n"
        f"TWEET: {tweet_text}\n\n"
        "Write a reply that ADDS VALUE — a specific data point, a "
        "respectful counter-angle, an additional fact from Zimbabwe, or a "
        "thoughtful question. AVOID empty agreement ('great post', 'so true'). "
        "MAX 240 characters. No emojis. No hashtags. Output the reply text "
        "ONLY, no commentary."
    )
    body = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 200},
    }
    try:
        req = urllib.request.Request(
            f"{GEMINI_URL}?key={GEMINI_API_KEY}",
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.load(resp)
        candidates = data.get("candidates", [])
        if not candidates:
            return ""
        parts = candidates[0].get("content", {}).get("parts", [])
        return (parts[0].get("text", "") if parts else "").strip()
    except Exception:
        return ""


# ── Article-quote-tweet pairing ───────────────────────────────
def pick_quote_tweet_pairs(handle_tweets, articles, count=2):
    """Pair a Tier-1/2 tweet with the most relevant Mutapa article.
    Simple word-overlap scoring — good enough at our scale.
    Returns list of (tweet, article) pairs."""
    pairs = []
    used_tweets = set()
    used_articles = set()
    for tweet in handle_tweets:
        if tweet["url"] in used_tweets:
            continue
        tweet_words = set(re.findall(r"[a-z]+", tweet["text"].lower()))
        best, best_score = None, 0
        for art in articles:
            if art["url"] in used_articles:
                continue
            art_words = set(re.findall(r"[a-z]+", (art["title"] + " " + art.get("description","")).lower()))
            score = len(tweet_words & art_words)
            if score > best_score:
                best, best_score = art, score
        if best and best_score >= 3:
            pairs.append((tweet, best))
            used_tweets.add(tweet["url"])
            used_articles.add(best["url"])
            if len(pairs) >= count:
                break
    return pairs


# ── Loaders ───────────────────────────────────────────────────
def load_influencers():
    with open(INFLUENCER_FILE) as f:
        return json.load(f)


def load_articles():
    if not os.path.exists(SPOTLIGHT_FILE):
        return []
    try:
        d = json.load(open(SPOTLIGHT_FILE))
    except (json.JSONDecodeError, IOError):
        return []
    out = []
    for a in (d.get("articles") or []) + (d.get("more") or []):
        title = (a.get("title") or "").strip()
        url = (a.get("url") or "").strip()
        if not title or not url:
            continue
        src = a.get("source")
        if isinstance(src, dict):
            src = src.get("name", "")
        out.append({
            "title": title,
            "url": url,
            "description": (a.get("description") or "").strip(),
            "source": str(src or "").strip(),
            "publishedAt": a.get("publishedAt") or "",
        })
    return out


# ── Plan rendering ────────────────────────────────────────────
def render_plan(replies, quote_pairs, follow_targets, like_targets,
                community_prompt, generated_at):
    lines = []
    lines.append(f"# Daily Engagement Plan — {generated_at.strftime('%A, %d %b %Y')}\n")
    lines.append(
        "10 min. Brand account (@mutapatimes). Open this on your phone, "
        "execute, close the tab. Don't write your own — these are calibrated.\n"
    )
    lines.append("---\n")

    lines.append("## 1. Reply to these tweets (3 × ~90 sec each)\n")
    if replies:
        for i, item in enumerate(replies, 1):
            lines.append(f"### {i}. @{item['handle']} ({item['name']})\n")
            lines.append(f"**Their tweet:** {item['tweet_text']}\n")
            lines.append(f"**Open:** {item['tweet_url']}\n")
            if item["draft"]:
                lines.append(f"**Suggested reply:**\n> {item['draft']}\n")
            else:
                lines.append(
                    "**Suggested reply:** (Gemini draft unavailable — write a "
                    "one-sentence value-add: a stat, a counter-angle, or a "
                    "specific question. No empty agreement.)\n"
                )
            lines.append("")
    else:
        lines.append(
            "_No fresh tweets pulled today (Nitter mirrors may be down). "
            "Open the brand account, scroll the home feed, reply to the top "
            "3 tweets you have a real take on._\n"
        )

    lines.append("---\n")
    lines.append("## 2. Quote-tweet with our angle (2 × ~90 sec each)\n")
    if quote_pairs:
        for i, (tweet, article) in enumerate(quote_pairs, 1):
            lines.append(f"### {i}. Re: @{tweet['handle']} on \"{tweet['text'][:80]}...\"\n")
            lines.append(f"**Their tweet:** {tweet['tweet_url']}\n")
            lines.append(f"**Quote-tweet text suggestion:**")
            lines.append(
                f"> Adding context from our coverage: {article['title']}.\n"
                f"> {article['mutapa_url']}\n"
            )
    else:
        lines.append(
            "_No strong tweet↔article match today. Skip — focus the time "
            "on replies above._\n"
        )

    lines.append("---\n")
    lines.append("## 3. Follow + like (2 min)\n")
    if follow_targets:
        for t in follow_targets:
            lines.append(f"- **Follow** [@{t['handle']}]({t['url']}) — {t['name']} ({t['topic']})")
    if like_targets:
        for t in like_targets:
            lines.append(f"- **Like** this tweet from @{t['handle']}: {t['url']}")
    lines.append("")

    lines.append("---\n")
    lines.append("## 4. Community engagement (~1 min)\n")
    lines.append(f"_{community_prompt}_\n")

    lines.append("---\n")
    lines.append("## After you're done\n")
    lines.append(
        "Spend 30 seconds checking @mutapatimes notifications. Reply to "
        "anyone who engaged with our posts in the last 24h — that's how "
        "the first 100 followers actually arrive.\n"
    )
    lines.append(f"\n_Generated {generated_at.isoformat()} by build_engagement_queue.py_\n")
    return "\n".join(lines)


def main():
    print("=== BUILD ENGAGEMENT QUEUE ===")
    if not os.path.exists(INFLUENCER_FILE):
        print(f"  ERROR: {INFLUENCER_FILE} missing")
        sys.exit(1)

    influencers = load_influencers()
    articles = load_articles()
    print(f"  Loaded {len(articles)} recent articles for quote-tweet pairing")

    # Pull recent tweets from Tier 1 + Tier 2 handles
    rng = random.Random(int(dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d")))
    tier1 = list(influencers.get("tier1", []))
    tier2 = list(influencers.get("tier2", []))
    tier3 = list(influencers.get("tier3", []))
    rng.shuffle(tier1)
    rng.shuffle(tier2)
    rng.shuffle(tier3)

    # Reply-prompt candidates: 3 from Tier 1 (rotate daily)
    reply_handles = tier1[:3]
    print(f"  Reply targets: {[h['handle'] for h in reply_handles]}")

    replies = []
    handle_tweets_cache = {}  # for quote-tweet pairing later

    for h in reply_handles:
        tweets = fetch_recent_tweets(h["handle"])
        handle_tweets_cache[h["handle"]] = [
            {**t, "handle": h["handle"], "name": h["name"]} for t in tweets
        ]
        if not tweets:
            print(f"    @{h['handle']}: 0 tweets fetched")
            continue
        # Pick the freshest tweet
        t = tweets[0]
        draft = gemini_reply_draft(t["text"], h["handle"], h["name"])
        replies.append({
            "handle": h["handle"],
            "name": h["name"],
            "tweet_url": t["url"],
            "tweet_text": t["text"][:240],
            "draft": draft,
        })
        print(f"    @{h['handle']}: drafted reply ({len(draft)} chars)")

    # Quote-tweet pairing: pull tweets from Tier 2 (4 handles), pair with articles
    quote_candidates = []
    for h in tier2[:4]:
        tweets = fetch_recent_tweets(h["handle"])
        for t in tweets:
            quote_candidates.append({
                **t,
                "handle": h["handle"],
                "name": h["name"],
                "tweet_url": t["url"],
            })
    # Articles need their mutapa landing URL for quote-tweet links
    for a in articles:
        a["mutapa_url"] = mutapa_landing_url(a)
    quote_pairs = pick_quote_tweet_pairs(quote_candidates, articles, count=2)
    print(f"  Quote-tweet pairs found: {len(quote_pairs)}")

    # Follow targets: 1 fresh Tier 2 + 1 Tier 3 each day, rotated
    follow_targets = []
    for h in (tier2[4:5] + tier3[:1]):
        follow_targets.append({
            "handle": h["handle"],
            "url": f"https://twitter.com/{h['handle']}",
            "name": h["name"],
            "topic": h["topic"],
        })

    # Like targets: 2 fresh tweets from Tier 1 already in our cache
    like_targets = []
    for tweets in handle_tweets_cache.values():
        if len(like_targets) >= 2:
            break
        for t in tweets[:2]:
            if len(like_targets) < 2:
                like_targets.append({"handle": t["handle"], "url": t["url"]})

    # Community prompt — rotates daily by weekday
    community_prompts = [
        "Search 'Zimbabwe' on X. Find one tweet from a non-public account "
        "with thoughtful commentary in the last hour. Reply with one helpful "
        "fact. (Builds the brand on threads not just from influencers.)",
        "Open the X 'For You' search for 'Harare' OR 'Bulawayo'. Reply to "
        "the most-engaged tweet there with a related Mutapa headline link.",
        "Post a 1-tweet hot take from @mutapatimes on the day's top story "
        "from spotlight.json. Include a question to drive replies.",
        "Find one Zimbabwean Threads or X user with under 1k followers and "
        "engaging takes. Follow + reply to 2 of their recent posts.",
        "Quote-tweet the top story from the Mutapa landing page with a "
        "20-word summary plus #Zimbabwe.",
        "Find one Zim journalist Twitter list, scroll it, follow 3 new "
        "accounts you don't follow yet. (Sets up future reply targets.)",
        "Skim r/Zimbabwe for a high-engagement thread. Cross-post the link "
        "to @mutapatimes Threads with our take.",
    ]
    weekday = dt.datetime.now(dt.timezone.utc).weekday()
    community_prompt = community_prompts[weekday % 7]

    output = render_plan(
        replies=replies,
        quote_pairs=quote_pairs,
        follow_targets=follow_targets,
        like_targets=like_targets,
        community_prompt=community_prompt,
        generated_at=dt.datetime.now(dt.timezone.utc),
    )

    os.makedirs(DATA_DIR, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(output)
    print(f"  Wrote {OUTPUT_FILE}")
    print("\n=== DONE ===")


if __name__ == "__main__":
    main()
