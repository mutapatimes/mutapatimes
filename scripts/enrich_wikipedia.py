#!/usr/bin/env python3
"""Fetch Wikipedia infobox + summary for ATS schools and save to data/ats-schools-wp.json.

Only entries in the verified mapping below are fetched. We do not auto-match by
fuzzy name; we want to be sure the Wikipedia article is actually about the same
school (ATS sometimes has multiple schools with similar names — e.g. Petra
College vs. Petra High School)."""
import json, re, urllib.request, urllib.parse, time
from pathlib import Path

ROOT = Path("/Users/valentineeluwasi/Documents/GitHub/mutapatimes")

# Verified ATS-name -> Wikipedia-title mapping. Confirmed by reading the
# Wikipedia article title-line and the published location of the ATS school.
MAPPING = {
    "Arundel School":                       "Arundel_School",
    "Bernard Mizeki College":               "Bernard_Mizeki_College",
    "Bryden Country School":                "Bryden_Country_School",
    "Chisipite Junior School":              "Chisipite_Junior_School",
    "Chisipite Senior School":              "Chisipite_Senior_School",
    "Christian Brothers' College":          "Christian_Brothers_College,_Bulawayo",
    "Dominican Convent High School (Bulawayo)":     "Dominican_Convent_High_School,_Bulawayo",
    "Dominican Convent Primary School (Bulawayo)":  "Dominican_Convent_Primary_School,_Bulawayo",
    "Eaglesvale Senior School":             "Eaglesvale_Senior_School",
    "Falcon College":                       "Falcon_College",
    "Gateway High School":                  "Gateway_High_School_(Zimbabwe)",
    "Girls' College":                       "Girls%27_College",
    "Goldridge College":                    "Goldridge_College",
    "Hartmann House Preparatory":           "Hartmann_House_Preparatory_School",
    "Hellenic Academy":                     "Hellenic_Academy",
    "Hillcrest College":                    "Hillcrest_College",
    "Kyle College":                         "Kyle_College",
    "Lilfordia School":                     "Lilfordia_School",
    "Lomagundi College":                    "Lomagundi_College",
    "Midlands Christian College":           "Midlands_Christian_College",
    "Peterhouse Boys":                      "Peterhouse_Boys%27_School",
    "Peterhouse Girls":                     "Peterhouse_Girls%27_School",
    "Ruzawi School":                        "Ruzawi_School",
    "Springvale House":                     "Springvale_House",
    "St John's College":                    "St._John%27s_College_(Harare)",
    "St. John's Preparatory School":        "St._John%27s_Preparatory_School_(Harare)",
    "St. George's College":                 "St._George%27s_College,_Harare",
    "Watershed College":                    "Watershed_College",
    "Westridge High School":                "Westridge_High_School",
    "Whitestone School":                    "Whitestone_School",
}

UA = "MutapaTimes/1.0 (https://www.mutapatimes.com; news@mutapatimes.com)"

def fetch_wikitext(title):
    url = f"https://en.wikipedia.org/w/api.php?action=parse&page={title}&prop=wikitext|sections&format=json&redirects=1"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=20) as r:
        j = json.load(r)
    return j.get("parse", {}).get("wikitext", {}).get("*", "")

def fetch_summary(title):
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{title}"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            j = json.load(r)
        return j.get("extract", "")
    except Exception:
        return ""

def parse_infobox(wikitext):
    """Extract first infobox block and return key:value dict, lightly cleaned."""
    m = re.search(r'\{\{Infobox[^\|]*\|', wikitext, re.I)
    if not m:
        # also try with hyphens / underscores
        m = re.search(r'\{\{Infobox[\s_\-]+school', wikitext, re.I)
        if not m: return {}
    start = m.start()
    # walk braces
    depth = 0
    i = start
    while i < len(wikitext):
        if wikitext[i:i+2] == '{{':
            depth += 1; i += 2; continue
        if wikitext[i:i+2] == '}}':
            depth -= 1; i += 2
            if depth == 0: break
            continue
        i += 1
    block = wikitext[start:i]
    out = {}
    # split into | key = value entries at the top level only
    # use a simple state machine: track nested {{ }} and [[ ]]
    parts = []
    cur = []
    depth_t = 0
    depth_l = 0
    for ch in block[2:-2]:  # strip outer {{ }}
        if ch == '|' and depth_t == 0 and depth_l == 0:
            parts.append(''.join(cur)); cur = []
        else:
            if cur and cur[-1] == '{' and ch == '{': depth_t += 1
            if cur and cur[-1] == '}' and ch == '}': depth_t -= 1
            if cur and cur[-1] == '[' and ch == '[': depth_l += 1
            if cur and cur[-1] == ']' and ch == ']': depth_l -= 1
            cur.append(ch)
    if cur: parts.append(''.join(cur))
    # first part is the template name
    for p in parts[1:]:
        if '=' not in p: continue
        k, v = p.split('=', 1)
        out[k.strip().lower()] = v.strip()
    return out

