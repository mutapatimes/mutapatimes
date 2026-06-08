#!/usr/bin/env python3
"""Build 5 new flight pages (Sydney, Cape Town, Johannesburg, from-Harare)
and update the /flights/ hub. Mirrors /flights/london-to-harare/ template."""
import json, html
from pathlib import Path

ROOT = Path("/Users/valentineeluwasi/Documents/GitHub/mutapatimes")
OUT  = ROOT / "flights"
TODAY = "2026-05-23"

widgets = json.loads((ROOT / "data" / "travelpayouts-widgets.json").read_text())["widgets"]

# Per-corridor page configs ---------------------------------------------------
CORRIDORS = {
    "sydney-to-harare": {
        "title_meta":   "Cheap flights Sydney to Harare — fares, airlines & live prices",
        "h1":           "Cheap flights Sydney to Harare",
        "stand":        "There are no direct flights between Australia and Zimbabwe. Every routing is one or two stops, typically via Perth then Joburg, or via the Gulf. Live prices in AUD below from Skyscanner, WayAway and Aviasales.",
        "flag_from":    "🇦🇺",  "flag_to": "🇿🇼",
        "origin_short": "Sydney",  "origin_full": "Sydney (SYD)",
        "dest_short":   "Harare",  "dest_full": "Harare (HRE)",
        "currency_lbl": "AUD",     "currency_sym": "A$",
        "widget_key":   "sydney-harare",
        "distance":     "11,500 km",
        "flight_time":  "22–28 hrs",
        "stops":        "1–2",
        "fare_range":   "A$1,800–A$3,500",
        "airlines": [
            ("Qantas + Qatar codeshare", "Doha (DOH)", "A$1,950–A$2,600"),
            ("Emirates",                 "Dubai (DXB)", "A$2,100–A$2,800"),
            ("Qantas + South African",   "Perth + Joburg (JNB)", "A$1,800–A$2,400"),
            ("Ethiopian + Qantas",       "Addis Ababa (ADD)", "A$2,000–A$2,700"),
        ],
        "intro_para":   "The Sydney–Harare route is one of the longer diaspora corridors in the world: 11,500 km of great-circle distance and 22–28 hours door-to-door. Australians flying home most commonly route through the Gulf (Dubai or Doha) for the most consistent service, or through Perth + Johannesburg for the lowest fare. Two-stop routings via the Gulf and Johannesburg are common and rarely cost more than the one-stop alternative.",
        "season":       "Australia's cheap months for the corridor are <strong>February–May</strong> and <strong>August–early November</strong>. Peak is <strong>December–January</strong> (Australian summer holidays aligning with Zimbabwean diaspora Christmas travel) and <strong>June–July</strong>. Book 12–16 weeks ahead; last-minute December fares from Sydney regularly exceed A$3,500.",
        "layovers": [
            ("Dubai (Emirates)", "8–10 hour total layover possible — Emirates' Sydney–Dubai is 14h, Dubai–Harare adds another 7h with a 2–4h transit."),
            ("Doha (Qatar/Qantas codeshare)", "Similar comfort to Dubai. Often the cheapest reliable option."),
            ("Johannesburg (via Perth)", "The cheapest option but the longest total elapsed time. SAA's JNB–HRE onward leg is on a separate ticket in some itineraries — check baggage through-checking."),
        ],
        "baggage":      "Qatar and Emirates both permit 2 × 23 kg checked in economy on Australia–Africa long-haul, which is generous. Qantas + JNB itineraries vary by booking class — verify before buying. Excess at the counter is 5–10× the booking-time rate.",
        "visa":         "Australian passport holders need a visa for Zimbabwe but it's issued on arrival at Harare International. US$55 cash single-entry. Bring USD cash — the visa desk does not accept card.",
        "faqs": [
            ("How much is a flight from Sydney to Harare?",
             "A$1,800 to A$3,500 return depending on season and how far ahead you book. Cheapest months are February–May and August–early November; most expensive is December–January and June–July. Live prices in AUD are in the search widget above."),
            ("Are there direct flights from Sydney to Harare?",
             "No. There are no direct services between Australia and Zimbabwe. Routings always have one or two stops, most commonly via Dubai, Doha, or Perth + Johannesburg."),
            ("How long is the flight from Sydney to Harare?",
             "22 to 28 hours including layovers. Pure flight time across two legs is ~18 hours; the rest is the transit stop. Sydney–Dubai is 14h, Dubai–Harare is 7h."),
            ("What's the cheapest way to fly from Sydney to Harare?",
             "Two-stop routings via Perth + Johannesburg (Qantas + South African or Airlink) typically come in lowest, often under A$2,000 in low season. The trade-off is more total elapsed time and tighter baggage through-checking."),
            ("Do Australian passport holders need a visa for Zimbabwe?",
             "Yes, but it's issued on arrival at Harare International for US$55 cash single-entry. No advance application needed. Bring USD cash."),
        ],
        "related": [
            ("Send AUD to Zimbabwe", "/fx/send-money-from-australia-to-zimbabwe/"),
            ("AUD to ZWG rate today", "/fx/aud-to-zwg/"),
            ("Visa on arrival", "/moving-to-zimbabwe/visa-on-arrival.html"),
        ],
    },
    "cape-town-to-harare": {
        "title_meta":   "Cheap flights Cape Town to Harare — fares, airlines & live prices",
        "h1":           "Cheap flights Cape Town to Harare",
        "stand":        "Cape Town to Harare is a 3-hour direct flight served by Airlink and SAA. One of the busier regional corridors in southern Africa. Live prices in ZAR below.",
        "flag_from":    "🇿🇦",  "flag_to": "🇿🇼",
        "origin_short": "Cape Town",  "origin_full": "Cape Town (CPT)",
        "dest_short":   "Harare",  "dest_full": "Harare (HRE)",
        "currency_lbl": "ZAR",     "currency_sym": "R",
        "widget_key":   "cape-town-harare",
        "distance":     "2,200 km",
        "flight_time":  "3 hrs (direct) or 5–7 hrs (via JNB)",
        "stops":        "0 or 1",
        "fare_range":   "R5,500–R12,000",
        "airlines": [
            ("Airlink",                "Direct CPT–HRE",        "R6,500–R9,500"),
            ("South African Airways",  "Via Johannesburg (JNB)","R5,500–R10,000"),
            ("FastJet",                "Via Johannesburg (JNB)","R5,500–R8,500"),
            ("Kenya Airways",          "Via Nairobi (NBO)",     "R7,000–R12,000"),
        ],
        "intro_para":   "Cape Town to Harare is one of the easier regional flights in southern Africa: roughly 2,200 km, three hours direct on Airlink, or via Joburg on SAA or FastJet at a slightly lower fare. SAA and Airlink share the route via codeshare so check who actually operates your specific flight when comparing.",
        "season":       "Cape Town's tourist high season (December–February) lifts the corridor's prices because the inbound CPT leg fills up. Cheapest months are <strong>March–May</strong> and <strong>September–early November</strong>. Book 4–8 weeks ahead — this is a more reactive corridor than the long-haul ones, and fares move within a smaller band.",
        "layovers": [
            ("Direct (Airlink)", "No layover. 3-hour scheduled flight time. The simplest routing if your dates work."),
            ("Johannesburg (SAA / FastJet)", "1.5h JNB layover typical. Adds 2–4 hours total elapsed time but can save R1,000–R2,000 versus direct."),
        ],
        "baggage":      "Airlink direct allows 1 × 23 kg checked in economy as standard, with the option to add a second bag at booking for R500–R900. SAA via JNB varies by class but generally 1 × 23 kg. FastJet is the budget option — checked bags are extra (R350–R700 per bag).",
        "visa":         "South African passport holders do not need a visa for Zimbabwe for stays under 90 days. Just bring your passport and proof of return travel.",
        "faqs": [
            ("How much is a flight from Cape Town to Harare?",
             "R5,500 to R12,000 return depending on direct vs one-stop and how far ahead you book. Direct on Airlink is usually R6,500–R9,500; via Joburg with SAA or FastJet can dip below R6,000 in low season."),
            ("Are there direct flights from Cape Town to Harare?",
             "Yes. Airlink operates direct Cape Town to Harare with a scheduled flight time of around 3 hours. SAA and FastJet route via Johannesburg, which is cheaper but longer."),
            ("How long is the direct flight from Cape Town to Harare?",
             "Approximately 3 hours direct on Airlink. Via Johannesburg the total journey time is 5–7 hours including the layover."),
            ("What is the cheapest way to fly from Cape Town to Harare?",
             "Via Johannesburg with FastJet or SAA, booked 4–8 weeks ahead in low season (March–May, September–early November), can sit at R5,500–R6,500 return. The trade-off is the extra hours and tighter baggage allowance."),
            ("Do South Africans need a visa for Zimbabwe?",
             "No. South African passport holders can visit Zimbabwe visa-free for up to 90 days. Just bring your passport."),
        ],
        "related": [
            ("Johannesburg to Harare flights", "/flights/johannesburg-to-harare/"),
            ("ZAR to ZWG rate today", "/fx/zar-to-zwg/"),
            ("Send ZAR to Zimbabwe", "/fx/send-money-from-south-africa-to-zimbabwe/"),
        ],
    },
    "johannesburg-to-harare": {
        "title_meta":   "Cheap flights Johannesburg to Harare — fares, airlines & live prices",
        "h1":           "Cheap flights Johannesburg to Harare",
        "stand":        "Johannesburg to Harare is the busiest air corridor between Zimbabwe and South Africa. Daily frequencies on SAA, Airlink and FastJet; 1h50 scheduled flight time. Live prices in ZAR below.",
        "flag_from":    "🇿🇦",  "flag_to": "🇿🇼",
        "origin_short": "Johannesburg",  "origin_full": "Johannesburg (JNB)",
        "dest_short":   "Harare",  "dest_full": "Harare (HRE)",
        "currency_lbl": "ZAR",     "currency_sym": "R",
        "widget_key":   "johannesburg-harare",
        "distance":     "1,100 km",
        "flight_time":  "1h 50m",
        "stops":        "0",
        "fare_range":   "R3,500–R8,500",
        "airlines": [
            ("South African Airways", "Direct JNB–HRE", "R4,500–R7,500"),
            ("Airlink",               "Direct JNB–HRE", "R4,200–R7,000"),
            ("FastJet",               "Direct JNB–HRE", "R3,500–R6,500"),
            ("Kenya Airways (via NBO)", "Via Nairobi",  "R6,000–R10,000"),
        ],
        "intro_para":   "Johannesburg to Harare is the most-flown corridor between South Africa and Zimbabwe. Three airlines fly it daily — SAA, Airlink and FastJet — with 1h 50m scheduled flight times. SAA and Airlink share the route via codeshare; FastJet is the budget option. Book 2–6 weeks ahead for the cheapest fares.",
        "season":       "Cheaper months are <strong>February–May</strong> and <strong>September–early November</strong>. Peak is December and the South African school holiday windows (April–early May, late June–mid July, late September–mid October). Christmas fares can double; book by October for December.",
        "layovers": [
            ("Direct on SAA / Airlink / FastJet", "No layover. 1h 50m scheduled flight, multiple daily frequencies."),
            ("Via Nairobi (Kenya Airways)", "Only relevant if you're connecting onward from JNB to Kenya — otherwise no reason to take an indirect routing on this corridor."),
        ],
        "baggage":      "SAA includes 1 × 23 kg checked. Airlink the same, with extras at R500–R900 each at booking. FastJet is the budget carrier — base fares exclude checked bags; budget R350–R700 per bag added at booking, more at the airport.",
        "visa":         "South African passport holders do not need a visa for Zimbabwe for stays under 90 days. UK, US, Australian, Canadian passport holders connecting through JNB will need a Zimbabwe visa on arrival at Harare (USD cash).",
        "faqs": [
            ("How much is a flight from Johannesburg to Harare?",
             "R3,500 to R8,500 return depending on carrier and season. FastJet is usually cheapest at R3,500–R6,500; SAA and Airlink sit at R4,500–R7,500. Christmas fares can exceed R10,000."),
            ("Are there direct flights from Johannesburg to Harare?",
             "Yes. SAA, Airlink and FastJet all fly direct Joburg to Harare, with 1h 50m scheduled flight time. Multiple daily frequencies on each."),
            ("How long is the flight from Johannesburg to Harare?",
             "1 hour 50 minutes scheduled flight time. Including check-in time, the full airport-to-airport journey is around 4 hours."),
            ("Which is the cheapest airline Johannesburg to Harare?",
             "FastJet is usually the cheapest, with one-way fares often under R2,000. SAA and Airlink come in higher but include more baggage allowance and faster connections at JNB."),
            ("How often do flights run Joburg to Harare?",
             "Multiple times daily. Combined across SAA, Airlink and FastJet there are typically 6–8 daily frequencies in each direction, including early morning, midday and evening departures."),
        ],
        "related": [
            ("Cape Town to Harare flights", "/flights/cape-town-to-harare/"),
            ("ZAR to ZWG rate today", "/fx/zar-to-zwg/"),
            ("Send ZAR to Zimbabwe", "/fx/send-money-from-south-africa-to-zimbabwe/"),
        ],
    },
    "from-harare": {
        "title_meta":   "Flights from Harare — book your return to the UK, USA, SA, Australia",
        "h1":           "Flights from Harare",
        "stand":        "Live price search for flights departing Harare to anywhere in the world. UK, USA, South Africa, Dubai, Australia and Canada are the busiest diaspora-return corridors. Prices in USD.",
        "flag_from":    "🇿🇼",  "flag_to": "🌍",
        "origin_short": "Harare",  "origin_full": "Harare (HRE)",
        "dest_short":   "anywhere",  "dest_full": "any destination",
        "currency_lbl": "USD",     "currency_sym": "$",
        "widget_key":   "from-harare",
        "distance":     "varies",
        "flight_time":  "varies by route",
        "stops":        "1+",
        "fare_range":   "$700–$2,500",
        "airlines": [
            ("Emirates",           "via Dubai (DXB)",          "to UK, EU, USA, Australia"),
            ("Qatar Airways",      "via Doha (DOH)",           "to UK, EU, USA"),
            ("Ethiopian Airlines", "via Addis Ababa (ADD)",    "to USA, Canada, EU, Asia"),
            ("Kenya Airways",      "via Nairobi (NBO)",        "to UK, EU, India"),
            ("South African / Airlink", "via Johannesburg (JNB)", "to UK, EU, USA, Australia (with onward partner)"),
        ],
        "intro_para":   "Harare is well-connected for a southern African hub: five major carriers operate daily long-haul departures, each routing through their hub (Dubai, Doha, Addis Ababa, Nairobi or Johannesburg) before fanning out to the diaspora's home cities. Use the search widget below to find live fares from HRE to wherever you're heading.",
        "season":       "Outbound prices from Harare follow the inbound diaspora calendar in reverse. Cheapest outbound months are typically <strong>January–February</strong> (after Christmas), <strong>August</strong> (after July returns) and <strong>November</strong> (pre-Christmas inbound rush). Peak outbound is <strong>mid-January</strong> (diaspora return to UK/SA after Christmas) and <strong>late July–early August</strong>.",
        "layovers": [
            ("Emirates via Dubai", "The most reliable hub for onward UK, US, EU, Australian connections."),
            ("Qatar via Doha", "Similar to Emirates, often a bit cheaper to the UK."),
            ("Ethiopian via Addis", "The cheapest option for North America and a key hub for African connections."),
            ("Kenya Airways via Nairobi", "Decent African network, occasionally competitive for the UK."),
            ("South African via Johannesburg", "The cheapest route to Australia (via Perth onward) but check whether your onward leg is on the same ticket."),
        ],
        "baggage":      "Emirates, Qatar and Ethiopian all permit 2 × 23 kg checked in economy on the Harare–[hub]–[destination] long-haul ticket. Kenya Airways and SAA itineraries vary by class. If you're flying with extra goods (a common diaspora pattern), Emirates is the most generous out of HRE.",
        "visa":         "Visa requirements at the destination apply; this page is about getting out of HRE, not about onward immigration. UK passport holders re-entering the UK need their passport only. US, Australian, Canadian green-card holders should check their own destination requirements.",
        "faqs": [
            ("How much is a flight from Harare to London?",
             "Typically US$900–US$1,800 return, with the cheap end in January–February and August. Emirates via Dubai and Qatar via Doha are the most-flown options; Kenya Airways via Nairobi is often a few hundred USD cheaper."),
            ("What's the cheapest flight from Harare to the USA?",
             "Ethiopian via Addis Ababa is consistently the cheapest to the US East Coast (US$1,100–US$1,900 return to NYC/Washington). For the West Coast, the same routing applies but adds another connection."),
            ("Which airlines fly from Harare?",
             "Five main carriers operate daily out of Harare International (HRE): Emirates (DXB), Qatar Airways (DOH), Ethiopian Airlines (ADD), Kenya Airways (NBO) and South African Airways / Airlink (JNB)."),
            ("When is the cheapest time to fly out of Harare?",
             "January–February (after the Christmas inbound rush), August (after July returns to school) and November (before the December inbound). Avoid mid-January and late July when diaspora outbound peaks."),
            ("Do I need a return ticket to leave Zimbabwe?",
             "Some destinations require proof of onward travel for entry. For UK/US/EU/Australian visa holders this is rarely an issue. For visitor visas, having a return ticket on the same booking smooths immigration at both ends."),
        ],
        "related": [
            ("London to Harare flights", "/flights/london-to-harare/"),
            ("Johannesburg to Harare flights", "/flights/johannesburg-to-harare/"),
            ("Send money home", "/fx/"),
        ],
    },
}

