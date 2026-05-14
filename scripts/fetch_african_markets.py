#!/usr/bin/env python3
"""Scrape pan-African stock-market indices from african-markets.com
and write data/markets-indices.json for the /markets page.

The site publishes a single "Stock Markets" summary table with one
row per exchange — index level, day change, YTD change, all
end-of-day. We pull it, normalise the fields, and write a compact
JSON consumed by js/markets.js.

End-of-day data only — no public real-time feed exists for these
exchanges either.
"""
import html as html_mod
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

USER_AGENT = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5) "
              "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6")
URL = "https://www.african-markets.com/en/stock-markets"

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "data", "markets-indices.json")

# The exchanges we care about — every other row gets dropped. Keys
# are the long-form name we expect in the African Markets table,
# values are display labels used by the page.
KEEP_EXCHANGES = {
    "Johannesburg Stock Exchange":     {"label": "JSE All Share",       "ccy": "ZAR", "country": "South Africa"},
    "Nigerian Exchange Group":         {"label": "NGX All-Share",       "ccy": "NGN", "country": "Nigeria"},
    "Egyptian Exchange":               {"label": "EGX 30",              "ccy": "EGP", "country": "Egypt"},
    "Nairobi Securities Exchange":     {"label": "NSE Kenya",           "ccy": "KES", "country": "Kenya"},
    "Casablanca Stock Exchange":       {"label": "MASI",                "ccy": "MAD", "country": "Morocco"},
    "Ghana Stock Exchange":            {"label": "GSE Composite",       "ccy": "GHS", "country": "Ghana"},
    "Botswana Stock Exchange":         {"label": "BSE Domestic",        "ccy": "BWP", "country": "Botswana"},
    "Zimbabwe Stock Exchange":         {"label": "ZSE All Share",       "ccy": "ZWG", "country": "Zimbabwe"},
    "Bourse Régionale des Valeurs Mobilières": {"label": "BRVM Composite", "ccy": "XOF", "country": "West Africa"},
    "Uganda Securities Exchange":      {"label": "USE All Share",       "ccy": "UGX", "country": "Uganda"},
}


def fetch_html(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, urllib.error.HTTPError) as e:
        print(f"  FAIL fetching {url}: {e}")
        return ""


def _clean(s):
    return html_mod.unescape(re.sub(r"<[^>]+>", "", s)).strip()


def parse_markets_summary(body):
    """Parse the African Markets summary table. Returns list of dicts."""
    body = re.sub(r"<script[^>]*>.*?</script>", "", body, flags=re.DOTALL)
    body = re.sub(r"<style[^>]*>.*?</style>", "", body, flags=re.DOTALL)
    tables = re.findall(r"<table[^>]*>(.*?)</table>", body, flags=re.DOTALL)
    out = []
    seen_keys = set()
    for tbl in tables:
        rows = re.findall(r"<tr[^>]*>(.*?)</tr>", tbl, flags=re.DOTALL)
        for r in rows:
            cells = [_clean(c) for c in re.findall(
                r"<t[hd][^>]*>(.*?)</t[hd]>", r, flags=re.DOTALL)]
            if len(cells) < 4 or cells[0].lower() in ("", "exchange", "stock exchange"):
                continue
            name = cells[0]
            match_key = None
            for key in KEEP_EXCHANGES:
                if key.lower() in name.lower():
                    match_key = key
                    break
            if not match_key or match_key in seen_keys:
                continue
            seen_keys.add(match_key)
            meta = KEEP_EXCHANGES[match_key]
            # Typical columns: Name | Index Value | 1D | YTD | Mcap (USD)
            value, day_chg, ytd = "", "", ""
            if len(cells) >= 5:
                value, day_chg, ytd = cells[1], cells[2], cells[3]
            elif len(cells) >= 4:
                value, day_chg, ytd = cells[1], cells[2], cells[3]
            out.append({
                "label": meta["label"],
                "country": meta["country"],
                "ccy": meta["ccy"],
                "value": value,
                "day_change": day_chg,
                "ytd": ytd,
            })
        if out:
            break
    return out


def main():
    print("=== FETCH AFRICAN MARKETS INDICES ===")
    body = fetch_html(URL)
    if not body:
        sys.exit(1)
    rows = parse_markets_summary(body)
    print(f"  Parsed {len(rows)} indices")
    payload = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source": URL,
        "indices": rows,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"  Wrote {OUT}")
    print("=== DONE ===")


if __name__ == "__main__":
    main()
