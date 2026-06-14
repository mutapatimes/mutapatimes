# Mutapa Times Academy — MVP runbook

A self-paced, fully automated journalism micro-lesson with **AI-graded
writing feedback**. No live sessions, no manual marking. This MVP exists
to validate one thing: does instant, rubric-based feedback on a student's
writing feel useful enough to build the rest around.

Decisions locked for v1: **AI credential only** (no human byline),
**one-time unlock** monetisation (added in step 2), **thin MVP first**.

## What's in this MVP

| Piece | File | Cost to run |
|---|---|---|
| Lesson page (reading + quiz + writing) | `academy/index.html` | free (static) |
| Auto-graded multiple choice | in the page, client-side | free |
| AI writing grader | `workers/academy-grade/worker.js` | per-call Anthropic API |
| Worker config | `workers/academy-grade/wrangler.toml` | free tier covers low volume |

The page is `noindex` for now (unfinished content; keep it out of the
sitemap and Google until launch).

## Architecture

```
Browser (/academy/)  --POST {exerciseId, answer}-->  Cloudflare Worker
                                                       |
                                          holds ANTHROPIC_API_KEY (secret)
                                          holds the exercise rubric
                                                       |
                                              Anthropic API (Claude)
                                                       |
        <-- {score, verdict, strengths, improvements, model_answer} --
```

The API key and the grading rubric live only in the Worker. The browser
never sees either, so the key can't leak and a student can't tamper with
how they're graded.

## Deploy (about 10 minutes)

You need: an **Anthropic API key** (console.anthropic.com, separate from
Claude Code) and your **Cloudflare** login (the site is already behind it).

1. Install Wrangler if needed: `npm i -g wrangler` (or use `npx`).
2. Authenticate: `npx wrangler login`.
3. From the worker folder, set the key as a secret and deploy:
   ```
   cd workers/academy-grade
   npx wrangler secret put ANTHROPIC_API_KEY    # paste the key when prompted
   npx wrangler deploy
   ```
4. Wrangler prints a URL like `https://academy-grade.<your-subdomain>.workers.dev`.
   Put it into `academy/index.html` at the `GRADE_ENDPOINT` constant
   (near the bottom, in the `<script>`).
5. Commit and push. Visit `https://mutapatimes.com/academy/` and try the
   writing exercise.

Optional: map the Worker to `https://mutapatimes.com/api/grade` via a
Cloudflare route instead of the workers.dev URL (tidier, same origin).

## Cost control

- `MODEL` is set to `claude-sonnet-4-6` in `wrangler.toml`. For cheaper
  grading at slightly lower nuance, switch to `claude-haiku-4-5-20251001`.
- Each grade is one short request (about 700 output tokens cap). Low.
- The Worker caps answer length and only accepts known `exerciseId`s.
- Before public launch, add basic rate limiting (Cloudflare rules or a
  per-IP counter) so the endpoint can't be hammered.

## What's next (after the loop is validated)

1. **One-time unlock** — Stripe Checkout; a second Worker handles the
   webhook and flips a "paid" flag. Gate the AI feedback behind it.
2. **Accounts + progress** — Supabase (auth + a progress table). Lets
   people resume and unlocks the credential.
3. **Gamification** — streak, XP, lesson map. The retention loop.
4. **More content** — more lessons and writing exercises as data; the
   grader already takes any `exerciseId` you add to `EXERCISES`.
5. **App** — the page wraps into the existing Capacitor shell for free.

## Certificate of completion (with email)

When a learner finishes every lesson and scores at least **70%** on the
graded questions, the home screen shows a "Claim your certificate"
button. The certificate page lets them put their name on a printable
certificate (Download / Print works with zero setup) and, if configured,
email it to themselves.

Scoring: each graded exercise (everything except the self-check writing
tasks) records correct/incorrect in localStorage. The pass mark is
`PASS_MARK` in `academy/app.js`.

### Enable emailing (optional)

The printable certificate works immediately. To turn on email delivery:

1. Create a **Resend** account (resend.com) and verify a sending domain
   (e.g. mutapatimes.com). Create an API key.
2. Set `FROM_EMAIL` in `workers/academy-certificate/wrangler.toml` to a
   verified sender on that domain.
3. Deploy the Worker:
   ```
   cd workers/academy-certificate
   npx wrangler secret put RESEND_API_KEY
   npx wrangler deploy
   ```
4. Put the printed URL into `academy/app.js` at `CERT_ENDPOINT`.

If `CERT_ENDPOINT` is left blank, the email button politely tells the
learner to use Download / Print instead. (Alternative provider: swap the
Resend call in `worker.js` for MailChannels if you prefer.)

## Landing page, payment and referrals

The Academy now has a public front door and a paid signup flow built for
Zimbabwe.

| Page | Path | Purpose |
|---|---|---|
| Landing / sales | `/academy/` | Sells the course, signup + pay |
| Welcome | `/academy/welcome/` | Confirms payment, unlocks course, shows referral link |
| Course | `/academy/learn/` | The course app (gateable) |

### Payment (Paynow)

Stripe does not pay out to Zimbabwe, so payments use **Paynow**, which
accepts EcoCash, OneMoney, Zimswitch, Visa and Mastercard. This covers
local mobile money and diaspora cards in one flow. (Pesepay is a drop-in
alternative if you prefer; swap the initiate/poll calls in the Worker.)

Flow: landing form -> `academy-pay` Worker creates a Paynow payment ->
browser redirects to Paynow -> on return, `/academy/welcome/` polls the
Worker until paid -> the Worker issues an access token, fires the
newsletter webhook, and returns a referral link.

