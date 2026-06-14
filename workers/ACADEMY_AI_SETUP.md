# Academy AI assessment + article submission — setup

The Academy works fully offline. These two Cloudflare Workers add the AI
features. The API keys live only in the Workers, never in the browser.

## What each Worker does

- **academy-grade** — grades written answers with Google Gemini
  (`gemini-2.0-flash`, the same model the rest of the site uses) against
  fixed, server-side rubrics. Powers:
  - the short `write` exercises (e.g. the crypto lede),
  - the in-exam ~500-word CCBA story (`exam-ccba-500`),
  - the final capstone article feedback (`{ kind: "submission" }`).
  Needs secret `GEMINI_API_KEY` (the same key value as your GitHub Actions
  `GEMINI_API_KEY` secret; Cloudflare cannot read GitHub secrets, so it must
  be set on the Worker too).

- **academy-certificate** — sends email with Brevo (the same account that
  sends the newsletter). Powers:
  - emailing the Certificate of Completion,
  - emailing the final capstone article to the editors
    (`{ kind: "submission" }` → `SUBMIT_TO`, default news@mutapatimes.com).
  Needs secret `BREVO_API_KEY` (same value as the GitHub Actions secret) and
  a verified `FROM_EMAIL` sender in Brevo.

## Deploy

```bash
# 1. Grader (AI feedback)
cd workers/academy-grade
npx wrangler secret put GEMINI_API_KEY        # paste the same Gemini key value
npx wrangler deploy                            # note the *.workers.dev URL

# 2. Emailer (certificate + submissions)
cd ../academy-certificate
npx wrangler secret put BREVO_API_KEY          # paste the same Brevo key value
# FROM_EMAIL in wrangler.toml must be a verified Brevo sender
npx wrangler deploy                            # note the *.workers.dev URL
```

## Wire the front end

Open `academy/app.js` and set the two constants near the top to the URLs
from the deploys above:

```js
var GRADE_ENDPOINT = "https://academy-grade.YOURNAME.workers.dev"; // AI feedback
var CERT_ENDPOINT  = "https://academy-certificate.YOURNAME.workers.dev"; // cert + submissions
```

Then bump the `app.js?v=` query string in `academy/learn/index.html` and
`academy/review/index.html` so browsers pick up the change.

## Graceful fallback

If the endpoints are left blank or a call fails:
- writing tasks fall back to a self-mark checklist plus the editor's model
  answer,
- the final submission shows a self-check and tells the learner to email
  their article to news@mutapatimes.com.

So nothing breaks if the Workers are not yet deployed.

## Notes

- The model defaults to `gemini-2.0-flash`; override with a `MODEL` var.
- `ALLOWED_ORIGIN` defaults to `https://mutapatimes.com`.
- The in-exam writing task is **feedback only**: it never affects the 80%
  pass mark (the engine excludes `write` items from scoring).
- The final submission route (`#/submit`) is gated behind passing the
  course (it requires the certificate to be earned first).
