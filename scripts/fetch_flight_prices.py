#!/usr/bin/env python3
"""Fetch live + cached flight prices per corridor from Travelpayouts Data API.

Strategy: hit multiple endpoints in parallel and aggregate everything we get.
Niche diaspora routes (LON->HRE, NYC->HRE, SYD->HRE) have very thin coverage
on a single endpoint, so we cast a wide net.

Endpoints used:
  /aviasales/v3/prices_for_dates  — current-month real prices, often richest
  /v2/prices/latest               — cached user searches (most recent)
  /v1/prices/calendar             — per-day cheapest, current+next month
  /v1/prices/monthly              — cheapest per month for next 12 months

For each corridor we try the route at both the city code (e.g. LON) and the
busiest airport (LHR). Output combines everything into:
  cheapest_overall  — lowest price found across all endpoints
  cheapest_direct   — lowest direct flight (number_of_changes == 0)
  monthly[]         — 6-12 months of "cheapest per month" data
  by_airline[]      — cheapest by airline (top 5)
  endpoints_tried[] — debug log

Writes to data/flight-prices.json. Safe to run with no token (writes empty
data; build proceeds without callouts).
"""
import calendar, datetime, json, os, sys, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT  = ROOT / "data" / "flight-prices.json"
TOKEN = os.environ.get("TRAVELPAYOUTS_TOKEN", "").strip()
TODAY = datetime.date.today()
DATE_ISO = TODAY.isoformat()

# Each corridor lists (origin_city, origin_airport_alt) so we can try both.
CORRIDORS = {
    "london-to-harare":         {"origin": "LON", "alt": "LHR", "destination": "HRE", "currency": "GBP", "currency_sym": "£"},
    "sydney-to-harare":         {"origin": "SYD", "alt": "SYD", "destination": "HRE", "currency": "AUD", "currency_sym": "A$"},
    "cape-town-to-harare":      {"origin": "CPT", "alt": "CPT", "destination": "HRE", "currency": "ZAR", "currency_sym": "R"},
    "johannesburg-to-harare":   {"origin": "JNB", "alt": "JNB", "destination": "HRE", "currency": "ZAR", "currency_sym": "R"},
    "new-york-to-harare":       {"origin": "NYC", "alt": "JFK", "destination": "HRE", "currency": "USD", "currency_sym": "$"},
    "dubai-to-harare":          {"origin": "DXB", "alt": "DXB", "destination": "HRE", "currency": "AED", "currency_sym": "AED"},
    "toronto-to-harare":        {"origin": "YYZ", "alt": "YYZ", "destination": "HRE", "currency": "CAD", "currency_sym": "C$"},
    "london-to-victoria-falls": {"origin": "LON", "alt": "LHR", "destination": "VFA", "currency": "GBP", "currency_sym": "£"},
}

UA = "MutapaTimes/1.0 (https://mutapatimes.com; news@mutapatimes.com)"


def http_get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "X-Access-Token": TOKEN})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def _safe(url):
    """Call API, return j or {'_error': str}. Never raises."""
    try:
        return http_get_json(url)
    except urllib.error.HTTPError as e:
        return {"_error": f"HTTP {e.code}"}
    except Exception as e:
        return {"_error": str(e)[:120]}


def normalise_observation(o):
    """Normalise the various shapes (v3, v2, v1) into one dict."""
    if not isinstance(o, dict):
        return None
    # v3 prices_for_dates: { price, airline, departure_at, return_at, transfers, duration, ... }
    # v2 prices/latest:    { value, airline, departure_at, return_at, number_of_changes, ... }
    # v1 prices/calendar:  { price, airline, departure_at, ... }
    price = o.get("price", o.get("value"))
    if not isinstance(price, (int, float)) or price <= 0:
        return None
    return {
        "price":    round(float(price)),
        "airline":  o.get("airline") or o.get("gate") or "",
        "departure_at": (o.get("departure_at") or "")[:10],
        "return_at":    (o.get("return_at") or "")[:10],
        "stops":    o.get("number_of_changes", o.get("transfers", None)),
        "duration": o.get("duration"),
        "currency": o.get("currency", ""),
    }


def fetch_v3(origin, destination, currency, period="year"):
    """/aviasales/v3/prices_for_dates — best general endpoint."""
    p = {
        "origin": origin, "destination": destination,
        "currency": currency.lower(),
        "departure_at": "",  # any
        "one_way": "true",
        "direct": "false",
        "market": "uk",
        "limit": "30",
        "sorting": "price",
        "token": TOKEN,
    }
    url = "https://api.travelpayouts.com/aviasales/v3/prices_for_dates?" + urllib.parse.urlencode(p)
    j = _safe(url)
    if "_error" in j: return [], j["_error"]
    return j.get("data", []), None


def fetch_v2(origin, destination, currency):
    """/v2/prices/latest — cached searches, often sparse for niche routes."""
    p = {"origin": origin, "destination": destination, "currency": currency.lower(),
         "limit": "30", "sorting": "price", "show_to_affiliates": "true", "token": TOKEN}
    url = "https://api.travelpayouts.com/v2/prices/latest?" + urllib.parse.urlencode(p)
    j = _safe(url)
    if "_error" in j: return [], j["_error"]
    return j.get("data", []), None


