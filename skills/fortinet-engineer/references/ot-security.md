# OT / Industrial Security

OT security with Fortinet across discrete manufacturing, process industries (chemical, pharma, CDMO), energy, water, transport, building automation. This reference is the design and engagement framework — verify every product capability claim against docs.fortinet.com and the **FortiGuard Industrial Security service** documentation for the FortiOS version in scope.

OT engagements fail more often from process and stakeholder mistakes than from technical mistakes. The engineering content below sits on top of a strict assumption: you've already aligned with the OT/process-engineering team and have explicit approval for any change.

---

## Frameworks customers will reference

### Purdue Reference Model (PERA, ISA-95)

| Level | Domain | Typical assets |
|---|---|---|
| 5 | Enterprise | ERP, corporate IT, SAP, business apps |
| 4 | Site business | MES interfaces, scheduling, plant ERP |
| 3.5 | DMZ | Historian replicas, jump servers, A/V update servers, patching |
| 3 | Operations | MES, plant historians, batch managers, OT engineering workstations |
| 2 | Supervisory | HMI, SCADA, OT domain controllers |
| 1 | Control | PLCs, DCS controllers, RTUs |
| 0 | Process | Sensors, actuators, instruments |

Fortinet's primary placements: a hardened **IT/OT DMZ** (Level 3.5) and **inter-zone segmentation** (Level 3 ↔ Level 2 ↔ Level 1). Lower than Level 1, you're inside vendor-locked DCS environments where firewall placement is rare and risky.

### IEC 62443

The reference standard for industrial security. Engineering-relevant parts:

| Part | Topic | What it means in design |
|---|---|---|
| 62443-2-1 | Asset owner program | Customer's overall OT security management — you'll be cited as a control implementation |
| 62443-2-4 | Service-provider requirements | Applies to integrators / vendors providing services to OT environments |
| 62443-3-2 | Risk assessment, zones, conduits | The design framework: **zone** = group of assets with shared SL-T (target security level); **conduit** = connection between zones; firewalls live on conduits |
| 62443-3-3 | System security requirements (SR) | The 7 foundational requirements (FRs): IAC, UC, SI, DC, RDF, TRE, RA |
| 62443-4-1 | Secure development for product suppliers | Fortinet's product security maturity (Fortinet has 62443-4-1 certifications on select products — verify current scope at fortinet.com / docs.fortinet.com) |
| 62443-4-2 | Component requirements | Per-device security capability requirements |

**Security Levels (SL)**: SL-1 (casual/coincidental), SL-2 (intentional, simple means), SL-3 (intentional, sophisticated, low resources), SL-4 (intentional, sophisticated, high resources). Most enterprises target SL-2 baseline with SL-3 on critical zones.

The design conversation is: **what is the SL-T per zone, and what conduit controls achieve it?**

### NIS2 (EU)

Transposed into national law in DACH:
- **DE**: NIS2UmsuCG (drafts iterating; check current status at the time of engagement — implementation has been delayed past the original Oct 2024 deadline).
- **AT**: NISG 2024.
- **CH**: not bound by NIS2; cyber regulation evolving (ISG / FINMA / sector-specific). Swiss organizations operating in EU are still in scope for NIS2 via subsidiaries.

NIS2 broadens "essential" / "important" entity scope significantly. For OT-heavy customers (chemical, pharma manufacturing, energy, water, food, manufacturing of critical products) — likely in scope. Maps cleanly to Fortinet capabilities (asset visibility → FortiNDR/FortiDeceptor + FortiSIEM CMDB; access control → ZTNA/IAM; incident detection → FortiEDR + FortiSIEM; reporting → FortiAnalyzer + FortiSOAR).

### Other relevant frameworks

- **NIST SP 800-82** — guide to OT/ICS security (US-anchored but referenced globally).
- **IEC 62443-3-3 + ISA/IEC 62443-4-2** mapping to MITRE ATT&CK for ICS.
- **NERC CIP** — North American electric utilities (rarely in DACH but appears in cross-border energy projects).
- **BSI ICS-Security-Kompendium** (DE) — German federal OT security guidance.
- **SR 510.518** / Swiss federal OT-relevant regulations — sector-specific.
- **FDA 21 CFR Part 11** + GAMP 5 (life sciences; relevant for pharma/CDMO with regulated systems).
- **KRITIS** (DE) — critical infrastructure designation under BSIG.

For a chemical/CDMO customer specifically: layered framework typically includes IEC 62443 baseline, NIS2 obligations (manufacturing of chemicals is NIS2-relevant), and GAMP 5 / FDA 21 CFR Part 11 for any GMP-regulated batch/CIP/QC systems.

