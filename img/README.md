# Image-upload convention

This folder holds the imagery for every microsite on mutapatimes.com.
The build scripts read these files at build time and the GitHub Action
"Rebuild microsites" re-runs them when images change. There is **no
manual code step** needed to put an image on a page — just upload it
with the correct filename and the site picks it up.

## Where to upload via Pages CMS

In the [Pages CMS editor](https://app.pagescms.org/mutapatimes/mutapatimes),
open the **Media** tab. You'll see six folders:

| Folder | Lives at | Used by |
|---|---|---|
| General uploads | `img/uploads/` | Article featured images, sponsor logos, ad-hoc |
| Flight pages | `img/flights/` | `/flights/<slug>/` hero banners + hub banner |
| Schools directory | `img/schools/` | `/schools/<slug>.html` heros + card images on the hub |
| ZSE companies | `img/zse/` | `/zse/<slug>.html` heros + hub banner |
| Mining directory | `img/mining/` | `/mining/<slug>.html` heros + card images on the hub |
| UK / Moving-to-Zimbabwe guide | `img/uk-guide/` | `/moving-to-zimbabwe/` page heros |

## Filename rules

The file's name **must match the page's slug**. Examples:

```
img/flights/london-to-harare.jpg          → /flights/london-to-harare/
img/flights/harare-airport.jpg            → /flights/harare-airport/
img/schools/falcon-college.jpg            → /schools/falcon-college.html
img/zse/delta-corporation.jpg             → /zse/delta-corporation.html
img/mining/bikita-minerals.jpg            → /mining/bikita-minerals.html
img/uk-guide/visa-on-arrival.jpg          → /moving-to-zimbabwe/visa-on-arrival.html
```

To put a banner image on a **hub** page (e.g. `/schools/`, `/mining/`,
`/zse/`), upload with the special filename `_hero.jpg`:

```
img/schools/_hero.jpg   → banner on /schools/
img/mining/_hero.jpg    → banner on /mining/
img/zse/_hero.jpg       → banner on /zse/
```

## Accepted file types

`.jpg` (or `.jpeg`), `.png`, `.webp`. Schools and ZSE also accept `.svg`
for logo-style entries. The build scripts try each extension in that
order, so if you accidentally upload both `falcon-college.jpg` and
`falcon-college.png`, the `.jpg` wins.

## What happens after upload

1. You upload via Pages CMS → it commits the image file to the repo.
2. The GitHub Action **"Rebuild microsites"** triggers on push to any
   path inside `img/<microsite>/` or `data/`.
3. The action runs:
   ```
   python3 scripts/build_schools.py
   python3 scripts/build_zse.py
   python3 scripts/build_mining.py
   python3 scripts/build_flight_pages_v2.py
   python3 scripts/install_nav_drawer.py
   ```
4. Regenerated HTML is committed back to `main`.
5. GitHub Pages redeploys.
6. Image is live, end-to-end, in **2–4 minutes**.

You don't need to do anything between steps 1 and 6.

## Reserved filenames (don't upload anything with these)

| Filename | Reason |
|---|---|
| `_hero.<ext>` | Hub banner |
| `_reserve-*.<ext>` | Holding area for images not yet assigned to a slug |

## Finding the right slug

If you're not sure of the slug for a school / company / mine / corridor,
the easiest way is to open the entity's live page and look at the URL.
For example:

- `https://www.mutapatimes.com/schools/peterhouse-boys.html` → slug is `peterhouse-boys`
- `https://www.mutapatimes.com/flights/london-to-harare/` → slug is `london-to-harare`

Slugs are also listed in `data/ats-schools.json`, `data/zse-companies.json`,
`data/mines.json`, and `data/travelpayouts-widgets.json`.

## Image sizing

- **Hub banners** (`_hero.jpg`) render at 21:9 aspect ratio. Upload at
  least 1600 × 686 px. Larger is fine; smaller crops badly.
- **Per-entity heros** on detail pages render at the same 21:9 ratio
  (flights) or as a square/wide image at the top of the profile
  (schools, ZSE, mining).
- **Card images** on directory hub cards render at 16:9 within a card
  that's ~280px wide. Upload at least 640 × 360 px.

There's no need to crop ahead of upload — CSS `object-fit: cover`
handles the framing. But the image's centre is what shows on small
viewports, so frame your subject centrally.

## Replacing / removing images

To **replace**: upload a new file with the same name. The old one is
overwritten in Git.

To **remove**: delete the file via Pages CMS Media. The page reverts
to its monogram (initial letter on a coloured tile) on the next
rebuild.

## Reserve directory (for ops use, ignore in CMS)

Files prefixed `_reserve-*` are images we've downloaded but not yet
assigned to a specific entity. Edit the filename to a real slug
(e.g. rename `_reserve-stocks-slide.jpg` to `old-mutual.jpg`) and
the auto-rebuild slots it into place.
