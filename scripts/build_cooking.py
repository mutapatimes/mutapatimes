#!/usr/bin/env python3
"""Build /cooking/ — the Mutapa Times Zimbabwean recipe guide.

10 authentic Zimbabwean dishes, each with full ingredient list, step-by-step
method, calorie estimate, cultural context and Recipe schema markup so
Google can show rich snippets. Hub page lists all recipes with cards.

Image convention: drop a photo at /img/cooking/<slug>.jpg and rebuild
to attach (filesystem check at render). Hub banner: /img/cooking/_hero.jpg.

Calorie estimates are computed by summing per-ingredient kcal from a
simple lookup table (USDA-derived round numbers) and dividing by the
declared serves count. Marked clearly as estimates on each page.
"""
import datetime, html, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT  = ROOT / "cooking"
OUT.mkdir(exist_ok=True)
TODAY = datetime.date.today().isoformat()

# Recent news for hub footer
WIRES = ROOT / "content" / "wires"
news_index = []
if WIRES.exists():
    for p in WIRES.glob("*.md"):
        try: news_index.append(p)
        except Exception: pass

def latest_news(max_n=6):
    out = []
    for p in news_index:
        m = re.match(r'(\d{4}-\d{2}-\d{2})-(.+)', p.stem)
        if not m: continue
        title = None
        try:
            parts = p.read_text(errors="ignore").split("---", 2)
            if len(parts) >= 3:
                tm = re.search(r'^title:\s*"?([^"\n]+)"?', parts[1], re.M)
                if tm: title = tm.group(1).strip().rstrip('"')
        except Exception: pass
        if not title: title = m.group(2).replace("-", " ").capitalize()
        out.append({"date": m.group(1), "title": title, "file": p.stem})
    out.sort(key=lambda h: h["date"], reverse=True)
    return out[:max_n]

# Calorie lookup (kcal per 100g or per unit) for the common Zimbabwean pantry
KCAL_PER_100G = {
    "maize meal": 355, "white maize": 355, "yellow maize": 365,
    "beef": 250, "chicken": 165, "kapenta": 380, "mopane worms": 290,
    "peanut butter": 588, "groundnut": 567, "peanuts": 567,
    "onion": 40, "tomato": 18, "garlic": 149, "ginger": 80,
    "salt": 0, "pepper": 0, "stock cube": 17,
    "vegetable oil": 884, "sunflower oil": 884, "cooking oil": 884,
    "butter": 717, "milk": 60, "water": 0,
    "spinach": 23, "collard greens": 32, "muriwo": 32, "pumpkin leaves": 32,
    "covo": 32, "rape leaves": 32, "amaranth": 23,
    "flour": 364, "bread flour": 364, "sugar": 387, "yeast": 325,
    "egg": 155, "rice": 130,
    "potato": 77, "pumpkin": 26, "carrot": 41,
    "cabbage": 25, "bean": 347, "beans": 347, "sugar beans": 347,
    "samp": 350, "millet": 378, "sorghum": 339,
    "popcorn": 387, "dried maize": 365,
}

def kcal_for(qty_g, ingredient_lower):
    """Best-effort: match an ingredient string against the lookup table."""
    for key, kcal100 in KCAL_PER_100G.items():
        if key in ingredient_lower:
            return (qty_g / 100.0) * kcal100
    return 0

def estimate_calories(ingredient_lines, serves):
    """Each ingredient line has format like '500g beef chuck, diced' or
    '2 tbsp peanut butter'. Returns approximate kcal/serving."""
    total = 0.0
    for line in ingredient_lines:
        l = line.lower()
        # Grams: "500g", "200 g", "1.5 kg"
        m = re.search(r'(\d+(?:\.\d+)?)\s*(kg|g)\b', l)
        if m:
            qty = float(m.group(1))
            if m.group(2) == "kg": qty *= 1000
            total += kcal_for(qty, l)
            continue
        # Tablespoons of oil/butter/PB: ~14g each
        m = re.search(r'(\d+(?:\.\d+)?)\s*tbsp', l)
        if m:
            qty_g = float(m.group(1)) * 14
            total += kcal_for(qty_g, l)
            continue
        # Cups: rough ~150g for grains, ~240g for liquid
        m = re.search(r'(\d+(?:\.\d+)?)\s*cup', l)
        if m:
            qty_g = float(m.group(1)) * 150
            total += kcal_for(qty_g, l)
            continue
        # Eggs: ~70 kcal each
        m = re.search(r'(\d+)\s*egg', l)
        if m:
            total += int(m.group(1)) * 70
            continue
        # Whole units like "1 onion" (~120g), "2 tomatoes" (~150g each)
        m = re.search(r'^(\d+)\s+(onion|tomato|carrot|potato|garlic clove|stock cube)', l)
        if m:
            n = int(m.group(1))
            weights = {"onion": 120, "tomato": 150, "carrot": 80, "potato": 200, "garlic clove": 5, "stock cube": 5}
            total += n * kcal_for(weights.get(m.group(2), 50), l)
            continue
    return round(total / max(serves, 1))


# ---------------------------------------------------------------------------
# RECIPES — 10 authentic Zimbabwean dishes
# ---------------------------------------------------------------------------

