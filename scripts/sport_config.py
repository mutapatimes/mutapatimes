#!/usr/bin/env python3
"""Single source of truth for the /sport section.

The sport section is cross-region (surfaced in every edition's nav) — the same
leagues and the same data/sport/*.json feed both the Zimbabwe root and /za.
Each edition just LEADS with its home league (see regions.py sport_lead).

Adding a league = one entry here. Two providers are supported:
  - "football_data"  → football-data.org (free token). Full current-season table.
  - "thesportsdb"    → TheSportsDB (key 123). Current season, but the FREE key
                       caps the table at the top 5 rows (upgrade to the $9/mo
                       Premium key for full tables + livescores — a secret swap,
                       no code change). Season is auto-detected per league.
"""

LEAGUES = [
    {
        "slug": "premier-league",
        "name": "Premier League",
        "short": "EPL",
        "country": "England",
        "flag": "\U0001F3F4\U000E0067\U000E0062\U000E0065\U000E006E\U000E0067\U000E007F",  # England
        "provider": "football_data",
        "fd_code": "PL",
    },
    {
        "slug": "dstv-premiership",
        "name": "DStv Premiership",
        "short": "PSL · SA",
        "country": "South Africa",
        "flag": "\U0001F1FF\U0001F1E6",
        "provider": "thesportsdb",
        "tsdb_league": "4802",
    },
    {
        "slug": "castle-lager-psl",
        "name": "Castle Lager PSL",
        "short": "PSL · Zim",
        "country": "Zimbabwe",
        "flag": "\U0001F1FF\U0001F1FC",
        "provider": "thesportsdb",
        "tsdb_league": "5261",
    },
]


def league_by_slug(slug):
    for lg in LEAGUES:
        if lg["slug"] == slug:
            return lg
    return None