---

## Industrial protocols — what you need to know

Protocol awareness drives policy granularity. Generic firewalls block by IP/port; OT-aware firewalls inspect protocol semantics (function codes, register ranges, command vs read).

| Protocol | Typical use | Inspection considerations |
|---|---|---|
| **Modbus TCP** (502) | Discrete + process control, ubiquitous | Function-code level inspection (read vs write); register/coil scope where supported. Easy attack surface — broadly authenticated only by network position |
| **DNP3** (20000) | Energy / utility SCADA | Function-code inspection; secure DNP3 (with DNP3-SA) where deployed — verify Fortinet support for SA |
| **IEC 60870-5-104** (2404) | Energy / power utility (EU heavy) | TCP-based; ASDU type inspection where supported |
| **IEC 61850** (102, GOOSE/SV/MMS) | Substation automation | MMS over TCP (102) is firewall-friendly; GOOSE/SV are L2 multicast — not firewall-traversed |
| **OPC Classic (DA/HDA/AE)** | Legacy SCADA-to-historian | DCOM / RPC dynamic ports — challenging to firewall cleanly. Pin to fixed ports where possible |
| **OPC UA** (4840) | Modern OPC, secure variants available | TCP, supports authentication and encryption — design preference. Cert mgmt needed |
| **S7 / S7Plus** (102) | Siemens PLCs (huge in DACH) | S7Comm function-code inspection; S7Plus uses different framing |
| **EtherNet/IP + CIP** (44818, 2222) | Rockwell / Allen-Bradley | CIP service inspection where supported |
| **PROFINET** | Siemens process / discrete | Real-time variants (RT/IRT) are L2 — not firewall-traversed; PROFINET-IO over UDP for non-RT |
| **BACnet** (47808) | Building automation, HVAC | UDP-based; relevant for facility/building security |
| **MQTT** (1883/8883) | IIoT messaging, edge data collection | TLS variant (8883) preferred; broker authentication critical |
| **HART-IP** (5094) | Process instrumentation | Recently more firewall-relevant as field assets get IP-connected |
| **CC-Link IE** | Mitsubishi (less common in DACH) | L2 mostly; gateway translation typical |

The Fortinet **Industrial Security service** (subscription bundled with most FortiGuard packages targeted at OT) provides the protocol-decode and signatures. Verify the current set of supported protocols and decode depth in the FortiOS Admin Guide → Industrial Security section, and in the FortiGuard service description for the version in scope.

---

## Fortinet OT-relevant products

### Hardware

- **FortiGate Rugged series** (FGR-XXXF) — DIN-rail mount, extended temperature range (typical -40°C to +75°C), shock/vibration rated, fanless. Use cases: substation, plant floor, transport, outdoor. Verify per-model environmental ratings and certifications (e.g., IEEE 1613, IEC 61850-3, ATEX/IECEx where applicable) on the model datasheet.
- **FortiSwitch Rugged series** — same envelope philosophy as Rugged FortiGates.
- **FortiAP outdoor / industrial models** — outdoor APs for plant/yard wireless.
- **FortiExtender** — LTE/5G uplinks for remote OT sites with no fixed line.

### Software / services

- **FortiGuard Industrial Security service** — IPS signatures + protocol decoders + application control entries for industrial protocols. Activated as part of the FortiGuard subscription bundle (verify current bundle composition in the ordering guide).
- **FortiNDR** (Network Detection and Response) — passive traffic analysis; valuable in OT where active scanning is forbidden. Detects anomalies and known threats from a SPAN/TAP. Often the first line of OT visibility because it requires no agent and no active probing.
- **FortiDeceptor** — deception assets (decoy PLCs, HMIs, engineering workstations). Detects lateral movement and reconnaissance with very low false-positive rate. Deployment-friendly in OT because decoys don't talk to real assets.
- **FortiSIEM** — OT-aware connectors and use cases; CMDB can model OT zones; correlations across IT and OT events.
- **FortiSOAR** — playbooks for OT incident workflows (with caution — automated containment in OT can cause more harm than the threat).
- **FortiEDR / FortiEndpoint** — for Windows-based OT assets (HMI, engineering workstations, historian servers). Verify compatibility with the OT vendor's support matrix — some OT vendors restrict third-party agents on certified workstations.
- **FortiAuthenticator + FortiPAM** — identity and privileged access for OT engineers; secure jump-host model into the OT zone.
- **FortiClient** — used carefully on OT endpoints; ZTNA can replace flat-VPN access for OT engineering remote-access scenarios.
- **FortiAI / FortiNDR-AI features** — anomaly detection in OT traffic; requires training data and tuning.

