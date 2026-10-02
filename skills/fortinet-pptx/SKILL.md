---
name: "fortinet-pptx"
description: "Build, edit or review Fortinet PowerPoint decks in the modern gradient house style on the official FTNT template, icons from icons.fortinet.com. Use for any Fortinet deck, slides or presentation request."
---

# Fortinet PPTX

Fortinet decks are not freehand design work. Fortinet's official 37-layout template solves the
colour, logo, footer and typography problem; the house style described here solves the content
layout problem. Every content slide is a composition of native, editable shapes placed on the
template's Title Only or Title Subtitle layout, with Fortinet icons from icons.fortinet.com. No
placeholder bullet dumps, no clip art, no invented colours.

**The house style is the modern gradient style** (default since September 2026). It follows the
design language of Fortinet's current corporate decks:

- accent **gradient cards** (accent colour to a darker shade of the same accent) as the main container,
- a **white inner panel** inside the gradient card that carries the bullets,
- **icon badges**: white circles with an accent ring and a soft shadow, sitting on the top edge of a card,
- **soft drop shadows** instead of grey 1 pt borders on white cards,
- a **dark gradient pill** as the takeaway band, blue gradient table headers, gradient chevrons,
- architecture diagrams built from gradient boxes with the coloured icon in a white badge.

Everything is built with the `ModernDeck` class (ftnt_modern.py) on top of the classic helper
library (ftnt_deck.py). The classic flat style (`FortiDeck` alone, 1 pt borders, no gradients) is
used only when the user explicitly asks for it. When the user connects a folder with current
Fortinet corporate decks, render a few of their slides once and compare your output against them.

## Before anything else

1. Read `references/brand-spec.md` if it is present (palette, typography, layout list, the red-block
   and grid motif). The values you need most are repeated in this file, so the skill also works
   when that reference is missing.
2. The base file for every deck is the bundled template `assets/FTNT_PPT_16x9_Light_Template.pptx`.
   If the asset is missing, look for the FTNT 16x9 light template in the user's connected folders
   or ask for it. Never build a "Fortinet" deck on a blank python-pptx or pptxgenjs presentation.
3. The general `pptx` skill provides the mechanics you still rely on: `scripts/office/validate.py`
   (run it on every output, with `--original <template>`), `scripts/thumbnail.py`, and the OOXML
   editing notes. Rendering for QA uses `scripts/render_slides.py` from this skill; if it is
   missing, convert with `soffice --headless --convert-to pdf` and `pdftoppm -jpeg -r 110`.
4. The build path is python-pptx with the two helper files at the end of this file. Write the first
   code block to `ftnt_deck.py` and the second to `ftnt_modern.py` in your working directory once
   per session (extract them from this SKILL.md with a short script rather than re-typing), then
   `from ftnt_modern import *` and `d = ModernDeck(template, icon_cache="icon_cache")`.
   `pip install cairosvg --break-system-packages` is needed once for icon rasterisation.

## Hard rules (a deck that breaks one of these is wrong, however pretty)

- Layouts by name only: `Title Slide Dark` (opening), `Agenda`, `Section Header 1` and `Section
  Header 2` (alternate them), `Title Only` and `Title Subtitle` (all content), `Closing Slide Dark`.
  Content is never typed into the body placeholder of `Title and Content`; it is built from shapes.
- Never touch title geometry. Set `slide.shapes.title.text` and nothing else. python-pptx writes a
  broken `xfrm` (offset 0/0, height 0) when only one of left/top/width/height is set, which throws
  the title into the top-left corner. Every content title sits at the layout default: 28 pt bold,
  left 353011, top 264872. If a title does not fit beside the tracker, shorten the title.
- Icons come from icons.fortinet.com only (procedure below). No emoji, no react-icons, no drawn
  substitutes, no screenshots of icons, no recolouring of the SVGs. On gradient fills the coloured
  icon goes into a white badge (`wbadge`, `badge`); the `-white` line variants are too faint on
  gradients and are only used on flat dark surfaces.
- Arial only. Colours only from the palette, the tints and the gradient stops below.
- Gradients: two-stop linear only, from an accent to its own darker stop (`DARK[accent]`), never two
  different accents in one gradient, never rainbow or radial. Angle 70 degrees (`ang=4200000`) for
  cards and boxes, 0 degrees for bands, pills, chevrons and arrows, 90 degrees for tint panels and
  thin bars. The helpers do this; do not hand-roll gradients.
- Shadows: only the soft drop shadows of the helpers (card 0.25 in blur, 0.08 in down, 22 % black;
  badge 0.17 in / 0.04 in / 30 %; band 0.22 in / 0.07 in / 25 %; table row labels 0.08 in / 0.02 in /
  18 %). No 3D, bevel, glow, reflection or outer glow.
- Punctuation: no em dashes, no en dashes as separators, no middle dots. Use commas, colons,
  slashes, "to" / "bis" for ranges and a spaced hyphen only if nothing else works. English decks use
  British spelling (analyse, organisation) unless the user asks otherwise; German decks use Swiss
  orthography (ss, never the sharp s), sentence case titles.
- No customer names unless the user gives them in the request. Examples are generic.
- Fortinet product claims are verified against docs.fortinet.com (and the ordering guides for
  licensing) before they go on a slide.
- **No sources in the deck** unless the user explicitly asks for them in the current request: no
  footnotes or source lines ("Quelle:", "Source:"), no links, no document names or revision numbers
  (ordering guide codes, deployment guide titles), neither on the slides nor in the speaker notes.
  Notes state the fact itself ("SPA licences are only needed at the hubs"), never "according to the
  ordering guide ...". The sources you used go into the chat reply instead. When sources are
  requested, use `footnote()` on the slides concerned (7.5 pt grey, bottom left).
- Speaker notes on every content slide (2 to 5 sentences: what to say, and any honesty caveat such
  as "this mapping is our interpretation" or "this value is an assumption").
- Offer and proposal decks show quantities, never prices, unless the user asks for prices.
- When the user has edited a deck by hand, later changes are in-place python-pptx edits on their
  file (find shapes by name, change text or add shapes). Never regenerate over their edits. A new
  design or content iteration of a generated deck is saved as a new version file (`_v2`, `_v3`)
  beside the previous one.

## Icons from icons.fortinet.com

The site is a static SvelteKit app with three things you can use directly:

| What | URL | Notes |
|---|---|---|
| Catalogue | `https://icons.fortinet.com/iconData.json` | List of objects: `Name`, `ID`, `Category`, `Path`, `White Path`, `Tags`. About 800 icons |
| Whole library | `https://icons.fortinet.com/Fortinet-Icon-Library.zip` | 3.5 MB, 1571 flat SVGs (`<ID>.svg` and `<ID>-white.svg`). Download once per session |
| Single icon | `https://icons.fortinet.com/icons/<ID>.svg` | Same file as in the zip. The server drops connections intermittently, so always retry |

Categories: Logos, Pillars, Form Factors, Secure Networking, Unified SASE, Security Operations,
OT-Aware Security Fabric, FortiGuard Services, Devices and Verticals. IDs are the file stems as
used on the site (case sensitive): `FortiGate`, `PLC`, `OT-Engineer`, `platform-OT-Security`.

Procedure (all wrapped in `IconLibrary` in the helper library):

1. `lib = IconLibrary("icon_cache")` downloads the zip and the catalogue on first use, with six
   retries and a back-off, and caches both. Reuse the cache directory across builds.
2. `lib.search("plc")`, `lib.search("rugged", "switch")` return `(ID, Category, Tags)` hits. Search
   on function, not on adjectives, and read the tags: some names lie. `Supply-Chain` is a VoIP
   phone, `3cx-Supply-Chain` is an outbreak icon, `Rugged` alone is a generic box. When nothing
   fits, prefer a generic concept icon over a wrong product icon.
3. `lib.png(ID, white=False, px=512)` rasterises the SVG to a cached 512 px PNG (cairosvg, or
   ImageMagick `convert` as a fallback). `FortiDeck.icon(slide, ID, x, y, size, white=...)` places
   it and names the shape `Icon <ID>` with `descr="<ID>.png"`, so the origin stays traceable.
4. Before building, render a contact sheet of every chosen icon (PIL, 8 per row) and look at it.
   Icons are checked for meaning, not just existence: a camera for IoT, a PLC for control, a
   handshake for partners.

Default icon style is dark grey line art with silver and red accents; it sits on white cards, on
tinted panels and inside white badges. On gradient fills the coloured icon always goes into a white
badge (`wbadge` without ring inside diagram boxes, `badge` with an accent ring on card edges); the
white variants are only for flat `INK` surfaces.

IDs that proved right in the reference deck (a starting vocabulary, not a limit): devices `PLC`,
`HMI`, `Robotic-Arm`, `Robotics`, `Industrial-Control`, `Security-Camera`, `Wireless-Thermostat`,
`Wireless-Door`, `Keycard`, `EVCS`, `Smart-Medical-Device`, `Router`, `Wireless`, `Laptop`,
`Desktop`, `Data-Center`, `Data-Center-Rack`, `Hard-Drive`, `Cloud`, `Enterprise`, `Headquarters`,
`Transportation-Truck`, `Chemical`, `Manufacturing`, `Equipment`, `Safe`; people `OT-Engineer`,
`OT-People`, `Single-User`, `Multi-User`, `Partnerships`; concepts `Convergence`, `Needs-Update`,
`Remote-Access`, `Unsecure-Equipment`, `Asset-Discovery`, `Business-Continuity`, `Guide`,
`Monitoring`, `Risk-Management`, `Segmentation`, `Planning`, `Detect`, `Respond`, `VPN`, `IAM`,
`Application-Control`, `Vulnerability-Management`, `High-Availability`,
`Incident-Response-Service`, `Security-Awareness-Training`, `Network-Security`,
`Internal-Segmentation-Firewall`, `Rugged-Firewall`, `Sec-Rating`, `platform-OT-Security`;
products `FortiGate`, `FortiSwitch-Rugged`, `FortiAP`, `FortiNAC`, `FortiAnalyzer`, `FortiManager`,
`FortiSIEM`, `FortiSOAR`, `FortiPAM`, `FortiAuthenticator`, `FortiClient`, `FortiEDR`,
`FortiSandbox`, `FortiDeceptor`, `FortiNDR`, `FortiGuard-Labs`.

