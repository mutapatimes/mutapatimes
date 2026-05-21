#!/usr/bin/env python3
"""Build the /moving-to-zimbabwe/ microsite.

Evergreen guides for British citizens moving to or living in Zimbabwe.
Purely SEO-driven entry funnel — not linked from main nav, but discoverable
via sitemap, footer, and Google. Each guide targets a specific long-tail
query and links internally to siblings + relevant live data pages on the
main site.

Verified facts come from the June 2024 gov.uk "Living in Zimbabwe" /
"Zimbabwe: doctors and medical facilities" guidance. Where a figure may
have shifted since then (visa fees, school fee bands, ZiG/USD rate), the
text either dates the source or points the reader to /fx.

Output: /moving-to-zimbabwe/index.html + one .html per guide.
"""
import html
import json
import os
import re

ROOT = os.path.join(os.path.dirname(__file__), "..")
OUT_DIR = os.path.join(ROOT, "moving-to-zimbabwe")
BASE_URL = "https://www.mutapatimes.com"

GUIDES = [
    {
        "slug": "visa-on-arrival",
        "title": "Zimbabwe visa on arrival for UK citizens",
        "h1": "Zimbabwe visa on arrival: a UK citizen's guide",
        "description": (
            "British passport holders cannot apply at the Zimbabwean Embassy in London. "
            "Most arrive on a visa on arrival at Harare or Victoria Falls. What it costs, "
            "what to bring, and how to avoid the overstay trap."
        ),
        "standfirst": (
            "The Zimbabwean Embassy in London no longer issues visas. Almost every "
            "British visitor now arrives on the visa on arrival service at Harare or "
            "Victoria Falls airports. Done right, it is a five-minute counter transaction. "
            "Done wrong, it is the reason for the deportations the British Embassy quietly "
            "spends most of its consular time on."
        ),
        "sections": [
            ("Do you actually need a visa?",
             "<p>Yes. Every British passport holder needs a visa to enter Zimbabwe. "
             "There is no visa waiver, and no e-visa is required in advance for tourist "
             "visits — the standard route is to buy the visa at the airport on arrival. "
             "If you are arriving overland from Zambia, South Africa or Mozambique, the "
             "same visa is issued at the land border post. Business, work and study "
             "visits require a different visa category and cannot be activated at the "
             "counter; you need to coordinate with the Department of Immigration "
             "beforehand.</p>"),
            ("What it costs",
             "<p>Per the UK Foreign, Commonwealth & Development Office guidance current "
             "as of June 2024, the visa on arrival fees were:</p>"
             "<ul>"
             "<li><strong>Single entry visa:</strong> US$55 (service charge included)</li>"
             "<li><strong>Double entry visa:</strong> US$70 (service charge included)</li>"
             "</ul>"
             "<p>Bring the fee in <strong>US dollars, in small notes</strong>. The "
             "counter rarely gives change, and credit-card payment is unreliable even "
             "where machines are present. UK debit cards will sometimes be declined "
             "outright at the airport — not because of fraud blocks, but because the "
             "terminal is offline. Carry the exact amount per traveller, plus a small "
             "buffer in case fees have moved since the gov.uk page was last updated. "
             "Verify the current price on "
             "<a href=\"https://www.evisa.gov.zw/home\" rel=\"noopener\" target=\"_blank\">"
             "evisa.gov.zw</a> before you fly.</p>"),
            ("What to bring to the counter",
             "<ul>"
             "<li>UK passport with at least six months' validity beyond your intended "
             "departure date and at least one blank page</li>"
             "<li>Return or onward ticket (the counter occasionally asks for proof)</li>"
             "<li>The address where you will stay in Zimbabwe — hotel name and suburb "
             "or full residential address is sufficient</li>"
             "<li>The visa fee in US dollars, in $5, $10 and $20 notes</li>"
             "</ul>"
             "<p>You will not be asked for yellow-fever certification unless you have "
             "arrived from a transmission country in the prior six days. Check the "
             "current "
             "<a href=\"https://www.gov.uk/foreign-travel-advice/zimbabwe\" rel=\"noopener\" target=\"_blank\">"
             "Zimbabwe Travel Advice</a> before flying.</p>"),
            ("How long can you stay?",
             "<p>The standard entry permission is 30 days, stamped at the port of entry. "
             "<strong>Check the date the immigration officer writes into your passport</strong> "
             "— it is occasionally less than 30 days for reasons that are not always "
             "explained, and the date in your passport, not the policy on the website, "
             "is what governs your stay. If 30 days is not enough, you can apply to "
             "extend or renew at the Department of Immigration headquarters in Harare. "
             "Do not assume the extension is automatic; apply at least a week before "
             "the existing stamp expires.</p>"),
            ("The overstay trap",
             "<p>This is the single most common mistake British citizens make in "
             "Zimbabwe, and the FCDO flags it explicitly in its guidance. If you "
             "overstay your visa, even by a day, you can be arrested at the port of "
             "exit, fined, and deported. Subsequent visa applications are then flagged. "
             "The same applies to working — even unpaid volunteering or missionary "
             "work over 30 days counts as work and requires a temporary employment "
             "permit. A tourist visa does not allow you to take up any form of "
             "employment, paid or unpaid.</p>"),
            ("Work and residence permits",
             "<p>If you intend to live in Zimbabwe long-term, you will need to deal "
             "with the Department of Immigration directly rather than at the airport. "
             "Work permits, residence permits and renewals are handled at:</p>"
             "<div class=\"contact-block\">"
             "<p><strong>Department of Immigration Headquarters</strong><br>"
             "Corner Herbert Chitepo and Leopold Takawira, Harare<br>"
             "Email: <a href=\"mailto:admin@evisa.gov.zw\">admin@evisa.gov.zw</a><br>"
             "Telephone: +263 (242) 971911<br>"
             "Open Monday to Friday, 8am to 4pm Zimbabwean time, except public holidays.</p>"
             "</div>"
             "<p>The British Embassy in Harare does <em>not</em> issue work or residence "
             "permits and cannot intervene in immigration decisions. You will need to "
             "engage directly with the Department, or via a Zimbabwean immigration "
             "lawyer.</p>"),
        ],
        "sources": [
            ("UK FCDO — Living in Zimbabwe (June 2024)",
             "https://www.gov.uk/guidance/living-in-zimbabwe"),
            ("Zimbabwe e-Visa portal",
             "https://www.evisa.gov.zw/home"),
            ("Zimbabwe Travel Advice (FCDO)",
             "https://www.gov.uk/foreign-travel-advice/zimbabwe"),
        ],
    },
    {
        "slug": "healthcare-and-medical-aid",
        "title": "Healthcare and medical aid in Zimbabwe for UK expats",
        "h1": "Healthcare in Zimbabwe for UK expats",
        "description": (
            "Zimbabwe and the UK have no reciprocal NHS agreement. UK travel insurance "
            "does not cover residents. A guide to the four main medical aid providers, "
            "the South Africa evacuation question, and what to budget."
        ),
        "standfirst": (
            "There is no NHS reciprocal arrangement with Zimbabwe, and standard UK "
            "travel insurance stops covering you the moment you become resident. "
            "Most working expats are covered by a local medical aid plan, usually "
            "provided as part of an employment package, but the products themselves "
            "are unfamiliar to anyone arriving from the British system. Here is how "
            "the market is structured, what to expect, and where the gaps are."
        ),
        "sections": [
            ("Medical aid is not insurance",
             "<p>The Zimbabwean concept of a <em>medical aid society</em> is closer to "
             "a US-style HMO than UK private health insurance. You pay a monthly "
             "contribution; in exchange, the society either pays the provider directly "
             "or reimburses you, subject to a benefit schedule. Plans range from "
             "basic outpatient cover to comprehensive packages including hospital, "
             "dental, optical, chronic medication and evacuation. Coverage is highly "
             "variable between tiers, and you should read the benefit schedule line by "
             "line — particularly for chronic conditions, cancer care and any planned "
             "procedure.</p>"),
            ("The four main providers",
             "<p>The UK FCDO highlights four medical aid providers used by British "
             "nationals in Zimbabwe:</p>"
             "<ul>"
             "<li><a href=\"https://www.cimas.co.zw/\" rel=\"noopener\" target=\"_blank\">"
             "<strong>Cimas</strong></a> — the largest medical aid society in the "
             "country, with the widest provider network</li>"
             "<li><a href=\"https://www.healthinternational.co/\" rel=\"noopener\" target=\"_blank\">"
             "<strong>Health International</strong></a> — popular with expats for its "
             "regional coverage</li>"
             "<li><a href=\"https://www.masca.healthcare/contact\" rel=\"noopener\" target=\"_blank\">"
             "<strong>Masca</strong></a></li>"
             "<li><a href=\"https://www.generationhealth.co.zw/\" rel=\"noopener\" target=\"_blank\">"
             "<strong>Generation Health</strong></a></li>"
             "</ul>"
             "<p>If your Zimbabwean employer offers medical aid as part of the salary "
             "package — which most do — confirm which society, which plan tier, and "
             "what is excluded. A plan that covers you adequately in Harare may not "
             "cover the same care in Bulawayo or Mutare, and almost all base-tier "
             "plans exclude evacuation outside Zimbabwe.</p>"),
            ("Why the South Africa evacuation matters",
             "<p>The FCDO specifically advises that any private medical cover for "
             "Zimbabwe should include provision for treatment in South Africa in the "
             "case of serious illness or injury. Tertiary care in Zimbabwe — trauma, "
             "complex surgery, oncology, cardiac — is concentrated in a small number "
             "of private facilities and is frequently capacity-constrained. For "
             "anything beyond routine, Johannesburg or Cape Town is the standard "
             "evacuation destination. A medical aid plan without cross-border "
             "evacuation will leave you paying out of pocket at the worst possible "
             "moment, and the bills run in the tens of thousands of US dollars.</p>"),
            ("What the system looks like on the ground",
             "<p>The FCDO is candid: provision is variable, drug stocks are uneven, "
             "and the best private hospitals are often full. Private clinics generally "
             "require payment up front, frequently in cash, before they will admit "
             "even an emergency case. An increasing number of medical providers will "
             "only accept US dollars in cash, not card. <strong>Always carry an "
             "emergency cash float in small US dollar notes.</strong> Even with "
             "medical aid, access can hinge on the provider trusting that your society "
             "will settle the claim — which is not always the assumption.</p>"
             "<p>Public hospitals exist and are nominally free or low-cost, but trained "
             "staff and drug supply are inconsistent. UK expats typically rely on the "
             "private system in practice.</p>"),
            ("Medicine and prescriptions",
             "<p>Bring enough of any prescription medicine to last several weeks past "
             "your arrival, with a copy of the prescription and the GP letter. Many "
             "UK brand names are not stocked in Zimbabwe; generic equivalents are "
             "usually available but a direct switch is your call to make with a doctor, "
             "not the pharmacy counter. Read NHS guidance on "
             "<a href=\"https://www.nhs.uk/common-health-questions/medicines/can-i-take-my-medicine-abroad\" "
             "rel=\"noopener\" target=\"_blank\">travelling with medicines</a> before "
             "you fly — certain medications you can buy over the counter in the UK "
             "are controlled substances in Zimbabwe.</p>"),
            ("Finding an English-speaking doctor",
             "<p>The FCDO maintains a current "
             "<a href=\"https://www.gov.uk/government/publications/zimbabwe-list-of-medical-facilities\" "
             "rel=\"noopener\" target=\"_blank\">list of English-speaking medical "
             "facilities</a> used by British nationals. Avicenna Medical Centre on "
             "Borrowdale Road in Harare's Gunhill suburb is the FCDO's most-cited "
             "first-line option for British arrivals; Drs Campbell and Cowper in "
             "Avondale are listed for gynaecology. The list is short and not "
             "exhaustive — most expats build their own panel of doctors via "
             "word of mouth in the first few months.</p>"),
        ],
        "sources": [
            ("UK FCDO — Living in Zimbabwe: Healthcare (June 2024)",
             "https://www.gov.uk/guidance/living-in-zimbabwe"),
            ("UK FCDO — Zimbabwe list of medical facilities",
             "https://www.gov.uk/government/publications/zimbabwe-list-of-medical-facilities"),
            ("NHS — Moving abroad",
             "https://www.nhs.uk/using-the-nhs/healthcare-abroad/moving-abroad/planning-your-healthcare/"),
        ],
    },
    {
        "slug": "international-schools",
        "title": "International schools in Zimbabwe for British families",
        "h1": "International schools in Zimbabwe: a guide for British families",
        "description": (
            "Most Zimbabwean private schools follow the Cambridge or ZIMSEC curriculum. "
            "What British families need to know about the IB option, the French school, "
            "boarding schools, fees and term calendars."
        ),
        "standfirst": (
            "Zimbabwe's private school system is one of the practical reasons British "
            "families end up staying longer than they planned. The Cambridge "
            "curriculum is widely available, the boarding tradition is intact, and "
            "fees in US dollars sit well below the equivalent UK independent schools. "
            "But the system is not a one-to-one substitute, and the choices to make "
            "before you arrive are different from the ones at home."
        ),
        "sections": [
            ("ZIMSEC, Cambridge — and the IB exception",
             "<p>Two examination systems dominate Zimbabwean schools. <strong>ZIMSEC</strong> "
             "is the local board, used by the majority of government and some private "
             "schools. <strong>Cambridge International</strong> (IGCSE and A-Level) is "
             "used by most of the established private schools that British and "
             "international families default to, and is portable straight back into "
             "the UK university system. A handful of schools offer the International "
             "Baccalaureate instead — most prominently Harare International School.</p>"
             "<p>If you intend to return your child to the UK during secondary school, "
             "Cambridge is the path of least friction. If they will finish school in "
             "Zimbabwe or transfer onward to North America or continental Europe, the "
             "IB at HIS is the broader passport.</p>"),
            ("Harare International School",
             "<p><a href=\"https://www.harare-international-school.com/\" rel=\"noopener\" target=\"_blank\">"
             "Harare International School</a> is the country's only full IB school, "
             "running the Primary Years, Middle Years and Diploma programmes. It is "
             "the school British diplomatic and NGO families most often default to, "
             "partly for the curriculum and partly because it follows the Northern "
             "Hemisphere calendar — the school year runs roughly mid-August to "
             "mid-June, aligned with the UK. This matters when you are mid-transfer: "
             "you do not lose a term in either direction.</p>"
             "<p>Fees are quoted in US dollars and verified directly with the school. "
             "Application is competitive; British families coming on a posting should "
             "engage with admissions as soon as the move is confirmed.</p>"),
            ("The French school",
             "<p>The <a href=\"https://www.facebook.com/FrenchSchoolHarare\" rel=\"noopener\" target=\"_blank\">"
             "Ecole française de Harare</a> is accredited by the French Ministry of "
             "Education and follows the French curriculum. For British families with "
             "French as a second language at home, or for binational households, it "
             "is the practical alternative to HIS. It does not run a UK-equivalent "
             "track.</p>"),
            ("The Cambridge private school circuit",
             "<p>Zimbabwe's traditional private day and boarding schools — the ones "
             "that have been operating for decades, in some cases more than a century — "
             "are predominantly Cambridge IGCSE/A-Level. They are listed in the "
             "<a href=\"https://www.atschisz.co.zw/schools-directory/\" rel=\"noopener\" target=\"_blank\">"
             "Association of Trust Schools directory</a>, which is the closest thing "
             "to a definitive listing. The Harare cluster (Borrowdale, Avondale, "
             "Highlands) and the Bulawayo cluster are where most British arrivals "
             "look first. Visit before you commit; reputation and current quality are "
             "not always the same thing.</p>"),
            ("Boarding schools — the conversation to have",
             "<p>Zimbabwe has a long boarding-school tradition, mostly outside Harare "
             "and Bulawayo. For UK families used to the British prep-and-public-school "
             "ladder, the model is familiar, but two things differ:</p>"
             "<ul>"
             "<li>Pastoral care infrastructure varies considerably between schools — "
             "more so than in the UK, where the inspection regime is uniform</li>"
             "<li>Distance from medical care is a real consideration outside the "
             "major cities, given the healthcare gaps the FCDO flags</li>"
             "</ul>"
             "<p>The FCDO advice is unambiguous: visit any boarding school in person "
             "before enrolling, talk to current parents, and make sure your child has "
             "a direct, reliable way to contact a responsible parent or family member "
             "in Zimbabwe — not just the school office — at all times. This is not "
             "the default in the UK system and you may need to ask for it explicitly.</p>"),
            ("Government schools",
             "<p>Zimbabwe has a network of <a href=\"http://mopse.co.zw/provinces-and-districts/schools-province-district\" "
             "rel=\"noopener\" target=\"_blank\">government schools</a>, mostly ZIMSEC "
             "curriculum, with fees substantially lower than the private circuit. "
             "British families on shorter postings rarely use them, but they exist "
             "and a small number have a strong academic record. Fee verification and "
             "site visits are essential.</p>"),
            ("Fees: how to find them",
             "<p>School fees in Zimbabwe change frequently and are not always "
             "advertised in advance. <strong>Contact each school directly</strong> for "
             "the current term's quoted fee, the currency of payment (most accept "
             "USD; some accept ZiG; the mix is school-specific), and any boarding, "
             "uniform and capital levies. Do this before you agree relocation terms "
             "with a UK employer — school fees are a meaningful part of an expat "
             "compensation package and quoted figures from a year ago will be out of "
             "date.</p>"),
        ],
        "sources": [
            ("UK FCDO — Living in Zimbabwe: Studying (June 2024)",
             "https://www.gov.uk/guidance/living-in-zimbabwe"),
            ("Association of Trust Schools (ATS) directory",
             "https://www.atschisz.co.zw/schools-directory/"),
            ("Ministry of Primary and Secondary Education",
             "http://mopse.co.zw/provinces-and-districts/schools-province-district"),
            ("Harare International School",
             "https://www.harare-international-school.com/"),
        ],
    },
    {
        "slug": "money-and-banking",
        "title": "Money and banking in Zimbabwe for UK arrivals",
        "h1": "Money and banking in Zimbabwe for UK arrivals",
        "description": (
            "Zimbabwe Gold (ZiG) is the primary legal tender but US dollars circulate "
            "alongside, and both use the dollar sign. A practical guide to currency, "
            "cards, money transfer and bank accounts for British arrivals."
        ),
        "standfirst": (
            "Zimbabwe runs a dual-currency economy. The Zimbabwe Gold (ZiG) is the "
            "primary legal tender, but US dollars circulate alongside it for most "
            "everyday transactions. Both use the dollar sign. This single fact is "
            "the source of most of the misunderstandings British arrivals have at "
            "the till, the petrol station and the airport taxi rank."
        ),
        "sections": [
            ("Two currencies, one dollar sign",
             "<p>The official primary legal tender in Zimbabwe is the Zimbabwe Gold "
             "(ZiG), introduced in April 2024 to replace the previous Zimbabwean "
             "dollar. US dollars remain accepted across most of the formal economy "
             "and dominate large or business-to-business transactions. <strong>Both "
             "currencies are written with the $ symbol</strong>, which means a price "
             "tag of \"$5\" might mean five US dollars or five ZiG depending on the "
             "vendor. Always confirm which currency a price is quoted in before you "
             "hand over notes.</p>"
             "<p>The official ZiG/USD rate is set by the Reserve Bank of Zimbabwe and "
             "moves frequently. Check the current rate on "
             "<a href=\"/fx\">The Mutapa Times FX page</a> before any meaningful "
             "transaction.</p>"),
            ("Cash, cards and what businesses actually take",
             "<p>Card acceptance in Zimbabwe is more limited than UK arrivals expect. "
             "Larger supermarkets, hotels in the major chains, and formal restaurants "
             "in Harare and Bulawayo will usually accept UK-issued Visa and Mastercard. "
             "But many businesses — including, the FCDO notes, some medical "
             "providers — accept US dollars in cash only. Petrol stations, taxis, and "
             "smaller retailers are almost universally cash. Carry small US dollar "
             "notes ($1, $5, $10, $20). Larger denominations are often refused for "
             "low-value transactions because change is not available, particularly "
             "in dollars.</p>"),
            ("Money transfer: Mukuru and Western Union",
             "<p>The two most widely used international remittance services in "
             "Zimbabwe are:</p>"
             "<ul>"
             "<li><a href=\"https://www.mukuru.com/zw/find-us/branches/\" rel=\"noopener\" target=\"_blank\">"
             "<strong>Mukuru</strong></a> — used heavily by the Zimbabwean diaspora, "
             "with a dense branch network and competitive rates for GBP-to-ZWL "
             "transfers</li>"
             "<li><a href=\"https://www.westernunion.com/gb/en/home.html\" rel=\"noopener\" target=\"_blank\">"
             "<strong>Western Union</strong></a> — the most established and the "
             "default for one-off transfers from the UK</li>"
             "</ul>"
             "<p>Wise and Revolut work to a degree for receiving funds via Zimbabwean "
             "bank accounts, but coverage is partial and rates are not always "
             "competitive against Mukuru for GBP-to-Zimbabwe specifically. Compare "
             "rates per-transaction.</p>"),
            ("Opening a Zimbabwean bank account",
             "<p>Documentation requirements vary by bank. The Reserve Bank of "
             "Zimbabwe publishes a current "
             "<a href=\"https://www.rbz.co.zw/index.php/regulation-supervision/regulation-supervision/banking-institutions\" "
             "rel=\"noopener\" target=\"_blank\">list of operational banking "
             "institutions</a>. Expect to provide your passport, a Zimbabwean "
             "residence permit or work permit, proof of address (a utility bill or "
             "landlord letter), and in some cases a reference from your employer. "
             "Account opening on a tourist visa is generally not possible at the "
             "main retail banks.</p>"),
            ("Foreign exchange is regulated",
             "<p>It is illegal to exchange foreign currency in Zimbabwe anywhere "
             "other than at a licensed dealer — a bank or a registered bureau de "
             "change. The informal street-side rate is occasionally better than the "
             "official rate, but transacting on it puts you in breach of the "
             "Exchange Control Act and the consequences include fines and "
             "confiscation. For visitors and short-term residents, the practical "
             "implication is simple: change money at the airport, your hotel, your "
             "bank, or a registered bureau. Do not change money on the street.</p>"),
        ],
        "sources": [
            ("UK FCDO — Living in Zimbabwe: Money and banking (June 2024)",
             "https://www.gov.uk/guidance/living-in-zimbabwe"),
            ("Reserve Bank of Zimbabwe — operational banking institutions",
             "https://www.rbz.co.zw/index.php/regulation-supervision/regulation-supervision/banking-institutions"),
            ("The Mutapa Times — live FX rates",
             "/fx"),
        ],
    },
    {
        "slug": "driving-and-vehicle-import",
        "title": "Driving in Zimbabwe on a UK licence",
        "h1": "Driving in Zimbabwe with a UK licence",
        "description": (
            "You can drive in Zimbabwe on a UK or International Driving Permit for "
            "12 months, then you need a Zimbabwean licence from CVR. The 12-month "
            "rule, vehicle import, and what to watch on the road."
        ),
        "standfirst": (
            "British arrivals can drive in Zimbabwe on their existing UK licence for "
            "up to twelve months from arrival. After that, the Central Vehicle "
            "Registry expects you to convert to a Zimbabwean licence. The deadline "
            "is firm, the conversion is inconvenient if you leave it late, and the "
            "missed-deadline conversation with traffic police is one most people "
            "would rather avoid."
        ),
        "sections": [
            ("The 12-month rule",
             "<p>Non-Zimbabweans and diplomats are permitted to drive in Zimbabwe "
             "using a foreign driver's licence or an International Driving Permit "
             "(IDP) for up to twelve months from the date of entry. After that, you "
             "are expected to hold a Zimbabwean driver's licence, issued by the "
             "<a href=\"http://www.transcom.gov.zw/central-vehicle-registry-cvr/\" "
             "rel=\"noopener\" target=\"_blank\">Central Vehicle Registry (CVR)</a>. "
             "The twelve months runs from your entry date, not from the date you "
             "decided to stay long-term — start the conversion process by month nine "
             "to comfortably finish in time.</p>"
             "<p>If you are asked at a roadblock for a letter authenticating or "
             "validating your UK licence, you should refer the request to the "
             "<a href=\"https://www.gov.uk/contact-the-dvla\" rel=\"noopener\" target=\"_blank\">"
             "DVLA</a>. The British Embassy in Harare does not issue this "
             "letter.</p>"),
            ("International Driving Permit: do you need one?",
             "<p>An IDP issued in the UK by the AA or the Post Office is widely "
             "recognised by Zimbabwean traffic police and is useful at roadblocks "
             "because it includes the standard pictogram categories. The UK licence "
             "alone is legally sufficient within the 12-month window, but the IDP "
             "smooths roadblock interactions in a country where photo ID translation "
             "is occasionally a source of dispute. The IDP is cheap, valid for 12 "
             "months, and worth carrying.</p>"),
            ("Applying for a Zimbabwean driver's licence",
             "<p>The CVR conversion process for holders of a foreign licence is more "
             "administrative than re-testing. Expect:</p>"
             "<ul>"
             "<li>Your original UK licence (photocard and counterpart, if you still "
             "have the counterpart)</li>"
             "<li>Passport and residence/work permit</li>"
             "<li>A Class 4 medical certificate from a registered doctor (vision, "
             "general fitness)</li>"
             "<li>Provisional learner test, eye test, and a practical demonstration "
             "depending on the examiner</li>"
             "<li>Fees in ZiG or USD, depending on the office</li>"
             "</ul>"
             "<p>The specific requirements have shifted over the past two years as "
             "CVR has digitised, so confirm directly with CVR or with the British "
             "Embassy's commercial section before queuing.</p>"),
            ("Importing a UK vehicle",
             "<p>If you intend to ship your UK car, follow the UK guidance on "
             "<a href=\"https://www.gov.uk/taking-vehicles-out-of-uk\" rel=\"noopener\" target=\"_blank\">"
             "taking vehicles out of the UK</a> first. On the Zimbabwean side, the "
             "vehicle goes through ZIMRA customs at the port of entry (most cars "
             "come in via Beitbridge or Plumtree from South Africa, occasionally via "
             "Durban-Beitbridge). Duty rates depend on engine size and vehicle age "
             "and are levied in US dollars. Used vehicles older than ten years face "
             "import restrictions that change periodically; check the current "
             "ZIMRA position before you ship.</p>"
             "<p>The practical question is whether shipping makes sense at all. The "
             "Zimbabwean second-hand market is liquid, and imported Japanese stock "
             "via Durban dominates the price-quality frontier. Most British arrivals "
             "buy locally rather than ship.</p>"),
            ("Insurance",
             "<p>Third-party motor insurance is compulsory in Zimbabwe and must be "
             "purchased from a local insurer. Most domestic underwriters offer "
             "comprehensive cover, though the claims experience is variable and the "
             "FCDO does not endorse any specific provider. Ask your employer or a "
             "local financial adviser for the current short list of insurers used by "
             "the expat community.</p>"),
            ("On the road",
             "<p>Zimbabwe drives on the left, the same as the UK. The standard "
             "hazards: pedestrians and livestock on rural roads, unlit vehicles at "
             "night, pothole damage even on major routes, and roadblocks operated by "
             "the Zimbabwe Republic Police (ZRP) where document checks are routine. "
             "Carry your licence, passport, vehicle registration and a current "
             "insurance certificate at all times. The FCDO's "
             "<a href=\"https://www.gov.uk/foreign-travel-advice/zimbabwe/safety-and-security#road-travel\" "
             "rel=\"noopener\" target=\"_blank\">road travel advice</a> is updated "
             "regularly and worth reading before any long drive.</p>"),
            ("Blue Badge holders",
             "<p>If you hold a UK Blue Badge and become resident in Zimbabwe, the "
             "<a href=\"https://www.gov.uk/government/collections/blue-badge-scheme\" "
             "rel=\"noopener\" target=\"_blank\">scheme</a> requires you to return "
             "it to the original UK issuing authority. Zimbabwe does not operate a "
             "directly equivalent national parking scheme.</p>"),
        ],
        "sources": [
            ("UK FCDO — Living in Zimbabwe: Driving (June 2024)",
             "https://www.gov.uk/guidance/living-in-zimbabwe"),
            ("Central Vehicle Registry (CVR)",
             "http://www.transcom.gov.zw/central-vehicle-registry-cvr/"),
            ("UK Government — Driving abroad",
             "https://www.gov.uk/driving-abroad"),
        ],
    },
]