### What Fortinet doesn't do natively (so you know the boundaries)

- **Active OT asset discovery / OT inventory** — Fortinet has visibility through traffic, not active polling like Claroty / Nozomi / Dragos. For deep OT asset inventory, customers often pair Fortinet (perimeter + segmentation + IT/OT bridge) with a dedicated OT visibility vendor. Honest framing in customer conversations.
- **Native PLC / DCS protocol gateway functions** — Fortinet inspects, doesn't translate.

---

## OT engagement workflow

### Phase 0 — pre-engagement

- Identify OT sponsor (process engineering / plant operations, **not** corporate IT).
- Understand the safety regime (functional safety SIL ratings, batch/process criticality, consequences of unintended trip).
- Map the regulatory exposure (sector, jurisdiction, frameworks above).
- Confirm change-control reality (most OT plants have weeks/months change windows; some only allow changes during planned shutdowns).

### Phase 1 — discovery

In addition to standard discovery (`references/presales-playbook.md`), OT-specific:

- Existing OT segmentation? (Often: flat networks with vendor-managed VLANs, or partial segmentation.)
- Existing OT visibility tooling? (None / passive vendor / dedicated OT product.)
- Remote access for vendors / engineers? (How is this done today? VPN? Jump server? Vendor-direct?)
- Patch posture? (When was the last patch on the historian? On the HMI? On the PLC firmware?)
- Backup posture for OT assets? (DCS configuration, PLC programs, HMI projects.)
- Incident history? (Have they had OT incidents? Were they caused by IT bleed-over?)
- Acceptable-impact tolerance: any change that could cause unintended packet drops to a process-critical asset must be mapped against process tolerance (some plants accept 0 ms; others accept ms-scale; very few accept sec-scale).

### Phase 2 — design

The standard design pattern:

```
[L4 Enterprise]
      │
   [Edge FortiGate cluster]  ← perimeter, IT
      │
   [IT/OT DMZ FortiGate cluster] ← all IT↔OT traffic transits this
      │  ┌── jump servers, patching, A/V, historian replica, vendor RAS gateway
      │
   [L3 OT Operations]
      │
   [Inter-zone FortiGate (Rugged where on-floor)]
      │
   [L2 Supervisory zones — per process unit / production line]
      │
   [L1 Control — typically vendor-locked, no FW placement]
```

Key design decisions:

- **Single DMZ vs zone-specific DMZs**: large multi-process plants often need per-process DMZs (Plant-A DMZ, Plant-B DMZ) rather than one mega-DMZ. Reduces blast radius.
- **FortiGate model selection** for OT zones: don't oversize for east-west OT traffic (which is usually low-bandwidth but latency-sensitive). Throughput is rarely the constraint — feature support and protocol inspection are.
- **HA model**: FGCP standard pair; for cross-cell redundancy, sometimes FGSP makes more sense.
- **Logging**: dedicated FortiAnalyzer instance for OT (or a dedicated ADOM) — log retention is often mandated per regulation, and OT logs shouldn't get drowned in IT noise.
- **Out-of-band management** — non-negotiable for OT zones. Note: Fortinet doesn't have a competitive native console-server story; hybrid with a 3rd-party (OpenGear, ZPE Nodegrid) is the typical recommendation.

### Phase 3 — build

OT build sequencing:

1. Deploy in **monitor-only mode** first (no enforcement). Mirror traffic to the new FortiGates via SPAN or in-line bypass mode. Log everything.
2. Build a **traffic baseline** over a representative period (typically 2–4 weeks across normal ops + shift change + shutdown/startup if cyclical).
3. **Validate the baseline** with the OT engineering team — every flow they don't recognize is a finding.
4. Define enforcement policies based on the **observed** traffic, not theoretical expected traffic.
5. Phased enforcement: warn → block. Start with non-critical flows. Move to critical only after stabilization.
6. Document **every** policy with the business reason and the OT engineer who validated it.

### Phase 4 — operate

- Change management to OT zones requires change-board approval **with OT engineering on the board**. Pure IT change boards aren't sufficient.
- Patching cadence aligns to plant turnaround / shutdown windows, not IT cadence. Plan FortiOS upgrade timing accordingly.
- Incident response playbooks must include **OT engineering escalation** before any containment action that touches OT traffic.
- Periodic re-baseline (e.g., after process changes, after vendor system upgrades).

---

## Chemical / CDMO sector specifics

Tailored notes for chemical and contract development & manufacturing organizations (CDMOs):