# ---------------------------------------------------------------------------
# Shared head + CSS (mirror London page so we don't drift)
# ---------------------------------------------------------------------------

CSS = """.fl-shell { max-width: 1100px; margin: 0 auto; padding: 0 20px; }
.fl-section-header { max-width: 1000px; margin: 0 auto; padding: 24px 20px 8px; }
.fl-eyebrow { font-family: 'Inter', system-ui, sans-serif; font-size: 0.72em;
  letter-spacing: 0.16em; text-transform: uppercase; color: var(--accent);
  font-weight: 700; margin: 0 0 8px; }
.fl-eyebrow a { color: inherit; text-decoration: none; }
.fl-title { font-family: 'Playfair Display', Georgia, serif; font-weight: 700;
  font-size: clamp(1.8em, 4vw, 2.6em); line-height: 1.1; color: var(--ink);
  margin: 0 0 10px; letter-spacing: -0.01em; }
.fl-stand { font-family: 'Inter', system-ui, sans-serif; font-size: 1.02em;
  line-height: 1.55; color: var(--text-mid); margin: 0; max-width: 44em; }
.fl-rule { width: 48px; height: 3px; background: var(--accent); border: 0; margin: 14px 0 0; }

.fl-facts { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 12px; max-width: 1000px; margin: 18px auto 8px; padding: 0 20px; }
.fl-fact { padding: 12px 14px; background: var(--paper); border: 1px solid var(--rule); border-radius: 8px; }
.fl-fact-label { font-family: 'Inter', system-ui, sans-serif; font-size: 0.66em;
  letter-spacing: 0.14em; text-transform: uppercase; color: var(--text-light);
  margin: 0 0 4px; font-weight: 600; }
.fl-fact-value { font-family: 'Playfair Display', Georgia, serif; font-size: 1.15em;
  line-height: 1.2; color: var(--ink); margin: 0; font-weight: 700; }

.fl-widget-wrap { max-width: 1000px; margin: 14px auto 22px; padding: 0 20px; }
.fl-widget-label { font-family: 'Inter', system-ui, sans-serif; font-size: 0.74em;
  letter-spacing: 0.14em; text-transform: uppercase; color: var(--text-light);
  margin: 0 0 8px; font-weight: 600; }
.fl-widget { background: #fff; border: 1px solid var(--rule); border-radius: 9px; padding: 6px; }

.fl-prose { max-width: 720px; margin: 0 auto; padding: 0 20px; font-family: 'Inter', system-ui, sans-serif; }
.fl-prose h2 { font-family: 'Playfair Display', Georgia, serif; font-weight: 700;
  font-size: 1.4em; color: var(--ink); margin: 26px 0 10px; }
.fl-prose p { font-size: 1em; line-height: 1.65; color: var(--text); margin: 0 0 12px; }
.fl-prose ul, .fl-prose ol { font-size: 1em; line-height: 1.65; padding-left: 20px; margin: 0 0 14px; }
.fl-prose li { margin-bottom: 5px; }
.fl-prose a { color: var(--accent); text-decoration: underline; }
.fl-prose strong { color: var(--ink); }
.fl-prose table { width: 100%; border-collapse: collapse; margin: 8px 0 18px; font-size: 0.95em; }
.fl-prose th, .fl-prose td { text-align: left; padding: 8px 12px; border-bottom: 1px solid var(--rule); }
.fl-prose th { font-family: 'Inter', system-ui, sans-serif; font-size: 0.72em;
  letter-spacing: 0.1em; text-transform: uppercase; color: var(--text-light);
  background: var(--paper); }

.fl-faq { max-width: 720px; margin: 22px auto; padding: 0 20px; font-family: 'Inter', system-ui, sans-serif; }
.fl-faq h2 { font-family: 'Playfair Display', Georgia, serif; font-weight: 700;
  font-size: 1.4em; color: var(--ink); margin: 0 0 14px; }
.fl-faq details { background: var(--paper); border: 1px solid var(--rule); border-radius: 8px;
  padding: 0; margin: 0 0 8px; }
.fl-faq summary { padding: 12px 16px; font-weight: 600; cursor: pointer;
  color: var(--ink); font-size: 0.98em; list-style: none; }
.fl-faq summary::-webkit-details-marker { display: none; }
.fl-faq summary::after { content: '＋'; float: right; color: var(--accent);
  font-weight: 400; transition: transform 0.15s; }
.fl-faq details[open] summary::after { content: '−'; }
.fl-faq details > p { padding: 0 16px 14px; margin: 0; line-height: 1.6;
  color: var(--text); font-size: 0.95em; }

.fl-sim-banner { max-width: 1000px; margin: 22px auto; padding: 0 20px; }
.fl-sim-banner-inner { background: var(--paper); border: 1px solid var(--rule);
  border-left: 3px solid var(--accent); border-radius: 6px; padding: 16px 20px;
  font-family: 'Inter', system-ui, sans-serif; }
.fl-sim-banner h3 { font-family: 'Playfair Display', Georgia, serif; font-weight: 700;
  font-size: 1.1em; margin: 0 0 4px; color: var(--ink); }
.fl-sim-banner p { font-size: 0.92em; line-height: 1.55; color: var(--text-mid); margin: 0 0 8px; }
.fl-sim-banner a { color: var(--accent); }

.fl-related { max-width: 1000px; margin: 22px auto; padding: 0 20px; }
.fl-related h2 { font-family: 'Playfair Display', Georgia, serif; font-weight: 700;
  font-size: 1.3em; color: var(--ink); margin: 0 0 12px; }
.fl-related-grid { display: grid; gap: 10px; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); }
.fl-related-link { display: block; padding: 14px 16px; background: #fff;
  border: 1px solid var(--rule); border-radius: 8px; text-decoration: none;
  color: var(--text); font-family: 'Inter', system-ui, sans-serif;
  transition: border-color 0.15s, transform 0.15s; }
.fl-related-link:hover { border-color: var(--accent); transform: translateY(-1px);
  text-decoration: none; color: var(--text); }
.fl-related-link strong { color: var(--ink); display: block; margin-bottom: 2px; font-size: 0.95em; }

.fl-sources { max-width: 720px; margin: 22px auto 6px; padding: 16px 20px;
  border-top: 2px solid var(--ink); font-family: 'Inter', system-ui, sans-serif; }
.fl-sources h2 { font-size: 0.74em; letter-spacing: 0.18em; text-transform: uppercase;
  margin: 0 0 10px; color: var(--text-light); font-weight: 700; font-family: inherit; }
.fl-sources ul { font-size: 0.88em; margin: 0 0 10px; padding-left: 20px; line-height: 1.55; color: var(--text); }
.fl-sources a { color: var(--ink); text-decoration: underline; }
.fl-sources-note { font-size: 0.8em; color: var(--text-light); margin: 0; line-height: 1.55; }

.fl-back { text-align: center; margin: 24px 0 40px; font-family: 'Inter', system-ui, sans-serif; }
.fl-back a { font-size: 0.88em; color: var(--ink); border-bottom: 1px solid var(--accent);
  text-decoration: none; padding-bottom: 2px; }"""