IDs that proved right in the SD-WAN / SASE offer deck: `Azure-vWAN`, `FortiGate-VM`,
`Secure-SD-WAN`, `SD-WAN-Orchestrator`, `Underlay-monitoring-performance`,
`Secure-local-internet-breakout`, `WAN`, `High-Availability`, `FortiSASE Cloud` (with a space),
`Secure-Web-Gateway`, `IPsec-VPN`, `ZTA`, `FortiClient-DEM`, `Data-Center-Building`, `Data-Center`,
`Branch-Office`, `Manufacturing`, `Multi-User`, `Compliance` (regulation), `Partnerships`,
`dart-board` (success criteria), `calendar-tool` (timeline), `Agreement` (requests, contracts),
`FortiAI`.

## The house style (modern gradient style)

### Slide anatomy

Slide 12192000 x 6858000 EMU (13.333 x 7.5 in). Content column from `LEFT = 448056` to
`RIGHT = 11786616` (`CONTENT_W = 11338560`). Content starts at `1188720` on Title Only and at
`1371600` on Title Subtitle (the grey 18 pt subtitle is the layout's placeholder idx 11, one sentence
of at most about 90 characters, so it stays on one line). Nothing goes below `BOTTOM = 6126480`;
the footnote line at `6437376` stays empty unless sources were explicitly requested. Gaps between
cards 182880 (0.2 in), between table chips 54864 / 73152. Corner radii in EMU: gradient cards
`ModernDeck.CARD_R = 164592`, tiles 91440, chips 73152, table cells 54864; bands and pills are
fully rounded (radius = height / 2). The optional step tracker sits top right at y 329184, right
edge 11859768; with a four-step tracker the title must stay under about 40 characters, with five
steps under about 36.

A typical content slide reads top to bottom: title (28 pt bold), optional subtitle (18 pt grey), one
row of gradient cards or one diagram, optionally a row of white tiles, and a full-width dark
gradient pill band at the bottom that states the one message of the slide. Architecture slides may
replace the band with a legend row. The slide is full but never crowded: three to five columns,
two to three rows, one band.

### Type scale (Arial, sizes in pt)

| Element | Size and weight | Colour |
|---|---|---|
| Slide title / subtitle | 28 bold / 18 regular (layout defaults) | black / 7F7F7F |
| Gradient card title, band statement | 14 bold | white (INK on yellow) |
| Question / sub line on a gradient card | 11.5 regular | `TINT[accent]` (INK on yellow) |
| KPI number on a gradient tile | 26 bold | white, label 10 in `TINT[accent]` |
| Tile title, box title in a diagram | 12.5 to 13 bold / 10.5 bold | black on white, white on gradient |
| Chevron step name, band lead sentence | 12.5 bold | white |
| Bullets in the white inner panel | 10.5 to 12 regular | black, square bullet in the accent |
| Body in tiles, table header | 10 to 10.5 regular / 10.5 bold | 464646 / white |
| Secondary text, table cells, diagram sub lines | 8.5 to 9.5 regular | 464646, tint text or `TINT[accent]` on gradient |
| Kickers (`STEP 1`, `ERGEBNIS`, `MICROSOFT AZURE, VIRTUAL WAN`) | 7.5 to 9 bold, upper case | accent or tint text |
| Tracker chevrons, pills | 7 bold | white (inactive: 75787B on DADDE2) |
| Footnote / source line (only when sources are explicitly requested) | 7.5 regular | 7F7F7F |

