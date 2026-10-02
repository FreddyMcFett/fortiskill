# Bill of Materials (BoM) Template

A defensible BoM is built on documented assumptions. Use this template structure for every customer BoM. Tailor to the specific opportunity; never ship a BoM without filling in every section.

---

## Header

```
Customer:           <name>
Project:            <project name / opportunity ID>
Author / SE:        <name>
Date:               <date>
Version:            <v0.1 / v1.0 / etc>
FortiOS target:     <e.g., 7.6.6 GA — verify in references/fortios-versions.md>
Currency:           CHF / EUR
Validity:           <quote validity, typically 30 days>
Channel partner:    <if applicable>
```

---

## 1. Executive summary (max ½ page)

- One sentence: what problem this BoM solves.
- Solution shape: products, key sizing decisions, license bundles.
- Total in CHF / EUR (high level, before negotiation).
- Key trade-offs the customer needs to be aware of.

---

## 2. Scope statement

**In scope:**
- (e.g., 2 datacenter NGFW HA pairs)
- (e.g., 8 branch FortiGates)
- (e.g., FortiManager + FortiAnalyzer for centralized mgmt and logging)
- (e.g., FortiSASE for 250 mobile users)

**Out of scope:**
- (e.g., FortiSIEM — handled by existing customer SIEM)
- (e.g., FortiClient EMS — to be addressed in Phase 2)
- (e.g., professional services for migration — separate SoW)

**Dependencies:**
- (e.g., customer to provide IP plan)
- (e.g., customer to migrate from existing third-party firewall cluster)
- (e.g., MPLS contract end date drives SD-WAN cutover timing)

---

## 3. Sizing assumptions

This is the most important section. Every sizing decision traces back here.

| Parameter | Assumed value | Source / rationale |
|---|---|---|
| HQ users | 1,000 | Customer discovery, <date> |
| Branch users (avg) | 50 | Customer discovery |
| Branch sites | 8 | Customer discovery |
| Internet egress (HQ peak) | 2 Gbps | Customer measured (NetFlow, <month>) |
| Internet egress (branch peak) | 200 Mbps | Customer estimate |
| SSL DPI scope | All north-south, 70% encrypted | Customer policy |
| IPS scope | All N-S + cross-DMZ E-W | Customer policy |
| AV scope | Web + mail | Customer policy |
| Application Control | Enabled all policies | Customer policy |
| Web filtering | Enabled all user policies | Customer policy |
| Growth assumption | 20% over 3 years | Customer business plan |
| Headroom buffer | 30% over peak | SE sizing standard |
| HA model | Active-Passive FGCP | Customer requirement (single ownership simplicity) |
| VDOM count | 1 (single-tenant) | Customer requirement |
| Compliance | NIS2, ISO 27001 | Customer regulatory scope |

---

## 4. Hardware

| Line | SKU | Description | Qty | Unit list price | Discount % | Net | Notes |
|---|---|---|---|---|---|---|---|
| 1 | FG-200G | FortiGate 200G hardware | 2 | <look up current> | <%> | <CHF> | DC pair, A-P HA |
| 2 | FG-90G | FortiGate 90G hardware | 8 | | | | Branches |
| 3 | FAZ-1000F | FortiAnalyzer 1000F | 1 | | | | DC, log retention 12mo |
| 4 | FMG-VM | FortiManager VM | 1 | | | | Hosted in customer DC, 100-device tier |
| 5 | FS-148F-POE | FortiSwitch 148F PoE | 4 | | | | HQ access |
| 6 | FAP-431G | FortiAP 431G | 30 | | | | HQ + branch APs |

> **All SKUs and prices to be verified against the current Fortinet ordering guide and current channel pricing at the time of quote. Prices in this template are placeholders.**

---

## 5. Software / VM

| Line | SKU | Description | Qty | Notes |
|---|---|---|---|---|
| 7 | FG-VM04 | FortiGate VM04 | 2 | Cloud edge in Azure (HQ→Azure transit) |
| 8 | FAZ-VM-GB10 | FortiAnalyzer VM, 10 GB/day | 1 | DR site |

---

## 6. Subscriptions / FortiGuard / licenses

License bundle composition is **version- and date-specific**. Verify against the **current ordering guide** before quoting. Do not rely on pre-existing assumptions.

| Line | SKU | Description | Term | Qty | Notes |
|---|---|---|---|---|---|
| 9 | FC-10-200G-...-UTP-... | UTP bundle for FG-200G | 36 mo | 2 | IPS/AV/AppCtrl/WebFilter/AS/SSL DPI |
| 10 | FC-10-90G-...-ENT-... | ENT bundle for FG-90G | 36 mo | 8 | Adds SASE-aligned features |
| 11 | FC-10-...-Industrial | Industrial Security service | 36 mo | <if OT> | OT-specific |

