#!/usr/bin/env python3
"""Fetch cheapest cached fares per corridor from Travelpayouts Data API.

Output: data/flight-prices.json
Reads:  env var TRAVELPAYOUTS_TOKEN (set in GitHub Actions secrets)

Endpoint reference: https://support.travelpayouts.com/hc/en-us/articles/203956163
  /v2/prices/latest  — most recently observed cheapest fares per route.
  /v1/prices/cheap   — alternative with monthly breakdown (we fall back to this).

The script is best-effort — if the token is missing or the API errors,
it writes a minimal JSON with status info and exits 0 so the workflow
keeps going. The build script gracefully skips price callouts when the
file is empty or stale.
"""
import datetime, json, os, sys, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT  = ROOT / "data" / "flight-prices.json"
TOKEN = os.environ.get("TRAVELPAYOUTS_TOKEN", "").strip()
TODAY = datetime.date.today().isoformat()

# Map our corridor slugs → IATA origin/destination + the display currency
# we want fares quoted in (matches each page's widget currency).
CORRIDORS = {
    "london-to-harare":         {"origin": "LON", "destination": "HRE", "currency": "GBP", "currency_sym": "£"},
    "sydney-to-harare":         {"origin": "SYD", "destination": "HRE", "currency": "AUD", "currency_sym": "A$"},
    "cape-town-to-harare":      {"origin": "CPT", "destination": "HRE", "currency": "ZAR", "currency_sym": "R"},
    "johannesburg-to-harare":   {"origin": "JNB", "destination": "HRE", "currency": "ZAR", "currency_sym": "R"},
    "new-york-to-harare":       {"origin": "NYC", "destination": "HRE", "currency": "USD", "currency_sym": "$"},
    "dubai-to-harare":          {"origin": "DXB", "destination": "HRE", "currency": "AED", "currency_sym": "AED"},
    "toronto-to-harare":        {"origin": "YYZ", "destination": "HRE", "currency": "CAD", "currency_sym": "C$"},
    "london-to-victoria-falls": {"origin": "LON", "destination": "VFA", "currency": "GBP", "currency_sym": "£"},
}

UA = "MutapaTimes/1.0 (https://www.mutapatimes.com; news@mutapatimes.com)"

def http_get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "X-Access-Token": TOKEN})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)

def fetch_latest(origin, destination, currency):
    """Pull cheapest cached return fares for this route.

    /v2/prices/latest returns 'data' as a list of price observations with
    fields: value (price), airline, departure_at, return_at,
    number_of_changes, trip_class, expires_at."""
    params = {
        "currency": currency.lower(),
        "origin": origin,
        "destination": destination,
        "limit": "30",
        "sorting": "price",
        "trip_class": "0",  # 0 = economy
        "show_to_affiliates": "true",
        "token": TOKEN,
    }
    url = "https://api.travelpayouts.com/v2/prices/latest?" + urllib.parse.urlencode(params)
    try:
        j = http_get_json(url)
    except Exception as e:
        return {"error": str(e), "data": []}
    return j

def summarise(observations):
    """Take the API's list of observations and compute headline numbers."""
    if not observations:
        return None
    # Cheapest overall
    cheapest = min(observations, key=lambda x: x.get("value", 1e9))
    # Cheapest direct (number_of_changes == 0)
    directs = [o for o in observations if o.get("number_of_changes") == 0]
    cheapest_direct = min(directs, key=lambda x: x.get("value", 1e9)) if directs else None
    # Lowest in next 30 days
    today = datetime.date.today()
    soon = []
    for o in observations:
        dep = (o.get("departure_at") or "")[:10]
        try:
            d = datetime.date.fromisoformat(dep)
            if 0 <= (d - today).days <= 30:
                soon.append(o)
        except Exception:
            pass
    cheapest_soon = min(soon, key=lambda x: x.get("value", 1e9)) if soon else None
    return {
        "cheapest":        cheapest,
        "cheapest_direct": cheapest_direct,
        "cheapest_30d":    cheapest_soon,
        "n_observations":  len(observations),
    }

# Always write the same file shape so the build script can rely on it
out = {
    "fetched_at": TODAY,
    "source": "Travelpayouts Data API (/v2/prices/latest)",
    "status": "ok" if TOKEN else "no-token",
    "corridors": {},
}

if not TOKEN:
    print("WARN: TRAVELPAYOUTS_TOKEN not set; writing empty data file.")
    OUT.write_text(json.dumps(out, indent=2))
    sys.exit(0)

print(f"Fetching {len(CORRIDORS)} corridors…")
for slug, meta in CORRIDORS.items():
    print(f"  {slug:30s} {meta['origin']} -> {meta['destination']}", end=" ")
    j = fetch_latest(meta["origin"], meta["destination"], meta["currency"])
    if j.get("error"):
        print(f"  ERROR: {j['error']}")
        out["corridors"][slug] = {"error": j["error"]}
        continue
    observations = j.get("data") or []
    summary = summarise(observations) or {}
    out["corridors"][slug] = {
        "origin": meta["origin"],
        "destination": meta["destination"],
        "currency": meta["currency"],
        "currency_sym": meta["currency_sym"],
        **summary,
    }
    cp = summary.get("cheapest") if summary else None
    if cp:
        print(f"  cheapest {meta['currency_sym']}{cp.get('value')} via {cp.get('airline')}")
    else:
        print("  no observations")

OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False))
print(f"\nwrote {OUT} ({len(out['corridors'])} corridors)")
