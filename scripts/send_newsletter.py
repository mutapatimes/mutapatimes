#!/usr/bin/env python3
"""
Send the biweekly Mutapa Times newsletter via Brevo API.
Reads data/*.json, builds an HTML email, creates a campaign, and sends it.
Stdlib only — no pip dependencies.
"""
import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone

# ── Configuration ───────────────────────────────────────────
BREVO_API_KEY = os.environ.get("BREVO_API_KEY", "")
BREVO_BASE = "https://api.brevo.com/v3"
BREVO_LIST_ID = int(os.environ.get("BREVO_LIST_ID", "2"))
DATA_DIR = "data"

SENDER_NAME = "The Mutapa Times"
SENDER_EMAIL = "mutapatimes@gmail.com"
SITE_URL = "https://www.mutapatimes.com"

CATEGORIES = ["business", "technology", "entertainment", "sports", "science", "health"]
MAX_PER_CATEGORY = 2
MAX_TOTAL = 12


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
def load_articles():
    """Read all data/*.json files, merge, deduplicate, sort by date."""
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

    # Deduplicate by URL
    seen = set()
    unique = []
    for a in all_articles:
        url = a.get("url", "")
        if url and url not in seen:
            seen.add(url)
            unique.append(a)

    unique.sort(key=lambda a: a.get("publishedAt", ""), reverse=True)
    return unique


def pick_top_articles(articles):
    """Pick top articles with category diversity."""
    cat_counts = {c: 0 for c in CATEGORIES}
    picked = []
    for a in articles:
        cat = a.get("_category", "")
        if cat_counts.get(cat, 0) >= MAX_PER_CATEGORY:
            continue
        picked.append(a)
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
        # Handle both ISO formats: "2026-02-17T22:12:33Z" and "2026-02-17 22:12:33"
        clean = date_str.replace("Z", "+00:00").replace(" ", "T")
        if "+" not in clean and clean.count("T") == 1:
            clean += "+00:00"
        dt = datetime.fromisoformat(clean)
        return dt.strftime("%B %d, %Y")
    except (ValueError, TypeError):
        return ""


