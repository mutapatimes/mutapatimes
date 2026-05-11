"""Curated map of names → official X handles, used to inject @mentions into
Autolist tweets (via feed.xml title) and Metricool CSV Twitter captions.

When @mentioned, the named account gets a notification — which often leads
to a like, reply, or repost from accounts orders of magnitude bigger than
ours. The single biggest lever for a 0-follower account.

Coverage is intentionally conservative: only names where the handle is
either officially documented or widely confirmed. Ambiguous abbreviations
(WHO, AP, ICC standalone) are matched only via their long-form names to
avoid mis-mentioning random tweets. Handles flagged "medium confidence" by
the user's research should be spot-checked before relying on them.
"""
import re

# Maximum mentions to inject per tweet so we don't look spammy or eat the
# 280-char budget. Source-publisher mention is separate and always wins.
MAX_ENTITY_MENTIONS = 2

# ── Source publisher → official X handle ────────────────────────
# Used to rewrite "via {Source Name}" into "via {@handle}" inside the
# tweet/description. One @mention per tweet — the publisher.
SOURCE_HANDLES = {
    "reuters": "@Reuters",
    "the guardian": "@guardian",
    "guardian": "@guardian",
    "bloomberg": "@business",
    "associated press": "@AP",
    "the associated press": "@AP",
    "cnn": "@CNN",
    "xinhua": "@XHNews",
    "espn cricinfo": "@ESPNcricinfo",
    "cricinfo": "@ESPNcricinfo",
    "sabc news": "@SABCNews",
    "sabc": "@SABCNews",
    "the herald": "@HeraldZimbabwe",
    "herald zimbabwe": "@HeraldZimbabwe",
    "herald zw": "@HeraldZimbabwe",
    "newsday zimbabwe": "@NewsDayZimbabwe",
    "newsday": "@NewsDayZimbabwe",
    "the zimbabwean": "@thezimbabwean",
    "bulawayo24": "@bulawayo24",
    "bulawayo24 news": "@bulawayo24",
    "263chat": "@263Chat",
    "iharare": "@iHarare",
    "techzim": "@Techzim",
    "nehanda radio": "@nehandaradio",
    "zimbabwe situation": "@zimsituation",
    "zimcricket": "@ZimCricketv",
}


# ── People / organisations → official X handle ──────────────────
# Matched against the article title + description. Multi-word names match
# as phrases; single-word names use \b word boundaries. Order doesn't
# matter — longest names are tried first so "Cyril Ramaphosa" wins over
# any single-word collision.
ENTITY_HANDLES = {
    # Music / celebrities (high confidence)
    "dr dre": "@drdre",
    "dr. dre": "@drdre",
    "kendrick lamar": "@kendricklamar",
    "will.i.am": "@iamwill",
    "shakira": "@shakira",
    "britney spears": "@britneyspears",
    "dolly parton": "@dollyparton",
    "david attenborough": "@BBCEarth",
    "chris rock": "@chrisrock",
    "ted turner": "@tedturner",

    # SA politics (high confidence)
    "cyril ramaphosa": "@CyrilRamaphosa",
    "julius malema": "@Julius_S_Malema",
    "mmusi maimane": "@MmusiMaimane",
    "gayton mckenzie": "@GaytonMcK",
    "economic freedom fighters": "@EFFSouthAfrica",
    "democratic alliance": "@Our_DA",
    "african national congress": "@MYANC",

    # ZW politics (high confidence + medium)
    "nelson chamisa": "@nelsonchamisa",
    "jonathan moyo": "@ProfJNMoyo",
    "prof jonathan moyo": "@ProfJNMoyo",
    "wicknell chivayo": "@wicknellchivayo",
    "blessed mhlanga": "@bbmhlanga",
    "tendai ruben mbofana": "@TendaiMbofana",
    "kudzayi mutisi": "@KMutisi",
    "tawanda maswanhise": "@TMaswanhise",
    "shingai shoniwa": "@ShingaiShoniwa",
    "learnmore jonasi": "@learnmorejonasi",
    "sonia mbele": "@Sonia_Mbele",
    "simz ngema": "@SimzNgema",
    "ibhetshu likazulu": "@IbhetshuLikaZul",
    "zanu pf": "@ZANUPF_Official",
    "zanu-pf": "@ZANUPF_Official",
    "zanupf": "@ZANUPF_Official",
    "friendship bench": "@FriendshipBench",
    "zimbabwe republic police": "@PoliceZimbabwe",
    "reserve bank of zimbabwe": "@ReserveBankZIM",
    "zimbabwe stock exchange": "@ZSE_ZW",
    "zesa": "@ZESAOfficial",
    "zesa holdings": "@ZESAOfficial",
    "netone": "@NetOneCellular",
    "telone": "@TelOneZW",
    "econet wireless": "@econetzimbabwe",
    "liquid intelligent technologies": "@LiquidInTech",
    "liquid telecom": "@LiquidInTech",
    "potraz": "@potrazinfo",
    "invictus energy": "@InvictusEnergy",
    "zimbabwe tourism authority": "@TourismZimbabwe",
    "zimbabwe cricket": "@ZimCricketv",
    "pakistan cricket board": "@TheRealPCB",
    "three men on a boat": "@3menonaboat",

    # International orgs
    "afreximbank": "@afreximbank",
    "african development bank": "@AfDB_Group",
    "world food programme": "@WFP",
    "international labour organization": "@ilo",
    "world health organization": "@WHO",
    "european union in zimbabwe": "@EUinZim",

    # Football clubs (high confidence)
    "manchester united": "@ManUtd",
    "man utd": "@ManUtd",
    "liverpool fc": "@LFC",
    "arsenal fc": "@Arsenal",
    "manchester city": "@ManCity",
    "man city": "@ManCity",
    "inter milan": "@Inter_en",
    "motherwell fc": "@MotherwellFC",
    "al ahly": "@AlAhly",
}