Bullets are the small square `▪` (U+25AA) in the card's accent colour, `marL 128016`, `indent
-128016`, 3 to 4 pt space before each paragraph after the first.

### Colour and surfaces

| Role | Value |
|---|---|
| Accents, in this order for columns and steps | Secure Red `DA291C`, Cloud Blue `307FE2`, SASE Purple `9063CD`, SecOps Teal `2CCCD3`, FortiGuard Green `3CB17E`; Connectivity Yellow `FFB900` and OT Grey `75787B` for special cases and neutral |
| Gradient dark stops (`DARK`) | red `9D1E14`, blue `185AAD`, purple `6535A6`, teal `209398`, green `2B7F5B`, yellow `B88500`, grey `545659`, INK `3A3A3A` to `1E1E1E` |
| Tints (zone panels, value chips, note boxes) | red `F8D4D2`, blue `D6E5F9`, purple `E9E0F5`, yellow `FFF1CC`, teal `D5F5F6`, green `D8EFE5`; as panels they run top to bottom into `LIGHT_END` (a lighter tint) |
| Text on tints | red `DA291C` bold, blue `1F5FB0`, purple `6B46A8`, yellow `7A5A00`, teal `0E7C82`, green `2A8C62`, neutral `464646` |
| Text on gradients | white titles, `TINT[accent]` sub lines; on yellow always INK |
| Accent text on the dark band | red `FF6A5E`, blue `7FB2F5`, green `6FD3A8`, purple `C9B3F0`, teal `7FE3E8`, yellow `FFD35C` |

Surface rules (the helpers apply them automatically through `ModernDeck.rounded`):

- An accent fill is always a gradient (accent to `DARK[accent]`) with a card shadow.
- A white card has no border, only the soft shadow (`rounded(..., WHITE, BORDER)` drops the border).
- A white card with an accent border keeps the border (use it for diagram boxes that must be
  colour-coded but stay light, for example destinations such as "Internet und SaaS").
- `LIGHT` (F0F0F0) is never a fill: it is the slide background and becomes invisible. Use WHITE.
- Tint panels (zone backgrounds like "MICROSOFT AZURE, VIRTUAL WAN") get a vertical tint gradient,
  no shadow, and an 8 pt bold upper-case kicker in the tint text colour at the top left.
- Small chips (under 0.55 in high) get no shadow except table row labels (light shadow).

Colour semantics in architecture and offer decks (keep them consistent on every slide): blue =
cloud, Azure and cloud hubs; red = FortiGate appliances (sites, data-centre hubs); purple =
FortiSASE; teal = management and logging (FortiManager, FortiAnalyzer); green = FortiGuard /
internet breakout; yellow = special or separate scope (e.g. a regional partner offer) with dark
text; grey = underlay and neutral.

### Pattern catalogue (helper call in brackets)

1. **Gradient header cards**, 3 or 4 across (`header_card` with `icon`): gradient card, icon badge
   centred on the top edge (badge diameter = 1.3 x `icon_size`, capped at 1.3 in), white 14 pt
   title, optional question line in `TINT[accent]`, white inner panel with accent bullets. Card
   height 3.7 to 4.2 in. Vertical budget with `icon_size` 0.8 to 0.9 in: the white panel starts
   about 2.1 in below the card's y; keep bullets to 3 or 4 (2 lines each at most). Use for
   principles, pillars, options, product blocks. A band underneath.
2. **Gradient list panels** (`header_card` without icon, `body=None`): gradient card with a white
   title band and a white inner panel starting 0.48 in below the top; draw your own rows inside
   from 0.55 in (country chip, name, proportional bar, label). Nine rows of 0.26 in with 0.025 in
   gaps fit into a 3.3 in panel. Use for footprints, inventories, region overviews.
3. **KPI gradient tiles**, 4 or 5 across (`rounded(slide, x, y, w, 0.85 in, accent, None,
   d.CARD_R, shade=True)` plus a 26 pt white number and a 10 pt `TINT[accent]` label). Use at the
   top of a situation slide.
4. **Icon tiles** (`icon_tile`): white shadowed tile, icon left (0.6 to 0.85 in), bold title and
   grey text right. 3 x 2 grid for challenges, findings, open points; a 4-row stack beside a diagram.
5. **Gradient panel with white rows** (`dark_panel` + `icon_tile(dark=True)`): accent gradient panel
   (default blue) with a white 14 pt title and tinted sub line, white rows with coloured icons
   (0.45 in) and 11 pt text. Use for "what we need from you", evidence, requirements. Pair it with a
   gradient header card on the left in a different accent.
6. **Chevron process row** (`chevrons`): gradient pentagon and chevrons, kicker `STEP n` 9 pt over
   the name 12.5 pt. Below each step a grey question and a bordered deliverable box.
7. **Step tracker** (`tracker`): five or four 750000 x 274320 mini chevrons top right, lit steps in
   their gradient, others `DADDE2` with `75787B` text, label 8 pt grey to the left. All steps lit on
   overview slides. Put it on every slide of the framework or phase (e.g. all PoC slides).
8. **Chip table** (`chip_table`): blue gradient header chips, white row-label chips with a light
   shadow, white neutral chips, tinted value chips (tint gradient), solid gradient chips for the
   verdict or component column. Columns weighted. Up to 8 rows of 0.43 to 0.5 in.
9. **Numbered step rows** (`step_rows`): white rows, gradient number square, 12 pt text, icon right.
10. **Quote panel** (`quote_panel`): dark gradient panel, red 72 pt quote mark, white 16 pt quote.
11. **Accent tiles** (`accent_tile`): white shadowed tile with an inset gradient pill bar on the
    left, 11.5 pt bold title, 9.5 pt grey text. Four across for rules, principles, constraints.
12. **Takeaway band** (`band`): full-width dark gradient pill with shadow, white 12.5 to 14 pt text
    and `ON_DARK` coloured lead words; `dark=False` gives a white pill with shadow (use it for
    "not in scope" statements with a red lead word). One per slide, height 0.55 to 0.75 in.
13. **Numbered cards with arrows** (`numbered_card` + `arrow`): white shadowed cards, gradient number
    circle, upper-case kicker in the accent, 14 pt title, icon badge ringed in the accent, centred
    11 pt grey text, gradient red arrows between cards. Keep `icon_size` at 0.7 to 0.8 in for a
    2.85 to 2.95 in card or the text runs out of the card. Optionally a row of white result boxes
    under the cards (inset gradient bar, kicker `ERGEBNIS` / `OUTCOME`, 11 pt bold text). Use for
    next steps, PoC tracks, engagement models.
14. **Architecture building blocks** (`gbox`, `wbadge`, tint zone panels, `line`, `chip`): tint zone
    panels for clouds and platforms; gradient boxes with the coloured icon in a white badge, white
    title and tinted sub line (`gbox`, several badges for combined products); white chips inside a
    box for sub-elements (PROD / DEV vNET, SIA / SPA / ZTNA); white shadowed boxes for users and
    external destinations. Draw all lines first, then the boxes, and check that no vertical line
    runs behind a box it does not belong to (compare the line x with every box span in that row).
    Solid 2.25 pt lines for overlays, dashed purple for SASE private access, a legend row with line
    samples at the bottom instead of a band.
15. **Site or device blueprint**: destinations on top (white boxes with accent border), underlay
    chips (grey gradient), the device as a gradient box with a white badge and the key specs,
    LAN box with icons at the bottom, an icon-tile stack on the right with the four key functions.
16. **Timeline / Gantt**: label column (3.5 in) plus weekly columns; gradient phase chevrons above
    the weeks in the tracker colours, dark gradient week header chips, WHITE cells, gradient bars
    with short 8.5 pt labels, grey dots for recurring meetings, one band with the start condition.
17. **Scope table for offers**: chip table "Baustein / Komponente / Menge / Services", quantities as
    tinted chips, then two note boxes: optional items (yellow tint) and "not included" (white).
18. Classic compositions still valid with the modern primitives: phase columns, zone or level rows
    with conduit pills, flow maps, rating dots, product icon rows (`icon_row`).

### Storyline conventions

Title Slide Dark, Agenda (5 to 7 lines), then per section a Section Header (alternate 1 and 2) and 2
to 6 content slides, a roadmap or PoC plan, next steps (numbered cards), Closing Slide Dark.
Customer decks run 20 to 26 slides; a follow-up 8 to 12. Titles are sentence case and carry the
message, the subtitle carries the explanation. Each content slide has exactly one message, repeated
in the band.

A proven offer-deck storyline (solution proposal plus PoC): situation (KPI tiles, region panels),
design principles (gradient header cards), section architecture (overview diagram, hub cards, site
blueprint, traffic-flow chip table), section SASE (gradient header cards, private-access flow,
regional special case), section operations and scope (management cards, scope table), section PoC
(tracks with rules, test topology, success criteria table with "target value (proposal)" column,
Gantt, roles with gradient card vs. gradient panel, open points as icon tiles), next steps.

## Build workflow

1. Clarify what is not given (audience, language, length, scope, which products) with one
   AskUserQuestion when the user is present; otherwise state the assumptions and build.
2. Collect the content first (the user's folder: BOM, site lists, diagrams; docs.fortinet.com for
   product facts; ordering guides for licensing). Write a storyline table: slide, layout, pattern,
   message, icons, source (the source column is for your own verification and the chat reply, it
   never goes into the deck).
3. Write `ftnt_deck.py` and `ftnt_modern.py` from the two code blocks below,
   `pip install cairosvg --break-system-packages`, create the icon library through
   `ModernDeck(...).icons`, search and shortlist the icon IDs, render the icon contact sheet and
   look at it.
4. Write `build_deck.py`: one block per slide using the helpers, `notes()` on every content slide,
   `save()` to the deliverable name. Keep this script; later edits reuse it or, if the user has since
   edited the deck by hand, open their file and patch shapes by name.
5. QA, all four steps every time: `lint(path)` (title overrides, off-palette colours, non-Arial
   fonts, em dashes, shapes below the content area, missing notes, source lines and document
   references on slides or in notes), the pptx skill's `validate.py --original <template>`,
   `render_slides.py` to JPEGs, and look at every slide (contact sheets of four at 110 dpi). Fix
   text that spills out of its box or its white panel, lines that run behind boxes, faint icons on
   gradients, white text on yellow, empty half slides. Re-render and look again. LibreOffice renders
   the gradients and shadows faithfully.
6. Deliver the .pptx (and write it to the connected folder when there is one), state the caveats
   that also live in the notes, list the sources in the chat reply (not in the deck), and keep the
   build script and icon cache for the next iteration.

### Lessons learned (each one cost a render round)

- `LIGHT` fills disappear on the light slide background; grid cells and panels are WHITE.
- White line icons on gradient fills are too faint: coloured icon in a white badge (`wbadge`).
- An icon badge costs height: in `numbered_card` keep `icon_size` at 0.7 to 0.8 in; in
  `header_card` with question and four bullets use `icon_size` 0.8 to 0.9 in and a card of 3.85 in
  or more. Shorten a bullet before shrinking the type.
- In diagrams, a line drawn before a box disappears behind it: move the box, not the line, until
  every vertical line has a free corridor.
- Yellow gradients and yellow circles carry INK text, never white.
- Subtitles longer than about 90 characters wrap into the content area; shorten them.
- Title slide subtitle: two lines at most ("topic" and "name, Fortinet, month year").
- `from pptx.enum.dml import MSO_LINE_DASH_STYLE` for dashed borders (`shape.line.dash_style`).
- The icon catalogue has entries with `Tags: null` (handled in `IconLibrary.search`) and IDs with
  spaces (`FortiSASE Cloud`): pass them exactly.
- Numbers on slides are checked against their source (site list, BOM) with a small assert in the
  build script (e.g. site count and user total), so a later data change cannot silently break a slide.
- Source footers were removed on request after delivery: sources never go into the deck (slides or
  notes) unless asked for; `lint` flags "Quelle:" / "Source:" lines and guide references.

### Common requests

- "Build a deck on X" or "a presentation for a customer about Y": full workflow above, 20 to 25
  slides for a customer story, 8 to 12 for a follow-up.
- "Make this deck Fortinet-branded" or "align this to Fortinet CI/CD" (a non-Fortinet deck is
  supplied): read its content with `markitdown`, map every slide to a pattern from the catalogue and
  rebuild it on the template. Never just recolour the existing slides.
- "Add a slide about X to this deck": open the deck, copy the patterns, colours and tracker state of
  the neighbouring slides, add the slide in place with the helpers and keep the user's edits.
- "Review this deck": run `lint`, render, and report against the hard rules and the QA checklist.
- "Make it more modern" or "like the Fortinet sales decks" on a classic-style deck: rebuild with
  `ModernDeck` from the same build script (swap the import and the class, then fix the diagram
  slides: gradient boxes with `gbox`, badges with `wbadge`), save as a new version beside the old one.
- "Change content X" after delivery (e.g. a quantity or a design decision such as "no HA at the
  sites"): change it in every slide and in the speaker notes (search the build script and the
  rendered text for all mentions), rebuild, and save the next version file.
- "Add the sources" / "mit Quellen": only then add `footnote()` lines on the slides that carry
  verified product facts or external figures, and run `lint(path, sources_ok=True)`; otherwise the
  deck stays free of sources.

## QA checklist (look at every rendered slide, then tick these)

- Titles all at the same position and size, none wrapped to two lines, none under the tracker.
- No text leaves its box or its white inner panel; no card, band or table crosses `BOTTOM`; margins
  identical on every slide.
- Every icon is a Fortinet library icon, means what the label says, sits in a white badge on
  gradients, is not pixelated or stretched (always square, 512 px source).
- Gradients only accent to its own dark stop; white text on every gradient except yellow (INK);
  no grey borders left on white cards; no LIGHT fills.
- Accent order, colour semantics and step colours consistent across slides; nothing off-palette
  (`lint` says so).
- One message per slide, stated in the band; notes present; no sources, footnotes or guide
  references on slides or in notes unless asked; no em dashes, no middle dots, no customer names
  unless given, no prices unless asked, British spelling in English and Swiss orthography in German.
- `validate.py --original <template>` passes; the file opens without a repair prompt.

## Editing a house-style deck the user has changed by hand

Open their file with `Presentation(path)`, locate slides by index or title text and shapes by name
(`Icon <ID>`, `Rounded Rectangle n`, `TextBox n`), change text runs in place, and add new shapes
with the same helpers by wrapping the existing slide (`ModernDeck` methods only need a slide object,
so instantiate `ModernDeck` on the template for the icon library and pass the user's slide). Save to
the same path only when asked; otherwise save a copy beside it. Never rebuild the whole deck, and
never set a placeholder's width or height (see the title bug above).

## If the environment is missing pieces

- No `soffice`: visual QA cannot run; say so explicitly rather than claiming the deck was checked.
  Building the .pptx does not need it.
- No `pdftoppm`: `render_slides.py` falls back to PyMuPDF (`pip install pymupdf`); expected, not an
  error.
- icons.fortinet.com unreachable after retries: reuse a cached `Fortinet-Icon-Library.zip` from an
  earlier build if one exists; otherwise stop and tell the user which icons are missing. Do not
  substitute icons from another source.
- No `cairosvg` and no ImageMagick: `pip install cairosvg --break-system-packages` (pure wheels, no
  system packages needed on the standard image).

## Helper library, part 1 (write this block to ftnt_deck.py)

The classic primitives, patterns, `IconLibrary` and `lint`. `ModernDeck` in part 2 builds on it.

```python
"""ftnt_deck.py - python-pptx helpers for Fortinet house-style decks (see SKILL.md).
Native editable shapes on the official FTNT 16x9 light template. All geometry in EMU
(914400 = 1 inch); the slide is 12192000 x 6858000."""
import json, os, re, time, zipfile, urllib.request
from pptx import Presentation
from pptx.util import Emu, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR, MSO_AUTO_SIZE
from pptx.oxml.ns import qn
from lxml import etree

# palette (brand-spec.md) and the derived tints used by the house style
RED, BLUE, PURPLE, YELLOW, TEAL, SILVER, GREEN, GREY = ("DA291C", "307FE2", "9063CD", "FFB900",
                                                        "2CCCD3", "A2B2C8", "3CB17E", "75787B")
