#!/usr/bin/env python3
"""
Send The Mutapa Times newsletter via Brevo API (Mon/Wed/Sat).
Reads data/spotlight.json and data/*.json category files, builds an HTML email
with a featured spotlight section and category headlines, creates a campaign,
and sends it. Stdlib only — no pip dependencies.
"""
import json
import os
import sys
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime, timezone

# ── Configuration ───────────────────────────────────────────
BREVO_API_KEY = os.environ.get("BREVO_API_KEY", "")
BREVO_BASE = "https://api.brevo.com/v3"
BREVO_LIST_ID = int(os.environ.get("BREVO_LIST_ID", "2"))
DATA_DIR = "data"

SENDER_NAME = "The Mutapa Times"
SENDER_EMAIL = "news@mutapatimes.com"
SITE_URL = "https://www.mutapatimes.com"

# Primary categories first — editorial focus for business & intelligence service
PRIMARY_CATEGORIES = ["business", "politics", "policy", "technology"]
SECONDARY_CATEGORIES = ["health", "entertainment", "sports", "science"]
CATEGORIES = PRIMARY_CATEGORIES + SECONDARY_CATEGORIES
MAX_PER_CATEGORY = 2
MAX_TOTAL = 12
MAX_ARTICLE_AGE_DAYS = 14  # Reject articles older than this
SPOTLIGHT_MAX_AGE_DAYS = 30

DAY_GREETINGS = {
    0: "Monday morning",
    2: "Wednesday midweek",
    5: "Saturday weekend",
}


