#!/usr/bin/env python3
"""Shared chapter library for the daily economy card + economy-feed.xml.

THIRTY-ONE distinct factual angles on the ZimStat GDP + RBZ Balance of
Payments data. Indexed by day-of-year (% N) so no stat repeats within
any 30-day window — even when ZimStat does not refresh the data for
months at a time.

Every chapter returns a single dict with two groups of fields:

  Card layout fields:
    eyebrow, headline, big_num, big_lbl, sub, bars, bar_unit, bg, footer_src

  RSS feed fields:
    rss_title, rss_desc

The card script renders the layout fields into a 1080×1350 PNG; the
RSS script writes rss_title + rss_desc into economy-feed.xml. Both
consumers call `pick_chapter_for_today()` to get the same chapter
on the same CAT day.
"""
import json
import os
from datetime import datetime, timezone, timedelta


ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
GDP_FILE = os.path.join(ROOT, "data", "gdp-zimbabwe-quarterly.json")
BOP_FILE = os.path.join(ROOT, "data", "zimstat-bop-quarterly.json")

# Brand palette — exposed so the card script can pass these through
CARD_BG_BUTTER = (245, 232, 200)
CARD_BG_SAGE = (216, 230, 213)
CARD_BG_ROSE = (242, 218, 213)
CARD_BG_CREAM = (236, 226, 207)


# ── Helpers ──────────────────────────────────────────────────
def load_data():
    """Return (gdp_dict, bop_dict). Both files are kept in the repo
    so this never hits the network."""
    with open(GDP_FILE) as f:
        gdp = json.load(f)
    with open(BOP_FILE) as f:
        bop = json.load(f)
    return gdp, bop


def fmt_money_compact(n):
    if n is None:
        return "—"
    abs_v = abs(n)
    sign = "−" if n < 0 else ""
    if abs_v >= 1e9: return f"{sign}${abs_v / 1e9:.1f}B"
    if abs_v >= 1e6: return f"{sign}${abs_v / 1e6:.0f}M"
    if abs_v >= 1e3: return f"{sign}${abs_v / 1e3:.0f}K"
    return f"{sign}${abs_v:,.0f}"


def fmt_bop(n_millions):
    if n_millions is None:
        return "—"
    return fmt_money_compact(n_millions * 1e6)


def fmt_pct(n, signed=True):
    if n is None:
        return "—"
    sign = "+" if (signed and n >= 0) else ("−" if signed and n < 0 else "")
    return f"{sign}{abs(n):.1f}%"


SHORT_SECTOR = {
    "Wholesale and retail trade; repair of motor vehicles and motorcycles": "Wholesale & retail",
    "Public administration and defence; compulsory social security": "Public admin & defence",
    "Water supply; sewerage, waste management and remediation activities": "Water & waste",
    "Electricity, gas, steam and air conditioning supply": "Electricity & gas",
    "Agiculture, Hunting and Fishing and forestry": "Agriculture",
    "Professional, scientific and technical activities": "Professional services",
    "Administrative and support service activities": "Admin & support",
    "Human health and social work activities": "Health & social work",
    "Arts, entertainment and recreation": "Arts & entertainment",
    "Accommodation and food service activities": "Hospitality",
    "Information and communication": "ICT",
    "Financial and insurance activities": "Finance & insurance",
    "Transportation and storage": "Transport & storage",
    "Mining and quarrying": "Mining",
    "Manufacturing": "Manufacturing",
    "Construction": "Construction",
    "Real estate activities": "Real estate",
    "Education": "Education",
    "Other service activities": "Other services",
    "Activities of Households as Employers Producing Activities of Households for own use": "Household employers",
}


def short(name):
    return SHORT_SECTOR.get(name, name)


def latest_q(gdp):
    """Convenience: (idx, quarter_name) for the latest GDP quarter."""
    last = len(gdp["quarters"]) - 1
    return last, gdp["quarters"][last]


def bop_latest_q(bop):
    last = len(bop["quarters"]) - 1
    return last, bop["quarters"][last]


def bop_latest_nonzero(bop, key):
    """For provisional-prone indicators (net_errors_omissions,
    net_lending_borrowing), walk back to the latest quarter with a
    real (non-null, non-zero) reading."""
    series = bop["series"][key]
    quarters = bop["quarters"]
    for i in range(len(series) - 1, -1, -1):
        if series[i] not in (None, 0, 0.0):
            return i, series[i], quarters[i]
    return len(series) - 1, series[-1], quarters[-1]


def sector_val(gdp, name, idx):
    return gdp["sectors"][name][idx] if name in gdp["sectors"] else None


def gdp_total(gdp, idx):
    return gdp["aggregates"]["GDP at Market Prices"][idx]


def sum_recent_quarters(series, n, count=4):
    """Sum the last `count` quarters of a series, treating None as 0
    but counting actual contributors."""
    total = 0.0
    contrib = 0
    for i in range(max(0, n - count), n):
        v = series[i]
        if v is not None:
            total += v
            contrib += 1
    return total, contrib


def yoy_pct(series, idx):
    """Percentage change vs 4 quarters ago. Returns None if unknown."""
    if idx - 4 < 0:
        return None
    ago = series[idx - 4]
    now = series[idx]
    if ago is None or ago == 0 or now is None:
        return None
    return ((now - ago) / ago) * 100


def cumulative_pct(series, idx, back_quarters):
    """Percentage change vs `back_quarters` ago."""
    j = idx - back_quarters
    if j < 0:
        return None
    ago = series[j]
    now = series[idx]
    if ago is None or ago == 0 or now is None:
        return None
    return ((now - ago) / ago) * 100


# ── CHAPTER BUILDERS ─────────────────────────────────────────
# Each returns a dict with the standard fields. Builders are pure
# functions of (gdp, bop). Order in CHAPTERS list determines rotation
# index — keep stable so a given day-of-year maps to a stable angle.


def ch_top_sector(gdp, bop):
    last, q = latest_q(gdp)
    total = gdp_total(gdp, last)
    pairs = sorted(
        [(n, gdp["sectors"][n][last]) for n in gdp["sector_order"]],
        key=lambda p: p[1], reverse=True)
    top_name, top_val = pairs[0]
    share = (top_val / total) * 100 if total else 0
    second_name, _ = pairs[1]
    third_name, _ = pairs[2]
    bars = [(short(n), v, n == top_name) for n, v in pairs[:5]]
    return {
        "key": "top_sector",
        "eyebrow": "LARGEST SECTOR",
        "headline": "Where the money lives.",
        "big_num": fmt_money_compact(top_val),
        "big_lbl": short(top_name),
        "sub": f"The largest contributor to GDP in {q} — {share:.1f}% of all output. "
               f"{short(second_name)} and {short(third_name)} follow.",
        "bars": bars,
        "bar_unit": "USD, latest quarter",
        "bg": CARD_BG_BUTTER,
        "footer_src": "Source: ZimStat, Quarterly GDP Tables.",
        "rss_title": f"Zim economy {q}: {short(top_name)} is the largest sector at "
                     f"{fmt_money_compact(top_val)} ({share:.1f}% of GDP).",
        "rss_desc": f"In {q}, {short(top_name)} contributed {fmt_money_compact(top_val)} "
                    f"to Zimbabwe GDP — {share:.1f}% of total output. {short(second_name)} "
                    f"and {short(third_name)} round out the top three. "
                    f"Full briefing: mutapatimes.com/economy",
    }