RECIPES = [
    {
        "slug": "sadza",
        "name": "Sadza",
        "tagline": "The Zimbabwean staple — a thick, white, finely textured cornmeal porridge eaten with almost every meal.",
        "category": "Main course",
        "course_tag": "main",
        "cuisine": "Zimbabwean",
        "prep_min": 5, "cook_min": 25, "serves": 4,
        "intro": (
            "Sadza is what Zimbabweans mean when they say 'food'. Cooked from white maize meal "
            "(or occasionally a finer-ground 'roller meal'), it has a stiff, almost dumpling-like "
            "consistency that you tear off with your fingers, ball lightly, and use to scoop up "
            "relish — meat stew, vegetables, or peanut-butter greens. The mark of a properly "
            "cooked sadza is no lumps and a slight gloss; ask any Zimbabwean grandmother and "
            "they will tell you the trick is to keep stirring through the build-up phase."
        ),
        "ingredients": [
            "1.5 litres water",
            "500g white maize meal (mealie meal)",
            "Salt to taste (optional, traditionally none)",
        ],
        "method": [
            "Bring 1 litre of the water to a rolling boil in a heavy-bottomed pot.",
            "Mix 200g of the maize meal with the remaining 500ml of cold water in a bowl to form a smooth slurry. Whisk out any lumps.",
            "Lower the heat to medium and pour the slurry into the boiling water, stirring constantly with a wooden spoon (a 'mugoti'). Cook this thinner porridge — sadza re-ufu — for 5 minutes, stirring.",
            "Gradually sprinkle in the remaining 300g of maize meal, a handful at a time, stirring vigorously after each addition. The mixture will thicken quickly.",
            "Once all the meal is in, reduce the heat to low. Cover and let it steam for 8-10 minutes.",
            "Uncover, give it one more firm stir to bring everything together into a smooth, stiff dough. Cook another 3 minutes uncovered.",
            "Wet a wooden spoon and divide into portions on plates. Serve immediately, hot, with your relish of choice.",
        ],
        "notes": (
            "Sadza is eaten with the hands. Wash before sitting down, tear off a chunk, ball it "
            "lightly in your right hand to make a thumb-indent, then dip into the relish. It is "
            "traditionally never seasoned with salt — the relish carries all the flavour. "
            "A good sadza shouldn't stick to the spoon."
        ),
        "about": (
            "Cornmeal porridges of similar style are eaten across southern Africa — ugali in "
            "Kenya, pap in South Africa, nshima in Zambia. The Zimbabwean version is "
            "characterised by being noticeably thicker and whiter than its neighbours; "
            "Zimbabweans pride themselves on the stiffness and the absence of lumps. "
            "'Mealie meal' refers to the white maize meal itself — the bag in every kitchen."
        ),
        "wikipedia": "",
    },
    {
        "slug": "muriwo-une-dovi",
        "name": "Muriwo une Dovi",
        "tagline": "Collard greens braised in a velvety peanut-butter sauce — the side dish every Zimbabwean kitchen knows by heart.",
        "category": "Side dish",
        "course_tag": "side",
        "cuisine": "Zimbabwean",
        "prep_min": 10, "cook_min": 20, "serves": 4,
        "intro": (
            "Muriwo une dovi — literally 'greens with peanut butter' — turns ordinary collards "
            "into something rich, creamy and deeply satisfying. The natural pairing of greens "
            "and groundnut is a thread that runs through southern and central African cooking, "
            "but in Zimbabwe it is the default partner for sadza. The peanut butter melts into "
            "the residual cooking water and coats every leaf."
        ),
        "ingredients": [
            "500g collard greens or covo (or kale as a substitute), thick stems removed",
            "1 onion, finely diced",
            "2 tomatoes, diced",
            "3 tbsp natural peanut butter (sugar-free)",
            "2 tbsp cooking oil",
            "Salt to taste",
            "200ml water",
        ],
        "method": [
            "Wash the greens thoroughly, stack the leaves and roll into a tight cigar. Slice across into thin ribbons (chiffonade).",
            "Heat the oil in a heavy pot over medium heat. Sweat the diced onion for 4 minutes until translucent.",
            "Add the diced tomatoes and a pinch of salt. Cook 5 minutes until they break down into a sauce.",
            "Add the sliced greens and stir to coat. Pour in 100ml of the water, cover, and cook 8 minutes until the greens are tender but still bright.",
            "In a small bowl, mix the peanut butter with the remaining 100ml warm water to make a smooth pourable paste.",
            "Pour the peanut paste over the greens. Stir gently to combine — the residual cooking water and the peanut paste will form a glossy sauce that coats every leaf. Cook 3 more minutes.",
            "Taste and adjust salt. Serve hot alongside sadza or as a vegetable side to grilled meat.",
        ],
        "notes": (
            "Use natural peanut butter, not the sweetened supermarket sort — the dish should "
            "be savoury. If using salted peanut butter, hold the added salt. Some cooks add "
            "a small amount of grated ginger or a chopped green chilli with the onion."
        ),
        "about": (
            "Covo, tsunga and rape are the traditional Zimbabwean greens for this dish; covo "
            "in particular is sold in tied bundles at every market. Outside Zimbabwe, collard "
            "greens or even kale work well. The dish was named one of the most "
            "characteristically Zimbabwean preparations by SADC's regional cuisine survey."
        ),
        "wikipedia": "",
    },
    {
        "slug": "nyama-mukute",
        "name": "Nyama (Zimbabwean Beef Stew)",
        "tagline": "Slow-cooked beef in onion and tomato — the everyday meat relish for sadza.",
        "category": "Main course",
        "course_tag": "main",
        "cuisine": "Zimbabwean",
        "prep_min": 15, "cook_min": 90, "serves": 4,
        "intro": (
            "Nyama is simply 'meat' in Shona, but used unqualified it means this dish: cubes "
            "of beef chuck or shin slowly braised down with onion and tomato until the meat "
            "yields to a spoon. There is no exotic ingredient list, no marinade, no pre-roast "
            "— just patience. A pressure cooker shortens this from 90 minutes to 30; "
            "purists insist the slower version tastes better."
        ),
        "ingredients": [
            "1kg beef chuck or shin, cut into 3cm cubes",
            "2 large onions, sliced",
            "3 tomatoes, diced (or one 400g can of chopped tomatoes)",
            "3 cloves garlic, crushed",
            "1 tbsp ginger, grated",
            "2 stock cubes (beef)",
            "3 tbsp cooking oil",
            "Salt and black pepper to taste",
            "500ml water or beef stock",
            "1 bay leaf (optional)",
        ],
        "method": [
            "Pat the beef cubes dry with kitchen paper. Season generously with salt and pepper.",
            "Heat the oil in a heavy-bottomed pot over high heat. Brown the beef in batches — don't crowd the pan or it will steam. Set browned meat aside.",
            "Lower the heat to medium. Add the onions to the same pot, scraping up the fond. Cook 8 minutes until softened and just starting to colour.",
            "Add the garlic and ginger, cook 1 minute until fragrant. Add the tomatoes and a pinch of salt, cook 6 minutes until they collapse into a thick sauce.",
            "Return the beef to the pot. Crumble in the stock cubes, add the bay leaf, and pour in the water/stock. Stir.",
            "Bring to a simmer, then cover and reduce the heat to low. Cook 75-90 minutes, stirring occasionally, until the meat pulls apart with a fork.",
            "If the sauce is too thin at the end, uncover and simmer 10 more minutes to reduce. Taste and adjust salt and pepper.",
            "Serve over or alongside sadza, with muriwo or another vegetable side.",
        ],
        "notes": (
            "Shin or shoulder gives the best texture — both have enough connective tissue to "
            "become silky after a long braise. Avoid lean cuts like topside, which will dry out. "
            "Leftovers improve overnight; the dish is often better on day two."
        ),
        "about": (
            "Beef is the default protein in Zimbabwean home cooking, with a strong cultural "
            "preference for slow-cooked stews over grilled steaks (those are for "
            "braais — barbecues — a separate tradition). The phrase 'nyama yenyama' literally "
            "means 'meat of meat', i.e. 'real meat'."
        ),
        "wikipedia": "",
    },
    {
        "slug": "huku-ne-dovi",
        "name": "Huku ne Dovi (Chicken in Peanut Sauce)",
        "tagline": "Bone-in chicken slow-simmered in a peanut-butter and tomato sauce — the Sunday-lunch classic.",
        "category": "Main course",
        "course_tag": "main",
        "cuisine": "Zimbabwean",
        "prep_min": 15, "cook_min": 60, "serves": 4,
        "intro": (
            "Huku ne dovi is what every Zimbabwean grandmother makes when family comes over. "
            "Chicken pieces — bone in, always — simmered with onion and tomato until the meat "
            "is falling off, then finished with peanut butter for a rich, glossy sauce. The "
            "ideal accompaniment is sadza, with which the sauce is essential."
        ),
        "ingredients": [
            "1.2kg bone-in chicken pieces (legs, thighs, drumsticks)",
            "2 onions, finely diced",
            "3 tomatoes, diced (or 400g canned)",
            "4 tbsp natural peanut butter",
            "2 cloves garlic, crushed",
            "1 tbsp ginger, grated",
            "2 tbsp cooking oil",
            "1 stock cube",
            "500ml water",
            "Salt and pepper",
        ],
        "method": [
            "Season the chicken with salt and pepper. Heat the oil in a heavy pot and brown the pieces in batches, skin-side down first, 6 minutes per side. Set aside.",
            "Reduce heat to medium. Add the onions and cook 8 minutes until soft and golden. Add the garlic and ginger, cook 1 minute.",
            "Add the tomatoes and cook 6 minutes until they break down. Crumble in the stock cube.",
            "Return the chicken to the pot. Pour in 400ml of the water, just enough to come halfway up the pieces. Bring to a simmer, cover, and cook 30 minutes.",
            "In a small bowl, mix the peanut butter with the remaining 100ml of warm water to form a smooth paste. Stir this into the pot.",
            "Continue cooking, uncovered, for 15-20 more minutes. The sauce should thicken to a coating consistency. The chicken should pull easily from the bone.",
            "Taste and adjust seasoning. Serve over sadza with muriwo on the side.",
        ],
        "notes": (
            "'Road runner' chicken — free-range birds that have actually walked — is the "
            "traditional preference and gives a much richer, deeper flavour than supermarket "
            "broilers. A cut-up whole bird works better than just breasts. Some cooks finish "
            "with a squeeze of lemon."
        ),
        "about": (
            "The dish is the close cousin of West African groundnut stew (maafe) and Congolese "
            "moambe — peanut-protein stews appear right across the equatorial belt. "
            "Zimbabwean versions tend to be a touch thicker and less spicy than their "
            "Senegalese counterparts."
        ),
        "wikipedia": "",
    },
    {
        "slug": "kapenta",
        "name": "Kapenta",
        "tagline": "Tiny sun-dried freshwater fish, fried with onion and tomato — Zimbabwe's everyday protein.",
        "category": "Main course",
        "course_tag": "main",
        "cuisine": "Zimbabwean",
        "prep_min": 10, "cook_min": 20, "serves": 4,
        "intro": (
            "Kapenta — Limnothrissa miodon — are a small freshwater fish endemic to Lake "
            "Tanganyika and introduced to Lake Kariba in the 1960s, where they have since "
            "become a backbone of Zimbabwean nutrition. Sun-dried on racks at the lakeside, "
            "they arrive at the market looking like fine silver coins. Quickly fried with "
            "onion and tomato, they make an inexpensive, protein-packed relish."
        ),
        "ingredients": [
            "200g dried kapenta (matemba)",
            "2 onions, finely diced",
            "3 tomatoes, diced",
            "2 cloves garlic, crushed",
            "3 tbsp cooking oil",
            "1 stock cube (optional)",
            "Salt and pepper",
            "1 green chilli, finely sliced (optional)",
        ],
        "method": [
            "Rinse the dried kapenta in cold water and drain. Some cooks soak them for 10 minutes; this gentles the strong dried-fish flavour.",
            "Heat the oil in a wide pan over medium-high heat. Add the kapenta and fry, stirring frequently, for 4 minutes until they crisp up and turn golden at the edges. Remove with a slotted spoon, leaving the oil.",
            "In the same oil, sweat the onions for 6 minutes until soft. Add the garlic and chilli (if using), cook 1 minute.",
            "Add the diced tomatoes and a pinch of salt. Cook 5 minutes until they collapse into a sauce.",
            "Return the kapenta to the pan. Crumble in the stock cube if using. Stir gently — the fish will absorb some of the sauce.",
            "Cook 3-4 more minutes. Taste and season with pepper and more salt if needed.",
            "Serve with sadza and a side of muriwo. The fish-and-tomato combination is also excellent over rice.",
        ],
        "notes": (
            "Kapenta have a strong, distinctive flavour — pre-soaking and the brief initial "
            "frying step both help mellow it for first-time eaters. Look for kapenta with a "
            "uniform silver colour; avoid bags with a strong fishy smell, which indicates "
            "poor drying. The dish keeps well refrigerated for 2 days."
        ),
        "about": (
            "Kariba kapenta are caught at night using lanterns to attract the fish to the "
            "surface, then sun-dried on lakeside racks. The fishery employs thousands of "
            "people on the Zimbabwean and Zambian sides of the lake and the dried fish is "
            "exported widely across the SADC region. They are a complete protein source and "
            "are eaten across the income spectrum in Zimbabwe."
        ),
        "wikipedia": "",
    },
    {
        "slug": "madora-mopane-worms",
        "name": "Madora (Mopane Worms)",
        "tagline": "The famous Zimbabwean delicacy: protein-rich caterpillars fried with onion and tomato.",
        "category": "Main course",
        "course_tag": "main",
        "cuisine": "Zimbabwean",
        "prep_min": 15, "cook_min": 25, "serves": 4,
        "intro": (
            "Madora — the caterpillars of the emperor moth Gonimbrasia belina, which feeds on "
            "the mopane tree — are perhaps Zimbabwe's most-talked-about food. Harvested by "
            "hand, sun-dried, and sold in bags at every market, they are a serious protein "
            "source (60-70% protein dry weight) and a culinary tradition that long predates "
            "colonial cuisine. Cooked in this style they taste meaty, faintly nutty and "
            "totally unlike what visitors anticipate."
        ),
        "ingredients": [
            "200g dried madora (mopane worms)",
            "2 onions, diced",
            "3 tomatoes, diced",
            "2 cloves garlic, crushed",
            "3 tbsp cooking oil",
            "Salt and pepper",
            "1 stock cube",
            "500ml water for rehydrating",
        ],
        "method": [
            "Place the dried madora in a bowl and cover with the warm water. Soak for 15 minutes to rehydrate. They will plump up noticeably.",
            "Drain (keep some of the soaking water aside) and rinse the madora in clean water. Pat dry.",
            "Heat the oil in a heavy pan. Add the madora and fry, stirring, for 5-6 minutes until they begin to crisp.",
            "Add the onions and cook another 6 minutes until softened. Add the garlic, cook 1 minute.",
            "Add the diced tomatoes, salt, and crumble in the stock cube. Cook 5 minutes until the tomatoes break down.",
            "Add 150ml of the reserved soaking water. Cover and simmer 8 minutes, allowing the madora to soften further and absorb the sauce.",
            "Uncover and reduce the sauce to a coating consistency, 3-4 minutes. Adjust salt and pepper.",
            "Serve hot with sadza. Many Zimbabweans also eat them as a snack, dry-roasted with salt — a different preparation entirely.",
        ],
        "notes": (
            "Source madora from a reputable seller — the harvest and drying process matters. "
            "Properly dried worms are dark grey-brown, with no signs of mould. Soaking is "
            "non-negotiable: it both softens the texture and removes any residual gut content."
        ),
        "about": (
            "The mopane worm trade is a substantial part of the rural economy in southern "
            "Zimbabwe and northern South Africa. Harvest happens twice a year, in November-"
            "December and April. Beyond their nutritional value, they are environmentally "
            "remarkable: as a complete protein source they require dramatically less land "
            "and water than equivalent beef production."
        ),
        "wikipedia": "",
    },
    {
        "slug": "mahewu",
        "name": "Mahewu (Mageu)",
        "tagline": "A traditional fermented maize drink — lightly sour, slightly fizzy, deeply refreshing in the heat.",
        "category": "Drink",
        "course_tag": "drink",
        "cuisine": "Zimbabwean",
        "prep_min": 15, "cook_min": 30, "serves": 8,
        "intro": (
            "Mahewu — known as mageu in South Africa — is a non-alcoholic fermented drink "
            "made from leftover sadza, water and a starter (often a few tablespoons of "
            "yesterday's drink, or a small amount of sorghum or wheat flour). After a day "
            "of fermentation it develops a pleasantly sour, faintly fizzy character with "
            "the body of a thin smoothie. It's refreshment, nutrition and probiotic in one."
        ),
        "ingredients": [
            "100g maize meal (or 200g leftover cold sadza)",
            "1.5 litres water",
            "2 tbsp wheat flour, sorghum flour, or millet flour (the 'starter')",
            "2 tbsp sugar (optional, to taste)",
        ],
        "method": [
            "If using leftover sadza, break it up roughly into pieces. If starting from maize meal, mix 100g of the meal with 500ml cold water to make a smooth slurry, then whisk into a pot of 1 litre simmering water and cook 5 minutes to make a thin porridge.",
            "Whichever you started with, let the porridge cool to lukewarm — body temperature, no warmer. This is essential: hot porridge will kill the wild yeasts.",
            "Stir in the wheat or sorghum flour starter. Whisk vigorously to break up any lumps. Sweeten if desired.",
            "Transfer to a clean glass jar or earthenware crock. Cover loosely with cloth (to keep flies out but let air in).",
            "Leave in a warm place — a sunny windowsill or a warm kitchen — for 18-36 hours, depending on temperature. Taste at the 18-hour mark: it should be pleasantly tart, like buttermilk, with a slight effervescence.",
            "Once ready, strain through a fine sieve into bottles. Refrigerate; serve cold. It will keep 3-4 days, growing more sour over time.",
        ],
        "notes": (
            "The first batch from scratch is the hardest — wild fermentation can be slow. "
            "Once you have a working batch, save 2 tbsp of the previous batch as the starter "
            "for the next one (rather than the flour). This shortens the fermentation to "
            "12-18 hours and gives a more consistent result."
        ),
        "about": (
            "Mahewu is an ancient drink across southern Africa, traditionally made as a way "
            "to preserve and add value to surplus cornmeal. It is now also sold commercially "
            "across the region in cardboard cartons under brand names like Sungold and "
            "Maheu, in flavoured varieties (banana, strawberry, plain). The homemade version "
            "is leagues better — and is genuinely a probiotic drink in the modern fermented-"
            "foods sense."
        ),
        "wikipedia": "",
    },
    {
        "slug": "maputi-roasted-corn",
        "name": "Maputi (Roasted Maize Snack)",
        "tagline": "Dried maize kernels dry-roasted in a pan until they pop and crisp — the Zimbabwean popcorn.",
        "category": "Snack",
        "course_tag": "snack",
        "cuisine": "Zimbabwean",
        "prep_min": 5, "cook_min": 15, "serves": 4,
        "intro": (
            "Maputi are dried maize kernels that have been popped or roasted dry in a pan "
            "or over an open fire. Unlike the soft, fully-puffed popcorn most non-Zimbabweans "
            "know, classic maputi keep a satisfying tooth — chewy in the centre, crisp at "
            "the edges. They are bagged at every roadside in Zimbabwe and eaten on long "
            "journeys, at football matches and as bar snacks."
        ),
        "ingredients": [
            "300g dried maize kernels (mealie kernels, not popcorn variety)",
            "Coarse salt to taste",
            "A pinch of sugar (optional, traditional in some recipes)",
        ],
        "method": [
            "Heat a heavy, dry cast-iron pan over medium heat until very hot. No oil.",
            "Add a single layer of maize kernels — don't crowd. Cover loosely with a lid (some will pop, others won't).",
            "Shake the pan continuously to keep the kernels moving. After 8-10 minutes they will start to puff, brown and crackle. Some will pop, some will simply turn golden and chewy. Both are 'maputi'.",
            "When the popping slows and the kernels are nutty-brown, tip onto a tray to cool.",
            "While still warm, toss with coarse salt to taste. Some cooks add a tiny pinch of sugar for the salt-sweet contrast.",
            "Store in an airtight tin. They stay crisp for a week.",
        ],
        "notes": (
            "Standard popcorn maize will give you fluffy popcorn, not classical maputi — for "
            "the authentic chewier version use ordinary dried mealie kernels. The chew is the "
            "point. If you only have popcorn corn, hold back on heat slightly so they brown "
            "rather than fully puff."
        ),
        "about": (
            "Maputi is a snack of the working day, sold by the cup at urban traffic lights, "
            "bus stations and rural market gates. The kernels are sometimes mixed with dried "
            "groundnuts or coated with caramel ('maputi ne shuga') for a treat version. "
            "Closely related to West African 'aadun' and Mexican esquites."
        ),
        "wikipedia": "",
    },
    {
        "slug": "samp-and-beans",
        "name": "Samp and Beans (Isitshwala lendumba)",
        "tagline": "Coarsely-cracked maize cooked with sugar beans — a slow-cooked, deeply nourishing one-pot.",
        "category": "Main course",
        "course_tag": "main",
        "cuisine": "Zimbabwean",
        "prep_min": 15, "cook_min": 120, "serves": 4,
        "intro": (
            "Samp — coarse, broken white maize — and sugar beans, cooked together until both "
            "soften into a thick, savoury one-pot. This is rural, working-people food: "
            "inexpensive, filling, and providing complete protein when the two grains "
            "are cooked together. It needs an overnight soak and a long simmer, but the "
            "active time is minimal."
        ),
        "ingredients": [
            "300g samp (coarsely cracked maize)",
            "200g dried sugar beans (or red speckled beans)",
            "1 large onion, diced",
            "3 tbsp cooking oil",
            "2 stock cubes",
            "Salt and pepper",
            "1.5 litres water",
        ],
        "method": [
            "The night before: soak the samp and beans separately in cold water. Both need at least 8 hours.",
            "Drain and rinse both. Combine in a heavy pot. Add the 1.5 litres of fresh water, bring to a boil, then reduce to a low simmer.",
            "Cook 75-90 minutes, partly covered, until the samp is plump and the beans are softening. Top up with hot water if it dries out — samp and beans absorb a lot.",
            "Meanwhile, in a separate pan, fry the diced onion in the oil over medium heat until deep golden, 10 minutes. Set aside.",
            "When samp and beans are both fork-tender, stir in the fried onion (and the oil from the pan), crumble in the stock cubes, and season with salt and pepper.",
            "Cook another 15-20 minutes uncovered to let everything come together into a thick, creamy texture.",
            "Taste and adjust seasoning. Serve hot, traditionally alongside a fresh vegetable side (muriwo) or a piece of grilled chicken or beef.",
        ],
        "notes": (
            "If you forget to soak, you can shortcut by parboiling the samp and beans together "
            "for 10 minutes, then resting in the cooking water for an hour. Same effect, "
            "less elegant. A pressure cooker reduces the total cook time to ~45 minutes."
        ),
        "about": (
            "Samp and beans is a staple across southern Africa — known as umngqusho in "
            "isiXhosa (Nelson Mandela's favourite dish, reportedly), isitshwala lendumba in "
            "Ndebele Zimbabwe. The grain-and-pulse combination is nutritionally important: "
            "together they form a complete protein, while neither alone does."
        ),
        "wikipedia": "",
    },
    {
        "slug": "chimodho-vetkoek",
        "name": "Chimodho (Steamed Cornbread)",
        "tagline": "A simple steamed maize-meal bread — slightly sweet, dense, the perfect partner for tea.",
        "category": "Bread",
        "course_tag": "bread",
        "cuisine": "Zimbabwean",
        "prep_min": 10, "cook_min": 60, "serves": 6,
        "intro": (
            "Chimodho is a steamed cornbread — closer to a pudding-cake than a Western "
            "yeasted loaf — eaten with tea, with butter, or as a side to a meat stew. It's "
            "made from the same white maize meal as sadza, but with sugar, a little flour, "
            "and steaming rather than boiling. The result is dense, moist and gently sweet."
        ),
        "ingredients": [
            "400g maize meal (mealie meal)",
            "100g bread flour",
            "100g sugar",
            "1 tsp baking powder",
            "1 tsp salt",
            "350ml water (warm)",
            "2 tbsp butter, melted",
        ],
        "method": [
            "Mix the maize meal, flour, sugar, baking powder and salt in a large bowl.",
            "Add the melted butter and warm water gradually, stirring with a wooden spoon, until you have a thick batter — like a stiff cake batter, pourable but not runny.",
            "Grease a heatproof 1.5-litre pudding basin or bowl thoroughly with butter or oil. Pour in the batter; it should reach about three-quarters full.",
            "Cover the basin tightly with foil and tie down with string, or use a plate as a lid weighted down. The seal matters — no steam should escape into the batter.",
            "Set the basin into a large pot. Add boiling water to come halfway up the side of the basin. Cover the pot and steam for 60 minutes on medium-low heat. Top up with boiling water as needed.",
            "Test with a skewer: it should come out clean. If still wet, steam another 15 minutes.",
            "Carefully lift the basin out (it will be hot). Let cool 10 minutes before turning out. Slice and serve warm with butter or jam.",
        ],
        "notes": (
            "Chimodho keeps well for 2 days at room temperature. Slice and toast it lightly to "
            "revive day-two pieces. The traditional Zimbabwean preparation is fully steamed; "
            "some modern recipes oven-bake it, which works but loses the characteristic "
            "moisture."
        ),
        "about": (
            "Chimodho is one of several Zimbabwean breads made primarily from maize rather "
            "than wheat — reflecting both the country's maize-centric agriculture and the "
            "expense of wheat flour historically. It is eaten at every level of Zimbabwean "
            "society and is a common Sunday-tea offering."
        ),
        "wikipedia": "",
    },
]

