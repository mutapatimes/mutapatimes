# The Mutapa Times — iOS App Roadmap (Expo)

_Draft, May 2026. Owner: Valentine. Audience: editor + any contractor pulled in._

---

## Situation read

We already have most of an iOS app's worth of plumbing built into the web product:

- **Data layer**: ~40 JSON endpoints under `/data/` (FX, jobs, ZSE, feature story, sponsors, spotlight, etc.) and 8 RSS feeds (`feed.xml`, `business-feed.xml`, `fx-feed.xml` and friends). Refresh every 3 hours via GitHub Actions.
- **Brand assets**: full icon set in `/img/`, `apple-icon-*` already sized to 57–180, logo + wordmark variants in `/img/brand/`, OG cards. Splash-screen ready.
- **PWA**: `site.webmanifest` + `sw.js` already in place, plus a `firebase-messaging-sw.js` stub for push.
- **Ad inventory**: live Hyatt / Marriott / Shopify / Belkin via Impact — needs in-app equivalents.
- **CMS**: Pages-CMS edits `content/articles/*.md` → GitHub Action regenerates HTML + feeds. The app can consume the same feeds — no second CMS needed.

What the iOS app adds that the web can't: **push notifications**, **offline reading**, **App Store distribution / discovery**, and an experience designed for a phone in the hand of a diaspora reader checking Zimbabwe news on the bus.

## Recommended approach: hybrid native shell

Three realistic shapes:

| Approach | Effort | App Store risk | Recommendation |
|---|---|---|---|
| **A. WebView wrapper** of mutapatimes.com | 1–2 weeks | High — Apple rejects under §4.2 "minimum functionality" | ❌ Don't ship as-is |
| **B. Native shell + WebView articles** (recommended) | 4–6 weeks | Low | ✅ Best risk/reward |
| **C. Fully native** screens for every section | 10–14 weeks | Lowest | Defer to v2 |

Approach B: native bottom-tab nav, native news feed, native FX / economy / city screens that hit the existing JSON endpoints, and articles rendered in a styled `react-native-webview` pointing at the existing HTML pages (which already load `sponsors.js` and `shopify-ads.js` — ads keep working). Push notifications, offline cache, share, and bookmarks live native. The reader experience is native enough for the App Store; the editorial pipeline doesn't fork.

**Headline tradeoff**: the article body is still served from mutapatimes.com inside a webview, so editorial changes propagate instantly without an App Store update — but the article reading experience is bound to whatever the web can do (which is most of what we need). v2 can re-render articles natively from the same `content/articles/*.md`.

## Phases

### Phase 0 — Foundation (week 1)
**Goal: unblock everything else.**
- [ ] Apple Developer Program enrolment ($99/yr, ~48-hour verification)
- [ ] Expo account + EAS subscription decision (free tier OK for v1; Production tier $99/mo when we hit OTA volume)
- [ ] `apps/ios/` directory in this repo (monorepo) — or separate repo if we want isolated CI. _Decision needed._
- [ ] `expo init` with Expo Router (file-based routing) + TypeScript
- [ ] Brand assets prepped: 1024×1024 marketing icon, 1242×2688 splash, app icon variants from `/img/brand/mark-1080.png`
- [ ] Bundle ID reserved: `com.mutapatimes.ios` (or similar — needs to be globally unique)
- [ ] App Store Connect skeleton created (name, primary category = News, app age rating, privacy policy URL)

**Deliverable**: empty Expo project that builds to a phone via TestFlight.

### Phase 1 — Read shell (weeks 2–3)
**Goal: a usable beta that reads the same content as the web.**
- [ ] Bottom tab bar: **News · Cities · Economy · Diaspora · More**
- [ ] News tab — `expo-router` index screen, pulls from `https://mutapatimes.com/data/spotlight.json`. Hero card (feature story), then card list. Pull-to-refresh.
- [ ] Cities tab — six city headers (Harare, Bulawayo, Mutare, Gweru, Masvingo, Vic Falls), each opens a feed view consuming the RSS sources we already publish.
- [ ] Article reader — `react-native-webview` pointing at the article's canonical URL. Native header with share + bookmark. Hide the site's chrome via injected JS / a `?app=1` query param the build script can read.
- [ ] Bookmarks — `AsyncStorage` of slugs. Empty-state copy.
- [ ] Share sheet — uses `expo-sharing`, posts the canonical URL.
- [ ] Search — `/articles?q=` in webview for v1; native search comes later.

**Deliverable**: TestFlight build #1. Read parity with the web, in a native shell.

### Phase 2 — Native features that justify the app (weeks 4–5)
**Goal: clear daylight between the app and the website.**
- [ ] **Push notifications** (the single biggest reason readers install)
  - Expo Notifications + APNs key
  - GitHub Action: when `fetch-news` lands a story tagged `breaking`, post to a Firebase / Supabase function that fires the push
  - Settings screen: notifications on/off, "breaking only" vs "daily briefing"
- [ ] **Offline reading** — `expo-file-system` + `expo-image` caching. Last 50 articles auto-cached on open.
- [ ] **Daily briefing widget** — first version is just a native screen at /briefing that pulls a curated set; iOS Widget proper deferred to v2.
- [ ] **FX corridor screen** (native, no webview) — consumes `/data/fx-rates.json`, big numbers, "Send money to Zimbabwe" CTA that opens the web FX page.
- [ ] **Dark mode** — auto-follow system; the web's `--paper`/`--bg`/`--accent` tokens carry over to React Native.

**Deliverable**: TestFlight build #2. Push working. Offline working. Native FX screen.