def ch_fastest_growing(gdp, bop):
    last, q = latest_q(gdp)
    movers = []
    for n in gdp["sector_order"]:
        v = yoy_pct(gdp["sectors"][n], last)
        if v is not None:
            movers.append((n, v, gdp["sectors"][n][last]))
    movers.sort(key=lambda x: x[1], reverse=True)
    top_name, top_pct, top_val = movers[0]
    bars = [(short(n), pct, n == top_name) for n, pct, _ in movers[:5]]
    return {
        "key": "fastest_growing",
        "eyebrow": "FASTEST GROWING SECTOR",
        "headline": "Where the growth is.",
        "big_num": fmt_pct(top_pct),
        "big_lbl": f"{short(top_name)} YoY",
        "sub": f"Strongest year-on-year growth across 20 tracked sectors in {q}. "
               f"Driven by post-2024 base effects after the ZiG currency rebase.",
        "bars": bars,
        "bar_unit": "YoY %, top 5",
        "bg": CARD_BG_SAGE,
        "footer_src": "Source: ZimStat, Quarterly GDP Tables.",
        "rss_title": f"Zim economy {q}: {short(top_name)} is the fastest-growing sector "
                     f"at {fmt_pct(top_pct)} YoY.",
        "rss_desc": f"Of 20 tracked ZimStat sectors, {short(top_name)} led growth in {q} "
                    f"with a {fmt_pct(top_pct)} year-on-year change. "
                    f"Full sector ranking: mutapatimes.com/economy",
    }


def ch_fastest_declining(gdp, bop):
    last, q = latest_q(gdp)
    movers = []
    for n in gdp["sector_order"]:
        v = yoy_pct(gdp["sectors"][n], last)
        if v is not None:
            movers.append((n, v))
    movers.sort(key=lambda x: x[1])  # ascending → bottom first
    bottom_name, bottom_pct = movers[0]
    bars = [(short(n), pct, n == bottom_name) for n, pct in movers[:5]]
    return {
        "key": "fastest_declining",
        "eyebrow": "STEEPEST DECLINE",
        "headline": "Where the contraction is.",
        "big_num": fmt_pct(bottom_pct),
        "big_lbl": f"{short(bottom_name)} YoY",
        "sub": f"Largest year-on-year contraction across all tracked sectors in {q}. "
               f"Post-2024 rebase changes the basis of comparison — read with caution.",
        "bars": bars,
        "bar_unit": "YoY %, bottom 5",
        "bg": CARD_BG_ROSE,
        "footer_src": "Source: ZimStat, Quarterly GDP Tables.",
        "rss_title": f"Zim economy {q}: {short(bottom_name)} is the steepest-declining "
                     f"sector at {fmt_pct(bottom_pct)} YoY.",
        "rss_desc": f"{short(bottom_name)} contracted {fmt_pct(bottom_pct)} year-on-year "
                    f"in {q} — the largest decline among 20 tracked sectors. "
                    f"Full chart: mutapatimes.com/economy",
    }


def ch_mining_vs_agri(gdp, bop):
    last, q = latest_q(gdp)
    mining = sector_val(gdp, "Mining and quarrying", last)
    agri = sector_val(gdp, "Agiculture, Hunting and Fishing and forestry", last)
    diff = (mining or 0) - (agri or 0)
    leader = "Mining" if mining > agri else "Agriculture"
    bars = [
        ("Mining", mining, leader == "Mining"),
        ("Agriculture", agri, leader == "Agriculture"),
    ]
    return {
        "key": "mining_vs_agri",
        "eyebrow": "TWO GREAT SECTORS",
        "headline": "Mining vs agriculture.",
        "big_num": fmt_money_compact(abs(diff)),
        "big_lbl": f"{leader} leads",
        "sub": f"In {q}, mining produced {fmt_money_compact(mining)} and agriculture "
               f"{fmt_money_compact(agri)}. Lithium and gold have rerated mining "
               f"since 2022.",
        "bars": bars,
        "bar_unit": "USD, latest quarter",
        "bg": CARD_BG_BUTTER,
        "footer_src": "Source: ZimStat, Quarterly GDP Tables.",
        "rss_title": f"Zim economy {q}: {leader} leads agriculture by "
                     f"{fmt_money_compact(abs(diff))}. Mining {fmt_money_compact(mining)}, "
                     f"agri {fmt_money_compact(agri)}.",
        "rss_desc": f"Mining {fmt_money_compact(mining)} versus agriculture "
                    f"{fmt_money_compact(agri)} in {q}. Lithium has driven mining sharply "
                    f"since 2022. Full briefing: mutapatimes.com/economy",
    }


def ch_mining_vs_mfg(gdp, bop):
    last, q = latest_q(gdp)
    mining = sector_val(gdp, "Mining and quarrying", last)
    mfg = sector_val(gdp, "Manufacturing", last)
    diff = (mining or 0) - (mfg or 0)
    leader = "Mining" if mining > mfg else "Manufacturing"
    bars = [
        ("Mining", mining, leader == "Mining"),
        ("Manufacturing", mfg, leader == "Manufacturing"),
    ]
    return {
        "key": "mining_vs_mfg",
        "eyebrow": "EXTRACTIVE VS INDUSTRIAL",
        "headline": "Mining vs manufacturing.",
        "big_num": fmt_money_compact(abs(diff)),
        "big_lbl": f"{leader} leads",
        "sub": f"In {q}, mining contributed {fmt_money_compact(mining)} and manufacturing "
               f"{fmt_money_compact(mfg)}. Mining has rerated on lithium and gold; "
               f"manufacturing remains constrained by power and capital.",
        "bars": bars,
        "bar_unit": "USD, latest quarter",
        "bg": CARD_BG_CREAM,
        "footer_src": "Source: ZimStat, Quarterly GDP Tables.",
        "rss_title": f"Zim economy {q}: {leader} leads on extractive vs industrial — "
                     f"mining {fmt_money_compact(mining)}, manufacturing "
                     f"{fmt_money_compact(mfg)}.",
        "rss_desc": f"Mining produced {fmt_money_compact(mining)} and manufacturing "
                    f"{fmt_money_compact(mfg)} in {q}. The economy is rebalancing toward "
                    f"extractives. Full briefing: mutapatimes.com/economy",
    }


def _post_rebase_anchor(gdp):
    """Return (idx, quarter_name) for the first post-rebase quarter
    (2024 Q1) — the earliest period that is methodologically comparable
    with the latest. Falls back to start of series if break_index is
    absent."""
    b = gdp.get("break_index", 0) or 0
    return b, gdp["quarters"][b]