# ---------------------------------------------------------------------------
# CSS — recipe-focused, beautiful chrome
# ---------------------------------------------------------------------------

CSS = """
body { background: #fff !important; }
.ck-shell { max-width: 1100px; margin: 0 auto; padding: 0 20px; }

/* Hub banner */
.ck-hub-img { max-width: 1100px; margin: 14px auto 0; padding: 0 20px; }
.ck-hub-img-inner { aspect-ratio: 21/9; border-radius: 12px; overflow: hidden;
  border: 1px solid var(--rule); background: #f0ece4; }
.ck-hub-img-inner img { width: 100%; height: 100%; object-fit: cover; display: block; }
@media (max-width: 640px) { .ck-hub-img-inner { aspect-ratio: 16/9; } }

/* Header */
.ck-header { padding: 28px 20px 6px; max-width: 1100px; margin: 0 auto; }
.ck-eyebrow { font-family: 'Inter', system-ui, sans-serif; font-size: 0.72em;
  letter-spacing: 0.18em; text-transform: uppercase; color: var(--accent);
  font-weight: 700; margin: 0 0 10px; }
.ck-eyebrow a { color: inherit; text-decoration: none; }
.ck-title { font-family: 'Playfair Display', Georgia, serif; font-weight: 700;
  font-size: clamp(2em, 5vw, 3.4em); line-height: 1.05; color: var(--ink);
  margin: 0 0 14px; letter-spacing: -0.022em; max-width: 16ch; }
.ck-stand { font-family: 'Inter', system-ui, sans-serif; font-size: clamp(1.05em, 1.6vw, 1.25em);
  line-height: 1.55; color: var(--text-mid); margin: 0; max-width: 52ch; }
.ck-rule { width: 56px; height: 3px; background: var(--accent); border: 0; margin: 22px 0 0; }

/* Hero image on recipe pages */
.ck-hero { max-width: 1080px; margin: 22px auto 0; padding: 0 20px; }
.ck-hero-inner { aspect-ratio: 16/9; overflow: hidden; border-radius: 14px;
  border: 1px solid var(--rule); background: #f0ece4; }
.ck-hero-inner img { width: 100%; height: 100%; object-fit: cover; display: block; }

/* Recipe stat strip */
.ck-stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 12px; max-width: 1080px; margin: 24px auto 0; padding: 0 20px;
  font-family: 'Inter', system-ui, sans-serif; }
.ck-stat { padding: 16px 18px; background: #fbfaf6; border: 1px solid var(--rule);
  border-radius: 10px; }
.ck-stat-label { font-size: 0.66em; letter-spacing: 0.16em; text-transform: uppercase;
  color: var(--text-light); margin: 0 0 4px; font-weight: 600; }
.ck-stat-value { font-family: 'Playfair Display', Georgia, serif; font-size: 1.3em;
  line-height: 1.1; color: var(--ink); margin: 0; font-weight: 700; }

/* Recipe body: side-by-side on desktop, stacked on mobile */
.ck-body { max-width: 1080px; margin: 36px auto 0; padding: 0 20px;
  display: grid; grid-template-columns: 1fr 2fr; gap: 48px;
  font-family: 'Inter', system-ui, sans-serif; }
@media (max-width: 800px) {
  .ck-body { grid-template-columns: 1fr; gap: 24px; }
}
.ck-section-h { font-family: 'Playfair Display', Georgia, serif; font-weight: 700;
  font-size: 1.3em; line-height: 1.1; color: var(--ink); margin: 0 0 14px;
  letter-spacing: -0.01em; padding-bottom: 8px; border-bottom: 2px solid var(--accent);
  display: inline-block; }
.ck-ingredients ul { list-style: none; padding: 0; margin: 0;
  font-size: 1em; line-height: 1.6; }
.ck-ingredients li { padding: 10px 0; border-bottom: 1px dotted var(--rule); color: var(--text); }
.ck-ingredients li:last-child { border-bottom: 0; }
.ck-method ol { list-style: none; padding: 0; margin: 0; counter-reset: step; }
.ck-method li { display: grid; grid-template-columns: 36px 1fr; gap: 14px; padding: 14px 0;
  border-bottom: 1px solid var(--rule); counter-increment: step;
  font-size: 1.02em; line-height: 1.6; color: var(--text); }
.ck-method li:last-child { border-bottom: 0; }
.ck-method li::before { content: counter(step); font-family: 'Playfair Display', Georgia, serif;
  font-weight: 700; font-size: 1.4em; line-height: 1; color: var(--accent);
  background: #fbfaf6; border: 1px solid var(--rule); border-radius: 50%;
  width: 36px; height: 36px; display: flex; align-items: center; justify-content: center; }

/* Lead / About */
.ck-lead { max-width: 720px; margin: 30px auto 0; padding: 0 20px;
  font-family: 'Inter', system-ui, sans-serif; font-size: 1.075em; line-height: 1.7;
  color: var(--text); }
.ck-lead p::first-letter {
  font-family: 'Playfair Display', Georgia, serif; font-weight: 700;
  font-size: 3.2em; float: left; line-height: 0.9; margin: 4px 8px 0 0;
  color: var(--ink);
}

.ck-section { max-width: 720px; margin: 32px auto 0; padding: 0 20px;
  font-family: 'Inter', system-ui, sans-serif; }
.ck-section h2 { font-family: 'Playfair Display', Georgia, serif; font-weight: 700;
  font-size: 1.5em; color: var(--ink); margin: 0 0 12px; letter-spacing: -0.015em; }
.ck-section p { font-size: 1.05em; line-height: 1.7; color: var(--text); margin: 0 0 12px; }
.ck-section a { color: var(--accent); text-decoration: underline; }

.ck-notes-callout { max-width: 720px; margin: 24px auto 0; padding: 18px 22px;
  background: linear-gradient(135deg, #fbfaf6 0%, #f3eedf 100%);
  border: 1px solid var(--rule); border-left: 4px solid var(--accent);
  border-radius: 10px; font-family: 'Inter', system-ui, sans-serif; }
.ck-notes-callout-label { font-size: 0.7em; letter-spacing: 0.18em; text-transform: uppercase;
  color: var(--accent); font-weight: 700; margin: 0 0 6px; }
.ck-notes-callout p { font-size: 1em; line-height: 1.65; color: var(--text);
  margin: 0; }

.ck-sources { max-width: 720px; margin: 36px auto 0; padding: 18px 20px;
  border-top: 2px solid var(--ink); font-family: 'Inter', system-ui, sans-serif; }
.ck-sources h2 { font-size: 0.74em; letter-spacing: 0.18em; text-transform: uppercase;
  margin: 0 0 12px; color: var(--text-light); font-weight: 700;
  font-family: 'Inter', system-ui, sans-serif; }
.ck-sources ul { font-size: 0.92em; margin: 0 0 8px; padding-left: 20px; line-height: 1.55;
  color: var(--text); }
.ck-sources a { color: var(--ink); text-decoration: underline; }
.ck-sources-note { font-size: 0.82em; color: var(--text-light); margin: 0; line-height: 1.55; }

.ck-back { text-align: center; margin: 32px 0 56px;
  font-family: 'Inter', system-ui, sans-serif; }
.ck-back a { font-size: 0.92em; color: var(--ink); border-bottom: 1px solid var(--accent);
  text-decoration: none; padding-bottom: 2px; }

/* Recipe grid (hub) */
.ck-grid { display: grid; gap: 18px; padding: 0 20px 32px;
  max-width: 1100px; margin: 26px auto 0;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); }
.ck-card { display: flex; flex-direction: column; background: #fff;
  border: 1px solid var(--rule); border-radius: 12px; overflow: hidden;
  color: var(--text); text-decoration: none;
  transition: border-color 0.15s ease, box-shadow 0.15s ease, transform 0.15s ease; }
.ck-card:hover { border-color: var(--accent); text-decoration: none;
  box-shadow: 0 6px 24px rgba(0,0,0,0.06); transform: translateY(-2px); }
.ck-card-img { aspect-ratio: 4/3; background: #f0ece4; }
.ck-card-img img { width: 100%; height: 100%; object-fit: cover; display: block; }
.ck-card-body { padding: 18px 20px 22px; }
.ck-card-tag { font-family: 'Inter', system-ui, sans-serif; font-size: 0.7em;
  letter-spacing: 0.12em; text-transform: uppercase; color: var(--accent);
  margin: 0 0 6px; font-weight: 700; }
.ck-card-name { font-family: 'Playfair Display', Georgia, serif; font-weight: 700;
  font-size: 1.2em; line-height: 1.2; color: var(--ink); margin: 0 0 6px; letter-spacing: -0.01em; }
.ck-card-tagline { font-family: 'Inter', system-ui, sans-serif; font-size: 0.92em;
  line-height: 1.5; color: var(--text-mid); margin: 0 0 12px; }
.ck-card-meta { font-family: 'Inter', system-ui, sans-serif; font-size: 0.78em;
  color: var(--text-light); margin: 0; padding-top: 10px; border-top: 1px solid var(--rule);
  display: flex; gap: 14px; flex-wrap: wrap; }
.ck-card-meta strong { color: var(--ink); font-weight: 600; }

/* Filter chips */
.ck-chips { display: flex; flex-wrap: wrap; gap: 6px; align-items: center;
  max-width: 1100px; margin: 14px auto 0; padding: 0 20px;
  font-family: 'Inter', system-ui, sans-serif; }
.ck-chip { font-size: 0.82em; padding: 7px 14px; background: #fbfaf6;
  border: 1px solid var(--rule); color: var(--ink); border-radius: 16px;
  cursor: pointer; user-select: none; font-family: inherit; font-weight: 500; }
.ck-chip:hover { border-color: var(--ink); }
.ck-chip[aria-pressed="true"] { background: var(--accent); border-color: var(--accent); color: #fff; }
.ck-card[hidden] { display: none; }

/* Recent news module */
.ck-news { max-width: 1100px; margin: 36px auto; padding: 0 20px;
  font-family: 'Inter', system-ui, sans-serif; }
.ck-news h2 { font-family: 'Playfair Display', Georgia, serif; font-weight: 700;
  font-size: 1.5em; color: var(--ink); margin: 0 0 16px; letter-spacing: -0.015em; }
.ck-news-grid { display: grid; gap: 12px;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); }
.ck-news-card { display: block; padding: 16px 18px; background: #fff;
  border: 1px solid var(--rule); border-radius: 8px; text-decoration: none;
  color: var(--text); transition: border-color 0.15s, transform 0.15s; }
.ck-news-card:hover { border-color: var(--accent); transform: translateY(-1px);
  text-decoration: none; color: var(--text); }
.ck-news-date { font-size: 0.72em; letter-spacing: 0.08em; text-transform: uppercase;
  color: var(--accent); font-weight: 700; margin: 0 0 6px; }
.ck-news-title { font-family: 'Playfair Display', Georgia, serif; font-weight: 700;
  font-size: 1em; line-height: 1.3; color: var(--ink); margin: 0; }
"""

