# Fortinet brand spec

Extracted from `assets/FTNT_PPT_16x9_Light_Template.pptx` — slide 1 of that file is Fortinet's own
official color reference (RGB/CMYK/Pantone), which is more authoritative than the raw theme XML.

## Named color palette

| Name | Hex | Pantone |
|---|---|---|
| Secure Red | `DA291C` | PMS 485 |
| Cloud Blue | `307FE2` | PMS 2727 |
| SASE Purple | `9063CD` | PMS 265 |
| Connectivity Yellow | `FFB900` | PMS 7548 |
| SecOps Teal | `2CCCD3` | PMS 319 |
| Fabric Silver | `A2B2C8` | PMS 2155 |
| FortiGuard Green | `3CB17E` | PMS 7724 |
| OT Grey | `75787B` | PMS Cool Gray 9 |

Neutrals: black `000000`, white `FFFFFF`, grey `B3B3B3`, light grey `F0F0F0`, hyperlink blue `0081E9`.

## Typography

- **Font: Arial** throughout, no custom typeface. It's on the safe-font list, so text-fit checks during
  visual QA are reliable — no extra size slack needed.
- Title slide: title 44pt bold, bottom-aligned, max 2 lines. Subtitle 20pt, `R127 G127 B127` grey,
  top-aligned, max 2 lines.
- Slide title (content layouts): bold, top-left, roughly 32-36pt.

## Layout and background rules

- Light layouts sit on an off-white grey (`F0F0F0`-ish), not pure white. Dark layouts (Title Slide Dark,
  Four Cards Dark, Closing Slide Dark) use near-black.
- Every slide carries the Fortinet brick-mark logo and a `© Fortinet Inc. All Rights Reserved.` footer
  with a page number.

## The recurring visual motif — reuse this, don't invent a new one

Short red rectangle accent blocks (roughly 1.5-2" wide, never full-width stripes) scattered near corners,
plus a large rounded-square grid and a small dot-grid pattern used as a background watermark on title,
section, and closing slides. This is Fortinet's actual brand identity, carried consistently across all 37
layouts in the template.

If you're used to generic slide-design guidance that says "never use accent stripes or color bars" —
that rule is for freehand designs with no template to anchor to. It does not apply here. These short red
blocks and the grid/dot watermark are the real Fortinet motif; keep them when building from this template,
and don't strip them out or replace them with something else.

## Available slide layouts (37 total — pick by content shape, don't invent a new one)

Title Slide (Light/Dark), Agenda, Section Header 1/2, Title Only, Title Subtitle, Blank,
Title and Content (with/without bullets, with subtitle), Two/Three Content (plain or with headers),
Chart with Content, Chart with Caption, Three Charts with Headers, Picture and Content,
Two/Three/Four Pictures with Captions, Two/Three/Four Panels (plain or with Images/Icons),
Process, Process with Images, Three/Four/Eight Cards (Four Cards has a Dark variant),
Quadrant Cards, Closing Slide (Light/Dark).

Match the layout to what the slide is actually saying: a 3-point comparison → Three Cards; a metric
breakdown → Chart with Content; a network/architecture visual → Picture and Content or Two Panels;
a roadmap → Process or Process with Images.

## What NOT to do

- Don't invent new colors outside the palette above.
- Don't switch fonts away from Arial.
- Don't reduce the deck to plain title+bullets when a card/panel/process layout fits the content better —
  the whole point of this template is that Fortinet already solved that layout problem.
- Don't treat the 55 slides in the template file itself as real content — most of them are labeled
  example/spec slides (one per layout), not something to present as-is. Use them as a layout reference,
  build actual content into fresh slides using the matching layout.
