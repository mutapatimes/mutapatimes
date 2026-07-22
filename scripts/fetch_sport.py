#!/usr/bin/env python3
"""Fetch standings + fixtures + results for the /sport section into JSON.

Writes data/sport/<slug>.json (one per league) + data/sport/index.json, in a
provider-normalised schema the client (js/sport.js) renders directly. Runs from
a scheduled workflow; keys come from env (GitHub secrets), never the repo:

  FOOTBALL_DATA_TOKEN   football-data.org free token   (EPL full table)
  THESPORTSDB_KEY       TheSportsDB key (default 123)   (SA + Zimbabwe)

Rate note: football-data free = 10 req/min (we use ~3 calls); TheSportsDB free
is generous but caps tables at 5 rows and season lists at 15 events. Both are
well within a ~2-hourly cron. A league that fails to fetch keeps its previous
JSON (we never overwrite good data with an error).
"""
import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sport_config import LEAGUES  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "data", "sport")

FD_TOKEN = os.environ.get("FOOTBALL_DATA_TOKEN", "").strip()
# `or "123"` (not a get-default) so an empty secret still falls back to the
# free key rather than producing a keyless ".../json//..." URL.
TSDB_KEY = (os.environ.get("THESPORTSDB_KEY") or "123").strip()
TSDB = "https://www.thesportsdb.com/api/v1/json/" + TSDB_KEY


def _get(url, headers=None, timeout=25):
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def _num(v, default=0):
    try:
        return int(v)
    except (TypeError, ValueError):
        return default


# ── football-data.org (EPL) ──────────────────────────────────────────────
def fetch_football_data(lg):
    if not FD_TOKEN:
        raise RuntimeError("FOOTBALL_DATA_TOKEN not set")
    h = {"X-Auth-Token": FD_TOKEN}
    code = lg["fd_code"]
    st = _get(f"https://api.football-data.org/v4/competitions/{code}/standings", h)
    season = ""
    s = st.get("season") or {}
    if s.get("startDate"):
        y1 = s["startDate"][:4]
        y2 = (s.get("endDate") or "")[:4]
        season = f"{y1}/{y2[2:]}" if y2 else y1
    total = (st.get("standings") or [{}])[0].get("table") or []
    table = [{
        "rank": row.get("position"),
        "team": (row.get("team") or {}).get("shortName") or (row.get("team") or {}).get("name"),
        "badge": (row.get("team") or {}).get("crest") or "",
        "played": row.get("playedGames"),
        "win": row.get("won"), "draw": row.get("draw"), "loss": row.get("lost"),
        "gf": row.get("goalsFor"), "ga": row.get("goalsAgainst"),
        "gd": row.get("goalDifference"), "points": row.get("points"),
    } for row in total]

    results, fixtures = [], []
    try:
        m = _get(f"https://api.football-data.org/v4/competitions/{code}/matches?status=FINISHED", h)
        for x in (m.get("matches") or [])[-8:]:
            ft = (x.get("score") or {}).get("fullTime") or {}
            results.append({
                "date": (x.get("utcDate") or "")[:10],
                "home": (x.get("homeTeam") or {}).get("shortName") or (x.get("homeTeam") or {}).get("name"),
                "away": (x.get("awayTeam") or {}).get("shortName") or (x.get("awayTeam") or {}).get("name"),
                "hs": ft.get("home"), "as": ft.get("away"),
            })
    except Exception as e:
        print(f"    (results skipped: {e})")
    try:
        m = _get(f"https://api.football-data.org/v4/competitions/{code}/matches?status=SCHEDULED", h)
        for x in (m.get("matches") or [])[:8]:
            fixtures.append({
                "date": (x.get("utcDate") or "")[:10],
                "time": (x.get("utcDate") or "")[11:16],
                "home": (x.get("homeTeam") or {}).get("shortName") or (x.get("homeTeam") or {}).get("name"),
                "away": (x.get("awayTeam") or {}).get("shortName") or (x.get("awayTeam") or {}).get("name"),
            })
    except Exception as e:
        print(f"    (fixtures skipped: {e})")

    return season, table, results, fixtures, False


