/* Mutapa Times Academy: course content.
   Pure data. Add lessons and exercises here; the engine renders them.
   Exercise types: "mcq" (one answer), "multi" (several), "order"
   (sequence), "write" (self-check against a model answer).
   House rules: no em dashes, no italics, Zimbabwe and diaspora voice. */

window.COURSE = {
  title: "Mutapa Times Academy",
  blurb: "Learn to report on Zimbabwe and the diaspora. Self-paced, with instant feedback.",
  units: [
    {
      id: "w1",
      title: "Week 1: Foundations",
      summary: "What news is, how it differs from PR, our voice, and the ethics that hold it all up.",
      lessons: [
        {
          id: "news-values",
          title: "What is news?",
          minutes: 6,
          intro: "News is what is new, true, and matters to your reader. Learn to spot it.",
          cards: [
            {
              h: "The six things that make a story news",
              body: [
                "A story is worth telling when it has one or more of these: timeliness (it is new), proximity (it is close to home), impact (it changes something), conflict (sides disagree), human interest (a person at the centre), and prominence (someone well known is involved).",
                "The more of these a story carries, and the stronger they are, the bigger the story."
              ]
            },
            {
              h: "Proximity is not only distance",
              body: [
                "For a Mutapa Times reader in London or Johannesburg, proximity is emotional and financial as much as geographic. A change to how the diaspora sends money home is close to home, even from three thousand miles away.",
                "Always ask: why does this matter to a Zimbabwean reading us today?"
              ]
            }
          ],
          exercises: [
            {
              type: "mcq",
              q: "Which story is most newsworthy for a Mutapa Times reader living in the UK?",
              options: [
                "A local council vote in a town they have no link to",
                "A change to how diaspora Zimbabweans can send money home",
                "A weather forecast for a country they do not live in",
                "A sports result from an unrelated league"
              ],
              answer: 1,
              explain: "Proximity is not only geographic. A change touching their family and money is close to home."
            },
            {
              type: "multi",
              q: "A long-serving cabinet minister resigns suddenly during a budget crisis. Which news values are clearly present? Select all.",
              options: ["Timeliness", "Prominence", "Conflict", "Human interest"],
              answers: [0, 1, 2],
              explain: "It is new (timeliness), involves a well known figure (prominence), and sits inside a dispute (conflict). Human interest would need a person's personal story at the centre."
            },
            {
              type: "mcq",
              q: "What does timeliness mean in news?",
              options: [
                "The story is well written",
                "The story is new, or newly relevant, right now",
                "The story is long enough to fill a page",
                "The story has a famous person in it"
              ],
              answer: 1,
              explain: "Timeliness is about now. An old fact can become timely again when something changes."
            }
          ]
        },
        {
          id: "news-vs-pr",
          title: "News, opinion and PR",
          minutes: 6,
          intro: "A press release wants you to act. News tells you what happened and lets you decide.",
          cards: [
            {
              h: "Three different things",
              body: [
                "News reports what happened, with sources. Opinion argues a view, clearly labelled as such. Public relations promotes a person, product or cause.",
                "Mixing them up is the fastest way to lose a reader's trust."
              ]
            },
            {
              h: "How to spot PR dressed as news",
              body: [
                "Watch for words that praise rather than inform: proud, excited, leading, world-class, game-changing. Watch for claims with no source, and for a call to act or believe.",
                "Strip the praise and ask what actually happened. If little is left, it was PR."
              ]
            }
          ],
          exercises: [
            {
              type: "mcq",
              q: "Which of these is news rather than public relations?",
              options: [
                "A company statement headlined: We are proud to announce our exciting new vision",
                "A report that a state firm's annual losses widened, with figures from its filings",
                "A release urging readers to join the movement today",
                "A brochure listing the benefits of a new product"
              ],
              answer: 1,
              explain: "News tells you what happened and lets you decide. The other three want you to act or believe something."
            },
            {
              type: "multi",
              q: "Which phrases are warning signs of PR language? Select all.",
              options: [
                "world-class, game-changing solution",
                "the company reported a loss of US$4m",
                "we are excited to lead the industry",
                "according to filings seen by our reporter"
              ],
              answers: [0, 2],
              explain: "Praise words with no source signal PR. Concrete figures and sourced claims signal reporting."
            },
            {
              type: "mcq",
              q: "An opinion piece must always be:",
              options: [
                "Free of any facts",
                "Clearly labelled as opinion",
                "Written by the editor",
                "Shorter than a news story"
              ],
              answer: 1,
              explain: "Opinion can use facts, but the reader must know they are reading an argument, not a report."
            }
          ]
        },
        {
          id: "remit-voice",
          title: "Our remit and voice",
          minutes: 5,
          intro: "Who reads us, what we cover, and the stories only we are placed to tell.",
          cards: [
            {
              h: "Who we write for",
              body: [
                "Mutapa Times serves Zimbabweans at home and across the diaspora. The reader is intelligent, often homesick, and wants Zimbabwe taken seriously, not explained to outsiders.",
                "We do not translate Zimbabwe for a foreign audience. We report it for our own."
              ]
            },
            {
              h: "A good Mutapa Times story",
              body: [
                "It is a story only we are placed to tell well: grounded in real detail, fair, and useful to a Zimbabwean reader. It avoids the generic wire angle and finds the specific.",
                "If a story could run anywhere with the country name swapped out, it is not yet a Mutapa Times story."
              ]
            }
          ],
          exercises: [
            {
              type: "mcq",
              q: "Which framing fits the Mutapa Times voice best?",
              options: [
                "Zimbabwe, a landlocked nation in southern Africa, is a place where...",
                "Diaspora families are bracing for higher fees on the money they send home",
                "For those unfamiliar with Zimbabwe, here is some background",
                "Experts say the situation in the African country is complex"
              ],
              answer: 1,
              explain: "We write for Zimbabweans, not for outsiders needing the country explained. Lead with what affects the reader."
            },
            {
              type: "mcq",
              q: "How do you know a story is not yet a Mutapa Times story?",
              options: [
                "It is too long",
                "It could run anywhere with the country name swapped out",
                "It quotes a source",
                "It is about the economy"
              ],
              answer: 1,
              explain: "If it is generic and interchangeable, it lacks the specific, grounded angle that makes it ours."
            }
          ]
        },
        {
          id: "ethics",
          title: "Ethics and responsibility",
          minutes: 6,
          intro: "Accuracy, fairness, and minimising harm, with the extra duty of reporting Zimbabwe well.",
          cards: [
            {
              h: "The three duties",
              body: [
                "Accuracy: get it right, and correct it openly when you do not. Fairness: give people a chance to respond, and represent views honestly. Harm: weigh the damage publication can do, especially to people without power.",
                "These are not optional extras. They are the job."
              ]
            },
            {
              h: "The extra weight when reporting Zimbabwe",
              body: [
                "Official information can be thin or contested, and getting it wrong can put real people at risk. That raises the bar for verification and for care with names and identifying detail.",
                "When in doubt, slow down and check again."
              ]
            }
          ],
          exercises: [
            {
              type: "mcq",
              q: "You publish a story and later find a key figure was wrong. What is the right move?",
              options: [
                "Quietly delete the story",
                "Leave it, since most readers will not notice",
                "Correct it openly and note the correction",
                "Blame the source in a new article"
              ],
              answer: 2,
              explain: "Accuracy includes correcting openly. Quiet deletion erodes trust more than the error did."
            },
            {
              type: "multi",
              q: "Which steps reduce harm when reporting on vulnerable people? Select all.",
              options: [
                "Withhold identifying detail that is not essential",
                "Publish a home address to prove you were there",
                "Consider the risk to the person, not just the story",
                "Give a named subject a chance to respond"
              ],
              answers: [0, 2, 3],
              explain: "Minimising harm means publishing only what is needed and weighing the risk to people, while still being fair."
            }
          ]
        }
      ]
    },
    {
      id: "newsroom",
      title: "Inside the newsroom",
      summary: "Who does what, how a story actually moves from tip to publication, and how to read an outlet.",
      lessons: [
        {
          id: "newsroom-roles",
          title: "Who does what",
          minutes: 8,
          intro: "A newsroom is a hierarchy of decisions. Learn who makes which one, and who to talk to.",
          cards: [
            {
              h: "Leadership sets direction, not the daily desk",
              body: [
                "At the top sits the editor-in-chief or executive editor, who sets the standards and the overall direction. Below them a managing editor runs daily operations across the newsroom. These are strategy roles. They rarely handle an individual story coming in from outside.",
                "If you want a specific story considered, the leadership is almost never your first contact. You want the people who run daily coverage."
              ]
            },
            {
              h: "The gatekeepers of daily coverage",
              body: [
                "The news editor and, in broadcast, the assignment editor decide what gets covered today. The assignment editor watches incoming tips, tracks breaking news, vets sources and moves stories forward. Section or desk editors (Business, Metro, Politics) shape coverage in their area.",
                "These are the people a story has to convince. They are busy and protective of their readers' time."
              ]
            },
            {
              h: "Reporters, producers and the digital desk",
              body: [
                "Reporters research, interview and write, often on a fixed beat such as courts, business or health. In smaller markets many are multimedia journalists who shoot and edit their own pieces. Producers build the running order of a broadcast and write scripts for anchors. A sub-editor or copy editor checks and tightens copy before it runs.",
                "Most newsrooms are now digital-first, so a digital editor or web producer publishes online, writes headlines for search, and often decides what gets homepage prominence."
              ]
            }
          ],
          exercises: [
            {
              type: "mcq",
              q: "You have a strong, non-urgent story idea for a daily paper. Who is usually the best first contact?",
              options: [
                "The editor-in-chief, to go straight to the top",
                "The beat reporter or section editor who covers that subject",
                "The managing editor, who runs the whole newsroom",
                "Whoever answers the main phone line"
              ],
              answer: 1,
              explain: "Pitch the person who owns that coverage day to day. Leadership sets direction and rarely handles individual story intake."
            },
            {
              type: "mcq",
              q: "In a broadcast newsroom, who tracks incoming tips and decides which stories move forward today?",
              options: ["The anchor", "The assignment editor", "The news director", "The camera operator"],
              answer: 1,
              explain: "The assignment editor is the daily gatekeeper. The news director sets strategy, not story-by-story intake."
            },
            {
              type: "mcq",
              q: "Who most often decides which story gets prominence on the homepage?",
              options: [
                "The photojournalist",
                "The digital editor or web producer",
                "The advertising team",
                "The anchor"
              ],
              answer: 1,
              explain: "In digital-first newsrooms the digital editor publishes online, writes search headlines, and shapes homepage placement."
            },
            {
              type: "mcq",
              q: "A reporter described as an MMJ in a small market most likely:",
              options: [
                "Manages the whole newsroom",
                "Reports, films and edits their own stories",
                "Only reads the news on air",
                "Sells advertising space"
              ],
              answer: 1,
              explain: "MMJ means multimedia journalist: a one-person crew who reports, shoots and edits, common in smaller markets."
            },
            {
              type: "multi",
              q: "Which of these are mainly leadership or strategy roles, not daily story intake? Select all.",
              options: ["Executive editor", "Assignment editor", "Managing editor", "Beat reporter"],
              answers: [0, 2],
              explain: "Executive and managing editors set direction and run operations. The assignment editor and beat reporter handle daily coverage."
            }
          ]
        },
        {
          id: "story-flow",
          title: "How a story moves",
          minutes: 8,
          intro: "From tip to published, a story passes through gathering, production and output. The path differs by medium.",
          cards: [
            {
              h: "Three stages, every newsroom",
              body: [
                "Gathering: reporters, researchers and tips bring news in, from sources, documents, agencies and PR. Production: the desk checks, edits and shapes it, deciding placement and framing. Output: it is published, on air, in print, or online.",
                "Quality control happens at each stage. A claim is checked before it becomes a fact, and copy is edited before it reaches a reader."
              ]
            },
            {
              h: "Print and broadcast differ in production",
              body: [
                "In print, an editorial team handles layout, images, headlines and the final placement decision, signed off by the editor and sub-editor. In broadcast, a story is rewritten for air, then built in the production control room, the PCR, which assembles the live programme. A master control room, the MCR, formats and verifies the final feed before it goes out.",
                "Those control rooms are unique to broadcast. Print and digital have no equivalent."
              ]
            },
            {
              h: "Digital is continuous, not a single deadline",
              body: [
                "Digital-first newsrooms publish around the clock and update in real time, rather than aiming at one nightly deadline. A single story may run online within minutes, get optimised for search, and be shared across social channels, living far beyond its first version.",
                "That speed raises both the opportunity and the risk of getting something wrong in public."
              ]
            }
          ],
          exercises: [
            {
              type: "order",
              q: "Put the journey of a story in order, from first to last.",
              items: [
                "Gathering: reporters and tips bring the news in",
                "Production: the desk checks, edits and shapes it",
                "Output: it is published online, on air or in print"
              ],
              explain: "Gather, then produce and verify, then publish. Quality control sits at each step."
            },
            {
              type: "mcq",
              q: "The PCR and MCR are control rooms found in which kind of newsroom?",
              options: ["Print newspapers", "Broadcast television and radio", "Newsletter platforms", "All newsrooms equally"],
              answer: 1,
              explain: "The production control room and master control room are specific to broadcast. Print and digital have no equivalent."
            },
            {
              type: "mcq",
              q: "What most sets a digital-first newsroom apart from a traditional print one?",
              options: [
                "It never checks facts",
                "It publishes continuously and updates in real time",
                "It has no editors",
                "It only works once a day at a single deadline"
              ],
              answer: 1,
              explain: "Digital is continuous and real time, not built around one nightly deadline."
            },
            {
              type: "mcq",
              q: "At which stage is a claim turned from a hypothesis into a verified fact?",
              options: [
                "Only after publication",
                "During production, when the desk checks and edits",
                "It never is",
                "Only by the advertising team"
              ],
              answer: 1,
              explain: "Verification belongs in production, before a story reaches the reader, not after."
            }
          ]
        },
        {
          id: "outlet-types",
          title: "Reading an outlet",
          minutes: 8,
          intro: "Different outlets serve different readers. Knowing where a story belongs is half the work.",
          cards: [
            {
              h: "The main types, and who they serve",
              body: [
                "A daily newspaper reaches a broad regional public and offers depth and analysis. A business journal speaks to executives, investors and decision-makers about the economy of a region. A trade publication serves professionals inside one industry and assumes they already know the basics.",
                "Broadcast reaches a wide local audience fast. Community and special-interest outlets serve a neighbourhood, cause or group that bigger media overlook."
              ]
            },
            {
              h: "Each medium wants a different story",
              body: [
                "Radio wants strong narration and good interview audio. Television wants visuals, sound bites and a clear on-camera explanation. Digital wants speed, clarity and search visibility. Trade and business outlets want expertise and data over colour.",
                "The same facts get pitched and written differently depending on where they will live."
              ]
            },
            {
              h: "Match the story to the audience",
              body: [
                "Before pitching, ask who needs to hear this, what you want them to do, and which outlet that audience trusts. A timely legal development might suit broadcast. A deep analysis suits a daily. A niche industry shift suits a trade title.",
                "The goal is not the most coverage. It is the right coverage in front of the right reader."
              ]
            }
          ],
          exercises: [
            {
              type: "mcq",
              q: "You have a deep, data-heavy analysis aimed at executives and investors in one region. Where does it best belong?",
              options: ["A neighbourhood community newsletter", "A regional business journal", "A children's magazine", "A sports radio show"],
              answer: 1,
              explain: "Business journals speak directly to executives, investors and decision-makers about the regional economy."
            },
            {
              type: "mcq",
              q: "A trade publication differs from a general newspaper mainly because it:",
              options: [
                "Never uses sources",
                "Assumes its readers already know the industry basics",
                "Only prints on paper",
                "Avoids any analysis"
              ],
              answer: 1,
              explain: "Trade outlets serve professionals in one field and assume subject-matter familiarity, so they prioritise expertise and depth."
            },
            {
              type: "mcq",
              q: "Which storytelling need is strongest for television specifically?",
              options: [
                "Search-optimised headlines",
                "Strong visuals and clear on-camera sound bites",
                "Long footnoted data tables",
                "Audio narration only"
              ],
              answer: 1,
              explain: "Television leads with visuals and concise sound bites. Audio narration is radio; search headlines are digital."
            },
            {
              type: "multi",
              q: "Good questions to ask before choosing an outlet to pitch. Select all.",
              options: [
                "Who needs to hear this message?",
                "Which outlet does that audience trust?",
                "How can I get the most placements anywhere?",
                "Does this story need immediacy, depth or industry context?"
              ],
              answers: [0, 1, 3],
              explain: "Strategy is about alignment with the right reader, not chasing the highest volume of scattered mentions."
            }
          ]
        },
        {
          id: "newsroom-of-one",
          title: "The newsroom of one",
          minutes: 7,
          intro: "An independent newsletter is a whole newsroom run by one person. Here is every job you take on.",
          cards: [
            {
              h: "You are every desk now",
              body: [
                "Running your own newsletter means you are the reporter, the editor, the sub-editor, the publisher and the growth team at once. The same disciplines still apply: gather and verify, edit yourself honestly, and publish on a reliable rhythm.",
                "The freedom is real, and so is the responsibility. There is no second pair of eyes unless you build one in."
              ]
            },
            {
              h: "What holds a newsletter together",
              body: [
                "A clear niche, a voice readers recognise, a cadence you can sustain, and trust earned by being accurate and consistent. For a Zimbabwean or diaspora audience, the edge is the specific story told from the inside, not the generic angle.",
                "Pick a rhythm you can keep for a year, not one you can keep for a fortnight."
              ]
            }
          ],
          exercises: [
            {
              type: "mcq",
              q: "What is the biggest practical risk of being a newsroom of one?",
              options: [
                "You cannot write headlines",
                "There is no second pair of eyes unless you build one in",
                "You are not allowed to use sources",
                "You cannot publish online"
              ],
              answer: 1,
              explain: "Solo means no built-in editor or fact-checker. Good independent writers create that check deliberately."
            },
            {
              type: "mcq",
              q: "Choosing a publishing cadence, the soundest advice is:",
              options: [
                "Publish as often as physically possible at first",
                "Pick a rhythm you can sustain for a year",
                "Never set a schedule",
                "Only publish when you feel inspired"
              ],
              answer: 1,
              explain: "Consistency over a long stretch builds trust and habit. A burst you cannot maintain does the opposite."
            }
          ]
        }
      ]
    },
    {
      id: "money",
      title: "How news makes money",
      summary: "Who pays for journalism, how paywalls work, how to include readers who cannot pay, and why funding shapes the news.",
      lessons: [
        {
          id: "revenue-models",
          title: "Who pays for the news",
          minutes: 8,
          intro: "A newsroom is a business. Knowing how it earns tells you a lot about the journalism it produces.",
          cards: [
            {
              h: "Someone always pays",
              body: [
                "News costs money. Reporters, editors and equipment all need funding, so every newsroom has to earn its keep somehow. The honest starting point is that no journalism is free to make, even when it is free to read.",
                "Because of that, every source of funding shapes the work to some degree. Follow the money and you understand a lot about why the news looks the way it does."
              ]
            },
            {
              h: "The four main models",
              body: [
                "Advertising: companies pay to place ads around the content, so readers get it free. Reader revenue: readers pay directly, through subscriptions or memberships. Public funding: the state supports public-service broadcasting. Nonprofit and donor: foundations and supporters fund mission-driven journalism.",
                "Most real newsrooms mix several of these rather than relying on one."
              ]
            },
            {
              h: "What each model suits",
              body: [
                "Advertising suits free, mass-reach content that would lose its audience behind a paywall. Subscriptions suit content unique enough that readers cannot get it free elsewhere. Public funding suits broad public-service media. Nonprofit funding suits impact journalism that may never be highly profitable but serves the public.",
                "The model an outlet chooses follows from what it makes and who it serves."
              ]
            }
          ],
          exercises: [
            {
              type: "mcq",
              q: "Why does it matter to a reader where a news outlet gets its money?",
              options: [
                "It does not matter at all",
                "Because the source of funding shapes the journalism that gets done",
                "Because readers must pay for every article",
                "Only advertisers need to know"
              ],
              answer: 1,
              explain: "Follow the money. Every funding source influences coverage, so knowing it helps you read the news wisely."
            },
            {
              type: "multi",
              q: "Which of these are the main ways news organisations fund themselves? Select all.",
              options: ["Advertising", "Reader revenue (subscriptions or memberships)", "Public or government funding", "Nonprofit and donor support"],
              answers: [0, 1, 2, 3],
              explain: "All four are core models. Most newsrooms combine several rather than relying on one."
            },
            {
              type: "mcq",
              q: "A subscription model works best when an outlet's content is:",
              options: [
                "Easy to find free anywhere else",
                "Unique enough that readers cannot get it for free elsewhere",
                "Only advertising",
                "Never updated"
              ],
              answer: 1,
              explain: "People pay for what they cannot get free. Subscriptions reward distinctive, high-value content."
            },
            {
              type: "mcq",
              q: "Under a pure advertising model, the reader typically gets the content:",
              options: ["For a monthly fee", "Free, because advertisers pay", "Only by donating", "Only from the government"],
              answer: 1,
              explain: "Advertisers pay to reach the audience, which lets the outlet offer content free and reach more people."
            }
          ]
        },
        {
          id: "news-business-today",
          title: "The news business today",
          minutes: 7,
          intro: "The newspaper industry is in the middle of a hard shift from print to digital. Here is the shape of it.",
          cards: [
            {
              h: "From print to digital",
              body: [
                "Readers have moved online, and the industry is following. Newspapers now invest heavily in websites, apps and newsletters, chasing real-time delivery and interactive content rather than a single daily print run. Most metro and national titles are digital-first, with print serving as a curated summary.",
                "The global newspaper business is still worth tens of billions of dollars a year, but the mix of where that money comes from is changing fast."
              ]
            },
            {
              h: "Print falls, reader revenue rises",
              body: [
                "Print circulation and print advertising have been declining for years, especially among younger readers. At the same time, digital subscriptions and other reader revenue are growing, and at some major titles reader revenue has now overtaken advertising for the first time.",
                "The strategic pivot for most newsrooms is the same: replace falling print income with digital subscriptions and direct reader support."
              ]
            },
            {
              h: "Competition, and the local opportunity",
              body: [
                "Social platforms and free online news compete fiercely for both attention and advertising, squeezing traditional outlets. Yet demand for local and community news is strong, and many readers prefer it to national coverage. Emerging markets, where internet use is still rising, are a growth frontier.",
                "The outlets that do well tend to own a clear niche, lean into local or specialist strength, and build a direct relationship with readers."
              ]
            }
          ],
          exercises: [
            {
              type: "mcq",
              q: "What is the biggest structural shift reshaping the newspaper industry?",
              options: [
                "A move from digital back to print",
                "A move from print to digital, with reader revenue replacing print income",
                "The end of all advertising",
                "Newspapers becoming free of cost to produce"
              ],
              answer: 1,
              explain: "Readers moved online, print declined, and digital subscriptions and reader revenue are taking over from print income."
            },
            {
              type: "mcq",
              q: "What has been happening to print circulation and print advertising?",
              options: [
                "Both rising sharply",
                "Both declining, especially among younger readers",
                "Print advertising rising, circulation falling",
                "No change for decades"
              ],
              answer: 1,
              explain: "Both have fallen for years as audiences shifted to digital, which is why newsrooms are pivoting online."
            },
            {
              type: "mcq",
              q: "Why is local news described as an opportunity, not just a casualty?",
              options: [
                "Readers dislike local news",
                "Demand for local and community coverage is strong and many readers prefer it",
                "Local news is illegal to charge for",
                "It needs no reporting"
              ],
              answer: 1,
              explain: "Strong, loyal demand for local and community news is a real growth opportunity for focused outlets."
            },
            {
              type: "multi",
              q: "Which trends are reshaping the newspaper business today? Select all.",
              options: [
                "Digital-first publishing and real-time delivery",
                "Growth in digital subscriptions and reader revenue",
                "Rising print circulation everywhere",
                "Competition from social platforms and free online news"
              ],
              answers: [0, 1, 3],
              explain: "Digital-first, reader revenue and platform competition are all rising. Print circulation is falling, not rising."
            }
          ]
        },
        {
          id: "paywalls",
          title: "Paywalls and reader revenue",
          minutes: 8,
          intro: "As reader revenue overtakes advertising at many titles, how you charge matters as much as whether you charge.",
          cards: [
            {
              h: "Not all paywalls are the same",
              body: [
                "A hard paywall locks almost everything. A metered paywall gives a set number of free articles a month, then asks you to pay. A freemium model keeps some content free and reserves the best for payers. A dynamic paywall flexes: one Swedish paper locks its most-read articles only a few hours after publishing.",
                "The wall can also move with the reader. A first-time visitor and a daily loyal reader can meet it in different places."
              ]
            },
            {
              h: "Subscription or membership",
              body: [
                "A subscription is a transaction: pay, and you get access. A membership is a relationship: you support the journalism and the mission, often with extras, but the conversation is about belonging, not just access. Membership models let an outlet talk to readers as supporters rather than customers.",
                "The more emotional, less transactional the relationship, the more loyal the reader tends to be."
              ]
            },
            {
              h: "Let readers taste the best",
              body: [
                "Readers will never value content they cannot sample. Many outlets deliberately open the paywall during big news, to let new readers in and start habits, then invite them to pay. One Swedish paper dropped its wall within a day when the pandemic hit, and converted a quarter of the new free registrations later.",
                "Think in phases: growth first, then retention, then monetisation."
              ]
            }
          ],
          exercises: [
            {
              type: "mcq",
              q: "What is a metered paywall?",
              options: [
                "Everything is locked from the first click",
                "Readers get a set number of free articles, then must pay",
                "All content is always free",
                "Only advertisers can read"
              ],
              answer: 1,
              explain: "Metered means a free allowance, then a prompt to subscribe. It lets readers sample before committing."
            },
            {
              type: "mcq",
              q: "A dynamic paywall that locks the most-read articles a few hours after publishing is designed to:",
              options: [
                "Punish loyal readers",
                "Capture demand for popular stories while still drawing a wide audience early",
                "Hide all news permanently",
                "Replace the newsroom"
              ],
              answer: 1,
              explain: "It lets a story reach many readers at first, then converts the strong ongoing demand into subscriptions."
            },
            {
              type: "mcq",
              q: "What best distinguishes a membership from a subscription?",
              options: [
                "Membership is always cheaper",
                "Membership is a relationship of support, not just paid access",
                "Subscriptions are illegal",
                "There is no difference"
              ],
              answer: 1,
              explain: "A subscription buys access. A membership is about supporting the mission, which builds a more loyal relationship."
            },
            {
              type: "order",
              q: "Put the reader-revenue phases in the order an outlet usually works through them.",
              items: [
                "Growth: get new readers in and sampling",
                "Retention: build the habit so they keep coming back",
                "Monetisation: convert the habit into paying support"
              ],
              explain: "Grow the audience, retain it into a habit, then monetise. Charging before there is a habit converts few."
            }
          ]
        },
        {
          id: "inclusive-revenue",
          title: "Readers who cannot pay (yet)",
          minutes: 8,
          intro: "Paywalls can shut out the people who most need the news. Some newsrooms build models that include them.",
          cards: [
            {
              h: "The risk of charging",
              body: [
                "A 2021 Reuters Institute survey found nearly half of news leaders worried that subscriptions could super-serve richer, more educated audiences and leave others behind. In a very unequal society, a strict paywall can put the truth out of reach of the people a story most affects.",
                "South Africa's Daily Maverick rejected a paywall for exactly this reason, arguing that hiding accountability journalism behind a fee would harm democracy."
              ]
            },
            {
              h: "Designs that include more people",
              body: [
                "Pay what you can: Daily Maverick lets readers choose a contribution on a sliding scale. Trust-based free access: Spain's elDiario.es added an I cannot pay option, on trust, without checking. Free for groups at risk of exclusion: a Swedish paper gave free subscriptions to first-time voters before an election, and others have done the same for unemployed readers.",
                "The common thread is to let people in, then invite support, rather than shutting them out at the door."
              ]
            },
            {
              h: "Why inclusion still pays",
              body: [
                "A reader who cannot pay today is still valuable: they may tell friends, take part in surveys, build the community, and pay later when they can. At elDiario.es, paid memberships kept growing even after a free option launched, because the relationship is emotional, not just transactional.",
                "Two articles will not build loyalty. Letting potential fans read first can."
              ]
            }
          ],
          exercises: [
            {
              type: "mcq",
              q: "What is the super-serving concern with subscription models?",
              options: [
                "They give too much away free",
                "They risk serving mainly richer, more educated audiences and excluding others",
                "They make news too cheap",
                "They only work for sport"
              ],
              answer: 1,
              explain: "If only the well-off can pay, journalism risks reaching only them, which is bad for an informed public."
            },
            {
              type: "mcq",
              q: "Daily Maverick's sliding-scale model means readers:",
              options: [
                "Must all pay the same high fee",
                "Choose how much to contribute, according to what they can afford",
                "Cannot read unless they are wealthy",
                "Pay only through advertising"
              ],
              answer: 1,
              explain: "Pay what you can lets each reader contribute at their own level, keeping the journalism open to all."
            },
            {
              type: "mcq",
              q: "elDiario.es lets readers select I cannot pay. How does it handle this?",
              options: [
                "It demands proof of unemployment",
                "It trusts readers and does not check, keeping content open to them",
                "It blocks them after one article",
                "It charges them double later"
              ],
              answer: 1,
              explain: "The model is built on trust. Readers who cannot pay stay part of the community rather than being shut out."
            },
            {
              type: "multi",
              q: "Why can a reader who cannot pay today still be valuable to a newsroom? Select all.",
              options: [
                "They may recommend the outlet to others",
                "They may take part in surveys and community",
                "They may pay later when their circumstances change",
                "They reduce the quality of the journalism"
              ],
              answers: [0, 1, 2],
              explain: "Non-paying readers build word of mouth, community and a future paying base. They do not lower quality."
            }
          ]
        },
        {
          id: "ownership-influence",
          title: "Follow the money",
          minutes: 7,
          intro: "Who owns and funds a newsroom shapes what it covers. Learning to ask is part of media literacy.",
          cards: [
            {
              h: "Funding shapes the journalism",
              body: [
                "However well meant, every funding source influences the work. Research has found that foundation funding can change which issues nonprofit newsrooms focus on and how much of certain work gets done. Ownership shapes a newsroom even when everyone involved has good intentions.",
                "This is not a conspiracy. It is the ordinary pull of who pays the bills."
              ]
            },
            {
              h: "When ownership concentrates",
              body: [
                "When a few large companies own many outlets, the range of voices can narrow and national coverage can crowd out local reporting. The decline of local news is linked in part to this consolidation. Fewer owners can mean fewer distinct stories and perspectives reaching the public.",
                "Diversity of ownership tends to support diversity of journalism."
              ]
            },
            {
              h: "Independence and transparency",
              body: [
                "Some worry that state funding can create a conflict of interest when a newsroom must scrutinise the government that pays it. Reader-funded and independent outlets often answer this with transparency: elDiario.es is owned by its founders, who work in the newsroom, and it publishes its results and revenue sources each year.",
                "As a reader, the useful habit is simple: ask who funds this, and what that might shape."
              ]
            }
          ],
          exercises: [
            {
              type: "mcq",
              q: "In media literacy, follow the money means:",
              options: [
                "Journalists should chase the highest salary",
                "Understanding who funds an outlet, because funding shapes its journalism",
                "Only read paid content",
                "Ignore where news comes from"
              ],
              answer: 1,
              explain: "Knowing who pays helps you judge possible influences on what is covered and how."
            },
            {
              type: "mcq",
              q: "What did research find about foundation funding of nonprofit newsrooms?",
              options: [
                "It has no effect on coverage",
                "It can change which issues they focus on and how much work gets done",
                "It guarantees total independence",
                "It only funds sport"
              ],
              answer: 1,
              explain: "Even mission-driven funding shapes the agenda. No funding source is entirely neutral."
            },
            {
              type: "mcq",
              q: "A common concern when a few companies own many outlets is that:",
              options: [
                "There is too much local news",
                "The range of voices narrows and local reporting declines",
                "Journalism becomes free",
                "Advertising disappears"
              ],
              answer: 1,
              explain: "Concentration is linked to fewer distinct voices and the decline of local news."
            },
            {
              type: "mcq",
              q: "Why do some worry about government funding for newsrooms?",
              options: [
                "It is always illegal",
                "It can create a conflict of interest when the newsroom must scrutinise its funder",
                "It makes news too expensive",
                "It bans advertising"
              ],
              answer: 1,
              explain: "A newsroom funded by the state may face pressure, real or perceived, when holding that state to account."
            },
            {
              type: "write",
              q: "Design a funding model for your publication.",
              brief: [
                "Imagine you are launching a small Zimbabwean or diaspora publication. In a few sentences, describe how it would fund itself.",
                "Cover: which models you would use, why they fit your readers, and one thing you would do so readers who cannot pay are not shut out."
              ],
              checklist: [
                "Does it name one or more specific revenue models and why they fit?",
                "Does it consider what your particular readers can realistically pay?",
                "Does it include readers who cannot pay, not just those who can?",
                "Is it honest about the trade-offs of the funding you chose?"
              ],
              model: "A diaspora newsletter could start free and ad-light to grow trust, then add a membership rather than a hard paywall: a pay-what-you-can scale from a small monthly amount upward, with extras like member events. To include those who cannot pay, an I cannot pay option on trust keeps the journalism open, since many readers send money home already and budgets are tight. The trade-off is slower revenue, accepted in exchange for reach and loyalty.",
              exerciseId: "funding-model-1"
            }
          ]
        }
      ]
    },
    {
      id: "w2",
      title: "Week 2: Reporting",
      summary: "Find sources, run an interview, verify what you are told, and report from a distance.",
      lessons: [
        {
          id: "finding-sources",
          title: "Finding sources",
          minutes: 6,
          intro: "Where stories actually come from, and the difference between a source and a press release.",
          cards: [
            {
              h: "Build people, not just contacts",
              body: [
                "The best stories come from people who trust you over time, not from a one-off email. Keep in touch when you do not need anything. Be reliable and fair, and sources come back.",
                "A press release is a starting point, never the story itself. It tells you someone wants something said."
              ]
            },
            {
              h: "Range of sources",
              body: [
                "Lean on more than one kind: people with direct knowledge, documents and data, and independent experts who can put it in context.",
                "One source is a claim. Two or more, that agree independently, start to become a fact."
              ]
            }
          ],
          exercises: [
            {
              type: "mcq",
              q: "A government department emails you a press release announcing a success. What is it?",
              options: [
                "A finished story ready to publish",
                "A starting point that tells you what someone wants said",
                "Proof the claim is true",
                "An independent source"
              ],
              answer: 1,
              explain: "A release is a prompt to report, not the report. Verify the claim before it becomes a story."
            },
            {
              type: "mcq",
              q: "Why keep in touch with sources when you do not need anything?",
              options: [
                "To fill time",
                "Because trust built over time produces better stories later",
                "Because it is required by law",
                "To get free tickets"
              ],
              answer: 1,
              explain: "Relationships, not transactions, produce the stories competitors cannot get."
            }
          ]
        },
        {
          id: "the-interview",
          title: "The interview",
          minutes: 7,
          intro: "Prepare, listen, and follow the unexpected answer. The interview is where stories are made.",
          cards: [
            {
              h: "Prepare, then listen",
              body: [
                "Do the research so you are not asking what you could have looked up. Write your questions, then be ready to abandon them. The best material often comes from following an answer you did not expect.",
                "Listen more than you talk. Silence makes people fill the gap."
              ]
            },
            {
              h: "On the record and background",
              body: [
                "Agree the terms before you start. On the record means you can quote and name them. Background means you can use the information but not the name. Set this clearly, and honour it.",
                "Record where you can, and still take notes."
              ]
            }
          ],
          exercises: [
            {
              type: "order",
              q: "Put a sound interview in order, from first to last.",
              items: [
                "Research the subject and the topic",
                "Prepare your questions",
                "Listen, and follow the unexpected answer",
                "Check facts and quotes before you finish"
              ],
              explain: "Research and prep come first so you can truly listen, then verify before you leave."
            },
            {
              type: "mcq",
              q: "A source says: you can use this, but do not name me. This is:",
              options: ["On the record", "On background", "A press release", "An opinion"],
              answer: 1,
              explain: "Background means use the information without attributing it to the named person. Agree it in advance."
            },
            {
              type: "mcq",
              q: "Why let silence sit after an answer?",
              options: [
                "To seem unsure",
                "Because people often fill the gap with more, and better, material",
                "To end the interview quickly",
                "Because recording needs a pause"
              ],
              answer: 1,
              explain: "Comfortable silence is a reporter's tool. The most revealing line often comes after the pause."
            }
          ]
        },
        {
          id: "verification",
          title: "Verification",
          minutes: 7,
          intro: "Treat every claim as a hypothesis until you confirm it. This matters doubly when reporting Zimbabwe.",
          cards: [
            {
              h: "Claim first, fact later",
              body: [
                "Until you check it, what you have been told is a hypothesis, not a fact. Cross-check against documents, data, and a second independent source.",
                "Confidence is not evidence. A source being sure does not make them right."
              ]
            },
            {
              h: "Simple checks that catch a lot",
              body: [
                "For images, a reverse image search shows whether a photo is old or from somewhere else. For documents, look for internal contradictions and check names, dates and figures against the record.",
                "Where official information is thin or contested, weigh sources against each other rather than trusting one."
              ]
            }
          ],
          exercises: [
            {
              type: "mcq",
              q: "A trusted contact tells you a figure with great confidence. You should:",
              options: [
                "Publish it, because they are trusted",
                "Treat it as a claim and check it against another source",
                "Ignore it",
                "Publish it as opinion"
              ],
              answer: 1,
              explain: "Confidence is not evidence. Verify before it becomes a fact in print."
            },
            {
              type: "multi",
              q: "Which are useful verification steps? Select all.",
              options: [
                "Reverse image search a photo",
                "Cross-check a figure against an independent source",
                "Trust a single anonymous tip with no support",
                "Check names and dates against the record"
              ],
              answers: [0, 1, 3],
              explain: "Independent corroboration and basic checks catch most errors. A lone unsupported tip does not."
            }
          ]
        },
        {
          id: "reporting-from-distance",
          title: "Reporting from a distance",
          minutes: 6,
          intro: "Practical methods for diaspora writers covering Zimbabwe remotely, and the limits to respect.",
          cards: [
            {
              h: "Methods that work remotely",
              body: [
                "Phone and video interviews, trusted people on the ground, official records, and local reporting you verify rather than copy. Build a small network you can call.",
                "Time zones and connectivity are real. Plan around them and confirm arrangements twice."
              ]
            },
            {
              h: "Know the limits of secondhand",
              body: [
                "You cannot describe what you did not witness as if you did. Attribute clearly: according to a resident, according to footage we verified.",
                "Distance is not a barrier to good reporting, but pretending you were there is dishonest."
              ]
            }
          ],
          exercises: [
            {
              type: "mcq",
              q: "You are in Manchester reporting on an event in Harare you did not witness. How should you describe it?",
              options: [
                "As if you were there, for impact",
                "With clear attribution to people and footage you verified",
                "Without any sources, to keep it clean",
                "As opinion"
              ],
              answer: 1,
              explain: "Attribute what you did not witness. Honesty about how you know is part of accuracy."
            },
            {
              type: "mcq",
              q: "What is the strongest asset for a diaspora reporter covering home?",
              options: [
                "Guessing well",
                "A trusted network on the ground plus careful verification",
                "Speed above all",
                "Copying local outlets"
              ],
              answer: 1,
              explain: "Trusted contacts you verify beat both guesswork and uncredited copying."
            }
          ]
        }
      ]
    },
    {
      id: "w3",
      title: "Week 3: Writing",
      summary: "Structure a piece, open it well, write clearly, and edit your own copy.",
      lessons: [
        {
          id: "structure",
          title: "Structure",
          minutes: 6,
          intro: "How a news piece is built, the inverted pyramid, and when to break it.",
          cards: [
            {
              h: "The inverted pyramid",
              body: [
                "Put the most important news first, then the key supporting facts, then quotes and detail, then background. A reader who stops after one paragraph should still have the story.",
                "It is not the only shape, but it is the one to master first."
              ]
            },
            {
              h: "When to break it",
              body: [
                "Features and human stories can open with a scene or a person and hold the news a little longer. The diaspora-newsletter format gives you room for that.",
                "Break the pyramid on purpose, for effect, not by accident."
              ]
            }
          ],
          exercises: [
            {
              type: "order",
              q: "Order a classic inverted-pyramid news story, from top to bottom.",
              items: [
                "The most important news: what happened and who it affects",
                "Key supporting facts and context",
                "Quotes and telling detail",
                "Background and minor detail"
              ],
              explain: "Most important first. A reader who leaves early still has the heart of the story."
            },
            {
              type: "mcq",
              q: "When is it fair to open with a scene instead of the hard news?",
              options: [
                "Never",
                "In a feature or human story, on purpose, for effect",
                "Only on the front page",
                "When you forgot the news"
              ],
              answer: 1,
              explain: "Break the pyramid deliberately in features, not by accident in hard news."
            }
          ]
        },
        {
          id: "the-lede",
          title: "The lede",
          minutes: 7,
          intro: "The first sentence decides whether anyone reads the second. Make it carry the story.",
          cards: [
            {
              h: "What a strong lede does",
              body: [
                "It leads with the single most newsworthy fact, names who it affects, stays concrete, and gets out of the way. Aim for one clear idea, usually under 35 words, in plain active voice.",
                "Find the one thing a reader would tell a friend, and start there."
              ]
            },
            {
              h: "What weak ledes do",
              body: [
                "They bury the point under throat-clearing: dates, process, or the name of a committee. They hedge, they pile on clauses, and they make the reader dig.",
                "If your first sentence has three commas, suspect it."
              ]
            }
          ],
          exercises: [
            {
              type: "mcq",
              q: "Which is the stronger lede?",
              options: [
                "At a meeting held on Tuesday, a committee convened to discuss various matters relating to crypto policy",
                "Zimbabwe will require crypto firms to register yearly and pay US$500, or face criminal charges"
              ],
              answer: 1,
              explain: "The second leads with the news and who it affects. The first buries it under process."
            },
            {
              type: "write",
              q: "Write the lede.",
              brief: [
                "Write the opening sentence of a news story from these facts. Lead with what matters most. Under 35 words, active voice.",
                "Facts: Zimbabwe's Finance Minister has issued the country's first crypto rules. Firms that buy, sell or hold crypto must register yearly with the Financial Intelligence Unit and pay US$500. Operating without registering is now a criminal offence."
              ],
              checklist: [
                "Does it lead with the new rules, not the date or the minister's title?",
                "Is it one clear sentence, roughly 35 words or fewer?",
                "Is it active voice and concrete?",
                "Is it accurate to the facts, inventing nothing?"
              ],
              model: "Zimbabwe will require every crypto business to register each year and pay US$500, or face criminal charges, under the country's first rules for the sector.",
              exerciseId: "lede-crypto-1"
            }
          ]
        },
        {
          id: "writing-clearly",
          title: "Writing clearly",
          minutes: 6,
          intro: "Cut clutter, use active voice, choose concrete detail, and let people speak.",
          cards: [
            {
              h: "Active and concrete",
              body: [
                "Active voice names who did what: the bank raised fees, not fees were raised. Concrete detail beats abstraction: US$500 a year beats significant costs.",
                "Prefer short, plain words. You are not being paid by the syllable."
              ]
            },
            {
              h: "Cut the clutter",
              body: [
                "Strike fillers: in order to, at this point in time, it should be noted that. Cut adjectives that praise rather than inform.",
                "Read a sentence and remove every word the meaning survives without."
              ]
            }
          ],
          exercises: [
            {
              type: "mcq",
              q: "Which sentence is clearer?",
              options: [
                "It should be noted that fees were raised by the bank at this point in time",
                "The bank raised fees"
              ],
              answer: 1,
              explain: "Active, concrete, and free of filler. Same meaning, a quarter of the words."
            },
            {
              type: "multi",
              q: "Which phrases are clutter you can usually cut? Select all.",
              options: [
                "in order to",
                "US$500",
                "at this point in time",
                "it should be noted that"
              ],
              answers: [0, 2, 3],
              explain: "Those three add words without meaning. A concrete figure like US$500 is information, keep it."
            }
          ]
        },
        {
          id: "editing-yourself",
          title: "Editing yourself",
          minutes: 5,
          intro: "Read your own work like a stranger. The second draft is where writing happens.",
          cards: [
            {
              h: "The second-draft mindset",
              body: [
                "Write the first draft to get it down. Edit the second to make it good. Leave a gap if you can, then read it as if someone else wrote it.",
                "Read it aloud. Your ear catches what your eye skips."
              ]
            },
            {
              h: "Common first mistakes",
              body: [
                "Burying the lede, leaning on adjectives, long winding sentences, and quotes that repeat what you already said. Check every name, figure and date one more time.",
                "If a paragraph does no work, cut it."
              ]
            }
          ],
          exercises: [
            {
              type: "mcq",
              q: "What is the best first move when editing your own draft?",
              options: [
                "Add more adjectives",
                "Read it aloud, as if a stranger wrote it",
                "Make it longer",
                "Publish before you lose nerve"
              ],
              answer: 1,
              explain: "Distance and your ear catch what re-reading silently will not."
            },
            {
              type: "multi",
              q: "Which are common mistakes to hunt in your second draft? Select all.",
              options: [
                "Burying the lede",
                "Quotes that repeat the text",
                "Checking every figure",
                "Long winding sentences"
              ],
              answers: [0, 1, 3],
              explain: "Those three are mistakes to fix. Checking every figure is exactly what you should be doing."
            }
          ]
        }
      ]
    },
    {
      id: "w4",
      title: "Week 4: Pitch and publish",
      summary: "Pitch a story properly, take edits well, and finish a publishable piece.",
      lessons: [
        {
          id: "the-pitch",
          title: "The pitch",
          minutes: 6,
          intro: "How to pitch an editor: the subject line, the hook, why you, and why now.",
          cards: [
            {
              h: "Four things a pitch must answer",
              body: [
                "What the story is, why it matters now, why you are the person to write it, and why it belongs in Mutapa Times specifically. Put the hook in the first two lines.",
                "An editor reads dozens of pitches. Respect their time and make the news obvious fast."
              ]
            },
            {
              h: "The subject line is the lede of your pitch",
              body: [
                "Make it specific and newsy: Diaspora families face higher fees as banks change rules. Not: story idea, or please read.",
                "If the subject line is vague, the pitch may not be opened."
              ]
            }
          ],
          exercises: [
            {
              type: "mcq",
              q: "Which pitch subject line is strongest?",
              options: [
                "Story idea",
                "Quick question",
                "Diaspora families face higher fees as banks change money-transfer rules",
                "Please read when you can"
              ],
              answer: 2,
              explain: "It is specific and newsy. The subject line is the lede of your pitch."
            },
            {
              type: "write",
              q: "Pitch the story in 150 words.",
              brief: [
                "Write a short pitch for a story you could report. Cover all four: what it is, why now, why you, and why Mutapa Times.",
                "Aim for around 150 words. Lead with the hook."
              ],
              checklist: [
                "Does the first line make the story and its news obvious?",
                "Does it say why now?",
                "Does it say why you are placed to write it?",
                "Is it clearly a Mutapa Times story, not a generic one?"
              ],
              model: "Hook: Zimbabweans in the UK are quietly switching to crypto to send money home as bank fees climb. Why now: new registration rules just brought crypto firms under formal oversight, changing the calculus for senders. Why me: I send money home monthly and have spoken to three families and two transfer agents about the shift. Why Mutapa Times: this is a diaspora money story told from the inside, not explained to outsiders. The piece would run about 900 words, with two case studies and a transfer-cost comparison.",
              exerciseId: "pitch-1"
            }
          ]
        },
        {
          id: "draft-to-published",
          title: "From draft to published",
          minutes: 6,
          intro: "Responding to edits without defensiveness, fact-checking, and the finishing touches.",
          cards: [
            {
              h: "Take edits well",
              body: [
                "An edit is not an attack. It is a second mind making the piece stronger. Ask why if you do not understand, but do not fight every change to defend the draft.",
                "The writers worth keeping are the ones who take feedback and get better fast."
              ]
            },
            {
              h: "The last checks before publication",
              body: [
                "Fact-check every name, figure and date. Write a headline that is accurate, not just catchy, and a standfirst that tells the reader why to care.",
                "A wrong fact in a strong piece still breaks trust."
              ]
            }
          ],
          exercises: [
            {
              type: "mcq",
              q: "An editor cuts a paragraph you liked. The best response is to:",
              options: [
                "Refuse and restore it",
                "Ask why if unclear, and learn from the reason",
                "Withdraw the piece",
                "Add two more paragraphs in protest"
              ],
              answer: 1,
              explain: "Edits make pieces stronger. Understand the reason rather than defend the draft."
            },
            {
              type: "multi",
              q: "Which belong on the pre-publication checklist? Select all.",
              options: [
                "Check every name, figure and date",
                "Make the headline accurate, not just catchy",
                "Add praise words to sound confident",
                "Write a standfirst that says why to care"
              ],
              answers: [0, 1, 3],
              explain: "Accuracy and a clear headline and standfirst matter. Praise words are the opposite of what to add."
            }
          ]
        },
        {
          id: "life-as-contributor",
          title: "Life as a contributor",
          minutes: 5,
          intro: "Deadlines, the pitching rhythm, and what earns the strongest writers more work.",
          cards: [
            {
              h: "Reliability is the whole game",
              body: [
                "Hit deadlines, file clean copy, and pitch regularly. An editor remembers who is dependable long after they forget a single clever line.",
                "Consistency, not the occasional brilliant piece, builds a byline."
              ]
            },
            {
              h: "What earns more work",
              body: [
                "Strong ideas, copy that needs little editing, and feedback taken well. Do those three and the work keeps coming.",
                "Treat every small piece as the audition for the next."
              ]
            }
          ],
          exercises: [
            {
              type: "mcq",
              q: "What does an editor value most over time?",
              options: [
                "One brilliant piece, then silence",
                "Reliability: deadlines met and clean copy, pitched regularly",
                "The longest articles",
                "The most adjectives"
              ],
              answer: 1,
              explain: "Dependability builds a byline. A single clever line is soon forgotten."
            },
            {
              type: "write",
              q: "Final reflection.",
              brief: [
                "In a few sentences, write the story you most want to report for Mutapa Times, and the first source you would approach.",
                "There is no wrong answer. This is your starting point."
              ],
              checklist: [
                "Is the story specific rather than a broad topic?",
                "Is it clearly a Mutapa Times story?",
                "Have you named a realistic first source?"
              ],
              model: "There is no single right answer. A strong response names a specific, grounded story (not a broad topic like the economy), explains why it suits Mutapa Times, and identifies a real first source you could actually reach.",
              exerciseId: "reflection-1"
            }
          ]
        }
      ]
    },
    {
      id: "independent",
      title: "Going independent",
      summary: "Take everything you have learned and launch your own publication: a Substack newsletter.",
      lessons: [
        {
          id: "substack-newsletter",
          title: "Start a Substack newsletter",
          minutes: 9,
          intro: "Plan and launch a newsletter you own, from the niche to the first issue.",
          cards: [
            {
              h: "What Substack is, and why writers use it",
              body: [
                "Substack is a platform for publishing an email newsletter. It is free to start, and it lets you offer both free issues and paid subscriptions. Readers sign up by email, so you build a direct relationship with your audience rather than chasing an algorithm.",
                "The key advantage is ownership: you keep your list of subscribers. If you ever move, you can take your audience with you. That independence is the whole point."
              ]
            },
            {
              h: "Four decisions before you publish",
              body: [
                "First, the promise: one clear sentence on who it is for and what they get. Second, the name: specific and memorable, not vague. Third, the cadence: weekly, fortnightly, monthly, a rhythm you can keep for a year. Fourth, the first issue: the piece that shows a new reader exactly what they signed up for.",
                "A sharp, narrow promise beats a broad one. For a diaspora audience, the specific story told from the inside is the edge."
              ]
            },
            {
              h: "Free, paid, and earning trust",
              body: [
                "Most newsletters start free to build readers and trust, then add a paid tier once there is something readers will pay to keep. Paid options include a monthly or yearly subscription, with some issues free and some for subscribers.",
                "Do not rush the money. Reliability and a voice readers recognise come first. Payment follows trust, not the other way around."
              ]
            }
          ],
          exercises: [
            {
              type: "mcq",
              q: "What is the main advantage of building an audience on a newsletter you own?",
              options: [
                "You never have to write again",
                "You keep a direct relationship with subscribers and can take your list with you",
                "It guarantees you go viral",
                "It removes the need to verify facts"
              ],
              answer: 1,
              explain: "Owning your email list means a direct relationship and independence. You are not at the mercy of an algorithm or a single platform."
            },
            {
              type: "mcq",
              q: "When should a new newsletter usually introduce a paid tier?",
              options: [
                "On day one, before any readers arrive",
                "Once it has built trust and offers something readers will pay to keep",
                "Never, paid newsletters are not allowed",
                "Only if it has a million subscribers"
              ],
              answer: 1,
              explain: "Start free to build trust and habit. Payment follows value and reliability, not the launch."
            },
            {
              type: "multi",
              q: "Which decisions should you make before you publish issue one? Select all.",
              options: [
                "The promise: who it is for and what they get",
                "A specific, memorable name",
                "The exact font on your future book cover",
                "A cadence you can sustain for a year"
              ],
              answers: [0, 1, 3],
              explain: "Promise, name and a sustainable cadence are the launch essentials. The rest is decoration you can decide later."
            },
            {
              type: "write",
              q: "Plan your Substack newsletter.",
              brief: [
                "Write a short launch plan for a newsletter you would actually run. Cover four things:",
                "1. The promise: one sentence on who it is for and what they get. 2. The name. 3. How often you will publish. 4. The headline and a two-line summary of your first issue."
              ],
              checklist: [
                "Is the promise one clear sentence about a specific reader?",
                "Is the name specific and memorable, not vague?",
                "Is the cadence one you could realistically keep for a year?",
                "Does the first issue show a new reader exactly what they signed up for?"
              ],
              model: "Promise: a weekly newsletter for Zimbabweans in the UK on the money side of diaspora life, sending, saving and supporting family back home. Name: Pounds and Home. Cadence: every Thursday morning. First issue headline: The real cost of sending GBP100 to Harare. Summary: a plain comparison of five transfer routes, what each actually costs after fees and rate, and the one most families get wrong.",
              exerciseId: "substack-plan-1"
            }
          ]
        }
      ]
    }
  ]
};
