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
    }
  ]
};