# ── HTML template helpers ──────────────────────────────────────

def esc(s):
    """HTML-escape attribute and text content."""
    return html.escape(s, quote=True)


def render_head(title, description, canonical_path):
    """The <head> block shared across all microsite pages."""
    canonical_url = f"{BASE_URL}{canonical_path}"
    schema_article = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title,
        "description": description,
        "url": canonical_url,
        "mainEntityOfPage": {"@type": "WebPage", "@id": canonical_url},
        "publisher": {
            "@type": "Organization",
            "name": "The Mutapa Times",
            "logo": {
                "@type": "ImageObject",
                "url": f"{BASE_URL}/img/logo.png",
            },
        },
        "inLanguage": "en",
        "author": {
            "@type": "Organization",
            "name": "The Mutapa Times Editorial",
        },
        "articleSection": "Guide",
    }
    breadcrumb = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home",
             "item": f"{BASE_URL}/"},
            {"@type": "ListItem", "position": 2, "name": "Moving to Zimbabwe",
             "item": f"{BASE_URL}/moving-to-zimbabwe/"},
            {"@type": "ListItem", "position": 3, "name": title,
             "item": canonical_url},
        ],
    }
    return f"""<!doctype html>
<html class="no-js" lang="en">
<head>
    <meta charset="utf-8">
    <title>{esc(title)} | The Mutapa Times</title>
    <link rel="canonical" href="{esc(canonical_url)}">
    <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
    <link rel="manifest" href="../site.webmanifest">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-title" content="Mutapa Times">
    <link rel="apple-touch-icon" href="../icon.png">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Playfair+Display:ital,wght@0,400;0,700;0,900;1,400&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css" media="print" onload="this.media='all'"><noscript><link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css"></noscript>
    <link rel="stylesheet" href="../css/normalize.css">
    <link rel="stylesheet" href="../css/main.css?v=102">
    <meta name="description" content="{esc(description)}">
    <meta name="robots" content="index, follow">
    <meta name="author" content="The Mutapa Times">
    <meta property="og:type" content="article">
    <meta property="og:title" content="{esc(title)} | The Mutapa Times">
    <meta property="og:description" content="{esc(description)}">
    <meta property="og:url" content="{esc(canonical_url)}">
    <meta property="og:site_name" content="The Mutapa Times">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:site" content="@mutapatimes">
    <meta name="twitter:title" content="{esc(title)} | The Mutapa Times">
    <meta name="twitter:description" content="{esc(description)}">
    <link rel="icon" type="image/png" sizes="32x32" href="../img/favicon-32x32.png">
    <link rel="icon" type="image/png" sizes="16x16" href="../img/favicon-16x16.png">
    <meta name="theme-color" content="#1a1a1a">
    <link rel="alternate" type="application/rss+xml" title="The Mutapa Times" href="{BASE_URL}/feed.xml">
    <link rel="alternate" hreflang="en" href="{esc(canonical_url)}">
    <link rel="alternate" hreflang="x-default" href="{esc(canonical_url)}">
<script type="application/ld+json">{json.dumps(schema_article, ensure_ascii=False)}</script>
<script type="application/ld+json">{json.dumps(breadcrumb, ensure_ascii=False)}</script>
<style>
.uk-guide-header {{ margin: 2rem 0 2.5rem; }}
.uk-guide-eyebrow {{ font-size: 0.8rem; letter-spacing: 0.12em; text-transform: uppercase;
  color: #6b6b6b; margin: 0 0 0.75rem; font-family: 'Inter', sans-serif; }}
.uk-guide-title {{ font-family: 'Playfair Display', serif; font-size: 2.4rem; line-height: 1.15;
  margin: 0 0 1rem; font-weight: 700; }}
.uk-guide-standfirst {{ font-family: 'Playfair Display', serif; font-style: italic;
  font-size: 1.25rem; line-height: 1.45; color: #333; margin: 0; max-width: 38em; }}
.uk-guide-body h2 {{ font-family: 'Playfair Display', serif; font-size: 1.5rem;
  margin: 2.5rem 0 1rem; font-weight: 700; }}
.uk-guide-body p {{ font-family: 'Inter', sans-serif; font-size: 1rem; line-height: 1.65;
  max-width: 38em; margin: 0 0 1rem; }}
.uk-guide-body ul {{ font-family: 'Inter', sans-serif; font-size: 1rem; line-height: 1.65;
  max-width: 38em; margin: 0 0 1.25rem; padding-left: 1.25rem; }}
.uk-guide-body li {{ margin-bottom: 0.4rem; }}
.uk-guide-body a {{ color: #1a4a8a; text-decoration: underline; }}
.uk-guide-body .contact-block {{ background: #f7f5ef; border-left: 3px solid #1a1a1a;
  padding: 1rem 1.25rem; margin: 1.5rem 0; max-width: 38em; }}
.uk-guide-body .contact-block p {{ margin: 0; font-size: 0.95rem; line-height: 1.5; }}
.uk-guide-sources {{ margin: 3rem 0 2rem; padding: 1.5rem; background: #f7f5ef;
  max-width: 38em; }}
.uk-guide-sources h2 {{ font-size: 1.1rem; margin: 0 0 0.75rem; font-family: 'Inter', sans-serif;
  text-transform: uppercase; letter-spacing: 0.08em; }}
.uk-guide-sources ul {{ margin: 0 0 1rem; padding-left: 1.25rem; font-family: 'Inter', sans-serif;
  font-size: 0.92rem; }}
.uk-guide-sources-note {{ font-family: 'Inter', sans-serif; font-size: 0.82rem;
  color: #666; line-height: 1.5; margin: 0; font-style: italic; }}
.uk-guide-siblings {{ margin: 2.5rem 0; padding: 1.5rem; border-top: 1px solid #ddd;
  border-bottom: 1px solid #ddd; max-width: 38em; }}
.uk-guide-siblings-eyebrow {{ font-size: 0.8rem; letter-spacing: 0.12em;
  text-transform: uppercase; color: #6b6b6b; margin: 0 0 0.75rem;
  font-family: 'Inter', sans-serif; }}
.uk-guide-siblings ul {{ margin: 0 0 1rem; padding-left: 1.25rem; font-family: 'Inter', sans-serif; }}
.uk-guide-siblings-back {{ margin: 0; font-family: 'Inter', sans-serif; font-size: 0.92rem; }}
.uk-guide-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 1.25rem; margin: 2rem 0; }}
.uk-guide-card {{ display: block; padding: 1.25rem 1.25rem 1.5rem; background: #f7f5ef;
  border: 1px solid #e5e1d6; text-decoration: none; color: inherit; transition: transform 0.15s ease; }}
.uk-guide-card:hover {{ transform: translateY(-2px); text-decoration: none; }}
.uk-guide-card h3 {{ font-family: 'Playfair Display', serif; font-size: 1.2rem;
  margin: 0 0 0.5rem; line-height: 1.25; }}
.uk-guide-card p {{ font-family: 'Inter', sans-serif; font-size: 0.92rem;
  line-height: 1.45; color: #444; margin: 0 0 0.75rem; }}
.uk-guide-card-read {{ font-family: 'Inter', sans-serif; font-size: 0.85rem;
  color: #1a4a8a; font-weight: 600; }}
.uk-guide-about, .uk-guide-subscribe {{ margin: 2.5rem 0; padding-top: 1.5rem;
  border-top: 1px solid #ddd; max-width: 38em; }}
.uk-guide-about h2, .uk-guide-subscribe h2 {{ font-family: 'Playfair Display', serif;
  font-size: 1.3rem; margin: 0 0 0.75rem; }}
.uk-guide-about p, .uk-guide-subscribe p {{ font-family: 'Inter', sans-serif;
  font-size: 0.95rem; line-height: 1.6; margin: 0 0 0.75rem; }}
@media (max-width: 640px) {{
  .uk-guide-title {{ font-size: 1.8rem; }}
  .uk-guide-standfirst {{ font-size: 1.1rem; }}
}}
</style>
</head>"""


