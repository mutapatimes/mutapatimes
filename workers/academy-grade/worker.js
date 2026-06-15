/**
 * Mutapa Times Academy - writing grader (Cloudflare Worker)
 *
 * Two jobs, both keeping the AI key server-side, never in the browser:
 *   1. Grade a student's short writing answer against a fixed, server-side
 *      rubric (POST { exerciseId, answer }).
 *   2. Grade a full article submission for the final capstone, section by
 *      section (POST { kind: "submission", headline, summary, body, ... }).
 * The briefs and rubrics live here so a student cannot tamper with how they
 * are graded.
 *
 * Uses Google Gemini (gemini-2.0-flash), the same model the rest of the site
 * uses. The GEMINI_API_KEY GitHub Actions secret cannot be read by Cloudflare,
 * so set the same key value here once:
 *
 * Deploy:
 *   cd workers/academy-grade
 *   npx wrangler secret put GEMINI_API_KEY   # paste the same key value
 *   npx wrangler deploy
 * Then put the resulting *.workers.dev URL into academy/app.js
 * (the GRADE_ENDPOINT constant).
 */

const GEMINI_MODEL = "gemini-2.5-flash";
const DEFAULT_MAX_CHARS = 800;

// CCBA facts, shared by the in-exam essay and the capstone nut graph so the
// grader checks answers against the same reality the student was shown.
const CCBA_FACTS = [
  "Coca-Cola Beverages Africa (CCBA) in Kenya, with partner Emerging Leaders, runs Uwezo Kwa Vijana (Skills for Youth), a six-month programme launched in January 2026.",
  "It says it aims to reach 3,000 participants in 2026. The headline says it 'supports 3,000 youth', but the body says it 'aims to reach' 3,000, so 3,000 is a target, not a result.",
  "It trains young people in confidence, financial literacy and starting a small business, with peer hubs and review sessions.",
  "It says women are 60 percent of participants (1,800), and at least 5 percent are persons with disabilities. 60 percent of 3,000 is 1,800, so that figure checks out.",
  "More than half are expected to move into retail, services and recycling. Recycling is closely tied to Coca-Cola's own packaging interests.",
  "It currently runs in Nairobi and Nakuru, with expansion to Makueni and Kisii planned.",
  "The only person quoted is CCBA's Public Affairs Director, Eric Githua: 'We are focused on supporting youth with practical skills that can help unlock economic opportunity.'",
  "CCBA has not released independent data on how many past participants went on to earn a lasting income.",
  "Coca-Cola is a major advertiser, which is a potential conflict of interest to disclose."
];

// Exercise definitions. Add new ones here as the course grows.
const EXERCISES = {
  "lede-crypto-1": {
    task:
      "Write the opening sentence (the lede) of a news story, leading with the most newsworthy fact, in active voice, under 35 words.",
    facts: [
      "Zimbabwe's Finance Minister has issued the country's first rules for cryptocurrency businesses.",
      "Firms that buy, sell, or hold crypto must register every year with the Financial Intelligence Unit.",
      "The annual fee is US$500. Operating without registering is now a criminal offence.",
      "This is a shift from the 2018 ban, which pushed crypto trading underground."
    ],
    rubric: [
      "Leads with the single most newsworthy fact (the new rules / mandatory registration), not the date, process, or background.",
      "Is accurate to the facts given and invents nothing not in them.",
      "Uses plain, active voice and concrete language.",
      "Is one clear sentence, roughly 35 words or fewer.",
      "Reads like a real news lede, not a summary or a headline."
    ]
  },
  "capstone-ccba-1": {
    task:
      "Write a nut graph (one or two sentences) framing the CCBA Kenya story for a Mutapa Times reader: what it is, who funds it, and the honest scope.",
    facts: CCBA_FACTS,
    rubric: [
      "Says clearly who is funding it (a Coca-Cola bottler / CCBA) and what it is (a youth skills programme).",
      "Makes clear that 3,000 is a 2026 target, not a number already trained.",
      "Does not repeat the company's slogans ('brighter future', 'world-class', 'doing business the right way') as fact.",
      "Signals the scrutiny, such as the lack of independent outcome data or that it is company-funded CSR.",
      "Is accurate to the facts and invents no figures or quotes."
    ]
  },
  "exam-ccba-500": {
    maxChars: 4000,
    task:
      "Write a news story of about 500 words for The Mutapa Times based on the CCBA Kenya press release. Lead with the honest news, attribute the company's claims, add context, and signal what independent verification is still needed.",
    facts: CCBA_FACTS,
    rubric: [
      "Leads with the honest news (a Coca-Cola bottler is funding a scheme that aims to reach 3,000 young Kenyans this year), not the company's spin.",
      "Reports 3,000 as a 2026 target, not as an achievement already delivered.",
      "Attributes the company's claims ('the company says') rather than stating them as fact, and never repeats slogans as fact.",
      "Adds real context, such as youth unemployment, and that this is company-funded CSR.",
      "Names the gap: only company data so far, a single quoted source, and no independent outcome figures.",
      "Gets the facts right: 60 percent is 1,800; it currently runs in Nairobi and Nakuru, with Makueni and Kisii planned.",
      "Is well structured (strong lede, supporting facts, context, scrutiny, the company's voice) and roughly 450 to 600 words.",
      "Clean, plain English with no em dashes."
    ]
  }
};

