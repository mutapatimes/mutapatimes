#!/usr/bin/env python3
"""
One-shot converter: data/zimstat-bop-quarterly.csv -> data/zimstat-bop-quarterly.json

Source: ZimStat / RBZ Balance of Payments (public domain). Run locally once
when the underlying CSV changes.

The raw CSV mixes annual columns (2009-2025) with quarterly columns
(2017 Q1 onwards). The page only consumes the quarterly series, so we
split them out and key each row by a stable semantic name (e.g.
"exports_goods") because the raw "INDICATOR" column reuses labels
("Exports", "Imports") at different nesting levels.
"""
import csv
import json
import os
import re
from datetime import datetime, timezone

CSV_PATH = "data/zimstat-bop-quarterly.csv"
JSON_PATH = "data/zimstat-bop-quarterly.json"

# Pin rows by 1-based line number in the CSV (the file's row order is stable
# in every ZimStat BoP release). Each entry: line → (key, label, blurb).
ROWS = {
    2:  ("current_account",          "Current Account",
         "Net balance of trade + income + transfers with the rest of the world."),
    4:  ("exports_total",            "Total Exports (Goods + Services)",
         "Everything Zimbabwe sold to the rest of the world."),
    5:  ("imports_total",            "Total Imports (Goods + Services)",
         "Everything Zimbabwe bought from the rest of the world."),
    6:  ("balance_goods",            "Balance on Goods",
         "Exports of goods minus imports of goods. Negative = trade deficit."),
    7:  ("exports_goods",            "Exports of Goods",
         "Minerals, tobacco, horticulture, manufactures."),
    8:  ("imports_goods",            "Imports of Goods",
         "Fuel, machinery, food, vehicles."),
    9:  ("balance_services",         "Balance on Services",
         "Transport, travel, financial, ICT services trade."),
    10: ("exports_services",         "Exports of Services",
         "Tourism, transport, business services sold abroad."),
    11: ("imports_services",         "Imports of Services",
         "Foreign services purchased — freight, royalties, consulting."),
    12: ("balance_primary_income",   "Balance on Primary Income",
         "Net dividends, interest, and compensation flows."),
    16: ("balance_secondary_income", "Balance on Secondary Income",
         "Net transfers including remittances and NGO inflows."),
    24: ("personal_transfers",       "Personal Transfers (Remittances)",
         "Money sent home by Zimbabweans living abroad."),
    35: ("net_lending_borrowing",    "Net Lending / Borrowing",
         "Overall balance — net flow of capital into or out of Zimbabwe."),
    61: ("net_errors_omissions",     "Net Errors & Omissions",
         "The unrecorded gap — a proxy for informal economic activity."),
}

QUARTER_RE = re.compile(r"^(\d{4}) Q([1-4])$")
YEAR_RE = re.compile(r"^(\d{4})$")


def parse_number(s):
    s = (s or "").strip()
    if not s or s == "—":
        return None
    try:
        return float(s)
    except ValueError:
        return None


def main():
    with open(CSV_PATH, encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        rows = list(reader)

    header = rows[0]
    # Header columns 0,1,2 are INDICATOR, Units, Scale. Real series start at 3.
    quarter_cols = []
    annual_cols = []
    for idx, name in enumerate(header[3:], start=3):
        name = name.strip()
        if QUARTER_RE.match(name):
            quarter_cols.append((idx, name))
        elif YEAR_RE.match(name):
            annual_cols.append((idx, name))

    quarters = [name for _, name in quarter_cols]
    years = [name for _, name in annual_cols]

    indicators = {}
    for line_no, (key, label, blurb) in ROWS.items():
        if line_no - 1 >= len(rows):
            print(f"  WARN: row {line_no} not in CSV — skipping {key}")
            continue
        row = rows[line_no - 1]
        if not row:
            continue
        # Sanity check the label against the CSV — the rest of the page
        # depends on us picking the right rows.
        raw_label = (row[0] or "").strip()
        scale = (row[2] or "").strip() if len(row) > 2 else ""
        annual = {y: parse_number(row[i]) for i, y in annual_cols if i < len(row)}
        quarterly = {q: parse_number(row[i]) for i, q in quarter_cols if i < len(row)}
        indicators[key] = {
            "label": label,
            "blurb": blurb,
            "raw_label": raw_label,
            "scale": scale,
            "annual": annual,
            "quarterly": quarterly,
        }

    # Convenience: quarterly-aligned arrays per indicator, in the same order
    # as `quarters`, so the front-end can index in lockstep without dict
    # gymnastics.
    series = {}
    for key, payload in indicators.items():
        series[key] = [payload["quarterly"].get(q) for q in quarters]

    # ── Provisional-zero scrubbing ────────────────────────────────
    # ZimStat ships some balance-sheet residuals (NE&O, net lending/
    # borrowing) with a literal 0.0 placeholder for the latest quarter
    # before the figure is finalised. A real zero is statistically
    # implausible for these indicators, so we treat trailing zeros as
    # null on read — front-end then skips the point instead of plotting
    # a misleading "$0".
    PROVISIONAL_KEYS = {"net_errors_omissions", "net_lending_borrowing"}
    for key in PROVISIONAL_KEYS:
        if key not in series:
            continue
        arr = series[key]
        for i in range(len(arr) - 1, -1, -1):
            if arr[i] == 0.0:
                arr[i] = None
                # Mirror in the indicator's quarterly dict too
                indicators[key]["quarterly"][quarters[i]] = None
            else:
                break

    output = {
        "source": "ZimStat / Reserve Bank of Zimbabwe — Balance of Payments",
        "currency": "USD",
        "scale": "millions",
        "frequency": "Quarterly",
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "quarters": quarters,
        "years": years,
        "indicators": indicators,   # full {annual, quarterly} per indicator
        "series": series,           # quarterly arrays aligned to `quarters`
    }

    os.makedirs(os.path.dirname(JSON_PATH), exist_ok=True)
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"Wrote {JSON_PATH}")
    print(f"  {len(indicators)} indicators")
    print(f"  {len(quarters)} quarters: {quarters[0]} → {quarters[-1]}")
    print(f"  {len(years)} annual readings: {years[0]} → {years[-1]}")
    # Quick sanity print
    latest_q = quarters[-1]
    ca = indicators["current_account"]["quarterly"].get(latest_q)
    pt = indicators["personal_transfers"]["quarterly"].get(latest_q)
    print(f"  {latest_q} Current Account: {ca}")
    print(f"  {latest_q} Personal Transfers: {pt}")


if __name__ == "__main__":
    main()
