# Presales Playbook

Discovery → qualification → demo → POC → BoM → RFP/RFI response → competitive positioning. Calibrated for DACH presales motion (channel-led, technical-buyer-driven, German + English).

The goal of presales is **not to sell every feature** — it is to map a customer's actual technical requirements, constraints, and risks to the smallest correctly-scoped Fortinet solution, and to present it so the customer can defend the decision internally.

---

## Discovery — what to ask before quoting anything

Discovery is the single highest-leverage activity in presales. A bad BoM almost always traces back to skipped discovery. The full structured question set is in `assets/templates/discovery-questions.md`. The summary below is the mental model.

### The five categories

1. **Topology & traffic** — what are we actually inspecting?
2. **Inspection profile** — at what depth?
3. **Operational model** — who runs it, with what tooling?
4. **Compliance & contractual constraints** — what's non-negotiable?
5. **Commercial / lifecycle** — buying motion, renewal posture, existing assets.

### Topology & traffic — anchor questions

- Sites: count, sizes (users + devices), connectivity (MPLS, DIA, broadband, LTE/5G), redundancy posture per site.
- Datacenter(s) vs cloud (AWS/Azure/GCP) vs edge — where does east/west traffic actually flow?
- Throughput **per direction per inspection profile** (north/south, east/west, internet egress, inter-DC, RA/VPN, B2B). Customers usually quote one number — push to break it down.
- IPv4 vs IPv6, NAT posture, asymmetric routing risks.
- Encrypted traffic % (for SSL DPI sizing — TLS 1.3 with ECH changes the picture; verify visibility model).
- Existing SD-WAN, MPLS contract end dates (SD-WAN sales align to MPLS renewal cycles).
- Application landscape: SaaS heavy? Self-hosted? OT? Multi-cloud?

### Inspection profile — the throughput multiplier

The inspection scope determines which datasheet number you use. Going from "firewall throughput" to "threat protection throughput" can be a 5–10x derate on the same box. See `references/sizing-and-licensing.md` for the FortiGate sizing methodology.

Ask:
- IPS on which traffic? (Internet only / all north-south / east-west too?)
- AV on which traffic? (Web only / mail / file shares?)
- Application Control everywhere?
- SSL DPI scope (full DPI, certificate-only inspection, bypass categories)?
- Web filtering / DNS filtering?
- ZTNA posture checks?
- Sandboxing inline or out-of-band?

### Operational model — who runs the thing

This shapes product selection more than people realize:

- In-house SOC / NOC vs MSSP — drives FortiManager vs FortiManager Cloud, FortiSIEM vs FortiAnalyzer-only, FortiSOAR scope.
- 24x7 vs business-hours — drives FortiCare tier (Premium vs Elite).
- Existing automation / IaC posture — drives whether to push Ansible/Terraform vs FortiManager templates.
- Skill level — junior team that needs FMG-driven workflows vs senior team that wants CLI/API access.
- Change management cadence — affects FortiOS version selection (mature 7.4.x vs current 7.6.6 GA).

### Compliance & contractual constraints

For DACH:
- Swiss FADP (revFADP since Sept 2023) — data residency expectations for Swiss-headquartered orgs.
- FINMA framework (banks, insurers) — outsourcing rules, in-Switzerland processing requirements.
- EU GDPR — applies to any DACH org with EU data subjects.
- NIS2 transposed nationally (DE: NIS2UmsuCG; AT: NISG 2024; CH: not bound but watch RECA-equivalent rules).
- DORA (financial entities, EU; effective Jan 2025) — operational resilience, ICT third-party risk.
- BSI IT-Grundschutz (Germany) — common in public sector and KRITIS.
- IEC 62443 (OT/ICS — see `references/ot-security.md`).
- Sector-specific: healthcare (CH: EPDG; DE: KHZG), public-sector procurement (Sourcing-as-a-Service frameworks, BBL/SECO, ÖB), KRITIS sectors.

Always ask: "Are there compliance frameworks that constrain the architecture, the operating model, or the data residency?" — this surfaces requirements the IT lead might forget but legal/compliance won't.