### Phase 3 — Monetisation parity (weeks 6–7)
**Goal: the sponsor revenue doesn't drop when readers migrate to the app.**
- [ ] **Sponsor strip + card** rendered natively from `/data/sponsors.json` (same data as the web)
  - The existing schema (`placements`, `card_placements`, `creative_url`, `impression_pixel`) maps 1:1 to React Native components.
  - One impression pixel fired per render via `Image` prefetch.
- [ ] **Shopify ads** — the negative-space banners. Two native components: `<ShopifyLeaderboard/>` and `<ShopifyHero/>`. Inventory rotates from the same `INVENTORY` object the web JS uses (consider extracting to a shared `/data/shopify-inventory.json`).
- [ ] **Newsletter signup** — native form posting to the same Brevo endpoint as the web subscribe page.
- [ ] **Apple's ad guidelines**: affiliate-link clicks (Hyatt, Marriott, Shopify, Belkin, Wise/WorldRemit/Mukuru for FX) are fine — they're not in-app purchases. Just need the right `rel`/disclosure language and a "Sponsored" eyebrow.
- [ ] **Avoid** Apple's IAP rules entirely until/unless we add paid subs.

**Deliverable**: TestFlight build #3. Revenue parity with web.

### Phase 4 — Submit + launch (week 8)
- [ ] App Store screenshots (6.7", 6.5", 5.5" — Expo can generate via Fastlane or we shoot from sim)
- [ ] App Store metadata (description, keywords, subtitle, what's new, support URL)
- [ ] App Privacy answers (this is Apple's labelled-list — we collect analytics + push tokens, that's it; no contact info, no health, etc.)
- [ ] Demo account credentials for App Review (probably not needed — there's no login)
- [ ] **Submit to App Review** — expect 1–3 days for first review, 24h for follow-ups
- [ ] **Known §4.2 risk mitigation**: highlight push notifications, offline cache, native FX/economy screens in the review notes — these are the features that take us past "wrapper" territory
- [ ] Soft launch in UK + South Africa first (our two biggest markets per GSC), worldwide after a week of stability
- [ ] Press: announce on the site + Metricool queue + Atlas + Brevo newsletter

**Deliverable**: shipped.

### Phase 5 — Post-launch (ongoing)
- [ ] iOS **home-screen widget** — `feature-story.json` powering a small/medium widget. Big diaspora signal driver.
- [ ] **iPadOS layout** — bigger column, sidebar nav. Probably 1 week of work.
- [ ] **Apple Watch glance** — FX corridor + headline only. Defer until iPhone usage justifies it.
- [ ] **EAS Update** — push JS bug fixes without App Store review. Enable from week 9 onwards.
- [ ] **Native article rendering** — incrementally replace the webview article reader with a markdown renderer that pulls from the same `content/articles/*.md` source via a new `/data/article/{slug}.json` endpoint.
- [ ] **Android (Expo same codebase)** — once iOS is stable.

## Key decisions to lock now

1. **Repo layout**. Monorepo (`/apps/ios/` here) vs separate repo. Recommend monorepo — share data + types + sponsor schema. The build system is already used to multi-target output.
2. **Push backend**. Three options: (a) GitHub Action calls Expo Push API directly when news lands — free, simple, ~OK at our volume; (b) Firebase Functions trigger; (c) Supabase Edge Function. Recommend (a) for v1, switch later if we outgrow it.
3. **Who's building**. Three credible answers: editor (us) part-time alongside web work — 2 weeks slips to 6; a contractor — 4–6 weeks of focused effort, ballpark £6–12k for a senior Expo developer; or an agency — fastest but £15k+. Recommend contractor for the build, editor in-house for post-launch iteration.
4. **App Store name + bundle ID**. Need to reserve before week 2.
5. **Apple Developer enrolment**. Individual ($99/yr) vs Organisation ($99/yr but needs a DUNS number, takes 1–4 weeks). Recommend Organisation — gives us "The Mutapa Times Ltd" in App Store, future-proof for paid subs.
6. **Analytics**. Keep Google Analytics on web, add `expo-firebase-analytics` or `posthog-react-native` on app. Recommend PostHog — better for product analytics, free tier generous.
7. **Push permission timing**. Don't ask on launch — that's a known anti-pattern (~60% reject rate). Ask after the user reads their 3rd article, or in onboarding step 3 framed as "be the first to know when Zimbabwean elections / SADC summits break". Recommend in-context prompt after 3rd article.

## Risks + open questions

- **§4.2 / §4.3 rejection** — biggest risk. Mitigations: push notifications, offline cache, native FX screen, app-only widgets in v2. Don't ship a WebView-only build.
- **Article reading in WebView feels web-y on iOS** — known issue, mitigated by injecting JS that hides the topbar/footer and adds native-feeling padding when `?app=1` is set.
- **Push pipeline reliability** — needs monitoring. A push that doesn't fire on a big story is a lost retention moment.
- **Cloudflare cache vs app freshness** — the JSON endpoints have `cache-control` set for web optimisation. May need `?app=1` cache-buster or shorter TTLs for in-app requests.
- **Bundle size** — 30 MB is the comfortable target; Expo defaults pull it close to that. Watch carefully.
- **Apple's algorithmic review** vs human reviewer — first review is human; flag-based re-reviews are algorithmic and stricter. Push the human review hard.

## Concrete next 3 actions this week

1. **Enrol in Apple Developer Program** as an organisation (gets the DUNS clock started — that's the long pole).
2. **Reserve the bundle ID** (`com.mutapatimes.ios` or whichever variant we want) and the App Store name.
3. **Decide who's building** — internal vs contractor vs agency. Until that's locked, phase 0 doesn't start.

Once those three are done, week 2 of phase 1 can begin in parallel: scaffold the Expo project, plug it into `data/spotlight.json`, and have a build on your phone within 5 days.

---

_Last updated: 2026-05-26. Next review: after Apple Developer enrolment clears._