NAV_BLOCK = """<body class="longform-page">
<div class="topbar" id="topbar" aria-label="Sticky navigation">
  <button class="topbar-menu" type="button" data-open-drawer aria-label="Open menu" aria-controls="navDrawer" aria-expanded="false">
    <span></span><span></span><span></span>
  </button>
  <a href="/" class="topbar-brand"><em>The Mutapa Times</em></a>
  <a href="/subscribe" class="topbar-cta">Subscribe</a>
</div>
<div class="paper">
  <a href="/" class="title-link">
    <div class="titleDiv"><h1 class="title notranslate">THE MUTAPA TIMES</h1></div>
    <h4 class="sub notranslate">Zimbabwe outside-in.</h4>
  </a>
  <nav id="mainNav">
    <p><a target="_self" class="notranslate" href="/">News</a></p>
    <p><a target="_self" class="economy-btn" href="/economy">Live Economy Data</a></p>
    <p><a target="_self" class="notranslate" href="/fx">FX</a></p>
    <p><a target="_self" class="notranslate" href="/property">Property</a></p>
    <p><a target="_self" class="notranslate" href="/jobs">Jobs</a></p>
    <p><a target="_self" class="notranslate" href="/articles">Articles</a></p>
  </nav>
  <hr class="topHr">
  <hr class="bottomHr">
  <hr class="dateHr">
"""