# ── Brevo API helper ───────────────────────────────────────
def brevo_request(endpoint, payload=None, method="POST"):
    """Make authenticated request to Brevo API."""
    url = BREVO_BASE + endpoint
    headers = {
        "api-key": BREVO_API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    data = json.dumps(payload).encode("utf-8") if payload else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, json.loads(body) if body.strip() else {}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        print(f"  Brevo API error {e.code}: {body}")
        return e.code, json.loads(body) if body.strip() else {}


# ── Data loading ────────────────────────────────────────────
def parse_article_date(date_str):
    """Parse various date formats into datetime, return None on failure."""
    if not date_str:
        return None
    try:
        # ISO 8601 format (GNews)
        clean = date_str.replace("Z", "+00:00")
        return datetime.fromisoformat(clean)
    except (ValueError, TypeError):
        pass
    try:
        # RFC 2822 format (RSS feeds) — e.g. "Wed, 28 Jan 2026 15:31:13 GMT"
        from email.utils import parsedate_to_datetime
        return parsedate_to_datetime(date_str)
    except Exception:
        pass
    return None


def is_article_fresh(article, max_age_days):
    """Check if article is within max_age_days of now. Reject unparseable dates."""
    dt = parse_article_date(article.get("publishedAt", ""))
    if dt is None:
        return False
    try:
        age = (datetime.now(timezone.utc) - dt).days
        return age <= max_age_days
    except Exception:
        return False


def normalize_title(title):
    """Lowercase, strip punctuation/whitespace for comparison."""
    import re
    t = title.lower().strip()
    t = re.sub(r"[^\w\s]", "", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def titles_are_similar(t1, t2, threshold=0.65):
    """Check if two titles are about the same story using word overlap (Jaccard)."""
    w1 = set(normalize_title(t1).split())
    w2 = set(normalize_title(t2).split())
    if not w1 or not w2:
        return False
    n1, n2 = normalize_title(t1), normalize_title(t2)
    if n1 in n2 or n2 in n1:
        return True
    intersection = w1 & w2
    union = w1 | w2
    return len(intersection) / len(union) >= threshold


def load_spotlight():
    """Read spotlight articles from data/spotlight.json — max 30 days old, reputable only."""
    filepath = os.path.join(DATA_DIR, "spotlight.json")
    if not os.path.exists(filepath):
        return []
    with open(filepath) as f:
        data = json.load(f)
    articles = data.get("articles", [])
    # Strict date filter — no old content in spotlight
    fresh = [a for a in articles if is_article_fresh(a, SPOTLIGHT_MAX_AGE_DAYS)]
    return fresh[:3]


def load_articles(exclude_urls=None):
    """Read all data/*.json files, merge, deduplicate, filter by date, sort by recency."""
    if exclude_urls is None:
        exclude_urls = set()
    all_articles = []
    for cat in CATEGORIES:
        filepath = os.path.join(DATA_DIR, f"{cat}.json")
        if not os.path.exists(filepath):
            continue
        with open(filepath) as f:
            data = json.load(f)
        for a in data.get("articles", []):
            a["_category"] = cat
        all_articles.extend(data.get("articles", []))

    # Deduplicate by URL, exclude spotlight URLs, filter by date, and dedup by title similarity
    seen_urls = set()
    unique = []
    for a in all_articles:
        url = a.get("url", "")
        title = a.get("title", "")
        if url and url in seen_urls:
            continue
        if url and url in exclude_urls:
            continue
        # Reject articles older than MAX_ARTICLE_AGE_DAYS
        if not is_article_fresh(a, MAX_ARTICLE_AGE_DAYS):
            continue
        # Title similarity deduplication — skip near-duplicate headlines
        if title and any(titles_are_similar(title, u.get("title", "")) for u in unique):
            continue
        if url:
            seen_urls.add(url)
        unique.append(a)

    unique.sort(key=lambda a: a.get("publishedAt", ""), reverse=True)
    return unique


def pick_top_articles(articles):
    """Pick top articles prioritizing primary categories (business, politics, policy, tech).

    Strategy:
    1. Fill primary categories first (up to MAX_PER_CATEGORY each)
    2. Then fill remaining slots with secondary categories
    3. Within each category, articles are already sorted by date (newest first)
    """
    cat_counts = {c: 0 for c in CATEGORIES}
    picked = []
    picked_urls = set()

    # Pass 1: primary categories first
    for a in articles:
        cat = a.get("_category", "")
        url = a.get("url", "")
        if cat not in PRIMARY_CATEGORIES:
            continue
        if cat_counts.get(cat, 0) >= MAX_PER_CATEGORY:
            continue
        if url in picked_urls:
            continue
        picked.append(a)
        picked_urls.add(url)
        cat_counts[cat] = cat_counts.get(cat, 0) + 1
        if len(picked) >= MAX_TOTAL:
            return picked

    # Pass 2: secondary categories fill remaining slots
    for a in articles:
        cat = a.get("_category", "")
        url = a.get("url", "")
        if cat in PRIMARY_CATEGORIES:
            continue
        if cat_counts.get(cat, 0) >= MAX_PER_CATEGORY:
            continue
        if url in picked_urls:
            continue
        picked.append(a)
        picked_urls.add(url)
        cat_counts[cat] = cat_counts.get(cat, 0) + 1
        if len(picked) >= MAX_TOTAL:
            break

    return picked


# ── HTML email builder ──────────────────────────────────────
def escape_html(text):
    """Escape HTML special characters."""
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


def format_date(date_str):
    """Format date string to human-readable."""
    if not date_str:
        return ""
    try:
        clean = date_str.replace("Z", "+00:00").replace(" ", "T")
        if "+" not in clean and clean.count("T") == 1:
            clean += "+00:00"
        dt = datetime.fromisoformat(clean)
        return dt.strftime("%B %d, %Y")
    except (ValueError, TypeError):
        return ""


def whatsapp_share_url(title, url):
    """Build a wa.me share URL with pre-populated Mutapa Times copy."""
    text = (
        f"{title}\n\n"
        f"\U0001f517 {url}\n\n"
        f"\U0001f1ff\U0001f1fc Stay informed on Zimbabwe \u2014 follow @MutapaTimes "
        f"for daily news, analysis & more.\n"
        f"\U0001f4f0 https://www.mutapatimes.com"
    )
    return "https://wa.me/?text=" + urllib.parse.quote(text, safe="")


def whatsapp_share_link(title, url, color="rgba(255,255,255,0.5)", size="11px"):
    """Build an inline WhatsApp share link for an article."""
    wa_url = whatsapp_share_url(title, url)
    return (
        f'<a href="{wa_url}" target="_blank" '
        f'style="font-family:Helvetica,Arial,sans-serif;font-size:{size};'
        f'color:{color};text-decoration:none;white-space:nowrap;" '
        f'title="Share on WhatsApp">'
        f'WhatsApp'
        f'</a>'
    )


def build_spotlight_html(spotlight_articles):
    """Build the dark-green spotlight section HTML."""
    if not spotlight_articles:
        return ""

    spotlight_rows = ""
    for a in spotlight_articles:
        title = escape_html(a.get("title", "No title"))
        raw_title = a.get("title", "No title")
        url = escape_html(a.get("url", "#"))
        raw_url = a.get("url", "#")
        desc = a.get("description", "")
        if desc and len(desc) > 200:
            desc = desc[:197] + "..."
        desc = escape_html(desc)
        image = a.get("image", "")
        source = a.get("source", "")
        source_name = escape_html(source if isinstance(source, str) else source.get("name", ""))
        pub_date = format_date(a.get("publishedAt", ""))
        meta_parts = [p for p in [source_name, pub_date] if p]
        meta_line = " &middot; ".join(meta_parts)

        wa_link = whatsapp_share_link(raw_title, raw_url, color="rgba(255,255,255,0.5)", size="11px")

        image_html = ""
        if image:
            image_html = (
                '<tr>'
                '<td style="padding:0;font-size:0;line-height:0;">'
                f'<a href="{url}" target="_blank" style="text-decoration:none;">'
                f'<img src="{escape_html(image)}" alt="{title}" width="600" '
                'style="display:block;width:100%;max-width:600px;height:auto;border:0;">'
                '</a>'
                '</td>'
                '</tr>'
            )

        desc_html = ""
        if desc:
            desc_html = (
                '<p style="font-family:Helvetica,Arial,sans-serif;font-size:13px;'
                f'color:rgba(255,255,255,0.75);margin:6px 0 0;line-height:1.5;">{desc}</p>'
            )

        spotlight_rows += (
            f'{image_html}'
            '<tr>'
            '<td style="padding:14px 20px 16px;border-bottom:1px solid rgba(255,255,255,0.12);">'
            f'<a href="{url}" target="_blank" '
            'style="font-family:Georgia,\'Times New Roman\',serif;'
            'font-size:18px;font-weight:700;color:#ffffff;'
            f'text-decoration:none;line-height:1.3;">{title}</a>'
            f'{desc_html}'
            '<p style="font-family:Helvetica,Arial,sans-serif;font-size:11px;'
            'color:rgba(255,255,255,0.45);margin:6px 0 0;'
            f'text-transform:uppercase;letter-spacing:0.04em;">'
            f'{meta_line}'
            f' &nbsp;&middot;&nbsp; {wa_link}'
            '</p>'
            '</td>'
            '</tr>'
        )

    return (
        '<!-- Spotlight Section -->'
        '<tr>'
        '<td style="background:#1a5632;padding:0;">'
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        'style="border-collapse:collapse;">'
        '<tr>'
        '<td style="padding:16px 20px 8px;">'
        '<h2 style="font-family:Georgia,\'Times New Roman\',serif;'
        'font-size:11px;font-weight:700;color:rgba(255,255,255,0.6);'
        'margin:0;text-transform:uppercase;letter-spacing:0.1em;">'
        '&#9679; Spotlight</h2>'
        '</td>'
        '</tr>'
        f'{spotlight_rows}'
        '</table>'
        '</td>'
        '</tr>'
    )


def build_html(spotlight_articles, category_articles):
    """Build inline-CSS HTML email matching The Mutapa Times website style."""
    today = datetime.now(timezone.utc)
    date_display = today.strftime("%A, %B %d, %Y")
    total_count = len(spotlight_articles) + len(category_articles)

    # Preheader: top spotlight headline or fallback
    if spotlight_articles:
        preheader = escape_html(spotlight_articles[0].get("title", ""))
    else:
        preheader = f"Top Zimbabwe headlines from foreign press &mdash; {date_display}"

    spotlight_html = build_spotlight_html(spotlight_articles)

    # Build category article rows
    rows = ""
    for i, a in enumerate(category_articles):
        title = escape_html(a.get("title", "No title"))
        raw_title = a.get("title", "No title")
        url = escape_html(a.get("url", "#"))
        raw_url = a.get("url", "#")
        desc = a.get("description", "")
        if desc and len(desc) > 200:
            desc = desc[:197] + "..."
        desc = escape_html(desc)

        source = a.get("source", {})
        source_name = escape_html(source.get("name", "") if isinstance(source, dict) else str(source))
        pub_date = format_date(a.get("publishedAt", ""))
        category = a.get("_category", "").capitalize()

        meta_parts = [p for p in [source_name, category, pub_date] if p]
        meta_line = " &middot; ".join(meta_parts)

        wa_link = whatsapp_share_link(raw_title, raw_url, color="#6b6b6b", size="11px")

        bg = "#ffffff" if i % 2 == 0 else "#fafafa"

        desc_html = ""
        if desc:
            desc_html = (
                '<p style="font-family:Helvetica,Arial,sans-serif;font-size:13px;'
                f'color:#2c2c2c;margin:6px 0 0;line-height:1.5;">{desc}</p>'
            )

        rows += (
            '<tr>'
            f'<td style="padding:14px 20px;background:{bg};border-bottom:1px solid #e8e6e3;">'
            f'<a href="{url}" target="_blank" '
            'style="font-family:Georgia,\'Times New Roman\',serif;'
            'font-size:16px;font-weight:700;color:#1a1a1a;'
            f'text-decoration:none;line-height:1.3;">{title}</a>'
            f'{desc_html}'
            '<p style="font-family:Helvetica,Arial,sans-serif;font-size:11px;'
            f'color:#6b6b6b;margin:6px 0 0;line-height:1.4;">'
            f'{meta_line}'
            f' &nbsp;&middot;&nbsp; {wa_link}'
            '</p>'
            '</td>'
            '</tr>'
        )

    # WhatsApp share URL for the general Mutapa Times share in footer
    general_wa_text = (
        "\U0001f4f0 The Mutapa Times \u2014 Zimbabwe outside-in.\n\n"
        "Curated news from foreign press, delivered Mon/Wed/Sat.\n\n"
        "\U0001f1ff\U0001f1fc Subscribe free: https://www.mutapatimes.com"
    )
    general_wa_url = "https://wa.me/?text=" + urllib.parse.quote(general_wa_text, safe="")

    html = f"""<!DOCTYPE html>
<html lang="en" xmlns="http://www.w3.org/1999/xhtml">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <meta http-equiv="X-UA-Compatible" content="IE=edge">
  <title>The Mutapa Times Newsletter</title>
  <!--[if mso]>
  <style>* {{ font-family: Georgia, serif !important; }}</style>
  <![endif]-->
  <style>
    @media only screen and (max-width: 620px) {{
      .outer-wrap {{ padding: 0 !important; }}
      .main-table {{ width: 100% !important; }}
      .masthead-title {{ font-size: 22px !important; letter-spacing: 0.02em !important; }}
      .tagline {{ font-size: 12px !important; }}
      .masthead-cell {{ padding: 20px 16px 8px !important; }}
      .date-cell {{ padding: 8px 16px !important; }}
      .intro-cell {{ padding: 14px 16px 10px !important; }}
      .intro-text {{ font-size: 13px !important; }}
      .spotlight-header-cell {{ padding: 12px 16px 6px !important; }}
      .spotlight-text-cell {{ padding: 12px 16px 14px !important; }}
      .spotlight-title {{ font-size: 16px !important; }}
      .spotlight-desc {{ font-size: 12px !important; }}
      .section-header-cell {{ padding: 14px 16px 0 !important; }}
      .article-cell {{ padding: 12px 16px !important; }}
      .article-title {{ font-size: 15px !important; }}
      .article-desc {{ font-size: 12px !important; }}
      .cta-cell {{ padding: 20px 16px !important; }}
      .divider-cell {{ padding: 0 16px !important; }}
      .footer-cell {{ padding: 16px 16px 24px !important; }}
      .share-cell {{ padding: 16px 16px 4px !important; }}
    }}
  </style>
</head>
<body style="margin:0;padding:0;background-color:#e8e6e3;
             font-family:Helvetica,Arial,sans-serif;-webkit-font-smoothing:antialiased;">

  <!-- Preheader -->
  <div style="display:none;max-height:0;overflow:hidden;mso-hide:all;">
    {preheader}
  </div>

  <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
         style="background-color:#e8e6e3;">
    <tr>
      <td align="center" class="outer-wrap" style="padding:16px 8px;">

        <!-- Main container -->
        <table role="presentation" width="600" cellpadding="0" cellspacing="0"
               class="main-table"
               style="max-width:600px;width:100%;background:#ffffff;border-collapse:collapse;">

          <!-- Masthead -->
          <tr>
            <td class="masthead-cell" style="padding:24px 20px 8px;text-align:center;
                       border-bottom:2px solid #1a1a1a;">
              <h1 class="masthead-title"
                  style="font-family:Georgia,'Times New Roman',serif;
                         font-size:26px;font-weight:900;color:#1a1a1a;
                         margin:0;letter-spacing:0.03em;text-transform:uppercase;">
                THE MUTAPA TIMES
              </h1>
              <p class="tagline"
                 style="font-family:Georgia,'Times New Roman',serif;
                        font-size:12px;font-style:italic;color:#6b6b6b;
                        margin:4px 0 0;">
                Zimbabwe outside-in.
              </p>
            </td>
          </tr>

          <!-- Date bar -->
          <tr>
            <td class="date-cell" style="padding:10px 20px;text-align:center;
                       border-bottom:1px solid #c8c8c8;">
              <span style="font-family:Helvetica,Arial,sans-serif;
                           font-size:10px;color:#6b6b6b;
                           text-transform:uppercase;letter-spacing:0.06em;">
                {date_display} &nbsp;&middot;&nbsp; Published Mon &middot; Wed &middot; Sat
              </span>
            </td>
          </tr>

          <!-- Intro -->
          <tr>
            <td class="intro-cell" style="padding:18px 20px 12px;text-align:center;">
              <p class="intro-text"
                 style="font-family:Helvetica,Arial,sans-serif;
                        font-size:14px;color:#2c2c2c;line-height:1.5;margin:0;">
                Your briefing of the most important Zimbabwe headlines
                from foreign press. Curated for the diaspora, three times a week.
              </p>
            </td>
          </tr>

          {spotlight_html}

          <!-- Section header -->
          <tr>
            <td class="section-header-cell" style="padding:16px 20px 0;">
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
                <tr>
                  <td style="border-top:2px solid #1a1a1a;padding-top:8px;">
                    <h2 style="font-family:Georgia,'Times New Roman',serif;
                               font-size:16px;font-weight:700;color:#1a1a1a;
                               margin:0 0 2px;text-transform:uppercase;
                               letter-spacing:0.04em;">
                      Top Headlines
                    </h2>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Articles -->
          {rows}

          <!-- CTA -->
          <tr>
            <td class="cta-cell" style="padding:24px 20px;text-align:center;">
              <a href="{SITE_URL}" target="_blank"
                 style="display:inline-block;padding:10px 28px;
                        font-family:Helvetica,Arial,sans-serif;
                        font-size:12px;font-weight:700;
                        text-transform:uppercase;letter-spacing:0.08em;
                        color:#ffffff;background:#00897b;
                        text-decoration:none;">
                Read More at mutapatimes.com
              </a>
            </td>
          </tr>

          <!-- Share with a friend -->
          <tr>
            <td class="share-cell" style="padding:20px 20px 6px;text-align:center;
                       border-top:1px solid #c8c8c8;">
              <p style="font-family:Georgia,'Times New Roman',serif;
                        font-size:15px;font-weight:700;color:#1a1a1a;
                        margin:0 0 6px;">
                Share the news
              </p>
              <p style="font-family:Helvetica,Arial,sans-serif;
                        font-size:12px;color:#6b6b6b;line-height:1.5;margin:0 0 12px;">
                Know someone who should be reading this? Send them The Mutapa Times.
              </p>
              <a href="{general_wa_url}" target="_blank"
                 style="display:inline-block;padding:8px 20px;
                        font-family:Helvetica,Arial,sans-serif;
                        font-size:12px;font-weight:700;
                        color:#ffffff;background:#25d366;
                        text-decoration:none;letter-spacing:0.02em;">
                Share on WhatsApp
              </a>
              &nbsp;&nbsp;
              <a href="mailto:?subject=The%20Mutapa%20Times&amp;body=Check%20out%20The%20Mutapa%20Times%20%E2%80%94%20curated%20Zimbabwe%20news%20from%20foreign%20press%2C%20delivered%20Mon%2FWed%2FSat.%0A%0Ahttps%3A%2F%2Fwww.mutapatimes.com"
                 target="_blank"
                 style="display:inline-block;padding:8px 20px;
                        font-family:Helvetica,Arial,sans-serif;
                        font-size:12px;font-weight:700;
                        color:#ffffff;background:#1a1a1a;
                        text-decoration:none;letter-spacing:0.02em;">
                Share via Email
              </a>
            </td>
          </tr>

          <!-- Divider -->
          <tr>
            <td class="divider-cell" style="padding:0 20px;">
              <hr style="border:none;border-top:1px solid #c8c8c8;margin:16px 0 0;">
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td class="footer-cell" style="padding:16px 20px 24px;text-align:center;background:#fafafa;">
              <p style="font-family:Helvetica,Arial,sans-serif;
                        font-size:11px;color:#6b6b6b;line-height:1.5;margin:0 0 6px;">
                The Mutapa Times delivers curated Zimbabwean news from foreign press
                for the diaspora &mdash; every Monday, Wednesday, and Saturday.
              </p>
              <p style="font-family:Helvetica,Arial,sans-serif;
                        font-size:10px;color:#999999;margin:0 0 6px;">
                <a href="{SITE_URL}" style="color:#00897b;text-decoration:none;">
                  mutapatimes.com
                </a>
                &nbsp;&middot;&nbsp;
                <a href="https://twitter.com/mutapatimes" style="color:#00897b;text-decoration:none;">
                  @mutapatimes
                </a>
              </p>
              <p style="font-family:Helvetica,Arial,sans-serif;
                        font-size:10px;color:#999999;margin:0;">
                <a href="{{{{ unsubscribe }}}}" style="color:#999999;text-decoration:underline;">
                  Unsubscribe
                </a>
                &nbsp;&middot;&nbsp;
                <a href="{{{{ mirror }}}}" style="color:#999999;text-decoration:underline;">
                  View in browser
                </a>
              </p>
            </td>
          </tr>

        </table>

      </td>
    </tr>
  </table>
</body>
</html>"""
    return html, total_count


# ── Brevo campaign ──────────────────────────────────────────
def create_and_send_campaign(html_content, subject):
    """Create email campaign in Brevo and send immediately."""
    today = datetime.now(timezone.utc)
    campaign_name = f"Newsletter {today.strftime('%Y-%m-%d')}"

    # Create campaign
    payload = {
        "name": campaign_name,
        "subject": subject,
        "sender": {"name": SENDER_NAME, "email": SENDER_EMAIL},
        "htmlContent": html_content,
        "recipients": {"listIds": [BREVO_LIST_ID]},
    }
    status, resp = brevo_request("/emailCampaigns", payload)
    if status not in (200, 201):
        print(f"ERROR: Failed to create campaign: {resp}")
        sys.exit(1)

    campaign_id = resp.get("id")
    print(f"  Campaign created: ID={campaign_id}")

    # Send immediately
    status, resp = brevo_request(f"/emailCampaigns/{campaign_id}/sendNow")
    if status not in (200, 202, 204):
        print(f"ERROR: Failed to send campaign: {resp}")
        sys.exit(1)

    print(f"  Campaign {campaign_id} sent successfully!")


# ── Main ────────────────────────────────────────────────────
def main():
    if not BREVO_API_KEY:
        print("ERROR: BREVO_API_KEY not set")
        sys.exit(1)

    print("Loading spotlight articles...")
    spotlight = load_spotlight()
    print(f"  Found {len(spotlight)} spotlight articles")

    # Collect spotlight URLs to avoid duplicates in category headlines
    spotlight_urls = {a.get("url", "") for a in spotlight if a.get("url")}

    print("Loading category articles...")
    articles = load_articles(exclude_urls=spotlight_urls)
    if not articles and not spotlight:
        print("No articles found in data/*.json — skipping newsletter")
        sys.exit(0)

    top = pick_top_articles(articles)
    print(f"  Selected {len(top)} category articles for newsletter")

    print("Building email HTML...")
    html, total_count = build_html(spotlight, top)

    # Dynamic subject line: "Monday morning briefing — 15 new headlines from Zimbabwe"
    today = datetime.now(timezone.utc)
    day_label = DAY_GREETINGS.get(today.weekday(), today.strftime("%A"))
    subject = f"{day_label} briefing \u2014 {total_count} new headlines from Zimbabwe"

    print(f"  Subject: {subject}")

    print("Creating and sending campaign via Brevo...")
    create_and_send_campaign(html, subject)

    print("\nNewsletter sent successfully.")


if __name__ == "__main__":
    main()