---

## 7. FortiCare (support) tier

| Line | SKU | Description | Term | Qty | Notes |
|---|---|---|---|---|---|
| 12 | FC-10-...-FortiCare-Premium | Premium 24x7 + advance HW replacement | 36 mo | 10 (per FG) | Required for production-critical |
| 13 | FAZ-...-FortiCare-Premium | FortiAnalyzer Premium | 36 mo | 1 | |

Alternative tiers: Essential (8x5), Premium (24x7 + AHR), Elite (Premium + TAM + faster SLAs).

---

## 8. SASE / cloud-delivered

| Line | SKU | Description | Term | Qty | Notes |
|---|---|---|---|---|---|
| 14 | FortiSASE user license (current SKU) | Per-user SASE | 36 mo | 250 | EU PoPs (Frankfurt / Zurich — verify) |
| 15 | FortiSASE add-on (DEM / DLP / etc.) | as applicable | 36 mo | 250 | |

---

## 9. FortiFlex (if applicable)

| Line | Points pool | Term | Notes |
|---|---|---|---|
| 16 | <points> | 36 mo | Covers POC + flexible expansion |

---

## 10. Professional services

| Line | Description | Days | Rate | Total |
|---|---|---|---|---|
| 17 | Implementation — DC | <days> | <CHF/day> | |
| 18 | Implementation — branches | <days> | | |
| 19 | Migration from <competitor> | | | |
| 20 | Knowledge transfer | | | |
| 21 | Hypercare (4 weeks) | | | |

> Scope and assumptions detailed in separate Statement of Work.

---

## 11. Total summary

| Category | CHF / EUR |
|---|---|
| Hardware | |
| Software / VM | |
| Subscriptions (3-year) | |
| FortiCare (3-year) | |
| FortiSASE (3-year) | |
| FortiFlex pool | |
| Professional services | |
| **Total (3-year, list)** | |
| Negotiated discount | |
| **Total (3-year, net)** | |

---

## 12. Risks & open questions

| # | Risk / question | Impact | Owner | Resolution by |
|---|---|---|---|---|
| 1 | Branch sites: are all 8 confirmed, or is final count 6–10? | Sizing of FG-90G + bundles | Customer | Before SO |
| 2 | SSL DPI scope on branch: full or selective? | Could justify smaller branch FG | Customer | Before SO |
| 3 | OT in scope? | Industrial Security service add-on | Customer | Discovery follow-up |
| 4 | Existing FortiAuthenticator? | Avoid double licensing if reuse possible | Customer | Inventory check |
| 5 | DR site requirements | Could expand FAZ + FG VM scope | Customer | Phase 2 conversation |

---

## 13. Alternatives considered

Document the alternatives you ruled out and why. This protects the design decision under audit / second-guessing.

- **Considered FG-100F instead of FG-90G for branches** — rejected because 90G generation has newer NPU + lower power; branch sites don't need the higher throughput of 100F.
- **Considered FortiSIEM instead of FortiAnalyzer** — rejected because customer's SIEM is Splunk-based and remains in scope for SOC; FortiAnalyzer covers the Fortinet-fabric-specific reporting and event correlation needed.
- **Considered FortiSASE-only (no cloud edge FortiGate VM)** — rejected because customer has VPN-back-to-DC patterns for legacy apps that need a real firewall in cloud; hybrid model selected.

---

## 14. Validity & assumptions

- This BoM is valid for **<N> days** from the date above.
- Pricing assumes **current Fortinet GPL** at time of quote, with **<discount>%** channel-derived discount applied.
- Excludes taxes (Swiss VAT 8.1% applies for CH-billed customers).
- Excludes shipping, customs (negligible within EU customs territory; CH is non-EU customs — verify duty implications).
- Excludes customer-side activities (rack/stack, IP plan, change windows).

---

## 15. Sign-off

| Role | Name | Date | Signature |
|---|---|---|---|
| Customer architect | | | |
| Customer procurement | | | |
| Fortinet SE | <SE name> | | |
| Channel partner | | | |

---

## Notes for the SE preparing the BoM

- **Look up every SKU and price in the current ordering guide.** Don't carry forward old SKUs from previous quotes — bundle composition changes.
- **Cross-check sizing** against the actual datasheet for the specific FortiOS version.
- **Have the BoM reviewed** by a peer SE for sanity-checking before sending to a customer.
- **Date and version** the document; track revisions in a changelog.
- **Don't quote support tier you wouldn't accept yourself** — Premium is the floor for anything in production.
- **Document inferred numbers explicitly.** If the customer said "around 1000 users" and you sized for 1200, write that down.
- **Flag everything that needs verification before order placement** in the open-questions section.
