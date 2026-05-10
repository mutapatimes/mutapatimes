#!/usr/bin/env python3
"""
One-shot converter: data/gdp-zimbabwe-quarterly.csv -> data/gdp-zimbabwe-quarterly.json
Source: ZimStat. Run locally once when the underlying CSV changes.
"""
import csv
import json
import os

CSV_PATH = "data/gdp-zimbabwe-quarterly.csv"
JSON_PATH = "data/gdp-zimbabwe-quarterly.json"

# ZimStat re-based the series at this quarter (post-ZiG methodology change).
BREAK_QUARTER = "2024 Q1"
BREAK_NOTE = (
    "ZimStat re-based the series in 2024 Q1 following the introduction of "
    "the Zimbabwe Gold (ZiG) currency. Pre-2024 figures use the prior USD "
    "conversion methodology; post-2024 figures are not directly comparable."
)

# Aggregate rows (not individual sectors) — keep separate.
AGGREGATE_ROWS = {
    "GDP at Basic Prices",
    "Taxes on products",
    "Less Subsidies on Products",
    "Net taxes on production",
    "GDP at Market Prices",
}


def main():
    with open(CSV_PATH, encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        quarters = header[1:]

        sectors = {}
        aggregates = {}

        for row in reader:
            name = row[0].strip()
            values = [float(v) for v in row[1:]]
            target = aggregates if name in AGGREGATE_ROWS else sectors
            target[name] = values

    # Sector totals (sum across all quarters) — used to rank sectors by size
    sector_totals = {n: sum(v) for n, v in sectors.items()}
    top_sectors = sorted(sector_totals, key=sector_totals.get, reverse=True)

    output = {
        "source": "National Statistics Agency, Zimbabwe (ZimStat)",
        "currency": "USD",
        "frequency": "Quarterly",
        "quarters": quarters,
        "break_quarter": BREAK_QUARTER,
        "break_index": quarters.index(BREAK_QUARTER) if BREAK_QUARTER in quarters else -1,
        "break_note": BREAK_NOTE,
        "sector_order": top_sectors,
        "sectors": sectors,
        "aggregates": aggregates,
    }

    os.makedirs(os.path.dirname(JSON_PATH), exist_ok=True)
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"Wrote {JSON_PATH}")
    print(f"  {len(sectors)} sectors, {len(aggregates)} aggregates")
    print(f"  {len(quarters)} quarters: {quarters[0]} → {quarters[-1]}")
    print(f"  Break at {BREAK_QUARTER} (index {output['break_index']})")
    print(f"  Top 3 sectors by total: {top_sectors[:3]}")


if __name__ == "__main__":
    main()