# ---------------------------------------------------------------------------
# SHARED CHROME — topbar + drawer + footer (matches other microsites)
# ---------------------------------------------------------------------------

TOPBAR = """<div class="topbar" id="topbar" aria-label="Sticky navigation">
  <button class="topbar-menu" type="button" data-open-drawer aria-label="Open menu" aria-controls="navDrawer" aria-expanded="false">
    <span></span><span></span><span></span>
  </button>
  <a href="/" class="topbar-brand"><em>The Mutapa Times</em></a>
  <a href="/subscribe" class="topbar-cta">Subscribe</a>
</div>"""

DRAWER = """<div class="nav-drawer-backdrop" data-close-drawer aria-hidden="true"></div>
<aside class="nav-drawer" id="navDrawer" aria-hidden="true" aria-label="Site navigation">
  <button class="nav-drawer-close" type="button" data-close-drawer aria-label="Close menu">
    <svg viewBox="0 0 24 24" width="24" height="24" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="round"><line x1="6" y1="6" x2="18" y2="18"/><line x1="18" y1="6" x2="6" y2="18"/></svg>
  </button>
  <form class="nav-drawer-search" action="/articles" method="get" role="search">
    <input type="search" name="q" placeholder="Search The Mutapa Times" aria-label="Search The Mutapa Times">
  </form>
  <nav class="nav-drawer-main" aria-label="Sections">
    <a href="/">News</a><a href="/economy">Economy</a><a href="/fx/">FX</a>
    <a href="/markets">Markets</a><a href="/property">Property</a>
    <a href="/jobs">Jobs</a><a href="/articles">Articles</a>
  </nav>
  <span class="nav-drawer-section">Directories</span>
  <nav class="nav-drawer-info" aria-label="Directories">
    <a href="/flights/">Flights</a><a href="/cooking/">Cooking</a>
    <a href="/schools/">Schools</a><a href="/zse/">ZSE companies</a>
    <a href="/mining/">Mining</a><a href="/moving-to-zimbabwe/">Moving to Zimbabwe</a>
  </nav>
  <span class="nav-drawer-section">Cities</span>
  <nav class="nav-drawer-cities" aria-label="Cities">
    <a href="/harare-news">Harare</a><a href="/bulawayo-news">Bulawayo</a>
    <a href="/mutare-news">Mutare</a><a href="/gweru-news">Gweru</a>
    <a href="/masvingo-news">Masvingo</a><a href="/victoria-falls-news">Victoria Falls</a>
  </nav>
  <span class="nav-drawer-section">Information</span>
  <nav class="nav-drawer-info" aria-label="Information">
    <a href="/about">About</a><a href="/advertising">Advertising</a>
    <a href="/terms">Terms</a><a href="/privacy">Privacy</a>
  </nav>
</aside>"""

