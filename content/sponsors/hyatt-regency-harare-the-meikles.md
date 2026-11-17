---
name: Hyatt Regency Harare The Meikles
active: false
strip_copy: "Sponsored briefing by Hyatt Regency Harare The Meikles, the 1915 landmark on Africa Unity Square."
url: "https://www.hyatt.com/hyatt-regency/en-US/hrerh-hyatt-regency-harare-the-meikles"
impression_pixel: ""

# Strip surfaces for the takeover week: the editorial line runs at the top
# of the homepage feed and every article page.
placements:
  - news
  - articles
  - harare-cities

# Card surfaces: the travel pages where a visual sits comfortably.
card_placements:
  - flights
  - airports
  - diaspora

# Creative: supply a 728x90 or 300x250 from the hotel, or leave blank and
# only the text strip runs.
creative_url: ""
creative_width: 728
creative_height: 90
creative_eyebrow: "Presented by Hyatt Regency Harare The Meikles"
creative_caption: "Harare's grand hotel, on the square since 1915 →"

# Weight above the travel partners so the takeover sponsor wins the
# rotation on shared surfaces for the week.
weight: 3.0
start_date: 2026-11-17T00:00:00.000Z
end_date: 2026-11-24T23:59:59.000Z
notes: |
  TEMPLATE. Set active: true when the contract is signed.

  The takeover week, in order:
    1. Article: content/articles/2026-11-17-hyatt-regency-harare-the-meikles-hotel-review.md
       Fill every [bracket], add the hero image, set draft: false and
       feature_story: true. The front matter already carries
       partner / partner_url / takeover: true, which turns the homepage
       Feature Story lead into the full-bleed "In partnership with" card.
    2. Run scripts/build_feature_story.py (writes data/feature-story.json
       and pins the piece to the top of the spotlight rail) and
       scripts/build_static_pages.py.
    3. This file: active: true, dates set to the campaign week. Run
       scripts/build_sponsors.py so the strip goes live across news,
       articles and the Harare city page.
    4. Optional: a Story Rail slide and a newsletter Takeover edition,
       sold separately on the rate card.

  To end the takeover: set feature_story: false on the article and
  active: false here, then rerun the two build scripts. The review stays
  live as an ordinary Travel longform.
---
