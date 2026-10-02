# Sizing and Licensing

How to size Fortinet hardware/VM/cloud, construct a defensible BoM, and reason about license bundles. The licensing landscape changes regularly — always cross-check against the current ordering guide before quoting SKUs.

## Table of contents

1. Sizing methodology — first principles
2. FortiGate sizing
3. FortiAnalyzer / FortiManager sizing
4. FortiSwitch / FortiAP sizing
5. FortiSASE sizing (consumption-based)
6. License bundle taxonomy (UTP / ENT / ATP / SP)
7. FortiCare support tiers
8. FortiFlex (consumption-based licensing)
9. Renewal mechanics and gotchas
10. Building a defensible BoM
11. DACH commercial considerations

---

## 1. Sizing methodology — first principles

The wrong sizing approach is to read a datasheet number and pick the next model up. Datasheet numbers are lab figures under specific traffic mixes; real customer traffic rarely matches.

The right sizing approach:

1. **Establish requirements** — throughput at peak, concurrent sessions, new sessions/sec, inspection requirements (IPS / SSL DPI / AV / sandboxing / DLP), retention/log volume, expected user/device counts, growth trajectory (24-month minimum)
2. **Map to inspection profile** — which throughput figure on the datasheet matches the inspection mix the customer will actually run
3. **Apply headroom** — 30–50% headroom over peak is standard; less for cost-sensitive deployments, more for unknown traffic profiles
4. **Cross-check with a second source** — e.g. a peer SE review or the Fortinet account team; use it as a cross-check, not as the sole input
5. **Validate with the customer's actual traffic** if possible — packet captures or NetFlow from existing infrastructure inform the real mix

---

## 2. FortiGate sizing

### Throughput tiers on the datasheet (typical)

For each FortiGate model, datasheets publish:

- **Firewall throughput** (1518-byte UDP, no inspection) — highest number, rarely matches reality
- **Firewall throughput (IMIX)** — internet-mix profile, more representative
- **IPsec VPN throughput** — with AES256-GCM typically
- **Threat Protection throughput** — IPS + AV + AppCtrl on, no SSL DPI
- **NGFW throughput** — IPS + AppCtrl on, no SSL DPI
- **SSL Inspection throughput** — typically a much lower figure; this is where the gap from spec to spec narrows between vendors
- **Concurrent sessions** and **New sessions/sec**

### Which number to use

Match the inspection scope:
- "Just firewall + minimal logging" → IMIX firewall throughput
- "Firewall + IPS" → Threat Protection
- "Firewall + IPS + AppCtrl" → NGFW Throughput
- "Firewall + IPS + SSL DPI" → SSL Inspection throughput (typically 30–50% of NGFW)
- "Full UTM in proxy mode" → measure conservatively; expect 40–60% of NGFW

### Headroom rule of thumb

- General enterprise: target 50% headroom over expected peak
- Mission-critical with bursty traffic: 100%
- Cost-sensitive SMB: 30% if growth is bounded

Headroom protects against (a) traffic-mix surprises, (b) feature additions over the lifecycle, (c) the gap between datasheet conditions and real conditions.

### NPU/CP/SP offload considerations

Different inspection modes use different ASIC paths:
- **NP (Network Processor)** — accelerates L4 firewall, IPsec, sometimes IPS depending on model
- **CP (Content Processor)** — accelerates flow-based content inspection (IPS, AV pattern matching)
- **SP (Security Processor)** — newer ASIC family for advanced inspection

Enabling certain features (some proxy-mode profiles, certain DLP options) **kicks sessions off NPU** to the CPU. For UTM-heavy environments, account for this — datasheet figures assume NPU-offloaded paths.

For exact NPU offload behavior per FortiOS version, check `docs.fortinet.com` → admin guide → "Hardware acceleration" section. Behavior changes between versions.

### VM sizing

FortiGate-VM is sized by vCPU, with memory and disk per the model spec:
- **VM01** — 1 vCPU
- **VM02** — 2 vCPU
- **VM04** — 4 vCPU
- **VM08** — 8 vCPU
- **VM16** — 16 vCPU
- **VM32** — 32 vCPU
- **VMUL** — unlimited

Throughput scales with vCPU + the underlying CPU. Modern Intel/AMD with AES-NI hits much better SSL throughput than older CPUs. Cloud instance type matters — `c5n` / `c6in` family on AWS, equivalent on Azure/GCP, give meaningfully better throughput than general-purpose instances.

### HA sizing

For active-passive, size the active unit to handle the full load — the passive unit is overhead, not capacity. For active-active, the cluster ratchets up under specific conditions but doesn't double effective UTM-mode throughput; conservative sizing assumes active-passive headroom.

### Common sizing mistakes

- Sizing on FW throughput when the customer needs SSL DPI
- Ignoring the 24-month growth trajectory
- Forgetting that adding VDOMs, additional inspection profiles, or more aggressive logging consumes resources
- Using outdated datasheet revisions — always pull the current datasheet
- Sizing FG-VMs without specifying the underlying CPU family

