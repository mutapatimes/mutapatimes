#!/usr/bin/env python3
"""Push a plain-text email to Brevo as a *draft* campaign.

Reads a text file whose first line is `Subject: ...` followed by a
blank line and the body. POSTs to Brevo /emailCampaigns (no /sendNow)
so the campaign sits in the dashboard for manual review + send.

Usage:
    BREVO_API_KEY=xxx python3 scripts/create_draft_campaign.py \\
        content/emails/2026-05-13-going-public.txt

The body is preserved verbatim: white-space: pre-wrap in HTML +
textContent for plain-text clients. Brevo's API needs htmlContent,
so we wrap the text in a single <pre>-styled <div> to keep it
reading exactly like a typed-out personal note.
"""
import html
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

BREVO_API_KEY = os.environ.get("BREVO_API_KEY", "")
BREVO_BASE = "https://api.brevo.com/v3"
BREVO_LIST_ID = int(os.environ.get("BREVO_LIST_ID", "2"))
SENDER_NAME = os.environ.get("BREVO_SENDER_NAME", "The Mutapa Times")
SENDER_EMAIL = os.environ.get("BREVO_SENDER_EMAIL", "news@mutapatimes.com")
REPLY_TO = os.environ.get("BREVO_REPLY_TO", SENDER_EMAIL)


def brevo_request(endpoint, payload=None, method="POST"):
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
        return e.code, json.loads(body) if body.strip() else {"error": body}


def parse_email_file(path):
    with open(path) as f:
        raw = f.read()
    lines = raw.splitlines()
    if not lines or not lines[0].lower().startswith("subject:"):
        sys.exit("ERROR: first line must be `Subject: …`")
    subject = lines[0].split(":", 1)[1].strip()
    # Body starts after first blank line
    i = 1
    while i < len(lines) and lines[i].strip() == "":
        i += 1
    body = "\n".join(lines[i:]).rstrip() + "\n"
    return subject, body


def text_to_html(body):
    """Wrap the plain-text body in a typewriter-style HTML container so
    Brevo's HTML-required campaign field renders the email exactly as
    it reads in /content/emails/. Sans-serif (not monospace) — feels
    like a personal note, not a code block."""
    escaped = html.escape(body)
    return (
        '<!DOCTYPE html><html><head>'
        '<meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1.0">'
        '</head>'
        '<body style="margin:0;padding:24px 16px;background:#f5e8c8;">'
        '<div style="max-width:560px;margin:0 auto;background:#ffffff;'
        'padding:32px 28px;border:1px solid #e8e6e3;">'
        '<pre style="font-family:-apple-system,BlinkMacSystemFont,'
        '\'Helvetica Neue\',Helvetica,Arial,sans-serif;'
        'font-size:15px;line-height:1.6;color:#1a1a1a;'
        'white-space:pre-wrap;word-wrap:break-word;margin:0;">'
        f'{escaped}'
        '</pre>'
        '</div></body></html>'
    )


def main():
    if not BREVO_API_KEY:
        sys.exit("ERROR: BREVO_API_KEY env var not set")
    if len(sys.argv) < 2:
        sys.exit("Usage: create_draft_campaign.py <path/to/email.txt>")

    path = sys.argv[1]
    subject, body = parse_email_file(path)

    today = datetime.now(timezone.utc)
    campaign_name = f"Draft – {os.path.basename(path)} – {today.strftime('%Y-%m-%d %H:%M UTC')}"

    payload = {
        "name": campaign_name,
        "subject": subject,
        "sender": {"name": SENDER_NAME, "email": SENDER_EMAIL},
        "replyTo": REPLY_TO,
        "htmlContent": text_to_html(body),
        # textContent populates the plain-text MIME part automatically.
        "textContent": body,
        "recipients": {"listIds": [BREVO_LIST_ID]},
    }

    print(f"=== CREATE DRAFT CAMPAIGN ===")
    print(f"  Name:      {campaign_name}")
    print(f"  Subject:   {subject}")
    print(f"  Sender:    {SENDER_NAME} <{SENDER_EMAIL}>")
    print(f"  List ID:   {BREVO_LIST_ID}")
    print(f"  Body:      {len(body)} chars")

    status, resp = brevo_request("/emailCampaigns", payload)
    if status not in (200, 201):
        sys.exit(f"ERROR ({status}): {resp}")
    cid = resp.get("id")
    print(f"\n  ✓ Draft created — campaign id {cid}")
    print(f"  Open: https://app.brevo.com/camp/edit/{cid}/email/template")
    print(f"\n  Not sent. Review and hit Send in Brevo when ready.\n")


if __name__ == "__main__":
    main()