def ch_lithium_boom(gdp, bop):
    """Mining since the post-2024 rebase — the lithium-era story.
    Pre-rebase quarters are NOT methodologically comparable, so we
    anchor to the first post-rebase quarter (2024 Q1)."""
    last, q = latest_q(gdp)
    mining = sector_val(gdp, "Mining and quarrying", last)
    ago_idx, ago_q = _post_rebase_anchor(gdp)
    ago_val = sector_val(gdp, "Mining and quarrying", ago_idx)
    pct = ((mining - ago_val) / ago_val) * 100 if ago_val else 0
    bars = [(ago_q, ago_val, False), (q, mining, True)]
    return {
        "key": "lithium_boom",
        "eyebrow": "THE LITHIUM ERA",
        "headline": "Mining since the rebase.",
        "big_num": fmt_pct(pct),
        "big_lbl": f"mining since {ago_q}",
        "sub": f"Mining produced {fmt_money_compact(ago_val)} in {ago_q} (the first "
               f"quarter after ZimStat's methodology rebase) and {fmt_money_compact(mining)} "
               f"in {q}. Zimbabwe is now a top-five global lithium producer.",
        "bars": bars,
        "bar_unit": "USD, mining quarterly",
        "bg": CARD_BG_BUTTER,
        "footer_src": "Source: ZimStat, Quarterly GDP — Mining & Quarrying (post-2024 series).",
        "rss_title": f"Zim mining sector has moved {fmt_pct(pct)} since the 2024 "
                     f"rebase quarter — now {fmt_money_compact(mining)} per quarter.",
        "rss_desc": f"Mining produced {fmt_money_compact(ago_val)} in {ago_q} (first "
                    f"post-rebase quarter) and now {fmt_money_compact(mining)} in {q}. "
                    f"Zimbabwe is now a top-five global lithium producer. "
                    f"Full briefing: mutapatimes.com/economy",
    }


def ch_manufacturing_trend(gdp, bop):
    """Manufacturing since the post-2024 rebase."""
    last, q = latest_q(gdp)
    mfg = sector_val(gdp, "Manufacturing", last)
    ago_idx, ago_q = _post_rebase_anchor(gdp)
    ago = sector_val(gdp, "Manufacturing", ago_idx)
    pct = ((mfg - ago) / ago) * 100 if ago else 0
    bars = [(ago_q, ago, False), (q, mfg, True)]
    return {
        "key": "manufacturing_trend",
        "eyebrow": "INDUSTRIAL BASE",
        "headline": "Manufacturing since the rebase.",
        "big_num": fmt_pct(pct),
        "big_lbl": f"manufacturing since {ago_q}",
        "sub": f"Manufacturing was {fmt_money_compact(ago)} in {ago_q} and is now "
               f"{fmt_money_compact(mfg)}. Plant utilisation has been a structural "
               f"problem since dollarisation.",
        "bars": bars,
        "bar_unit": "USD, manufacturing quarterly",
        "bg": CARD_BG_ROSE,
        "footer_src": "Source: ZimStat, Quarterly GDP — Manufacturing (post-2024 series).",
        "rss_title": f"Zim manufacturing has moved {fmt_pct(pct)} since the 2024 "
                     f"rebase — now {fmt_money_compact(mfg)} per quarter.",
        "rss_desc": f"Manufacturing output was {fmt_money_compact(ago)} in {ago_q}, "
                    f"now {fmt_money_compact(mfg)}. The industrial base has not kept pace. "
                    f"Full chart: mutapatimes.com/economy",
    }


def ch_wholesale_retail(gdp, bop):
    last, q = latest_q(gdp)
    name = "Wholesale and retail trade; repair of motor vehicles and motorcycles"
    val = sector_val(gdp, name, last)
    total = gdp_total(gdp, last)
    share = (val / total) * 100 if total else 0
    bars = [(short(name), val, True)]
    # add top 4 other sectors for comparison context
    others = [(n, gdp["sectors"][n][last]) for n in gdp["sector_order"]
              if n != name]
    others.sort(key=lambda x: x[1], reverse=True)
    for n, v in others[:4]:
        bars.append((short(n), v, False))
    return {
        "key": "wholesale_retail",
        "eyebrow": "INFORMAL ECONOMY",
        "headline": "The trader economy.",
        "big_num": fmt_money_compact(val),
        "big_lbl": "wholesale & retail",
        "sub": f"Wholesale and retail trade — spaza shops, market stalls, distributors — "
               f"produced {fmt_money_compact(val)} in {q}, {share:.1f}% of GDP. "
               f"Largely informal.",
        "bars": bars,
        "bar_unit": "USD, latest quarter",
        "bg": CARD_BG_BUTTER,
        "footer_src": "Source: ZimStat, Quarterly GDP — Wholesale & Retail Trade.",
        "rss_title": f"Zim economy {q}: wholesale & retail trade produced "
                     f"{fmt_money_compact(val)}, {share:.1f}% of GDP.",
        "rss_desc": f"The trader economy — spaza shops, market stalls, distributors — "
                    f"contributed {fmt_money_compact(val)} in {q}, or {share:.1f}% of "
                    f"GDP. Full briefing: mutapatimes.com/economy",
    }


def ch_ict_rise(gdp, bop):
    """ICT in the latest quarter with a YoY comparison (post-rebase
    only so the percentage is methodologically clean)."""
    last, q = latest_q(gdp)
    val = sector_val(gdp, "Information and communication", last)
    total = gdp_total(gdp, last)
    share = (val / total) * 100 if total else 0
    yoy = yoy_pct(gdp["sectors"]["Information and communication"], last)
    bars = [
        ("ICT", val, True),
        ("Finance & insurance", sector_val(gdp, "Financial and insurance activities", last), False),
        ("Wholesale & retail", sector_val(gdp, "Wholesale and retail trade; repair of motor vehicles and motorcycles", last), False),
    ]
    return {
        "key": "ict_rise",
        "eyebrow": "ICT SECTOR",
        "headline": "Digital Zimbabwe.",
        "big_num": fmt_money_compact(val),
        "big_lbl": "ICT this quarter",
        "sub": f"Information and communication produced {fmt_money_compact(val)} in {q} "
               f"({share:.1f}% of GDP). YoY change: {fmt_pct(yoy)}. Mobile money and "
               f"fibre buildout drive growth.",
        "bars": bars,
        "bar_unit": "USD, latest quarter",
        "bg": CARD_BG_SAGE,
        "footer_src": "Source: ZimStat, Quarterly GDP — Information & Communication.",
        "rss_title": f"Zim ICT sector: {fmt_money_compact(val)} in {q}, "
                     f"{share:.1f}% of GDP, {fmt_pct(yoy)} YoY.",
        "rss_desc": f"Information and communication contributed {fmt_money_compact(val)} "
                    f"in {q} — {share:.1f}% of GDP, {fmt_pct(yoy)} year-on-year. "
                    f"Mobile money and fibre drive the trend. "
                    f"Full briefing: mutapatimes.com/economy",
    }


