#!/usr/bin/env python3
"""Pull the Zimbabwe Stock Exchange end-of-day Market Activity from the ZSE's
own public JSON API and write data/zse-market-activity.json.

The zse.co.zw site is a Next.js app that renders the Market Activity numbers
client-side from a public (no-auth) JSON API served via CloudFront. We call the
same endpoints the site uses:

  {BASE}/api/fetch/dtr?exchange=ZSE        Daily Trade Report:
                                             turnover, trades, volume,
                                             total market cap, movers/shakers
  {BASE}/api/fetch/indices?exchange=ZSE    every index (close + % change)
  {BASE}/api/fetch/market-capitalisation   per-company (name -> symbol map)
  {BASE}/api/notices?exchange=ZSE          ZSE notices + press releases

End-of-day only; the exchange publishes after the ~15:00 CAT close. The
CloudFront host can change if the ZSE redeploys — override with ZSE_API_BASE.
"""
import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone

# Public API base the zse.co.zw bundle calls (no auth). Overridable in case the
# CloudFront distribution id rotates on a ZSE redeploy.
API_BASE = os.environ.get("ZSE_API_BASE", "https://ds88jcmqc11je.cloudfront.net").rstrip("/")
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5) AppleWebKit/605.1.15 "
      "(KHTML, like Gecko) Version/16.6 Safari/605.1.15")

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "data", "zse-market-activity.json")
HIST = os.path.join(ROOT, "data", "zse-history.json")


def _get(path):
    url = f"{API_BASE}{path}"
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=25) as resp:
        return json.loads(resp.read().decode("utf-8", errors="replace"))


def _data(payload):
    """Endpoints wrap the useful bit in {status, data: ...}."""
    if isinstance(payload, dict):
        return payload.get("data", payload)
    return payload


def _round(x, n=2):
    try:
        return round(float(x), n)
    except (TypeError, ValueError):
        return None


def _as_of_from_indices(indices):
    """indices[].latestDate is a [Y, M, D] array."""
    for row in indices:
        d = row.get("latestDate")
        if isinstance(d, list) and len(d) == 3:
            return f"{d[0]:04d}-{d[1]:02d}-{d[2]:02d}"
    return None


def _symbol_map(mcap_rows):
    """UPPERCASE company name -> ticker symbol (e.g. 'SEED.ZW')."""
    m = {}
    for r in mcap_rows:
        name = (r.get("companyName") or "").strip().upper()
        sym = (r.get("symbol") or "").strip()
        if name and sym:
            m[name] = sym
    return m


def _mover(row, symmap):
    name = (row.get("counter") or "").strip()
    return {
        "name": name.title(),
        "symbol": symmap.get(name.upper(), ""),
        "price": _round(row.get("todayPrice")),
        "change_pct": _round(row.get("percentageChange")),
    }


def _index_row(row):
    pct = row.get("percentageChange")
    pts = row.get("pointChange")
    direction = "flat"
    try:
        if float(pct) > 0:
            direction = "up"
        elif float(pct) < 0:
            direction = "down"
    except (TypeError, ValueError):
        pass
    return {
        "name": (row.get("index") or "").strip(),
        "value": _round(row.get("close")),
        "change_pct": _round(pct),
        "change_points": _round(pts, 4),
        "direction": direction,
    }


