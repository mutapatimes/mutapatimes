#!/usr/bin/env python3
"""
Send The Mutapa Times newsletter via Brevo API (Mon/Wed/Sat).
Reads data/*.json category files plus games/shona-wordle/words.json, builds
an HTML email with a Today's Shona Wordle promo + category headlines, creates
a campaign, and sends it. Stdlib only, no pip dependencies.
"""
import json
import os
import sys
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime, timezone

# ── Configuration ───────────────────────────────────────────
BREVO_API_KEY = os.environ.get("BREVO_API_KEY", "")
BREVO_BASE = "https://api.brevo.com/v3"
BREVO_LIST_ID = int(os.environ.get("BREVO_LIST_ID", "2"))
DATA_DIR = "data"

SENDER_NAME = "The Mutapa Times"
SENDER_EMAIL = "news@mutapatimes.com"
SITE_URL = "https://www.mutapatimes.com"

# Primary categories first — editorial focus for business & intelligence service
PRIMARY_CATEGORIES = ["business", "politics", "policy", "technology"]
SECONDARY_CATEGORIES = ["health", "entertainment", "sports", "science"]
CATEGORIES = PRIMARY_CATEGORIES + SECONDARY_CATEGORIES
MAX_PER_CATEGORY = 2
MAX_TOTAL = 12
MAX_ARTICLE_AGE_DAYS = 14  # Reject articles older than this

# Editor's pick: pin one article as the newsletter lead/headline, overriding
# the automatic top-of-category pick. `until` is an inclusive UTC date — the
# override applies only up to and including that day, then auto-clears so it
# never gets stuck as a stale headline. Set to None when there's no pick.
LEAD_OVERRIDE = {
    "until": "2026-06-08",
    "title": "Exclusive: Air Zimbabwe is going back to London",
    "url": "https://www.mutapatimes.com/articles/2026-06-07-air-zimbabwe-returns-to-london-plus-ultra-acmi.html",
    "description": "From 1 July, an Airbus A330 flies Harare to London under the Air Zimbabwe code for the first time in over a decade. Inside the Plus Ultra wet-lease that quietly reopens the route, the legal route around the UK ban, and what it is worth.",
    "source": "The Mutapa Times",
    "publishedAt": "2026-06-07T07:00:00.000Z",
    "_category": "business",
}

DAY_GREETINGS = {
    0: "Monday morning",
    2: "Wednesday midweek",
    5: "Saturday weekend",
}