# ── TheSportsDB (SA + Zimbabwe) ───────────────────────────────────────────
def fetch_thesportsdb(lg):
    lid = lg["tsdb_league"]
    # Auto-detect the current season so it rolls over without a code change.
    season = ""
    try:
        info = (_get(f"{TSDB}/lookupleague.php?id={lid}").get("leagues") or [{}])[0]
        season = info.get("strCurrentSeason") or ""
    except Exception as e:
        print(f"    (season lookup failed: {e})")

    table = []
    if season:
        try:
            t = _get(f"{TSDB}/lookuptable.php?l={lid}&s={season}").get("table") or []
            table = [{
                "rank": _num(r.get("intRank")),
                "team": r.get("strTeam"),
                "badge": r.get("strBadge") or "",
                "played": _num(r.get("intPlayed")),
                "win": _num(r.get("intWin")), "draw": _num(r.get("intDraw")), "loss": _num(r.get("intLoss")),
                "gf": _num(r.get("intGoalsFor")), "ga": _num(r.get("intGoalsAgainst")),
                "gd": _num(r.get("intGoalDifference")), "points": _num(r.get("intPoints")),
            } for r in t]
        except Exception as e:
            print(f"    (table failed: {e})")

    def _events(url):
        try:
            return _get(url).get("events") or []
        except Exception:
            return []

    results = []
    for x in _events(f"{TSDB}/eventspastleague.php?id={lid}"):
        if not isinstance(x, dict):
            continue
        results.append({
            "date": x.get("dateEvent"),
            "home": x.get("strHomeTeam"), "away": x.get("strAwayTeam"),
            "hs": _num(x.get("intHomeScore"), None), "as": _num(x.get("intAwayScore"), None),
        })
    fixtures = []
    for x in _events(f"{TSDB}/eventsnextleague.php?id={lid}"):
        if not isinstance(x, dict):
            continue
        fixtures.append({
            "date": x.get("dateEvent"), "time": (x.get("strTime") or "")[:5],
            "home": x.get("strHomeTeam"), "away": x.get("strAwayTeam"),
        })
    # Free key returns at most 5 table rows — flag it so the UI can say so.
    capped = len(table) <= 5
    return season, table, results[:8], fixtures[:8], capped


FETCHERS = {"football_data": fetch_football_data, "thesportsdb": fetch_thesportsdb}

KUNDAI = "kundai kaycee"


def build_editorial(now):
    """Write data/sport/editorial.json — the sport columns/reads surfaced on the
    /sport pages. Kundai Kaycee's columns come first, then the latest Sport reads.
    Sourced from the article index so new pieces appear without a page rebuild."""
    idx = os.path.join(ROOT, "content", "articles", "index.json")
    try:
        with open(idx, encoding="utf-8") as f:
            arts = json.load(f)
        if isinstance(arts, dict):
            arts = arts.get("articles") or arts.get("items") or []
    except Exception as e:
        print(f"[editorial] skipped: {e}")
        return

    def is_col(a):
        return (a.get("author") or "").strip().lower() == KUNDAI

    sport = [a for a in arts if a.get("category") == "Sport" or is_col(a)]
    sport.sort(key=lambda a: a.get("date") or "", reverse=True)
    ordered = [a for a in sport if is_col(a)] + [a for a in sport if not is_col(a)]

    items = []
    for a in ordered[:12]:
        slug = a.get("slug")
        if not slug:
            continue
        items.append({
            "title": a.get("title") or "Untitled",
            "url": f"/articles/{slug}.html",
            "date": a.get("date") or "",
            "author": a.get("author") or "The Mutapa Times",
            "is_column": is_col(a),
            "card_image": a.get("card_image") or a.get("image") or "",
        })
    with open(os.path.join(OUT_DIR, "editorial.json"), "w", encoding="utf-8") as f:
        json.dump({"items": items, "updated": now}, f, ensure_ascii=False, indent=1)
    print(f"[editorial] {len(items)} items "
          f"({sum(1 for i in items if i['is_column'])} Kundai Kaycee columns)")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    index = []
    for lg in LEAGUES:
        print(f"[{lg['slug']}] via {lg['provider']}")
        # Always list the league in the index (so the hub shows its card even
        # before a source is wired up); the per-league data file may lag.
        entry = {"slug": lg["slug"], "name": lg["name"], "short": lg["short"],
                 "country": lg["country"], "flag": lg.get("flag", ""),
                 "season": "", "capped": False}
        try:
            season, table, results, fixtures, capped = FETCHERS[lg["provider"]](lg)
        except Exception as e:
            print(f"  FAILED: {e} — keeping previous JSON if any")
            index.append(entry)
            continue
        entry["season"] = season
        entry["capped"] = capped
        payload = {
            "slug": lg["slug"], "name": lg["name"], "short": lg["short"],
            "country": lg["country"], "flag": lg.get("flag", ""),
            "season": season, "provider": lg["provider"], "capped": capped,
            "table": table, "results": results, "fixtures": fixtures,
            "updated": now,
        }
        with open(os.path.join(OUT_DIR, f"{lg['slug']}.json"), "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=1)
        print(f"  season {season or '?'}: {len(table)} table rows, "
              f"{len(results)} results, {len(fixtures)} fixtures"
              f"{' (capped)' if capped else ''}")
        index.append(entry)
    with open(os.path.join(OUT_DIR, "index.json"), "w", encoding="utf-8") as f:
        json.dump({"leagues": index, "updated": now}, f, ensure_ascii=False, indent=1)
    print(f"Wrote {len(index)} league file(s) + index.json")
    build_editorial(now)


if __name__ == "__main__":
    main()
