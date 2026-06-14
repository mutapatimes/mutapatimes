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