### Commercial / lifecycle

- Existing Fortinet footprint (renewal vs new logo).
- Existing competitor footprint and contract end dates (PA, Cisco, Check Point, Zscaler, Netskope) — replacement opportunities cluster around renewal dates.
- Buying motion: capex vs opex, FortiFlex appetite, multi-year discount sensitivity.
- RFP coming or direct award?
- Channel partner who owns the relationship.

---

## Qualification (BANT-adjacent, presales-flavored)

Quick mental filter — if you can't answer these in two sentences each after discovery, qualify out or push to defer:

- **What problem is the customer actually solving?** (not "they want a firewall")
- **Who's the technical decision maker?** (must be identifiable)
- **What's the timeline driver?** (renewal date, project go-live, audit finding)
- **What's the realistic budget envelope?** (not "TBD")
- **Why Fortinet, why now, why not the incumbent?**

If timeline driver is vague and the customer has no incumbent pain, the deal will slip. Set expectations with sales accordingly.

---

## Demo design

Customer demos should answer **specific** questions raised in discovery, not show off product features. The single most common presales mistake is the canned demo.

### Patterns

- **Problem-led demo** — customer described a pain ("we have no visibility into shadow SaaS"). Show the workflow that resolves that pain, end-to-end (FortiSASE inline CASB → user/app dashboard → policy enforcement → remediation). Not a feature tour.
- **Architecture walk** — for buyers wrestling with topology decisions (SD-WAN hub design, ZTNA placement). Whiteboard or Visio + live FortiManager view, no slides.
- **Hands-on lab** — for technical evaluators who will run the POC. Give them CLI + GUI, walk away, debrief 30 min later.
- **POC kickoff demo** — narrowly scoped: "here's how we'll prove out X, here's the success criterion, here's how we'll measure."

### Anti-patterns

- Showing every UTM profile when the customer only asked about IPsec.
- Demo'ing FortiSIEM in a ZTNA conversation.
- Live-demoing on a freshly-deployed FortiGate where features aren't pre-configured (always have a populated lab).
- Using marketing slides as a demo.

---

## POC / pilot scoping

A POC is won or lost in the **success criteria definition**, not in the configuration. Before anything is racked or licensed:

1. **Written success criteria** — specific, measurable, time-bound. "Throughput ≥ 5 Gbps with IPS+AV on internet egress, measured by iperf3 + traffic generator over 4 hours." Not "performance is good."
2. **Scope boundary** — what's in, what's out, what's stretch. Document explicitly.
3. **Comparison baseline** — what's the incumbent doing today? (latency, throughput, visibility metrics) — POC must beat or match.
4. **Decision matrix** — at the end, criteria are scored. Customer signs.
5. **Timeline with go/no-go gates** — typically 4–8 weeks for FortiSASE/SSE; 2–4 weeks for FortiGate refresh; longer for SOC/SIEM.
6. **Roles and responsibilities** — who configures, who tests, who escalates, who decides.

Default tooling: FortiFlex for short-term POC licensing (avoids permanent SKU commitment); demo licenses via partner portal; NFR licenses for the SE if available.

---

## BoM construction

Detailed methodology + template lives in `assets/templates/bom-template.md` and `references/sizing-and-licensing.md`. Discipline points worth repeating here:

- **Document every assumption.** Throughput numbers, user counts, SSL inspection scope, HA model, VDOM count — all written down. This protects everyone when scope creeps.
- **Headroom**: sized for 3-year growth + inspection-profile expansion + peak ≠ average.
- **Don't undersize to win the deal.** A right-sized BoM that loses on price is recoverable. An undersized BoM that gets deployed is reputational damage.
- **Always offer two tiers** when appropriate — recommended (sized properly) and "minimum viable" (with documented risk). Let the customer choose with eyes open.
- **License bundle selection** — UTP for general-purpose NGFW; ATP if the customer doesn't need URL filtering; ENT if they need full SASE-aligned features. Verify current bundle composition in the ordering guide — bundles change.
- **Renewals**: include FortiCare tier explicitly with rationale. Premium = 24x7 with hardware advance replacement; Elite = + TAM + faster SLAs. For business-critical infrastructure, default to Premium.
- **Spares and DOA**: for chassis or business-critical edge, include spares in the BoM with rationale.
- **Services**: implementation, knowledge transfer, health-check — line items, not assumptions.