def ch_finance(gdp, bop):
    last, q = latest_q(gdp)
    val = sector_val(gdp, "Financial and insurance activities", last)
    total = gdp_total(gdp, last)
    share = (val / total) * 100 if total else 0
    bars = [(short("Financial and insurance activities"), val, True)]
    top_others = [(n, gdp["sectors"][n][last]) for n in gdp["sector_order"]
                  if n != "Financial and insurance activities"]
    top_others.sort(key=lambda x: x[1], reverse=True)
    for n, v in top_others[:4]:
        bars.append((short(n), v, False))
    return {
        "key": "finance",
        "eyebrow": "FINANCE & INSURANCE",
        "headline": "The banking sector, sized.",
        "big_num": fmt_money_compact(val),
        "big_lbl": "finance & insurance",
        "sub": f"Banks, insurance and asset managers produced {fmt_money_compact(val)} "
               f"in {q} — {share:.1f}% of GDP. Among the most resilient sectors through "
               f"currency reform.",
        "bars": bars,
        "bar_unit": "USD, latest quarter",
        "bg": CARD_BG_CREAM,
        "footer_src": "Source: ZimStat, Quarterly GDP — Financial & Insurance.",
        "rss_title": f"Zim finance & insurance sector produced {fmt_money_compact(val)} "
                     f"in {q} — {share:.1f}% of GDP.",
        "rss_desc": f"Banking, insurance and asset management contributed "
                    f"{fmt_money_compact(val)} in {q}, or {share:.1f}% of GDP. "
                    f"Full briefing: mutapatimes.com/economy",
    }


def ch_construction(gdp, bop):
    last, q = latest_q(gdp)
    val = sector_val(gdp, "Construction", last)
    # YoY only (last-4) — comparisons further back cross the 2024 rebase.
    yoy = yoy_pct(gdp["sectors"]["Construction"], last)
    ago_idx = max(0, last - 4)
    ago = sector_val(gdp, "Construction", ago_idx)
    bars = [(gdp["quarters"][ago_idx], ago, False), (q, val, True)]
    return {
        "key": "construction",
        "eyebrow": "CONSTRUCTION",
        "headline": "What gets built.",
        "big_num": fmt_money_compact(val),
        "big_lbl": "construction sector",
        "sub": f"Construction output was {fmt_money_compact(val)} in {q}, "
               f"{fmt_pct(yoy)} year-on-year. A leading indicator for household and "
               f"government capital spending.",
        "bars": bars,
        "bar_unit": "USD, construction quarterly",
        "bg": CARD_BG_BUTTER,
        "footer_src": "Source: ZimStat, Quarterly GDP — Construction.",
        "rss_title": f"Zim construction sector: {fmt_money_compact(val)} in {q}, "
                     f"{fmt_pct(yoy)} YoY.",
        "rss_desc": f"Construction produced {fmt_money_compact(val)} in {q}, "
                    f"{fmt_pct(yoy)} year-on-year vs {gdp['quarters'][ago_idx]}. "
                    f"Full briefing: mutapatimes.com/economy",
    }


def ch_hospitality(gdp, bop):
    last, q = latest_q(gdp)
    val = sector_val(gdp, "Accommodation and food service activities", last)
    yoy = yoy_pct(gdp["sectors"]["Accommodation and food service activities"], last)
    ago_idx = max(0, last - 4)
    ago = sector_val(gdp, "Accommodation and food service activities", ago_idx)
    bars = [(gdp["quarters"][ago_idx], ago, False), (q, val, True)]
    return {
        "key": "hospitality",
        "eyebrow": "HOSPITALITY",
        "headline": "Tourism, sized.",
        "big_num": fmt_money_compact(val),
        "big_lbl": "hospitality sector",
        "sub": f"Hotels, lodges, restaurants and bars: {fmt_money_compact(val)} in {q}, "
               f"{fmt_pct(yoy)} year-on-year. Victoria Falls drives most of the visible "
               f"recovery.",
        "bars": bars,
        "bar_unit": "USD, hospitality quarterly",
        "bg": CARD_BG_SAGE,
        "footer_src": "Source: ZimStat, Quarterly GDP — Accommodation & Food.",
        "rss_title": f"Zim hospitality sector: {fmt_money_compact(val)} in {q}, "
                     f"{fmt_pct(yoy)} YoY.",
        "rss_desc": f"Hotels, lodges and restaurants produced {fmt_money_compact(val)} "
                    f"in {q}, {fmt_pct(yoy)} year-on-year vs {gdp['quarters'][ago_idx]}. "
                    f"Full briefing: mutapatimes.com/economy",
    }


def ch_transport(gdp, bop):
    last, q = latest_q(gdp)
    val = sector_val(gdp, "Transportation and storage", last)
    total = gdp_total(gdp, last)
    share = (val / total) * 100 if total else 0
    bars = [("Transport & storage", val, True)]
    # add 3 related: agri, mining, wholesale (sectors that ship)
    for n in [
        "Wholesale and retail trade; repair of motor vehicles and motorcycles",
        "Mining and quarrying",
        "Agiculture, Hunting and Fishing and forestry",
    ]:
        bars.append((short(n), gdp["sectors"][n][last], False))
    return {
        "key": "transport",
        "eyebrow": "LOGISTICS",
        "headline": "Moving the economy.",
        "big_num": fmt_money_compact(val),
        "big_lbl": "transport & storage",
        "sub": f"Transport and storage contributed {fmt_money_compact(val)} in {q} — "
               f"{share:.1f}% of GDP. The country is a transit hub for north-south "
               f"and east-west SADC trade.",
        "bars": bars,
        "bar_unit": "USD, latest quarter",
        "bg": CARD_BG_CREAM,
        "footer_src": "Source: ZimStat, Quarterly GDP — Transport & Storage.",
        "rss_title": f"Zim transport & storage sector: {fmt_money_compact(val)} in {q}, "
                     f"{share:.1f}% of GDP.",
        "rss_desc": f"Transport, logistics and storage produced {fmt_money_compact(val)} "
                    f"in {q}, or {share:.1f}% of GDP. Zimbabwe is a SADC transit hub. "
                    f"Full briefing: mutapatimes.com/economy",
    }


def ch_real_estate(gdp, bop):
    last, q = latest_q(gdp)
    val = sector_val(gdp, "Real estate activities", last)
    ago_idx = max(0, last - 4)
    ago = sector_val(gdp, "Real estate activities", ago_idx)
    pct = ((val - ago) / ago) * 100 if ago else 0
    bars = [(gdp["quarters"][ago_idx], ago, False), (q, val, True)]
    return {
        "key": "real_estate",
        "eyebrow": "REAL ESTATE",
        "headline": "Bricks and mortar.",
        "big_num": fmt_money_compact(val),
        "big_lbl": "real estate sector",
        "sub": f"Real estate output was {fmt_money_compact(val)} in {q}, {fmt_pct(pct)} "
               f"year-on-year. Diaspora capital flows here first — Harare and Bulawayo "
               f"premium values reflect it.",
        "bars": bars,
        "bar_unit": "USD, real estate quarterly",
        "bg": CARD_BG_BUTTER,
        "footer_src": "Source: ZimStat, Quarterly GDP — Real Estate.",
        "rss_title": f"Zim real estate sector: {fmt_money_compact(val)} in {q}, "
                     f"{fmt_pct(pct)} YoY.",
        "rss_desc": f"Real estate activities produced {fmt_money_compact(val)} in {q}, "
                    f"{fmt_pct(pct)} year-on-year. Diaspora demand keeps a floor under "
                    f"premium prices. Full briefing: mutapatimes.com/economy",
    }