# ── Shona proverbs (same list as config.js, same daily rotation) ──
SHONA_PROVERBS = [
    {"shona": "Chara chimwe hachitswanyi inda.", "english": "One finger cannot crush a louse."},
    {"shona": "Kudzidza hakuperi.", "english": "Learning never ends."},
    {"shona": "Rume rimwe harikombi churu.", "english": "One man cannot surround an anthill."},
    {"shona": "Chirere chigokurerawo.", "english": "Raise a child and it will raise you too."},
    {"shona": "Rina manyanga hariputirwi.", "english": "That which has horns cannot be wrapped."},
    {"shona": "Chisi hachieri chisingabudi rimwe.", "english": "A day of rest doesn\u2019t end without another dawning."},
    {"shona": "Mugoni wepwere ndeasinayo.", "english": "The one who knows how to raise children is one who has none."},
    {"shona": "Kufa kwendega kufa kusingachemerwe.", "english": "To die alone is to die without being mourned."},
    {"shona": "Mwana asingachemi anofira mumbereko.", "english": "A child who does not cry dies on its mother\u2019s back."},
    {"shona": "Kugarira nhaka kuona bvute.", "english": "To inherit is to see the dust settle."},
    {"shona": "Gudo guru peta muswe vadiki vakutye.", "english": "Great baboon, curl your tail so the little ones may fear you."},
    {"shona": "Kuziva mbuya huudzwa.", "english": "To know grandmother is to be told about her."},
    {"shona": "Chakafukidza dzimba matenga.", "english": "What covers houses is the roof."},
    {"shona": "Zviri muvanhu hazvienzani.", "english": "What is in people is not equal."},
    {"shona": "Murombo munhu.", "english": "A poor person is still a person."},
    {"shona": "Zano pangwa une rako.", "english": "Accept advice, but keep your own counsel."},
    {"shona": "Mvura ngainaye; hapana anodzivisa.", "english": "Let the rain fall; no one can stop it."},
    {"shona": "Nzara haina hama.", "english": "Hunger has no relatives."},
    {"shona": "Chitsva chiri murutsoka.", "english": "What is new is underfoot."},
    {"shona": "Dura rinokanganwa gejo.", "english": "The granary forgets the hoe."},
    {"shona": "Nhamo yeumwe hairambirwi sadza.", "english": "Another\u2019s troubles don\u2019t stop you from eating."},
    {"shona": "Gonzo redziva harityi mvura.", "english": "A rat of the river does not fear water."},
    {"shona": "Harisi zuva rimwe guru rakasakara.", "english": "The great baobab did not grow in a single day."},
    {"shona": "Kure kwegava ndokusina mugariri.", "english": "The distance of the vulture is because no one stays there."},
    {"shona": "Kutsva kwendebvu varume vanodzimurana.", "english": "When a beard catches fire, men help each other put it out."},
    {"shona": "Atsemhira zuva anochembera.", "english": "One who races with the sun grows old."},
    {"shona": "Chinonzi mhosva kana matakadya.", "english": "What is called a crime depends on whether you have eaten."},
    {"shona": "Mbudzi kudya mufenje haina mhosva.", "english": "When a goat eats a baboon\u2019s food, there is no crime."},
    {"shona": "Shiri huru haigarire dendere rimwe.", "english": "A great bird does not sit in one nest."},
    {"shona": "Chinono chinogara chiuru.", "english": "The small and steady accumulates a thousand."},
    # ── Expanded from the curated Tsumo DzeChiShona database ──
    {"shona": "Aive madziva ava mazambuko.", "english": "What used to be hard is now simple."},
    {"shona": "Akuruma nzeve ndewako.", "english": "Those who advise you are on your side."},
    {"shona": "Ane benzi ndeane rake, kudzana unopururudza.", "english": "When you know someone’s flaws you are not surprised when they show."},
    {"shona": "Ateya mariva murutsva haatyi kusviba magaro.", "english": "A person will do whatever it takes to reach their goal."},
    {"shona": "Chaitemura chava kuseva.", "english": "The once great are now impoverished."},
    {"shona": "Chikuriri chine chimwe.", "english": "What is great now will be smaller than another."},
    {"shona": "Chinobhururuka chinomhara.", "english": "What flies eventually lands."},
    {"shona": "Chisingaperi chinoshura.", "english": "All things come to an end."},
    {"shona": "Chiri mumusakasaka chinozvinzwira.", "english": "People take advice that pertains to them, even in a group."},
    {"shona": "Charova sei chando chakwidza hamba mumuti.", "english": "Extreme situations make people behave in unusual ways."},
    {"shona": "Charovedzera charovedzera, gudo rakakwira mawere kwasviba.", "english": "Practice makes even hard things easy."},
    {"shona": "Chembere mukadzi hazvienzani nekurara mugota.", "english": "Poor quality is still better than nothing."},
    {"shona": "Chidamoyo hamba yakada makwati.", "english": "People are free to choose what they want."},
    {"shona": "Chinono chinengwe, bere rakadya richifamba.", "english": "Do what you do with speed."},
    {"shona": "Chinoziva ivhu kuti mwana wembeva anorwara.", "english": "Only those close to a person know their true affairs."},
    {"shona": "Chiri mumoyo chiri muninga.", "english": "What is in the heart is hidden."},
    {"shona": "Chiri pamuchena chiri pamutenure.", "english": "The poor person’s victories do not last."},
    {"shona": "Chitaurirwa hunyimwa mbare dzekumusana.", "english": "Being told is never the same as seeing for yourself."},
    {"shona": "Chenga ose manhanga hapana risina mhodzi.", "english": "There is a reward in trying every option."},
    {"shona": "Guyu kutsvuka kutsvuka zvaro asi mukati rine masvosve.", "english": "Some things look attractive outside but are rotten inside."},
    {"shona": "Igaroziva kuti mhanza yembudzi iri mumabvi.", "english": "Things are not always what they seem."},
    {"shona": "Imbwa nyoro ndidzo tsengi dzamatovo.", "english": "The innocent-looking are often the guilty."},
    {"shona": "Kakara kununa hudya kamwe.", "english": "Success comes through the help of others."},
    {"shona": "Kamoto kamberevere kakapisa matanda mberi.", "english": "Small issues can grow into big problems."},
    {"shona": "Kandiro kanoenda kunobva kamwe.", "english": "Favours return to those who have given them."},
    {"shona": "Kukurukura hunge wapotswa.", "english": "You can only tell the story once you have survived it."},
    {"shona": "Kure kwegava ndiko kusina mutsubvu.", "english": "People go great distances for what they truly want."},
    {"shona": "Kure kwemeso nzeve dzinodya.", "english": "You don’t need to be there to know what happened."},
    {"shona": "Kuwanda kwakanaka, kwakaipira kupedza muto.", "english": "Numbers are good, but they demand more resources."},
    {"shona": "Kuwanda huuya.", "english": "The more, the merrier."},
    {"shona": "Kuzeza chati kwati hunge uine katurike.", "english": "Over-reactions usually hide something."},
    {"shona": "Mandikurumidze akazvara mandinonoke.", "english": "Rushing leads to redoing, which takes longer in the end."},
    {"shona": "Manga chena yakaparira parere nhema.", "english": "The good makes the bad visible."},
    {"shona": "Matakadya kare haanyaradzi mwana.", "english": "Yesterday’s feats don’t fill today’s belly."},
    {"shona": "Mbeva zhinji hadzina mashe.", "english": "When everyone is responsible, no one is."},
    {"shona": "Mbudzi kuzvarira pavanhu kuda kutandirwa imbwa.", "english": "People do embarrassing things in public to ask for help."},
    {"shona": "Mazvokuda mavanga enyora.", "english": "Self-inflicted anguish."},
    {"shona": "Mhembwe rudzi inozvara mwana ane kazhumu.", "english": "The apple doesn’t fall far from the tree."},
    {"shona": "Mudzimu wakupa chironda wati nhunzi dzikudye.", "english": "For everything that happens, there is a reason."},
    {"shona": "Muroyi royera kure vekwako vagokureverera.", "english": "Do not be mean to those closest to you."},
    {"shona": "Mwana wamambo muranda kumwe.", "english": "Authority only works within its territory."},
    {"shona": "Mwana kuberekwa vaviri.", "english": "Some things cannot be done alone."},
    {"shona": "Mviromviro yemhanza mapfeka.", "english": "Big events announce themselves with early signs."},
    {"shona": "Mombe yekurunzirwa ndeyekukama wakarinde nzira.", "english": "Borrowed things never enjoy the freedom of your own."},
    {"shona": "Nzombe huru yakabva mukurerwa.", "english": "Great people are raised up by others."},
    {"shona": "Nzou hairemerwi nenyanga dzayo.", "english": "A person has the strength to carry their own load."},
    {"shona": "Pfavira ngoma, husiku hurefu.", "english": "Be calm and take your time."},
    {"shona": "Ramba kuudzwa akaonekwa nembonje pahuma.", "english": "Those who refuse warnings end up bruised."},
    {"shona": "Rega zvipore akabva mukutsva.", "english": "A burnt child dreads fire."},
    {"shona": "Regai dzive shiri, mazai haana muto.", "english": "Wait for full maturity before harvesting."},
    {"shona": "Rudo ibofu.", "english": "Love is blind."},
    {"shona": "Seka urema wafa.", "english": "Do not mock another’s misfortune; it may come to you."},
    {"shona": "Simbi inorohwa ichapisa.", "english": "Strike the iron while it is still hot."},
    {"shona": "Varume kutsva kwendebvu vanodzimurana.", "english": "Men help each other in times of trouble."},
    {"shona": "Vasikana kudada kudada zvenyu, tichaonana magaro pakuyambuka.", "english": "Reject people in good times and you will need them in hard ones."},
    {"shona": "Wakurumidza kumedza, kutsenga uchada.", "english": "You rushed ahead before finishing what was behind."},
    {"shona": "Yadeuka yadeuka mvura yemuguchu haidyorerwi.", "english": "What has happened cannot be undone."},
    {"shona": "Yatsika dope yanwa.", "english": "Whoever was there participated."},
    {"shona": "Zano ndega akasiya jira mumasese.", "english": "Going it alone means losing what you valued."},
    {"shona": "Zizi harina nyanga.", "english": "Things are not what they seem."},
    {"shona": "Zviuya hazviwanani.", "english": "Perfect people rarely find each other."},
    {"shona": "Zviro zviyedzwa.", "english": "You never know what is rewarding unless you try."},
    {"shona": "Zingizi gonyera pamwe maruva enyika haaperi.", "english": "Settle with one; the world’s flowers are endless."},
    {"shona": "Zvikoni zvikoni mimba haibvi negosoro.", "english": "Some things have no simple solution."},
]


