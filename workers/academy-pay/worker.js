/**
 * Mutapa Times Academy - enrolment + payment (Cloudflare Worker)
 *
 * Handles the whole signup-to-access flow with Paynow, the standard
 * Zimbabwean gateway (EcoCash, OneMoney, Zimswitch, Visa, Mastercard):
 *   - POST {action:"create"}  start a payment, return the Paynow browserurl
 *   - POST {action:"status"}  confirm payment, return an access token
 *   - GET/POST ?action=result Paynow's server-to-server confirmation
 *
 * On payment it also: issues a referral code, credits the referrer,
 * applies a friend discount, and fires the newsletter webhook.
 *
 * Needs a KV namespace bound as ACADEMY and these secrets/vars:
 *   secrets:  PAYNOW_ID, PAYNOW_KEY, ACCESS_SECRET
 *   vars:     PRICE, REF_DISCOUNT, SITE_URL, ALLOWED_ORIGIN,
 *             NEWSLETTER_WEBHOOK (optional)
 *
 * Deploy:
 *   cd workers/academy-pay
 *   npx wrangler kv namespace create ACADEMY        # then add the id to wrangler.toml
 *   npx wrangler secret put PAYNOW_ID
 *   npx wrangler secret put PAYNOW_KEY
 *   npx wrangler secret put ACCESS_SECRET           # any long random string
 *   npx wrangler deploy
 * Put the deployed URL into PAY_ENDPOINT in academy/index.html and
 * academy/welcome/index.html.
 */

const PAYNOW_INITIATE = "https://www.paynow.co.zw/interface/initiatetransaction";
const PAID_STATUSES = ["paid", "awaiting delivery", "delivered"];

// ---------- crypto helpers ----------
async function digestHex(algo, str) {
  const buf = await crypto.subtle.digest(algo, new TextEncoder().encode(str));
  return [...new Uint8Array(buf)].map(b => b.toString(16).padStart(2, "0")).join("");
}
async function sha512Upper(str) { return (await digestHex("SHA-512", str)).toUpperCase(); }
async function hmacHex(key, msg) {
  const k = await crypto.subtle.importKey("raw", new TextEncoder().encode(key), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  const sig = await crypto.subtle.sign("HMAC", k, new TextEncoder().encode(msg));
  return [...new Uint8Array(sig)].map(b => b.toString(16).padStart(2, "0")).join("");
}
function randHex(n) { const a = new Uint8Array(n); crypto.getRandomValues(a); return [...a].map(b => b.toString(16).padStart(2, "0")).join(""); }

// ---------- KV helpers ----------
async function getJSON(env, key) { const v = await env.ACADEMY.get(key); return v ? JSON.parse(v) : null; }
async function putJSON(env, key, val) { await env.ACADEMY.put(key, JSON.stringify(val)); }

// ---------- http helpers ----------
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

// ---------- Paynow ----------
async function paynowInitiate(env, order) {
  // Field order matters: it is the order hashed.
  const fields = {
    resulturl: order.resulturl,
    returnurl: order.returnurl,
    reference: order.reference,
    amount: order.amount,
    id: env.PAYNOW_ID,
    additionalinfo: "Mutapa Times Academy enrolment",
    authemail: order.email,
    status: "Message"
  };
  const hash = await sha512Upper(Object.values(fields).join("") + env.PAYNOW_KEY);
  const body = new URLSearchParams(Object.assign({}, fields, { hash }));
  const resp = await fetch(PAYNOW_INITIATE, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: body.toString()
  });
  return new URLSearchParams(await resp.text());
}
async function paynowPoll(pollurl) {
  const resp = await fetch(pollurl);
  return new URLSearchParams(await resp.text());
}

async function makeReferralCode(env, email) {
  const h = await digestHex("SHA-256", email + "|" + (env.ACCESS_SECRET || "salt"));
  return h.slice(0, 8).toUpperCase();
}
async function accessToken(env, order) {
  return hmacHex(env.ACCESS_SECRET || "key", order.email + "|" + order.paidTs);
}

