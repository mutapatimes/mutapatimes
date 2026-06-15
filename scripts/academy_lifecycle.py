#!/usr/bin/env python3
"""
Mutapa Times Academy - email lifecycle (daily cron).

Drives the timed drip emails for Academy students using Brevo contacts and
custom attributes. The immediate emails (welcome #1 at signup, the completion
pitch invite) are sent by the academy-certificate Worker; this script sends
everything that is time based:

  Welcome series (students who have not finished):
    - day 2  : read like a journalist  (WELCOME_STEP -> 2)
    - day 5  : where this leads, the byline  (WELCOME_STEP -> 3)
    - day 14 : gentle "still time to finish" nudge  (WELCOME_STEP -> 4)

  Graduates (ACADEMY_DONE = true):
    - a pitch reminder every PITCH_INTERVAL_DAYS (default 30)

It also makes sure every student is on the briefings (newsletter) list.

State lives in Brevo contact attributes, so the job is idempotent and sends at
most one email per contact per run. Runs on GitHub Actions with BREVO_API_KEY
(and BREVO_LIST_ID for the briefings list). Stdlib only.
"""

import json
import os
import sys
import urllib.request
import urllib.error
import urllib.parse
from datetime import date, datetime

BREVO_API_KEY = os.environ.get("BREVO_API_KEY", "")
BREVO_BASE = "https://api.brevo.com/v3"
NEWSLETTER_LIST_ID = int(os.environ.get("BREVO_LIST_ID", "2"))
SITE_URL = os.environ.get("SITE_URL", "https://mutapatimes.com")
SENDER_NAME = os.environ.get("SENDER_NAME", "The Mutapa Times Academy")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "news@mutapatimes.com")
PITCH_INTERVAL_DAYS = int(os.environ.get("PITCH_INTERVAL_DAYS", "30"))
DRY_RUN = os.environ.get("DRY_RUN", "") == "1"

STUDENTS_LIST = "Mutapa Times Academy - Students"
GRADUATES_LIST = "Mutapa Times Academy - Graduates"

ATTRS = [
    ("ACADEMY_SIGNUP", "date"),
    ("ACADEMY_WELCOME_STEP", "float"),
    ("ACADEMY_DONE", "boolean"),
    ("ACADEMY_DONE_DATE", "date"),
    ("ACADEMY_LAST_PITCH", "date"),
]