def ch_top3_share(gdp, bop):
    last, q = latest_q(gdp)
    total = gdp_total(gdp, last)
    pairs = sorted(
        [(n, gdp["sectors"][n][last]) for n in gdp["sector_order"]],
        key=lambda p: p[1], reverse=True)
    top3 = pairs[:3]
    top3_sum = sum(v for _, v in top3)
    share = (top3_sum / total) * 100 if total else 0
    bars = [(short(n), v, True) for n, v in top3]
    return {
        "key": "top3_share",
        "eyebrow": "TOP THREE SECTORS",
        "headline": "The economy in three lines.",
        "big_num": fmt_pct(share, signed=False),
        "big_lbl": "of GDP",
        "sub": f"In {q}, {short(top3[0][0])}, {short(top3[1][0])} and "
               f"{short(top3[2][0])} together produced {fmt_pct(share, signed=False)} of "
               f"GDP. The remaining 17 sectors share what is left — a wide but shallow "
               f"productive base.",
        "bars": bars,
        "bar_unit": "USD, top three latest quarter",
        "bg": CARD_BG_CREAM,
        "footer_src": "Source: ZimStat, Quarterly GDP Tables.",
        "rss_title": f"Zim economy {q}: top three sectors are "
                     f"{fmt_pct(share, signed=False)} of GDP.",
        "rss_desc": f"Three sectors — {short(top3[0][0])}, {short(top3[1][0])} and "
                    f"{short(top3[2][0])} — account for {fmt_pct(share, signed=False)} "
                    f"of all Zimbabwe GDP in {q}. The base is narrow. "
                    f"Full briefing: mutapatimes.com/economy",
    }


def ch_education(gdp, bop):
    last, q = latest_q(gdp)
    val = sector_val(gdp, "Education", last)
    total = gdp_total(gdp, last)
    share = (val / total) * 100 if total else 0
    bars = [
        ("Education", val, True),
        ("Health & social work", sector_val(gdp, "Human health and social work activities", last), False),
        ("Public admin", sector_val(gdp, "Public administration and defence; compulsory social security", last), False),
    ]
    return {
        "key": "education",
        "eyebrow": "EDUCATION",
        "headline": "What schooling produces.",
        "big_num": fmt_money_compact(val),
        "big_lbl": "education sector",
        "sub": f"Schools, universities and training: {fmt_money_compact(val)} in {q}, "
               f"{share:.1f}% of GDP. Zimbabwe still has one of the higher literacy "
               f"rates in Sub-Saharan Africa.",
        "bars": bars,
        "bar_unit": "USD, latest quarter",
        "bg": CARD_BG_SAGE,
        "footer_src": "Source: ZimStat, Quarterly GDP — Education.",
        "rss_title": f"Zim education sector: {fmt_money_compact(val)} in {q}, "
                     f"{share:.1f}% of GDP.",
        "rss_desc": f"Education produced {fmt_money_compact(val)} in {q}, or "
                    f"{share:.1f}% of GDP. Zimbabwe's literacy rate remains among "
                    f"the highest in Sub-Saharan Africa. "
                    f"Full briefing: mutapatimes.com/economy",
    }


def ch_health(gdp, bop):
    last, q = latest_q(gdp)
    val = sector_val(gdp, "Human health and social work activities", last)
    total = gdp_total(gdp, last)
    share = (val / total) * 100 if total else 0
    bars = [
        ("Health & social work", val, True),
        ("Education", sector_val(gdp, "Education", last), False),
        ("Public admin", sector_val(gdp, "Public administration and defence; compulsory social security", last), False),
    ]
    return {
        "key": "health",
        "eyebrow": "HEALTH SECTOR",
        "headline": "What care costs.",
        "big_num": fmt_money_compact(val),
        "big_lbl": "health & social work",
        "sub": f"The health and social work sector — clinics, hospitals, mission care, "
               f"social protection — produced {fmt_money_compact(val)} in {q}, "
               f"{share:.1f}% of GDP.",
        "bars": bars,
        "bar_unit": "USD, latest quarter",
        "bg": CARD_BG_ROSE,
        "footer_src": "Source: ZimStat, Quarterly GDP — Health & Social Work.",
        "rss_title": f"Zim health & social work sector: {fmt_money_compact(val)} in {q}, "
                     f"{share:.1f}% of GDP.",
        "rss_desc": f"Health, hospitals and social work produced {fmt_money_compact(val)} "
                    f"in {q}, or {share:.1f}% of GDP. "
                    f"Full briefing: mutapatimes.com/economy",
    }


def ch_smallest_sector(gdp, bop):
    last, q = latest_q(gdp)
    pairs = sorted(
        [(n, gdp["sectors"][n][last]) for n in gdp["sector_order"]],
        key=lambda p: p[1])
    bottom_name, bottom_val = pairs[0]
    bars = [(short(n), v, n == bottom_name) for n, v in pairs[:5]]
    return {
        "key": "smallest_sector",
        "eyebrow": "THE SMALL CORNERS",
        "headline": "The economy's quiet edges.",
        "big_num": fmt_money_compact(bottom_val),
        "big_lbl": short(bottom_name),
        "sub": f"The smallest tracked sector in {q}. Even the smallest line in ZimStat's "
               f"GDP tables is a real industry employing real people.",
        "bars": bars,
        "bar_unit": "USD, bottom 5",
        "bg": CARD_BG_CREAM,
        "footer_src": "Source: ZimStat, Quarterly GDP Tables.",
        "rss_title": f"Zim economy {q}: {short(bottom_name)} is the smallest tracked "
                     f"sector at {fmt_money_compact(bottom_val)}.",
        "rss_desc": f"Among 20 ZimStat sectors, {short(bottom_name)} is the smallest "
                    f"in {q} at {fmt_money_compact(bottom_val)}. "
                    f"Full sector ranking: mutapatimes.com/economy",
    }


# ── BoP-based chapters ──

def ch_goods_trade(gdp, bop):
    last, q = bop_latest_q(bop)
    exp = bop["series"]["exports_goods"][last]
    imp = bop["series"]["imports_goods"][last]
    gap = (imp or 0) - (exp or 0)
    in_surplus = gap < 0
    bars = [
        ("Exports", (exp or 0) * 1e6, in_surplus),
        ("Imports", (imp or 0) * 1e6, not in_surplus),
    ]
    label = "trade surplus" if in_surplus else "trade deficit"
    return {
        "key": "goods_trade",
        "eyebrow": "GOODS TRADE",
        "headline": "The trade balance.",
        "big_num": fmt_bop(abs(gap)),
        "big_lbl": label,
        "sub": f"In {q} Zimbabwe exported {fmt_bop(exp)} of goods and imported "
               f"{fmt_bop(imp)} — a {label} of {fmt_bop(abs(gap))}. "
               f"The balance flipped to surplus in 2024 on lithium and gold exports.",
        "bars": bars,
        "bar_unit": "USD, latest quarter",
        "bg": CARD_BG_BUTTER,
        "footer_src": "Source: RBZ / ZimStat, Balance of Payments.",
        "rss_title": f"Zim trade balance {q}: {fmt_bop(abs(gap))} {label}. "
                     f"Exports {fmt_bop(exp)}, imports {fmt_bop(imp)}.",
        "rss_desc": f"Zimbabwe exported {fmt_bop(exp)} of goods and imported "
                    f"{fmt_bop(imp)} in {q} — a {label} of {fmt_bop(abs(gap))}. "
                    f"The goods balance flipped to surplus in 2024. "
                    f"Full briefing: mutapatimes.com/economy",
    }