TOPBAR = """<div class="topbar" id="topbar" aria-label="Sticky navigation">
  <button class="topbar-menu" type="button" data-open-drawer aria-label="Open menu" aria-controls="navDrawer" aria-expanded="false">
    <span></span><span></span><span></span>
  </button>
  <a href="/" class="topbar-brand"><em>The Mutapa Times</em></a>
  <a href="/subscribe" class="topbar-cta">Subscribe</a>
</div>"""

FOOTER = """<footer class="atlantic-foot">
  <div class="atlantic-foot-inner">
    <div class="atlantic-foot-fine">
      <a href="/">News</a><span class="sep">·</span>
      <a href="/flights/">Flights</a><span class="sep">·</span>
      <a href="/fx/">FX rates</a><span class="sep">·</span>
      <a href="/zse/">ZSE companies</a><span class="sep">·</span>
      <a href="/mining/">Mining</a><span class="sep">·</span>
      <a href="/schools/">Schools</a><span class="sep">·</span>
      <a href="/moving-to-zimbabwe/">UK guide</a><span class="sep">·</span>
      <a href="/authors/">Masthead</a><span class="sep">·</span>
      <a href="/privacy">Privacy</a><span class="sep">·</span>
      <a href="/terms">Terms</a><span class="sep">·</span>
      <a href="mailto:news@mutapatimes.com">Contact</a>
    </div>
    <p class="atlantic-foot-copy">&copy; 2020&ndash;2026 The Mutapa Times. All rights reserved. Operated from the United Kingdom.</p>
  </div>
</footer>
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XQPRFK7JTB"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-XQPRFK7JTB');
</script>"""