FOOTER = """<footer class="atlantic-foot">
  <div class="atlantic-foot-inner">
    <div class="atlantic-foot-fine">
      <a href="/">News</a><span class="sep">·</span>
      <a href="/flights/">Flights</a><span class="sep">·</span>
      <a href="/cooking/">Cooking</a><span class="sep">·</span>
      <a href="/fx/">FX rates</a><span class="sep">·</span>
      <a href="/schools/">Schools</a><span class="sep">·</span>
      <a href="/zse/">ZSE companies</a><span class="sep">·</span>
      <a href="/mining/">Mining</a><span class="sep">·</span>
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
</script>
<script defer src="/js/nav.js"></script>"""

# ---------------------------------------------------------------------------
# RENDERERS
# ---------------------------------------------------------------------------

def hero_for(slug):
    for ext in (".jpg", ".jpeg", ".png", ".webp"):
        p = ROOT / "img" / "cooking" / f"{slug}{ext}"
        if p.exists():
            return f"/img/cooking/{p.name}"
    return None

def hub_banner_html():
    for ext in (".jpg", ".jpeg", ".png", ".webp"):
        p = ROOT / "img" / "cooking" / f"_hero{ext}"
        if p.exists():
            return f'<figure class="ck-hub-img"><div class="ck-hub-img-inner"><img src="/img/cooking/_hero{ext}" alt="" loading="eager"></div></figure>'
    return ""

