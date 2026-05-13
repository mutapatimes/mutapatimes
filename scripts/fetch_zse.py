#!/usr/bin/env python3
"""Scrape Zimbabwe Stock Exchange daily closes from african-markets.com
and write data/zse-ticker.json for the /economy ticker tape.

Source: african-markets.com publishes daily close prices for every
ZSE-listed company in a clean HTML table — Company / Sector / Price /
1D change / YTD / Market Cap / Date. We pull the table, normalise the
fields, and write the top N by market cap (with the most-popular names
always included) so the ticker reads as a meaningful slice not a wall
of micro-caps.

End-of-day data only — there is no public real-time feed for ZSE.
"""
import html as html_mod
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

URL = "https://www.african-markets.com/en/stock-markets/zse/listed-companies"
USER_AGENT = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5) "
              "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6")

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "data", "zse-ticker.json")

# Names we always want in the ticker even if their mcap is small —
# diaspora reader recognition matters more than market weight here.
ALWAYS_INCLUDE = {
    "Delta Corporation", "Econet Wireless Zimbabwe", "Innscor Africa",
    "FBC Holdings", "CBZ Holdings", "OK Zimbabwe", "Padenga Holdings",
    "Simbisa Brands", "First Mutual Holdings", "Nampak Zimbabwe",
    "RioZim", "Hippo Valley Estates", "British American Tobacco",
    "Old Mutual", "NMB Holdings", "Zimre Holdings", "TSL Limited",
    "Meikles", "ZB Financial Holdings",
}

TICKER_TARGET_COUNT = 18


def fetch_html(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, urllib.error.HTTPError) as e:
        print(f"  FAIL fetching {url}: {e}")
        return ""


def parse_listings_table(body):
    """Return list of dicts with company + sector + price + change + mcap."""
    # Strip scripts/styles so re.findall doesn't pull in noise
    body = re.sub(r"<script[^>]*>.*?</script>", "", body, flags=re.DOTALL)
    body = re.sub(r"<style[^>]*>.*?</style>", "", body, flags=re.DOTALL)
    tables = re.findall(r"<table[^>]*>(.*?)</table>", body, flags=re.DOTALL)
    if not tables:
        return []
    rows = re.findall(r"<tr[^>]*>(.*?)</tr>", tables[0], flags=re.DOTALL)
    out = []
    for r in rows:
        cells = [
            html_mod.unescape(re.sub(r"<[^>]+>", "", c)).strip()
            for c in re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", r, flags=re.DOTALL)
        ]
        # Header row → skip
        if len(cells) < 6 or cells[0].lower() == "company":
            continue
        company, sector, price, day_chg, ytd, mcap = cells[:6]
        out.append({
            "company": company,
            "sector": sector,
            "price": price,
            "day_change": day_chg.replace(" ", "").strip("- "),
            "ytd": ytd,
            "mcap_b": _mcap_to_float(mcap),
        })
    return out


def _mcap_to_float(s):
    """Strip non-numeric chars and return a float; useful for sorting."""
    try:
        return float(re.sub(r"[^\d.]", "", s))
    except (ValueError, TypeError):
        return 0.0


def shortlist(rows):
    """Pick ~18 tickers: always-include set first, then largest by mcap."""
    by_name = {r["company"]: r for r in rows}
    picks = []
    seen = set()
    for name in ALWAYS_INCLUDE:
        for cname, row in by_name.items():
            if name.lower() in cname.lower() and cname not in seen:
                picks.append(row)
                seen.add(cname)
                break
    # Fill remainder with largest-mcap names not already picked
    rest = sorted([r for r in rows if r["company"] not in seen],
                  key=lambda r: r["mcap_b"], reverse=True)
    for row in rest:
        if len(picks) >= TICKER_TARGET_COUNT:
            break
        picks.append(row)
        seen.add(row["company"])
    return picks


def main():
    print("=== FETCH ZSE TICKER ===")
    body = fetch_html(URL)
    if not body:
        sys.exit(1)
    rows = parse_listings_table(body)
    print(f"  Parsed {len(rows)} companies from listings table")
    picks = shortlist(rows)
    print(f"  Shortlist for ticker: {len(picks)} names")
    payload = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source": URL,
        "exchange": "ZSE",
        "currency": "ZWG",
        "tickers": picks,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"  Wrote {OUT}")
    print("=== DONE ===")


if __name__ == "__main__":
    main()