// Gemini structured-output schemas (OpenAPI subset, uppercase types).
const GRADE_SCHEMA = {
  type: "OBJECT",
  properties: {
    score: { type: "INTEGER", description: "0 to 100 overall quality against the rubric." },
    verdict: { type: "STRING", description: "One short sentence, max 14 words, on the overall judgement." },
    strengths: { type: "ARRAY", items: { type: "STRING" }, description: "1 to 3 specific things the student did well. Empty if none." },
    improvements: { type: "ARRAY", items: { type: "STRING" }, description: "1 to 3 specific, actionable fixes. Each tied to the rubric." },
    model_answer: { type: "STRING", description: "One strong example an editor might write." }
  },
  required: ["score", "verdict", "strengths", "improvements", "model_answer"]
};

const SUBMISSION_SCHEMA = {
  type: "OBJECT",
  properties: {
    score: { type: "INTEGER", description: "0 to 100 overall, weighted heavily on the article body and accuracy." },
    verdict: { type: "STRING", description: "One short sentence, max 16 words, on whether it is close to publishable." },
    publishable: { type: "BOOLEAN", description: "True only if it could run with light edits." },
    strengths: { type: "ARRAY", items: { type: "STRING" }, description: "1 to 3 things done well across the whole piece." },
    improvements: { type: "ARRAY", items: { type: "STRING" }, description: "2 to 4 specific, actionable fixes, most important first." },
    headline_note: { type: "STRING", description: "One sentence on the headline: accurate, specific, active?" },
    summary_note: { type: "STRING", description: "One sentence on the summary or standfirst." },
    body_note: { type: "STRING", description: "Two or three sentences on the article body: lede, structure, attribution, accuracy, balance." },
    bio_note: { type: "STRING", description: "One sentence on the author bio: concise and credible?" }
  },
  required: ["score", "verdict", "publishable", "strengths", "improvements", "headline_note", "summary_note", "body_note", "bio_note"]
};

function cors(origin, allowed) {
  const ok = allowed === "*" || origin === allowed;
  return {
    "Access-Control-Allow-Origin": ok ? (origin || allowed) : allowed,
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Max-Age": "86400"
  };
}

function json(body, status, headers) {
  return new Response(JSON.stringify(body), {
    status,
    headers: Object.assign({ "Content-Type": "application/json" }, headers)
  });
}

function clip(s, max) {
  s = (s || "").toString().trim();
  return s.length > max ? s.slice(0, max) : s;
}

async function callGemini(env, system, userMsg, schema, maxTokens) {
  const model = env.MODEL || GEMINI_MODEL;
  const url = "https://generativelanguage.googleapis.com/v1beta/models/" +
    model + ":generateContent?key=" + env.GEMINI_API_KEY;
  const body = {
    systemInstruction: { parts: [{ text: system }] },
    contents: [{ role: "user", parts: [{ text: userMsg }] }],
    generationConfig: {
      temperature: 0.4,
      // 2.5 models "think" by default and spend the output budget on it,
      // which truncates structured JSON. Turn it off for this graded task.
      thinkingConfig: { thinkingBudget: 0 },
      maxOutputTokens: maxTokens || 1200,
      responseMimeType: "application/json",
      responseSchema: schema
    }
  };
  const resp = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });
  if (!resp.ok) { const t = await resp.text(); throw new Error("upstream " + resp.status + " " + t.slice(0, 400)); }
  const data = await resp.json();
  const parts = data && data.candidates && data.candidates[0] &&
    data.candidates[0].content && data.candidates[0].content.parts;
  const text = parts && parts[0] && parts[0].text;
  if (!text) throw new Error("no-output " + JSON.stringify(data).slice(0, 400));
  return JSON.parse(text);
}