# ── Brevo API ───────────────────────────────────────────────
def brevo(endpoint, payload=None, method="POST"):
    url = BREVO_BASE + endpoint
    headers = {
        "api-key": BREVO_API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, (json.loads(body) if body.strip() else {})
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        return e.code, (json.loads(body) if body.strip() else {"_raw": body})
    except Exception as e:  # noqa: BLE001
        return 0, {"_error": str(e)}


def ensure_attributes():
    for name, typ in ATTRS:
        # 400 means it already exists; that is fine.
        brevo("/contacts/attributes/normal/" + name, {"type": typ}, "POST")


def find_list_id(name):
    offset = 0
    while offset < 400:
        status, data = brevo(
            "/contacts/lists?limit=50&offset=%d" % offset, None, "GET"
        )
        lists = (data or {}).get("lists", []) or []
        for l in lists:
            if (l.get("name") or "").lower() == name.lower():
                return l.get("id")
        if len(lists) < 50:
            break
        offset += 50
    return None


def list_contacts(list_id):
    out = []
    if not list_id:
        return out
    offset = 0
    while True:
        status, data = brevo(
            "/contacts/lists/%d/contacts?limit=500&offset=%d" % (list_id, offset),
            None,
            "GET",
        )
        contacts = (data or {}).get("contacts", []) or []
        out.extend(contacts)
        if len(contacts) < 500:
            break
        offset += 500
    return out


def update_attributes(email, attributes):
    ident = urllib.parse.quote(email, safe="")
    return brevo("/contacts/" + ident, {"attributes": attributes}, "PUT")


def add_to_list(list_id, emails):
    if not emails:
        return
    for i in range(0, len(emails), 150):
        brevo(
            "/contacts/lists/%d/contacts/add" % list_id,
            {"emails": emails[i : i + 150]},
            "POST",
        )


def send_email(to_email, to_name, subject, html):
    if DRY_RUN:
        print("  [dry-run] would send '%s' to %s" % (subject, to_email))
        return True
    payload = {
        "sender": {"name": SENDER_NAME, "email": SENDER_EMAIL},
        "to": [{"email": to_email, "name": to_name or to_email}],
        "subject": subject,
        "htmlContent": html,
    }
    status, _ = brevo("/smtp/email", payload, "POST")
    ok = status in (200, 201)
    if not ok:
        print("  send failed (%s) to %s" % (status, to_email))
    return ok


# ── dates ───────────────────────────────────────────────────
def parse_day(value):
    if not value:
        return None
    s = str(value)[:10]
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        return None


def days_since(value):
    d = parse_day(value)
    if not d:
        return None
    return (date.today() - d).days


# ── email templates ─────────────────────────────────────────
def esc(s):
    return (
        str(s or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def shell(inner):
    return (
        '<div style="max-width:560px;margin:0 auto;font-family:Arial,Helvetica,sans-serif;color:#1a1a1a;line-height:1.6;">'
        '<div style="text-align:center;padding:6px 0 14px;">'
        '<span style="color:#c41e1e;font-weight:900;font-size:24px;font-family:Georgia,serif;">M&middot;T</span>'
        '<div style="font-size:12px;letter-spacing:2px;text-transform:uppercase;color:#8a8a8a;margin-top:2px;">The Mutapa Times Academy</div></div>'
        + inner
        + '<p style="font-size:12px;color:#9a9a9a;border-top:1px solid #e2e2e2;padding-top:14px;margin-top:26px;">'
        "You are receiving this because you enrolled at The Mutapa Times Academy. If you would rather not get these, just reply and we will remove you.</p>"
        "</div>"
    )


def button(href, label):
    return (
        '<p style="margin:22px 0;"><a href="%s" style="background:#c41e1e;color:#fff;text-decoration:none;font-weight:700;padding:13px 22px;border-radius:8px;display:inline-block;">%s</a></p>'
        % (esc(href), esc(label))
    )


def first_name(name):
    return esc((name or "there").split(" ")[0])


def tpl_welcome_started(name):
    return shell(
        '<h1 style="font-family:Georgia,serif;font-size:22px;margin:0 0 12px;">A reporter reads everything, %s.</h1>'
        "<p>One habit separates people who get published from people who do not: they read like a journalist. Notice the lede. Ask who is quoted, and who is missing. Spot the claim that is not yet proven.</p>"
        "<p>Bring that eye back to the course. The units on sourcing and the inverted pyramid will land harder once you are reading the news this way.</p>"
        % first_name(name)
        + button(SITE_URL + "/academy/learn/", "Continue the course")
        + "<p>Keep going.<br>The Mutapa Times Academy</p>"
    )


def tpl_welcome_byline(name):
    return shell(
        '<h1 style="font-family:Georgia,serif;font-size:22px;margin:0 0 12px;">Where this leads, %s.</h1>'
        "<p>The Academy is not the destination. Finish the course and pass the final exam, and you can pitch stories to The Mutapa Times and earn your own monthly column.</p>"
        "<p>That means a published byline you can show universities and employers, and a reference from a real newsroom. Graduates also get a built-in CV builder that lists the qualification and final mark, ready to download as a PDF.</p>"
        % first_name(name)
        + button(SITE_URL + "/academy/learn/", "Pick up where you left off")
        + "<p>We are looking forward to reading you.<br>The Mutapa Times Academy</p>"
    )


def tpl_nudge(name):
    return shell(
        '<h1 style="font-family:Georgia,serif;font-size:22px;margin:0 0 12px;">Still time to finish, %s.</h1>'
        "<p>Your place at the Academy is still here. Even fifteen minutes gets you through a lesson, and the certificate plus the path to a byline are waiting at the end.</p>"
        % first_name(name)
        + button(SITE_URL + "/academy/learn/", "Resume the course")
        + "<p>The Mutapa Times Academy</p>"
    )


def tpl_pitch(name):
    return shell(
        '<h1 style="font-family:Georgia,serif;font-size:22px;margin:0 0 12px;">What is your story this month, %s?</h1>'
        "<p>This is your monthly nudge to pitch The Mutapa Times. Strong contributors keep a running list of ideas, then send the best one.</p>"
        "<p>Pitch in three or four sentences: what the story is, why now, and who you would talk to. Email <a href=\"mailto:news@mutapatimes.com\">news@mutapatimes.com</a> with the subject line <strong>Pitch: your story in one line</strong>.</p>"
        % first_name(name)
        + button(
            "mailto:news@mutapatimes.com?subject=" + urllib.parse.quote("Pitch: "),
            "Send a pitch",
        )
        + "<p>Land enough of these and the monthly column is yours.<br>The Mutapa Times</p>"
    )


# welcome schedule: (min_days_since_signup, step_number, template)
WELCOME_SCHEDULE = [
    (2, 2, tpl_welcome_started),
    (5, 3, tpl_welcome_byline),
    (14, 4, tpl_nudge),
]


# ── main ────────────────────────────────────────────────────
def attr_get(contact, key):
    a = contact.get("attributes") or {}
    # Brevo returns attribute keys uppercase, but be tolerant.
    if key in a:
        return a[key]
    for k, v in a.items():
        if k.upper() == key.upper():
            return v
    return None


def is_done(contact):
    v = attr_get(contact, "ACADEMY_DONE")
    return v is True or str(v).lower() == "true"


def main():
    if not BREVO_API_KEY:
        print("ERROR: BREVO_API_KEY not set")
        return 1

    ensure_attributes()
    students_id = find_list_id(STUDENTS_LIST)
    grads_id = find_list_id(GRADUATES_LIST)
    print("Students list: %s   Graduates list: %s" % (students_id, grads_id))

    # Merge contacts from both lists, dedup by email.
    contacts = {}
    for c in list_contacts(students_id) + list_contacts(grads_id):
        email = (c.get("email") or "").lower()
        if not email:
            continue
        if email in contacts:
            contacts[email].setdefault("listIds", [])
            contacts[email]["listIds"] = list(
                set((contacts[email].get("listIds") or []) + (c.get("listIds") or []))
            )
            # merge attributes (later wins for set keys)
            merged = dict(contacts[email].get("attributes") or {})
            merged.update(c.get("attributes") or {})
            contacts[email]["attributes"] = merged
        else:
            contacts[email] = c
    print("Processing %d contact(s)" % len(contacts))

    # Make sure every student receives the briefings.
    missing_newsletter = [
        c.get("email")
        for c in contacts.values()
        if NEWSLETTER_LIST_ID not in (c.get("listIds") or [])
    ]
    if missing_newsletter:
        print("Adding %d student(s) to the briefings list" % len(missing_newsletter))
        if not DRY_RUN:
            add_to_list(NEWSLETTER_LIST_ID, missing_newsletter)

    today_iso = date.today().isoformat()
    sent = 0

    for email, c in contacts.items():
        name = attr_get(c, "FIRSTNAME") or (c.get("attributes") or {}).get("FNAME") or ""

        if is_done(c):
            last = attr_get(c, "ACADEMY_LAST_PITCH") or attr_get(c, "ACADEMY_DONE_DATE")
            gap = days_since(last)
            if gap is None or gap >= PITCH_INTERVAL_DAYS:
                if send_email(email, name, "Your monthly pitch to The Mutapa Times", tpl_pitch(name)):
                    update_attributes(email, {"ACADEMY_LAST_PITCH": today_iso})
                    sent += 1
            continue

        # Welcome series for students still working through the course.
        signup = attr_get(c, "ACADEMY_SIGNUP") or c.get("createdAt")
        days = days_since(signup)
        if days is None:
            continue
        try:
            step = int(float(attr_get(c, "ACADEMY_WELCOME_STEP") or 1))
        except (TypeError, ValueError):
            step = 1

        # highest scheduled step that is due and not yet sent
        target = None
        for min_days, step_no, tpl in WELCOME_SCHEDULE:
            if days >= min_days and step_no > step:
                target = (step_no, tpl)
        if target:
            step_no, tpl = target
            subjects = {2: "Read like a journalist", 3: "Where the Academy leads", 4: "Still time to finish your course"}
            if send_email(email, name, subjects.get(step_no, "The Mutapa Times Academy"), tpl(name)):
                update_attributes(email, {"ACADEMY_WELCOME_STEP": step_no})
                sent += 1

    print("Done. Sent %d email(s)." % sent)
    return 0


if __name__ == "__main__":
    sys.exit(main())
