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
  var verify = "https://mutapatimes.com/academy/verify/?id=" + encodeURIComponent(id);
  return '<div style="max-width:600px;margin:0 auto;font-family:Georgia,\'Times New Roman\',serif;color:#1a1a1a;">' +
    '<div style="background:#fbf8ec;border:3px solid #1a1a1a;padding:34px 30px;text-align:center;">' +
      '<div style="margin-bottom:22px;">' +
        '<span style="display:inline-block;background:#c41e1e;color:#ffffff;font-weight:bold;font-size:15px;padding:9px 11px;border-radius:4px 4px 16px 16px;vertical-align:middle;">M&middot;T</span>' +
        '<span style="display:inline-block;vertical-align:middle;text-align:left;margin-left:10px;">' +
          '<span style="display:block;font-size:22px;font-weight:bold;line-height:1;">The Mutapa Times</span>' +
          '<span style="display:block;font-size:11px;letter-spacing:4px;color:#c41e1e;font-weight:bold;margin-top:5px;">ACADEMY</span>' +
        '</span>' +
      '</div>' +
      '<p style="font-size:15px;color:#3a3a3a;margin:14px 0 12px;">The Mutapa Times Academy certifies that</p>' +
      '<p style="font-size:26px;font-weight:bold;letter-spacing:1px;text-transform:uppercase;margin:0 0 14px;">' + esc(name) + '</p>' +
      '<p style="font-size:15px;color:#3a3a3a;margin:0 0 8px;">has successfully completed</p>' +
      '<p style="font-size:21px;font-weight:bold;color:#c41e1e;margin:0 0 8px;">Professional Certificate in Journalism</p>' +
      '<p style="font-size:14px;color:#3a3a3a;margin:0 0 6px;">a self-paced online programme in the craft of journalism</p>' +
      '<p style="font-size:14px;font-weight:bold;margin:0 0 28px;">Awarded ' + esc(date) + ' &middot; Final mark ' + esc(score) + '%</p>' +
      '<div style="margin:22px auto 0;">' +
        '<div style="font-family:\'Brush Script MT\',\'Segoe Script\',cursive;font-size:26px;line-height:1;">Valentine Eluwasi</div>' +
        '<div style="width:230px;border-bottom:1px solid #1a1a1a;margin:3px auto 7px;"></div>' +
        '<div style="font-size:13px;font-weight:bold;">Valentine Eluwasi</div>' +
        '<div style="font-size:12px;color:#555555;">Founder and Director, The Mutapa Times</div>' +
      '</div>' +
      '<p style="font-size:15px;letter-spacing:5px;text-transform:uppercase;margin:26px 0 6px;">Certificate of Completion</p>' +
      '<p style="font-size:11px;letter-spacing:2px;text-transform:uppercase;color:#6a6a6a;margin:0;">Harare, Zimbabwe &middot; ' + esc(date) + '</p>' +
      '<p style="font-size:10px;letter-spacing:1px;text-transform:uppercase;color:#c41e1e;font-weight:bold;margin:14px 0 0;">Verify at mutapatimes.com/academy/verify &middot; ID ' + esc(id) + '</p>' +
    '</div>' +
    '<p style="font-family:Arial,sans-serif;font-size:13px;color:#6a6a6a;text-align:center;margin-top:16px;">' +
      'Add this to your CV and LinkedIn. Anyone can confirm it at <a href="' + verify + '">mutapatimes.com/academy/verify</a>.' +
    '</p>' +
  '</div>';
}

// ---------- Brevo contact + list management (lifecycle emails) ----------
var STUDENTS_LIST = "Mutapa Times Academy - Students";
var GRADUATES_LIST = "Mutapa Times Academy - Graduates";

async function brevo(env, method, path, body) {
  var resp = await fetch("https://api.brevo.com/v3" + path, {
    method: method,
    headers: { "api-key": env.BREVO_API_KEY, "Content-Type": "application/json", "accept": "application/json" },
    body: body ? JSON.stringify(body) : undefined
  });
  var j = null; try { j = await resp.json(); } catch (e) {}
  return { status: resp.status, ok: resp.ok, json: j };
}

