# Customer decks: title slide, discovery research, options with a recommendation

Rules for every deck that is presented to a named customer. `SKILL.md` carries the short form of
these rules (hard rules, patterns, helper code); this file carries the procedures.

## Deck types

| Deck type | Recognise it by | Extra requirements on top of the house style |
|---|---|---|
| Any deck | always | Title slide presenter line `Vorname Name - Systems Engineer` |
| Customer deck | a customer is named or the deck is "for customer X" | Customer logo top right on the title slide |
| Discovery deck | discovery call, discovery workshop, first meeting, Erstgespräch, Kennenlernen | Company research first, pain points as hypotheses on a slide, research brief in the chat |
| Solution or offer deck with options | Lösungspräsentation, Angebotspräsentation, proposal, "Variante A/B", several designs or scopes | Exactly one recommended option, the others marked OPTIONAL, all options on one page |

The types combine: a discovery deck for a customer gets the logo, a proposal with options for a
customer gets the logo and the recommendation layout.

## Title slide

### Presenter line

The title slide subtitle has two lines at most:

1. topic or occasion, optionally with the month: `Discovery Workshop, Oktober 2026`,
   `Lösungsvorschlag Secure SD-WAN`,
2. the presenter, always in exactly this form: `Vorname Name - Systems Engineer`.

The spaced hyphen in the presenter line is the user's required format and the one accepted
exception to the punctuation rule. Use the presenter's real first and last name as the user gives
it (request, earlier conversation, account profile). Never invent a name. When the name is not known
and the user is present, ask for it together with the other clarifications; otherwise keep the
literal `Vorname Name` and say so in the chat reply (`lint` keeps flagging it). The role stays
`Systems Engineer` unless the user names a different title. Build it with
`d.title_slide(title, topic, presenter="Vorname Name")`.

### Customer logo

Every customer deck shows the customer's logo top right on the title slide, on a white rounded plate
(`d.title_slide(..., logo=path)` or `d.customer_logo(slide, path)`). The plate keeps any logo
legible on the dark title slide; `plate=False` is only for a white (negative) logo version.

Where the logo comes from, in this order:

1. A logo file the user supplied (upload, connected folder, earlier deck). If the user is present and
   no file was supplied, ask for one in the same question round as the other clarifications.
2. The customer's official website: the logo in the site header (an `<img>` or `<svg>` whose class,
   id, alt text or file name contains "logo"), or the press / media / brand page, which often offers
   the logo as SVG or high-resolution PNG. Download with `curl -L -o <file> <url>` or
   `IconLibrary._get(url)`.
3. Wikimedia Commons, which hosts the official SVG logo of many larger companies. Check that it
   matches the logo currently used on the customer's website.

Requirements and checks:

- Prefer SVG, then PNG with a transparent background, at least 400 px wide (`logo_png` warns below
  that). Favicons, app icons and social-media avatars are not the logo: use them only if they are
  the full logo.
- The right entity: a subsidiary, a Swiss branch or a hospital of a group may use its own logo. Use
  the logo of the organisation the deck is addressed to.
- Never redraw, recolour, crop, stretch, combine or AI-generate a logo, and never type the company
  name in a font as a logo substitute.
- Inline website SVGs sometimes take their colours from CSS (`currentColor`, classes) and rasterise
  black or empty: look at the render and use the press-kit file instead.
- No logo found: build with `logo="placeholder"` (dashed frame "KUNDENLOGO"), say so in the chat
  reply, and leave the warning in `lint` until a real logo is in place. A placeholder never goes to
  the customer.
- Logos, research briefs and customer decks stay in the working or deliverable folder. Never commit
  them to a repository.

## Discovery decks

A discovery call is mostly listening. The deck is short (8 to 12 slides) and shows that we did our
homework, states what we believe the customer's challenges are as hypotheses, and gives the call a
structure. Research comes before the storyline.

### Research procedure

Search the web every time, even for well-known companies (facts change: reorganisations,
acquisitions, new sites, incidents). Collect only public information and record a source and a date
for every item.

| Area | What to find | Typical sources |
|---|---|---|
| Profile | legal entity, industry, ownership (listed, family-owned, public sector, cooperative), employees, revenue if published | company website, annual report, commercial register (Zefix / SHAB in Switzerland, Handelsregister in Germany), stock exchange filings |
| Footprint | headquarters, sites, plants, branches, countries, data centres or cloud usage if public | website (locations page), annual report, press releases |
| Strategy and change | growth, M&A, carve-outs, new plants, digitalisation or cloud programmes, OT or IoT projects, cost programmes | press releases, annual report (strategy and risk sections), interviews with executives, trade press |
| Security and IT signals | publicly reported incidents, IT leadership changes, security or network job postings (they reveal the tech stack and the open gaps), certifications (ISO 27001, TISAX, IEC 62443) | news, the company's own statements, job portals, LinkedIn job posts |
| Regulation | data protection (revDSG / FADP, GDPR for EU business), FINMA for financial institutions, the Swiss reporting obligation for cyberattacks on critical infrastructure (ISG, reported to BACS), NIS2 and DORA for EU entities, IEC 62443 for OT, sector rules (health, energy) | the regulator, the company's own disclosures; the `fortinet-engineer` skill's DACH context |
| Industry threat picture | what attacks hit this sector and region (ransomware on manufacturing, OT exposure, phishing on healthcare) | FortiGuard Labs threat reports, BACS / NCSC publications |