# Single-word club names — only matched when one of these context cues
# also appears in the text, to avoid mentioning @Arsenal for a weapons
# article or @LFC for an unrelated person named "Liverpool".
_FOOTBALL_CONTEXT = re.compile(
    r"\b(football|soccer|premier\s*league|premiership|champions\s*league|"
    r"goal|striker|midfield|fixture|kick[-\s]*off|matchday|league|fa\s*cup|"
    r"epl|coach|manager|defender|signing|transfer|fixture)\b",
    re.IGNORECASE,
)
_CONTEXTUAL_CLUB_PATTERNS = [
    (re.compile(r"(?<![A-Za-z0-9])arsenal(?![A-Za-z0-9])", re.IGNORECASE), "@Arsenal"),
    (re.compile(r"(?<![A-Za-z0-9])liverpool(?![A-Za-z0-9])", re.IGNORECASE), "@LFC"),
]


def _pattern_for(name):
    """Compile a word-boundary regex for one name. Handles spaces flexibly
    (one or more whitespace chars between words)."""
    parts = [re.escape(p) for p in name.split()]
    return re.compile(r"(?<![A-Za-z0-9])" + r"\s+".join(parts) + r"(?![A-Za-z0-9])", re.IGNORECASE)


# Longest names first so multi-word entities are tried before any
# substring inside them (e.g., "Cyril Ramaphosa" beats just "ANC").
_ENTITY_PATTERNS = [
    (_pattern_for(name), handle)
    for name, handle in sorted(ENTITY_HANDLES.items(), key=lambda x: -len(x[0]))
]


def find_entity_mentions(text, limit=MAX_ENTITY_MENTIONS):
    """Return up to `limit` unique @handles for entities named in `text`."""
    if not text:
        return []
    seen = set()
    out = []
    for pattern, handle in _ENTITY_PATTERNS:
        if handle in seen:
            continue
        if pattern.search(text):
            seen.add(handle)
            out.append(handle)
            if len(out) >= limit:
                return out
    # Single-word club mentions only fire when football context is present —
    # avoids mistagging an article about a weapons "arsenal".
    if _FOOTBALL_CONTEXT.search(text):
        for pattern, handle in _CONTEXTUAL_CLUB_PATTERNS:
            if handle in seen:
                continue
            if pattern.search(text):
                seen.add(handle)
                out.append(handle)
                if len(out) >= limit:
                    return out
    return out


def source_mention(source_name):
    """Return @handle for a known source publisher, or None."""
    if not source_name:
        return None
    return SOURCE_HANDLES.get(source_name.strip().lower())


def all_mentions(title, description="", source=""):
    """Convenience: combined source @handle (if known) + up to
    MAX_ENTITY_MENTIONS entity @handles found in title + description.
    Deduplicates so we never repeat the same handle.

    Returns the list ordered: [source_handle, entity_handle_1, ...]."""
    out = []
    sh = source_mention(source)
    if sh:
        out.append(sh)
    seen = set(out)
    for h in find_entity_mentions(f"{title}\n{description}"):
        if h not in seen:
            out.append(h)
            seen.add(h)
    return out