def build_html(articles):
    """Build inline-CSS HTML email matching The Mutapa Times style."""
    today = datetime.now(timezone.utc)
    date_display = today.strftime("%A, %B %d, %Y")

    # Build article rows
    rows = ""
    for i, a in enumerate(articles):
        title = escape_html(a.get("title", "No title"))
        url = escape_html(a.get("url", "#"))
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

        bg = "#ffffff" if i % 2 == 0 else "#fafafa"

        desc_html = ""
        if desc:
            desc_html = (
                f'<p style="font-family:Helvetica,Arial,sans-serif;font-size:14px;'
                f'color:#2c2c2c;margin:8px 0 0;line-height:1.5;">{desc}</p>'
            )

        rows += f"""
        <tr>
          <td style="padding:20px 30px;background:{bg};border-bottom:1px solid #e8e6e3;">
            <a href="{url}" target="_blank"
               style="font-family:'Playfair Display',Georgia,'Times New Roman',serif;
                      font-size:18px;font-weight:700;color:#1a1a1a;
                      text-decoration:none;line-height:1.3;">
              {title}
            </a>
            <p style="font-family:Helvetica,Arial,sans-serif;font-size:13px;
                      color:#6b6b6b;margin:6px 0 0;line-height:1.4;">
              {meta_line}
            </p>
            {desc_html}
          </td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <title>The Mutapa Times Newsletter</title>
  <!--[if mso]>
  <style>* {{ font-family: Georgia, serif !important; }}</style>
  <![endif]-->
</head>
<body style="margin:0;padding:0;background-color:#e8e6e3;
             font-family:Helvetica,Arial,sans-serif;-webkit-font-smoothing:antialiased;">

  <!-- Preheader -->
  <div style="display:none;max-height:0;overflow:hidden;mso-hide:all;">
    Top Zimbabwe headlines from foreign press &mdash; {date_display}
  </div>

  <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
         style="background-color:#e8e6e3;">
    <tr>
      <td align="center" style="padding:20px 10px;">

        <!-- Main container -->
        <table role="presentation" width="600" cellpadding="0" cellspacing="0"
               style="max-width:600px;width:100%;background:#ffffff;border-collapse:collapse;">

          <!-- Masthead -->
          <tr>
            <td style="padding:30px 30px 10px;text-align:center;
                       border-bottom:2px solid #1a1a1a;">
              <h1 style="font-family:'Playfair Display',Georgia,'Times New Roman',serif;
                         font-size:32px;font-weight:900;color:#1a1a1a;
                         margin:0;letter-spacing:0.04em;text-transform:uppercase;">
                THE MUTAPA TIMES
              </h1>
              <p style="font-family:'Playfair Display',Georgia,'Times New Roman',serif;
                        font-size:14px;font-style:italic;color:#6b6b6b;
                        margin:6px 0 0;">
                Zimbabwe outside-in.
              </p>
            </td>
          </tr>

          <!-- Date bar -->
          <tr>
            <td style="padding:12px 30px;text-align:center;
                       border-bottom:1px solid #c8c8c8;">
              <span style="font-family:Helvetica,Arial,sans-serif;
                           font-size:11px;color:#6b6b6b;
                           text-transform:uppercase;letter-spacing:0.08em;">
                {date_display} &nbsp;&middot;&nbsp; Biweekly Newsletter
              </span>
            </td>
          </tr>

          <!-- Intro -->
          <tr>
            <td style="padding:24px 30px 16px;text-align:center;">
              <p style="font-family:Helvetica,Arial,sans-serif;
                        font-size:15px;color:#2c2c2c;line-height:1.6;margin:0;">
                Your biweekly briefing of the most important Zimbabwe headlines
                from foreign press. Curated for the diaspora.
              </p>
            </td>
          </tr>

          <!-- Section header -->
          <tr>
            <td style="padding:0 30px;">
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
                <tr>
                  <td style="border-top:2px solid #1a1a1a;padding-top:10px;">
                    <h2 style="font-family:'Playfair Display',Georgia,'Times New Roman',serif;
                               font-size:20px;font-weight:700;color:#1a1a1a;
                               margin:0 0 4px;text-transform:uppercase;
                               letter-spacing:0.05em;">
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
            <td style="padding:28px 30px;text-align:center;">
              <a href="{SITE_URL}" target="_blank"
                 style="display:inline-block;padding:12px 32px;
                        font-family:Helvetica,Arial,sans-serif;
                        font-size:13px;font-weight:700;
                        text-transform:uppercase;letter-spacing:0.1em;
                        color:#ffffff;background:#1a1a1a;
                        text-decoration:none;">
                Read More at mutapatimes.com
              </a>
            </td>
          </tr>

          <!-- Divider -->
          <tr>
            <td style="padding:0 30px;">
              <hr style="border:none;border-top:1px solid #c8c8c8;margin:0;">
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="padding:20px 30px 30px;text-align:center;background:#fafafa;">
              <p style="font-family:Helvetica,Arial,sans-serif;
                        font-size:12px;color:#6b6b6b;line-height:1.6;margin:0 0 8px;">
                The Mutapa Times delivers curated Zimbabwean news from foreign press
                for the diaspora.
              </p>
              <p style="font-family:Helvetica,Arial,sans-serif;
                        font-size:11px;color:#999999;margin:0 0 8px;">
                <a href="{SITE_URL}" style="color:#00897b;text-decoration:none;">
                  mutapatimes.com
                </a>
                &nbsp;&middot;&nbsp;
                <a href="https://twitter.com/mutapatimes" style="color:#00897b;text-decoration:none;">
                  @mutapatimes
                </a>
              </p>
              <p style="font-family:Helvetica,Arial,sans-serif;
                        font-size:11px;color:#999999;margin:0;">
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
    return html


# ── Brevo campaign ──────────────────────────────────────────
def create_and_send_campaign(html_content):
    """Create email campaign in Brevo and send immediately."""
    today = datetime.now(timezone.utc)
    subject = f"The Mutapa Times \u2014 {today.strftime('%B %d, %Y')}"
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

    print("Loading articles...")
    articles = load_articles()
    if not articles:
        print("No articles found in data/*.json — skipping newsletter")
        sys.exit(0)

    top = pick_top_articles(articles)
    print(f"  Selected {len(top)} articles for newsletter")

    print("Building email HTML...")
    html = build_html(top)

    print("Creating and sending campaign via Brevo...")
    create_and_send_campaign(html)

    print("\nNewsletter sent successfully.")


if __name__ == "__main__":
    main()
