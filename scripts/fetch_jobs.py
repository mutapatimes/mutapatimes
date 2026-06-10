#!/usr/bin/env python3
"""Scrape Zimbabwe job listings from public job boards and save to
data/jobs.json for client-side rendering on /jobs.html.

We aggregate - each listing links back to the source board so the apply
flow happens on their site. New boards can be added by appending another
(label, url, parser) tuple to SOURCES. Each parser receives the raw HTML
and returns a list of normalised job dicts.
"""
import html as html_mod
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

DATA_DIR = "data"
OUTPUT_FILE = os.path.join(DATA_DIR, "jobs.json")
USER_AGENT = "Mozilla/5.0 (compatible; MutapaTimesBot/1.0; +https://mutapatimes.com)"
MAX_JOBS = 300  # accumulate up to ~30 days of inflow; page filters
RETENTION_DAYS = 30  # prune listings older than this


def fetch_html(url, timeout=30):
    req = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-US,en;q=0.9",
    })
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def clean_text(s):
    if not s:
        return ""
    return re.sub(r"\s+", " ", html_mod.unescape(s)).strip()


def absolute_url(base, href):
    if not href:
        return ""
    if href.startswith("//"):
        return "https:" + href
    if href.startswith("/"):
        return base + href
    return href


# ── vacancymail.co.zw ─────────────────────────────────────────
VM_BASE = "https://vacancymail.co.zw"
VM_CARD_RE = re.compile(
    r'<a\s+href="(/jobs/[^"]+)"\s+class="job-listing"[^>]*>(.*?)</a>',
    re.DOTALL,
)
VM_TITLE_RE = re.compile(
    r'<h3[^>]*class="job-listing-title"[^>]*>(.*?)</h3>', re.DOTALL,
)
VM_COMPANY_RE = re.compile(
    r'<h4[^>]*class="job-listing-company"[^>]*>(.*?)</h4>', re.DOTALL,
)
VM_TEXT_RE = re.compile(
    r'<p[^>]*class="job-listing-text"[^>]*>(.*?)</p>', re.DOTALL,
)
VM_LOGO_RE = re.compile(
    r'<img\s+src="([^"]+)"', re.DOTALL,
)
# Each <li> in the footer has an icon + the field. Match by icon class.
VM_LOCATION_RE = re.compile(
    r'<i\s+class="icon-material-outline-location-on"[^>]*></i>\s*([^<]+?)</li>',
    re.DOTALL,
)
VM_EXPIRES_RE = re.compile(
    r'<i\s+class="icon-material-outline-access-time"[^>]*></i>\s*Expires\s+([^<]+?)</li>',
    re.DOTALL,
)
VM_TYPE_RE = re.compile(
    r'<i\s+class="icon-material-outline-business-center"[^>]*></i>\s*([^<]+?)</li>',
    re.DOTALL,
)
VM_SALARY_RE = re.compile(
    r'<i\s+class="icon-material-outline-account-balance-wallet"[^>]*></i>\s*([^<]+?)</li>',
    re.DOTALL,
)
VM_POSTED_RE = re.compile(
    r'<i\s+class="icon-material-outline-access-time"[^>]*></i>\s*Posted\s+([^<]+?)</li>',
    re.DOTALL,
)


def _first(pattern, text):
    """Return group(1) of pattern.search(text), or '' if no match."""
    m = pattern.search(text)
    return m.group(1) if m else ""


def parse_vacancymail(html):
    jobs = []
    for href, card_html in VM_CARD_RE.findall(html):
        title = clean_text(_first(VM_TITLE_RE, card_html))
        if not title:
            continue
        company = clean_text(_first(VM_COMPANY_RE, card_html))
        text = clean_text(_first(VM_TEXT_RE, card_html))
        if len(text) > 200:
            text = text[:199].rstrip() + "…"
        logo = absolute_url(VM_BASE, _first(VM_LOGO_RE, card_html))
        location = clean_text(_first(VM_LOCATION_RE, card_html))
        expires = clean_text(_first(VM_EXPIRES_RE, card_html))
        job_type = clean_text(_first(VM_TYPE_RE, card_html))
        salary = clean_text(_first(VM_SALARY_RE, card_html))
        if salary.upper() == "TBA":
            salary = ""
        posted = clean_text(_first(VM_POSTED_RE, card_html))
        jobs.append({
            "title": title,
            "url": absolute_url(VM_BASE, href),
            "company": company,
            "logo": logo,
            "summary": text,
            "location": location,
            "expires": expires,
            "type": job_type,
            "salary": salary,
            "posted": posted,
        })
    return jobs