### Setup

1. Create a Paynow merchant account and get your Integration ID + Key.
2. Deploy the Worker:
   ```
   cd workers/academy-pay
   npx wrangler kv namespace create ACADEMY     # paste the id into wrangler.toml
   npx wrangler secret put PAYNOW_ID
   npx wrangler secret put PAYNOW_KEY
   npx wrangler secret put ACCESS_SECRET        # any long random string
   npx wrangler deploy
   ```
3. Put the deployed Worker URL into `PAY_ENDPOINT` in BOTH
   `academy/index.html` and `academy/welcome/index.html`.
4. Set the price in `wrangler.toml` (`PRICE`) and on the landing page
   (`PRICE` constant, for display).
5. Test in Paynow's test mode first. If hash checks fail, confirm the
   field order in `paynowInitiate` matches your Paynow account.

Until `PAY_ENDPOINT` is set, the landing page just captures interest.

### Gating the course

`academy/app.js` has `REQUIRE_ACCESS = false` by default, so the course
stays open while you set up payments. Flip it to `true` once Paynow is
live: visitors without a paid access token are redirected to `/academy/`.
The token is set on the welcome page after a confirmed payment.

### Referrals

Every buyer gets a referral code (shown on the welcome page as a link
like `/academy/?ref=ABC12345`). A friend who arrives with `?ref=` sees a
discount (default 15%, set by `REF_DISCOUNT`), and the Worker credits the
referrer's count in KV. To see who has referred how much, read the
`user:<email>` keys in the ACADEMY KV namespace. Rewarding top referrers
is currently manual; it can be automated later.

### Newsletter trigger

On a confirmed payment the Worker POSTs `{email, name, tags}` to
`NEWSLETTER_WEBHOOK`. Point it at Mailchimp (via a small proxy), Zapier,
Make, or your own endpoint. If unset, payment still works; no newsletter
call is made.

## UPDATE: payment provider is Lemon Squeezy (not Paynow)

Paynow needs a Zimbabwean merchant identity, which we do not have. The
payment Worker now uses **Lemon Squeezy**, a merchant of record: it signs
up from the UK, accepts global cards, PayPal and Apple/Google Pay,
handles VAT, and pays out to a UK bank. (The Paynow section above is kept
only for reference; the code in `workers/academy-pay` is Lemon Squeezy.)

Local EcoCash is not covered by this route; it can be added later as a
separate option.

### Lemon Squeezy setup

1. Create a Lemon Squeezy account and store, and a one-time **product**
   for the course at your price.
2. Copy the product's **buy link** into `LS_BUY_LINK` in `wrangler.toml`,
   and set the product's "Redirect to URL after purchase" to
   `https://mutapatimes.com/academy/welcome/`.
3. (Optional, for referrals) create a discount code such as `FRIEND15`
   (15% off) and set `LS_DISCOUNT_CODE`.
4. Add a **webhook**: URL `https://<your-worker>/?action=webhook`, signing
   secret of your choice, event `order_created`. Put that secret in
   `LS_WEBHOOK_SECRET`.
5. Deploy:
   ```
   cd workers/academy-pay
   npx wrangler kv namespace create ACADEMY     # paste id into wrangler.toml
   npx wrangler secret put LS_WEBHOOK_SECRET
   npx wrangler secret put ACCESS_SECRET        # any long random string
   npx wrangler deploy
   ```
6. Put the worker URL into `PAY_ENDPOINT` in `academy/index.html` and
   `academy/welcome/index.html`.

Flow: landing creates an order and a Lemon Squeezy checkout link (with the
referral code + friend discount attached) -> buyer pays on Lemon Squeezy
-> Lemon Squeezy's webhook tells the Worker it is paid (which credits the
referrer and fires the newsletter) -> the welcome page polls the Worker,
unlocks the course and shows the buyer's referral link.

## Local payment via access codes (Mukuru, EcoCash, bank, cash)

Mukuru is a remittance service, not a checkout gateway, so it cannot be
wired in like a card processor. Instead the landing page has a "Paying
from Zimbabwe?" section where a local buyer enters a one-time **access
code** that unlocks the course. You collect the local payment however
works (Mukuru, EcoCash via someone in Zim, bank, cash), confirm it, then
hand over a code.

Set `ADMIN_KEY` (a long random string) as a Worker secret:
```
npx wrangler secret put ADMIN_KEY
```

Generate codes (returns the codes to hand out):
```
curl -X POST "https://<your-worker>/" -H "Content-Type: application/json" \
  -d '{"action":"gencode","adminKey":"YOUR_ADMIN_KEY","count":5,"prefix":"MT","note":"March batch"}'
```

Or create one by hand in KV:
```
npx wrangler kv key put --binding=ACADEMY "acccode:MT123ABC" '{"status":"unused"}'
```

Each code is single-use, ties to the buyer's email (so they can re-unlock
on another device), credits any referrer, and fires the newsletter, just
like a card sale. Tune the local instructions text in `academy/index.html`
(`#localInstructions`).

## Easiest way to make codes: the admin page

`/academy/admin/` is a password-protected page for generating access
codes with a button, no Terminal needed. Set its `PAY_ENDPOINT` to the
same Worker URL as the landing page. Enter your `ADMIN_KEY`, choose how
many codes, click Generate, and copy the codes to send to local buyers.
The page is safe to leave online because nothing generates without the
admin password (checked by the Worker). It is noindex.
