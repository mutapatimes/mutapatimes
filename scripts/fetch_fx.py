#!/usr/bin/env python3
"""Fetch live FX rates from open.er-api.com and save to data/fx-rates.json
for client-side rendering on /fx.html.

Source: open.er-api.com (ECB + national-bank composite, free tier, no
auth, daily refresh). Includes ZWG (Zim Gold) — the current official
Zimbabwe currency — plus all SADC neighbours and major diaspora
currencies. We pull USD-based rates and let the page math cross-rates
client-side from those (one source of truth, no rounding drift).

This is the OFFICIAL interbank composite. Parallel-market rates are a
v2 follow-up — they require a different upstream we can't reach from
this host right now.
"""
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

DATA_DIR = "data"
OUTPUT_FILE = os.path.join(DATA_DIR, "fx-rates.json")
SOURCE_URL = "https://open.er-api.com/v6/latest/USD"
USER_AGENT = "Mozilla/5.0 (compatible; MutapaTimesBot/1.0; +https://www.mutapatimes.com)"

# Currencies we surface on /fx.html — keep narrow so the page stays
# scannable. SADC neighbours + major diaspora corridors + Zim's own ZWG.
# Order matters for display.
DISPLAY_CURRENCIES = [
    # Headline
    "ZWG",  # Zim Gold (current official Zimbabwe currency)
    # SADC / regional
    "ZAR",  # South African rand
    "BWP",  # Botswana pula
    "MZN",  # Mozambican metical
    "ZMW",  # Zambian kwacha
    # Major diaspora corridors
    "GBP",  # UK
    "EUR",  # Eurozone
    "AUD",  # Australia
    "CAD",  # Canada
    "CNY",  # China
    "AED",  # UAE
    # Anchor
    "USD",
]


def fetch_json(url, timeout=20):
    req = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    })
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main():
    print("=== FETCH FX RATES ===")
    print(f"  Source: {SOURCE_URL}")

    try:
        data = fetch_json(SOURCE_URL)
    except urllib.error.HTTPError as e:
        print(f"  HTTP {e.code}: {e.reason}")
        sys.exit(1)
    except Exception as e:
        print(f"  ERROR fetching: {e}")
        sys.exit(1)

    if data.get("result") != "success":
        print(f"  WARN: upstream returned non-success: {data.get('result')!r}")
        sys.exit(1)

    raw_rates = data.get("rates") or {}
    if not raw_rates:
        print("  WARN: empty rates payload — not overwriting existing data")
        sys.exit(1)

    # Subset to the currencies we display. Skip missing keys quietly —
    # the upstream basket shifts occasionally.
    rates = {}
    for code in DISPLAY_CURRENCIES:
        if code in raw_rates:
            rates[code] = float(raw_rates[code])
    if "ZWG" not in rates:
        # Without ZWG the page is useless — fail loud so the workflow
        # leaves the previous good file untouched.
        print("  ERROR: ZWG missing from upstream — refusing to write")
        sys.exit(1)

    output = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source": SOURCE_URL,
        "source_label": "open.er-api.com (official interbank composite)",
        "base": "USD",
        "as_of": data.get("time_last_update_utc", ""),
        "next_update": data.get("time_next_update_utc", ""),
        "rates": rates,
    }

    os.makedirs(DATA_DIR, exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"  ZWG: {rates.get('ZWG'):.4f} per USD")
    print(f"  Wrote {OUTPUT_FILE} ({len(rates)} currencies)")
    print(f"  As of: {output['as_of']}")
    print("\n=== DONE ===")


if __name__ == "__main__":
    main()
