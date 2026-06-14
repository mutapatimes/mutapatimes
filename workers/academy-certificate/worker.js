/**
 * Mutapa Times Academy - certificate emailer (Cloudflare Worker)
 *
 * Receives a completed learner's details from the Academy app and emails
 * them a styled Certificate of Completion. The front end only calls this
 * when the learner has finished every lesson and scored at least the pass
 * mark (70%), so the gate is enforced client-side; this Worker re-checks
 * the score field as a basic guard.
 *
 * Email is sent via Brevo (https://brevo.com), reusing the same account that
 * sends the newsletter. The same BREVO_API_KEY value as the GitHub Actions
 * secret must be set on this Worker (Cloudflare cannot read GitHub secrets).
 *
 * Deploy:
 *   cd workers/academy-certificate
 *   npx wrangler secret put BREVO_API_KEY      # paste the same Brevo key value
 *   # FROM_EMAIL in wrangler.toml must be a verified Brevo sender
 *   npx wrangler deploy
 * Then put the resulting URL into academy/app.js (CERT_ENDPOINT).
 */

const PASS_MARK = 70;

// FROM_EMAIL may be "Name <email>" or just "email"; Brevo wants them split.
function parseSender(from) {
  from = String(from || "");
  var m = from.match(/^\s*(.*?)\s*<([^>]+)>\s*$/);
  if (m) return { name: m[1] || "The Mutapa Times Academy", email: m[2].trim() };
  return { name: "The Mutapa Times Academy", email: from.trim() };
}

async function sendEmail(env, opts) {
  var body = {
    sender: parseSender(env.FROM_EMAIL),
    to: opts.to.map(function (e) { return { email: e }; }),
    subject: opts.subject,
    htmlContent: opts.html
  };
  if (opts.replyTo) body.replyTo = { email: opts.replyTo };
  if (opts.bcc && opts.bcc.length) body.bcc = opts.bcc.map(function (e) { return { email: e }; });
  return fetch("https://api.brevo.com/v3/smtp/email", {
    method: "POST",
    headers: { "Content-Type": "application/json", "accept": "application/json", "api-key": env.BREVO_API_KEY },
    body: JSON.stringify(body)
  });
}

function cors(origin, allowed) {
  var ok = allowed === "*" || origin === allowed;
  return {
    "Access-Control-Allow-Origin": ok ? (origin || allowed) : allowed,
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Max-Age": "86400"
  };
}
function json(body, status, headers) {
  return new Response(JSON.stringify(body), { status: status, headers: Object.assign({ "Content-Type": "application/json" }, headers) });
}
function esc(s) {
  return String(s || "").replace(/[&<>"']/g, function (c) {
    return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
  });
}

function submissionHTML(p) {
  var paras = String(p.body || "").split(/\n+/).map(function (x) { return x.trim(); }).filter(Boolean)
    .map(function (x) { return '<p style="margin:0 0 12px;">' + esc(x) + '</p>'; }).join("");
  return '<div style="max-width:640px;margin:0 auto;font-family:Georgia,serif;color:#1a1a1a;">' +
    '<p style="font-family:Arial,sans-serif;font-size:12px;letter-spacing:2px;text-transform:uppercase;color:#c41e1e;font-weight:700;">Mutapa Times Academy &middot; Article submission</p>' +
    '<table style="width:100%;font-family:Arial,sans-serif;font-size:13px;color:#444;border-collapse:collapse;margin:0 0 18px;">' +
      '<tr><td style="padding:4px 8px 4px 0;color:#8a8a8a;">From</td><td style="padding:4px 0;">' + esc(p.byline || p.name) + '</td></tr>' +
      '<tr><td style="padding:4px 8px 4px 0;color:#8a8a8a;">Email</td><td style="padding:4px 0;">' + esc(p.email) + '</td></tr>' +
      (p.imageUrl ? '<tr><td style="padding:4px 8px 4px 0;color:#8a8a8a;">Image</td><td style="padding:4px 0;"><a href="' + esc(p.imageUrl) + '">' + esc(p.imageUrl) + '</a></td></tr>' : '') +
      (p.imageCaption ? '<tr><td style="padding:4px 8px 4px 0;color:#8a8a8a;">Caption</td><td style="padding:4px 0;">' + esc(p.imageCaption) + '</td></tr>' : '') +
    '</table>' +
    '<h1 style="font-size:26px;line-height:1.2;margin:0 0 6px;">' + esc(p.headline) + '</h1>' +
    (p.summary ? '<p style="font-size:16px;color:#555;margin:0 0 18px;">' + esc(p.summary) + '</p>' : '') +
    '<hr style="border:none;border-top:1px solid #ddd;margin:0 0 18px;">' +
    '<div style="font-size:16px;line-height:1.6;">' + paras + '</div>' +
    (p.bio ? '<hr style="border:none;border-top:1px solid #ddd;margin:18px 0;"><p style="font-family:Arial,sans-serif;font-size:13px;color:#666;"><strong>About the author.</strong> ' + esc(p.bio) + '</p>' : '') +
  '</div>';
}