async function getFolderId(env) {
  if (env.ACADEMY_FOLDER_ID) return parseInt(env.ACADEMY_FOLDER_ID, 10);
  var r = await brevo(env, "GET", "/contacts/folders?limit=50&offset=0");
  var folders = (r.json && r.json.folders) || [];
  var found = folders.filter(function (f) { return (f.name || "").toLowerCase() === "academy"; })[0];
  if (found) return found.id;
  var c = await brevo(env, "POST", "/contacts/folders", { name: "Academy" });
  if (c.json && c.json.id) return c.json.id;
  return folders.length ? folders[0].id : 1;
}

async function getOrCreateList(env, name) {
  for (var offset = 0; offset < 300; offset += 50) {
    var r = await brevo(env, "GET", "/contacts/lists?limit=50&offset=" + offset);
    var lists = (r.json && r.json.lists) || [];
    var found = lists.filter(function (l) { return (l.name || "").toLowerCase() === name.toLowerCase(); })[0];
    if (found) return found.id;
    if (lists.length < 50) break;
  }
  var folderId = await getFolderId(env);
  var c = await brevo(env, "POST", "/contacts/lists", { name: name, folderId: folderId });
  return (c.json && c.json.id) || null;
}

// Create the custom attributes if they do not exist. Errors (already exists)
// are ignored on purpose.
async function ensureAttributes(env) {
  var attrs = [["ACADEMY_SIGNUP", "date"], ["ACADEMY_WELCOME_STEP", "float"],
    ["ACADEMY_DONE", "boolean"], ["ACADEMY_DONE_DATE", "date"], ["ACADEMY_LAST_PITCH", "date"]];
  for (var i = 0; i < attrs.length; i++) {
    await brevo(env, "POST", "/contacts/attributes/normal/" + attrs[i][0], { type: attrs[i][1] });
  }
}

async function upsertContact(env, email, attributes, listIds) {
  return brevo(env, "POST", "/contacts", { email: email, attributes: attributes, listIds: listIds.filter(Boolean), updateEnabled: true });
}

function emailShell(inner) {
  return '<div style="max-width:560px;margin:0 auto;font-family:Arial,Helvetica,sans-serif;color:#1a1a1a;line-height:1.6;">' +
    '<div style="text-align:center;padding:6px 0 14px;"><span style="color:#c41e1e;font-weight:900;font-size:24px;font-family:Georgia,serif;">M&middot;T</span>' +
    '<div style="font-size:12px;letter-spacing:2px;text-transform:uppercase;color:#8a8a8a;margin-top:2px;">The Mutapa Times Academy</div></div>' +
    inner +
    '<p style="font-size:12px;color:#9a9a9a;border-top:1px solid #e2e2e2;padding-top:14px;margin-top:26px;">' +
    'You are receiving this because you enrolled at The Mutapa Times Academy. If you would rather not get these, just reply and we will remove you.</p>' +
  '</div>';
}
function btn(href, label) {
  return '<p style="margin:22px 0;"><a href="' + esc(href) + '" style="background:#c41e1e;color:#fff;text-decoration:none;font-weight:700;padding:13px 22px;border-radius:8px;display:inline-block;">' + esc(label) + '</a></p>';
}
function welcomeHTML(name, site) {
  var first = esc((name || "there").split(" ")[0]);
  return emailShell(
    '<h1 style="font-family:Georgia,serif;font-size:24px;margin:0 0 12px;">Welcome, ' + first + '.</h1>' +
    '<p>You have taken the first step towards a real byline. The Mutapa Times Academy is self-paced and built around doing the work: writing ledes, weighing sources, structuring stories, and ending with a real article you submit to our editors.</p>' +
    '<p><strong>How to get the most from it</strong></p>' +
    '<p>Set aside a short block most days rather than one long sitting. Each unit unlocks the next, and the checkpoints are meant to be a little hard. That is the point.</p>' +
    btn(site + "/academy/learn/", "Start learning") +
    '<p>Over the next week or two we will send a few short notes to keep you moving, and you will start receiving the Mutapa Times briefings so you can see how working journalists frame the day.</p>' +
    '<p>Welcome aboard.<br>The Mutapa Times Academy</p>'
  );
}
function completionHTML(name, site) {
  var first = esc((name || "there").split(" ")[0]);
  return emailShell(
    '<h1 style="font-family:Georgia,serif;font-size:24px;margin:0 0 12px;">You did it, ' + first + '.</h1>' +
    '<p>You have completed The Mutapa Times Academy and earned your certificate. Now the real work begins, and it is the best part.</p>' +
    '<p><strong>You can now pitch stories to The Mutapa Times, and earn your own monthly column.</strong></p>' +
    '<p>Here is how to pitch:</p>' +
    '<p>Email <a href="mailto:news@mutapatimes.com">news@mutapatimes.com</a> with the subject line <strong>Pitch: your story in one line</strong>. In three or four sentences tell us what the story is, why it matters now, and who you would talk to. If it is a fit, an editor will commission it and run it with your byline.</p>' +
    btn(site + "/academy/learn/#/submit", "Submit an article now") +
    '<p>We will send you a reminder each month so pitching becomes a habit. The contributors who show up regularly are the ones who get the column.</p>' +
    '<p style="border-top:1px solid #e2e2e2;padding-top:18px;margin-top:24px;"><strong>One more thing: build your CV.</strong> The Academy now has a free CV builder with your qualification and final mark already filled in. Create it in minutes and download it as a PDF.</p>' +
    btn(site + "/academy/learn/#/cv", "Build your CV") +
    '<p>Congratulations, and welcome to the newsroom.<br>The Mutapa Times</p>'
  );
}