def build():
    dtr_raw = _data(_get("/api/fetch/dtr?exchange=ZSE"))
    indices_raw = _data(_get("/api/fetch/indices?exchange=ZSE"))
    try:
        mcap_raw = _data(_get("/api/fetch/market-capitalisation?exchange=ZSE"))
    except Exception as e:
        print(f"  market-cap fetch failed (symbols will be blank): {e}")
        mcap_raw = []
    try:
        notices_raw = _data(_get("/api/notices?exchange=ZSE"))
    except Exception as e:
        print(f"  notices fetch failed: {e}")
        notices_raw = []

    # DTR content is a JSON string inside data[0].content
    dtr = {}
    if isinstance(dtr_raw, list) and dtr_raw:
        try:
            dtr = json.loads(dtr_raw[0].get("content", "{}"))
        except Exception as e:
            print(f"  DTR content parse failed: {e}")
    vt = dtr.get("volumeAndTurnover", {}) or {}
    movers = (dtr.get("moversAndShakers", {}) or {})
    symmap = _symbol_map(mcap_raw if isinstance(mcap_raw, list) else [])

    indices = [_index_row(r) for r in (indices_raw or []) if r.get("index")]
    # Order the marquee indices first, then the rest, for stable display.
    lead = ["ALL SHARE", "ZSE TOP 10", "ZSE TOP 15", "MID CAP INDEX",
            "SMALL CAP INDEX"]
    indices.sort(key=lambda r: (lead.index(r["name"]) if r["name"] in lead else 99, r["name"]))

    as_of = _as_of_from_indices(indices_raw or []) or datetime.now(timezone.utc).strftime("%Y-%m-%d")

    notices = []
    for n in (notices_raw or [])[:8]:
        notices.append({
            "date": (n.get("date") or "")[:10],
            "title": (n.get("name") or "").strip(),
            "category": ((n.get("category") or {}) or {}).get("name") or "",
            "url": n.get("proxy_download_url") or n.get("link_url") or "",
        })

    payload = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "as_of": as_of,
        "source": "Zimbabwe Stock Exchange (public market-data API)",
        "source_url": "https://www.zse.co.zw",
        "currency": "ZWG",
        "activity": {
            "trades": vt.get("totalNumberOfTrades"),
            "turnover": _round(vt.get("totalMarketTurnover")),
            "volume": _round(vt.get("totalMarketVolumeShares"), 0),
            "market_cap": _round(dtr.get("totalMarketCapitalisation")),
        },
        "indices": indices,
        "gainers": [_mover(r, symmap) for r in (movers.get("movers") or [])[:5]],
        "losers": [_mover(r, symmap) for r in (movers.get("shakers") or [])[:5]],
        "notices": notices,
    }
    return payload


def append_history(payload):
    """Upsert the day's closes into data/zse-history.json (one entry per
    trading day) so 1M/3M/6M/YTD/all-time charts can be built. There is no
    public ZSE history endpoint, so the series is accumulated forward from
    each end-of-day snapshot."""
    d = payload.get("as_of")
    if not d:
        return
    hist = {"updated": "", "series": []}
    if os.path.isfile(HIST):
        try:
            hist = json.load(open(HIST, encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            hist = {"updated": "", "series": []}
    idx = {}
    for x in payload.get("indices", []):
        if x.get("name") and x.get("value") is not None:
            idx[x["name"]] = x["value"]
    entry = {
        "d": d,
        "idx": idx,
        "turnover": payload.get("activity", {}).get("turnover"),
        "mcap": payload.get("activity", {}).get("market_cap"),
    }
    series = [e for e in hist.get("series", []) if e.get("d") != d]  # upsert by date
    series.append(entry)
    series.sort(key=lambda e: e.get("d", ""))
    hist["series"] = series
    hist["updated"] = datetime.now(timezone.utc).isoformat()
    with open(HIST, "w", encoding="utf-8") as f:
        json.dump(hist, f, ensure_ascii=False, separators=(",", ":"))
    print(f"  history: {len(series)} trading day(s) in {os.path.relpath(HIST, ROOT)}")


def main():
    try:
        payload = build()
    except (urllib.error.URLError, urllib.error.HTTPError, ValueError) as e:
        print(f"ERROR fetching ZSE market data: {e}")
        sys.exit(1)

    act = payload["activity"]
    if not act.get("turnover") and not payload["indices"]:
        print("ERROR: empty ZSE payload, refusing to overwrite")
        sys.exit(1)

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    append_history(payload)
    print(f"Wrote {os.path.relpath(OUT, ROOT)}  (as of {payload['as_of']})")
    print(f"  trades={act['trades']}  turnover={act['turnover']}  mcap={act['market_cap']}")
    print(f"  indices={len(payload['indices'])}  gainers={len(payload['gainers'])}  "
          f"losers={len(payload['losers'])}  notices={len(payload['notices'])}")


if __name__ == "__main__":
    main()