Distinguish facts from inferences and tag them like the `fortinet-engineer` confidence protocol:
a fact carries its source (`[Annual report 2025]`, `[Press release, 2026-03]`, `[Website]`), an
inference is `[Inferred]`, anything unconfirmed is marked as such. Third-party sources such as
Reddit are marked explicitly. Do not use paywalled or non-public material, and never use information
from other customers' engagements.

### From signals to pain points

Derive each pain point from one or more signals, never from a generic list:

`signal (what we saw, with source) -> pain point (what it probably means for them) -> business impact
-> Fortinet angle (platform capability, verified) -> discovery question (how we validate it)`

Example of the shape (generic): "12 new sites announced in two years" -> "network roll-out speed and
consistent security per site" -> "projects delayed by firewall and WAN provisioning" -> "Secure
SD-WAN with zero-touch provisioning, central management" -> "How long does it take today to bring a
new site online, and who does it?"

Aim for four to six pain points, ranked by evidence strength and relevance for the meeting. When
evidence is thin, say so and keep fewer pain points rather than padding with generic ones.

### Research brief (chat reply, not the deck)

Deliver it with the deck, in the chat reply:

1. Company snapshot (5 to 8 facts, each with source and date).
2. Pain point hypotheses: a table with signal, pain point, impact, Fortinet angle, discovery question,
   confidence.
3. Sensitive findings (reported incidents, lawsuits, layoffs, leadership departures): listed here
   only, see below.
4. Gaps: what could not be found and should be asked in the call.
5. Sources: the list of links used.

### How it goes into the deck

- Pain points are hypotheses and the slide says so: the subtitle or a white band such as
  "Unsere Hypothesen aus öffentlichen Quellen, heute gemeinsam validieren".
- Each pain point tile carries the pain point as title and the observable signal plus the question in
  the body (`icon_tile` 3 x 2), or use a chip table with the columns pain point, what we see,
  question to you.
- Sensitive findings stay out of the slides: no named incidents, breaches or internal problems of the
  customer on a slide. Address the topic on industry level ("Ransomware trifft die Fertigung") and
  leave the specific point to the presenter (chat brief, and the speaker notes only if the user agrees).
- Speaker notes per pain point slide name the evidence behind each hypothesis in plain words ("They
  announced three plant openings this year") and repeat that these are hypotheses. No links or
  document names in the notes (the house rule on sources still applies).
- Company facts on the snapshot slide are only verified facts; figures carry their year ("rund 1'200
  Mitarbeitende (2025)"). Swiss German number format with the apostrophe as thousands separator.

### Discovery storyline (8 to 12 slides)

1. Title Slide Dark with customer logo and presenter line.
2. Agenda: "Ziel des Termins", "Ihr Unternehmen, wie wir es sehen", "Ihre Herausforderungen",
   "Ihre Fragen und Prioritäten", "Fortinet in Kürze", "Nächste Schritte".
3. Ziel des Termins: three gradient header cards (understand, align, agree next steps) or numbered cards.
4. Company snapshot: KPI gradient tiles (employees, sites, countries, industry) plus icon tiles of key
   developments, all verified.
5. Pain point hypotheses: icon tiles 3 x 2 or chip table, white band "Hypothesen, heute validieren".
6. Discovery questions: gradient panel with white rows (pattern 5) or numbered step rows, grouped by
   topic, at most eight questions on the slide (the full question bank lives in the presenter's
   notes, see `fortinet-engineer` presales playbook).
7. Fortinet in brief, mapped to their pain points: gradient header cards, one per relevant platform
   area, no generic portfolio tour.
8. Optional: one reference architecture or an industry use case relevant to the top pain point.
9. Next steps: numbered cards (workshop, PoC scoping, documents needed).
10. Closing Slide Dark.

## Solution and offer decks with several options

### Rules

- Exactly one option is recommended. The recommendation follows from the customer's requirements,
  constraints and our design reasoning; when the conversation gives no basis for a recommendation,
  ask the user which option to recommend instead of picking one.
- All options appear together on one page: the recommended one highlighted, the others marked
  OPTIONAL. Do not spread the alternatives over one slide each.
- Detail slides (architecture, scope table, PoC) follow for the recommended option only. If an
  optional variant needs more explanation, add one "Optionale Varianten" page (`option_split`) that
  states per variant what changes compared with the recommendation.
- The band under the options states the recommendation and its main reason:
  "Empfehlung Option A: ..." with the lead words in `ON_DARK[color]`.
- Facts rows compare like with like: the same labels in the same order on every option (sites,
  quantities, operating model, effort, migration risk, time to value). Quantities and qualitative
  values only; prices only when the user asks for them.
- Speaker notes name the trade-offs honestly: when an optional variant is better on a criterion, say
  so.
- Keep the options in their natural order (small to large, phase 1 to 3) and highlight the
  recommended one wherever it falls; without a natural order put the recommended option first.

### Choosing the layout

| Options | Layout |
|---|---|
| 2 or 3 | `option_cards` (columns). Card height 3.6 to 3.9 in, two to four bullets, up to four facts rows |
| 4 | `option_cards` with short texts (title up to about 18 characters, sub line up to about 30, three bullets of one line), or `option_split` |
| 5 or more, or a recommended option with much more content | `option_split`: recommended card left (60 %), compact OPTIONAL rows right |

### Accent colour

The recommended card uses Secure Red by default. Use the colour semantics of the deck instead when
the options map to them (purple for a FortiSASE-led option, blue for a cloud-hub option), so the
highlight matches the architecture slides that follow. Optional cards stay white with grey OPTIONAL
pills, whatever the accent.