def fetch_monthly(origin, destination, currency):
    """/v1/prices/monthly — cheapest per month for the year ahead."""
    p = {"origin": origin, "destination": destination, "currency": currency.lower(), "token": TOKEN}
    url = "https://api.travelpayouts.com/v1/prices/monthly?" + urllib.parse.urlencode(p)
    j = _safe(url)
    if "_error" in j: return [], j["_error"]
    # Returns {data: {month_str: [observation, ...]}} or {data: {month: observation}}
    data = j.get("data") or {}
    out = []
    if isinstance(data, dict):
        for month, payload in data.items():
            items = payload if isinstance(payload, list) else [payload]
            for it in items:
                if isinstance(it, dict):
                    it["_month"] = month  # YYYY-MM-DD or YYYY-MM
                    out.append(it)
    return out, None


def fetch_calendar(origin, destination, currency):
    """/v1/prices/calendar — cheapest per day, this month + next."""
    p = {"origin": origin, "destination": destination, "currency": currency.lower(),
         "depart_date": TODAY.strftime("%Y-%m"),
         "calendar_type": "departure_date", "length": "30",
         "show_to_affiliates": "true", "token": TOKEN}
    url = "https://api.travelpayouts.com/v1/prices/calendar?" + urllib.parse.urlencode(p)
    j = _safe(url)
    if "_error" in j: return [], j["_error"]
    data = j.get("data") or {}
    out = []
    if isinstance(data, dict):
        for date_str, observation in data.items():
            if isinstance(observation, dict):
                observation["_date"] = date_str
                out.append(observation)
    return out, None


def aggregate(meta):
    """Hit every endpoint, with both origin and alt-airport codes, aggregate."""
    origin, alt, dest, cur = meta["origin"], meta["alt"], meta["destination"], meta["currency"]
    pool, tried = [], []

    for o in dict.fromkeys([origin, alt]):  # dedupe but preserve order
        for fn, name in [(fetch_v3, "v3"), (fetch_monthly, "monthly"),
                         (fetch_calendar, "calendar"), (fetch_v2, "v2")]:
            data, err = fn(o, dest, cur)
            tried.append({"endpoint": name, "origin": o, "n": len(data), "error": err})
            for d in data:
                n = normalise_observation(d)
                if n: pool.append(n)
            if data and not err:
                # Don't keep hammering once we have something useful
                pass

    if not pool:
        return {"endpoints_tried": tried, "observations": 0}

    # Dedup by (price, departure_at, airline)
    seen = set(); deduped = []
    for o in pool:
        k = (o["price"], o["departure_at"], o["airline"])
        if k in seen: continue
        seen.add(k); deduped.append(o)
    pool = deduped

    cheapest = min(pool, key=lambda x: x["price"])
    directs = [o for o in pool if o.get("stops") == 0]
    cheapest_direct = min(directs, key=lambda x: x["price"]) if directs else None

    # Monthly breakdown — cheapest per month going forward
    by_month = {}
    for o in pool:
        dep = o["departure_at"]
        if not dep: continue
        try:
            d = datetime.date.fromisoformat(dep)
        except Exception: continue
        if d < TODAY: continue
        m = d.strftime("%Y-%m")
        if m not in by_month or o["price"] < by_month[m]["price"]:
            by_month[m] = o
    monthly = [by_month[k] for k in sorted(by_month.keys())[:9]]

    # Cheapest per airline (top 5)
    by_airline = {}
    for o in pool:
        a = (o.get("airline") or "").strip()
        if not a: continue
        if a not in by_airline or o["price"] < by_airline[a]["price"]:
            by_airline[a] = o
    by_airline_list = sorted(by_airline.values(), key=lambda x: x["price"])[:5]

    return {
        "cheapest_overall": cheapest,
        "cheapest_direct":  cheapest_direct,
        "monthly":          monthly,
        "by_airline":       by_airline_list,
        "endpoints_tried":  tried,
        "observations":     len(pool),
    }


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

out = {
    "fetched_at": DATE_ISO,
    "source": "Travelpayouts Data API (v3 prices_for_dates, v2 latest, v1 monthly, v1 calendar)",
    "status": "ok" if TOKEN else "no-token",
    "corridors": {},
}

if not TOKEN:
    print("WARN: TRAVELPAYOUTS_TOKEN not set; writing empty data.")
    OUT.write_text(json.dumps(out, indent=2))
    sys.exit(0)

print(f"Fetching {len(CORRIDORS)} corridors across 4 endpoints x 2 origin codes...\n")
for slug, meta in CORRIDORS.items():
    agg = aggregate(meta)
    record = {
        "origin": meta["origin"],
        "destination": meta["destination"],
        "currency": meta["currency"],
        "currency_sym": meta["currency_sym"],
        **agg,
    }
    out["corridors"][slug] = record
    cp = record.get("cheapest_overall")
    if cp:
        airline = cp.get("airline") or "—"
        print(f"  {slug:30s} cheapest {meta['currency_sym']}{cp['price']:,} via {airline:25s} | observations: {record['observations']:3d} | monthly: {len(record.get('monthly',[]))}")
    else:
        # Show which endpoints failed
        errs = ", ".join(f"{t['endpoint']}={t['error'] or '0'}" for t in record["endpoints_tried"][:4])
        print(f"  {slug:30s} no data ({errs})")

OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False))
total_obs = sum(c.get("observations", 0) for c in out["corridors"].values())
print(f"\nwrote {OUT} ({len(out['corridors'])} corridors, {total_obs} total observations)")
