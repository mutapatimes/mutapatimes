/**
 * Mutapa Times Academy - enrolment + payment (Cloudflare Worker)
 *
 * Uses Lemon Squeezy (a merchant of record) so payment works from the UK
 * with no Zimbabwe documents, and accepts global cards, PayPal and
 * Apple/Google Pay. Lemon Squeezy handles VAT/tax and pays out to a UK
 * bank.
 *
 *   - POST {action:"create"}    build a Lemon Squeezy checkout URL
 *   - POST {action:"status"}    confirm payment, return an access token
 *   - POST ?action=webhook      Lemon Squeezy order webhook (server-side)
 *
 * On payment it issues a referral code, credits the referrer, and fires
 * the newsletter webhook. The friend discount is applied by attaching a
 * Lemon Squeezy discount code to the checkout link.
 *
 * Needs a KV namespace bound as ACADEMY and these secrets/vars:
 *   secrets:  LS_WEBHOOK_SECRET, ACCESS_SECRET
 *   vars:     LS_BUY_LINK, LS_DISCOUNT_CODE (optional), PRICE,
 *             REF_DISCOUNT, SITE_URL, ALLOWED_ORIGIN,
 *             NEWSLETTER_WEBHOOK (optional)
 *
 * Setup:
 *   1. In Lemon Squeezy create a product (one-time) and copy its buy
 *      link (e.g. https://YOURSTORE.lemonsqueezy.com/buy/UUID). Set the
 *      product's "Redirect to URL after purchase" to
 *      https://mutapatimes.com/academy/welcome/
 *   2. (Optional) create a discount code (e.g. FRIEND15, 15% off) for
 *      referrals and set LS_DISCOUNT_CODE.
 *   3. Add a webhook: URL = <worker-url>/?action=webhook, signing secret
 *      = LS_WEBHOOK_SECRET, event = order_created.
 *   4. Deploy and put the worker URL into PAY_ENDPOINT in
 *      academy/index.html and academy/welcome/index.html.
 */

const PAID = "paid";

async function digestHex(algo, str) {
  const buf = await crypto.subtle.digest(algo, new TextEncoder().encode(str));
  return [...new Uint8Array(buf)].map(b => b.toString(16).padStart(2, "0")).join("");
}
async function hmacHex(key, msg) {
  const k = await crypto.subtle.importKey("raw", new TextEncoder().encode(key), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  const sig = await crypto.subtle.sign("HMAC", k, new TextEncoder().encode(msg));
  return [...new Uint8Array(sig)].map(b => b.toString(16).padStart(2, "0")).join("");
}
function randHex(n) { const a = new Uint8Array(n); crypto.getRandomValues(a); return [...a].map(b => b.toString(16).padStart(2, "0")).join(""); }

async function getJSON(env, key) { const v = await env.ACADEMY.get(key); return v ? JSON.parse(v) : null; }
async function putJSON(env, key, val) { await env.ACADEMY.put(key, JSON.stringify(val)); }

function cors(origin, allowed) {
  const ok = allowed === "*" || origin === allowed;
  return {
    "Access-Control-Allow-Origin": ok ? (origin || allowed) : allowed,
    "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Max-Age": "86400"
  };
}
function json(body, status, headers) {
  return new Response(JSON.stringify(body), { status, headers: Object.assign({ "Content-Type": "application/json" }, headers || {}) });
}

async function makeReferralCode(env, email) {
  const h = await digestHex("SHA-256", email + "|" + (env.ACCESS_SECRET || "salt"));
  return h.slice(0, 8).toUpperCase();
}
async function accessToken(env, order) {
  return hmacHex(env.ACCESS_SECRET || "key", (order.email || "").toLowerCase() + "|" + order.paidTs);
}
// Verify a token a learner presents (for progress sync). The token is bound to
// their email and the timestamp they paid, both stored on the user record.
async function verifyToken(env, email, token) {
  email = (email || "").toLowerCase();
  if (!email || !token) return false;
  const user = await getJSON(env, "user:" + email);
  if (!user || !user.paid || !user.paidTs) return false;
  const expected = await hmacHex(env.ACCESS_SECRET || "key", email + "|" + user.paidTs);
  return token === expected;
}

// Idempotent: mark paid, issue codes, credit referrer, newsletter.
async function finalize(env, order, override) {
  override = override || {};
  if (order.status !== PAID) {
    order.status = PAID;
    order.paidTs = Date.now();
    if (override.email) order.email = override.email;
    if (override.name) order.name = override.name;
    order.email = (order.email || "").toLowerCase();

    let user = (await getJSON(env, "user:" + order.email)) || { referrals: 0, paid: false };
    if (!user.referralCode) {
      user.referralCode = await makeReferralCode(env, order.email);
      await env.ACADEMY.put("code:" + user.referralCode, order.email);
    }
    user.paid = true;
    user.paidTs = order.paidTs;        // needed to verify access tokens later
    if (order.name) user.name = order.name;
    await putJSON(env, "user:" + order.email, user);
    order.referralCode = user.referralCode;

    if (order.ref) {
      const refEmail = await env.ACADEMY.get("code:" + order.ref);
      if (refEmail && refEmail !== order.email) {
        let ru = (await getJSON(env, "user:" + refEmail)) || { referrals: 0 };
        ru.referrals = (ru.referrals || 0) + 1;
        await putJSON(env, "user:" + refEmail, ru);
      }
    }
    await putJSON(env, "order:" + order.reference, order);

    if (env.NEWSLETTER_WEBHOOK) {
      try {
        await fetch(env.NEWSLETTER_WEBHOOK, {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email: order.email, name: order.name, tags: ["academy", order.ref ? "referred" : "direct"] })
        });
      } catch (e) {}
    }
  } else if (!order.referralCode) {
    const user = await getJSON(env, "user:" + order.email);
    if (user && user.referralCode) order.referralCode = user.referralCode;
  }
  return order;
}