TRACKING = """<!-- impact.com Universal Tracking Tag (UTT) -->
<script type="text/javascript">(function(i,m,p,a,c,t){c.ire_o=p;c[p]=c[p]||function(){(c[p].a=c[p].a||[]).push(arguments)};t=a.createElement(m);var z=a.getElementsByTagName(m)[0];t.async=1;t.src=i;z.parentNode.insertBefore(t,z)})('https://utt.impactcdn.com/P-A7333443-d775-4dfb-addf-0aa89ab29f151.js','script','impactStat',document,window);impactStat('transformLinks');impactStat('trackImpression');</script>
<!-- Travelpayouts Drive tracking -->
<script nowprocket data-noptimize="1" data-cfasync="false" data-wpfc-render="false" seraph-accel-crit="1" data-no-defer="1">
  (function () {
      var script = document.createElement("script");
      script.async = 1;
      script.src = 'https://emrldtp.cc/NTMyMTA3.js?t=532107';
      document.head.appendChild(script);
  })();
</script>"""

def render_corridor(slug, c):
    widget = widgets[c["widget_key"]]["embed"]
    airline_rows = "\n".join(
        f"        <tr><td><strong>{html.escape(name)}</strong></td><td>{html.escape(hub)}</td><td>{html.escape(fare)}</td></tr>"
        for name, hub, fare in c["airlines"]
    )
    layover_items = "\n".join(
        f"      <li><strong>{html.escape(hub)}</strong> &mdash; {html.escape(note)}</li>"
        for hub, note in c["layovers"]
    )
    faq_html = "\n".join(
        f'''    <details>
      <summary>{html.escape(q)}</summary>
      <p>{html.escape(a)}</p>
    </details>''' for q, a in c["faqs"]
    )
    faq_ld = json.dumps({
        "@context": "https://schema.org", "@type": "FAQPage",
        "mainEntity": [{"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}} for q, a in c["faqs"]]
    }, ensure_ascii=False)
    trip_ld = json.dumps({
        "@context":"https://schema.org","@type":"Trip",
        "name": f"{c['origin_short']} to {c['dest_short']}",
        "description": f"Flight from {c['origin_full']} to {c['dest_full']}",
        "provider": {"@type":"Organization","name":"The Mutapa Times","url":"https://www.mutapatimes.com"}
    }, ensure_ascii=False)
    breadcrumb_ld = json.dumps({
        "@context":"https://schema.org","@type":"BreadcrumbList",
        "itemListElement":[
            {"@type":"ListItem","position":1,"name":"Home","item":"https://www.mutapatimes.com/"},
            {"@type":"ListItem","position":2,"name":"Flights","item":"https://www.mutapatimes.com/flights/"},
            {"@type":"ListItem","position":3,"name": f"{c['origin_short']} to {c['dest_short']}", "item": f"https://www.mutapatimes.com/flights/{slug}/"}
        ]
    }, ensure_ascii=False)
    related_html = "\n".join(
        f'      <a class="fl-related-link" href="{href}"><strong>{html.escape(name)}</strong></a>'
        for name, href in c["related"]
    )
    title = c["title_meta"] + " | The Mutapa Times"
    return f'''<!doctype html>
<html class="no-js" lang="en">
<head>
    <meta charset="utf-8">
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-4428529474445353" crossorigin="anonymous"></script>
    <title>{title}</title>
    <link rel="canonical" href="https://www.mutapatimes.com/flights/{slug}/">
    <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
    <link rel="manifest" href="../../site.webmanifest">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-title" content="Mutapa Times">
    <link rel="apple-touch-icon" href="../../icon.png">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Playfair+Display:ital,wght@0,400;0,700;0,900;1,400&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css" media="print" onload="this.media='all'"><noscript><link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css"></noscript>
    <link rel="stylesheet" href="../../css/normalize.css">
    <link rel="stylesheet" href="../../css/main.css?v=102">
    <link rel="icon" type="image/png" sizes="32x32" href="../../img/favicon-32x32.png">
    <link rel="icon" type="image/png" sizes="16x16" href="../../img/favicon-16x16.png">
    <meta name="theme-color" content="#1a1a1a">
    <meta name="author" content="The Mutapa Times">
    <meta name="twitter:site" content="@mutapatimes">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="description" content="{html.escape(c["title_meta"])}">
    <meta name="robots" content="index, follow">
    <meta property="og:type" content="article">
    <meta property="og:title" content="{html.escape(c["title_meta"])}">
    <meta property="og:description" content="{html.escape(c["stand"])[:200]}">
    <meta property="og:url" content="https://www.mutapatimes.com/flights/{slug}/">
    <meta property="og:site_name" content="The Mutapa Times">
    <meta name="twitter:title" content="{html.escape(c["title_meta"])}">
    <meta name="twitter:description" content="{html.escape(c["stand"])[:200]}">
<script type="application/ld+json">{breadcrumb_ld}</script>
<script type="application/ld+json">{faq_ld}</script>
<script type="application/ld+json">{trip_ld}</script>
{TRACKING}
<style>{CSS}</style>
</head>
<body>
{TOPBAR}
<main>
  <header class="fl-section-header">
    <p class="fl-eyebrow"><a href="../">Flights</a> &middot; {c["flag_from"]} {c["origin_short"]} → {c["flag_to"]} {c["dest_short"]}</p>
    <h1 class="fl-title">{html.escape(c["h1"])}</h1>
    <p class="fl-stand">{c["stand"]}</p>
    <hr class="fl-rule">
  </header>

  <div class="fl-facts" role="list">
    <div class="fl-fact"><p class="fl-fact-label">Distance</p><p class="fl-fact-value">{html.escape(c["distance"])}</p></div>
    <div class="fl-fact"><p class="fl-fact-label">Flight time</p><p class="fl-fact-value">{html.escape(c["flight_time"])}</p></div>
    <div class="fl-fact"><p class="fl-fact-label">Stops</p><p class="fl-fact-value">{html.escape(c["stops"])}</p></div>
    <div class="fl-fact"><p class="fl-fact-label">Typical fare</p><p class="fl-fact-value">{html.escape(c["fare_range"])}</p></div>
  </div>

  <div class="fl-widget-wrap">
    <p class="fl-widget-label">Live price search &mdash; {c["origin_short"]} → {c["dest_short"]} in {c["currency_lbl"]}</p>
    <div class="fl-widget">
      {widget}
    </div>
  </div>

  <div class="fl-prose">
    <h2>{c["origin_short"]} to {c["dest_short"]} &mdash; the route</h2>
    <p>{c["intro_para"]}</p>

    <h2>Airlines and typical fares</h2>
    <table>
      <thead><tr><th>Airline</th><th>Routing</th><th>Typical fare</th></tr></thead>
      <tbody>
{airline_rows}
      </tbody>
    </table>

    <h2>When is the cheapest time to fly?</h2>
    <p>{c["season"]}</p>

    <h2>Layover patterns</h2>
    <ul>
{layover_items}
    </ul>

    <h2>Baggage</h2>
    <p>{c["baggage"]}</p>

    <h2>{"Visa note" if slug != "from-harare" else "Re-entry note"}</h2>
    <p>{c["visa"]}</p>
  </div>

  <aside class="fl-sim-banner">
    <div class="fl-sim-banner-inner">
      <h3>Before you fly: Zimbabwe eSIM</h3>
      <p>Get connectivity sorted before you land. An eSIM with a Zimbabwean
        data plan means you arrive online &mdash; no airport SIM queues, no
        roaming charges. <a href="/moving-to-zimbabwe/sim-card-and-mobile.html">Compare Zimbabwe eSIM options &rarr;</a></p>
    </div>
  </aside>

  <section class="fl-faq" aria-label="Frequently asked questions">
    <h2>Frequently asked questions</h2>
{faq_html}
  </section>

  <section class="fl-related">
    <h2>Related</h2>
    <div class="fl-related-grid">
{related_html}
    </div>
  </section>

  <section class="fl-sources" aria-label="Sources">
    <h2>Sources &amp; further reading</h2>
    <ul>
      <li>Live price data: <a href="https://www.travelpayouts.com/" rel="noopener" target="_blank">Travelpayouts</a>, aggregating Skyscanner, Aviasales, WayAway and Kiwi.com.</li>
      <li>Fare ranges and route commentary are editorial, last reviewed {TODAY}.</li>
    </ul>
    <p class="fl-sources-note">The Mutapa Times may earn a referral commission
      when readers book through the embedded search; this does not change
      the price you pay or which airlines we list.</p>
  </section>

  <p class="fl-back"><a href="../">&larr; Back to flights guide</a></p>
</main>

{FOOTER}
</body>
</html>
'''

# Build all corridor pages
for slug, cfg in CORRIDORS.items():
    out_dir = OUT / slug
    out_dir.mkdir(exist_ok=True)
    (out_dir / "index.html").write_text(render_corridor(slug, cfg))
    print(f"wrote /flights/{slug}/index.html")