async function sendSubmission(p, env, ch) {
  var name = (p.name || p.byline || "").toString().trim().slice(0, 80);
  var email = (p.email || "").toString().trim().slice(0, 120);
  var headline = (p.headline || "").toString().trim().slice(0, 200);
  var body = (p.body || "").toString().trim().slice(0, 12000);

  if (name.length < 2) return json({ error: "Name required" }, 400, ch);
  if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) return json({ error: "Valid email required" }, 400, ch);
  if (headline.length < 3) return json({ error: "Headline required" }, 400, ch);
  if (body.split(/\s+/).filter(Boolean).length < 80) return json({ error: "Article too short" }, 400, ch);

  if (!env.BREVO_API_KEY || !env.FROM_EMAIL) return json({ error: "Emailer not configured" }, 500, ch);

  var to = (env.SUBMIT_TO || "news@mutapatimes.com").split(",").map(function (s) { return s.trim(); }).filter(Boolean);
  var html = submissionHTML({
    name: name, byline: (p.byline || name), email: email,
    headline: headline, summary: (p.summary || "").toString().slice(0, 600),
    body: body, bio: (p.bio || "").toString().slice(0, 800),
    imageUrl: (p.imageUrl || "").toString().slice(0, 400),
    imageCaption: (p.imageCaption || "").toString().slice(0, 300)
  });

  var resp;
  try {
    resp = await sendEmail(env, { to: to, replyTo: email, subject: "Academy submission: " + headline, html: html });
  } catch (e) { return json({ error: "Email service unreachable" }, 502, ch); }

  if (!resp.ok) { console.error("submission email", resp.status); return json({ error: "Email send failed" }, 502, ch); }
  return json({ ok: true }, 200, ch);
}

function certificateHTML(name, score, date, id) {
  return '<div style="max-width:560px;margin:0 auto;font-family:Georgia,serif;">' +
    '<div style="position:relative;background:#ffffff;border:2px solid #121212;border-radius:6px;padding:36px 28px;text-align:center;">' +
      '<div style="color:#c41e1e;font-weight:900;font-size:26px;">M&middot;T</div>' +
      '<div style="font-weight:900;font-size:22px;margin-top:4px;">The Mutapa Times Academy</div>' +
      '<div style="font-size:11px;letter-spacing:3px;text-transform:uppercase;color:#8a8a8a;margin:6px 0 26px;">Certificate of Completion</div>' +
      '<div style="font-size:14px;color:#6a6a6a;">This certifies that</div>' +
      '<div style="font-weight:700;font-size:30px;color:#c41e1e;margin:6px 0 14px;">' + esc(name) + '</div>' +
      '<div style="font-size:15px;color:#2a2a2a;max-width:420px;margin:0 auto 26px;">has completed the Mutapa Times Academy course in journalism for Zimbabwe and the diaspora, passing with a score of ' + esc(score) + '%.</div>' +
      '<div style="display:flex;justify-content:space-between;border-top:1px solid #d4d4d4;padding-top:14px;font-size:12px;color:#8a8a8a;">' +
        '<span>Awarded ' + esc(date) + '</span><span>ID ' + esc(id) + '</span>' +
      '</div>' +
    '</div>' +
    '<p style="font-family:Arial,sans-serif;font-size:13px;color:#6a6a6a;text-align:center;margin-top:18px;">' +
      'Add this to your CV and LinkedIn. List <strong>The Mutapa Times Academy</strong> under Education.' +
    '</p>' +
  '</div>';
}

export default {
  async fetch(request, env) {
    var allowed = env.ALLOWED_ORIGIN || "https://mutapatimes.com";
    var origin = request.headers.get("Origin") || "";
    var ch = cors(origin, allowed);

    if (request.method === "OPTIONS") return new Response(null, { status: 204, headers: ch });
    if (request.method !== "POST") return json({ error: "Method not allowed" }, 405, ch);

    var p;
    try { p = await request.json(); } catch (e) { return json({ error: "Invalid JSON" }, 400, ch); }

    // Final-capstone article submission: email it to the editors.
    if (p && p.kind === "submission") return sendSubmission(p, env, ch);

    var name = (p.name || "").toString().trim().slice(0, 60);
    var email = (p.email || "").toString().trim().slice(0, 120);
    var score = parseInt(p.score, 10) || 0;
    var date = (p.date || "").toString().trim().slice(0, 40);
    var id = (p.id || "").toString().trim().slice(0, 24);

    if (name.length < 2) return json({ error: "Name required" }, 400, ch);
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) return json({ error: "Valid email required" }, 400, ch);
    if (score < PASS_MARK) return json({ error: "Pass mark not met" }, 403, ch);

    if (!env.BREVO_API_KEY || !env.FROM_EMAIL) return json({ error: "Emailer not configured" }, 500, ch);

    var html = certificateHTML(name, score, date, id);
    var resp;
    try {
      resp = await sendEmail(env, {
        to: [email],
        subject: "Your Mutapa Times Academy certificate",
        html: html,
        bcc: env.CC_EMAIL ? [env.CC_EMAIL] : null
      });
    } catch (e) { return json({ error: "Email service unreachable" }, 502, ch); }

    if (!resp.ok) { console.error("certificate email", resp.status); return json({ error: "Email send failed" }, 502, ch); }
    return json({ ok: true }, 200, ch);
  }
};
