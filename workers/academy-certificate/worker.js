/**
 * Mutapa Times Academy - certificate emailer (Cloudflare Worker)
 *
 * Receives a completed learner's details from the Academy app and emails
 * them a styled Certificate of Completion. The front end only calls this
 * when the learner has finished every lesson and scored at least the pass
 * mark (70%), so the gate is enforced client-side; this Worker re-checks
 * the score field as a basic guard.
 *
 * Email is sent via Resend (https://resend.com). You need a verified
 * sending domain and an API key.
 *
 * Deploy:
 *   cd workers/academy-certificate
 *   npx wrangler secret put RESEND_API_KEY     # paste your Resend key
 *   # set FROM_EMAIL in wrangler.toml to a verified sender
 *   npx wrangler deploy
 * Then put the resulting URL into academy/app.js (CERT_ENDPOINT).
 */

const PASS_MARK = 70;

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

    var name = (p.name || "").toString().trim().slice(0, 60);
    var email = (p.email || "").toString().trim().slice(0, 120);
    var score = parseInt(p.score, 10) || 0;
    var date = (p.date || "").toString().trim().slice(0, 40);
    var id = (p.id || "").toString().trim().slice(0, 24);

    if (name.length < 2) return json({ error: "Name required" }, 400, ch);
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) return json({ error: "Valid email required" }, 400, ch);
    if (score < PASS_MARK) return json({ error: "Pass mark not met" }, 403, ch);

    if (!env.RESEND_API_KEY || !env.FROM_EMAIL) return json({ error: "Emailer not configured" }, 500, ch);

    var html = certificateHTML(name, score, date, id);
    var payload = {
      from: env.FROM_EMAIL,
      to: [email],
      subject: "Your Mutapa Times Academy certificate",
      html: html
    };
    if (env.CC_EMAIL) payload.bcc = [env.CC_EMAIL];

    var resp;
    try {
      resp = await fetch("https://api.resend.com/emails", {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": "Bearer " + env.RESEND_API_KEY },
        body: JSON.stringify(payload)
      });
    } catch (e) { return json({ error: "Email service unreachable" }, 502, ch); }

    if (!resp.ok) { return json({ error: "Email send failed" }, 502, ch); }
    return json({ ok: true }, 200, ch);
  }
};
