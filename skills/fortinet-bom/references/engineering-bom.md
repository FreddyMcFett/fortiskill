# Engineering BOM — layout specification

One workbook, typically three sheets:
`BOM` (main), optional option-variant BOM sheets, and `Kosten pro Standort` (per-site CAPEX/OPEX).

## Sheet "BOM"

### Header block (rows 1–6)

| Row | Content |
|-----|---------|
| 1 | `FORTINET  •  BILL OF MATERIALS` — Arial 15 bold, Fortinet red `DA291C` |
| 2 | Subtitle: `<Kunde> – <Projekt>  ·  <Scope>  ·  Laufzeit <n> Jahre` — Arial 11 bold, `23252A` |
| 3 | `Kunde:` / value / `Ersteller:` / value (labels bold Arial 10, values regular) |
| 4 | `Projekt:` / value / `Stand:` / ISO date |
| 5 | `Version:` / value / `Bundle:` / e.g. `ATP durchgängig · VM-S Subscriptions · alle 5 J` |
| 6 | `Region:` / value / `Währung:` / e.g. `USD – Listenpreis Q2-2026 (Recommended), exkl. Rabatt/MwSt.` |

### Column layout (header row 8, freeze panes at A9)

| Col | Header | Width | Notes |
|-----|--------|-------|-------|
| A | Pos | 5 | integer for HW lines, empty for service lines, `O1…` in option blocks |
| B | SKU | 24 | HW SKU bold Arial 9; service SKU regular Arial 9, gray `555E6B` |
| C | Beschreibung | 93.5 | Arial 9; technical: interfaces, throughput class, storage, licencing scope |
| D | Rolle / Standort | 40 | where and why; service lines: `↳ <Service> zu <Gerät>` |
| E, F | `Menge\n<Region1>`, `Menge\n<Region2>` | 8 | one column per region; adapt count to project |
| G | `Menge\nTotal` | 9 | **formula** `=E10+F10` |
| H | `Stückpreis\n(USD)` | 15 | number format `#,##0.00`, right-aligned |
| I | `Total\n(USD)` | 17 | **formula** `=G10*H10`, bold |
| J | Bemerkung | 40 | Arial 8, gray `8A929E` — deltas vs. previous version (`NEU`, `von 2 auf 1 reduziert`), design notes |

Header row: Arial 10 bold white on `23252A`, centered, wrap text, row height 30.

### Body structure

- **Section rows**: one merged-look row per architecture domain, lettered:
  `A  —  RECHENZENTREN …`, `B  —  CLOUD …`, `C  —  ZENTRALES MANAGEMENT …`,
  `D  —  STANDORTE: FortiGate Spokes`, `E — Switching`, `F — 4G/5G-Konnektivität`, `G — Wireless`.
  Style: Arial 10 bold `23252A` on light gray `E9ECF1`, spans all columns (apply fill A:J).
- **Line-item pairs**: hardware row (numbered Pos) immediately followed by its service row (no Pos, `↳` in column D, same quantities). Subscriptions (VM-S, FGT-VM BYOL sub) are a single row — the sub includes support.
- Group identical hardware that serves different roles into separate positions when quantities/roles differ (e.g. FG-50G for small vs. large sites) — this keeps the per-site math auditable.

### Grand total (after last section)

`GESAMTINVESTITION  (<n> Jahre · <Regionen> · Listenpreis <Währung>, exkl. Rabatt/MwSt.)` —
white bold Arial 12 on Fortinet red `DA291C` across the row; column I: `=SUM(I<first>:I<last>)` covering **only the main sections**. Column J notes what is excluded (e.g. `Options-Sektion I nicht in Gesamtsumme enthalten`).

### Option blocks (below the grand total)

Alternatives the customer may pick instead of a main position:
section header `I — OPTION: … — NICHT IN GESAMTSUMME`, Pos numbered `O1, O2 …`,
own subtotal row (`SUMME OPTION …`, same red style) with note pointing at the positions it would replace. Typical options: hardware appliances instead of VM subscriptions, alternative switch series.

## Sheet "Kosten pro Standort" (per-site CAPEX/OPEX)

Purpose: make the BOM auditable per site type and feed the customer configurator.

- Title + price-basis line (rows 1–2).
- **Summary matrix** on top: rows = `CAPEX (HW)`, `OPEX (nJ)`, `TCO n Jahre`, `Δ Ersparnis` per variant; columns = site types. All cells are **references to the detail blocks below** — never retyped numbers.
- **Detail block per site type** (and per variant if there are variants): one-line description of the site profile, then table `Komponente | Menge | CAPEX/Stk | OPEX nJ/Stk | CAPEX | OPEX (nJ) | Total (nJ)` with formulas `=B*C`, `=B*D`, `=E+F`, and a `Summe pro Standort` row with `=SUM()`.
- CAPEX = hardware list price; OPEX = service/subscription over full term. State this in a footnote, plus which SKU family the OPEX derives from.
- Cross-check: per-site quantities × site counts must equal the BOM sheet quantities.

## Styling summary

- Font: Arial throughout. Fortinet red `DA291C` (title, total rows), dark `23252A` (header fills, subtitle), section fill `E9ECF1`, secondary text `555E6B` / `8A929E`.
- Number formats: prices `#,##0.00`; quantities integer, centered.
- Freeze panes below the column header row. No gridline decoration needed beyond fills.
- Versioning: bump the version in filename and header on every revision (`v1.0` → `v1.1`); use column J to mark what changed (`NEU`, `Ersetzt X`, quantity changes) so the delta to the previous version is readable without a diff.