async function handleEnrol(p, env, ch) {
  var name = (p.name || "").toString().trim().slice(0, 80);
  var email = (p.email || "").toString().trim().slice(0, 120);
  if (name.length < 2) return json({ error: "Name required" }, 400, ch);
  if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) return json({ error: "Valid email required" }, 400, ch);
  if (!env.BREVO_API_KEY || !env.FROM_EMAIL) return json({ error: "Emailer not configured" }, 500, ch);

  var site = env.SITE_URL || "https://mutapatimes.com";
  var today = new Date().toISOString().slice(0, 10);
  try {
    await ensureAttributes(env);
    var studentsList = await getOrCreateList(env, STUDENTS_LIST);
    var newsletterList = env.NEWSLETTER_LIST_ID ? parseInt(env.NEWSLETTER_LIST_ID, 10) : null;
    await upsertContact(env, email,
      { FIRSTNAME: name.split(" ")[0], ACADEMY_SIGNUP: today, ACADEMY_WELCOME_STEP: 1 },
      [studentsList, newsletterList]);
  } catch (e) { console.error("enrol contact", e && e.message); }

  try { await sendEmail(env, { to: [email], subject: "Welcome to The Mutapa Times Academy", html: welcomeHTML(name, site) }); }
  catch (e) { console.error("welcome email", e && e.message); }
  return json({ ok: true }, 200, ch);
}

async function handleComplete(p, env, ch) {
  var name = (p.name || "").toString().trim().slice(0, 80);
  var email = (p.email || "").toString().trim().slice(0, 120);
  if (name.length < 2) return json({ error: "Name required" }, 400, ch);
  if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) return json({ error: "Valid email required" }, 400, ch);
  if (!env.BREVO_API_KEY || !env.FROM_EMAIL) return json({ error: "Emailer not configured" }, 500, ch);

  var site = env.SITE_URL || "https://mutapatimes.com";
  var today = new Date().toISOString().slice(0, 10);
  try {
    await ensureAttributes(env);
    var gradsList = await getOrCreateList(env, GRADUATES_LIST);
    var newsletterList = env.NEWSLETTER_LIST_ID ? parseInt(env.NEWSLETTER_LIST_ID, 10) : null;
    await upsertContact(env, email,
      { FIRSTNAME: name.split(" ")[0], ACADEMY_DONE: true, ACADEMY_DONE_DATE: today, ACADEMY_LAST_PITCH: today },
      [gradsList, newsletterList]);
  } catch (e) { console.error("complete contact", e && e.message); }

  try { await sendEmail(env, { to: [email], subject: "You did it. Now pitch The Mutapa Times.", html: completionHTML(name, site) }); }
  catch (e) { console.error("completion email", e && e.message); }
  return json({ ok: true }, 200, ch);
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

    // Lifecycle: capture a new student and send the welcome email.
    if (p && p.kind === "enrol") return handleEnrol(p, env, ch);
    // Lifecycle: mark a graduate and send the pitch invitation.
    if (p && p.kind === "complete") return handleComplete(p, env, ch);
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