async function gradeExercise(payload, env, ch) {
  const ex = EXERCISES[payload && payload.exerciseId];
  if (!ex) return json({ error: "Unknown exercise" }, 400, ch);

  let answer = (payload.answer || "").toString().trim();
  if (answer.length < 3) return json({ error: "Answer too short" }, 400, ch);
  answer = clip(answer, ex.maxChars || DEFAULT_MAX_CHARS);

  const system =
    "You are a fair but exacting news editor at The Mutapa Times grading a student's writing exercise. " +
    "Grade only against the rubric provided. Be specific and concrete: quote the student's words when pointing something out. " +
    "Be encouraging but honest. Do not use em dashes anywhere in your output.";

  const userMsg =
    "TASK GIVEN TO STUDENT:\n" + ex.task + "\n\n" +
    "FACTS THE STUDENT WAS GIVEN:\n- " + ex.facts.join("\n- ") + "\n\n" +
    "GRADING RUBRIC:\n- " + ex.rubric.join("\n- ") + "\n\n" +
    "STUDENT'S ANSWER:\n\"" + answer + "\"\n\n" +
    "Grade it now.";

  let g;
  try { g = await callGemini(env, system, userMsg, GRADE_SCHEMA, ex.maxChars ? 1800 : 1200); }
  catch (e) { console.error("grade", e && e.message); return json({ error: "Grader upstream error" }, 502, ch); }

  return json({
    score: g.score,
    verdict: g.verdict,
    strengths: Array.isArray(g.strengths) ? g.strengths : [],
    improvements: Array.isArray(g.improvements) ? g.improvements : [],
    model_answer: g.model_answer || ""
  }, 200, ch);
}

async function gradeSubmission(payload, env, ch) {
  const headline = clip(payload.headline, 200);
  const summary = clip(payload.summary, 600);
  const body = clip(payload.body, 9000);
  const bio = clip(payload.bio, 600);
  const imageDesc = clip(payload.imageDesc || payload.imageCaption, 400);

  if (body.split(/\s+/).filter(Boolean).length < 80) {
    return json({ error: "Article too short to assess" }, 400, ch);
  }

  const system =
    "You are the commissioning editor at The Mutapa Times assessing a graduate's first full article submission for a real byline. " +
    "Judge it as you would a freelance pitch from a promising junior: hold it to professional standards but be constructive and specific. " +
    "Quote the writer's own words when you point something out. Weight the article body and factual accuracy most heavily. " +
    "Reward a clear lede, fair attribution, real context and balance; penalise PR-style spin, unsupported claims and burying the news. " +
    "Do not use em dashes anywhere in your output.";

  const userMsg =
    "A graduate of the Mutapa Times Academy has submitted an article of their own choice for editorial review.\n\n" +
    "HEADLINE:\n" + (headline || "(none)") + "\n\n" +
    "SUMMARY / STANDFIRST:\n" + (summary || "(none)") + "\n\n" +
    "IMAGE (described by the writer):\n" + (imageDesc || "(none)") + "\n\n" +
    "ARTICLE BODY:\n" + body + "\n\n" +
    "AUTHOR BIO:\n" + (bio || "(none)") + "\n\n" +
    "Assess it now.";

  let g;
  try { g = await callGemini(env, system, userMsg, SUBMISSION_SCHEMA, 2200); }
  catch (e) { console.error("submission", e && e.message); return json({ error: "Assessor upstream error" }, 502, ch); }

  return json({
    kind: "submission",
    score: g.score,
    verdict: g.verdict,
    publishable: !!g.publishable,
    strengths: Array.isArray(g.strengths) ? g.strengths : [],
    improvements: Array.isArray(g.improvements) ? g.improvements : [],
    sections: {
      headline: g.headline_note || "",
      summary: g.summary_note || "",
      body: g.body_note || "",
      bio: g.bio_note || ""
    }
  }, 200, ch);
}