def ch_remittances_quarterly(gdp, bop):
    last, q = bop_latest_q(bop)
    pt = bop["series"]["personal_transfers"]
    latest = pt[last]
    sum4, _ = sum_recent_quarters(pt, last + 1, 4)
    start = max(0, last - 3)
    bars = [(bop["quarters"][i], (pt[i] or 0) * 1e6, i == last) for i in range(start, last + 1)]
    return {
        "key": "remittances_quarterly",
        "eyebrow": "DIASPORA DIVIDEND",
        "headline": "Money home.",
        "big_num": fmt_bop(latest),
        "big_lbl": f"sent in {q}",
        "sub": f"Personal transfers in {q}. Over the trailing four quarters, "
               f"{fmt_bop(sum4)} flowed in via official channels. Informal channels "
               f"add more.",
        "bars": bars,
        "bar_unit": "USD, last four quarters",
        "bg": CARD_BG_SAGE,
        "footer_src": "Source: RBZ, Balance of Payments — Personal Transfers.",
        "rss_title": f"Zim remittances {q}: diaspora sent {fmt_bop(latest)} home "
                     f"officially. Trailing four quarters: {fmt_bop(sum4)}.",
        "rss_desc": f"Personal Transfers reached {fmt_bop(latest)} in {q}. "
                    f"Trailing four quarters total: {fmt_bop(sum4)}. "
                    f"Full chart: mutapatimes.com/economy",
    }


def ch_remittances_annual(gdp, bop):
    """Annual remittances totals for the last 5 years."""
    ind = bop["indicators"]["personal_transfers"]["annual"]
    years = sorted([y for y, v in ind.items() if v is not None])
    recent = years[-5:]
    bars = [(y, ind[y] * 1e6, y == recent[-1]) for y in recent]
    latest_year = recent[-1]
    latest_val = ind[latest_year]
    five_years_ago = recent[0]
    five_years_ago_val = ind[five_years_ago]
    pct = ((latest_val - five_years_ago_val) / five_years_ago_val) * 100 if five_years_ago_val else 0
    return {
        "key": "remittances_annual",
        "eyebrow": "REMITTANCES OVER TIME",
        "headline": "Five years of remittances.",
        "big_num": fmt_bop(latest_val),
        "big_lbl": f"sent home in {latest_year}",
        "sub": f"Recorded diaspora remittances rose from {fmt_bop(five_years_ago_val)} "
               f"in {five_years_ago} to {fmt_bop(latest_val)} in {latest_year} — "
               f"{fmt_pct(pct)} over five years.",
        "bars": bars,
        "bar_unit": "USD, annual",
        "bg": CARD_BG_SAGE,
        "footer_src": "Source: RBZ, Balance of Payments — Personal Transfers (annual).",
        "rss_title": f"Zim remittances {latest_year}: diaspora sent {fmt_bop(latest_val)} "
                     f"home — {fmt_pct(pct)} over five years.",
        "rss_desc": f"In {latest_year}, officially-recorded diaspora remittances totalled "
                    f"{fmt_bop(latest_val)} — up {fmt_pct(pct)} from "
                    f"{fmt_bop(five_years_ago_val)} in {five_years_ago}. "
                    f"Full briefing: mutapatimes.com/economy",
    }


def ch_services_trade(gdp, bop):
    last, q = bop_latest_q(bop)
    exp = bop["series"]["exports_services"][last]
    imp = bop["series"]["imports_services"][last]
    bal = (exp or 0) - (imp or 0)
    kind = "surplus" if bal > 0 else "deficit"
    bars = [
        ("Services exports", (exp or 0) * 1e6, bal > 0),
        ("Services imports", (imp or 0) * 1e6, bal < 0),
    ]
    return {
        "key": "services_trade",
        "eyebrow": "SERVICES TRADE",
        "headline": "Services in and out.",
        "big_num": fmt_bop(abs(bal)),
        "big_lbl": f"services {kind}",
        "sub": f"Zimbabwe sold {fmt_bop(exp)} of services in {q} — tourism, transport, "
               f"financial — and bought {fmt_bop(imp)}. The services balance is "
               f"structurally negative.",
        "bars": bars,
        "bar_unit": "USD, latest quarter",
        "bg": CARD_BG_CREAM,
        "footer_src": "Source: RBZ / ZimStat, Balance of Payments — Services.",
        "rss_title": f"Zim services trade {q}: {fmt_bop(abs(bal))} {kind}. "
                     f"Sold {fmt_bop(exp)}, bought {fmt_bop(imp)}.",
        "rss_desc": f"Zimbabwe exported {fmt_bop(exp)} of services in {q} and imported "
                    f"{fmt_bop(imp)} — a structural services {kind}. "
                    f"Full briefing: mutapatimes.com/economy",
    }


def ch_exports_trailing(gdp, bop):
    last, q = bop_latest_q(bop)
    series = bop["series"]["exports_goods"]
    sum4, _ = sum_recent_quarters(series, last + 1, 4)
    sum_prior, _ = sum_recent_quarters(series, last - 3, 4) if last >= 4 else (0, 0)
    pct = ((sum4 - sum_prior) / sum_prior) * 100 if sum_prior else 0
    bars = [
        ("Year ending " + bop["quarters"][last - 4], sum_prior * 1e6, False) if last >= 4
        else ("Prior period", 0, False),
        ("Year ending " + q, sum4 * 1e6, True),
    ]
    return {
        "key": "exports_trailing",
        "eyebrow": "TRADE FLOWS",
        "headline": "What Zimbabwe sells.",
        "big_num": fmt_bop(sum4),
        "big_lbl": "goods exports, 4Q",
        "sub": f"Trailing four-quarter goods exports ending {q}: {fmt_bop(sum4)}, "
               f"{fmt_pct(pct)} versus the prior four. Lithium, gold and tobacco "
               f"lead.",
        "bars": bars,
        "bar_unit": "USD, trailing-4Q goods exports",
        "bg": CARD_BG_BUTTER,
        "footer_src": "Source: RBZ / ZimStat, Balance of Payments — Exports.",
        "rss_title": f"Zim goods exports (4Q trailing to {q}): {fmt_bop(sum4)}, "
                     f"{fmt_pct(pct)} vs prior period.",
        "rss_desc": f"Trailing-four-quarter goods exports reached {fmt_bop(sum4)} "
                    f"to {q}, {fmt_pct(pct)} versus the prior period. "
                    f"Full briefing: mutapatimes.com/economy",
    }