# Registered sources. Add more tuples here to extend coverage.
SOURCES = [
    ("vacancymail.co.zw", f"{VM_BASE}/jobs/", parse_vacancymail),
]


def main():
    print("=== FETCH JOBS ===")
    all_jobs = []
    sources_used = []
    for label, url, parser in SOURCES:
        print(f"\n  {label} → {url}")
        try:
            page = fetch_html(url)
        except urllib.error.HTTPError as e:
            print(f"    HTTP {e.code}: {e.reason}")
            continue
        except Exception as e:
            print(f"    fetch ERROR: {e}")
            continue
        try:
            jobs = parser(page)
        except Exception as e:
            print(f"    parse ERROR: {e}")
            continue
        for j in jobs:
            j["source"] = label
        all_jobs.extend(jobs)
        sources_used.append(label)
        print(f"    parsed {len(jobs)} jobs")
        time.sleep(1)  # polite delay between boards

    if not all_jobs:
        print("\n  WARN: 0 jobs parsed across all sources. Not overwriting.")
        sys.exit(1)

    # ── Accumulate like the wire archive: each listing keeps a
    #    first_seen timestamp, and we prune anything older than
    #    RETENTION_DAYS. Source removals no longer drop active listings
    #    that are still within the window.
    from datetime import timedelta
    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()
    retention_cutoff = now - timedelta(days=RETENTION_DAYS)

    # Load the previous run, keyed by URL
    existing = {}
    try:
        with open(OUTPUT_FILE) as f:
            prev = json.load(f)
        for old in prev.get("jobs", []):
            u = old.get("url")
            if u:
                existing[u] = old
    except (IOError, json.JSONDecodeError):
        pass

    # Merge fresh fetch over the existing dict, preserving first_seen
    seen_urls = set()
    for j in all_jobs:
        u = j.get("url", "")
        if not u or u in seen_urls:
            continue
        seen_urls.add(u)
        if u in existing:
            j["first_seen"] = existing[u].get("first_seen") or now_iso
        else:
            j["first_seen"] = now_iso
        j["last_seen"] = now_iso
        existing[u] = j

    # Drop entries whose first_seen is older than RETENTION_DAYS
    def _within_retention(entry):
        ts = entry.get("first_seen")
        if not ts:
            return True  # keep entries with no timestamp (legacy); next run will stamp them
        try:
            d = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            return d >= retention_cutoff
        except ValueError:
            return True

    fresh_count = sum(1 for j in existing.values() if j.get("first_seen") == now_iso and j["url"] in seen_urls)
    kept_count = sum(1 for j in existing.values() if j.get("last_seen") != now_iso)
    expired_count = sum(1 for j in existing.values() if not _within_retention(j))

    unique = [j for j in existing.values() if _within_retention(j)]
    # Newest first
    unique.sort(key=lambda j: j.get("first_seen", ""), reverse=True)
    unique = unique[:MAX_JOBS]

    print(f"  Listings: {fresh_count} new, {kept_count} carried over, {expired_count} expired (>{RETENTION_DAYS}d)")

    output = {
        "fetched_at": now_iso,
        "sources": sources_used,
        "retention_days": RETENTION_DAYS,
        "count": len(unique),
        "jobs": unique,
    }

    os.makedirs(DATA_DIR, exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n  Wrote {OUTPUT_FILE} ({len(unique)} jobs from {len(sources_used)} source"
          f"{'s' if len(sources_used) != 1 else ''})")
    print("\n=== DONE ===")


if __name__ == "__main__":
    main()
