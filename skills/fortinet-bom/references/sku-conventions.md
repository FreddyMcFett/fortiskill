# Fortinet SKU conventions & price-list structure

These are recurring patterns observed across Fortinet price lists and ordering guides. They help you **search** for the right SKU — they are not a substitute for verifying the SKU exists in the price list (patterns change between product generations; ordering guides are authoritative: https://www.fortinet.com/resources/ordering-guides).

## Price list workbook

File like `fortinet-pricelist.xlsx`. The machine-readable sheet is **`DataSet`**; the columns that matter are `Item`, `SKU`, `Description #1` and `Price`.

- Large sheet; search it with `scripts/pricelist_lookup.py`, not by eye.
- Per-family sheets (FortiGate, FortiSwitch, …) duplicate the data with human formatting — use them only for browsing.
- The `Item` column groups SKUs by product+service; `Description #1` spells out term and bundle contents.
- Note the price-list quarter — it goes into the BOM header.

## Hardware SKUs

- `FG-<model>` FortiGate (e.g. `FG-401G`, `FG-50G`, `FG-30G`), `FGR-` Rugged FortiGate, `FWF-` FortiWiFi
- `FS-<model>` FortiSwitch (e.g. `FS-124G-FPOE`), `FSR-` Rugged switch
- `FAP-<model>-<region>` FortiAP — **region code matters** (`-E` for Europe): `FAP-221K-E`
- `FER-<model>-<region>` FortiExtender Rugged, `FEX-`/`FEW-` other FortiExtender
- `FMG-`, `FAZ-`, `FAC-` FortiManager/-Analyzer/-Authenticator appliances
- `SP-` spare parts / PSUs (e.g. `SP-RGDIN-240-PS`), `FAC-HW-<n>UG` user upgrades

## Service / subscription SKUs

General shape: `FC-10-<HWCODE>-<service>-02-<term>`

- `<HWCODE>` is a 5-char code derived from the hardware model, **not guessable reliably** (FG-401G → `FG4H1`, FG-50G → `GT50G`, FG-30G → `FG30G`, FGR-60G → `GR60G`). Always find it by searching the price list for the model name.
- `<service>` — the bundle:
  - `928` = Advanced Threat Protection (ATP: IPS, AMP, App Control) incl. FortiCare Premium
  - `950` = Unified Threat Protection (UTP) incl. FortiCare Premium
  - `809` = Enterprise Protection (EP); FAZ EP is e.g. `1263`
  - `247` = FortiCare Premium support only (switches, APs, extenders, appliances)
  - `284` = FortiCare Elite
- `<term>` in months: `-12`, `-36`, `-60`. A 5-year BOM uses `-60` everywhere.
- Quantity of the service line always equals the hardware quantity (HA pair = 2× service too).

## VM subscriptions (VM-S: license + support + services in one SKU)

- FortiGate-VM: `FC<n>-10-FGVVS-<service>-02-<term>` where `FC1`=VM01, `FC2`=VM02, `FC3`=VM04, `FC4`=VM08 … (vCPU tier). `993` = ATP bundle for VM subscription.
- FortiManager: `FC<tier>-10-FMGVS-258-01-<term>` — tier by managed devices/VDOMs (sizing per ordering guide; stack multiple subscriptions to scale).
- FortiAnalyzer: `FC<tier>-10-AZVMS-465-01-<term>` — tier by GB/day; `465` includes IOC, Security Automation, Outbreak Detection.
- FortiAuthenticator: `FC2-10-ACVMS-1268-02-<term>` — **priced per user**, quantity = user count; HA = license each node separately.
- Subscriptions include support → single BOM line, no ↳ service pair; CAPEX = 0 in customer view.

## Recurring licensing gotchas (verify in the ordering guide)

- **HA**: FortiGate/appliance HA pairs need hardware + services on *both* nodes. FortiManager/FortiAnalyzer HA is built into the license model differently — check the OG.
- **Bundle scope**: ATP ≠ UTP ≠ EP; list the included services in the description so the customer sees what they pay for.
- **User/volume tiers** (FAC users, FAZ GB/day, FMG devices): pick the tier ≥ requirement, note headroom in Bemerkung.
- **Region codes** on APs/Extenders (`-E`, `-A`, `-N` …) — wrong region = wrong regulatory domain, unorderable in the customer's country.
- **PoE budget / power accessories**: rugged gear often needs explicit PSUs (`SP-…`, often packs of 2) with no service attach.
- BYOL VM on cloud (AWS/Azure): the Fortinet subscription covers the license; cloud compute costs are *not* part of the BOM — say so in a note if relevant.