BLACK, WHITE, INK, DARK2, BODY_GREY, MUTED = "000000", "FFFFFF", "1E1E1E", "2E2E2E", "464646", "7F7F7F"
BORDER, LIGHT, ON_DARK_GREY = "DADDE2", "F0F0F0", "D0D0D0"
TINT = {RED: "F8D4D2", BLUE: "D6E5F9", PURPLE: "E9E0F5", YELLOW: "FFF1CC", TEAL: "D5F5F6",
        GREEN: "D8EFE5", GREY: "E3E4E5", SILVER: "E3E4E5"}
TINT_TEXT = {RED: RED, BLUE: "1F5FB0", PURPLE: "6B46A8", YELLOW: "7A5A00", TEAL: "0E7C82",
             GREEN: "2A8C62", GREY: BODY_GREY, SILVER: BODY_GREY}
ON_LIGHT = {GREEN: "2A8C62", TEAL: "0E7C82", YELLOW: "7A5A00"}          # accent text on white
ON_DARK = {RED: "FF6A5E", BLUE: "7FB2F5", GREEN: "6FD3A8", PURPLE: "C9B3F0", TEAL: "7FE3E8",
           YELLOW: "FFD35C"}                                            # accent text on INK
STEP_COLORS = [RED, BLUE, PURPLE, TEAL, GREEN]
PALETTE = set([RED, BLUE, PURPLE, YELLOW, TEAL, SILVER, GREEN, GREY, BLACK, WHITE, INK, DARK2,
               BODY_GREY, MUTED, BORDER, LIGHT, ON_DARK_GREY, "B3B3B3", "C9CED6", "3A3A3A", "565656",
               "8F9295", "9EB5CB"] + list(TINT.values()) + list(TINT_TEXT.values())
              + list(ON_LIGHT.values()) + list(ON_DARK.values()))

# geometry
SLIDE_W, SLIDE_H = 12192000, 6858000
LEFT, RIGHT = 448056, 11786616                  # content column edges
CONTENT_W = RIGHT - LEFT                        # 11338560
TOP_TITLE_ONLY, TOP_TITLE_SUB = 1188720, 1371600
BOTTOM, FOOTNOTE_Y = 6126480, 6437376           # nothing below BOTTOM except the footnote
GAP, INS_X, INS_Y = 182880, 45720, 27432
R_CARD, R_TILE, R_CHIP, R_CELL = 109728, 91440, 73152, 54864   # corner radii in EMU


def rgb(h):
    return RGBColor.from_string(h)


def cols(n, gap=GAP, x0=LEFT, width=CONTENT_W, weights=None):
    """[(x, w), ...] for n columns across the content width; weights make columns unequal."""
    weights = weights or [1] * n
    unit = (width - gap * (n - 1)) / sum(weights)
    out, x = [], x0
    for wt in weights:
        w = int(unit * wt)
        out.append((int(x), w))
        x += w + gap
    return out


def rows(n, y0, height, gap=GAP):
    unit = (height - gap * (n - 1)) / n
    return [(int(y0 + i * (unit + gap)), int(unit)) for i in range(n)]


class IconLibrary:
    """icons.fortinet.com: one zip download (about 3.5 MB, 1571 SVGs), then everything is local.
    ids are the file stems used on the site ('FortiGate', 'PLC', 'OT-Engineer'); nearly every
    icon has a white variant id + '-white' for dark fills."""
    ZIP_URL = "https://icons.fortinet.com/Fortinet-Icon-Library.zip"
    DATA_URL = "https://icons.fortinet.com/iconData.json"
    ICON_URL = "https://icons.fortinet.com/icons/{}.svg"

    def __init__(self, cache_dir):
        self.dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        self.zip_path = os.path.join(cache_dir, "Fortinet-Icon-Library.zip")
        self.data_path = os.path.join(cache_dir, "iconData.json")
        self._zip = self._data = None

    @staticmethod
    def _get(url, tries=6):
        last = None
        for t in range(tries):                     # the server drops connections now and then
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Connection": "close"})
                with urllib.request.urlopen(req, timeout=120) as r:
                    return r.read()
            except Exception as e:
                last = e
                time.sleep(1.5 * (t + 1))
        raise RuntimeError(f"download failed after {tries} tries: {url} ({last})")

    def zip(self):
        if self._zip is None:
            if not os.path.exists(self.zip_path):
                open(self.zip_path, "wb").write(self._get(self.ZIP_URL))
            self._zip = zipfile.ZipFile(self.zip_path)
        return self._zip

    def data(self):
        if self._data is None:
            if not os.path.exists(self.data_path):
                try:
                    open(self.data_path, "wb").write(self._get(self.DATA_URL))
                except Exception:
                    self._data = []
                    return self._data
            self._data = json.load(open(self.data_path, encoding="utf8"))
        return self._data

    def search(self, *words, limit=25):
        """Match all words against Name, ID, Category and Tags. Look at the hits before choosing."""
        words = [w.lower() for w in words]
        hits = [(it["ID"], it["Category"], (it.get("Tags") or "")[:70]) for it in self.data()
                if all(w in f"{it['Name']} {it['ID']} {it['Category']} {it.get('Tags') or ''}".lower() for w in words)]
        if not hits:
            hits = [(n[:-4], "?", "") for n in self.zip().namelist()
                    if n.endswith(".svg") and not n.endswith("-white.svg") and all(w in n.lower() for w in words)]
        return hits[:limit]

    def svg(self, icon_id, white=False):
        name = f"{icon_id}-white.svg" if white else f"{icon_id}.svg"
        try:
            return self.zip().read(name)
        except KeyError:
            return self._get(self.ICON_URL.format(name[:-4]))

    def png(self, icon_id, white=False, px=512):
        out = os.path.join(self.dir, f"{icon_id}{'-white' if white else ''}-{px}.png")
        if not os.path.exists(out):
            svg = self.svg(icon_id, white)
            try:
                import cairosvg
                cairosvg.svg2png(bytestring=svg, write_to=out, output_width=px, output_height=px)
            except ImportError:                     # pip install cairosvg is the normal path
                tmp = out[:-4] + ".svg"
                open(tmp, "wb").write(svg)
                os.system(f'convert -background none -density 384 "{tmp}" -resize {px}x{px} "{out}"')
        return out