async function gradeAnalysis(payload, env, ch) {
  const title = clip(payload.title, 300);
  const summary = clip(payload.summary, 900);
  const answer = clip(payload.answer, 3000);
  if (answer.split(/\s+/).filter(Boolean).length < 30) {
    return json({ error: "Analysis too short" }, 400, ch);
  }

  const system =
    "You are a journalism tutor at The Mutapa Times assessing a student's written analysis of recent news articles. " +
    "Judge the quality of their analytical thinking against the rubric, not their writing style. " +
    "Be specific and constructive, and quote the student's own words. Do not use em dashes anywhere in your output.";

  const userMsg =
    "THE ARTICLE(S) THE STUDENT ANALYSED:\n" + (title || "(title not provided)") +
    (summary ? "\nSummary: " + summary : "") + "\n\n" +
    "ANALYSIS RUBRIC (judge the student's analysis against these):\n" +
    "- Identifies the lede and the single most important news point.\n" +
    "- Names the sources used and assesses whether they are independent and balanced.\n" +
    "- Identifies the article's angle or framing.\n" +
    "- Notes what is missing: other voices, data, context, or what they would check.\n" +
    "- Assesses the news value: why it matters and to whom.\n" +
    "- Where two articles are compared, says how their approaches differ.\n" +
    "- Is specific to the article rather than vague and generic.\n\n" +
    "STUDENT'S ANALYSIS:\n\"" + answer + "\"\n\n" +
    "Grade it now. In model_answer, give a short example of what a strong analysis would notice.";

  let g;
  try { g = await callGemini(env, system, userMsg, GRADE_SCHEMA, 1200); }
  catch (e) { console.error("analysis", e && e.message); return json({ error: "Grader upstream error" }, 502, ch); }

  return json({
    score: g.score,
    verdict: g.verdict,
    strengths: Array.isArray(g.strengths) ? g.strengths : [],
    improvements: Array.isArray(g.improvements) ? g.improvements : [],
    model_answer: g.model_answer || "",
  }, 200, ch);
}

const REWORD_SCHEMA = {
  type: "OBJECT",
  properties: { suggestion: { type: "STRING", description: "The rewritten text, and nothing else." } },
  required: ["suggestion"],
};

async function rewordText(payload, env, ch) {
  const text = clip(payload.text, 1500);
  const context = clip(payload.context, 80);
  if (text.split(/\s+/).filter(Boolean).length < 3) return json({ error: "Too short to improve" }, 400, ch);

  const system =
    "You are an expert CV and resume editor. Rewrite the user's text so it is more impactful, concise and professional for a CV, " +
    "in clear plain English with strong action verbs. " +
    "Keep it strictly truthful: do not invent or exaggerate facts, employers, job titles, dates, metrics or skills that are not in the original. " +
    "Keep it roughly the same length or shorter, and keep the same point of view. Do not use em dashes. " +
    "Return only the rewritten text via the tool.";

  const userMsg =
    "CV SECTION: " + (context || "text") + "\n\n" +
    "ORIGINAL TEXT:\n\"" + text + "\"\n\n" +
    "Rewrite it now.";

  let g;
  try { g = await callGemini(env, system, userMsg, REWORD_SCHEMA, 700); }
  catch (e) { console.error("reword", e && e.message); return json({ error: "Could not improve the text" }, 502, ch); }
  return json({ suggestion: g.suggestion || "" }, 200, ch);
}

export default {
  async fetch(request, env) {
    const allowed = env.ALLOWED_ORIGIN || "https://mutapatimes.com";
    const origin = request.headers.get("Origin") || "";
    const ch = cors(origin, allowed);

    if (request.method === "OPTIONS") return new Response(null, { status: 204, headers: ch });
    if (request.method !== "POST") return json({ error: "Method not allowed" }, 405, ch);

    let payload;
    try { payload = await request.json(); }
    catch (e) { return json({ error: "Invalid JSON" }, 400, ch); }

    if (!env.GEMINI_API_KEY) return json({ error: "Grader not configured" }, 500, ch);

    if (payload && payload.kind === "submission") return gradeSubmission(payload, env, ch);
    if (payload && payload.kind === "analysis") return gradeAnalysis(payload, env, ch);
    if (payload && payload.kind === "reword") return rewordText(payload, env, ch);
    return gradeExercise(payload, env, ch);
  }
};