// Idempotent: marks order paid, issues codes, credits referrer, newsletter.
async function finalize(env, order) {
  if (order.status !== "paid") {
    order.status = "paid";
    order.paidTs = Date.now();

    let user = (await getJSON(env, "user:" + order.email)) || { referrals: 0, paid: false };
    if (!user.referralCode) {
      user.referralCode = await makeReferralCode(env, order.email);
      await env.ACADEMY.put("code:" + user.referralCode, order.email);
    }
    user.paid = true;
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

    // Paynow server-to-server confirmation.
    if (url.searchParams.get("action") === "result") {
      let reference = url.searchParams.get("reference");
      if (!reference && request.method === "POST") {
        try { const form = await request.formData(); reference = form.get("reference"); } catch (e) {}
      }
      if (reference) {
        const order = await getJSON(env, "order:" + reference);
        if (order && order.pollurl) {
          const st = (await paynowPoll(order.pollurl)).get("status") || "";
          if (PAID_STATUSES.indexOf(st.toLowerCase()) !== -1) await finalize(env, order);
        }
      }
      return new Response("ok", { status: 200 });
    }

    if (request.method !== "POST") return json({ error: "Method not allowed" }, 405, ch);

    let body;
    try { body = await request.json(); } catch (e) { return json({ error: "Invalid JSON" }, 400, ch); }

    // ---- create ----
    if (body.action === "create") {
      if (!env.PAYNOW_ID || !env.PAYNOW_KEY) return json({ error: "Payments not configured" }, 500, ch);
      const name = (body.name || "").toString().trim().slice(0, 60);
      const email = (body.email || "").toString().trim().slice(0, 120);
      const ref = (body.ref || "").toString().trim().slice(0, 16).toUpperCase();
      if (name.length < 2) return json({ error: "Name required" }, 400, ch);
      if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) return json({ error: "Valid email required" }, 400, ch);

      const price = parseFloat(env.PRICE || "15");
      const refDiscount = parseFloat(env.REF_DISCOUNT || "0.15");
      let amount = price;
      if (ref) {
        const refEmail = await env.ACADEMY.get("code:" + ref);
        if (refEmail && refEmail !== email) amount = price * (1 - refDiscount);
      }
      amount = amount.toFixed(2);

      const site = env.SITE_URL || "https://mutapatimes.com";
      const reference = "MTA-" + Date.now().toString(36).toUpperCase() + "-" + randHex(3).toUpperCase();
      const order = {
        reference, email, name, ref, amount, status: "created", createdTs: Date.now(),
        returnurl: site + "/academy/welcome/?reference=" + reference,
        resulturl: url.origin + "/?action=result&reference=" + reference
      };

      const res = await paynowInitiate(env, order);
      if ((res.get("status") || "").toLowerCase() !== "ok" || !res.get("browserurl")) {
        return json({ error: res.get("error") || "Could not start payment" }, 502, ch);
      }
      order.pollurl = res.get("pollurl");
      await putJSON(env, "order:" + reference, order);
      return json({ browserurl: res.get("browserurl"), reference }, 200, ch);
    }

    // ---- status ----
    if (body.action === "status") {
      const reference = (body.reference || "").toString().trim();
      const order = await getJSON(env, "order:" + reference);
      if (!order) return json({ paid: false }, 200, ch);

      if (order.status !== "paid" && order.pollurl) {
        const st = (await paynowPoll(order.pollurl)).get("status") || "";
        if (PAID_STATUSES.indexOf(st.toLowerCase()) !== -1) await finalize(env, order);
      }
      if (order.status === "paid") {
        const finalized = await finalize(env, order); // idempotent, ensures referralCode present
        return json({
          paid: true, token: await accessToken(env, finalized),
          referralCode: finalized.referralCode || "", email: finalized.email, name: finalized.name
        }, 200, ch);
      }
      return json({ paid: false }, 200, ch);
    }

    return json({ error: "Unknown action" }, 400, ch);
  }
};