class FortiDeck:
    def __init__(self, template_path, icon_cache="icon_cache"):
        self.prs = Presentation(template_path)
        lst = self.prs.slides._sldIdLst                  # drop the 55 example slides
        for sldId in list(lst):
            self.prs.part.drop_rel(sldId.rId)
            lst.remove(sldId)
        self.icons = IconLibrary(icon_cache)

    def layout(self, name):
        for l in self.prs.slide_layouts:
            if l.name == name:
                return l
        raise KeyError(name)

    def save(self, path):
        self.prs.save(path)
        return path

    # slide types: placeholders only, never move or resize a title
    def title_slide(self, title, subtitle="", dark=True):
        s = self.prs.slides.add_slide(self.layout("Title Slide Dark" if dark else "Title Slide"))
        s.shapes.title.text, s.placeholders[1].text = title, subtitle
        return s

    def section(self, title, subtitle="", variant=1):
        s = self.prs.slides.add_slide(self.layout(f"Section Header {variant}"))
        s.shapes.title.text, s.placeholders[1].text = title, subtitle
        return s

    def agenda(self, items, title="Agenda"):
        s = self.prs.slides.add_slide(self.layout("Agenda"))
        s.shapes.title.text = title
        tf = s.placeholders[1].text_frame
        tf.text = items[0]
        for it in items[1:]:
            tf.add_paragraph().text = it
        return s

    def content(self, title, subtitle=None):
        """Title Only (subtitle None) or Title Subtitle. Returns (slide, y where content starts)."""
        if subtitle is None:
            s, top = self.prs.slides.add_slide(self.layout("Title Only")), TOP_TITLE_ONLY
        else:
            s, top = self.prs.slides.add_slide(self.layout("Title Subtitle")), TOP_TITLE_SUB
            s.placeholders[11].text = subtitle
        s.shapes.title.text = title
        return s, top

    def closing(self, dark=True):
        return self.prs.slides.add_slide(self.layout("Closing Slide Dark" if dark else "Closing Slide"))

    @staticmethod
    def notes(slide, text):
        slide.notes_slide.notes_text_frame.text = text

    # primitives
    @staticmethod
    def _style(shape, fill, line, line_w=12700):
        if fill is None:
            shape.fill.background()
        else:
            shape.fill.solid()
            shape.fill.fore_color.rgb = rgb(fill)
        if line is None:
            shape.line.fill.background()
        else:
            shape.line.color.rgb = rgb(line)
            shape.line.width = Emu(line_w)
        shape.shadow.inherit = False
        return shape

    def rounded(self, slide, x, y, w, h, fill=WHITE, line=BORDER, radius=R_CARD):
        sh = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Emu(x), Emu(y), Emu(w), Emu(h))
        self._style(sh, fill, line)
        sh.adjustments[0] = min(0.5, radius / min(w, h))   # fixed radius whatever the size
        return sh

    def rect(self, slide, x, y, w, h, fill, line=None):
        return self._style(slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Emu(x), Emu(y), Emu(w), Emu(h)), fill, line)

    def circle(self, slide, x, y, d, fill, line=None, line_w=12700):
        return self._style(slide.shapes.add_shape(MSO_SHAPE.OVAL, Emu(x), Emu(y), Emu(d), Emu(d)), fill, line, line_w)

    def line(self, slide, x1, y1, x2, y2, color=BORDER, w=12700, dash=False):
        c = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Emu(x1), Emu(y1), Emu(x2), Emu(y2))
        c.line.color.rgb, c.line.width = rgb(color), Emu(w)
        if dash:
            etree.SubElement(c.line._get_or_add_ln(), qn("a:prstDash")).set("val", "dash")
        return c

    def arrow(self, slide, x, y, w=173736, h=219456, color=RED):
        return self._style(slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Emu(x), Emu(y), Emu(w), Emu(h)), color, None)

    def text(self, slide, x, y, w, h, paras, size=10.5, color=BLACK, bold=False, align="l", anchor="t",
             bullets=None, insets=(INS_X, INS_Y), spacing=None):
        """paras: str | [str] | [[(run_text, {size, bold, color, italic}), ...]]. bullets=accent hex."""
        tb = slide.shapes.add_textbox(Emu(x), Emu(y), Emu(w), Emu(h))
        self._fill(tb, paras, size, color, bold, align, anchor, bullets, insets, spacing)
        return tb

    @staticmethod
    def _fill(shape, paras, size=10.5, color=BLACK, bold=False, align="l", anchor="t", bullets=None,
              insets=(INS_X, INS_Y), spacing=None):
        tf = shape.text_frame
        tf.word_wrap, tf.auto_size = True, MSO_AUTO_SIZE.NONE
        tf.margin_left = tf.margin_right = Emu(insets[0])
        tf.margin_top = tf.margin_bottom = Emu(insets[1])
        tf.vertical_anchor = {"t": MSO_ANCHOR.TOP, "ctr": MSO_ANCHOR.MIDDLE, "b": MSO_ANCHOR.BOTTOM}[anchor]
        for i, para in enumerate([paras] if isinstance(paras, str) else paras):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.alignment = {"l": PP_ALIGN.LEFT, "ctr": PP_ALIGN.CENTER, "r": PP_ALIGN.RIGHT}[align]
            if spacing and i:
                p.space_before = Pt(spacing)
            for txt, st in ([(para, {})] if isinstance(para, str) else para):
                r = p.add_run()
                r.text = txt
                f = r.font
                f.name, f.size = "Arial", Pt(st.get("size", size))
                f.bold, f.italic = st.get("bold", bold), st.get("italic", False)
                f.color.rgb = rgb(st.get("color", color))
            pPr = p._p.get_or_add_pPr()
            if bullets:                                   # small square bullet in the accent colour
                pPr.set("marL", "128016")
                pPr.set("indent", "-128016")
                etree.SubElement(etree.SubElement(pPr, qn("a:buClr")), qn("a:srgbClr")).set("val", bullets)
                etree.SubElement(pPr, qn("a:buSzPct")).set("val", "100000")
                etree.SubElement(pPr, qn("a:buFont")).set("typeface", "Arial")
                etree.SubElement(pPr, qn("a:buChar")).set("char", "▪")
            else:
                etree.SubElement(pPr, qn("a:buNone"))
        return shape

    def shape_text(self, shape, paras, **kw):
        """Text inside an autoshape (header bars, chevrons, chips): centred, bold, white by default."""
        for k, v in (("anchor", "ctr"), ("align", "ctr"), ("color", WHITE), ("bold", True)):
            kw.setdefault(k, v)
        return self._fill(shape, paras, **kw)

    def icon(self, slide, icon_id, x, y, size, white=False, px=512):
        pic = slide.shapes.add_picture(self.icons.png(icon_id, white, px), Emu(x), Emu(y), Emu(size), Emu(size))
        pic.name = f"Icon {icon_id}{'-white' if white else ''}"
        pic._element.find(qn("p:nvPicPr")).find(qn("p:cNvPr")).set("descr", f"{icon_id}.png")
        return pic

    # house patterns
    def header_card(self, slide, x, y, w, h, header, color, body=None, icon=None, icon_size=822960,
                    question=None, header_h=420624, bullet_size=10.5):
        """White card, 1 pt accent border, accent header bar; optional centred icon, question line, bullets."""
        self.rounded(slide, x, y, w, h, WHITE, color)
        hb = slide.shapes.add_shape(MSO_SHAPE.ROUND_2_SAME_RECTANGLE, Emu(x), Emu(y), Emu(w), Emu(header_h))
        self._style(hb, color, color)
        hb.adjustments[0], hb.adjustments[1] = R_CARD / min(w, header_h), 0
        self.shape_text(hb, header, size=14, insets=(INS_X, 0))
        cy = y + header_h + 137160
        if icon:
            self.icon(slide, icon, x + (w - icon_size) // 2, cy, icon_size)
            cy += icon_size + 91440
        if question:
            self.text(slide, x + 182880, cy, w - 365760, 640080, question, size=13, bold=True,
                      color=ON_LIGHT.get(color, color), align="ctr", anchor="ctr")
            cy += 731520
            self.line(slide, x + w // 8, cy, x + w - w // 8, cy)
            cy += 91440
        if body:
            self.text(slide, x + 182880, cy, w - 365760, y + h - cy - 91440, body, size=bullet_size,
                      bullets=color, spacing=3)
        return cy

    def icon_tile(self, slide, x, y, w, h, icon, title, body, dark=False, icon_size=731520,
                  title_size=13, body_size=10.5):
        """Neutral tile: icon left, bold title and grey text right. dark=True gives a chip for a dark panel."""
        self.rounded(slide, x, y, w, h, DARK2 if dark else WHITE, None if dark else BORDER, R_CHIP if dark else R_TILE)
        ix = x + 137160
        self.icon(slide, icon, ix, y + (h - icon_size) // 2, icon_size, white=dark)
        tx = ix + icon_size + 91440
        if title:
            paras = [[(title, {"size": title_size, "bold": True, "color": WHITE if dark else BLACK})],
                     [(body, {"size": body_size, "color": ON_DARK_GREY if dark else BODY_GREY})]]
        else:
            paras = [[(body, {"size": body_size, "color": WHITE if dark else BLACK})]]
        self.text(slide, tx, y + 91440, x + w - tx - 91440, h - 182880, paras, anchor="t" if title else "ctr")

    def accent_tile(self, slide, x, y, w, h, title, body, color=RED):
        """White tile with a 0.08 in accent bar on the left edge."""
        self.rounded(slide, x, y, w, h, WHITE, BORDER, R_TILE)
        self.rect(slide, x, y, 73152, h, color)
        self.text(slide, x + 164592, y + 36576, w - 210312, h - 73152,
                  [[(title, {"size": 11.5, "bold": True})], [(body, {"size": 9.5, "color": BODY_GREY})]], anchor="ctr")

    def band(self, slide, y, paras, h=658368, dark=True, size=13, x=LEFT, w=CONTENT_W, align="ctr"):
        """Full-width takeaway band. Coloured runs on the dark band use ON_DARK tints."""
        sh = self.rounded(slide, x, y, w, h, INK if dark else WHITE, None if dark else SILVER, R_CHIP)
        self.shape_text(sh, paras, size=size, color=WHITE if dark else BLACK, bold=False, align=align)
        return sh

    def chip(self, slide, x, y, w, h, text, fill, color=None, bold=True, size=9, radius=R_CELL, line=None):
        sh = self.rounded(slide, x, y, w, h, fill, line, radius)
        self.shape_text(sh, text, size=size, color=color or WHITE, bold=bold, insets=(54864, INS_Y))
        return sh

    def pill(self, slide, x, y, w, h, text, color=RED):
        return self.chip(slide, x, y, w, h, text, color, WHITE, size=7, radius=h // 2)

    def chevrons(self, slide, y, steps, h=868680, x0=LEFT, width=CONTENT_W, gap=-18288, label_size=9, name_size=12.5):
        """Process row: pentagon first, chevrons after. steps: [(kicker, name, color)]. Returns [(x, w)]."""
        n = len(steps)
        w = int((width - gap * (n - 1)) / n)
        out = []
        for i, (lab, name, color) in enumerate(steps):
            x = x0 + i * (w + gap)
            sh = slide.shapes.add_shape(MSO_SHAPE.PENTAGON if i == 0 else MSO_SHAPE.CHEVRON, Emu(x), Emu(y), Emu(w), Emu(h))
            self._style(sh, color, None)
            sh.adjustments[0] = 0.22
            paras = ([[(lab, {"size": label_size})]] if lab else []) + [[(name, {"size": name_size})]]
            self.shape_text(sh, paras, insets=(274320 if i else 91440, 0))
            sh.text_frame.margin_right = Emu(201168)
            out.append((x, w))
        return out

    def tracker(self, slide, steps, active=None, label="", colors=STEP_COLORS, right=11859768, y=329184,
                w=750000, pitch=715000, h=274320):
        """Compact step tracker top right beside the title. active: 1-based step, or None to light all.
        Titles must stay short enough (about 52 characters at 28 pt) not to run under it."""
        x0 = right - (w + pitch * (len(steps) - 1))
        for i, st in enumerate(steps):
            lit = active is None or active == i + 1
            sh = slide.shapes.add_shape(MSO_SHAPE.PENTAGON if i == 0 else MSO_SHAPE.CHEVRON,
                                        Emu(x0 + i * pitch), Emu(y), Emu(w), Emu(h))
            self._style(sh, colors[i % len(colors)] if lit else BORDER, None)
            sh.adjustments[0] = 0.35
            self.shape_text(sh, st, size=7, color=WHITE if lit else GREY, insets=(109728 if i else 36576, 0))
            sh.text_frame.margin_right, sh.text_frame.word_wrap = Emu(54864), False
        if label:
            self.text(slide, x0 - 566928, y, 548640, h, label, size=8, bold=True, color=GREY, align="r",
                      anchor="ctr", insets=(0, 0))
        return x0

    def chip_table(self, slide, y, columns, rows_, header_h=384048, row_h=420624, col_gap=54864, row_gap=73152,
                   x0=LEFT, width=CONTENT_W, label_col=True):
        """Table built from chips. columns: [(header, weight)]. A cell is a str (neutral grey chip),
        (text, ACCENT) for a tinted chip, or (text, ACCENT, 'solid') for a filled one. Returns next y."""
        cx = cols(len(columns), gap=col_gap, x0=x0, width=width, weights=[wt for _, wt in columns])
        for (hdr, _), (x, w) in zip(columns, cx):
            self.chip(slide, x, y, w, header_h, hdr, INK, size=10.5)
        yy = y + header_h + row_gap
        for r in rows_:
            for j, (cell, (x, w)) in enumerate(zip(r, cx)):
                if j == 0 and label_col:
                    sh = self.rounded(slide, x, yy, w, row_h, WHITE, BORDER, R_CELL)
                    self.shape_text(sh, cell, size=11, color=BLACK, align="l", insets=(109728, 0))
                elif isinstance(cell, tuple) and len(cell) > 2 and cell[2] == "solid":
                    self.chip(slide, x, yy, w, row_h, cell[0], cell[1], WHITE, size=9.5)
                elif isinstance(cell, tuple):
                    self.chip(slide, x, yy, w, row_h, cell[0], TINT[cell[1]], TINT_TEXT[cell[1]], size=9.5,
                              bold=cell[1] in (RED, PURPLE, BLUE))
                else:
                    self.chip(slide, x, yy, w, row_h, cell, TINT[GREY], BODY_GREY, bold=False, size=9.5)
            yy += row_h + row_gap
        return yy

    def step_rows(self, slide, x, y, w, items, h=868680, gap=118872, num_w=960120, icon_size=566928):
        """Numbered rows: coloured number square, text, optional icon right. items: (kicker, number, text, color, icon)."""
        for i, (lab, num, txt, color, ic) in enumerate(items):
            yy = y + i * (h + gap)
            self.rounded(slide, x, yy, w, h, WHITE, BORDER, R_CHIP)
            self.shape_text(self.rounded(slide, x, yy, num_w, h, color, None, R_CHIP),
                            [[(lab, {"size": 8})], [(str(num), {"size": 18})]])
            tw = w - num_w - 274320 - (icon_size + 274320 if ic else 0)
            self.text(slide, x + num_w + 137160, yy, tw, h, txt, size=12, anchor="ctr")
            if ic:
                self.icon(slide, ic, x + w - icon_size - 137160, yy + (h - icon_size) // 2, icon_size)

    def quote_panel(self, slide, x, y, w, h, quote, attribution="", note=""):
        self.rounded(slide, x, y, w, h, INK, None, R_CARD)
        self.text(slide, x + 182880, y - 45720, 914400, 914400, "“", size=72, bold=True, color=RED)
        paras = [[(quote, {"size": 16, "color": WHITE})]]
        if note:
            paras.append([(note, {"size": 13, "color": ON_DARK_GREY})])
        if attribution:
            paras.append([(attribution, {"size": 9.5, "color": SILVER})])
        self.text(slide, x + 320040, y + 457200, w - 640080, h - 640080, paras, anchor="ctr", spacing=8)

    def numbered_card(self, slide, x, y, w, h, number, kicker, title, body, color, icon=None, icon_size=822960):
        """Accent-bordered card: numbered circle, kicker and title, centred icon, centred grey text."""
        self.rounded(slide, x, y, w, h, WHITE, color)
        d = 457200
        self.circle(slide, x + 182880, y + 182880, d, color)
        self.text(slide, x + 182880, y + 182880, d, d, str(number), size=16, bold=True, color=WHITE, align="ctr",
                  anchor="ctr", insets=(0, 0))
        self.text(slide, x + 274320 + d, y + 137160, w - d - 457200, 548640,
                  [[(kicker, {"size": 8, "bold": True, "color": ON_LIGHT.get(color, color)})],
                   [(title, {"size": 14, "bold": True})]], anchor="ctr")
        cy = y + 411480 + d
        if icon:
            self.icon(slide, icon, x + (w - icon_size) // 2, cy, icon_size)
            cy += icon_size + 137160
        self.text(slide, x + 182880, cy, w - 365760, y + h - cy - 137160, body, size=11, color=BODY_GREY, align="ctr")

    def icon_row(self, slide, x, y, w, items, icon_size=502920, label_size=8.5, white=False, label_h=329184):
        """Row of icons with centred labels underneath, e.g. products per zone. items: [(icon_id, label)]."""
        cell = w / len(items)
        for i, (ic, label) in enumerate(items):
            cxm = x + cell * i + cell / 2
            self.icon(slide, ic, int(cxm - icon_size / 2), y, icon_size, white=white)
            self.text(slide, int(cxm - cell / 2), y + icon_size + 45720, int(cell), label_h, label, size=label_size,
                      color=WHITE if white else BLACK, align="ctr", anchor="t", insets=(0, 0))

    def dark_panel(self, slide, x, y, w, h, title, sub=None):
        """INK panel with white title and grey sub line; put icon_tile(..., dark=True) chips inside."""
        self.rounded(slide, x, y, w, h, INK, None, R_TILE)
        paras = [[(title, {"size": 14, "bold": True, "color": WHITE})]]
        if sub:
            paras.append([(sub, {"size": 10.5, "color": ON_DARK_GREY})])
        self.text(slide, x + 283464, y + 73152, w - 566928, 777240, paras)

    def footnote(self, slide, text, x=868680, w=8686800):
        """Source line bottom left. Only when the user explicitly asks for sources in the deck."""
        self.text(slide, x, FOOTNOTE_Y, w, 201168, text, size=7.5, color=MUTED, insets=(0, 0))


SOURCE_RE = re.compile(r"(\b(Quelle|Quellen|Source|Sources)\s*:|docs\.fortinet\.com|https?://|Ordering Guide|"
                       r"Deployment Guide|Administration Guide|Reference Guide|FSS-OG-)", re.I)


def lint(pptx_path, sources_ok=False):
    """House-rule checks. Prints and returns a list of warnings; run before rendering.
    sources_ok=True only when the user explicitly asked for sources in the deck."""
    p, out = Presentation(pptx_path), []
    for i, s in enumerate(p.slides, 1):
        for sh in s.shapes:
            if sh.is_placeholder and sh.placeholder_format.type is not None and "TITLE" in str(sh.placeholder_format.type):
                if sh._element.find(qn("p:spPr")).find(qn("a:xfrm")) is not None:
                    out.append(f"slide {i}: title placeholder has its own xfrm (geometry override), remove it")
            if sh.shape_type != 14 and sh.top is not None:          # non-placeholders
                if sh.left < 0 or sh.top < 0 or sh.left + sh.width > SLIDE_W + 1000 or sh.top + sh.height > SLIDE_H:
                    out.append(f"slide {i}: '{sh.name}' runs off the slide")
                elif sh.top + sh.height > BOTTOM + 91440 and sh.top < FOOTNOTE_Y - 91440:
                    out.append(f"slide {i}: '{sh.name}' goes below the content area (BOTTOM)")
            if sh.has_text_frame:
                t = sh.text_frame.text
                if "—" in t or "·" in t or "• " in t:
                    out.append(f"slide {i}: '{sh.name}' contains an em dash, middle dot or literal bullet")
                if not sources_ok and SOURCE_RE.search(t):
                    out.append(f"slide {i}: '{sh.name}' contains a source or document reference (not requested)")
                for r in sh._element.iter(qn("a:rPr")):
                    lat = r.find(qn("a:latin"))
                    if lat is not None and lat.get("typeface") not in (None, "Arial"):
                        out.append(f"slide {i}: '{sh.name}' uses font {lat.get('typeface')}")
            for c in sh._element.iter(qn("a:srgbClr")):
                if c.get("val").upper() not in PALETTE:
                    out.append(f"slide {i}: '{sh.name}' uses off-palette colour {c.get('val')}")
        if s.slide_layout.name in ("Title Only", "Title Subtitle") and not (s.has_notes_slide and s.notes_slide.notes_text_frame.text.strip()):
            out.append(f"slide {i}: no speaker notes")
        if not sources_ok and s.has_notes_slide and SOURCE_RE.search(s.notes_slide.notes_text_frame.text):
            out.append(f"slide {i}: speaker notes contain a source or document reference (not requested)")
    for w in sorted(set(out)):
        print("LINT", w)
    return out
```

## Helper library, part 2 (write this block to ftnt_modern.py)

The modern layer: `grad`, `shadow`, `DARK`, `LIGHT_END` and `ModernDeck` (gradient `rounded`,
`header_card` with badge and inner panel, `badge`, `wbadge`, `gbox`, dark pill `band`, blue table
headers, gradient chevrons and tracker). Always build with `ModernDeck`.

```python
"""ftnt_modern.py - modern variant of the Fortinet house style.

Same template, grid, type scale and palette as ftnt_deck.py, plus the design language of the current
Fortinet corporate decks: accent gradients inside cards,
soft drop shadows instead of 1 pt borders, white inner panels in gradient cards, and icon badges
(white circles) sitting on the top edge of a card."""
from ftnt_deck import *
from ftnt_deck import PALETTE
from pptx.oxml.ns import qn
from lxml import etree

# darker gradient stops (HLS luminance x 0.72, like lumMod 75 % in the Fortinet decks)
DARK = {RED: "9D1E14", BLUE: "185AAD", PURPLE: "6535A6", TEAL: "209398", GREEN: "2B7F5B",
        YELLOW: "B88500", GREY: "545659", INK: "1E1E1E", SILVER: "7F90A8"}
LIGHT_END = {TINT[BLUE]: "EEF4FC", TINT[PURPLE]: "F5F0FA", TINT[YELLOW]: "FFF8E5", TINT[RED]: "FCEBEA",
             TINT[TEAL]: "EDFBFB", TINT[GREEN]: "EEF8F3", TINT[GREY]: "F4F4F5"}
INK_TOP = "3A3A3A"
ACCENTS = set(DARK)
PALETTE.update(DARK.values())
PALETTE.update(LIGHT_END.values())
PALETTE.update([INK_TOP, "7F90A8"])


def _clear_fill(spPr):
    for tag in ("a:solidFill", "a:gradFill", "a:noFill", "a:pattFill", "a:blipFill"):
        for e in spPr.findall(qn(tag)):
            spPr.remove(e)


def grad(shape, c1, c2, ang=4200000):
    """Two-stop linear gradient, light (c1) top-left to dark (c2) bottom-right."""
    spPr = shape._element.spPr
    _clear_fill(spPr)
    g = etree.Element(qn("a:gradFill"))
    g.set("rotWithShape", "1")
    lst = etree.SubElement(g, qn("a:gsLst"))
    for pos, c in ((0, c1), (100000, c2)):
        gs = etree.SubElement(lst, qn("a:gs"))
        gs.set("pos", str(pos))
        etree.SubElement(gs, qn("a:srgbClr")).set("val", c)
    lin = etree.SubElement(g, qn("a:lin"))
    lin.set("ang", str(ang))
    lin.set("scaled", "0")
    geom = spPr.find(qn("a:prstGeom"))
    if geom is None:
        geom = spPr.find(qn("a:custGeom"))
    geom.addnext(g)
    return shape


def shadow(shape, blur=228600, dist=76200, alpha=22000, size=98000):
    """Soft drop shadow straight down, as used on the cards of the Fortinet sales decks."""
    spPr = shape._element.spPr
    eff = spPr.find(qn("a:effectLst"))
    if eff is None:
        eff = etree.SubElement(spPr, qn("a:effectLst"))
    for ch in list(eff):
        eff.remove(ch)
    sh = etree.SubElement(eff, qn("a:outerShdw"))
    for k, v in (("blurRad", blur), ("dist", dist), ("dir", 5400000), ("sx", size), ("sy", size),
                 ("algn", "t"), ("rotWithShape", "0")):
        sh.set(k, str(v))
    clr = etree.SubElement(sh, qn("a:prstClr"))
    clr.set("val", "black")
    etree.SubElement(clr, qn("a:alpha")).set("val", str(alpha))
    return shape


class ModernDeck(FortiDeck):
    CARD_R = 164592            # 0.18 in, a little rounder than the classic cards

    # ---------------------------------------------------------------- primitives
    def rounded(self, slide, x, y, w, h, fill=WHITE, line=BORDER, radius=R_CARD, shade=None, ang=4200000):
        """Accent fills become gradients, white cards lose the grey border and get a soft shadow,
        tints become a gentle tint-to-lighter gradient. shade: None = auto (cards >= 0.55 in high)."""
        sh = super().rounded(slide, x, y, w, h, fill, line, radius)
        big = h >= 502920 and w >= 822960
        if fill in ACCENTS:
            grad(sh, INK_TOP if fill == INK else fill, DARK[fill], ang)
        elif fill in LIGHT_END:
            grad(sh, fill, LIGHT_END[fill], 5400000)
        if fill == WHITE and line == BORDER:
            sh.line.fill.background()
        if fill == LIGHT and line in (BORDER, None):
            sh.fill.solid()
            sh.fill.fore_color.rgb = rgb(WHITE)
            sh.line.fill.background()
        if shade or (shade is None and big and fill not in LIGHT_END):
            shadow(sh)
        return sh

    def rect(self, slide, x, y, w, h, fill, line=None):
        sh = super().rect(slide, x, y, w, h, fill, line)
        if fill in ACCENTS:
            grad(sh, fill, DARK[fill], 5400000)
        return sh

    def circle(self, slide, x, y, d, fill, line=None, line_w=12700):
        sh = super().circle(slide, x, y, d, fill, line, line_w)
        if fill in ACCENTS:
            grad(sh, fill, DARK[fill], 4200000)
        return sh

    def arrow(self, slide, x, y, w=173736, h=219456, color=RED):
        sh = super().arrow(slide, x, y, w, h, color)
        if color in ACCENTS:
            grad(sh, color, DARK[color], 0)
        return sh

    def badge(self, slide, cx, cy, d, icon, ring=BLUE, icon_ratio=0.62):
        """White circle with an accent ring and soft shadow, icon centred: sits on a card edge."""
        c = super().circle(slide, cx - d // 2, cy - d // 2, d, WHITE, ring, 28575)
        shadow(c, blur=152400, dist=38100, alpha=30000)
        isz = int(d * icon_ratio)
        self.icon(slide, icon, cx - isz // 2, cy - isz // 2, isz)
        return c

    # ---------------------------------------------------------------- patterns
    def header_card(self, slide, x, y, w, h, header, color, body=None, icon=None, icon_size=822960,
                    question=None, header_h=420624, bullet_size=10.5):
        """Gradient card. With icon: white badge on the top edge, white title under it. Without icon:
        white title in the top band. Question in the light tint colour, then a white inner panel."""
        if icon:
            d = min(int(icon_size * 1.3), 1188720)
            top = y + d // 2
            self.rounded(slide, x, top, w, y + h - top, color, None, self.CARD_R, shade=True)
            self.badge(slide, x + w // 2, top, d, icon, ring=color)
            ty = top + d // 2 + 54864
            th = 420624
        else:
            self.rounded(slide, x, y, w, h, color, None, self.CARD_R, shade=True)
            ty, th = y, header_h
        tcol = INK if color == YELLOW else WHITE
        self.text(slide, x + 91440, ty, w - 182880, th, header, size=14, bold=True, color=tcol, align="ctr",
                  anchor="ctr")
        cy = ty + th
        if question:
            self.text(slide, x + 137160, cy - 18288, w - 274320, 457200, question, size=11.5, bold=False,
                      color=INK if color == YELLOW else TINT[color], align="ctr", anchor="ctr")
            cy += 438912
        pad = 109728
        py = cy + 36576
        panel_h = y + h - pad - py
        if body is not None or not icon:
            self.rounded(slide, x + pad, py, w - 2 * pad, panel_h, WHITE, None, R_TILE, shade=False)
        if body:
            self.text(slide, x + pad + 118872, py + 91440, w - 2 * pad - 237744, panel_h - 137160, body,
                      size=bullet_size, bullets=color if color != YELLOW else DARK[YELLOW], spacing=4)
        return py

    def icon_tile(self, slide, x, y, w, h, icon, title, body, dark=False, icon_size=731520,
                  title_size=13, body_size=10.5):
        """White shadowed tile. dark=True (inside a gradient panel): white row, no shadow."""
        self.rounded(slide, x, y, w, h, WHITE, None, R_TILE if not dark else R_CHIP, shade=not dark)
        ix = x + 137160
        self.icon(slide, icon, ix, y + (h - icon_size) // 2, icon_size)
        tx = ix + icon_size + 109728
        if title:
            paras = [[(title, {"size": title_size, "bold": True, "color": BLACK})],
                     [(body, {"size": body_size, "color": BODY_GREY})]]
        else:
            paras = [[(body, {"size": body_size, "color": BLACK})]]
        self.text(slide, tx, y + 91440, x + w - tx - 91440, h - 182880, paras, anchor="t" if title else "ctr")

    def dark_panel(self, slide, x, y, w, h, title, sub=None, color=BLUE):
        """Former INK panel: now an accent gradient card with white title; rows are white chips."""
        self.rounded(slide, x, y, w, h, color, None, self.CARD_R, shade=True)
        paras = [[(title, {"size": 14, "bold": True, "color": WHITE})]]
        if sub:
            paras.append([(sub, {"size": 10.5, "color": TINT[color]})])
        self.text(slide, x + 283464, y + 73152, w - 566928, 777240, paras)

    def accent_tile(self, slide, x, y, w, h, title, body, color=RED):
        self.rounded(slide, x, y, w, h, WHITE, BORDER, R_TILE, shade=True)
        bar = super().rounded(slide, x + 73152, y + 118872, 54864, h - 237744, color, None, 27432)
        grad(bar, color, DARK[color], 5400000)
        self.text(slide, x + 182880, y + 36576, w - 228600, h - 73152,
                  [[(title, {"size": 11.5, "bold": True})], [(body, {"size": 9.5, "color": BODY_GREY})]], anchor="ctr")

    def band(self, slide, y, paras, h=658368, dark=True, size=13, x=LEFT, w=CONTENT_W, align="ctr"):
        if dark:
            sh = super().rounded(slide, x, y, w, h, INK, None, h // 2)
            grad(sh, INK_TOP, INK, 0)
            shadow(sh, blur=203200, dist=63500, alpha=25000)
        else:
            sh = super().rounded(slide, x, y, w, h, WHITE, None, h // 2)
            shadow(sh, blur=203200, dist=63500, alpha=18000)
        self.shape_text(sh, paras, size=size, color=WHITE if dark else BLACK, bold=False, align=align,
                        insets=(274320, 0))
        return sh

    def chip(self, slide, x, y, w, h, text, fill, color=None, bold=True, size=9, radius=R_CELL, line=None):
        sh = self.rounded(slide, x, y, w, h, fill, line, radius, shade=False)
        if fill == WHITE and line == BORDER:
            shadow(sh, blur=76200, dist=19050, alpha=18000)
        self.shape_text(sh, text, size=size, color=color or WHITE, bold=bold, insets=(54864, INS_Y))
        return sh

    def pill(self, slide, x, y, w, h, text, color=RED):
        return self.chip(slide, x, y, w, h, text, color, INK if color == YELLOW else WHITE, size=7, radius=h // 2)

    def chip_table(self, slide, y, columns, rows_, header_h=384048, row_h=420624, col_gap=54864, row_gap=73152,
                   x0=LEFT, width=CONTENT_W, label_col=True):
        cx = cols(len(columns), gap=col_gap, x0=x0, width=width, weights=[wt for _, wt in columns])
        for (hdr, _), (x, w) in zip(columns, cx):
            self.chip(slide, x, y, w, header_h, hdr, BLUE, size=10.5)
        yy = y + header_h + row_gap
        for r in rows_:
            for j, (cell, (x, w)) in enumerate(zip(r, cx)):
                if j == 0 and label_col:
                    sh = self.rounded(slide, x, yy, w, row_h, WHITE, None, R_CELL, shade=False)
                    shadow(sh, blur=76200, dist=19050, alpha=18000)
                    self.shape_text(sh, cell, size=11, color=BLACK, align="l", insets=(109728, 0))
                elif isinstance(cell, tuple) and len(cell) > 2 and cell[2] == "solid":
                    self.chip(slide, x, yy, w, row_h, cell[0], cell[1], INK if cell[1] == YELLOW else WHITE, size=9.5)
                elif isinstance(cell, tuple):
                    self.chip(slide, x, yy, w, row_h, cell[0], TINT[cell[1]], TINT_TEXT[cell[1]], size=9.5,
                              bold=cell[1] in (RED, PURPLE, BLUE))
                else:
                    self.chip(slide, x, yy, w, row_h, cell, WHITE, BODY_GREY, bold=False, size=9.5)
            yy += row_h + row_gap
        return yy

    def numbered_card(self, slide, x, y, w, h, number, kicker, title, body, color, icon=None, icon_size=822960):
        """White shadowed card, gradient number circle, kicker and title, icon badge ringed in the accent."""
        self.rounded(slide, x, y, w, h, WHITE, BORDER, self.CARD_R, shade=True)
        d = 457200
        self.circle(slide, x + 182880, y + 228600, d, color)
        self.text(slide, x + 182880, y + 228600, d, d, str(number), size=16, bold=True,
                  color=INK if color == YELLOW else WHITE, align="ctr", anchor="ctr", insets=(0, 0))
        self.text(slide, x + 274320 + d, y + 182880, w - d - 457200, 548640,
                  [[(kicker, {"size": 8, "bold": True, "color": ON_LIGHT.get(color, color)})],
                   [(title, {"size": 14, "bold": True})]], anchor="ctr")
        cy = y + 457200 + d
        if icon:
            bd = int(icon_size * 1.25)
            self.badge(slide, x + w // 2, cy + bd // 2, bd, icon, ring=color)
            cy += bd + 137160
        self.text(slide, x + 182880, cy, w - 365760, y + h - cy - 137160, body, size=11, color=BODY_GREY, align="ctr")

    def chevrons(self, slide, y, steps, h=868680, x0=LEFT, width=CONTENT_W, gap=-18288, label_size=9, name_size=12.5):
        n0 = len(slide.shapes)
        out = super().chevrons(slide, y, steps, h, x0, width, gap, label_size, name_size)
        for sh, (_, _, c) in zip(list(slide.shapes)[n0:], steps):
            grad(sh, c, DARK[c], 0)
        return out

    def tracker(self, slide, steps, active=None, label="", colors=STEP_COLORS, right=11859768, y=329184,
                w=750000, pitch=715000, h=274320):
        x0 = super().tracker(slide, steps, active, label, colors, right, y, w, pitch, h)
        # gradient on the lit chevrons
        for sh in slide.shapes:
            if sh.shape_type == 1 and sh.top == y and sh.height == h and sh.left >= x0 - 10:
                fc = sh.fill.fore_color.rgb if sh.fill.type == 1 else None
                if fc is not None and str(fc) in DARK:
                    grad(sh, str(fc), DARK[str(fc)], 0)
        return x0

    # ---------------------------------------------------------------- diagram building blocks
    def wbadge(self, slide, x, y, size, icon):
        """White circle without ring, coloured icon inside, top-left at x, y. Use it for icons on gradient
        fills: the white line icons of the library are too faint on gradients."""
        return self.badge(slide, x + size // 2, y + size // 2, size, icon, ring=WHITE, icon_ratio=0.66)

    def gbox(self, slide, x, y, w, h, color, icon, t1, t2, icons=1, isz=502920, dark_text=False):
        """Architecture building block: gradient box, white badge(s) with the icon, white title and a
        tinted sub line. icon can be a list for several badges (e.g. FortiManager + FortiAnalyzer).
        Boxes >= 1.2 in high keep the icon and text in the top 0.7 in (room for chips below)."""
        self.rounded(slide, x, y, w, h, color, None, R_TILE, shade=True)
        tall = h >= 1097280
        for k in range(icons):
            ic = icon[k] if isinstance(icon, (list, tuple)) else icon
            self.wbadge(slide, x + 91440 + k * int(isz * 0.8), y + 91440 if tall else y + (h - isz) // 2, isz, ic)
        tx = x + 182880 + int(isz * 0.8) * (icons - 1) + isz
        self.text(slide, tx, y + 45720, x + w - tx - 45720, 566928 if tall else h - 91440,
                  [[(t1, {"size": 10.5, "bold": True, "color": INK if dark_text else WHITE})],
                   [(t2, {"size": 8.5, "color": BODY_GREY if dark_text else TINT.get(color, WHITE)})]], anchor="ctr")
```

### Worked example (tested: renders cleanly, `lint` returns no warnings, `validate.py` passes)

```python
from ftnt_modern import *
d = ModernDeck("<skill dir>/assets/FTNT_PPT_16x9_Light_Template.pptx", icon_cache="icon_cache")
I = lambda v: int(v * 914400)
STEPS = ["Criteria", "Build", "Test", "Review"]

d.title_slide("Secure SD-WAN and SASE", "Solution proposal and PoC approach\nName, Systems Engineer, Month Year")
d.agenda(["Starting point", "Target architecture", "PoC approach", "Next steps"])
d.section("Target architecture", "SD-WAN hubs in the cloud, SASE for remote users", variant=2)

# 1 gradient header cards with icon badges and white inner panels
s, top = d.content("Four design principles")
for (x, w), (hdr, c, ic, q, items) in zip(cols(4), [
        ("One site building block", RED, "Secure-SD-WAN", "Every site, one design", ["FortiGate at every site", "Zero touch provisioning"]),
        ("Hubs close to the cloud", BLUE, "Azure-vWAN", "Close to the workloads", ["FortiGate-VM in the vWAN hub", "Two instances per hub"]),
        ("Security follows the user", PURPLE, "FortiSASE Cloud", "Office, home, on the road", ["FortiSASE for remote users", "Private access via the hubs"]),
        ("One management", TEAL, "FortiManager", "One cockpit", ["FortiManager and FortiAnalyzer", "FortiAI for operations"])]):
    d.header_card(s, x, top + I(0.05), w, I(3.85), hdr, c, body=items, icon=ic, icon_size=I(0.9), question=q, bullet_size=11.5)
d.band(s, top + I(4.15), [[("One building block, one policy, one management: ", {"bold": True}),
                          ("from the plant to the home office.", {"bold": True, "color": ON_DARK[RED]})]], h=I(0.72), size=14)
d.notes(s, "Four principles behind the design.")

# 2 architecture building blocks: tinted zone panel, gradient boxes with white badges, lines first
s, top = d.content("Target architecture at a glance")
zx, zy, zw, zh = LEFT, I(1.32), I(8.9), I(1.72)
d.rounded(s, zx, zy, zw, zh, TINT[BLUE], None, d.CARD_R)
d.text(s, zx + I(0.15), zy + I(0.04), I(4), I(0.25), "MICROSOFT AZURE, VIRTUAL WAN", size=8, bold=True, color=TINT_TEXT[BLUE], insets=(0, 0))
hx = [zx + I(0.2) + i * I(2.93) for i in range(3)]
for x in hx:                                             # lines before boxes
    d.line(s, x + I(0.55), zy + I(1.63), x + I(0.55), I(4.72), RED, w=28575)
for x, name in zip(hx, ["Region A", "Region B", "Region C"]):
    d.gbox(s, x, zy + I(0.33), I(2.6), I(1.3), BLUE, "Azure-vWAN", "Hub " + name, "2x FortiGate-VM (NVA)")
    for j, v in enumerate(["PROD vNET", "DEV vNET"]):
        d.chip(s, x + I(0.12) + j * I(1.21), zy + I(1.19), I(1.13), I(0.3), v, WHITE, TINT_TEXT[BLUE], size=8)
for x, reg in zip(hx, ["Region A", "Region B", "Region C"]):
    d.gbox(s, x, I(4.72), I(2.6), I(1.05), RED, "Branch-Office", f"{reg}: sites", "FortiGate, UTP", isz=I(0.6))
d.gbox(s, I(9.6), I(1.65), RIGHT - I(9.6), I(0.95), TEAL, ["FortiManager", "FortiAnalyzer"], "Management",
       "FortiManager, FortiAnalyzer", icons=2, isz=I(0.5))
d.notes(s, "Architecture overview.")

# 3 chip table with blue gradient header
s, top = d.content("Scope at a glance", "Quantities per building block")
yy = d.chip_table(s, top + I(0.05), [("Building block", 1.4), ("Component", 2.1), ("Quantity", 1.3), ("Services", 2.6)], [
    ["Hub", "FortiGate-VM", ("4 instances", BLUE), "UTP"],
    ["Sites", "FortiGate", ("20 units", RED), "UTP"],
    ["Remote users", "FortiSASE", ("250 users", PURPLE), ("Advanced", PURPLE, "solid")]], row_h=I(0.45))
d.notes(s, "Scope without prices.")

# 4 PoC: tracker, numbered cards with badges, accent tiles
s, top = d.content("Three PoC tracks")
d.tracker(s, STEPS, active=None, label="PoC")
for (x, w), (n, k, t, ic, b, c) in zip(cols(3), [(1, "TRACK", "SD-WAN PoC", "Secure-SD-WAN", "Pilot sites with loan units.", RED),
                                                 (2, "TRACK", "SASE PoC", "FortiSASE Cloud", "Test users with FortiClient.", PURPLE),
                                                 (3, "SEPARATE", "Optional PoC", "Partnerships", "Scoped separately.", YELLOW)]):
    d.numbered_card(s, x, top + I(0.1), w, I(2.85), n, k, t, b, c, icon=ic, icon_size=I(0.7))
for (x, w), (t, b) in zip(cols(4), [("2 months", "Kick-off to decision."), ("Pilot sites", "Selected sites only."),
                                    ("Loan hardware", "Returned after the PoC."), ("Criteria first", "No start without them.")]):
    d.accent_tile(s, x, top + I(3.15), w, I(0.95), t, b, RED)
d.band(s, top + I(4.3), [[("Fortinet supports the PoC actively.", {"bold": True})]], h=I(0.62))
d.notes(s, "PoC tracks.")
d.closing()
d.save("example.pptx")
print(lint("example.pptx"))
```