def head_html(title, canonical, desc, schemas):
    schemas_html = "\n".join(f'<script type="application/ld+json">{s}</script>' for s in schemas)
    return f"""<head>
    <meta charset="utf-8">
    <title>{title}</title>
    <link rel="canonical" href="{canonical}">
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
    <link rel="icon" type="image/png" sizes="32x32" href="../img/favicon-32x32.png">
    <link rel="icon" type="image/png" sizes="16x16" href="../img/favicon-16x16.png">
    <meta name="theme-color" content="#1a1a1a">
    <meta name="author" content="The Mutapa Times">
    <meta name="twitter:site" content="@mutapatimes">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="description" content="{html.escape(desc)}">
    <meta name="robots" content="index, follow">
    <meta property="og:type" content="article">
    <meta property="og:title" content="{html.escape(title)}">
    <meta property="og:description" content="{html.escape(desc)}">
    <meta property="og:url" content="{canonical}">
    <meta property="og:site_name" content="The Mutapa Times">
{schemas_html}
<style>{CSS}</style>
</head>"""


def render_recipe(r):
    slug = r["slug"]
    canonical = f"https://www.mutapatimes.com/cooking/{slug}/"
    total_min = r["prep_min"] + r["cook_min"]
    cal = estimate_calories(r["ingredients"], r["serves"])

    # Recipe schema (Google rich snippet eligible)
    instructions_schema = [
        {"@type": "HowToStep", "position": i+1, "text": stripped(step)}
        for i, step in enumerate(r["method"])
    ]
    recipe_schema = {
        "@context": "https://schema.org",
        "@type": "Recipe",
        "name": r["name"],
        "image": [f"https://www.mutapatimes.com{hero_for(slug)}"] if hero_for(slug) else [],
        "description": r["tagline"],
        "author": {"@type": "Organization", "name": "The Mutapa Times"},
        "datePublished": TODAY,
        "prepTime": f"PT{r['prep_min']}M",
        "cookTime": f"PT{r['cook_min']}M",
        "totalTime": f"PT{total_min}M",
        "recipeCategory": r["category"],
        "recipeCuisine": r["cuisine"],
        "recipeYield": f"{r['serves']} servings",
        "recipeIngredient": r["ingredients"],
        "recipeInstructions": instructions_schema,
        "nutrition": {
            "@type": "NutritionInformation",
            "calories": f"{cal} kcal",
            "servingSize": "1 serving",
        },
    }
    breadcrumb_schema = {
        "@context": "https://schema.org", "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://www.mutapatimes.com/"},
            {"@type": "ListItem", "position": 2, "name": "Cooking", "item": "https://www.mutapatimes.com/cooking/"},
            {"@type": "ListItem", "position": 3, "name": r["name"], "item": canonical},
        ],
    }

    ingredients_html = "\n".join(f"      <li>{html.escape(i)}</li>" for i in r["ingredients"])
    method_html = "\n".join(f"      <li>{html.escape(s)}</li>" for s in r["method"])

    hero_path = hero_for(slug)
    hero_html = f'<figure class="ck-hero"><div class="ck-hero-inner"><img src="{hero_path}" alt="{html.escape(r["name"])}" loading="eager"></div></figure>' if hero_path else ""

    title = f"{r['name']} — Zimbabwean recipe | The Mutapa Times"
    desc = f"{r['tagline']} Prep {r['prep_min']} min · Cook {r['cook_min']} min · Serves {r['serves']} · ~{cal} kcal/serving."

    wiki_link = ""
    if r.get("wikipedia"):
        wiki_link = f'      <li><a href="{r["wikipedia"]}" rel="noopener" target="_blank">Wikipedia &mdash; background on {html.escape(r["name"])}</a></li>'

    return f"""<!doctype html>
<html class="no-js" lang="en">
{head_html(title, canonical, desc, [json.dumps(recipe_schema, ensure_ascii=False), json.dumps(breadcrumb_schema, ensure_ascii=False)])}
<body>
{TOPBAR}
{DRAWER}
<main>
  <header class="ck-header">
    <p class="ck-eyebrow"><a href="/cooking/">Cooking</a> &middot; Zimbabwean recipes</p>
    <h1 class="ck-title">{html.escape(r["name"])}</h1>
    <p class="ck-stand">{html.escape(r["tagline"])}</p>
    <hr class="ck-rule">
  </header>

  {hero_html}

  <div class="ck-stats" role="list">
    <div class="ck-stat"><p class="ck-stat-label">Prep</p><p class="ck-stat-value">{r['prep_min']} min</p></div>
    <div class="ck-stat"><p class="ck-stat-label">Cook</p><p class="ck-stat-value">{r['cook_min']} min</p></div>
    <div class="ck-stat"><p class="ck-stat-label">Serves</p><p class="ck-stat-value">{r['serves']}</p></div>
    <div class="ck-stat"><p class="ck-stat-label">Approx. kcal</p><p class="ck-stat-value">~{cal}</p></div>
  </div>

  <div class="ck-lead">
    <p>{html.escape(r["intro"])}</p>
  </div>

  <div class="ck-body">
    <div class="ck-ingredients">
      <h2 class="ck-section-h">Ingredients</h2>
      <ul>
{ingredients_html}
      </ul>
    </div>
    <div class="ck-method">
      <h2 class="ck-section-h">Method</h2>
      <ol>
{method_html}
      </ol>
    </div>
  </div>

  <aside class="ck-notes-callout">
    <p class="ck-notes-callout-label">Notes</p>
    <p>{r["notes"]}</p>
  </aside>

  <section class="ck-section">
    <h2>About this dish</h2>
    <p>{r["about"]}</p>
  </section>

  <section class="ck-sources" aria-label="Sources">
    <h2>Sources &amp; further reading</h2>
    <ul>
{wiki_link if wiki_link else ''}
      <li>Calorie estimate: per-ingredient kcal table (USDA-derived), divided by serves. Approximate &mdash; varies with portion size and exact ingredients used.</li>
      <li>Cultural context and method are editorial, based on widely-documented Zimbabwean home cooking. Last reviewed {TODAY}.</li>
    </ul>
    <p class="ck-sources-note">Have a family variation that we missed? Email
      <a href="mailto:news@mutapatimes.com?subject=Cooking%20guide%3A%20{html.escape(r['name'])}">news@mutapatimes.com</a>
      &mdash; we credit contributors.</p>
  </section>

  <p class="ck-back"><a href="/cooking/">&larr; Back to all recipes</a></p>
</main>
{FOOTER}
</body>
</html>
"""


