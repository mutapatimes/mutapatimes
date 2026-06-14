/**
 * Mutapa Times Academy — writing grader (Cloudflare Worker)
 *
 * Receives a student's short writing answer and returns a rubric-based
 * grade from Claude. The Anthropic API key lives only here, server-side,
 * never in the browser. The exercise briefs and rubrics also live here so
 * a student cannot tamper with how they are graded.
 *
 * Deploy:
 *   cd workers/academy-grade
 *   npx wrangler secret put ANTHROPIC_API_KEY   # paste your key
 *   npx wrangler deploy
 * Then put the resulting *.workers.dev URL into academy/index.html
 * (the GRADE_ENDPOINT constant).
 */

const ANTHROPIC_URL = "https://api.anthropic.com/v1/messages";
const MAX_ANSWER_CHARS = 800;

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
  }
};

const GRADE_TOOL = {
  name: "return_grade",
  description: "Return the grade for the student's writing.",
  input_schema: {
    type: "object",
    properties: {
      score: { type: "integer", description: "0 to 100 overall quality against the rubric." },
      verdict: { type: "string", description: "One short sentence, max 12 words, on the overall judgement." },
      strengths: {
        type: "array", items: { type: "string" },
        description: "1 to 3 specific things the student did well. Empty if none."
      },
      improvements: {
        type: "array", items: { type: "string" },
        description: "1 to 3 specific, actionable fixes. Each tied to the rubric."
      },
      model_answer: { type: "string", description: "One strong example lede an editor might write." }
    },
    required: ["score", "verdict", "strengths", "improvements", "model_answer"]
  }
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

    const ex = EXERCISES[payload && payload.exerciseId];
    if (!ex) return json({ error: "Unknown exercise" }, 400, ch);

    let answer = (payload.answer || "").toString().trim();
    if (answer.length < 3) return json({ error: "Answer too short" }, 400, ch);
    if (answer.length > MAX_ANSWER_CHARS) answer = answer.slice(0, MAX_ANSWER_CHARS);

    if (!env.ANTHROPIC_API_KEY) return json({ error: "Grader not configured" }, 500, ch);

    const system =
      "You are a fair but exacting news editor at The Mutapa Times grading a student's writing exercise. " +
      "Grade only against the rubric provided. Be specific and concrete: quote the student's words when pointing something out. " +
      "Be encouraging but honest. Do not use em dashes anywhere in your output. " +
      "Return your grade by calling the return_grade tool, and nothing else.";

    const userMsg =
      "TASK GIVEN TO STUDENT:\n" + ex.task + "\n\n" +
      "FACTS THE STUDENT WAS GIVEN:\n- " + ex.facts.join("\n- ") + "\n\n" +
      "GRADING RUBRIC:\n- " + ex.rubric.join("\n- ") + "\n\n" +
      "STUDENT'S ANSWER:\n\"" + answer + "\"\n\n" +
      "Grade it now via return_grade.";

    const body = {
      model: env.MODEL || "claude-sonnet-4-6",
      max_tokens: 700,
      system,
      tools: [GRADE_TOOL],
      tool_choice: { type: "tool", name: "return_grade" },
      messages: [{ role: "user", content: userMsg }]
    };

    let resp;
    try {
      resp = await fetch(ANTHROPIC_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "x-api-key": env.ANTHROPIC_API_KEY,
          "anthropic-version": "2023-06-01"
        },
        body: JSON.stringify(body)
      });
    } catch (e) {
      return json({ error: "Upstream unreachable" }, 502, ch);
    }

    if (!resp.ok) {
      return json({ error: "Grader upstream error" }, 502, ch);
    }

    let data;
    try { data = await resp.json(); }
    catch (e) { return json({ error: "Bad upstream response" }, 502, ch); }

    const block = (data.content || []).find(function (b) { return b.type === "tool_use" && b.name === "return_grade"; });
    if (!block || !block.input) return json({ error: "Could not grade" }, 502, ch);

    const g = block.input;
    return json({
      score: g.score,
      verdict: g.verdict,
      strengths: Array.isArray(g.strengths) ? g.strengths : [],
      improvements: Array.isArray(g.improvements) ? g.improvements : [],
      model_answer: g.model_answer || ""
    }, 200, ch);
  }
};
