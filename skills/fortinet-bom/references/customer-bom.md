# Customer configurator — layout specification

A simplified, **interactive** workbook the customer can play with. It is derived from the engineering BOM but deliberately different:

- **No SKUs.** Product name + plain-language benefit ("FortiGate-50G – kompakte Standort-Firewall mit Bedrohungsschutz (HA-Paar, 2 Stück für Ausfallsicherheit)").
- **CAPEX / OPEX / TCO** instead of Stückpreis/Total: `CAPEX / Stk`, `OPEX nJ / Stk`, `CAPEX`, `OPEX (n J)`, `TCO (n J)`.
- **Everything recalculates**: quantities and scenario choices are inputs, all money cells are formulas.
- **No internal remarks** (version deltas, margin hints, "Ersetzt X" notes stay in the engineering BOM).

## Four sheets

### 1 · Konfiguration & Total
- Title bar: Arial 15 bold white on Fortinet red `DA291C`; subtitle with price basis.
- Numbered section headers `①②③④` — Arial 11 bold white on gray `595959`.
- **① Einstellungen**: scenario dropdowns via data validation (e.g. `G-Serie,F-Serie` and `VM (Abo),Hardware`), each with a `◄ …` hint text explaining the choice in one line.
- **② Standorte**: one row per site type — `Anzahl` editable, CAPEX/OPEX/TCO per site pulled from sheet 2 via `IF($C$5="F-Serie", …)` switching on the dropdown, then `gesamt = Anzahl × pro Standort`. Subtotal row.
- **③ Zentrale Komponenten**: aggregate rows referencing sheet 3 sums; the central-services row switches between VM/Hardware blocks based on the dropdown.
- **④ Gesamt-Investition**: TOTAL row, white bold on red `DA291C`.
- **Legende & Hinweise**: bullet block (Arial 9, `404040`) explaining editable cells, CAPEX/OPEX/TCO definitions, HA in plain words ("zwei Geräte für Ausfallsicherheit"), price basis, and where to fine-tune (sheets 3/4).

### 2 · Standorte im Detail
One block per site type × variant: heading, one-line profile sentence, table
`Produkt / Beschreibung | Menge | CAPEX / Stk | OPEX n J / Stk | CAPEX | OPEX (n J) | TCO (n J) | Datenblatt`
with `Summe pro Standort` row. Column H: hyperlink text `Datenblatt ▸` pointing at the official fortinet.com datasheet URL of that product.

### 3 · Zentrale Komponenten
Same table pattern for DC firewalls, cloud hubs, and central services — with **both variants** (VM-Abo and Hardware) as separate blocks so sheet 1 can switch between their sum rows. Subscriptions: CAPEX/Stk = 0, full cost in OPEX.

### 4 · Standort-Konfigurator
- **① Mein Standort**: full component catalog (every product from sheet 2, quantity 0 where unused) with editable quantities and a live total — lets the customer compose a nonstandard site.
- **② Vergleich**: dropdown to pick a reference site type; comparison table `Mein Standort / Standard-Referenz / Differenz` using `VLOOKUP` against a hidden-in-plain-sight reference table below that pulls the sums from sheet 2. Note line: `(positiv = teurer als Standard · negativ = günstiger)`.

## Editable-cell convention (critical)

All user inputs — quantities and dropdown cells — are **bold blue `0000FF` on light yellow `FFE699`**, and the legend says so ("Blaue Zahlen = editierbar"). Everything else is locked-looking (regular styling). Computed money cells may use dark green `006100` to signal "calculated".

## Styling summary

- Arial; red `DA291C` (title + TOTAL), gray `595959` (section/table headers, white bold text), notes `404040`.
- Money format `$#,##0` (or the project currency), negative in parentheses, `–` for zero: `\$#,##0;"($"#,##0\);\–`. Quantities `#,##0` centered.
- Freeze panes below the title. Wrap text on description columns.
- Sheet names numbered with `·` separator: `1 · Konfiguration & Total` etc., so tab order reads as a guided flow.
