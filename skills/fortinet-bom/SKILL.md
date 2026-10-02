---
name: fortinet-bom
description: Create professional Fortinet Bill of Materials (BOM) Excel workbooks — detailed engineering BOMs with verified SKUs, section grouping and option blocks, and simplified customer-facing configurator workbooks with CAPEX/OPEX/TCO and scenario dropdowns. Use this skill whenever the user asks for a BOM, Stückliste, bill of materials, Preiskalkulation, Kostenaufstellung, budget estimate, TCO calculation, or quote preparation involving Fortinet products (FortiGate, FortiSwitch, FortiAP, FortiExtender, FortiManager, FortiAnalyzer, FortiAuthenticator, VM subscriptions, FortiCare, etc.), and also when updating, extending or reviewing an existing Fortinet BOM xlsx, or exporting a BOM as an SFDC (Salesforce) Quote Lines import CSV ("SFDC import", "Quote Lines CSV", distributor RFQ CSV format). Requires a Fortinet price list xlsx as the price source.
---

# Fortinet BOM Builder

Build Fortinet BOMs the way a presales SE needs them: verified SKUs, list prices straight from the official price list, live Excel formulas, and a layout the customer's procurement team can actually read.

There are three deliverable types. Ask which one the user needs if it isn't obvious (they often want the engineering BOM first and the customer version later, derived from it):

1. **Engineering BOM** — the internal/partner working document. Full SKU detail, sections by architecture role, HW + attached-service line pairs, per-region quantity columns, option blocks excluded from the grand total. Spec: `references/engineering-bom.md`.
2. **Customer configurator** — a simplified, self-service workbook for the customer. Plain-language product descriptions (no SKUs), CAPEX/OPEX/TCO per site type, dropdown scenarios, editable quantities, datasheet links. Spec: `references/customer-bom.md`.
3. **SFDC quote import CSV** — the engineering BOM exported as a Salesforce Quote Lines import file (`UID,Quantity,Disti Discount,Quote Line Item Notes`, `EMEA` suffix on every SKU, UTF-8 without BOM, CRLF). Derived from an existing engineering BOM — one CSV per orderable scenario/option. Spec: `references/sfdc-import.md`, validator: `scripts/sfdc_csv_check.py`.

## Ground rules (why they matter)

- **Never invent a price.** Prices come exclusively from a Fortinet price list workbook (typically `fortinet-pricelist.xlsx`, containing a `DataSet` sheet). Search the working folder for it first. If none is found, stop and ask the user to provide one — a BOM with guessed prices is worse than no BOM, because it will be forwarded to a customer.
- **Never invent a SKU.** Every SKU must be confirmed to exist in the price list via `scripts/pricelist_lookup.py`. Fortinet SKUs are brutally specific (one wrong character = unorderable line item). If a needed SKU is not in the price list, check the product's ordering guide (og-*.pdf files in the project folder, or https://www.fortinet.com/resources/ordering-guides) and flag the line to the user rather than guessing.
- **Licensing logic comes from ordering guides**, not from memory. Bundle contents (ATP vs UTP vs Enterprise Protection), per-user vs per-device licensing, HA licensing rules, VM sizing tiers — verify against the ordering guide or docs.fortinet.com when in doubt. `references/sku-conventions.md` documents the recurring patterns, but ordering guides win on conflict.
- **Formulas, not hardcoded results.** Quantity totals, line totals, section sums, grand totals, and any cross-sheet aggregation must be live Excel formulas so the user can adjust quantities and everything recalculates. This is the whole point of delivering xlsx instead of PDF.
- **State the price basis.** Every workbook header carries: currency, price-list quarter (e.g. "USD – Listenpreis Q2-2026"), price type (list/recommended), and "exkl. Rabatt/MwSt." — discounts are the account team's business, never the BOM's.
- **Language**: match the project language (the reference examples are German, Swiss conventions: "gemäss", "Ausfallsicherheit", decimal formats per spec). Product descriptions in the engineering BOM are technical; in the customer version they explain what the device does for the business.

## Workflow

1. **Collect the design inputs.** From conversation, architecture documents, or an existing BOM in the folder: site/location types and counts, HA yes/no per role, central components (DC firewalls, cloud hubs, management/analytics/auth), security bundle level (ATP/UTP/EP), contract term (usually 36 or 60 months), regions (separate quantity columns per region), currency, VM vs hardware options. If key inputs are missing, ask — a BOM built on assumed quantities gets rebuilt twice.
2. **Map roles to products.** For each role, pick the product and note *why* (this becomes the Rolle/Standort and Bemerkung columns). Check ordering guides/datasheets in the folder for sizing rules (e.g. FortiManager device counts, FortiAnalyzer GB/day, FortiAuthenticator user tiers).
3. **Resolve SKUs and prices** with `scripts/pricelist_lookup.py` (see script header for usage). For each hardware item you need: the HW SKU + the matching service SKU for the chosen bundle and term. For subscriptions/VMs: the all-inclusive subscription SKU. Patterns in `references/sku-conventions.md`.
4. **Build the workbook** with openpyxl following the relevant reference spec exactly (colors, fonts, column layout, number formats, freeze panes). Read the spec file before writing any code.
5. **Verify before delivering** (see checklist below).

## Verification checklist

Run through this before presenting the file — these are the errors that actually happen:

- Every hardware line has its attached service line (↳) with identical quantities; every subscription line covers the full term.
- Every SKU/price pair was returned by the lookup script from the price list — re-run the script on the final SKU list as a batch check.
- Grand total sums only the main sections; option sections (alternative hardware, F-series variants …) are explicitly excluded and labeled as such.
- All totals are formulas; recalculate the workbook (e.g. with LibreOffice headless: `soffice --headless --convert-to xlsx`) or manually verify 2–3 line items and one section sum.
- Quantities are internally consistent (e.g. per-site quantities × site counts = BOM totals; HA pairs = 2× site count).
- Header block states customer, project, version, date, author, price basis, term.
- Customer version only: dropdowns work (data validation), editable cells are visually marked, datasheet hyperlinks resolve, no internal SKUs or margin-relevant remarks leaked into it.
- SFDC CSV only: run `scripts/sfdc_csv_check.py` with `--pricelist`; leave Disti Discount blank unless the user supplied deal-reg rates.

## Reference files

- `references/engineering-bom.md` — full layout spec of the engineering BOM (sections, columns, styles, option blocks, per-site cost sheet). Read before building type 1.
- `references/customer-bom.md` — full layout spec of the 4-sheet customer configurator. Read before building type 2.
- `references/sku-conventions.md` — Fortinet SKU patterns (service suffixes, terms, bundles, VM tiers) and price-list structure. Read during step 3.
- `references/sfdc-import.md` — exact format of the SFDC Quote Lines import CSV (header, EMEA suffix rules, discount policy, verification). Read before building type 3.