FOOTER_BLOCK = """
</div>
<footer class="atlantic-foot">
  <div class="atlantic-foot-inner">
    <div class="atlantic-foot-fine">
      <a href="/authors/">Masthead</a><span class="sep">·</span>
      <a href="/privacy">Privacy</a><span class="sep">·</span>
      <a href="/terms">Terms</a><span class="sep">·</span>
      <a href="/advertising">Advertising guidelines</a><span class="sep">·</span>
      <a href="mailto:news@mutapatimes.com">Contact</a>
    </div>
    <p class="atlantic-foot-copy">&copy; 2020&ndash;2026 The Mutapa Times. All rights reserved. Operated from the United Kingdom.</p>
  </div>
</footer>
<script defer src="../js/nav.js"></script>
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XQPRFK7JTB"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-XQPRFK7JTB');
</script>
</body>
</html>
"""


def render_sibling_nav(current_slug):
    """List of the other guides + a back-to-hub link."""
    siblings = [g for g in GUIDES if g["slug"] != current_slug]
    items = "\n".join(
        f'      <li><a href="./{g["slug"]}.html">{esc(g["h1"])}</a></li>'
        for g in siblings
    )
    return f"""
    <aside class="uk-guide-siblings" aria-label="Related guides">
      <p class="uk-guide-siblings-eyebrow">More in this guide</p>
      <ul>
{items}
      </ul>
      <p class="uk-guide-siblings-back"><a href="./">&larr; Back to Moving to Zimbabwe</a></p>
    </aside>
"""