def stripped(s):
    """Strip HTML for JSON-LD text content."""
    return re.sub(r"<[^>]+>", "", s).replace("&amp;", "&").replace("&mdash;", "—")


def render_hub():
    canonical = "https://www.mutapatimes.com/cooking/"
    title = "Zimbabwean recipes — The Mutapa Times Cooking Guide"
    desc = "10 authentic Zimbabwean recipes with full method, calorie estimates and cultural context. Sadza, muriwo une dovi, kapenta, madora and more."

    page_schema = {
        "@context": "https://schema.org", "@type": "CollectionPage",
        "headline": title, "description": desc, "url": canonical, "inLanguage": "en",
    }
    breadcrumb_schema = {
        "@context": "https://schema.org", "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://www.mutapatimes.com/"},
            {"@type": "ListItem", "position": 2, "name": "Cooking", "item": canonical},
        ],
    }
    item_list_schema = {
        "@context": "https://schema.org", "@type": "ItemList",
        "name": "Zimbabwean recipes",
        "itemListElement": [
            {"@type": "ListItem", "position": i+1,
             "url": f"https://www.mutapatimes.com/cooking/{r['slug']}/",
             "name": r["name"]}
            for i, r in enumerate(RECIPES)
        ],
    }

    cards = []
    for r in RECIPES:
        total = r["prep_min"] + r["cook_min"]
        cal = estimate_calories(r["ingredients"], r["serves"])
        img = hero_for(r["slug"])
        img_html = f'<div class="ck-card-img"><img src="{img}" alt="{html.escape(r["name"])}" loading="lazy"></div>' if img else '<div class="ck-card-img"></div>'
        cards.append(f'''    <a class="ck-card" href="/cooking/{r["slug"]}/" data-tag="{r["course_tag"]}">
      {img_html}
      <div class="ck-card-body">
        <p class="ck-card-tag">{html.escape(r["category"])}</p>
        <h3 class="ck-card-name">{html.escape(r["name"])}</h3>
        <p class="ck-card-tagline">{html.escape(r["tagline"])}</p>
        <p class="ck-card-meta"><strong>{total} min</strong> &middot; serves {r["serves"]} &middot; ~{cal} kcal</p>
      </div>
    </a>''')
    cards_html = "\n".join(cards)

    # Categories for filter chips
    tags = sorted({r["course_tag"] for r in RECIPES})
    tag_labels = {"main": "Mains", "side": "Sides", "drink": "Drinks", "snack": "Snacks", "bread": "Breads"}
    chips_html = "".join(
        f'    <button class="ck-chip" data-filter="{t}" aria-pressed="false">{tag_labels.get(t, t.title())}</button>\n'
        for t in tags
    )

    recent_news = latest_news(6)
    news_html = "\n".join(
        f'      <a class="ck-news-card" href="/articles/{n["file"]}.html"><p class="ck-news-date">{n["date"]}</p><h3 class="ck-news-title">{html.escape(n["title"])}</h3></a>'
        for n in recent_news
    ) if recent_news else ""

    return f"""<!doctype html>
<html class="no-js" lang="en">
{head_html(title, canonical, desc, [json.dumps(page_schema, ensure_ascii=False), json.dumps(breadcrumb_schema, ensure_ascii=False), json.dumps(item_list_schema, ensure_ascii=False)])}
<body>
{TOPBAR}
{DRAWER}
<main>
  <header class="ck-header">
    <p class="ck-eyebrow">Mutapa Times &middot; Cooking</p>
    <h1 class="ck-title">Zimbabwean recipes</h1>
    <p class="ck-stand">Authentic home cooking, written for the diaspora kitchen. Full method, calorie estimates, the cultural context, and the small details a Zimbabwean grandmother would know.</p>
    <hr class="ck-rule">
  </header>

  {hub_banner_html()}

  <div class="ck-chips" role="group" aria-label="Filter by course">
    <button class="ck-chip is-all" data-filter="all" aria-pressed="true">All</button>
{chips_html}  </div>

  <div class="ck-grid" id="ckGrid">
{cards_html}
  </div>

  <section class="ck-news" aria-label="Latest from The Mutapa Times">
    <h2>Latest from The Mutapa Times</h2>
    <div class="ck-news-grid">
{news_html}
    </div>
  </section>

  <section class="ck-sources" aria-label="About this guide">
    <h2>About this guide</h2>
    <ul>
      <li>Recipes are editorial, based on widely-documented Zimbabwean home cooking. Where dishes have Wikipedia articles, we cross-link them for background.</li>
      <li>Calorie estimates are approximate, computed per-ingredient and divided by the declared serves. They are not nutritional advice.</li>
      <li>Have a family recipe to share? Email <a href="mailto:news@mutapatimes.com?subject=Cooking%20guide%20submission">news@mutapatimes.com</a> — we credit contributors and we love variations.</li>
    </ul>
  </section>
</main>
{FOOTER}
<script>
(function() {{
  var chips = Array.from(document.querySelectorAll('.ck-chip'));
  var cards = Array.from(document.querySelectorAll('.ck-card'));
  chips.forEach(function(chip) {{
    chip.addEventListener('click', function() {{
      var f = chip.dataset.filter;
      chips.forEach(function(c) {{ c.setAttribute('aria-pressed', c === chip ? 'true' : 'false'); }});
      cards.forEach(function(card) {{
        if (f === 'all' || card.dataset.tag === f) card.hidden = false;
        else card.hidden = true;
      }});
    }});
  }});
}})();
</script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

# Make sure /img/cooking/ exists
(ROOT / "img" / "cooking").mkdir(parents=True, exist_ok=True)

for r in RECIPES:
    d = OUT / r["slug"]
    d.mkdir(exist_ok=True)
    (d / "index.html").write_text(render_recipe(r))
    print(f"wrote /cooking/{r['slug']}/index.html")

(OUT / "index.html").write_text(render_hub())
print(f"wrote /cooking/index.html (hub)")
print(f"\nTotal: {len(RECIPES)} recipe pages + hub = {len(RECIPES)+1} pages")