def ch_imports_trailing(gdp, bop):
    last, q = bop_latest_q(bop)
    series = bop["series"]["imports_goods"]
    sum4, _ = sum_recent_quarters(series, last + 1, 4)
    sum_prior, _ = sum_recent_quarters(series, last - 3, 4) if last >= 4 else (0, 0)
    pct = ((sum4 - sum_prior) / sum_prior) * 100 if sum_prior else 0
    bars = [
        ("Year ending " + bop["quarters"][last - 4], sum_prior * 1e6, False) if last >= 4
        else ("Prior period", 0, False),
        ("Year ending " + q, sum4 * 1e6, True),
    ]
    return {
        "key": "imports_trailing",
        "eyebrow": "IMPORT BILL",
        "headline": "What Zimbabwe buys.",
        "big_num": fmt_bop(sum4),
        "big_lbl": "goods imports, 4Q",
        "sub": f"Trailing four-quarter goods imports ending {q}: {fmt_bop(sum4)}, "
               f"{fmt_pct(pct)} versus the prior four. Fuel, machinery and food "
               f"dominate the bill.",
        "bars": bars,
        "bar_unit": "USD, trailing-4Q goods imports",
        "bg": CARD_BG_ROSE,
        "footer_src": "Source: RBZ / ZimStat, Balance of Payments — Imports.",
        "rss_title": f"Zim goods imports (4Q trailing to {q}): {fmt_bop(sum4)}, "
                     f"{fmt_pct(pct)} vs prior period.",
        "rss_desc": f"Trailing-four-quarter goods imports reached {fmt_bop(sum4)} "
                    f"to {q}, {fmt_pct(pct)} versus the prior period. "
                    f"Full briefing: mutapatimes.com/economy",
    }


def ch_current_account(gdp, bop):
    last, q = bop_latest_q(bop)
    ca = bop["series"]["current_account"][last]
    sum4, _ = sum_recent_quarters(bop["series"]["current_account"], last + 1, 4)
    bars = [(bop["quarters"][i], (bop["series"]["current_account"][i] or 0) * 1e6,
             i == last) for i in range(max(0, last - 3), last + 1)]
    return {
        "key": "current_account",
        "eyebrow": "CURRENT ACCOUNT",
        "headline": "Zimbabwe versus the world.",
        "big_num": fmt_bop(ca),
        "big_lbl": "current account",
        "sub": f"The official current account printed {fmt_bop(ca)} in {q}. "
               f"Trailing-four-quarter: {fmt_bop(sum4)}. Includes trade, income, "
               f"and transfers combined.",
        "bars": bars,
        "bar_unit": "USD, last four quarters",
        "bg": CARD_BG_CREAM,
        "footer_src": "Source: RBZ, Balance of Payments — Current Account.",
        "rss_title": f"Zim current account {q}: {fmt_bop(ca)}. Trailing four quarters: "
                     f"{fmt_bop(sum4)}.",
        "rss_desc": f"The official current account read {fmt_bop(ca)} in {q}, "
                    f"with a trailing-four-quarter total of {fmt_bop(sum4)}. "
                    f"Full briefing: mutapatimes.com/economy",
    }


def ch_missing_money(gdp, bop):
    idx, ne, q = bop_latest_nonzero(bop, "net_errors_omissions")
    ca = bop["series"]["current_account"][idx]
    bars = [
        ("Current account", (ca or 0) * 1e6, False),
        ("Net errors & omissions", (ne or 0) * 1e6, True),
    ]
    return {
        "key": "missing_money",
        "eyebrow": "THE MISSING MONEY",
        "headline": "What the books cannot see.",
        "big_num": fmt_bop(ne),
        "big_lbl": "unrecorded balance",
        "sub": f"In {q}, the Balance of Payments residual — money that should add up "
               f"but does not — read {fmt_bop(ne)}. Likely a proxy for informal "
               f"economic activity not captured in the official ledger.",
        "bars": bars,
        "bar_unit": "USD, latest reported quarter",
        "bg": CARD_BG_ROSE,
        "footer_src": "Source: RBZ, Balance of Payments — Net Errors & Omissions.",
        "rss_title": f"Zim balance-of-payments residual {q}: net errors & omissions "
                     f"{fmt_bop(ne)} against current account {fmt_bop(ca)}.",
        "rss_desc": f"The Balance of Payments residual line — Net Errors & Omissions — "
                    f"printed {fmt_bop(ne)} in {q}, against an official current account "
                    f"of {fmt_bop(ca)}. A quiet statistical admission that the informal "
                    f"economy moves real money the books cannot fully see. "
                    f"Full briefing: mutapatimes.com/economy",
    }


def ch_primary_income(gdp, bop):
    last, q = bop_latest_q(bop)
    pi = bop["series"]["balance_primary_income"][last]
    sum4, _ = sum_recent_quarters(bop["series"]["balance_primary_income"], last + 1, 4)
    bars = [(bop["quarters"][i],
             (bop["series"]["balance_primary_income"][i] or 0) * 1e6, i == last)
            for i in range(max(0, last - 3), last + 1)]
    return {
        "key": "primary_income",
        "eyebrow": "INCOME FLOWS",
        "headline": "Interest and dividends, out.",
        "big_num": fmt_bop(pi),
        "big_lbl": "primary income balance",
        "sub": f"Net interest and dividend flows in {q}: {fmt_bop(pi)}. Negative means "
               f"more leaves the country than arrives — a marker of foreign-held debt "
               f"and equity service.",
        "bars": bars,
        "bar_unit": "USD, last four quarters",
        "bg": CARD_BG_ROSE,
        "footer_src": "Source: RBZ, Balance of Payments — Primary Income.",
        "rss_title": f"Zim primary income {q}: {fmt_bop(pi)}. Trailing four quarters: "
                     f"{fmt_bop(sum4)}.",
        "rss_desc": f"Net primary income flows printed {fmt_bop(pi)} in {q}, with a "
                    f"trailing-four-quarter total of {fmt_bop(sum4)}. Negative readings "
                    f"reflect outbound dividends and interest payments to foreign "
                    f"creditors and equity holders. "
                    f"Full briefing: mutapatimes.com/economy",
    }


def ch_secondary_income(gdp, bop):
    last, q = bop_latest_q(bop)
    si = bop["series"]["balance_secondary_income"][last]
    sum4, _ = sum_recent_quarters(bop["series"]["balance_secondary_income"], last + 1, 4)
    bars = [(bop["quarters"][i],
             (bop["series"]["balance_secondary_income"][i] or 0) * 1e6, i == last)
            for i in range(max(0, last - 3), last + 1)]
    return {
        "key": "secondary_income",
        "eyebrow": "TRANSFERS",
        "headline": "Net transfers in.",
        "big_num": fmt_bop(si),
        "big_lbl": "secondary income",
        "sub": f"Net transfers in {q}: {fmt_bop(si)}. Includes diaspora remittances, "
               f"NGO and donor flows, government grants — the inbound side of "
               f"non-trade money.",
        "bars": bars,
        "bar_unit": "USD, last four quarters",
        "bg": CARD_BG_SAGE,
        "footer_src": "Source: RBZ, Balance of Payments — Secondary Income.",
        "rss_title": f"Zim secondary income {q}: {fmt_bop(si)}. Trailing four quarters: "
                     f"{fmt_bop(sum4)}.",
        "rss_desc": f"Net secondary income — remittances plus NGO and donor flows "
                    f"minus outbound transfers — reached {fmt_bop(si)} in {q}, with "
                    f"a trailing-four-quarter total of {fmt_bop(sum4)}. "
                    f"Full briefing: mutapatimes.com/economy",
    }