- **Process types**: continuous (e.g., bulk chemicals) vs batch (typical CDMO, fine chemicals, API manufacture). Batch processes have hard cycles where any interference is intolerable — design and pilot windows must respect this.
- **DCS dominance**: chemical plants run heavily on DCS (Honeywell Experion, Yokogawa CENTUM, ABB Ability System 800xA, Emerson DeltaV, Siemens PCS 7). Each has its own segmentation guidance. Don't impose a generic OT model — read the vendor's reference architecture for the specific DCS in scope.
- **Functional safety**: chemical plants run SIS (Safety Instrumented Systems, often physically separate networks). SIS networks should not be touched by IT/OT firewalls — they have their own engineering chain. Verify scope before designing.
- **Regulated systems** (GMP for CDMOs producing APIs / pharma intermediates): GAMP 5, FDA 21 CFR Part 11 (if US market), EU Annex 11. Any change to the IT/OT boundary that could affect data integrity (e.g., audit trail, electronic records) needs validation review (IQ/OQ/PQ). Plan validation effort in the program timeline.
- **Hazardous-area considerations**: some plant zones are ATEX/IECEx classified. Equipment placed in those zones (rare for FW, more common for switches/APs/wireless gateways) needs zone-rated certifications.
- **Vendor lock-in patterns**: DCS vendors strongly recommend (and sometimes contractually require) specific network architectures. Fortinet's role is typically the **upper conduits** (IT↔DCS-DMZ↔Operations), not inside the DCS data network. Stay in your lane.
- **Remote vendor access** is a typical pain point (DCS vendor support, instrument calibration vendors). FortiGate + FortiAuthenticator + FortiPAM with explicit time-bounded access policies and full session recording is a strong narrative.
- **NIS2 relevance**: chemical manufacturing is in scope as an "essential" or "important" entity depending on size and product category. Pharma manufacturing (CDMO outputs) is in scope. Map design controls to NIS2 articles in the customer-facing document.
- **Cyber insurance**: increasingly demanded, increasingly granular. Common questionnaire items map well to Fortinet capabilities (segmentation, EDR, MFA on engineering workstations, SIEM, IR plan).

For a chemical/CDMO engagement with multi-process sites, combine the above sector framing with a discovery focus on DCS estate, regulatory scope (GMP boundaries if any), site count and topology, existing OT visibility tooling, and remote-vendor-access pain. Use customer-specific details only when the user provides them in the current request.

---

## OT-specific risks the customer will ask about

| Concern | How to address honestly |
|---|---|
| "Can the firewall break my process?" | Yes, if misconfigured; that's why we deploy in monitor mode first, baseline, then enforce; we test failover during a planned window; we coordinate with process engineering at every change |
| "What about latency?" | Fortinet hardware (NPU-offloaded) is sub-millisecond on simple flows; deep inspection adds latency proportional to feature set. Measure under load in the lab. For real-time control protocols (PROFINET RT, EtherCAT, etc.) — those don't traverse the firewall anyway |
| "Will it work with my DCS vendor's reference architecture?" | We design to the DCS vendor's guidance; we don't override it. If there's a conflict, the DCS guidance wins for in-DCS traffic; we provide the outer conduits |
| "Patch cadence?" | OT-cadence, not IT-cadence. Aligned to turnaround windows. We do not push automatic firmware updates to OT FortiGates |
| "What if the firewall fails?" | HA pair as standard; selective fail-open / fail-closed per conduit per business decision; OOB management for recovery without traversing the failed path |
| "Can attackers move from IT to OT?" | The whole design is built to make this hard: zoned, monitored, controlled by least-privilege policies, with deception (FortiDeceptor) catching lateral movement |
| "Active scanning of OT assets?" | No. Fortinet's OT visibility is passive (traffic analysis, FortiNDR). For deep asset inventory, complementary tools (Claroty/Nozomi/Dragos) may be needed |

---

## Documentation specific to OT engagements

In addition to the standard implementation deliverables (`references/implementation-playbook.md`):

- **Zone & conduit document** (per IEC 62443-3-2): zones defined, SL-T per zone, conduits identified, controls per conduit, residual risk register.
- **Traffic baseline** (output of monitor-mode phase): inventory of observed flows with OT-engineer validation per flow.
- **Operational impact assessment** for any policy enforcement: which flows could be affected, what the worst-case outcome is, how it's mitigated.
- **GMP / regulated systems impact assessment** if applicable: which validated systems are touched, what validation activity is required (IQ/OQ revalidation typically), aligned with QA timeline.
- **OT incident response runbook**: distinct from IT IR; includes OT-engineering escalation, manual fallback procedures, vendor support contacts.
- **OT change-management procedure**: agreed RACI between IT security, OT engineering, plant operations, and (where applicable) the DCS vendor.