---

## 3. FortiAnalyzer / FortiManager sizing

### FortiAnalyzer

Driven primarily by **logs/sec** and **GB/day**.

- Estimate logs/sec from FortiGate device counts × per-device log rate × inspection-feature multiplier
  - Rough rule: a busy mid-size FortiGate with full UTM logging produces ~1000–3000 logs/sec at peak
  - Web-filter-on adds significantly; URL filter logs every request
- Estimate GB/day from logs/sec × average log size × 86400 / compression
  - Compressed average log size: ~250–400 bytes
- Multiply by retention period for storage requirement
- **Always over-spec disk** — initial estimates underrun in 60%+ of deployments

### FortiManager

Driven by:
- Number of managed devices
- Number of policy packages and ADOMs
- Workflow / approval mode (more overhead)
- Frequency of changes

Models scale to specific device counts — verify against current datasheet.

### Cloud variants

FortiAnalyzer Cloud / FortiManager Cloud have **storage tiers** and **retention limits** that may not match what customers expect from on-prem. Always pull the service description for the current limits.

---

## 4. FortiSwitch / FortiAP sizing

### FortiSwitch

- **Port count** — start from connected device count + growth
- **PoE budget** — sum of per-port PoE class × number of PoE devices (don't just count ports)
- **Uplink** — 10G uplinks for access switches in modern deployments are baseline; 25G/100G for aggregation/core
- **Stacking** vs MLAG — stacking simplifies management but ties units to a single failure domain
- **FortiLink controller capacity** — managing FortiGate has a maximum supported FortiSwitch count per model

### FortiAP

- **AP count** — site-survey driven; rough rule for office: ~1 AP per 200–300 m² in standard density, ~1 per 50–100 m² in high density
- **WiFi 6 / 6E / 7** — match to country regulatory and client device mix
- **Backhaul** — 1G uplink for WiFi 6 access; 2.5G or 10G for WiFi 6E/7
- **Power** — IEEE 802.3at (PoE+, 30W) sufficient for most APs; 802.3bt (PoE++, up to 60/100W) needed for high-end APs

---

## 5. FortiSASE sizing (consumption-based)

FortiSASE is licensed by **users** (concurrent or named, depending on tier). Add-ons:
- Inline CASB — typically included in main user license
- API CASB / SaaS Security — separate add-on
- Data privacy/DLP enhancements — separate
- Bandwidth tiers — verify in current ordering guide

**For sizing**:
- Start from named-user count or concurrent-user count
- Account for branch-site SD-WAN integration if hybrid (SD-WAN + SASE)
- Verify PoP availability in target regions
- For DACH: check EU PoP coverage, including any Swiss-specific data-residency offers

---

## 6. License bundle taxonomy

The bundle landscape has shifted multiple times. **Pull the current ordering guide before quoting**. The general structure as of late 2026:

### UTP — Unified Threat Protection

Traditional UTM bundle. Typically includes:
- IPS
- AV
- Antispam
- Web Filtering
- Application Control
- DNS Filter

Verify exact inclusion in the current ordering guide.

### ENT — Enterprise Bundle

UTP + additional services. Typically includes:
- All UTP services
- SD-WAN orchestration / cloud
- ZTNA (moved into ENT in recent guides)
- FortiCare
- Other services that vary

### ATP — Advanced Threat Protection

Narrower, threat-prevention focused. Typically includes:
- IPS
- AV
- Sandbox cloud (some tiers)
- Specific advanced threat services

### SP and other variants

The SP (Security Protection) and other named bundles vary by product and time. Always check the current ordering guide.

### Per-service vs bundle

Customers can also buy individual FortiGuard services:
- IPS subscription
- AV subscription
- Web Filtering subscription
- Application Control subscription
- Antispam subscription
- FortiSandbox Cloud
- FortiAI subscription (where applicable)
- Industrial Security service (OT)

For OT environments specifically, confirm the **Industrial Security service** is in the BoM — it carries the Modbus / DNP3 / IEC 60870-5-104 / S7 / Ethernet-IP / BACnet signatures that aren't in the standard IPS bundle.

---

## 7. FortiCare support tiers

Tier names have been adjusted historically. As of late 2026 (verify in current ordering guide):

- **FortiCare Essential** — entry-level 24x7 support
- **FortiCare Premium** — accelerated SLA, faster RMA
- **FortiCare Elite** — best response time, priority RMA, additional services

For mission-critical environments, **FortiCare Elite + Advanced Hardware Replacement** is the typical recommendation.

### Support hour windows and SLA

Verify the current SLA matrix per tier in the support description. SLA typically expressed as:
- **First response time** for severity 1 cases
- **RMA shipping window** (Advanced Hardware Replacement reduces this)
- **TAC access scope** (some bundles include limited TAC access for VM/cloud)

### DACH-specific

EU stocking is good. Switzerland-specific RMA logistics: confirmable from local distribution. For customers in remote sites or in countries with customs delays (some non-EU), verify shipping times — ARH may not deliver on the SLA window in all geographies.

---

## 8. FortiFlex

Consumption-based licensing. Customer purchases **FortiFlex points** that can be allocated dynamically across:
- FortiGate-VM (different sizes consume different points)
- FortiAnalyzer-VM
- FortiManager-VM
- FortiSASE seats
- Other supported products

**When FortiFlex makes sense**:
- MSSP with variable customer load
- Enterprise with elastic scaling needs (autoscaling cloud workloads)
- Customers that want to pre-allocate capacity across a portfolio without committing to specific products upfront
- Pilot/PoC consumption that may evolve

**When NOT to choose FortiFlex**:
- Stable, well-understood deployment with no scaling variance — traditional licensing is often cheaper
- Hardware-only environments (FortiFlex covers VM/cloud primarily)

For specifics on points allocation per product/size, consult the current FortiFlex ordering guide.

---

## 9. Renewal mechanics and gotchas

- **Co-terming**: when adding services mid-contract, co-term to the existing renewal date to simplify renewals
- **Lapse impact**: FortiGuard service lapse means signatures stop updating; the device continues with its last-known signatures but is increasingly vulnerable
- **License migration on RMA**: ensure the replacement unit picks up the original entitlements; coordinate with channel
- **Bundle change at renewal**: customer can change bundles (UTP → ENT, etc.) at renewal; mid-contract changes are vendor-discretion
- **End-of-Order (EoO) vs End-of-Support (EoS) vs End-of-Life (EoL)**:
  - EoO: Fortinet stops selling new units of the model
  - EoS: Fortinet stops providing technical support
  - EoL: Final lights-out
  - Refresh planning: aim to refresh before EoS, well before EoL

For specific model EoO/EoS/EoL dates: docs.fortinet.com → Hardware Lifecycle, or via Fortinet Support Portal.

---

## 10. Building a defensible BoM

A defensible BoM tells the customer **what** they're buying, **why**, and what assumptions it rests on.

### Structure

```
Bill of Materials — <Customer> — <Solution> — <Date>

Assumptions
- FortiOS version: 7.6.x
- Inspection mix: <X% SSL-inspected, Y% IPS-only, Z% bypass>
- Peak throughput: <N Gbps>
- Concurrent users: <N>
- Site count: <N>
- 24-month growth: <%>
- Refresh horizon: <years>
- Support tier: FortiCare <Essential/Premium/Elite>
- Bundle: <UTP/ENT/ATP>

Hardware
- FG-<model> × <quantity> — Site role: <perimeter/SD-WAN edge/HA pair>
  - SKU: FG-<model>
  - HA: <Active-Passive / Active-Active / Standalone>
  - Reason: <throughput justification, NPU offload need, etc.>
- FS-<model> × <quantity> — LAN edge access switching
- FAP-<model> × <quantity> — Wireless access

Software / VM
- FortiAnalyzer-VM × 1 — central log/report
  - Sizing: <logs/sec, GB/day, retention months>
  - Storage: <TB>

Subscriptions (per device, X-year term)
- FG-<model>-BDL-<bundle>-<term> — covers UTP/ENT/ATP services + FortiCare
- FortiManager / FortiAnalyzer subscriptions per their licensing model
- FortiSandbox Cloud (if applicable)
- FortiAI subscription (if applicable)

Support
- FortiCare <tier> for <term> — included in bundle SKU above

Out of scope
- <items the customer might assume are included but aren't>

Risks
- <known dependencies, e.g., requires AD readiness, requires HA pair on customer side>
- <assumption-failure consequences, e.g., if SSL inspection is wider than estimated, FG-<model> may need to step up>

Open questions
- <items needing customer-side input>
```

### Anti-patterns

- Quoting throughput without specifying inspection mode
- Listing SKUs without bundle/term suffix (a partial SKU is a quote you can't actually order from)
- Forgetting FortiCare line items (bundle SKUs typically include FortiCare, but standalone SKUs don't)
- Not stating assumptions explicitly — when sizing turns out wrong, the assumption section is where you defend the design
- Quoting EoO models for new deployments

---

## 11. DACH commercial considerations

- **Pricing** — list price is in USD on US ordering guides; EMEA pricing in EUR/CHF with regional discount structure. Channel quotes the actual customer price.
- **Public-sector / banking / insurance customers** — often have specific procurement frameworks (e.g., Swiss Federal procurement frameworks, FINMA-aligned banking). Verify framework compliance with channel before committing to specific bundles.
- **Term**: 1, 3, 5-year terms commonly available. 3-year is the typical default; 5-year for stable infrastructure with budget cycle alignment.
- **Multi-currency** — Switzerland customers often want CHF; verify available currency in the quote.
- **Public lists**: Fortinet publishes US list prices via the ordering guide; channel-discounted local pricing is the actual customer number.

For exact pricing, work through the channel partner / distributor — Fortinet's commercial model is fully channel-led in DACH.
