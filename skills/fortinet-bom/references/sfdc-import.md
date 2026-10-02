# SFDC Quote Lines Import CSV

Deliverable: a CSV that imports BOM lines directly into a Salesforce (SFDC) quote via the
**Quote Lines** importer (same format as distributor RFQ CSV exports).
Trigger phrases: "SFDC import", "Quote Lines CSV", "SFDC Import von der BOM", "RFQ CSV".

## File format — exact, the importer is strict

- Header row, exactly: `UID,Quantity,Disti Discount,Quote Line Item Notes`
- Encoding: UTF-8 **without BOM**. A BOM prepends invisible bytes to the `UID` header and
  the first column silently fails to match on import.
- Line endings: CRLF (`\r\n`), matching the reference exports.
- One row per SKU. Aggregate duplicate SKUs into a single row (sum the quantities).
- Trailing commas per row (empty Disti Discount / Notes fields) — keep all 4 columns on every row.
- Naming: `<Customer>_SFDC_QuoteLines_Import_EMEA.csv`, saved to the project folder.

## Column rules

| Column | Rule |
|---|---|
| UID | Base SKU + `EMEA` appended **directly, no separator**: `FG-401G` → `FG-401GEMEA`, `FC-10-FG4H1-928-02-60` → `FC-10-FG4H1-928-02-60EMEA` |
| Quantity | Identical to the BOM total for that SKU. A multi-year term SKU (`…-02-60`) is **one** line covering the whole term — never qty × years. |
| Disti Discount | **Blank by default.** Deal-specific (deal reg, disti program) — never guess. Only fill when the user supplies the rates. Rates differ per product family (hardware, FortiCare, bundles, FortiSASE, VM subscriptions) — never carry one deal's rates over to another. |
| Quote Line Item Notes | Blank unless the user asks for notes. |

## EMEA suffix — confidence levels

Confirmed by a distributor reference export: hardware SKUs and FortiCare/service SKUs carry the
`EMEA` suffix. For **VM subscriptions** (`FC*-…-FGVVS/FMGVS/AZVMS/ACVMS`) and **accessories**
(e.g. `SP-RGDIN-240-PS`) the suffix is applied by analogy only (~60% confidence — not present
in the reference). Tell the user: if the importer rejects exactly those rows, retry those rows
without the suffix.

## Source and scope

- Source is the current **engineering BOM** xlsx: main sections only. Option blocks
  (alternative hardware, F-series variants …) are excluded — offer a separate variant CSV
  per option instead (one CSV per orderable scenario, as with the BOM options themselves).
- Every base SKU (UID minus `EMEA`) must exist in the price list. Batch check:
  `sed 's/EMEA$//' skus.txt | python scripts/pricelist_lookup.py <pricelist.xlsx> --verify`

## Verification before delivering

Run `scripts/sfdc_csv_check.py` (see script header) — it checks header, encoding/BOM, CRLF,
EMEA suffix, duplicate SKUs, integer quantities, and (with a price list) that every base SKU
resolves. Additionally eyeball: row count vs BOM line count, and that quantities match the BOM
1:1 (sum check).