def ch_export_concentration(gdp, bop):
    """Goods exports as a share of total exports."""
    last, q = bop_latest_q(bop)
    goods = bop["series"]["exports_goods"][last] or 0
    services = bop["series"]["exports_services"][last] or 0
    total = goods + services
    share = (goods / total) * 100 if total else 0
    bars = [
        ("Goods exports", goods * 1e6, True),
        ("Services exports", services * 1e6, False),
    ]
    return {
        "key": "export_concentration",
        "eyebrow": "EXPORT MIX",
        "headline": "Goods vs services.",
        "big_num": fmt_pct(share, signed=False),
        "big_lbl": "of exports are goods",
        "sub": f"Of {fmt_bop(total)} in total exports in {q}, "
               f"{fmt_pct(share, signed=False)} were physical goods. The country sells "
               f"materials and grows tobacco; it does not yet export services at scale.",
        "bars": bars,
        "bar_unit": "USD, latest quarter",
        "bg": CARD_BG_BUTTER,
        "footer_src": "Source: RBZ / ZimStat, Balance of Payments — Exports breakdown.",
        "rss_title": f"Zim export mix {q}: {fmt_pct(share, signed=False)} of "
                     f"{fmt_bop(total)} exports are physical goods.",
        "rss_desc": f"Of {fmt_bop(total)} in total exports in {q}, "
                    f"{fmt_pct(share, signed=False)} were goods ({fmt_bop(goods)}) "
                    f"and the remainder services ({fmt_bop(services)}). "
                    f"Full briefing: mutapatimes.com/economy",
    }


def ch_import_dependency(gdp, bop):
    """Goods imports as a share of GDP — import dependency."""
    last, q = bop_latest_q(bop)
    imports4, _ = sum_recent_quarters(bop["series"]["imports_goods"], last + 1, 4)
    # Match the most recent GDP year (sum the GDP quarterly aggregate)
    gdp_last = len(gdp["quarters"]) - 1
    gdp4, _ = sum_recent_quarters(gdp["aggregates"]["GDP at Market Prices"], gdp_last + 1, 4)
    gdp4_millions = (gdp4 or 0) / 1e6  # convert to millions to compare
    share = (imports4 / gdp4_millions) * 100 if gdp4_millions else 0
    bars = [
        ("GDP, trailing 4Q", (gdp4 or 0), False),
        ("Imports, trailing 4Q", imports4 * 1e6, True),
    ]
    return {
        "key": "import_dependency",
        "eyebrow": "IMPORT DEPENDENCY",
        "headline": "How much we buy from abroad.",
        "big_num": fmt_pct(share, signed=False),
        "big_lbl": "imports vs GDP, 4Q",
        "sub": f"Trailing-four-quarter goods imports were {fmt_pct(share, signed=False)} "
               f"of GDP. Fuel, machinery and food dominate. Domestic industry has not "
               f"yet substituted at scale.",
        "bars": bars,
        "bar_unit": "USD, trailing four quarters",
        "bg": CARD_BG_ROSE,
        "footer_src": "Source: RBZ, BoP + ZimStat, Quarterly GDP.",
        "rss_title": f"Zim import dependency {q}: trailing-4Q goods imports are "
                     f"{fmt_pct(share, signed=False)} of GDP.",
        "rss_desc": f"Zimbabwe imported {fmt_bop(imports4)} of goods in the trailing "
                    f"four quarters ending {q} — {fmt_pct(share, signed=False)} of GDP. "
                    f"Full briefing: mutapatimes.com/economy",
    }


def ch_current_account_5y(gdp, bop):
    """Current account, last 5 annual readings."""
    ind = bop["indicators"]["current_account"]["annual"]
    years = sorted([y for y, v in ind.items() if v is not None])
    recent = years[-5:]
    bars = [(y, ind[y] * 1e6, y == recent[-1]) for y in recent]
    latest_year = recent[-1]
    latest_val = ind[latest_year]
    return {
        "key": "current_account_5y",
        "eyebrow": "EXTERNAL BALANCE",
        "headline": "Current account, five years.",
        "big_num": fmt_bop(latest_val),
        "big_lbl": f"in {latest_year}",
        "sub": f"The current account combines trade, income and transfers. Across the "
               f"last five years it has averaged near balance — a structural improvement "
               f"on the heavy deficits of the early 2010s.",
        "bars": bars,
        "bar_unit": "USD, annual",
        "bg": CARD_BG_CREAM,
        "footer_src": "Source: RBZ, Balance of Payments — Current Account (annual).",
        "rss_title": f"Zim current account in {latest_year}: {fmt_bop(latest_val)}. "
                     f"Five-year trend shows persistent near-balance.",
        "rss_desc": f"Zimbabwe's full-year {latest_year} current account read "
                    f"{fmt_bop(latest_val)}. The annual series has hovered near "
                    f"balance across the last five years — a structural improvement. "
                    f"Full briefing: mutapatimes.com/economy",
    }


# ── Master rotation list ─────────────────────────────────────
# Length = 31 — index by day-of-year so no stat repeats inside any
# 30-day calendar window. Order is fixed (do not shuffle once shipped:
# the same date in different years should produce the same chapter for
# consistency).
CHAPTERS = [
    ch_top_sector,             # 0
    ch_goods_trade,            # 1
    ch_fastest_growing,        # 2
    ch_remittances_quarterly,  # 3
    ch_mining_vs_agri,         # 4
    ch_services_trade,         # 5
    ch_missing_money,          # 6
    ch_lithium_boom,           # 7
    ch_exports_trailing,       # 8
    ch_top3_share,             # 9
    ch_remittances_annual,     # 10
    ch_manufacturing_trend,    # 11
    ch_current_account,        # 12
    ch_ict_rise,               # 13
    ch_imports_trailing,       # 14
    ch_wholesale_retail,       # 15
    ch_primary_income,         # 16
    ch_finance,                # 17
    ch_export_concentration,   # 18
    ch_construction,           # 19
    ch_fastest_declining,      # 20
    ch_hospitality,            # 21
    ch_secondary_income,       # 22
    ch_mining_vs_mfg,          # 23
    ch_transport,              # 24
    ch_current_account_5y,     # 25
    ch_education,              # 26
    ch_import_dependency,      # 27
    ch_real_estate,            # 28
    ch_health,                 # 29
    ch_smallest_sector,        # 30
]


def pick_chapter_for_today(override=None):
    """Pick today's chapter dict + metadata. CAT (UTC+2) day-of-year mod
    len(CHAPTERS) — so no stat repeats within any 30-day window.

    Returns (idx, day_name, chapter_dict)."""
    gdp, bop = load_data()
    if override is not None:
        idx = override % len(CHAPTERS)
        # Use a synthetic name so test output is meaningful
        day_name = f"chapter-{idx:02d}"
        return idx, day_name, CHAPTERS[idx](gdp, bop)
    cat = datetime.now(timezone(timedelta(hours=2)))
    idx = (cat.timetuple().tm_yday - 1) % len(CHAPTERS)
    day_name = cat.strftime("%A")
    return idx, day_name, CHAPTERS[idx](gdp, bop)


def num_chapters():
    return len(CHAPTERS)