def clean_value(v):
    if not v: return ""
    # Strip ref tags
    v = re.sub(r'<ref[^>]*>.*?</ref>', '', v, flags=re.S)
    v = re.sub(r'<ref[^>]*/>', '', v)
    # Strip image links
    v = re.sub(r'\[\[File:[^\]]+\]\]', '', v, flags=re.I)
    # Strip {{cite ...}} templates
    v = re.sub(r'\{\{cite[^}]*\}\}', '', v, flags=re.I)
    # Wikilinks: [[X|Y]] -> Y, [[X]] -> X
    v = re.sub(r'\[\[([^|\]]+)\|([^\]]+)\]\]', r'\2', v)
    v = re.sub(r'\[\[([^\]]+)\]\]', r'\1', v)
    # Bold/italic
    v = re.sub(r"'''([^']+)'''", r'\1', v)
    v = re.sub(r"''([^']+)''", r'\1', v)
    # Templates we can't resolve cleanly — drop them
    v = re.sub(r'\{\{[^}]*\}\}', '', v)
    # HTML tags
    v = re.sub(r'<br\s*/?>', '; ', v, flags=re.I)
    v = re.sub(r'<[^>]+>', '', v)
    # Whitespace
    v = re.sub(r'\s+', ' ', v).strip()
    v = v.strip(' ;,.')
    return v

KEYS_OF_INTEREST = [
    "name","established","established_date","founded","opened",
    "type","gender","religion","religious_affiliation","denomination",
    "motto","motto_translation","head","headteacher","headmaster","headmistress","principal",
    "rector","president","fees","enrollment","enrolment","students","number_of_students",
    "houses","colours","colors","slogan","grades","staff","alumni","mascot",
    "language","curriculum","examboard","exam_board","schoolboard","authority",
    "trust","accreditation","newspaper","yearbook","sports","patron","status",
]

def extract(title):
    wt = fetch_wikitext(title)
    if not wt: return None
    ib = parse_infobox(wt)
    out = {}
    for k in KEYS_OF_INTEREST:
        if k in ib:
            cv = clean_value(ib[k])
            if cv: out[k] = cv
    # Normalise some common variants
    if "established" not in out:
        for alt in ("founded","established_date","opened"):
            if alt in out:
                out["established"] = out[alt]; break
    if "head" not in out:
        for alt in ("headteacher","headmaster","headmistress","principal","rector"):
            if alt in out:
                out["head"] = out[alt]
                out["head_title"] = alt.replace("_"," ").title()
                break
    if "denomination" not in out:
        for alt in ("religion","religious_affiliation"):
            if alt in out: out["denomination"] = out[alt]; break

    out["summary"] = fetch_summary(title)
    out["wikipedia"] = f"https://en.wikipedia.org/wiki/{title}"
    return out

if __name__ == "__main__":
    enriched = {}
    for ats_name, wp_title in MAPPING.items():
        print(f"  fetching {ats_name} <- {wp_title}")
        try:
            data = extract(wp_title)
            if data:
                enriched[ats_name] = data
        except Exception as e:
            print(f"    error: {e}")
        time.sleep(0.4)  # be polite
    out_file = ROOT / "data" / "ats-schools-wp.json"
    out_file.write_text(json.dumps(enriched, indent=2, ensure_ascii=False))
    print(f"\nwrote {len(enriched)} enrichments -> {out_file}")