def render_sources(sources):
    """Sources / further reading block at the foot of each guide."""
    items = "\n".join(
        f'      <li><a href="{esc(href)}" rel="noopener" target="_blank">{esc(label)}</a></li>'
        for label, href in sources
    )
    return f"""
    <section class="uk-guide-sources" aria-label="Sources and further reading">
      <h2>Sources and further reading</h2>
      <ul>
{items}
      </ul>
      <p class="uk-guide-sources-note">Fees, fees schedules and contact details are
      current as of the FCDO's June 2024 guidance and may have changed. Verify
      directly with the relevant authority before acting on anything in this
      guide.</p>
    </section>
"""


def render_guide(guide):
    """Render a single guide page."""
    canonical_path = f"/moving-to-zimbabwe/{guide['slug']}.html"
    sections_html = "\n".join(
        f"      <h2>{esc(heading)}</h2>\n      {body}"
        for heading, body in guide["sections"]
    )
    head = render_head(guide["h1"], guide["description"], canonical_path)
    return (
        head
        + NAV_BLOCK
        + f"""
  <main>
    <article class="article-full uk-guide">
      <nav class="article-breadcrumb" aria-label="Breadcrumb">
        <a href="../index.html">Home</a> <span aria-hidden="true">/</span>
        <a href="./">Moving to Zimbabwe</a> <span aria-hidden="true">/</span>
        <span>{esc(guide['h1'])}</span>
      </nav>
      <header class="uk-guide-header">
        <p class="uk-guide-eyebrow">UK GUIDE &middot; MOVING TO ZIMBABWE</p>
        <h1 class="uk-guide-title">{esc(guide['h1'])}</h1>
        <p class="uk-guide-standfirst">{guide['standfirst']}</p>
      </header>
      <div class="article-body uk-guide-body">
{sections_html}
{render_sources(guide['sources'])}
{render_sibling_nav(guide['slug'])}
      </div>
    </article>
  </main>
"""
        + FOOTER_BLOCK
    )


