/* Mutapa Times Academy: course content.
   Pure data. Add lessons and exercises here; the engine renders them.
   Exercise types: "mcq" (one answer), "multi" (several), "order"
   (sequence), "write" (self-check against a model answer).
   House rules: no em dashes, no italics, Zimbabwe and diaspora voice. */

window.COURSE = {
  title: "Mutapa Times Academy",
  blurb: "Learn to report on Zimbabwe, the diaspora and the wider continent. Self-paced, with instant feedback.",
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
                "A new shopping centre opening in a town they have no link to",
                "A change to how diaspora Zimbabweans can send money home",
                "A weather forecast for a country they do not live in",
                "A sports result from an unrelated league"
              ],
              answer: 1,
              explain: "Proximity is not only geographic. A change touching their family and money is close to home."
            },
            {
              type: "multi",
              q: "A long-serving company chief executive resigns suddenly during a financial crisis. Which news values are clearly present? Select all.",
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
            },
            {
              type: "swipe",
              q: "News or PR? Decide fast.",
              leftLabel: "PR",
              rightLabel: "News",
              cards: [
                { text: "We are thrilled to unveil our award-winning, world-class platform.", side: "left" },
                { text: "A factory cut 200 jobs, the company confirmed.", side: "right" },
                { text: "Join the thousands who already love our revolutionary app.", side: "left" },
                { text: "Inflation rose to 12 percent last month, official figures show.", side: "right" },
                { text: "Our visionary leadership is proud to take the industry forward.", side: "left" },
                { text: "Three public hospitals reported drug shortages this week.", side: "right" }
              ],
              explain: "PR praises and urges you to act. News reports what happened, with facts and sources."
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
        },
        {
          id: "cp-foundations",
          title: "Foundations",
          checkpoint: true,
          minutes: 12,
          intro: "A checkpoint on the foundations. You need 80% to pass, so think each one through.",
          cards: [
            {
              h: "Before you start",
              body: [
                "This checkpoint pulls together news values, news versus PR, our remit and ethics. There is no teaching here, only questions.",
                "If you do not reach 80%, review the unit and try again. There is no shortcut."
              ]
            }
          ],
          exercises: [
            {
              type: "mcq",
              q: "A mining company sends a glossy statement headlined 'We are proud to launch our world-class, community-first project.' What is the strongest news angle for The Mutapa Times?",
              options: [
                "Republish the statement so readers hear the good news",
                "Investigate what the project means for the community and whether the claims hold up",
                "Run it as an opinion piece praising the company",
                "Ignore it, company news is never relevant"
              ],
              answer: 1,
              explain: "A release is a prompt, not a story. The news is what it means for people and whether the claims stand up."
            },
            {
              type: "multi",
              q: "A long-serving company chief resigns abruptly during a financial scandal, the day after a leaked audit. Which news values are strongly present? Select all.",
              options: ["Timeliness", "Prominence", "Conflict", "Human interest"],
              answers: [0, 1, 2],
              explain: "It is new, involves a prominent figure and sits inside a dispute. Human interest would need a person's personal story at the centre."
            },
            {
              type: "mcq",
              q: "After publishing, you find you misspelt a source's name and got their title wrong. The right action is to:",
              options: [
                "Leave it, the story is otherwise fine",
                "Delete the whole story",
                "Correct both openly and note the correction",
                "Change it quietly and tell no one"
              ],
              answer: 2,
              explain: "Accuracy includes correcting openly. Quiet changes erode trust more than the error did."
            },
            {
              type: "categorize",
              q: "Sort each item as news or as PR.",
              buckets: [
                { id: "news", label: "News" },
                { id: "pr", label: "PR or promotion" }
              ],
              items: [
                { text: "A sourced report that a state firm's losses widened", bucket: "news" },
                { text: "We are excited to announce our visionary new app", bucket: "pr" },
                { text: "A factory cut 200 jobs, the company confirmed", bucket: "news" },
                { text: "Back our cause and join the movement today", bucket: "pr" },
                { text: "Figures drawn from the company's own filings", bucket: "news" }
              ],
              explain: "News reports what happened, with sources. PR praises or urges you to act."
            },
            {
              type: "mcq",
              q: "Which opening best fits the Mutapa Times voice?",
              options: [
                "Zimbabwe, a landlocked country in southern Africa, is a place where...",
                "Diaspora families face higher fees on the money they send home from next month",
                "For readers unfamiliar with Zimbabwe, some background first",
                "Experts say the African nation faces complex challenges"
              ],
              answer: 1,
              explain: "We write for Zimbabweans, leading with what affects the reader, not explaining the country to outsiders."
            },
            {
              type: "mcq",
              q: "A factory closure is disputed and you can reach managers but not the affected workers. The most responsible approach is to:",
              options: [
                "Run only the managers' version as settled fact",
                "Make clear what is claimed and by whom, and keep seeking other voices",
                "Invent worker quotes to balance it",
                "Drop the story entirely"
              ],
              answer: 1,
              explain: "Attribute claims, do not present one side as fact, and keep working to reach the people affected."
            },
            {
              type: "swipe",
              q: "News or PR?",
              leftLabel: "PR",
              rightLabel: "News",
              cards: [
                { text: "Inflation rose to 12 percent, official data shows.", side: "right" },
                { text: "We are honoured to be the region's leading, award-winning firm.", side: "left" },
                { text: "Two hospitals reported drug shortages this week.", side: "right" },
                { text: "Do not miss our game-changing launch event.", side: "left" }
              ],
              explain: "Sourced facts are news. Praise and calls to act are PR."
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
                "The news editor and, in broadcast, the assignment editor decide what gets covered today. The assignment editor watches incoming tips, tracks breaking news, vets sources and moves stories forward. Section or desk editors (Business, Metro, Sport) shape coverage in their area.",
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
            },
            {
              type: "match",
              q: "Match each newsroom role to what they do.",
              pairs: [
                { a: "Assignment editor", b: "Decides which stories get covered today" },
                { a: "Beat reporter", b: "Covers one subject area over time" },
                { a: "Sub-editor", b: "Checks and tightens copy before it runs" },
                { a: "Digital editor", b: "Publishes online and shapes homepage placement" }
              ],
              explain: "Each desk owns a different decision. Knowing who does what tells you who to pitch."
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
            },
            {
              type: "categorize",
              q: "Sort each outlet by who it mainly serves.",
              buckets: [
                { id: "broad", label: "Broad public" },
                { id: "niche", label: "Specialist or niche" }
              ],
              items: [
                { text: "Regional daily newspaper", bucket: "broad" },
                { text: "Local TV news", bucket: "broad" },
                { text: "Industry trade publication", bucket: "niche" },
                { text: "Neighbourhood community newsletter", bucket: "niche" },
                { text: "Business journal for executives", bucket: "niche" }
              ],
              explain: "Dailies and broadcast reach a broad public. Trade, business and community titles serve a defined niche."
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
        },
        {
          id: "cp-newsroom",
          title: "Inside the newsroom",
          checkpoint: true,
          minutes: 12,
          intro: "A checkpoint on how a newsroom works. You need 80% to pass.",
          cards: [
            {
              h: "Before you start",
              body: [
                "This covers newsroom roles, how a story moves, and reading an outlet.",
                "No teaching here, only questions. Below 80% means a review and a retry."
              ]
            }
          ],
          exercises: [
            {
              type: "match",
              q: "Match each role to what they do.",
              pairs: [
                { a: "Assignment editor", b: "Tracks tips and decides today's coverage" },
                { a: "Sub-editor", b: "Tightens and checks copy before it runs" },
                { a: "Producer", b: "Builds the running order and writes anchor scripts" },
                { a: "Managing editor", b: "Runs daily operations across the newsroom" }
              ],
              explain: "Each desk owns a different decision. The assignment editor is the daily gatekeeper; leadership runs the whole operation."
            },
            {
              type: "mcq",
              q: "You have an evergreen feature on a health issue for a daily paper. Best first contact?",
              options: ["The editor-in-chief", "The health beat reporter", "The advertising team", "The receptionist"],
              answer: 1,
              explain: "Pitch the person who owns that coverage day to day. For an evergreen story, go to the relevant beat reporter."
            },
            {
              type: "order",
              q: "Put a story's journey in order, from first to last.",
              items: [
                "Gathering: tips and reporters bring the news in",
                "Production: the desk checks, edits and shapes it",
                "Output: it is published online, on air or in print"
              ],
              explain: "Gather, then verify and edit in production, then publish."
            },
            {
              type: "categorize",
              q: "Sort each outlet by who it mainly serves.",
              buckets: [
                { id: "broad", label: "Broad public" },
                { id: "niche", label: "Specialist or niche" }
              ],
              items: [
                { text: "Regional daily newspaper", bucket: "broad" },
                { text: "Local TV news", bucket: "broad" },
                { text: "Industry trade publication", bucket: "niche" },
                { text: "Neighbourhood community newsletter", bucket: "niche" },
                { text: "Business journal for executives", bucket: "niche" }
              ],
              explain: "Dailies and broadcast reach a broad public; trade, business and community titles serve a defined niche."
            },
            {
              type: "mcq",
              q: "The production control room and master control room are unique to which kind of newsroom?",
              options: ["Print newspapers", "Broadcast television and radio", "Newsletters", "All newsrooms equally"],
              answer: 1,
              explain: "The PCR and MCR are specific to broadcast. Print and digital have no equivalent."
            },
            {
              type: "mcq",
              q: "What best defines a digital-first newsroom?",
              options: [
                "It works to one nightly deadline",
                "It publishes continuously and updates in real time",
                "It never checks facts",
                "It has no editors"
              ],
              answer: 1,
              explain: "Digital-first means continuous, real-time publishing rather than a single daily deadline."
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
            },
            {
              type: "match",
              q: "Match each funding model to its description.",
              pairs: [
                { a: "Advertising", b: "Companies pay to place ads; readers get it free" },
                { a: "Subscription", b: "Readers pay a recurring fee for access" },
                { a: "Public funding", b: "The state supports public-service media" },
                { a: "Nonprofit", b: "Foundations and donors fund the journalism" }
              ],
              explain: "Most newsrooms blend these, but each has a distinct source and a distinct pull on coverage."
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
                "Pay what you can: Daily Maverick lets readers choose a contribution on a sliding scale. Trust-based free access: Spain's elDiario.es added an I cannot pay option, on trust, without checking. Free for groups at risk of exclusion: a Swedish paper gave free subscriptions to young readers, and others have done the same for unemployed readers.",
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
        },
        {
          id: "cp-money",
          title: "How news makes money",
          checkpoint: true,
          minutes: 12,
          intro: "A checkpoint on the business of news. You need 80% to pass.",
          cards: [
            {
              h: "Before you start",
              body: [
                "This covers revenue models, the industry today, paywalls, inclusive models, and how funding shapes coverage.",
                "Questions only. Below 80% means a review and a retry."
              ]
            }
          ],
          exercises: [
            {
              type: "match",
              q: "Match each funding model to its description.",
              pairs: [
                { a: "Advertising", b: "Companies pay to place ads; readers get it free" },
                { a: "Subscription", b: "Readers pay a recurring fee for access" },
                { a: "Public funding", b: "The state supports public-service media" },
                { a: "Nonprofit", b: "Foundations and donors fund the journalism" }
              ],
              explain: "Most newsrooms blend these, but each has a distinct source and a distinct pull on coverage."
            },
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
              explain: "A metered paywall gives a free allowance, then prompts the reader to subscribe."
            },
            {
              type: "mcq",
              q: "A pay-what-you-can membership, like Daily Maverick's, means readers:",
              options: [
                "Must all pay the same high fee",
                "Choose how much to contribute, according to what they can afford",
                "Cannot read unless wealthy",
                "Pay only through advertising"
              ],
              answer: 1,
              explain: "Pay what you can keeps journalism open to all while still inviting support."
            },
            {
              type: "mcq",
              q: "In media literacy, 'follow the money' means:",
              options: [
                "Chase the highest salary",
                "Understand who funds an outlet, because funding shapes its journalism",
                "Only read paid content",
                "Ignore where news comes from"
              ],
              answer: 1,
              explain: "Knowing who pays helps you judge the influences on what gets covered and how."
            },
            {
              type: "multi",
              q: "Which trends are reshaping the newspaper business today? Select all.",
              options: [
                "Digital-first publishing",
                "Growth in reader revenue and subscriptions",
                "Rising print circulation everywhere",
                "Competition from social platforms and free online news"
              ],
              answers: [0, 1, 3],
              explain: "Digital-first, reader revenue and platform competition are rising. Print circulation is falling, not rising."
            },
            {
              type: "mcq",
              q: "What is the 'super-serving' concern with subscription models?",
              options: [
                "They give too much away free",
                "They risk serving mainly richer, more educated audiences and excluding others",
                "They make news too cheap",
                "They only work for sport"
              ],
              answer: 1,
              explain: "If only the well-off can pay, journalism risks reaching only them, which is bad for an informed public."
            }
          ]
        }
      ]
    },
    {
      id: "reporting-africa",
      title: "Reporting Africa, by Africans",
      summary: "How African media covers Africa, the stereotypes to avoid, and how to tell fuller, fairer stories of the continent.",
      lessons: [
        {
          id: "africa-narrative",
          title: "The story of Africa",
          minutes: 8,
          intro: "The frames a newsroom reaches for shape how readers see a whole continent. Learn to see them.",
          cards: [
            {
              h: "Frames shape how a continent is seen",
              body: [
                "Research into coverage of Africa finds the same frames repeating: poverty, poor leadership, corruption, conflict and disease. Together they paint Africa as broken, dependent and lacking agency, as if things only happen to Africans rather than being done by them.",
                "These frames have real consequences. They shape foreign investment, how the world treats the continent, and how young Africans see their own futures and whether to stay."
              ]
            },
            {
              h: "It is not only a Western problem",
              body: [
                "It would be easy to blame outside media alone. But studies of African outlets show the same stereotypes appear in coverage by Africans, for Africans. In one survey, half of the editors admitted there were stereotypes in the stories they ran.",
                "Most did not want to run them. The gap between the coverage they wanted and what they published came down mostly to resources, not intent."
              ]
            },
            {
              h: "Why the storyteller matters",
              body: [
                "Africans learn about themselves and their neighbours through the media. If African newsrooms repeat the broken-continent frame, they reinforce it for African readers, not just foreign ones.",
                "Telling fuller stories is not about pretending problems away. It is about restoring context, agency and the full range of African life."
              ]
            }
          ],
          exercises: [
            {
              type: "multi",
              q: "Which frames does research repeatedly find in coverage of Africa? Select all.",
              options: ["Poverty", "Corruption and poor leadership", "Conflict and disease", "Constant innovation and agency"],
              answers: [0, 1, 2],
              explain: "The recurring frames tie Africa to poverty, corruption, conflict and disease. Innovation and agency are exactly what tends to be missing."
            },
            {
              type: "mcq",
              q: "Why do negative frames about Africa matter beyond the page?",
              options: [
                "They do not matter at all",
                "They shape investment, how the world treats the continent, and how young Africans see their futures",
                "They only affect foreign readers",
                "They make stories longer"
              ],
              answer: 1,
              explain: "Frames have real-world effects on investment, migration and the opportunities young people believe they have."
            },
            {
              type: "mcq",
              q: "Are stereotypes about Africa found only in Western media?",
              options: [
                "Yes, African media never use them",
                "No, African media run them too, often due to resources rather than intent",
                "Only in broadcast",
                "Only in opinion pieces"
              ],
              answer: 1,
              explain: "Surveyed African editors acknowledged stereotypes in their own coverage. The cause was mostly a lack of resources, not a wish to stereotype."
            }
          ]
        },
        {
          id: "beyond-bleeds",
          title: "Beyond 'if it bleeds, it leads'",
          minutes: 8,
          intro: "Crisis is not the only story. Learn what African coverage over-tells, and what it leaves out.",
          cards: [
            {
              h: "Event-driven coverage",
              body: [
                "Much coverage of African countries clusters around a few dramatic events: crises, disasters and accidents, which editors often treat as more newsworthy. In one review, straight news made up about 80 percent of coverage, while in-depth features were under 10 percent.",
                "The result is a continent told through flashpoints, with little of the context that explains the why and the how."
              ]
            },
            {
              h: "The missing stories",
              body: [
                "Stories of African success, innovation and technology are almost absent. Mobile money, M-Pesa, transformed payments from Kenya years before similar services reached Europe. Ordinary people's voices are often missing, or used only to reinforce a negative frame.",
                "Telling these stories is not boosterism. It is filling in a picture that is currently half-drawn."
              ]
            },
            {
              h: "Solutions and agency",
              body: [
                "Solutions journalism reports not just the problem but how people are responding to it, and whether it works. Done well, it restores agency without ignoring hard truths.",
                "Ask of any story: who is acting here, and have I shown them, or only what was done to them?"
              ]
            }
          ],
          exercises: [
            {
              type: "mcq",
              q: "What kind of coverage dominates reporting on African countries?",
              options: [
                "In-depth features",
                "Event-driven hard news around crises and dramatic events",
                "Arts and culture",
                "Solutions journalism"
              ],
              answer: 1,
              explain: "Coverage clusters around dramatic events, with straight news far outweighing context-rich features."
            },
            {
              type: "mcq",
              q: "M-Pesa is an example of what kind of under-told African story?",
              options: [
                "A routine announcement",
                "A homegrown innovation that led the world",
                "A sports story",
                "A disaster story"
              ],
              answer: 1,
              explain: "Mobile money scaled in Kenya years before similar services reached richer markets. Innovation like this is routinely under-covered."
            },
            {
              type: "categorize",
              q: "Sort these story ideas by how the continent is usually covered.",
              buckets: [
                { id: "over", label: "Already over-covered" },
                { id: "under", label: "Under-covered" }
              ],
              items: [
                { text: "A dramatic accident", bucket: "over" },
                { text: "A sudden disaster", bucket: "over" },
                { text: "A mobile-money startup scaling up", bucket: "under" },
                { text: "A community solving a water shortage", bucket: "under" },
                { text: "Everyday life and ordinary voices", bucket: "under" }
              ],
              explain: "Dramatic events and crises are over-represented. Innovation, solutions and ordinary life are what tend to be missing."
            },
            {
              type: "mcq",
              q: "What does solutions journalism add to a story about a problem?",
              options: [
                "It hides the problem",
                "It reports how people are responding and whether it works",
                "It avoids all facts",
                "It only quotes officials"
              ],
              answer: 1,
              explain: "Solutions journalism keeps the problem in view but also shows the response and its results, restoring agency."
            }
          ]
        },
        {
          id: "sources-agenda",
          title: "Whose agenda? Sources and wires",
          minutes: 8,
          intro: "Who supplies and who is quoted in a story decides whose version of Africa readers get.",
          cards: [
            {
              h: "The wire problem",
              body: [
                "Facing tight budgets, many African outlets rely on Western agencies such as AFP, the BBC and Reuters for news about other African countries. In one review, agencies supplied close to half of all stories about African countries, and only about a fifth of those agency stories came from African agencies.",
                "When non-Africans supply most of the copy, non-Africans largely set the agenda and the framing, often for a Western audience."
              ]
            },
            {
              h: "Authorities over citizens",
              body: [
                "Coverage leans heavily on officials, spokespeople and observers. Ordinary citizens are often absent, or quoted only to reinforce a negative frame. Press releases published as-is are the least investment of all, and the most agenda-driven.",
                "A story told only through those in power is only half the story."
              ]
            },
            {
              h: "Build African sourcing",
              body: [
                "Use African correspondents and contacts, centre the people actually affected, and pool stories with other African newsrooms. African agencies and networks can supply copy framed for African readers.",
                "Whose phone you pick up to call decides whose Africa you publish."
              ]
            }
          ],
          exercises: [
            {
              type: "mcq",
              q: "Where does a large share of stories about African countries come from?",
              options: [
                "Mostly African agencies",
                "Mostly Western wire agencies such as AFP, BBC and Reuters",
                "Only citizen journalists",
                "Only company press offices"
              ],
              answer: 1,
              explain: "Reviews show agencies supply close to half of African-country stories, and only about a fifth of those are from African agencies."
            },
            {
              type: "mcq",
              q: "What is the main risk of relying on Western wires for African news?",
              options: [
                "Stories are too long",
                "Non-Africans set the agenda and framing, often for a Western audience",
                "Stories are always false",
                "There is no risk"
              ],
              answer: 1,
              explain: "Whoever supplies the copy shapes the agenda. Western framing often serves Western expectations of Africa."
            },
            {
              type: "multi",
              q: "Which are signs of low-investment, agenda-driven coverage? Select all.",
              options: [
                "Press releases published as-is",
                "Only officials quoted, no ordinary voices",
                "No context for the why and how",
                "Interviews with the people actually affected"
              ],
              answers: [0, 1, 2],
              explain: "Unedited releases, authority-only sourcing and missing context all signal low investment. Reaching affected people is the opposite."
            }
          ]
        },
        {
          id: "pan-african",
          title: "Pan-African reporting",
          minutes: 8,
          intro: "Most coverage fixes on a few countries. Learn to report the whole continent, in its full variety.",
          cards: [
            {
              h: "Cover the continent, not a caricature",
              body: [
                "Coverage concentrates on a handful of countries, often Nigeria and South Africa, while many countries barely feature at all. And beware the 'Africa is one country' trope: name the country, give its specific context, and show how places differ.",
                "Fifty-four countries cannot share one storyline."
              ]
            },
            {
              h: "Diversity of topics is the goal",
              body: [
                "In one study, the countries covered most fully, such as South Africa and Egypt, were those reported across many topics. Others appeared only around a single crisis or dramatic event, which distorts how readers see them.",
                "Aim to cover a country across business, culture, science, sport and ordinary life, not through one event."
              ]
            },
            {
              h: "Collaborate across borders",
              body: [
                "The fixes that practitioners suggest are practical: pool stories and multimedia between African newsrooms, build networks of editors and journalists, invest in coverage, and reward good journalism with African awards.",
                "Shared content means more countries get told, by people closer to them."
              ]
            }
          ],
          exercises: [
            {
              type: "mcq",
              q: "What is the 'Africa is one country' trope, and how do you avoid it?",
              options: [
                "Treating Africa as uniform; avoid it by naming the country and giving its specific context",
                "Covering too many countries; avoid it by covering fewer",
                "A type of headline; avoid it by using photos",
                "It is not a real problem"
              ],
              answer: 0,
              explain: "Flattening 54 countries into one story erases difference. Name the country and ground it in its own context."
            },
            {
              type: "mcq",
              q: "Which countries tend to dominate African coverage of Africa?",
              options: ["Lesotho and Eritrea", "Nigeria and South Africa", "Seychelles and Comoros", "None, coverage is even"],
              answer: 1,
              explain: "Coverage concentrates on a few large countries, often Nigeria and South Africa, while many others barely feature."
            },
            {
              type: "multi",
              q: "Which practical fixes did practitioners suggest for better pan-African coverage? Select all.",
              options: [
                "Pool stories and multimedia between newsrooms",
                "Build networks of editors and journalists",
                "Invest in original reporting",
                "Rely more heavily on Western wires"
              ],
              answers: [0, 1, 2],
              explain: "Pooling, networks and investment widen coverage. Leaning harder on Western wires is the problem, not the fix."
            },
            {
              type: "write",
              q: "Pitch the missing story.",
              brief: [
                "Pitch a story about an under-covered African country, or an under-covered angle (innovation, ordinary life, a solution), for a pan-African audience.",
                "Say what the story is, which country or region, why it matters, and why it counters the usual frame."
              ],
              checklist: [
                "Is it about a specific country or place, named and in context?",
                "Does it go beyond crisis and disaster?",
                "Does it centre people, not only authorities?",
                "Does it restore agency rather than reinforce a stereotype?"
              ],
              model: "Story: how a women-led cooperative in northern Zambia is using solar cold-storage to cut post-harvest losses. Where: Zambia, a country rarely covered beyond its own borders. Why it matters: post-harvest loss is a continent-wide problem, and here is a working response. Why it counters the frame: it centres the farmers solving it, shows African innovation and agency, and gives context rather than a snapshot of hardship.",
              exerciseId: "missing-story-1"
            }
          ]
        },
        {
          id: "cp-africa",
          title: "Reporting Africa",
          checkpoint: true,
          minutes: 12,
          intro: "A checkpoint on covering the continent. You need 80% to pass.",
          cards: [
            {
              h: "Before you start",
              body: [
                "This covers the frames and stereotypes, event-driven coverage, the wire problem, and pan-African reporting.",
                "Questions only. Below 80% means a review and a retry."
              ]
            }
          ],
          exercises: [
            {
              type: "multi",
              q: "Which frames does research repeatedly find in coverage of Africa? Select all.",
              options: ["Poverty", "Corruption and poor leadership", "Conflict and disease", "Constant innovation and agency"],
              answers: [0, 1, 2],
              explain: "The recurring frames tie Africa to poverty, corruption, conflict and disease. Innovation and agency are what go missing."
            },
            {
              type: "mcq",
              q: "In reviews of African coverage, where did the stories largely come from?",
              options: [
                "Almost none from agencies",
                "About half from agencies, and only about a fifth of those from African agencies",
                "All from African agencies",
                "Agencies are never used"
              ],
              answer: 1,
              explain: "Agencies supplied close to half of African-country stories, and only about a fifth of those were from African agencies, so non-Africans often set the agenda."
            },
            {
              type: "categorize",
              q: "Sort these story ideas by how the continent is usually covered.",
              buckets: [
                { id: "over", label: "Already over-covered" },
                { id: "under", label: "Under-covered" }
              ],
              items: [
                { text: "A dramatic accident", bucket: "over" },
                { text: "A sudden disaster", bucket: "over" },
                { text: "A homegrown tech innovation", bucket: "under" },
                { text: "A community solving a local problem", bucket: "under" },
                { text: "Everyday life and ordinary voices", bucket: "under" }
              ],
              explain: "Dramatic events and crises are over-represented. Innovation, solutions and ordinary life are what tend to be missing."
            },
            {
              type: "mcq",
              q: "How do you avoid the 'Africa is one country' trope?",
              options: [
                "Cover fewer countries",
                "Name the specific country and ground the story in its own context",
                "Use more photos",
                "Only write about the continent as a whole"
              ],
              answer: 1,
              explain: "Fifty-four countries cannot share one storyline. Name the country and give it specific context."
            },
            {
              type: "mcq",
              q: "Which kind of African story is most consistently missing from coverage?",
              options: [
                "Daily weather",
                "Sports results",
                "Innovation, success and ordinary voices",
                "Routine announcements"
              ],
              answer: 2,
              explain: "Success, innovation like M-Pesa, and the voices of ordinary people are the stories repeatedly left out."
            },
            {
              type: "mcq",
              q: "Which countries tend to dominate African coverage of Africa?",
              options: ["Lesotho and Eritrea", "Nigeria and South Africa", "Seychelles and Comoros", "Coverage is perfectly even"],
              answer: 1,
              explain: "Coverage concentrates on a few large countries, often Nigeria and South Africa, while many others barely feature."
            }
          ]
        }
      ]
    },
    {
      id: "africa-regions",
      title: "Africa region by region",
      summary: "A reporter's map of the continent: the five regions, their media hubs, languages and the bodies that shape the news.",
      lessons: [
        {
          id: "region-north",
          title: "North Africa",
          minutes: 6,
          intro: "From Egypt to Morocco: an Arabic-speaking region where broadcast and the state loom large.",
          cards: [
            {
              h: "The lay of the land",
              body: [
                "North Africa spans countries including Egypt, Libya, Tunisia, Algeria and Morocco. Arabic is the dominant language, French is widely used across the Maghreb, and Amazigh (Berber) languages are spoken too.",
                "The regional grouping for the Maghreb is the Arab Maghreb Union, though it has been largely inactive."
              ]
            },
            {
              h: "Media landscape",
              body: [
                "Egypt has one of the oldest press traditions on the continent, with titles like Al-Ahram. In some countries broadcast leads: in Tunisia, broadcast outlets are the most influential media.",
                "Press freedom varies sharply and can be tightly constrained, with real risks to journalists."
              ]
            }
          ],
          exercises: [
            {
              type: "mcq",
              q: "What is the dominant language of North African media, alongside French in the Maghreb?",
              options: ["Swahili", "Arabic", "Portuguese", "Amharic"],
              answer: 1,
              explain: "Arabic dominates, with French widely used across the Maghreb and Amazigh languages also spoken."
            },
            {
              type: "mcq",
              q: "In Tunisia, which kind of media is the most influential?",
              options: ["Print newspapers", "Broadcast", "Trade journals", "Newsletters"],
              answer: 1,
              explain: "Tunisia is a case where broadcast media, not print, leads in influence."
            },
            {
              type: "match",
              q: "Match each North African country to its capital.",
              pairs: [
                { a: "Egypt", b: "Cairo" },
                { a: "Tunisia", b: "Tunis" },
                { a: "Morocco", b: "Rabat" },
                { a: "Algeria", b: "Algiers" }
              ],
              explain: "Knowing the basics of a region, capitals included, is the groundwork of credible reporting."
            }
          ]
        },
        {
          id: "region-west",
          title: "West Africa",
          minutes: 6,
          intro: "Nigeria, Ghana, Senegal and more: a region split across English and French, anchored by ECOWAS.",
          cards: [
            {
              h: "The lay of the land",
              body: [
                "West Africa includes Nigeria, Ghana, Senegal and Côte d'Ivoire, split between Anglophone countries (such as Nigeria and Ghana) and Francophone ones (such as Senegal and Côte d'Ivoire). Many Francophone states share the CFA franc.",
                "The regional bloc is ECOWAS, the Economic Community of West African States."
              ]
            },
            {
              h: "Media landscape",
              body: [
                "Nigeria is the continent's most populous country and one of its biggest economies, with a large, combative press, titles like Premium Times, Punch and Vanguard, and Nollywood, a film industry of global scale. Lagos is a major media hub.",
                "Ghana and Senegal have strong press traditions of their own."
              ]
            }
          ],
          exercises: [
            {
              type: "mcq",
              q: "What is the main regional bloc of West Africa?",
              options: ["SADC", "EAC", "ECOWAS", "The Arab Maghreb Union"],
              answer: 2,
              explain: "ECOWAS, the Economic Community of West African States, is the region's main bloc."
            },
            {
              type: "categorize",
              q: "Sort these West African countries by their main official language.",
              buckets: [
                { id: "anglo", label: "Mainly English-speaking" },
                { id: "franco", label: "Mainly French-speaking" }
              ],
              items: [
                { text: "Nigeria", bucket: "anglo" },
                { text: "Ghana", bucket: "anglo" },
                { text: "Senegal", bucket: "franco" },
                { text: "Côte d'Ivoire", bucket: "franco" }
              ],
              explain: "Crossing the Anglophone and Francophone line is how a West African story reaches the whole region."
            },
            {
              type: "mcq",
              q: "Which West African country is the continent's most populous and home to Nollywood?",
              options: ["Ghana", "Senegal", "Nigeria", "Mali"],
              answer: 2,
              explain: "Nigeria is the most populous African country, one of its largest economies, and home to the Nollywood film industry."
            }
          ]
        },
        {
          id: "region-east",
          title: "East Africa",
          minutes: 6,
          intro: "Kenya, Tanzania, Ethiopia and more: Nairobi is a continental hub and Swahili a regional superpower.",
          cards: [
            {
              h: "The lay of the land",
              body: [
                "East Africa includes Kenya, Tanzania, Uganda, Rwanda and Ethiopia. Swahili is widely spoken across Kenya and Tanzania, Ethiopia uses Amharic, and Rwanda has Kinyarwanda. The regional bloc is the East African Community, the EAC.",
                "Swahili is a powerful tool for reaching audiences across borders."
              ]
            },
            {
              h: "Media landscape",
              body: [
                "Nairobi, in Kenya, is a major continental media hub, home to many correspondents and outlets like the Daily Nation and The Standard. Kenya also gave the world M-Pesa mobile money. Ethiopia has a large media scene, though press freedom there has been volatile.",
                "Kenyan media, like South African media, cover the rest of Africa more than most."
              ]
            }
          ],
          exercises: [
            {
              type: "mcq",
              q: "What is the regional bloc of East Africa?",
              options: ["The East African Community (EAC)", "ECOWAS", "ECCAS", "SADC"],
              answer: 0,
              explain: "The East African Community, the EAC, is the region's bloc."
            },
            {
              type: "mcq",
              q: "Which language is widely spoken across Kenya and Tanzania and useful for regional reach?",
              options: ["Amharic", "Swahili", "Portuguese", "Hausa"],
              answer: 1,
              explain: "Swahili is widely spoken across Kenya and Tanzania, making it a powerful cross-border tool."
            },
            {
              type: "match",
              q: "Match each East African country to a key fact.",
              pairs: [
                { a: "Kenya", b: "Home of M-Pesa mobile money" },
                { a: "Ethiopia", b: "Speaks Amharic" },
                { a: "Rwanda", b: "Speaks Kinyarwanda" },
                { a: "Tanzania", b: "Swahili widely spoken" }
              ],
              explain: "Each country has its own language and story. Lumping them together is exactly the trap to avoid."
            }
          ]
        },
        {
          id: "region-central",
          title: "Central Africa",
          minutes: 6,
          intro: "The DRC and its neighbours: a vast, French-speaking region, and the least covered of all.",
          cards: [
            {
              h: "The lay of the land",
              body: [
                "Central Africa includes the Democratic Republic of Congo, Cameroon, Chad, the Central African Republic, the Republic of Congo and Gabon. French is widely official, and the DRC also has Lingala, Swahili, Kikongo and Tshiluba. The regional bloc is ECCAS.",
                "The DRC is one of Africa's largest countries by both area and population."
              ]
            },
            {
              h: "The least-covered region",
              body: [
                "Central Africa is among the least covered regions in African media. In one continental review, it barely featured in regional coverage at all. Great distances and weak connectivity make reporting genuinely hard.",
                "That gap is also an opportunity: original reporting here is rare and valuable."
              ]
            }
          ],
          exercises: [
            {
              type: "mcq",
              q: "What is the regional bloc of Central Africa?",
              options: ["ECCAS", "ECOWAS", "EAC", "SADC"],
              answer: 0,
              explain: "ECCAS, the Economic Community of Central African States, is the region's bloc."
            },
            {
              type: "mcq",
              q: "Which language is widely official across much of Central Africa?",
              options: ["English", "French", "Portuguese", "Arabic"],
              answer: 1,
              explain: "French is widely official, alongside national languages such as Lingala and Swahili in the DRC."
            },
            {
              type: "mcq",
              q: "How well covered is Central Africa in African media?",
              options: [
                "The most covered region",
                "Among the least covered, barely featuring in regional coverage",
                "Covered only for sport",
                "Covered evenly with all regions"
              ],
              answer: 1,
              explain: "Central Africa is among the least covered regions, which makes original reporting there especially valuable."
            }
          ]
        },
        {
          id: "region-southern",
          title: "Southern Africa",
          minutes: 6,
          intro: "South Africa to Zimbabwe: the continent's largest media hub, and our own backyard.",
          cards: [
            {
              h: "The lay of the land",
              body: [
                "Southern Africa includes South Africa, Zimbabwe, Zambia, Botswana, Namibia and Mozambique. English is widely used in media across much of the region, alongside Portuguese in Mozambique and many indigenous languages. The regional bloc is SADC.",
                "Press freedom varies: Namibia ranks among the freest in the world, while others are more constrained."
              ]
            },
            {
              h: "Media landscape",
              body: [
                "South Africa, centred on Johannesburg, is the continent's largest media hub, with titles like Daily Maverick, Mail & Guardian and City Press, and the most diverse coverage in one continental review. South African media cover the rest of Africa relatively well.",
                "Smaller neighbours get less attention. The regional diaspora, including Zimbabweans across Southern Africa and beyond, is a rich, under-told beat, and the home patch of The Mutapa Times."
              ]
            }
          ],
          exercises: [
            {
              type: "mcq",
              q: "What is the regional bloc of Southern Africa?",
              options: ["SADC", "ECOWAS", "EAC", "ECCAS"],
              answer: 0,
              explain: "SADC, the Southern African Development Community, is the region's bloc."
            },
            {
              type: "mcq",
              q: "Which country ranks among the freest in the world for press freedom?",
              options: ["Eritrea", "Namibia", "Egypt", "Chad"],
              answer: 1,
              explain: "Namibia ranks among the freest in the world, a reminder that press freedom varies hugely across the continent."
            },
            {
              type: "match",
              q: "Match each Southern African country to a key fact.",
              pairs: [
                { a: "South Africa", b: "Largest media hub, centred on Johannesburg" },
                { a: "Mozambique", b: "Portuguese-speaking" },
                { a: "Zimbabwe", b: "Home patch of The Mutapa Times" },
                { a: "Namibia", b: "Among the world's freest press" }
              ],
              explain: "Even one region holds many languages, histories and media systems. Specifics beat generalisations."
            }
          ]
        },
        {
          id: "cp-regions",
          title: "Africa region by region",
          checkpoint: true,
          minutes: 10,
          intro: "A checkpoint on the continent's regions. You need 80% to pass. No explanations during the test.",
          cards: [
            { h: "Before you start", body: ["This covers the five regions, their languages, hubs and blocs.", "Questions only. Below 80% means a review and a retry."] }
          ],
          exercises: [
            {
              type: "match",
              q: "Match each region to its main bloc.",
              pairs: [
                { a: "West Africa", b: "ECOWAS" },
                { a: "East Africa", b: "EAC" },
                { a: "Central Africa", b: "ECCAS" },
                { a: "Southern Africa", b: "SADC" }
              ],
              explain: "Each region has its own economic community."
            },
            {
              type: "categorize",
              q: "Sort these West African countries by main official language.",
              buckets: [
                { id: "anglo", label: "Mainly English-speaking" },
                { id: "franco", label: "Mainly French-speaking" }
              ],
              items: [
                { text: "Nigeria", bucket: "anglo" },
                { text: "Ghana", bucket: "anglo" },
                { text: "Senegal", bucket: "franco" },
                { text: "Côte d'Ivoire", bucket: "franco" }
              ],
              explain: "West Africa splits between Anglophone and Francophone states."
            },
            {
              type: "mcq",
              q: "In which North African country is broadcast the most influential media?",
              options: ["Egypt", "Tunisia", "Morocco", "Algeria"],
              answer: 1,
              explain: "Tunisia is the case where broadcast, not print, leads."
            },
            {
              type: "mcq",
              q: "Which language is widely spoken across Kenya and Tanzania?",
              options: ["Amharic", "Swahili", "Portuguese", "Hausa"],
              answer: 1,
              explain: "Swahili is widely spoken in Kenya and Tanzania, useful for regional reach."
            },
            {
              type: "mcq",
              q: "Which region is the least covered in African media?",
              options: ["Southern Africa", "East Africa", "Central Africa", "West Africa"],
              answer: 2,
              explain: "Central Africa barely featured in regional coverage, which makes original reporting there valuable."
            },
            {
              type: "mcq",
              q: "Which country ranks among the freest in the world for press freedom?",
              options: ["Eritrea", "Namibia", "Egypt", "Chad"],
              answer: 1,
              explain: "Namibia ranks among the freest, a reminder that press freedom varies hugely."
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
              q: "A company's press office emails you a release announcing a success. What is it?",
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
        },
        {
          id: "cp-reporting",
          title: "Reporting",
          checkpoint: true,
          minutes: 10,
          intro: "A checkpoint on reporting. You need 80% to pass. No explanations during the test.",
          cards: [
            { h: "Before you start", body: ["This covers finding sources, the interview, verification and reporting from a distance.", "Questions only. Below 80% means a review and a retry."] }
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
              explain: "Research and prep first, so you can truly listen, then verify before you leave."
            },
            {
              type: "mcq",
              q: "A source says: you can use this, but do not name me. This is:",
              options: ["On the record", "On background", "A press release", "An opinion"],
              answer: 1,
              explain: "Background means use the information without naming the person."
            },
            {
              type: "mcq",
              q: "A company's press office emails a release announcing a success. It is:",
              options: [
                "A finished story",
                "A starting point that tells you what someone wants said",
                "Proof the claim is true",
                "An independent source"
              ],
              answer: 1,
              explain: "A release is a prompt to report, not the report itself."
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
            },
            {
              type: "mcq",
              q: "You report from abroad on an event you did not witness. How should you describe it?",
              options: [
                "As if you were there, for impact",
                "With clear attribution to people and footage you verified",
                "Without any sources",
                "As opinion"
              ],
              answer: 1,
              explain: "Attribute what you did not witness. Honesty about how you know is part of accuracy."
            },
            {
              type: "mcq",
              q: "A trusted contact gives you a figure with great confidence. You should:",
              options: [
                "Publish it, they are trusted",
                "Treat it as a claim and check it against another source",
                "Ignore it",
                "Publish it as opinion"
              ],
              answer: 1,
              explain: "Confidence is not evidence. Verify before it becomes a fact in print."
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
                "Facts: Zimbabwe's authorities have issued the country's first crypto rules. Firms that buy, sell or hold crypto must register yearly with the Financial Intelligence Unit and pay US$500. Operating without registering is now a criminal offence."
              ],
              checklist: [
                "Does it lead with the new rules, not the date or who issued them?",
                "Is it one clear sentence, roughly 35 words or fewer?",
                "Is it active voice and concrete?",
                "Is it accurate to the facts, inventing nothing?"
              ],
              model: "Zimbabwe will require every crypto business to register each year and pay US$500, or face criminal charges, under the country's first rules for the sector.",
              exerciseId: "lede-crypto-1"
            },
            {
              type: "swipe",
              q: "Strong lede or weak lede?",
              leftLabel: "Weak",
              rightLabel: "Strong",
              cards: [
                { text: "Zimbabwe will require crypto firms to register yearly or face criminal charges.", side: "right" },
                { text: "A meeting was held on Tuesday to discuss a number of important matters.", side: "left" },
                { text: "Diaspora families face higher fees to send money home from next month.", side: "right" },
                { text: "It should be noted that the committee, which met recently, reached decisions.", side: "left" },
                { text: "Power cuts will lengthen to 18 hours a day across Harare, the utility says.", side: "right" }
              ],
              explain: "Strong ledes lead with the news and who it affects. Weak ones bury it under process."
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
            },
            {
              type: "highlight",
              q: "Tap the clutter.",
              instruction: "Tap every word you could cut without losing the meaning.",
              tokens: ["It", "should", "be", "noted", "that", "the", "bank", "raised", "fees"],
              targets: [0, 1, 2, 3, 4],
              explain: "It should be noted that adds nothing. The bank raised fees says it all."
            },
            {
              type: "fillblank",
              q: "Complete the active, concrete sentence.",
              text: "The ___ raised ___ by US$500 a year.",
              bank: ["bank", "fees", "were", "prices"],
              answer: ["bank", "fees"],
              explain: "Active voice names who did what: the bank raised fees. Direct and concrete."
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
        },
        {
          id: "cp-writing",
          title: "Writing",
          checkpoint: true,
          minutes: 10,
          intro: "A checkpoint on writing. You need 80% to pass. No explanations during the test.",
          cards: [
            { h: "Before you start", body: ["This covers structure, the lede, clear writing and self-editing.", "Questions only. Below 80% means a review and a retry."] }
          ],
          exercises: [
            {
              type: "order",
              q: "Order a classic inverted-pyramid news story, top to bottom.",
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
              q: "Which is the stronger lede?",
              options: [
                "At a meeting held on Tuesday, a committee convened to discuss various matters",
                "Zimbabwe will require crypto firms to register yearly and pay US$500, or face charges"
              ],
              answer: 1,
              explain: "The second leads with the news and who it affects."
            },
            {
              type: "mcq",
              q: "Which sentence is clearer?",
              options: [
                "It should be noted that fees were raised by the bank at this point in time",
                "The bank raised fees"
              ],
              answer: 1,
              explain: "Active, concrete and free of filler."
            },
            {
              type: "multi",
              q: "Which phrases are clutter you can usually cut? Select all.",
              options: ["in order to", "US$500", "at this point in time", "it should be noted that"],
              answers: [0, 2, 3],
              explain: "Those three add words without meaning. A concrete figure is information."
            },
            {
              type: "highlight",
              q: "Tap the clutter.",
              instruction: "Tap every word you could cut without losing the meaning.",
              tokens: ["It", "should", "be", "noted", "that", "the", "bank", "raised", "fees"],
              targets: [0, 1, 2, 3, 4],
              explain: "It should be noted that adds nothing."
            },
            {
              type: "mcq",
              q: "The best first move when editing your own draft is to:",
              options: [
                "Add more adjectives",
                "Read it aloud, as if a stranger wrote it",
                "Make it longer",
                "Publish before you lose nerve"
              ],
              answer: 1,
              explain: "Distance and your ear catch what silent re-reading misses."
            }
          ]
        }
      ]
    },
    {
      id: "fact-copy",
      title: "Fact-checking and copy-editing",
      summary: "The last lines of defence before a reader sees your work: verify every claim, then catch every error.",
      lessons: [
        {
          id: "fact-checking",
          title: "Fact-checking",
          minutes: 8,
          intro: "Before a story runs, every claim, number, name and quote has to stand up. Practise checking them.",
          cards: [
            {
              h: "Every claim is a hypothesis",
              body: [
                "Until you have verified it, what you have is a claim, not a fact. Check it against documents, data and a second independent source. Confidence is not evidence: a source being sure does not make them right.",
                "The more surprising or convenient a claim, the harder you should check it."
              ]
            },
            {
              h: "Numbers, names and quotes",
              body: [
                "The three things readers trust most are the easiest to get wrong. Check every figure against its original source, spell every name correctly (people, places and organisations), and confirm every quote against your recording or notes.",
                "One wrong number or misspelt name can sink the credibility of an otherwise sound story."
              ]
            },
            {
              h: "Red flags",
              body: [
                "Slow down at a single anonymous source with no support, a screenshot with no clear origin, a statistic that seems too perfect, or a claim that confirms exactly what you already believed.",
                "When something is too good, too neat, or too on-the-nose, check it twice."
              ]
            }
          ],
          exercises: [
            {
              type: "mcq",
              q: "In fact-checking, how should you treat any claim until you confirm it?",
              options: [
                "As a fact, if the source sounds sure",
                "As a hypothesis, until verified against another source",
                "As an opinion",
                "As unusable"
              ],
              answer: 1,
              explain: "Treat every claim as a hypothesis. Confidence is not evidence, so verify before it becomes a fact in print."
            },
            {
              type: "multi",
              q: "Which of these are red flags that should make you check harder? Select all.",
              options: [
                "A single anonymous source with no support",
                "A screenshot with no clear origin",
                "A statistic that seems too perfect",
                "Two independent sources who agree"
              ],
              answers: [0, 1, 2],
              explain: "Lone anonymous tips, unsourced screenshots and too-perfect numbers are warning signs. Independent corroboration is reassurance, not a red flag."
            },
            {
              type: "match",
              q: "Match each thing you need to check to how you would verify it.",
              pairs: [
                { a: "A viral photo", b: "Reverse image search to see if it is current and real" },
                { a: "A surprising statistic", b: "Trace it to the original document or dataset" },
                { a: "A direct quote", b: "Check it against your recording or notes" },
                { a: "A person's job title", b: "Confirm it against the official record" }
              ],
              explain: "Each kind of claim has its own check. Matching the method to the claim is the craft of verification."
            },
            {
              type: "categorize",
              q: "Sort these sources by how much you can lean on them.",
              buckets: [
                { id: "strong", label: "Stronger starting point" },
                { id: "weak", label: "Weak: treat with caution" }
              ],
              items: [
                { text: "An official budget document you read", bucket: "strong" },
                { text: "A named expert speaking on the record", bucket: "strong" },
                { text: "An anonymous WhatsApp forward", bucket: "weak" },
                { text: "A random social-media post", bucket: "weak" },
                { text: "A press release making a claim", bucket: "weak" }
              ],
              explain: "Documents and named, on-record sources are stronger starting points. Anonymous forwards, random posts and press releases need hard verification."
            },
            {
              type: "swipe",
              q: "Verified, or still just a claim?",
              leftLabel: "Still a claim",
              rightLabel: "Verified",
              cards: [
                { text: "A figure you read directly in the audited financial report.", side: "right" },
                { text: "A WhatsApp message saying a company has collapsed.", side: "left" },
                { text: "Two independent sources confirm the same number.", side: "right" },
                { text: "A dramatic photo sent to you with no source.", side: "left" },
                { text: "A statistic a source recited confidently from memory.", side: "left" }
              ],
              explain: "Documents you have seen and independent corroboration are verified. A single message, an unsourced photo or a number from memory is still a claim."
            }
          ]
        },
        {
          id: "copy-checking",
          title: "Copy-editing",
          minutes: 8,
          intro: "The last check before a reader sees your work: catch the typo, the wrong word and the broken style.",
          cards: [
            {
              h: "Read like a stranger, and aloud",
              body: [
                "Your eye skips what your ear catches, so read your copy aloud as if someone else wrote it. Then check every name, number and date one more time.",
                "In journalism a typo is not a small thing. It undercuts the very accuracy you are selling."
              ]
            },
            {
              h: "The usual suspects",
              body: [
                "Watch spelling, homophones (their, there, they're; its, it's), stray or missing apostrophes, and capitalisation. Check consistency too: if one bullet ends with a full stop, they all should.",
                "Names are the classic trap. Check the spelling of every person, place and organisation."
              ]
            },
            {
              h: "Headlines and house style",
              body: [
                "A headline must be accurate first and catchy second. A headline that oversells the story is an error, even if every word is spelled right.",
                "Keep tense, spelling and number style consistent with your publication's house style."
              ]
            }
          ],
          exercises: [
            {
              type: "highlight",
              q: "Tap the errors.",
              instruction: "Tap each word that is misspelt or the wrong word.",
              tokens: ["The", "resturant", "said", "there", "new", "branch", "opens", "Monday"],
              targets: [1, 3],
              explain: "Resturant should be restaurant, and there should be their. Two small errors, both fatal to your credibility."
            },
            {
              type: "fillblank",
              q: "Choose the right words.",
              text: "They parked ___ car over ___ by the market.",
              bank: ["their", "there", "they're"],
              answer: ["their", "there"],
              explain: "Their shows possession (their car); there shows place (over there); they're means they are."
            },
            {
              type: "mcq",
              q: "Which sentence is clean, with no errors?",
              options: [
                "Its been a long year for the company.",
                "The company published its report on Friday.",
                "He recieved the award last night.",
                "Their going to announce it tomorrow."
              ],
              answer: 1,
              explain: "The others have errors: Its should be It's, recieved should be received, and Their should be They're."
            },
            {
              type: "multi",
              q: "Which errors appear in this sentence: \"its a big day and the company has published they're report\"? Select all.",
              options: [
                "its should be it's",
                "they're should be their",
                "big is misspelt",
                "report is misspelt"
              ],
              answers: [0, 1],
              explain: "Its should be it's (it is), and they're should be their (possessive). Big and report are spelt correctly."
            },
            {
              type: "swipe",
              q: "Clean, or does it contain an error?",
              leftLabel: "Has an error",
              rightLabel: "Clean",
              cards: [
                { text: "She received the award.", side: "right" },
                { text: "He recieved the award.", side: "left" },
                { text: "Their going to the launch.", side: "left" },
                { text: "The CEO's statement was clear.", side: "right" },
                { text: "Its been a long year.", side: "left" }
              ],
              explain: "Recieved, Their (for they're) and Its (for it's) are errors. Received and CEO's are correct."
            },
            {
              type: "mcq",
              q: "A bus company cut its fares by 10%. Which headline is accurate?",
              options: [
                "Bus firm slashes fares by 90%",
                "Bus firm cuts fares by 10%",
                "Bus firm scraps all fares for good",
                "Fares chaos as bus firm strikes again"
              ],
              answer: 1,
              explain: "Accuracy comes first. The others distort the number or sensationalise beyond what the facts support."
            }
          ]
        },
        {
          id: "cp-factcopy",
          title: "Fact-checking and copy",
          checkpoint: true,
          minutes: 12,
          intro: "A checkpoint on verification and clean copy. You need 80% to pass.",
          cards: [
            {
              h: "Before you start",
              body: [
                "This tests both skills together: verify the claim, then catch the error.",
                "Questions only. Below 80% means a review and a retry."
              ]
            }
          ],
          exercises: [
            {
              type: "highlight",
              q: "Tap the errors.",
              instruction: "Tap each word that is misspelt or the wrong word.",
              tokens: ["Yesterday", "the", "comapny", "announced", "there", "new", "product"],
              targets: [2, 4],
              explain: "Comapny should be company, and there should be their."
            },
            {
              type: "fillblank",
              q: "Choose the right words.",
              text: "___ been a hard year, and the company lost ___ funding.",
              bank: ["It's", "Its", "Their"],
              answer: ["It's", "Its"],
              explain: "It's means it has (It's been); its shows possession (its funding). Their is a distractor."
            },
            {
              type: "match",
              q: "Match each claim to how you would verify it.",
              pairs: [
                { a: "A viral photo", b: "Reverse image search" },
                { a: "A surprising statistic", b: "Trace it to the original dataset" },
                { a: "A direct quote", b: "Check it against your recording" },
                { a: "A person's job title", b: "Confirm it against the official record" }
              ],
              explain: "Each kind of claim has its own check. Match the method to the claim."
            },
            {
              type: "swipe",
              q: "Verified, or still just a claim?",
              leftLabel: "Still a claim",
              rightLabel: "Verified",
              cards: [
                { text: "A figure you read in the audited financial report.", side: "right" },
                { text: "A WhatsApp message saying a company has collapsed.", side: "left" },
                { text: "Two independent sources confirm the same number.", side: "right" },
                { text: "A statistic a source recited from memory.", side: "left" }
              ],
              explain: "Documents you have seen and independent corroboration are verified. A single message or a number from memory is still a claim."
            },
            {
              type: "mcq",
              q: "A company was cleared of one charge, but a second case continues. Which headline is accurate?",
              options: [
                "Company cleared of all charges",
                "Company cleared on one charge; second case continues",
                "Company walks free for good",
                "Case collapses entirely"
              ],
              answer: 1,
              explain: "Accuracy first. Only the second headline reflects what actually happened."
            },
            {
              type: "multi",
              q: "Which are red flags that should make you check harder? Select all.",
              options: [
                "A single anonymous source with no support",
                "A screenshot with no clear origin",
                "A statistic that seems too perfect",
                "Two independent sources who agree"
              ],
              answers: [0, 1, 2],
              explain: "Lone anonymous tips, unsourced screenshots and too-perfect numbers are warning signs. Independent corroboration is reassurance."
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
        },
        {
          id: "cp-pitch",
          title: "Pitch and publish",
          checkpoint: true,
          minutes: 10,
          intro: "A checkpoint on pitching and publishing. You need 80% to pass. No explanations during the test.",
          cards: [
            { h: "Before you start", body: ["This covers the pitch, taking edits, the pre-publication checklist and contributor life.", "Questions only. Below 80% means a review and a retry."] }
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
              explain: "Specific and newsy. The subject line is the lede of your pitch."
            },
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
            },
            {
              type: "mcq",
              q: "What does an editor value most in a contributor over time?",
              options: [
                "One brilliant piece, then silence",
                "Reliability: deadlines met, clean copy, pitched regularly",
                "The longest articles",
                "The most adjectives"
              ],
              answer: 1,
              explain: "Dependability builds a byline. A single clever line is soon forgotten."
            },
            {
              type: "multi",
              q: "A strong pitch answers which questions? Select all.",
              options: [
                "What the story is",
                "Why it matters now",
                "Why you are the one to write it",
                "How long you have been a reader"
              ],
              answers: [0, 1, 2],
              explain: "What, why now, and why you, plus why it fits this publication. Your reading history is not the point."
            }
          ]
        }
      ]
    },
    {
      id: "digital-journalist",
      title: "The digital journalist",
      summary: "Work across platforms, build a personal brand, and freelance with a portfolio that gets you hired.",
      lessons: [
        {
          id: "digital-age",
          title: "Journalism in the digital age",
          minutes: 7,
          intro: "Digital publishing changed how news is made and consumed. The modern journalist works across every platform.",
          cards: [
            {
              h: "Always on, every platform",
              body: [
                "Online news is continuous. Stories are sourced, written and published almost in real time, with live blogging for breaking events and new formats for analysis in progress. A journalist today is expected to move across print, broadcast and online rather than sticking to one.",
                "The skill is not just writing. It is choosing the right format, fast, for the story and the platform."
              ]
            },
            {
              h: "Open journalism and your audience",
              body: [
                "Social media means readers are now sources, contributors and a community, not just an audience. You can mine your readership for leads and case studies, and build a following around your work. User-generated content, from eyewitness photos to tips, can enrich a story.",
                "The rule is unchanged: verify it. A photo from social media is a claim until you confirm it."
              ]
            },
            {
              h: "Spotting fake news and infotainment",
              body: [
                "In an era of fake news and infotainment, part of the job is helping readers tell reliable journalism from noise. Public-service journalism informs and holds power to account. Infotainment entertains and chases clicks. The two can look alike at a glance.",
                "Speed is the digital advantage and the digital danger. The faster you can publish, the faster you can be wrong in public."
              ]
            }
          ],
          exercises: [
            {
              type: "mcq",
              q: "What does open journalism mean in a digital newsroom?",
              options: [
                "Publishing without any editing",
                "Using the online audience as a source of leads, case studies and community",
                "Making all content free",
                "Only using social media"
              ],
              answer: 1,
              explain: "Open journalism treats readers as contributors and sources, enriching reporting, while still verifying what they provide."
            },
            {
              type: "mcq",
              q: "A dramatic photo arrives via social media during a breaking story. What do you do first?",
              options: [
                "Publish it immediately for speed",
                "Verify it, since user content is a claim until confirmed",
                "Ignore all social media",
                "Assume it is fake and delete it"
              ],
              answer: 1,
              explain: "User-generated content can be gold, but it must be verified. Speed never overrides accuracy."
            },
            {
              type: "multi",
              q: "Which are real features of digital-age journalism? Select all.",
              options: [
                "Real-time, continuous publishing",
                "Working across print, broadcast and online",
                "A guarantee that nothing is ever wrong",
                "Readers acting as sources and community"
              ],
              answers: [0, 1, 3],
              explain: "Real-time, multi-platform and audience-as-source are all real. Speed raises the risk of error, it does not remove it."
            }
          ]
        },
        {
          id: "personal-brand",
          title: "Build your personal brand",
          minutes: 8,
          intro: "Editors now expect reporters to have a presence. Build one that is clear, consistent and genuinely you.",
          cards: [
            {
              h: "Clarity, consistency, constancy",
              body: [
                "Know your unique promise of value: what you cover and what makes you worth following. Keep your accounts consistent with one another, and post regularly. A reporter with a clear, steady presence is easier for an editor to picture in their newsroom.",
                "Be picky about what you share. Whatever you post online tends to stay there."
              ]
            },
            {
              h: "You are always broadcasting",
              body: [
                "Even a personal account is, to some extent, professional once you are a journalist. A useful filter is the 80/20 rule: roughly 80 percent professional content, 20 percent personal. And ask the hard question: if you saw your own profile, would you hire you?",
                "Mixing personal and professional is fine. Forgetting that it is all public is not."
              ]
            },
            {
              h: "Network, and be human",
              body: [
                "Do not only push out your own work. Follow people in your patch, comment, reply, and join the conversation. Inject real personality, readers connect with a person, not a hollow corporate voice. AI can help tidy a post, but do not let it write for you, as readers can usually tell.",
                "You cannot build connections by waiting for everyone to come to you."
              ]
            }
          ],
          exercises: [
            {
              type: "mcq",
              q: "What is the 80/20 rule for a journalist's social media?",
              options: [
                "Post 80 percent personal, 20 percent professional",
                "Post roughly 80 percent professional content and 20 percent personal",
                "Only post 20 percent of the time",
                "Spend 80 percent of your day online"
              ],
              answer: 1,
              explain: "Lead with professional content, leavened with some personality. It keeps your presence useful and human."
            },
            {
              type: "mcq",
              q: "Why treat even a personal post as broadcasting?",
              options: [
                "Because it is private",
                "Because as a journalist anything you post is public and reflects on you professionally",
                "Because nobody reads it",
                "Because it boosts ad revenue"
              ],
              answer: 1,
              explain: "Once you are a journalist, the personal is another branch of the professional. Post accordingly."
            },
            {
              type: "mcq",
              q: "After finishing this course, what should you add to the Education or Certifications part of your LinkedIn?",
              options: [
                "Nothing, online courses do not count",
                "The Mutapa Times Academy",
                "Only your university",
                "A list of hobbies"
              ],
              answer: 1,
              explain: "List The Mutapa Times Academy. It shows initiative and signals your focus on Zimbabwe and diaspora reporting."
            },
            {
              type: "write",
              q: "Set up your LinkedIn profile.",
              brief: [
                "Draft the key parts of a LinkedIn profile that positions you as a journalist.",
                "Write three things: a one-line headline, a two to three sentence About summary, and your Education entry, which should include The Mutapa Times Academy."
              ],
              checklist: [
                "Does your headline say what you cover, not just aspiring journalist?",
                "Does the About summary show your niche and point to a portfolio?",
                "Have you listed The Mutapa Times Academy under Education or Licenses and certifications?",
                "Is it consistent with how you present yourself elsewhere online?"
              ],
              model: "Headline: Multimedia journalist covering Zimbabwe and the diaspora, with a focus on money and migration. About: I report on the economics of diaspora life, from remittances to small business, for a Zimbabwean audience rather than for outsiders. I recently completed the Mutapa Times Academy. Portfolio at the link below, and open to freelance commissions. Education: The Mutapa Times Academy, journalism foundations and reporting.",
              exerciseId: "linkedin-1"
            }
          ]
        },
        {
          id: "freelance-portfolio",
          title: "Freelance and your portfolio",
          minutes: 7,
          intro: "Freelancing is a growing route in. Your portfolio, not your CV alone, is what wins the work.",
          cards: [
            {
              h: "What freelancing is",
              body: [
                "A freelance journalist is self-employed, taking on commissions for different outlets by the piece, the hour or the word. You might pitch an idea, be handed an assignment, or earn regular work once an editor trusts you. The independence is the appeal and the challenge.",
                "Platforms like Medium and Substack have given independent reporters more room than ever to build an audience directly."
              ]
            },
            {
              h: "Build a portfolio that sells you",
              body: [
                "Collect your best and most varied work in one place a commissioner can reach in a click. Show range: news, features, multimedia, a series. You do not need to have been professionally published. Reporting something and publishing it yourself shows initiative and resourcefulness.",
                "A live portfolio link beats any list of claimed skills."
              ]
            },
            {
              h: "The skills that keep work coming",
              body: [
                "Courage and curiosity to chase the story, clear writing, and journalistic integrity. On top of those, reliability: hitting deadlines and filing clean copy. Editors rehire the freelancer who makes their life easy.",
                "Relationships with editors, built over time, turn one commission into a steady flow."
              ]
            }
          ],
          exercises: [
            {
              type: "mcq",
              q: "Do you need to have been professionally published to build a journalism portfolio?",
              options: [
                "Yes, only paid, published work counts",
                "No, reporting and self-publishing your own work shows initiative",
                "Only if you have a degree",
                "Portfolios are not used for freelancers"
              ],
              answer: 1,
              explain: "Self-published, self-initiated work demonstrates exactly the resourcefulness commissioners look for."
            },
            {
              type: "mcq",
              q: "What most reliably turns a one-off commission into regular freelance work?",
              options: [
                "Filing late but brilliantly",
                "Reliability and a good relationship with the editor",
                "Pitching only once a year",
                "Refusing edits"
              ],
              answer: 1,
              explain: "Editors rehire dependable writers who file clean copy on time. Relationships compound."
            },
            {
              type: "multi",
              q: "Which belong in a strong freelance portfolio? Select all.",
              options: [
                "Your best and most varied pieces",
                "A clear, clickable link a commissioner can open",
                "Every rough draft you have ever written",
                "Self-published work that shows initiative"
              ],
              answers: [0, 1, 3],
              explain: "Curate the best and most varied, make it easy to reach, and include self-started work. Do not dump every draft."
            }
          ]
        },
        {
          id: "cp-digital",
          title: "The digital journalist",
          checkpoint: true,
          minutes: 10,
          intro: "A checkpoint on digital skills. You need 80% to pass. No explanations during the test.",
          cards: [
            { h: "Before you start", body: ["This covers digital-age journalism, personal brand and freelancing.", "Questions only. Below 80% means a review and a retry."] }
          ],
          exercises: [
            {
              type: "mcq",
              q: "What does open journalism mean in a digital newsroom?",
              options: [
                "Publishing without editing",
                "Using the online audience as a source of leads, case studies and community",
                "Making all content free",
                "Only using social media"
              ],
              answer: 1,
              explain: "Open journalism treats readers as contributors and sources, while still verifying what they provide."
            },
            {
              type: "mcq",
              q: "What is the 80/20 rule for a journalist's social media?",
              options: [
                "80 percent personal, 20 percent professional",
                "Roughly 80 percent professional content, 20 percent personal",
                "Post only 20 percent of the time",
                "Spend 80 percent of the day online"
              ],
              answer: 1,
              explain: "Lead with professional content, leavened with some personality."
            },
            {
              type: "mcq",
              q: "After finishing this course, what should you add to your LinkedIn Education?",
              options: ["Nothing", "The Mutapa Times Academy", "Only your university", "A list of hobbies"],
              answer: 1,
              explain: "List The Mutapa Times Academy. It shows initiative and signals your focus."
            },
            {
              type: "mcq",
              q: "Do you need to have been professionally published to build a portfolio?",
              options: [
                "Yes, only published work counts",
                "No, reporting and self-publishing shows initiative",
                "Only with a degree",
                "Portfolios are not used"
              ],
              answer: 1,
              explain: "Self-started, self-published work demonstrates resourcefulness."
            },
            {
              type: "mcq",
              q: "What most reliably turns a one-off commission into regular freelance work?",
              options: [
                "Filing late but brilliantly",
                "Reliability and a good relationship with the editor",
                "Pitching once a year",
                "Refusing edits"
              ],
              answer: 1,
              explain: "Editors rehire dependable writers who file clean copy on time."
            },
            {
              type: "multi",
              q: "Which belong in a strong freelance portfolio? Select all.",
              options: [
                "Your best and most varied pieces",
                "A clear, clickable link",
                "Every rough draft you have written",
                "Self-published work that shows initiative"
              ],
              answers: [0, 1, 3],
              explain: "Curate the best, make it easy to reach, include self-started work. Do not dump every draft."
            }
          ]
        }
      ]
    },
    {
      id: "getting-hired",
      title: "Getting hired",
      summary: "Build a CV and cover letter that get a journalist noticed, and avoid the mistakes that get applications binned.",
      lessons: [
        {
          id: "journalism-cv",
          title: "Your journalism CV",
          minutes: 8,
          intro: "Your CV is your pitch. It has to show, fast, that you have a journalist's skills and instincts.",
          cards: [
            {
              h: "What a journalism CV must contain",
              body: [
                "Your name and contact details with a link to your portfolio. A short personal statement: your pitch in one paragraph. A tailored list of key skills. Your experience in reverse chronological order, with the results you achieved, not just duties. Then education, and any awards.",
                "Keep it to one or two pages. Editors skim, so put the most important things on the first page."
              ]
            },
            {
              h: "Show, do not tell",
              body: [
                "Do not just list reporting and writing. In journalism those are assumed. Show range and impact instead: the kinds of stories you covered, the exclusives you broke, the numbers you moved. Grew site traffic by 30 percent lands harder than improved engagement.",
                "Be specific. Instead of works to deadlines, write produced a weekly feature series, coordinating interviews and edits to meet a strict schedule."
              ]
            },
            {
              h: "Tailor it, and lead with your niche",
              body: [
                "One CV does not fit every job. Keep a master copy with everything, then build a job-specific version that mirrors the language of each advert and foregrounds the most relevant work. Highlight your specialism, whether that is courts, business, data or video, so you stand out.",
                "An editor should see in seconds why you fit this role, not journalism in general."
              ]
            }
          ],
          exercises: [
            {
              type: "mcq",
              q: "What should always sit near the top of a journalist's CV alongside contact details?",
              options: [
                "Your school exam grades",
                "A link to your portfolio of work",
                "A list of hobbies",
                "Your date of birth"
              ],
              answer: 1,
              explain: "Editors want to see your work. A portfolio link is essential and belongs where it is easy to find."
            },
            {
              type: "mcq",
              q: "What is a sensible maximum length for a CV?",
              options: ["Half a page", "One or two pages", "Five pages", "As long as possible"],
              answer: 1,
              explain: "One to two pages. Editors skim, so keep it tight and put the strongest material first."
            },
            {
              type: "mcq",
              q: "Which bullet point is strongest on a journalism CV?",
              options: [
                "Responsible for writing and reporting",
                "Good at working to deadlines",
                "Broke a story on unreported campus assaults that led to new safety measures",
                "Did various tasks at the newspaper"
              ],
              answer: 2,
              explain: "Show, do not tell. A specific, high-impact achievement beats vague duties every time."
            },
            {
              type: "multi",
              q: "Which belong on a journalism CV? Select all.",
              options: [
                "A one-paragraph personal statement",
                "A tailored list of key skills",
                "Experience with the results you achieved",
                "A long unfocused list of every task you have ever done"
              ],
              answers: [0, 1, 2],
              explain: "Statement, tailored skills and achievement-led experience all belong. A laundry list of tasks does not."
            },
            {
              type: "mcq",
              q: "Why tailor your CV to each job?",
              options: [
                "To make it longer",
                "So the editor sees quickly why you fit that specific role",
                "Because it is required by law",
                "To hide your experience"
              ],
              answer: 1,
              explain: "A targeted CV mirrors the advert and foregrounds the most relevant work, so your fit is obvious fast."
            }
          ]
        },
        {
          id: "cover-letter",
          title: "The cover letter",
          minutes: 7,
          intro: "The cover letter expands your CV and proves you can write snappy, persuasive copy. Make it count.",
          cards: [
            {
              h: "What the cover letter does",
              body: [
                "It introduces you and the role you want, highlights your most relevant experience and skills, and explains why you fit this newsroom specifically. It is also a live sample of your writing, so it must be sharp. Around 300 to 400 words is plenty.",
                "Lead with who you are and what you cover, then build the case. No waffle: editors have no time for it."
              ]
            },
            {
              h: "Show you have done your homework",
              body: [
                "The strongest letters prove you actually read the publication. Refer to a recent piece or strand of coverage and say why it caught your eye, then connect it to the work you want to do. That is why them, not just why you.",
                "Close with confidence: a polite, direct request for an interview or a conversation."
              ]
            }
          ],
          exercises: [
            {
              type: "mcq",
              q: "Roughly how long should a journalism cover letter be?",
              options: ["Two or three pages", "Around 300 to 400 words", "A single sentence", "There is no limit"],
              answer: 1,
              explain: "Around 300 to 400 words. Tight and persuasive. You can expand in the interview."
            },
            {
              type: "mcq",
              q: "What is the strongest way to show you fit a particular newsroom?",
              options: [
                "Say you are passionate and hard working",
                "Reference a recent piece they ran and connect it to the work you want to do",
                "List every job you have ever had",
                "Use a flashy design"
              ],
              answer: 1,
              explain: "Referencing their actual work proves you did your homework and shows genuine, specific interest."
            },
            {
              type: "mcq",
              q: "How should a cover letter end?",
              options: [
                "By apologising for taking their time",
                "With a confident, polite request for an interview",
                "With no sign-off at all",
                "By repeating your whole CV"
              ],
              answer: 1,
              explain: "Close with confidence and a clear call to action. You are asking for a conversation, so ask."
            },
            {
              type: "write",
              q: "Write your cover-letter opening.",
              brief: [
                "Write the first three or four sentences of a cover letter applying to write for The Mutapa Times.",
                "Say who you are and what you cover, reference what draws you to this newsroom specifically, and keep it sharp."
              ],
              checklist: [
                "Does the first line say who you are and what you cover?",
                "Does it name something specific about The Mutapa Times, not generic flattery?",
                "Is the writing tight, with no waffle?",
                "Would an editor want to read the next paragraph?"
              ],
              model: "I am a reporter covering the economics of diaspora life, with bylines on remittances and small-business migration. What draws me to The Mutapa Times is that you report Zimbabwe for Zimbabweans rather than explaining it to outsiders, and your recent coverage of crypto registration rules is exactly the kind of money story I want to dig into. I would bring sourced, on-the-ground reporting and a steady diaspora-money beat.",
              exerciseId: "cover-letter-1"
            }
          ]
        },
        {
          id: "cv-mistakes",
          title: "Common CV mistakes",
          minutes: 7,
          intro: "Most applications fall down on the same handful of errors. Learn to avoid them.",
          cards: [
            {
              h: "Skills, not just activities",
              body: [
                "Do not only say what you did in past jobs. Say what skills it built. Bar work means dealing with the public, building rapport fast and handling conflict. Work with money means numeracy and data. Repetitive work means patience and persistence. All of it transfers.",
                "Every job also gives you insight into a part of society a newsroom may not know. That has value."
              ]
            },
            {
              h: "Typos are fatal in journalism",
              body: [
                "Spelling and grammar errors are not minor here. Some editors bin applications for a single typo, because attention to detail is the job. Check every name, of people, places and organisations. Watch homophones, apostrophes, and consistent style in your bullet points.",
                "Proofread it, then have someone else proofread it. A flawless application is itself a writing sample."
              ]
            },
            {
              h: "Do not undersell yourself",
              body: [
                "Do not reduce a degree to two lines. Give a paragraph on what you actually learned and did: the student paper, media law, an investigation, research skills. And do not hide personal experience. Caring for family, being first to university, or coming from a community a newsroom does not represent are all real value.",
                "Always link to your work. You do not need to be published to have a portfolio. Self-publishing shows initiative."
              ]
            }
          ],
          exercises: [
            {
              type: "mcq",
              q: "How should you present a non-journalism job, like bar work, on a journalism CV?",
              options: [
                "Leave it off entirely",
                "List only the tasks, like serving drinks",
                "Highlight the transferable skills it built, like handling the public and conflict",
                "Pretend it was a reporting job"
              ],
              answer: 2,
              explain: "Focus on transferable skills. Dealing with people, pressure and money all matter to a journalist."
            },
            {
              type: "mcq",
              q: "Why are typos especially damaging on a journalism application?",
              options: [
                "They are not, editors ignore them",
                "Because attention to detail is the job, so errors undercut your core claim",
                "Because they make the CV longer",
                "Only broadcast editors care"
              ],
              answer: 1,
              explain: "Accuracy is the craft. A typo-riddled application contradicts the very skill you are selling."
            },
            {
              type: "multi",
              q: "Which of these are common CV mistakes to avoid? Select all.",
              options: [
                "Listing tasks instead of the skills you built",
                "Generic cliches like hard working team player",
                "Quantifying your achievements with real numbers",
                "Reducing a three-year degree to two bare lines"
              ],
              answers: [0, 1, 3],
              explain: "Tasks-not-skills, cliches and underselling your education are all mistakes. Quantifying achievements is good practice."
            },
            {
              type: "mcq",
              q: "Do you need to have been professionally published to build a portfolio?",
              options: [
                "Yes, only published work counts",
                "No, you can report and self-publish your own work to show initiative",
                "Only if you have a degree",
                "Portfolios are not used in journalism"
              ],
              answer: 1,
              explain: "Reporting independently and publishing it yourself shows initiative and gives editors real work to judge."
            }
          ]
        },
        {
          id: "cp-hired",
          title: "Getting hired",
          checkpoint: true,
          minutes: 10,
          intro: "A checkpoint on CVs and cover letters. You need 80% to pass. No explanations during the test.",
          cards: [
            { h: "Before you start", body: ["This covers the journalism CV, the cover letter and common mistakes.", "Questions only. Below 80% means a review and a retry."] }
          ],
          exercises: [
            {
              type: "mcq",
              q: "Which bullet point is strongest on a journalism CV?",
              options: [
                "Responsible for writing and reporting",
                "Good at working to deadlines",
                "Broke a story on unreported campus assaults that led to new safety measures",
                "Did various tasks at the newspaper"
              ],
              answer: 2,
              explain: "Show, do not tell. A specific, high-impact achievement beats vague duties."
            },
            {
              type: "mcq",
              q: "A sensible maximum length for a CV is:",
              options: ["Half a page", "One or two pages", "Five pages", "As long as possible"],
              answer: 1,
              explain: "One to two pages, strongest material first."
            },
            {
              type: "mcq",
              q: "The strongest way to show you fit a particular newsroom in a cover letter is to:",
              options: [
                "Say you are passionate and hard working",
                "Reference a recent piece they ran and connect it to the work you want to do",
                "List every job you have had",
                "Use a flashy design"
              ],
              answer: 1,
              explain: "Referencing their actual work proves you did your homework."
            },
            {
              type: "mcq",
              q: "Why are typos especially damaging on a journalism application?",
              options: [
                "They are not, editors ignore them",
                "Because attention to detail is the job, so errors undercut your core claim",
                "Because they make the CV longer",
                "Only broadcast editors care"
              ],
              answer: 1,
              explain: "A typo-riddled application contradicts the very skill you are selling."
            },
            {
              type: "multi",
              q: "Which are common CV mistakes to avoid? Select all.",
              options: [
                "Listing tasks instead of the skills you built",
                "Generic cliches like hard-working team player",
                "Quantifying achievements with real numbers",
                "Reducing a three-year degree to two bare lines"
              ],
              answers: [0, 1, 3],
              explain: "Tasks-not-skills, cliches and underselling your education are mistakes. Quantifying is good practice."
            },
            {
              type: "mcq",
              q: "How should you present a non-journalism job, like bar work, on a journalism CV?",
              options: [
                "Leave it off",
                "List only the tasks",
                "Highlight the transferable skills it built, like handling the public and conflict",
                "Pretend it was a reporting job"
              ],
              answer: 2,
              explain: "Focus on transferable skills. Dealing with people, pressure and money all matter."
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
    },
    {
      id: "final",
      title: "Final assessment",
      summary: "One comprehensive exam across the whole course. Pass it to earn your certificate.",
      lessons: [
        {
          id: "final-exam",
          title: "Final exam",
          checkpoint: true,
          minutes: 20,
          intro: "The final exam, drawing on the whole course. You need 80% to pass. No explanations during the test.",
          cards: [
            {
              h: "Before you start",
              body: [
                "This pulls together everything: foundations, the newsroom, the business of news, reporting Africa, the craft, fact-checking and copy, and getting your work out.",
                "There is no teaching here. Take your time, and if you do not reach 80%, review the units and sit it again."
              ]
            }
          ],
          exercises: [
            {
              type: "mcq",
              q: "A company statement calls its new app \"the most secure in Africa.\" The most defensible way to use this is to:",
              options: [
                "Report it as fact, the company would not lie",
                "Attribute it as the company's claim and seek independent verification",
                "Rewrite it in your own words as praise",
                "Ignore the story entirely"
              ],
              answer: 1,
              explain: "An unverified superlative is a claim, not a fact. Attribute it and check it."
            },
            {
              type: "mcq",
              q: "A health ministry reports a measles outbreak of 200 cases. Which is the strongest lede?",
              options: [
                "The health ministry held a press conference on Tuesday morning.",
                "A measles outbreak has infected 200 people, the health ministry says, as clinics scramble to cope.",
                "Health, an ever-important issue, is back in the news this week.",
                "Officials gathered to discuss a range of health matters."
              ],
              answer: 1,
              explain: "Lead with the news and its human impact, attributed, not the process or vague throat-clearing."
            },
            {
              type: "mcq",
              q: "Two contacts give you the same striking figure. It counts as verified only if they:",
              options: [
                "Both read it in the same company statement",
                "Are independent of each other and of the original source",
                "Are both senior people",
                "Both sound very certain"
              ],
              answer: 1,
              explain: "Two people repeating one source is still one source. Independence is what verifies."
            },
            {
              type: "multi",
              q: "Which of these are red flags in a tip? Select all.",
              options: [
                "A single anonymous source with no support",
                "A screenshot with no clear origin",
                "A statistic that seems too perfect",
                "Two independent sources who agree"
              ],
              answers: [0, 1, 2],
              explain: "Lone anonymous tips, unsourced screenshots and too-perfect numbers warrant caution. Independent agreement is reassurance."
            },
            {
              type: "mcq",
              q: "A leaked file names a junior whistleblower who would be endangered if identified. You should:",
              options: [
                "Name them, accuracy means full detail",
                "Report the substance and withhold the non-essential identifying detail",
                "Drop the story to be safe",
                "Name them with a disclaimer"
              ],
              answer: 1,
              explain: "Minimise harm without losing the public-interest story."
            },
            {
              type: "mcq",
              q: "Which sentence is correct?",
              options: [
                "The board, who's members met today, approved it's budget.",
                "The board, whose members met today, approved its budget.",
                "The board, whose members met today, approved it's budget.",
                "The board, who's members met today, approved its budget."
              ],
              answer: 1,
              explain: "Whose shows possession; who's means who is. Its with no apostrophe is the possessive."
            },
            {
              type: "highlight",
              q: "Tap the errors.",
              instruction: "Tap each word that is misspelt or the wrong word.",
              tokens: ["The", "resturant", "said", "there", "prices", "had", "risen"],
              targets: [1, 3],
              explain: "Resturant should be restaurant, and there should be their."
            },
            {
              type: "fillblank",
              q: "Choose the right words.",
              text: "___ been a hard year, and the team lost ___ funding.",
              bank: ["It's", "Its", "Their"],
              answer: ["It's", "Its"],
              explain: "It's means it has; its shows possession."
            },
            {
              type: "mcq",
              q: "A feature headlined \"Doing business in Africa\" draws every example from a single city. The main flaw is that it:",
              options: [
                "Is too detailed",
                "Treats a whole continent as interchangeable, erasing huge differences",
                "Mentions business at all",
                "Is too short"
              ],
              answer: 1,
              explain: "The 'Africa is one country' trope. Name the place and give it context."
            },
            {
              type: "mcq",
              q: "An outlet publishes a mining company's press release almost word for word as news. The core problem is that it:",
              options: [
                "Is shorter than usual",
                "Lets an interested party set the agenda, unchecked and without context",
                "Used a press release, which is banned",
                "Should have been an opinion piece"
              ],
              answer: 1,
              explain: "Repeating one side unchecked hands them the agenda."
            },
            {
              type: "multi",
              q: "Which genuinely help reader-funded journalism sustain itself? Select all.",
              options: [
                "Distinctive reporting readers will pay for",
                "Loyal subscribers who renew over time",
                "Trust built through accuracy and consistency",
                "Filling the site with free wire copy"
              ],
              answers: [0, 1, 2],
              explain: "Distinctive, trusted work that earns loyal subscribers sustains reader revenue. Cheap filler does not."
            },
            {
              type: "order",
              q: "Order a news story, top to bottom.",
              items: [
                "The most important news: what happened and who it affects",
                "Key supporting facts and context",
                "A telling quote",
                "Background and minor detail"
              ],
              explain: "Most important first. A reader who stops early still has the heart of the story."
            }
          ]
        },
        {
          id: "capstone-press-release",
          title: "Capstone: from press release to published story",
          minutes: 25,
          intro: "Put it all into practice. A company has sent a press release. Take it from your inbox to a published story, the right way.",
          cards: [
            {
              h: "The brief",
              body: [
                "A press release has landed from Savanna Solar, a clean-energy company in Kenya. (It is a made-up company, for this exercise.)",
                "Read it, then work through the steps: judge it, structure the article, plan the newsroom roll-out, pitch it, and work out how it pays. Minimal writing, but you will show you understand the whole process."
              ]
            },
            {
              h: "The press release",
              body: [
                "FOR IMMEDIATE RELEASE. Savanna Solar, the leading and most innovative clean-energy company in East Africa, is proud to announce a game-changing 50 megawatt solar plant near Nakuru. The world-class project will transform the region and create thousands of jobs. Construction begins next month, backed by a US$80 million investment from international partners. CEO Aisha Mwangi said: We are thrilled to lead Africa into a brighter future.",
                "What the release does not say: how many jobs are permanent, where the US$80 million comes from, what happens to the land, or whether the local grid can take the power."
              ]
            }
          ],
          exercises: [
            {
              type: "highlight",
              q: "Tap the spin.",
              instruction: "Tap the self-praising words a reporter should not repeat as fact.",
              tokens: ["Savanna", "Solar", "the", "leading", "and", "most", "innovative", "clean-energy", "company", "is", "proud", "to", "announce", "a", "game-changing", "plant"],
              targets: [3, 6, 10, 14],
              explain: "Leading, innovative, proud and game-changing are the company praising itself. Strip them and report what is verifiable."
            },
            {
              type: "mcq",
              q: "What is the right journalistic approach to this release?",
              options: [
                "Publish it as a story, lightly reworded",
                "Verify the claims, find what is genuinely newsworthy, and seek independent voices",
                "Run it as an opinion column",
                "Ignore it, company news is never relevant"
              ],
              answer: 1,
              explain: "A release is a tip, not a story. Verify, contextualise, and talk to people beyond the company."
            },
            {
              type: "categorize",
              q: "Sort the release's statements.",
              buckets: [
                { id: "report", label: "Report (after checking)" },
                { id: "drop", label: "Drop or attribute as spin" }
              ],
              items: [
                { text: "A 50MW plant is planned near Nakuru", bucket: "report" },
                { text: "US$80m investment, construction next month", bucket: "report" },
                { text: "The most innovative company in East Africa", bucket: "drop" },
                { text: "It will transform the region", bucket: "drop" },
                { text: "Thousands of jobs (number unverified)", bucket: "drop" }
              ],
              explain: "Concrete, checkable facts can be reported once verified. Self-praise and vague promises are spin to drop or attribute."
            },
            {
              type: "mcq",
              q: "Which framing serves readers best here?",
              options: [
                "A celebration of the company's vision",
                "Straight news on the plant, with scrutiny of the jobs, funding and grid claims",
                "A disaster story about the energy sector",
                "An opinion piece arguing for solar power"
              ],
              answer: 1,
              explain: "Report the development, but hold the claims to account. Jobs, money and impact are the real public-interest questions."
            },
            {
              type: "order",
              q: "Order your article, top to bottom.",
              items: [
                "Lede: a 50MW solar plant is planned near Nakuru, with US$80m behind it",
                "The verified facts: size, timeline, who is funding it",
                "Context: the region's power needs and what the grid can handle",
                "A company quote, balanced against an independent voice",
                "Background on the company and the unanswered questions"
              ],
              explain: "Most important and verified first, then context, then quotes and background."
            },
            {
              type: "order",
              q: "Order the newsroom roll-out, first to last.",
              items: [
                "Pitch approved by the editor",
                "Report and verify the claims",
                "Write the draft",
                "Sub-editor checks and tightens the copy",
                "Fact-check names, figures and the quote",
                "Write an accurate headline and standfirst",
                "Publish, then promote"
              ],
              explain: "Verify, write, edit, fact-check, then headline and publish. Promotion comes after it is right, not before."
            },
            {
              type: "order",
              q: "Order your pitch to the editor.",
              items: [
                "A specific subject line with the news",
                "What the story is, in one line",
                "Why it matters now",
                "Why you can deliver it",
                "Length and format"
              ],
              explain: "Lead with the news, then why now, why you, and the practicalities."
            },
            {
              type: "multi",
              q: "How could this story help sustain the newsroom? Select all that apply.",
              options: [
                "Distinctive, verified reporting that draws and keeps readers",
                "Traffic and ad views from a story people share",
                "A sponsorship paid by Savanna Solar to cover it",
                "Building trust that supports subscriptions over time"
              ],
              answers: [0, 1, 3],
              explain: "Reader revenue, reach and trust all help. Taking money from the company you cover is a conflict of interest, not a business model."
            },
            {
              type: "write",
              q: "Write your pitch subject line.",
              brief: [
                "In one line, write the email subject line you would send the editor for this story.",
                "Make it specific and newsy, not vague."
              ],
              checklist: [
                "Does it state the actual news (the plant, the money)?",
                "Is it specific, not 'story idea'?",
                "Would an editor open it?"
              ],
              model: "Subject line: US$80m, 50MW solar plant planned near Nakuru, but who gets the jobs?",
              exerciseId: "capstone-subject-1"
            }
          ]
        }
      ]
    }
  ]
};