---

## RFP / RFI responses

### Structure for RFP technical sections

1. **Executive summary** — problem framing, solution framing, why Fortinet, key differentiators (max 1 page).
2. **Compliance matrix** — answer every numbered requirement with Comply / Partial / Roadmap / Won't Comply, with a reference to the supporting section.
3. **Solution architecture** — diagrams + narrative. Include design alternatives considered and rejected.
4. **Operational model** — runbook, change mgmt, escalation, training.
5. **Commercial** — separate document; price summary in the technical doc with reference.
6. **Appendices** — datasheets, certifications, references, case studies.

### Discipline points

- **Never claim Comply when Partial.** This is the most common reason RFPs fail in due diligence — and in DACH, due diligence is rigorous. Partial with a roadmap reference is fine; false Comply is reputational.
- **Quote dates and versions** for every product claim. "FortiGate 200G with FortiOS 7.6.6 supports …"
- **Cite Fortinet docs** for non-obvious claims. RFP evaluators frequently look up references.
- **Match the customer's terminology.** If they say "next-generation firewall," don't switch to "NGFW" mid-sentence. If German RFP, respond in German (or German with English technical terms — common in DACH).
- **Compliance certifications**: Common Criteria, FIPS 140-2/3, USGv6, IPv6 Ready, ISO 27001 (Fortinet corporate). Always look up the **current** certification status per product — these change.

### Common RFP traps

- Open-ended "describe your approach" questions where the customer expects a specific framework — answer to the framework they're evaluating against (NIST CSF, ISO 27001, CIS Controls, MITRE ATT&CK).
- Questions about features that don't exist as named — translate to the closest Fortinet capability and explain the mapping.
- Trick questions on competitors' features — answer factually, no FUD.
- Pricing in the technical section — separate per RFP rules, don't pollute the technical response.

---

## Competitive positioning

The goal is **honest differentiation**, not FUD. DACH technical buyers are skeptical and well-informed; FUD lands as unprofessional and hurts the deal.

### Palo Alto Networks (PAN-OS)

- **Where Fortinet wins**: integrated single-vendor stack (FortiSwitch + FortiAP + FortiGate + FortiSASE + FortiClient — all Security Fabric), price-performance on hardware (purpose-built NP/CP ASIC offload), SD-WAN maturity at scale, SASE pricing flexibility (FortiFlex).
- **Where PA wins**: Panorama is highly polished and many SOCs are trained on it; PAN-OS feature velocity is steady; Strata Cloud Manager + Prisma Access integration narrative is tight.
- **Honest framing**: both are top-tier NGFW vendors. Differentiator is usually fabric breadth (Fortinet) vs unified cloud-native control plane (PA).
- **Don't say**: PA can't do SD-WAN. They can.

### Cisco (Firepower / Meraki / Catalyst SD-WAN)

- **Where Fortinet wins**: customers facing an ASA→FTD migration often re-evaluate the platform anyway; SD-WAN is native to FortiOS (no separate SD-WAN product line); one Security Fabric across firewall, SD-WAN, switching and wireless, managed from one place.
- **Where Cisco wins**: existing Cisco shops have routing/switching gravity; Talos threat intel is well-respected; Meraki ease-of-use for distributed retail.
- **Honest framing**: if the customer is a deep Cisco shop with a mature operational model, the switching cost may not be worth it for the security tier alone. Lead with fabric value or stay narrow (FortiGate-only refresh).

### Check Point (Quantum / Harmony)

- **Where Fortinet wins**: hardware price-performance, SD-WAN, SASE breadth, SaaS+endpoint integration.
- **Where Check Point wins**: management UX (SmartConsole) is loved by operators; threat prevention reputation is strong.
- **Honest framing**: feature parity is close on NGFW; differentiation is fabric and operational tooling.

### Zscaler (ZIA / ZPA / ZDX)