def render_index():
    """Render the /moving-to-zimbabwe/ hub page."""
    title = "Moving to Zimbabwe: a UK citizen's guide"
    description = (
        "Practical guides for British citizens moving to or living in Zimbabwe, "
        "covering visas, healthcare, schools, money, and driving. Written by "
        "The Mutapa Times using the UK FCDO's June 2024 guidance as a spine."
    )
    cards = "\n".join(
        f"""        <a class="uk-guide-card" href="./{g['slug']}.html">
          <h3>{esc(g['h1'])}</h3>
          <p>{esc(g['description'])}</p>
          <span class="uk-guide-card-read">Read the guide &rarr;</span>
        </a>"""
        for g in GUIDES
    )
    head = render_head(title, description, "/moving-to-zimbabwe/")
    return (
        head
        + NAV_BLOCK
        + f"""
  <main>
    <article class="article-full uk-guide-hub">
      <nav class="article-breadcrumb" aria-label="Breadcrumb">
        <a href="../index.html">Home</a> <span aria-hidden="true">/</span>
        <span>Moving to Zimbabwe</span>
      </nav>
      <header class="uk-guide-header">
        <p class="uk-guide-eyebrow">UK GUIDE</p>
        <h1 class="uk-guide-title">Moving to Zimbabwe</h1>
        <p class="uk-guide-standfirst">Five practical guides for British citizens
          moving to or living in Zimbabwe. We use the UK Foreign, Commonwealth &amp;
          Development Office's June 2024 guidance as a spine and add the
          on-the-ground context a government PDF cannot. Verify fees and figures
          directly with the relevant authority before acting on anything here.</p>
      </header>
      <div class="article-body uk-guide-hub-body">
        <div class="uk-guide-grid">
{cards}
        </div>
        <section class="uk-guide-about">
          <h2>About this guide</h2>
          <p>The Mutapa Times is a Zimbabwean newspaper operated from the United
          Kingdom. We publish this microsite because the British citizens we hear
          from most often arrive in Zimbabwe having read the FCDO guidance and
          still missing the practical details that only come from being in the
          country &mdash; which medical aid plan actually covers Joburg evacuation,
          which schools follow the Northern Hemisphere calendar, what a price tag
          marked &quot;$5&quot; really means at the till.</p>
          <p>The guides are written editorially. We do not earn affiliate commission
          on any provider mentioned, and the FCDO has not reviewed or endorsed this
          content. If you spot something out of date, email
          <a href="mailto:news@mutapatimes.com">news@mutapatimes.com</a>.</p>
        </section>
        <section class="uk-guide-subscribe">
          <h2>Get our weekly briefing</h2>
          <p>If you are planning a move to Zimbabwe or already here, our twice-weekly
          newsletter covers the news that affects you &mdash; FX moves, policy
          changes, and the stories Zimbabwe&rsquo;s English-language papers do not
          carry. <a href="/subscribe">Subscribe here</a>.</p>
        </section>
      </div>
    </article>
  </main>
"""
        + FOOTER_BLOCK
    )


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    written = []
    index_path = os.path.join(OUT_DIR, "index.html")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(render_index())
    written.append(index_path)
    for guide in GUIDES:
        path = os.path.join(OUT_DIR, f"{guide['slug']}.html")
        with open(path, "w", encoding="utf-8") as f:
            f.write(render_guide(guide))
        written.append(path)
    print(f"Wrote {len(written)} files to /moving-to-zimbabwe/:")
    for p in written:
        print(f"  {os.path.relpath(p, ROOT)}")


if __name__ == "__main__":
    main()