# ── Tsumo of the Day ──────────────────────────────────────
def get_tsumo_of_the_day():
    """Return today's Shona proverb using the same daily rotation as config.js."""
    import time
    day_index = int(time.time() // 86400) % len(SHONA_PROVERBS)
    return SHONA_PROVERBS[day_index]


# ── Zimbabwean of the Day (Wikidata birthday match) ───────
WIKIDATA_ENDPOINT = "https://query.wikidata.org/sparql"

BIRTHDAY_SPARQL = """
SELECT ?person ?personLabel ?personDescription ?image ?birthDate ?occupationLabel ?article WHERE {{
  ?person wdt:P31 wd:Q5.
  ?person wdt:P27 wd:Q954.
  ?person wdt:P569 ?birthDate.
  FILTER(MONTH(?birthDate) = {month} && DAY(?birthDate) = {day})
  OPTIONAL {{ ?person wdt:P18 ?image. }}
  OPTIONAL {{ ?person wdt:P106 ?occupation. }}
  OPTIONAL {{
    ?article schema:about ?person.
    ?article schema:isPartOf <https://en.wikipedia.org/>.
  }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
}}
LIMIT 20
"""


def fetch_birthday_zimbabweans(today=None):
    """Query Wikidata for Zimbabweans born on today's date. Returns list of dicts."""
    if today is None:
        today = datetime.now(timezone.utc)
    query = BIRTHDAY_SPARQL.format(month=today.month, day=today.day)
    url = WIKIDATA_ENDPOINT + "?" + urllib.parse.urlencode({
        "query": query,
        "format": "json",
    })
    req = urllib.request.Request(url, headers={
        "User-Agent": "MutapaTimesNewsletter/1.0 (news@mutapatimes.com)",
        "Accept": "application/sparql-results+json",
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"  Wikidata query failed: {e}")
        return []

    results = []
    seen_ids = set()
    for binding in data.get("results", {}).get("bindings", []):
        person_uri = binding.get("person", {}).get("value", "")
        qid = person_uri.split("/")[-1] if person_uri else ""
        if not qid or qid in seen_ids:
            continue
        seen_ids.add(qid)

        name = binding.get("personLabel", {}).get("value", "")
        # Skip if label is just the QID (no English label)
        if name.startswith("Q") and name[1:].isdigit():
            continue

        description = binding.get("personDescription", {}).get("value", "")
        image = binding.get("image", {}).get("value", "")
        birth_date = binding.get("birthDate", {}).get("value", "")
        occupation = binding.get("occupationLabel", {}).get("value", "")
        wiki_url = binding.get("article", {}).get("value", "")
        wikidata_url = person_uri

        # Parse birth year
        birth_year = ""
        if birth_date:
            try:
                birth_year = str(datetime.fromisoformat(birth_date.replace("Z", "+00:00")).year)
            except (ValueError, TypeError):
                pass

        results.append({
            "qid": qid,
            "name": name,
            "description": description,
            "image": image,
            "birth_year": birth_year,
            "occupation": occupation,
            "wikipedia_url": wiki_url,
            "wikidata_url": wikidata_url,
        })

    return results


def pick_person_of_the_day(people, today=None):
    """Pick one person from the birthday list. Rotate deterministically if multiple."""
    if not people:
        return None
    if today is None:
        today = datetime.now(timezone.utc)
    # Deterministic daily rotation among birthday matches
    day_of_year = today.timetuple().tm_yday
    return people[day_of_year % len(people)]


# ── Brevo API helper ───────────────────────────────────────
def brevo_request(endpoint, payload=None, method="POST"):
    """Make authenticated request to Brevo API."""
    url = BREVO_BASE + endpoint
    headers = {
        "api-key": BREVO_API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    data = json.dumps(payload).encode("utf-8") if payload else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, json.loads(body) if body.strip() else {}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        print(f"  Brevo API error {e.code}: {body}")
        return e.code, json.loads(body) if body.strip() else {}


# ── Data loading ────────────────────────────────────────────
def parse_article_date(date_str):
    """Parse various date formats into datetime, return None on failure."""
    if not date_str:
        return None
    try:
        # ISO 8601 format (GNews)
        clean = date_str.replace("Z", "+00:00")
        return datetime.fromisoformat(clean)
    except (ValueError, TypeError):
        pass
    try:
        # RFC 2822 format (RSS feeds) — e.g. "Wed, 28 Jan 2026 15:31:13 GMT"
        from email.utils import parsedate_to_datetime
        return parsedate_to_datetime(date_str)
    except Exception:
        pass
    return None


def is_article_fresh(article, max_age_days):
    """Check if article is within max_age_days of now. Reject unparseable dates."""
    dt = parse_article_date(article.get("publishedAt", ""))
    if dt is None:
        return False
    try:
        age = (datetime.now(timezone.utc) - dt).days
        return age <= max_age_days
    except Exception:
        return False


def normalize_title(title):
    """Lowercase, strip punctuation/whitespace for comparison."""
    import re
    t = title.lower().strip()
    t = re.sub(r"[^\w\s]", "", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def titles_are_similar(t1, t2, threshold=0.65):
    """Check if two titles are about the same story using word overlap (Jaccard)."""
    w1 = set(normalize_title(t1).split())
    w2 = set(normalize_title(t2).split())
    if not w1 or not w2:
        return False
    n1, n2 = normalize_title(t1), normalize_title(t2)
    if n1 in n2 or n2 in n1:
        return True
    intersection = w1 & w2
    union = w1 | w2
    return len(intersection) / len(union) >= threshold


def load_wordle_today():
    """Read today's Shona Wordle from games/shona-wordle/words.json.

    Mirrors the day-index math used in the game's JS so the newsletter
    promotes the same word the site is serving:

        EPOCH      = 2026-05-27 UTC (Day 1)
        dayIndex   = floor((todayUTC - EPOCH) / 86400000)
        word       = answers[dayIndex % len(answers)]

    Returns dict with day_n (1-based), date_str, word, meaning,
    yesterday_word and yesterday_meaning (None if today is Day 1),
    or None if the words file is missing/empty.
    """
    filepath = os.path.join("games", "shona-wordle", "words.json")
    if not os.path.exists(filepath):
        return None
    with open(filepath) as f:
        data = json.load(f)
    answers = data.get("answers", [])
    meanings = data.get("meanings", {})
    if not answers:
        return None

    epoch = datetime(2026, 5, 27, tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    today_midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    day_index = max(0, (today_midnight - epoch).days)
    word = answers[day_index % len(answers)]

    if day_index >= 1:
        ywd = answers[(day_index - 1) % len(answers)]
        yesterday_word = ywd
        yesterday_meaning = meanings.get(ywd, "")
    else:
        yesterday_word = None
        yesterday_meaning = None

    return {
        "day_n":             day_index + 1,
        "date_str":          now.strftime("%B %d, %Y"),
        "word":              word,
        "meaning":           meanings.get(word, ""),
        "yesterday_word":    yesterday_word,
        "yesterday_meaning": yesterday_meaning,
    }


def load_articles(exclude_urls=None):
    """Read all data/*.json files, merge, deduplicate, filter by date, sort by recency."""
    if exclude_urls is None:
        exclude_urls = set()
    all_articles = []
    for cat in CATEGORIES:
        filepath = os.path.join(DATA_DIR, f"{cat}.json")
        if not os.path.exists(filepath):
            continue
        with open(filepath) as f:
            data = json.load(f)
        for a in data.get("articles", []):
            a["_category"] = cat
        all_articles.extend(data.get("articles", []))

    # Deduplicate by URL, honour exclude_urls, filter by date, and dedup by title similarity
    seen_urls = set()
    unique = []
    for a in all_articles:
        url = a.get("url", "")
        title = a.get("title", "")
        if url and url in seen_urls:
            continue
        if url and url in exclude_urls:
            continue
        # Reject articles older than MAX_ARTICLE_AGE_DAYS
        if not is_article_fresh(a, MAX_ARTICLE_AGE_DAYS):
            continue
        # Title similarity deduplication — skip near-duplicate headlines
        if title and any(titles_are_similar(title, u.get("title", "")) for u in unique):
            continue
        if url:
            seen_urls.add(url)
        unique.append(a)

    unique.sort(key=lambda a: a.get("publishedAt", ""), reverse=True)
    return unique


def pick_top_articles(articles):
    """Pick top articles prioritizing primary categories (business, politics, policy, tech).

    Strategy:
    1. Fill primary categories first (up to MAX_PER_CATEGORY each)
    2. Then fill remaining slots with secondary categories
    3. Within each category, articles are already sorted by date (newest first)
    """
    cat_counts = {c: 0 for c in CATEGORIES}
    picked = []
    picked_urls = set()

    # Pass 1: primary categories first
    for a in articles:
        cat = a.get("_category", "")
        url = a.get("url", "")
        if cat not in PRIMARY_CATEGORIES:
            continue
        if cat_counts.get(cat, 0) >= MAX_PER_CATEGORY:
            continue
        if url in picked_urls:
            continue
        picked.append(a)
        picked_urls.add(url)
        cat_counts[cat] = cat_counts.get(cat, 0) + 1
        if len(picked) >= MAX_TOTAL:
            return picked

    # Pass 2: secondary categories fill remaining slots
    for a in articles:
        cat = a.get("_category", "")
        url = a.get("url", "")
        if cat in PRIMARY_CATEGORIES:
            continue
        if cat_counts.get(cat, 0) >= MAX_PER_CATEGORY:
            continue
        if url in picked_urls:
            continue
        picked.append(a)
        picked_urls.add(url)
        cat_counts[cat] = cat_counts.get(cat, 0) + 1
        if len(picked) >= MAX_TOTAL:
            break

    return picked


# ── HTML email builder ──────────────────────────────────────
def escape_html(text):
    """Escape HTML special characters."""
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


def format_date(date_str):
    """Format date string to human-readable."""
    if not date_str:
        return ""
    try:
        clean = date_str.replace("Z", "+00:00").replace(" ", "T")
        if "+" not in clean and clean.count("T") == 1:
            clean += "+00:00"
        dt = datetime.fromisoformat(clean)
        return dt.strftime("%B %d, %Y")
    except (ValueError, TypeError):
        return ""


def add_utm(url, medium="email"):
    """Add UTM tracking parameters to a URL."""
    sep = "?" if "?" not in url else "&"
    return f"{url}{sep}utm_source=newsletter&utm_medium={medium}&utm_campaign=newsletter"


def whatsapp_share_url(title, url):
    """Build a wa.me share URL with pre-populated Mutapa Times copy."""
    tracked_url = add_utm(url, "whatsapp_from_newsletter")
    text = (
        f"{title}\n\n"
        f"\U0001f517 {tracked_url}\n\n"
        f"via The Mutapa Times \u2014 Zimbabwe news from 100+ sources \U0001f1ff\U0001f1fc\n"
        f"\U0001f4f0 https://www.mutapatimes.com?utm_source=newsletter&utm_medium=whatsapp&utm_campaign=newsletter"
    )
    return "https://wa.me/?text=" + urllib.parse.quote(text, safe="")


def whatsapp_share_link(title, url, color="rgba(255,255,255,0.5)", size="11px"):
    """Build an inline WhatsApp share link for an article."""
    wa_url = whatsapp_share_url(title, url)
    return (
        f'<a href="{wa_url}" target="_blank" '
        f'style="font-family:Helvetica,Arial,sans-serif;font-size:{size};'
        f'color:{color};text-decoration:none;white-space:nowrap;" '
        f'title="Share on WhatsApp">'
        f'WhatsApp'
        f'</a>'
    )


def build_wordle_html(wordle):
    """Build the Today's Shona Wordle section.

    Editorial-style block matching the site's wordle card: red accent
    eyebrow, day number + date, a row of six empty tiles styled like
    the in-game board, optional yesterday's reveal as a hook, and a
    dark CTA button. Email-safe (table layout, no flexbox, no SVG).
    """
    if not wordle:
        return ""

    wordle_url = (
        "https://www.mutapatimes.com/games/shona-wordle/"
        "?utm_source=newsletter&utm_medium=email&utm_campaign=wordle"
    )

    # Six empty tiles, rendered as table cells so Outlook + Gmail get them
    # consistently. 38x38 with a 2px hairline border and white fill.
    tile_cells = ""
    for _ in range(6):
        tile_cells += (
            '<td width="38" height="38" '
            'style="width:38px;height:38px;'
            'background:#ffffff;'
            'border:2px solid #d0cfc8;'
            'border-radius:4px;'
            'padding:0;mso-line-height-rule:exactly;line-height:0;">'
            '&nbsp;'
            '</td>'
            '<td width="4" style="width:4px;">&nbsp;</td>'
        )
    # Strip the trailing spacer so the row is symmetric.
    tile_cells = tile_cells.rsplit('<td width="4"', 1)[0]

    # Yesterday's word — small grey teaser, only on day 2+.
    yesterday_html = ""
    if wordle.get("yesterday_word"):
        ymeaning = wordle.get("yesterday_meaning") or ""
        ywd = escape_html(wordle["yesterday_word"].upper())
        ymeaning_part = (
            f' <span style="color:#8b8678;">({escape_html(ymeaning)})</span>'
            if ymeaning else ''
        )
        yesterday_html = (
            '<tr>'
            '<td align="center" style="padding:4px 20px 0;">'
            '<p style="font-family:Helvetica,Arial,sans-serif;font-size:12px;'
            'color:#4a4a44;margin:0;letter-spacing:0.02em;">'
            f'Yesterday&rsquo;s word: <strong style="color:#121212;'
            f'font-family:Georgia,\'Times New Roman\',serif;'
            f'letter-spacing:0.05em;">{ywd}</strong>'
            f'{ymeaning_part}'
            '</p>'
            '</td>'
            '</tr>'
        )

    return (
        '<!-- Today\'s Shona Wordle -->'
        '<tr>'
        '<td style="background:#fafaf7;padding:0;border-bottom:1px solid #e8e6df;">'
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        'style="border-collapse:collapse;">'

        # Eyebrow + headline
        '<tr>'
        '<td style="padding:24px 20px 4px;text-align:center;">'
        '<p style="font-family:Helvetica,Arial,sans-serif;font-size:11px;'
        'font-weight:700;color:#c41e1e;margin:0;'
        'text-transform:uppercase;letter-spacing:0.18em;">'
        'Today&rsquo;s Shona Wordle'
        '</p>'
        f'<h2 style="font-family:Georgia,\'Times New Roman\',serif;'
        f'font-size:22px;font-weight:900;color:#121212;'
        f'margin:8px 0 2px;line-height:1.2;letter-spacing:-0.01em;">'
        f'Word #{wordle["day_n"]} is live.'
        '</h2>'
        '<p style="font-family:Helvetica,Arial,sans-serif;font-size:13px;'
        'color:#4a4a44;margin:0 0 16px;line-height:1.5;">'
        f'{escape_html(wordle["date_str"])} &middot; '
        'Guess the six-letter Shona word in six tries.'
        '</p>'
        '</td>'
        '</tr>'

        # Six empty tiles
        '<tr>'
        '<td align="center" style="padding:0 20px 16px;">'
        '<table role="presentation" cellpadding="0" cellspacing="0" border="0">'
        f'<tr>{tile_cells}</tr>'
        '</table>'
        '</td>'
        '</tr>'

        f'{yesterday_html}'

        # CTA
        '<tr>'
        '<td align="center" style="padding:14px 20px 24px;">'
        f'<a href="{wordle_url}" target="_blank" '
        'style="display:inline-block;padding:12px 28px;'
        'font-family:Helvetica,Arial,sans-serif;'
        'font-size:12px;font-weight:700;'
        'color:#ffffff;background:#121212;'
        'text-decoration:none;text-transform:uppercase;'
        'letter-spacing:0.08em;">'
        'Play today&rsquo;s puzzle &rarr;'
        '</a>'
        '</td>'
        '</tr>'

        '</table>'
        '</td>'
        '</tr>'
    )


def build_stories_rail_html():
    """IG-Stories-style highlight rail for the newsletter top.

    Each chip is an <a> linking to the homepage with ?story=KEY&snap=0,
    so taps on mobile Mail open Safari and auto-launch the viewer for
    that category. The "IG glow" ring is a static linear-gradient on
    the chip wrapper — Apple Mail / iOS Mail / Gmail web render it;
    Outlook desktop falls back to the solid chip colour but the circle
    still reads. Inside the ring sits the faded brand-tone chip with the
    category label centred (same pattern as the site rail).
    """
    # Mirrors CHIP_COLORS from js/stories.js — pale brand tones with
    # dark ink text legibility. We seed the rail with a curated set
    # that almost always has fresh content on a publish day; if a key
    # has nothing on the site that day, the deep-link gracefully
    # degrades to just landing on the homepage.
    chips = [
        ("_latest",  "Latest",   "#E8C9C5"),  # faded brand-red
        ("Business", "Business", "#ECE2CF"),  # warm cream
        ("Policy",   "Policy",   "#D8E6D5"),  # sage green
        ("Tech",     "Tech",     "#DDE4ED"),  # pale slate
        ("Sport",    "Sport",    "#F0DCC6"),  # warm peach
        ("Culture",  "Culture",  "#E5DBE8"),  # pale lavender
    ]
    # Classic IG ring — yellow → orange → pink → purple → blue.
    ig_glow = (
        "linear-gradient(135deg,#feda75 0%,#fa7e1e 25%,"
        "#d62976 50%,#962fbf 75%,#4f5bd5 100%)"
    )

    cells = ""
    for key, label, chip_bg in chips:
        url = f"https://www.mutapatimes.com/?story={urllib.parse.quote(key)}&snap=0"
        cells += (
            '<td align="center" valign="top" '
            'style="padding:0 6px;">'
            f'<a href="{url}" target="_blank" '
            'style="text-decoration:none;display:inline-block;">'
            # Outer gradient ring (IG glow) — table for Outlook compat
            '<table role="presentation" cellpadding="0" cellspacing="0" '
            'border="0" align="center" '
            f'style="background-image:{ig_glow};'
            'background-color:#d62976;'  # Outlook desktop fallback
            'border-radius:44px;">'
            '<tr><td style="padding:3px;">'
            # Inner chip — faded brand tone, label centred
            '<table role="presentation" cellpadding="0" cellspacing="0" '
            'border="0" align="center" '
            f'style="background-color:{chip_bg};border-radius:40px;'
            'width:80px;height:80px;">'
            '<tr><td align="center" valign="middle" '
            'width="80" height="80" '
            'style="width:80px;height:80px;'
            'font-family:Helvetica,Arial,sans-serif;'
            'font-size:11px;font-weight:700;color:#1a1a1a;'
            'line-height:1.1;text-transform:uppercase;'
            f'letter-spacing:0.04em;text-align:center;">{escape_html(label)}'
            '</td></tr>'
            '</table>'
            '</td></tr>'
            '</table>'
            '</a>'
            '</td>'
        )

    return (
        '<!-- Stories rail — IG-style highlights, taps open Safari -->'
        '<tr>'
        '<td style="padding:14px 8px 8px;background:#ffffff;'
        'border-bottom:1px solid #e8e6e3;">'
        '<table role="presentation" width="100%" cellpadding="0" '
        'cellspacing="0" border="0">'
        '<tr>'
        f'{cells}'
        '</tr>'
        '</table>'
        '<p style="font-family:Helvetica,Arial,sans-serif;'
        'font-size:10px;color:#8b8678;margin:10px 0 0;'
        'text-align:center;letter-spacing:0.04em;">'
        'Tap a story &middot; opens in your browser'
        '</p>'
        '</td>'
        '</tr>'
    )


def build_tsumo_html(proverb):
    """Build the Tsumo of the Day section for the newsletter."""
    if not proverb:
        return ""
    shona = escape_html(proverb["shona"])
    english = escape_html(proverb["english"])
    return (
        '<!-- Tsumo of the Day -->'
        '<tr>'
        '<td style="background:#1a1a1a;padding:18px 20px;text-align:center;">'
        '<p style="font-family:Helvetica,Arial,sans-serif;font-size:9px;'
        'font-weight:600;color:rgba(255,255,255,0.25);margin:0 0 6px;'
        'text-transform:uppercase;letter-spacing:0.15em;">'
        'Tsumo of the Day</p>'
        f'<p style="font-family:Georgia,\'Times New Roman\',serif;'
        f'font-style:italic;font-size:15px;color:rgba(255,255,255,0.75);'
        f'margin:0 0 4px;line-height:1.5;">'
        f'\u201c{shona}\u201d</p>'
        f'<p style="font-family:Helvetica,Arial,sans-serif;font-size:11px;'
        f'color:rgba(255,255,255,0.35);margin:0;letter-spacing:0.04em;">'
        f'{english}</p>'
        '</td>'
        '</tr>'
    )


def build_person_of_day_html(person):
    """Build the Zimbabwean of the Day section. Neutral, factual tone."""
    if not person:
        return ""
    name = escape_html(person.get("name", ""))
    description = escape_html(person.get("description", ""))
    occupation = escape_html(person.get("occupation", ""))
    birth_year = person.get("birth_year", "")
    image = person.get("image", "")

    # Build subtitle: occupation + birth year
    subtitle_parts = []
    if occupation:
        subtitle_parts.append(occupation.capitalize())
    if birth_year:
        subtitle_parts.append(f"b.\u2009{birth_year}")
    subtitle = " &middot; ".join(subtitle_parts)

    # Use description as the bio line (Wikidata short description)
    bio_html = ""
    if description:
        bio_html = (
            f'<p style="font-family:Helvetica,Arial,sans-serif;font-size:13px;'
            f'color:#2c2c2c;margin:6px 0 0;line-height:1.5;">'
            f'{description[0].upper()}{description[1:] if len(description) > 1 else ""}.</p>'
            if not description.endswith(".")
            else f'<p style="font-family:Helvetica,Arial,sans-serif;font-size:13px;'
            f'color:#2c2c2c;margin:6px 0 0;line-height:1.5;">'
            f'{description[0].upper()}{description[1:] if len(description) > 1 else ""}</p>'
        )

    # Image (if available from Wikidata)
    image_html = ""
    if image:
        image_html = (
            '<td style="padding:0 0 0 14px;vertical-align:top;" width="72">'
            f'<img src="{escape_html(image)}" alt="{name}" width="72" height="72" '
            'style="display:block;width:72px;height:72px;object-fit:cover;'
            'border-radius:50%;">'
            '</td>'
        )

    # Link — always drive traffic to Mutapa People page
    people_url = add_utm(f"{SITE_URL}/people.html")
    link_html = (
        f'<p style="font-family:Helvetica,Arial,sans-serif;font-size:11px;'
        f'margin:8px 0 0;">'
        f'<a href="{escape_html(people_url)}" target="_blank" '
        f'style="color:#00897b;text-decoration:none;">Read more on Mutapa People &rarr;</a>'
        f'</p>'
        )

    return (
        '<!-- Zimbabwean of the Day -->'
        '<tr>'
        '<td style="padding:0 20px;">'
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0"'
        ' style="border-collapse:collapse;">'
        '<tr><td style="border-top:2px solid #1a1a1a;padding-top:8px;">'
        '<p style="font-family:Georgia,\'Times New Roman\',serif;'
        'font-size:11px;font-weight:700;color:#8b8678;margin:0 0 10px;'
        'text-transform:uppercase;letter-spacing:0.1em;">'
        'Zimbabwean of the Day</p>'
        '</td></tr>'
        '</table>'
        '</td>'
        '</tr>'
        '<tr>'
        '<td style="padding:0 20px 16px;">'
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0"'
        ' style="border-collapse:collapse;">'
        '<tr>'
        '<td style="vertical-align:top;">'
        f'<p style="font-family:Georgia,\'Times New Roman\',serif;'
        f'font-size:17px;font-weight:700;color:#1a1a1a;margin:0;line-height:1.3;">'
        f'{name}</p>'
        f'<p style="font-family:Helvetica,Arial,sans-serif;font-size:11px;'
        f'color:#8b8678;margin:3px 0 0;text-transform:uppercase;'
        f'letter-spacing:0.04em;">{subtitle}</p>'
        f'{bio_html}'
        f'{link_html}'
        '</td>'
        f'{image_html}'
        '</tr>'
        '</table>'
        '</td>'
        '</tr>'
    )


def build_html(category_articles, wordle=None, tsumo=None):
    """Build inline-CSS HTML email matching The Mutapa Times website style."""
    today = datetime.now(timezone.utc)
    date_display = today.strftime("%A, %B %d, %Y")
    total_count = len(category_articles)

    # Preheader: today's Shona Wordle teaser. Falls back to a generic
    # briefing line if the wordle data is unavailable. Plain text only
    # (Apple Mail / Gmail render this as the inbox snippet).
    if wordle:
        preheader = (
            f"Today’s Shona Wordle is live. Word #{wordle['day_n']}, "
            "play free in your browser."
        )
    else:
        preheader = f"Top Zimbabwe headlines from foreign press, {date_display}."

    wordle_html = build_wordle_html(wordle)
    stories_rail_html = build_stories_rail_html()
    tsumo_html = build_tsumo_html(tsumo)

    # Build category article rows
    rows = ""
    for i, a in enumerate(category_articles):
        title = escape_html(a.get("title", "No title"))
        raw_title = a.get("title", "No title")
        url = escape_html(a.get("url", "#"))
        raw_url = a.get("url", "#")
        desc = a.get("description", "")
        if desc and len(desc) > 200:
            desc = desc[:197] + "..."
        desc = escape_html(desc)

        source = a.get("source", {})
        source_name = escape_html(source.get("name", "") if isinstance(source, dict) else str(source))
        pub_date = format_date(a.get("publishedAt", ""))
        category = a.get("_category", "").capitalize()

        meta_parts = [p for p in [source_name, category, pub_date] if p]
        meta_line = " &middot; ".join(meta_parts)

        wa_link = whatsapp_share_link(raw_title, raw_url, color="#8b8678", size="11px")

        bg = "#ffffff" if i % 2 == 0 else "#fafaf7"

        desc_html = ""
        if desc:
            desc_html = (
                '<p style="font-family:Helvetica,Arial,sans-serif;font-size:13px;'
                f'color:#4a4a44;margin:6px 0 0;line-height:1.5;">{desc}</p>'
            )

        rows += (
            '<tr>'
            f'<td style="padding:14px 20px;background:{bg};border-bottom:1px solid #e8e6df;">'
            f'<a href="{url}" target="_blank" '
            'style="font-family:Georgia,\'Times New Roman\',serif;'
            'font-size:16px;font-weight:700;color:#121212;'
            f'text-decoration:none;line-height:1.3;">{title}</a>'
            f'{desc_html}'
            '<p style="font-family:Helvetica,Arial,sans-serif;font-size:11px;'
            f'color:#8b8678;margin:6px 0 0;line-height:1.4;">'
            f'{meta_line}'
            f' &nbsp;&middot;&nbsp; {wa_link}'
            '</p>'
            '</td>'
            '</tr>'
        )

    # WhatsApp share URL for the general Mutapa Times share in footer
    general_wa_text = (
        "\U0001f4f0 The Mutapa Times \u2014 Zimbabwe outside-in.\n\n"
        "Curated news from foreign press, delivered Mon/Wed/Sat.\n\n"
        "\U0001f1ff\U0001f1fc Subscribe free: https://www.mutapatimes.com"
    )
    general_wa_url = "https://wa.me/?text=" + urllib.parse.quote(general_wa_text, safe="")

    html = f"""<!DOCTYPE html>
<html lang="en" xmlns="http://www.w3.org/1999/xhtml">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <meta http-equiv="X-UA-Compatible" content="IE=edge">
  <title>The Mutapa Times Newsletter</title>
  <!--[if mso]>
  <style>* {{ font-family: Georgia, serif !important; }}</style>
  <![endif]-->
  <style>
    @media only screen and (max-width: 620px) {{
      .outer-wrap {{ padding: 0 !important; }}
      .main-table {{ width: 100% !important; }}
      .masthead-title {{ font-size: 22px !important; letter-spacing: 0.02em !important; }}
      .tagline {{ font-size: 12px !important; }}
      .masthead-cell {{ padding: 20px 16px 8px !important; }}
      .date-cell {{ padding: 8px 16px !important; }}
      .intro-cell {{ padding: 14px 16px 10px !important; }}
      .intro-text {{ font-size: 13px !important; }}
      .section-header-cell {{ padding: 14px 16px 0 !important; }}
      .article-cell {{ padding: 12px 16px !important; }}
      .article-title {{ font-size: 15px !important; }}
      .article-desc {{ font-size: 12px !important; }}
      .cta-cell {{ padding: 20px 16px !important; }}
      .divider-cell {{ padding: 0 16px !important; }}
      .footer-cell {{ padding: 16px 16px 24px !important; }}
      .share-cell {{ padding: 16px 16px 4px !important; }}
    }}
  </style>
</head>
<body style="margin:0;padding:0;background-color:#f0efeb;
             font-family:Helvetica,Arial,sans-serif;-webkit-font-smoothing:antialiased;">

  <!-- Preheader -->
  <div style="display:none;max-height:0;overflow:hidden;mso-hide:all;">
    {preheader}
  </div>

  <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
         style="background-color:#f0efeb;">
    <tr>
      <td align="center" class="outer-wrap" style="padding:16px 8px;">

        <!-- Main container -->
        <table role="presentation" width="600" cellpadding="0" cellspacing="0"
               class="main-table"
               style="max-width:600px;width:100%;background:#ffffff;border-collapse:collapse;">

          <!-- Masthead -->
          <tr>
            <td class="masthead-cell" style="padding:24px 20px 8px;text-align:center;
                       border-bottom:2px solid #121212;">
              <h1 class="masthead-title"
                  style="font-family:Georgia,'Times New Roman',serif;
                         font-size:26px;font-weight:900;color:#121212;
                         margin:0;letter-spacing:0.03em;text-transform:uppercase;">
                THE MUTAPA TIMES
              </h1>
              <p class="tagline"
                 style="font-family:Helvetica,Arial,sans-serif;
                        font-size:11px;color:#8b8678;
                        margin:6px 0 0;text-transform:uppercase;
                        letter-spacing:0.18em;">
                Zimbabwe outside-in
              </p>
            </td>
          </tr>

          <!-- Date bar -->
          <tr>
            <td class="date-cell" style="padding:10px 20px;text-align:center;
                       border-bottom:1px solid #e8e6df;">
              <span style="font-family:Helvetica,Arial,sans-serif;
                           font-size:10px;color:#4a4a44;
                           text-transform:uppercase;letter-spacing:0.06em;">
                {date_display} &nbsp;&middot;&nbsp; Published Mon &middot; Wed &middot; Sat
              </span>
            </td>
          </tr>

          <!-- Intro -->
          <tr>
            <td class="intro-cell" style="padding:18px 20px 12px;text-align:center;">
              <p class="intro-text"
                 style="font-family:Helvetica,Arial,sans-serif;
                        font-size:14px;color:#4a4a44;line-height:1.5;margin:0;">
                Your briefing of the most important Zimbabwe headlines
                from foreign press. Curated for the diaspora, twice a week.
              </p>
            </td>
          </tr>

          {stories_rail_html}

          {wordle_html}

          {tsumo_html}

          <!-- Section header -->
          <tr>
            <td class="section-header-cell" style="padding:16px 20px 0;">
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
                <tr>
                  <td style="border-top:2px solid #121212;padding-top:8px;">
                    <h2 style="font-family:Georgia,'Times New Roman',serif;
                               font-size:16px;font-weight:700;color:#121212;
                               margin:0 0 2px;text-transform:uppercase;
                               letter-spacing:0.04em;">
                      Top Headlines
                    </h2>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Articles -->
          {rows}

          <!-- CTA -->
          <tr>
            <td class="cta-cell" style="padding:24px 20px;text-align:center;">
              <a href="{SITE_URL}" target="_blank"
                 style="display:inline-block;padding:10px 28px;
                        font-family:Helvetica,Arial,sans-serif;
                        font-size:12px;font-weight:700;
                        text-transform:uppercase;letter-spacing:0.08em;
                        color:#ffffff;background:#c41e1e;
                        text-decoration:none;">
                Read More at mutapatimes.com
              </a>
            </td>
          </tr>

          <!-- Share with a friend -->
          <tr>
            <td class="share-cell" style="padding:20px 20px 6px;text-align:center;
                       border-top:1px solid #e8e6df;">
              <p style="font-family:Georgia,'Times New Roman',serif;
                        font-size:15px;font-weight:700;color:#121212;
                        margin:0 0 6px;">
                Share the news
              </p>
              <p style="font-family:Helvetica,Arial,sans-serif;
                        font-size:12px;color:#4a4a44;line-height:1.5;margin:0 0 12px;">
                Know someone who should be reading this? Send them The Mutapa Times.
              </p>
              <a href="{general_wa_url}" target="_blank"
                 style="display:inline-block;padding:8px 20px;
                        font-family:Helvetica,Arial,sans-serif;
                        font-size:12px;font-weight:700;
                        color:#ffffff;background:#25d366;
                        text-decoration:none;letter-spacing:0.02em;">
                Share on WhatsApp
              </a>
              &nbsp;&nbsp;
              <a href="mailto:?subject=The%20Mutapa%20Times&amp;body=Check%20out%20The%20Mutapa%20Times%2C%20curated%20Zimbabwe%20news%20from%20foreign%20press%2C%20delivered%20Mondays%20%26%20Thursdays.%0A%0AIf%20a%20friend%20forwarded%20this%20to%20you%2C%20subscribe%20at%3A%0Ahttps%3A%2F%2Fwww.mutapatimes.com%2Fsubscribe.html%3Fref%3Dnewsletter-share"
                 target="_blank"
                 style="display:inline-block;padding:8px 20px;
                        font-family:Helvetica,Arial,sans-serif;
                        font-size:12px;font-weight:700;
                        color:#ffffff;background:#121212;
                        text-decoration:none;letter-spacing:0.02em;">
                Share via Email
              </a>
              <p style="font-family:Helvetica,Arial,sans-serif;
                        font-size:11px;color:#4a4a44;margin:14px 0 0;">
                Forward to a friend. It is how we grow. If this was
                forwarded to you, <a href="https://www.mutapatimes.com/subscribe.html?ref=newsletter-forward"
                style="color:#c41e1e;font-weight:700;">subscribe free</a>.
              </p>
            </td>
          </tr>

          <!-- Follow @mutapatimes on X — pushes brand-account growth -->
          <tr>
            <td class="follow-cell" style="padding:6px 20px 16px;text-align:center;">
              <p style="font-family:Helvetica,Arial,sans-serif;
                        font-size:12px;color:#4a4a44;line-height:1.5;margin:0 0 10px;">
                Between briefings, follow us on X for breaking stories.
              </p>
              <a href="https://twitter.com/intent/follow?screen_name=mutapatimes"
                 target="_blank"
                 style="display:inline-block;padding:8px 20px;
                        font-family:Helvetica,Arial,sans-serif;
                        font-size:12px;font-weight:700;
                        color:#ffffff;background:#121212;
                        text-decoration:none;letter-spacing:0.02em;
                        border-radius:999px;">
                𝕏  Follow @mutapatimes
              </a>
            </td>
          </tr>

          <!-- Divider -->
          <tr>
            <td class="divider-cell" style="padding:0 20px;">
              <hr style="border:none;border-top:1px solid #e8e6df;margin:16px 0 0;">
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td class="footer-cell" style="padding:16px 20px 24px;text-align:center;background:#fafaf7;">
              <p style="font-family:Helvetica,Arial,sans-serif;
                        font-size:11px;color:#4a4a44;line-height:1.5;margin:0 0 6px;">
                The Mutapa Times delivers curated Zimbabwean news from foreign press
                for the diaspora, every Monday and Thursday.
              </p>
              <p style="font-family:Helvetica,Arial,sans-serif;
                        font-size:10px;color:#8b8678;margin:0 0 6px;">
                <a href="{SITE_URL}" style="color:#c41e1e;text-decoration:none;">
                  mutapatimes.com
                </a>
                &nbsp;&middot;&nbsp;
                <a href="https://twitter.com/mutapatimes" style="color:#c41e1e;text-decoration:none;">
                  @mutapatimes
                </a>
              </p>
              <p style="font-family:Helvetica,Arial,sans-serif;
                        font-size:10px;color:#8b8678;margin:0;">
                <a href="{{{{ unsubscribe }}}}" style="color:#8b8678;text-decoration:underline;">
                  Unsubscribe
                </a>
                &nbsp;&middot;&nbsp;
                <a href="{{{{ mirror }}}}" style="color:#8b8678;text-decoration:underline;">
                  View in browser
                </a>
              </p>
            </td>
          </tr>

        </table>

      </td>
    </tr>
  </table>
</body>
</html>"""
    return html, total_count


# ── Brevo campaign ──────────────────────────────────────────
def create_and_send_campaign(html_content, subject):
    """Create email campaign in Brevo and send immediately."""
    today = datetime.now(timezone.utc)
    campaign_name = f"Newsletter {today.strftime('%Y-%m-%d')}"

    # Create campaign
    payload = {
        "name": campaign_name,
        "subject": subject,
        "sender": {"name": SENDER_NAME, "email": SENDER_EMAIL},
        "htmlContent": html_content,
        "recipients": {"listIds": [BREVO_LIST_ID]},
    }
    status, resp = brevo_request("/emailCampaigns", payload)
    if status not in (200, 201):
        print(f"ERROR: Failed to create campaign: {resp}")
        sys.exit(1)

    campaign_id = resp.get("id")
    print(f"  Campaign created: ID={campaign_id}")

    # Send immediately
    status, resp = brevo_request(f"/emailCampaigns/{campaign_id}/sendNow")
    if status not in (200, 202, 204):
        print(f"ERROR: Failed to send campaign: {resp}")
        sys.exit(1)

    print(f"  Campaign {campaign_id} sent successfully!")


# ── Main ────────────────────────────────────────────────────
def main():
    if not BREVO_API_KEY:
        print("ERROR: BREVO_API_KEY not set")
        sys.exit(1)

    print("Loading today's Shona Wordle...")
    wordle = load_wordle_today()
    if wordle:
        print(f"  Word #{wordle['day_n']}, {wordle['date_str']}")
    else:
        print("  No wordle data found; sending without the wordle block")

    print("Loading category articles...")
    articles = load_articles()
    if not articles:
        print("No articles found in data/*.json, skipping newsletter")
        sys.exit(0)

    top = pick_top_articles(articles)
    print(f"  Selected {len(top)} category articles for newsletter")

    # Editor's pick: force a pinned lead to the top (auto-expires by date).
    if LEAD_OVERRIDE:
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if today_str <= LEAD_OVERRIDE.get("until", today_str):
            lead = {k: v for k, v in LEAD_OVERRIDE.items() if k != "until"}
            top = [a for a in top
                   if a.get("url") != lead.get("url")
                   and not titles_are_similar(a.get("title", ""), lead.get("title", ""))]
            top.insert(0, lead)
            print(f"  Lead override (until {LEAD_OVERRIDE['until']}): {lead['title']}")
        else:
            print(f"  Lead override expired ({LEAD_OVERRIDE['until']}); using auto-pick")

    # Tsumo of the Day, same daily rotation as the website
    tsumo = get_tsumo_of_the_day()
    print(f"  Tsumo: \u201c{tsumo['shona']}\u201d")

    print("Building email HTML...")
    html, total_count = build_html(top, wordle=wordle, tsumo=tsumo)

    # Dynamic subject line: "Monday morning briefing: 15 new headlines from Zimbabwe"
    today = datetime.now(timezone.utc)
    day_label = DAY_GREETINGS.get(today.weekday(), today.strftime("%A"))
    subject = f"{day_label} briefing: {total_count} new headlines from Zimbabwe"

    print(f"  Subject: {subject}")

    print("Creating and sending campaign via Brevo...")
    create_and_send_campaign(html, subject)

    print("\nNewsletter sent successfully.")


if __name__ == "__main__":
    main()