export default {
  async fetch(request, env) {
    const allowed = env.ALLOWED_ORIGIN || "https://mutapatimes.com";
    const ch = cors(request.headers.get("Origin") || "", allowed);
    const url = new URL(request.url);

    if (request.method === "OPTIONS") return new Response(null, { status: 204, headers: ch });
    if (!env.ACADEMY) return json({ error: "Storage not configured" }, 500, ch);

    // ---- Lemon Squeezy webhook (server-to-server) ----
    if (url.searchParams.get("action") === "webhook") {
      const raw = await request.text();
      const sig = request.headers.get("X-Signature") || "";
      const expected = await hmacHex(env.LS_WEBHOOK_SECRET || "", raw);
      if (sig !== expected) return new Response("bad signature", { status: 401 });
      let body; try { body = JSON.parse(raw); } catch (e) { return new Response("bad json", { status: 400 }); }
      const event = body && body.meta && body.meta.event_name;
      if (event === "order_created") {
        const custom = (body.meta && body.meta.custom_data) || {};
        const reference = custom.ref_purchase;
        const attrs = (body.data && body.data.attributes) || {};
        if (reference) {
          let order = await getJSON(env, "order:" + reference);
          if (!order) {
            order = { reference, email: attrs.user_email || "", name: attrs.user_name || "", ref: (custom.referrer || "").toUpperCase(), status: "created", createdTs: Date.now() };
          }
          await finalize(env, order, { email: attrs.user_email, name: attrs.user_name });
        }
      }
      return new Response("ok", { status: 200 });
    }

    if (request.method !== "POST") return json({ error: "Method not allowed" }, 405, ch);

    let body;
    try { body = await request.json(); } catch (e) { return json({ error: "Invalid JSON" }, 400, ch); }

    // ---- create ----
    if (body.action === "create") {
      if (!env.LS_BUY_LINK) return json({ error: "Payments not configured" }, 500, ch);
      const name = (body.name || "").toString().trim().slice(0, 60);
      const email = (body.email || "").toString().trim().slice(0, 120);
      const ref = (body.ref || "").toString().trim().slice(0, 16).toUpperCase();
      if (name.length < 2) return json({ error: "Name required" }, 400, ch);
      if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) return json({ error: "Valid email required" }, 400, ch);
      const emailLc = email.toLowerCase();

      const reference = "MTA-" + Date.now().toString(36).toUpperCase() + "-" + randHex(3).toUpperCase();
      let referrerValid = false;
      if (ref) {
        const refEmail = await env.ACADEMY.get("code:" + ref);
        if (refEmail && refEmail !== emailLc) referrerValid = true;
      }
      await putJSON(env, "order:" + reference, { reference, email: emailLc, name, ref: referrerValid ? ref : "", status: "created", createdTs: Date.now() });

      const p = [
        "checkout[email]=" + encodeURIComponent(emailLc),
        "checkout[custom][ref_purchase]=" + encodeURIComponent(reference)
      ];
      if (referrerValid) {
        p.push("checkout[custom][referrer]=" + encodeURIComponent(ref));
        if (env.LS_DISCOUNT_CODE) p.push("checkout[discount_code]=" + encodeURIComponent(env.LS_DISCOUNT_CODE));
      }
      const sep = env.LS_BUY_LINK.indexOf("?") >= 0 ? "&" : "?";
      return json({ checkoutUrl: env.LS_BUY_LINK + sep + p.join("&"), reference }, 200, ch);
    }

    // ---- status ----
    if (body.action === "status") {
      const reference = (body.reference || "").toString().trim();
      const order = await getJSON(env, "order:" + reference);
      if (!order) return json({ paid: false }, 200, ch);
      if (order.status === PAID) {
        const finalized = await finalize(env, order);
        return json({
          paid: true, token: await accessToken(env, finalized),
          referralCode: finalized.referralCode || "", email: finalized.email, name: finalized.name
        }, 200, ch);
      }
      return json({ paid: false }, 200, ch);
    }

    // ---- redeem (manual / local payment access code) ----
    if (body.action === "redeem") {
      const code = (body.code || "").toString().trim().toUpperCase().slice(0, 32);
      const name = (body.name || "").toString().trim().slice(0, 60);
      const email = (body.email || "").toString().trim().slice(0, 120);
      const ref = (body.ref || "").toString().trim().slice(0, 16).toUpperCase();
      if (!code) return json({ error: "Enter your access code" }, 400, ch);
      if (name.length < 2) return json({ error: "Name required" }, 400, ch);
      if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) return json({ error: "Valid email required" }, 400, ch);
      const emailLc = email.toLowerCase();

      const rec = await getJSON(env, "acccode:" + code);
      if (!rec) return json({ error: "That code is not valid" }, 400, ch);

      if (rec.status === "used") {
        // Allow the original buyer to re-unlock on another device.
        if (rec.email && rec.email === emailLc) {
          const user = await getJSON(env, "user:" + emailLc);
          const order = { email: emailLc, paidTs: rec.paidTs || Date.now() };
          return json({ ok: true, token: await accessToken(env, order), referralCode: (user && user.referralCode) || "", email: emailLc }, 200, ch);
        }
        return json({ error: "That code has already been used" }, 400, ch);
      }

      const reference = "AC-" + code + "-" + randHex(2).toUpperCase();
      let order = { reference, email: emailLc, name, ref, status: "created", createdTs: Date.now(), via: "code" };
      order = await finalize(env, order, { email: emailLc, name });
      rec.status = "used"; rec.email = emailLc; rec.reference = reference; rec.paidTs = order.paidTs;
      await env.ACADEMY.put("acccode:" + code, JSON.stringify(rec));
      return json({ ok: true, token: await accessToken(env, order), referralCode: order.referralCode || "", email: emailLc }, 200, ch);
    }

    // ---- gencode (admin only): create access codes for local buyers ----
    if (body.action === "gencode") {
      if (!env.ADMIN_KEY || body.adminKey !== env.ADMIN_KEY) return json({ error: "Unauthorized" }, 401, ch);
      const count = Math.min(parseInt(body.count, 10) || 1, 100);
      const note = (body.note || "").toString().slice(0, 80);
      const prefix = (body.prefix || "MT").toString().toUpperCase().replace(/[^A-Z0-9]/g, "").slice(0, 6) || "MT";
      const codes = [];
      for (let i = 0; i < count; i++) {
        const c = prefix + randHex(3).toUpperCase();
        await env.ACADEMY.put("acccode:" + c, JSON.stringify({ status: "unused", note, createdTs: Date.now() }));
        codes.push(c);
      }
      return json({ codes }, 200, ch);
    }

    // ---- verify (does this email + token still have access?) ----
    if (body.action === "verify") {
      const ok = await verifyToken(env, body.email, body.token);
      return json({ ok }, 200, ch);
    }

    // ---- progress-get (cross-device resume) ----
    if (body.action === "progress-get") {
      if (!await verifyToken(env, body.email, body.token)) return json({ error: "Unauthorized" }, 401, ch);
      const rec = await getJSON(env, "progress:" + (body.email || "").toLowerCase());
      return json({ ok: true, progress: rec ? rec.data : null, updatedTs: rec ? rec.updatedTs : 0 }, 200, ch);
    }

    // ---- progress-put (cross-device resume; last write wins by updatedTs) ----
    if (body.action === "progress-put") {
      if (!await verifyToken(env, body.email, body.token)) return json({ error: "Unauthorized" }, 401, ch);
      const data = body.progress;
      if (!data || typeof data !== "object") return json({ error: "Bad progress" }, 400, ch);
      const updatedTs = parseInt(body.updatedTs, 10) || Date.now();
      const key = "progress:" + (body.email || "").toLowerCase();
      const existing = await getJSON(env, key);
      if (existing && existing.updatedTs > updatedTs) {
        // The server already has a newer copy (another device). Return it.
        return json({ ok: true, newer: true, progress: existing.data, updatedTs: existing.updatedTs }, 200, ch);
      }
      await putJSON(env, key, { data, updatedTs });
      return json({ ok: true, updatedTs }, 200, ch);
    }

    return json({ error: "Unknown action" }, 400, ch);
  }
};