- This is a SASE/SSE-only competitor — different conversation.
- **Where Fortinet wins**: hybrid model (FortiSASE + FortiGate same vendor, no architectural seam between LAN-edge and cloud-edge), private app access integrated with on-prem ZTNA proxy, single-vendor procurement and support, predictable licensing.
- **Where Zscaler wins**: cloud-native maturity, ZIA/ZPA polish, larger PoP footprint historically, mindshare with cloud-first buyers.
- **Honest framing**: if customer wants a cloud-only SSE play and has no on-prem firewall renewal in scope, Zscaler is a serious incumbent. Fortinet's pitch is the **integrated** story (one vendor end-to-end), not pure SSE feature parity.
- **Watch**: PoP coverage in Switzerland specifically (Zurich PoP availability for both vendors should be verified at quote time).

### Netskope, Cato, Versa

- Smaller scope conversations, usually cloud-led.
- Fortinet's edge: hardware + SaaS combined, FortiClient as the unified agent across SASE + ZTNA + EDR.

### Microsoft (Defender for Endpoint / Entra Internet Access / Entra Private Access)

- Increasingly relevant in DACH, especially in M365 E5 shops.
- **Where Fortinet wins**: dedicated security vendor focus, NGFW + OT + networking depth, breadth across SASE + SecOps.
- **Where Microsoft wins**: bundling (E5 absorbs SSE-like capabilities into license customer already pays for), identity-native architecture, integration with the rest of Entra/Purview/Defender.
- **Honest framing**: this is a real competitor especially in mid-market and identity-led shops. Don't dismiss. Differentiate on networking depth, OT, and operational maturity for security workloads.

---

## Value mapping — talking to non-technical buyers

When the audience is CIO/CISO/CFO, switch from features to outcomes:

| Customer concern | Fortinet narrative |
|---|---|
| Vendor sprawl, integration cost | Security Fabric — single vendor, integrated telemetry, unified management |
| Capex pressure | FortiFlex points-based licensing for opex profile |
| Operational headcount | Automation via Fabric, FortiManager templates, FortiAnalyzer/FortiSIEM correlation |
| Compliance audit | Coherent reporting across the fabric, FortiAnalyzer compliance reports, FortiSIEM CMDB |
| Cyber insurance posture | EDR + ZTNA + email security + MFA in one stack |
| Cloud journey friction | FortiSASE for cloud-edge, FortiGate-CNF/VM in cloud, same operating model |
| OT/IT convergence risk | Industrial Security service, OT-aware NGFW (rugged FortiGates), passive OT visibility (FortiNDR + FortiDeceptor) |

These are talk-tracks, not slogans — back each with a concrete demo or reference architecture.

---

## German-language considerations

- Most Fortinet docs are English-only; some marketing material and select KB articles in German.
- Customer-facing decks: prefer German for executive audiences in Switzerland/Germany/Austria; English-with-German-glossary works for technical audiences.
- Common DACH technical-term mappings:
  - "Firewall-Cluster" = HA pair
  - "Hochverfügbarkeit" = HA
  - "Mikrosegmentierung" = micro-segmentation (often used for VDOM/zone-based segmentation pitches)
  - "Schutzbedarf" = protection requirement (used in BSI Grundschutz)
  - "KRITIS" = critical infrastructure (DE-specific designation)
- Be careful: some translated marketing terms drift from English original meaning. When in doubt, use the English term once with the German term in parentheses.

---

## Discovery → outcome checklist

Before producing a proposal:

- [ ] Topology + sites + traffic profile documented
- [ ] Inspection scope per traffic type documented
- [ ] Operational model captured
- [ ] Compliance constraints captured
- [ ] Existing footprint + competitive context captured
- [ ] Timeline driver identified
- [ ] Decision maker + influencers mapped
- [ ] Budget envelope (rough) understood
- [ ] Demo plan tailored to the discovered pains
- [ ] POC criteria written if POC is in scope
- [ ] BoM assumptions documented before sizing
- [ ] Risks called out (under-sizing, missing visibility, operational gaps)

If 3+ of these are blank when the proposal is being drafted, **stop and re-discover**.
