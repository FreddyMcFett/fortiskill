# Fortinet Product Portfolio — Engineering View

A peer-level map of the Fortinet portfolio, organized by the three current pillars (Secure Networking, Unified SASE, Security Operations) plus cross-cutting products. Each entry covers: what it is, when to choose it over alternatives (Fortinet or otherwise), key integration points, and common gotchas.

This is a **map, not a comprehensive admin guide**. For behavior, always verify against `docs.fortinet.com` for the relevant version.

## Table of contents

1. Pillar 1: Secure Networking
2. Pillar 2: Unified SASE
3. Pillar 3: Security Operations
4. Cross-cutting: Identity, Management, Cloud, Subscriptions
5. OT-specific portfolio (cross-pillar)
6. Choosing between adjacent products (decision matrices)

---

## 1. Pillar 1: Secure Networking

### FortiGate / FortiOS

The flagship NGFW platform. Single OS spans the full hardware/VM/cloud range — same FortiOS on a desk-edge FG-40F as on an FG-7000F chassis.

**Hardware families** (high level — verify exact model availability against the current datasheet):
- **Desktop / SOHO**: FG-30G, FG-40F, FG-50G, FG-60F/E, FG-70F/G, FG-80F, FG-90G
- **Mid-range**: FG-100F, FG-200F, FG-400F, FG-600F, FG-900G, FG-1000F
- **High-end**: FG-1800F, FG-2600F, FG-3000F, FG-3500F, FG-4200F, FG-4800F
- **Chassis**: FG-5000 series (legacy carrier-grade), FG-6000F, FG-7000E, FG-7000F
- **Rugged (OT)**: FortiGate Rugged 30D/35D/60F/70F/520D — IEC 61850-3, EN 50121-4, IP rated for industrial environments

**VM / Cloud**: FG-VM (sized by vCPU — VM01/VM02/VM04/VM08/VM16/VM32/VMUL with bring-your-own-license or pay-as-you-go), FG-VMx for ESX-specific. Available on AWS, Azure, GCP, OCI, Alibaba, IBM, plus VMware/KVM/Hyper-V on-prem.

**FortiGate-CNF (Cloud-Native Firewall)** — Fortinet-managed, native-cloud-integrated firewall service for AWS and Azure. Trade VM control for native integration with cloud routing. Reach for it when the customer wants Fortinet inspection but doesn't want to operate FG-VMs themselves.

**Differentiators worth mentioning**:
- **NPU/CP/SP offload** — bespoke ASICs for L4/IPsec/SSL/IPS offload. The performance gap between FortiGate hardware and competitor x86-only platforms shows up under SSL inspection load.
- **Single OS portability** — config from a small FortiGate is largely portable to a chassis. Same admin guide.
- **Security Fabric integration** — FortiGate is the typical fabric root; FortiAnalyzer/FortiManager/FortiSwitch/FortiAP/FortiClient/FortiSandbox/FortiAuthenticator all federate to it.

**Common gotchas**:
- **Proxy-mode vs flow-mode** UTM inspection has different feature support. Flow-mode is faster; proxy-mode supports certain DLP and content reassembly features that flow doesn't.
- **NPU offload** is feature-dependent. Enabling certain inspection features kicks sessions off the NPU and to the CPU. Check the NPU offload reference for the FortiOS version.
- **VDOMs** (Virtual Domains) divide a FortiGate into administrative domains. Free up to a model-dependent count; over that requires a VDOM upgrade license.
- **Active-Active HA** (cluster session-table sharing across units) does not load-balance proxy-mode UTM inspection well. For UTM-heavy environments, Active-Passive is often preferable despite the headroom waste.

### FortiManager

Centralized policy and device manager. Operates in **ADOMs** (Administrative Domains) for tenant/zone separation.

**When to use**:
- Multiple FortiGates (>5–10) where consistent policy is required
- MSSP / multi-tenant scenarios (each customer in its own ADOM)
- Complex multi-site SD-WAN where the SD-WAN orchestrator workflow is needed
- Workflow approval requirements (config changes need review before deployment)
- Policy versioning and rollback discipline

**FortiManager Cloud** — SaaS variant. Same logical model, hosted by Fortinet. Useful when the customer doesn't want to operate the manager. Region availability matters (verify in service description).

**Common gotchas**:
- **Provisioning templates vs policy packages** — separate concepts. Templates handle device-level config (interfaces, system settings); packages handle firewall policy. Misalignment between them causes deployment surprises.
- **Out-of-sync detection** is conservative. Manual changes on the FortiGate (CLI direct) will mark the device as out-of-sync; reconciliation is a deliberate action.
- **Version compatibility** — the FortiManager version typically supports a window of FortiGate FortiOS versions. Check the compatibility matrix before mixed-version operation.
- **Workflow mode** changes the UX significantly; not all customers want the change-approval gate.

### FortiAnalyzer

Centralized log collection, correlation, reporting, and entry-level SOC features (event-handlers, FortiView, incidents). Often paired with FortiManager.

**Storage sizing matters most**: log volume is dominated by traffic logs. Estimate logs/sec from traffic patterns (FortiAnalyzer datasheet has guidance), retention period (regulatory + operational), and compression. Always over-spec disk vs initial estimate.

**Common gotchas**:
- **Indexed vs raw logs** — different retention policies possible. Compressed/archived logs are searchable but slower.
- **Reports** — ship with templates, but customer-specific reports often need customization. Plan for report-customization time.
- **Privacy** — log content may include user attribution (UTM logs, web-filter logs). Verify GDPR / FADP / works-council requirements before enabling user-level reporting.
- **FortiAnalyzer Cloud vs on-prem** — on-prem retains full log control; Cloud has region constraints. Check service description for retention limits.

### FortiSwitch / FortiSwitchOS

LAN edge switching. Two modes:
- **Standalone** — managed locally via FortiSwitchOS GUI/CLI
- **FortiLink-managed** — managed by a FortiGate as the switch controller (zero-touch from the FortiGate's GUI)

FortiLink is the typical SE choice. FortiGate becomes the management plane, simplifying operations.

**Switch families** (verify current models in datasheet):
- 1xx series (access)
- 2xx / 4xx (mid-range access/aggregation)
- 5xx / 1xxx (aggregation / core)
- Rugged variants (FSR-) for industrial environments

**Common gotchas**:
- **FortiLink compatibility** between FortiOS and FortiSwitchOS is enforced. Check the FortiLink Compatibility table for the FortiOS version.
- **Empty admin password** on managed FortiSwitches is no longer permitted from FortiOS 7.6.1+ — FortiGate will auto-generate a password. Document this for customers upgrading from earlier 7.x.
- **Stacking** is supported on specific models — check the model's stacking support, not just family.
- **PoE budget** is per-model, not just port-count × max-power. Plan for both budget and per-port profile.

### FortiAP / FortiWiFi

Wireless access points. Managed by FortiGate (via FortiLink-equivalent wireless controller) or FortiCloud.

**Modes**:
- **Tunnel mode** — traffic tunneled to FortiGate for inspection. Standard for security-first deployments.
- **Bridge mode** — local breakout at the AP. Lower latency, no inspection at the FortiGate unless backhauled.
- **Mesh** — for areas where wired backhaul isn't practical.

**Common gotchas**:
- **WiFi 6 vs WiFi 6E vs WiFi 7** model differentiation matters for new buys — match to country regulatory (EU 6 GHz availability varies vs US).
- **FortiPresence** (analytics) and **CPI** (Channel Protection / RF management) are distinct subscriptions.
- **Channel planning** in dense environments is non-trivial; the auto-RF works but high-density site surveys are still recommended.

### FortiNAC-F

Network Access Control. The "F" suffix denotes the current generation, replacing legacy FortiNAC. Provides:
- Device discovery and profiling
- Policy-based access control (802.1X + MAB + agentless)
- Endpoint compliance enforcement
- IoT visibility

**When to use**: regulated environments requiring NAC, OT environments needing visibility into industrial devices, healthcare/manufacturing with high IoT density.

**Common gotcha**: NAC deployment is a project, not a product install — discovery → profiling → policy modeling → enforcement phases all take time. Set customer expectations on timeline (typically 3–6 months for a meaningful enforcement state in mid-size enterprises).

### FortiExtender

Cellular gateway / WAN extender. 4G/5G uplink for branch redundancy or as primary in cellular-first deployments.

**When to use**:
- Branch SD-WAN with cellular backup
- Pop-up / temporary sites
- Remote / lift-station / OT sites without fixed-line connectivity
- Out-of-band management (limited — see note)

**FortiExtender as OOB management**: it can carry OOB traffic but is not a full console-server replacement. For dedicated OOB with serial console aggregation, FortiExtender alone is insufficient — third-party console servers (OpenGear, Lantronix, ZPE) are typically needed alongside. Be honest with customers about this gap.

### FortiEdge Cloud

Cloud-hosted management plane for FortiAP and FortiSwitch in deployments that don't have a FortiGate as controller. Useful for:
- Pure LAN-edge deployments (switch + AP without FortiGate)
- MSSPs managing multi-customer LAN edge

---

## 2. Pillar 2: Unified SASE

### FortiSASE

Fortinet's cloud-delivered SASE / SSE platform. Combines:
- **SWG** (Secure Web Gateway)
- **CASB** (inline + with optional API CASB add-on)
- **ZTNA** (universal ZTNA, on/off-net consistent)
- **FWaaS** (Firewall as a Service)
- **DLP**
- **SD-WAN integration** (via FortiGate, hybrid model)

**Versioning**: FortiSASE follows a release-name versioning scheme (e.g., 24.x for 2024 releases), distinct from FortiOS. Always confirm the version in the customer tenant.

**Architecture options**:
- **Pure SaaS** — users connect to FortiSASE via FortiClient; FortiSASE inspects and forwards
- **Hybrid (SD-WAN + SASE)** — branches break out to FortiSASE via FortiGate SD-WAN; remote users go directly via FortiClient
- **ZTNA-only** — using FortiSASE as the ZTNA broker, with private-app access via the FortiClient

**FortiSASE PoP locations** matter for latency and data residency. EU PoPs include multiple regions; **always check current PoP availability in the service description** before promising EU-only data flows.

**Common gotchas**:
- **CASB scope**: inline CASB sees HTTPS traffic going through FortiSASE; out-of-band API CASB (for SaaS posture, DLP-at-rest) is a separate add-on with separate SaaS coverage.
- **DEM** (Digital Experience Monitoring) is included in newer tiers — verify in the current ordering guide.
- **FortiSASE vs FortiGate SD-WAN** — these are complements, not alternatives. FortiSASE is the cloud security stack; FortiGate SD-WAN is the on-prem steering. Hybrid is the typical enterprise deployment.

### FortiClient / FortiClient Cloud

Endpoint agent. Multiple personalities depending on license:
- **VPN-only** (free, subset of features)
- **EMS-managed** (enterprise — managed by FortiClient EMS or FortiClient Cloud)
- **FortiSASE agent** (FortiClient with FortiSASE-specific features)
- **Endpoint security features**: EPP, web filtering, application firewall, vulnerability scanning, ZTNA agent

**FortiClient EMS** = on-prem management server. **FortiClient Cloud** = SaaS-managed equivalent.

**Common gotchas**:
- **FortiEDR is a separate product**, not a FortiClient feature. They can coexist (FortiEDR's agent + FortiClient agent on the same endpoint), but they are commercially and architecturally distinct.
- **Per-user vs per-device** licensing depends on the bundle — verify in the ordering guide.

### FortiProxy

Explicit-proxy / Secure Web Gateway product, complementary to FortiGate. Supports WCCP integration for environments that need a dedicated proxy.

**When to use FortiProxy over FortiGate's built-in proxy**:
- Very high SWG throughput requirements
- Clear separation of SWG responsibility from perimeter firewall
- WCCP integration with existing routing/security designs
- Explicit-proxy deployment patterns

**Field note**: WCCP + FortiProxy + SSL DPI requires careful certificate trust-store placement on Windows endpoints — certificates must land in the correct Windows store (Trusted Root, machine context) for transparent SSL DPI to work without browser errors.

### FortiWeb

Web Application Firewall. Available as:
- **FortiWeb appliance / VM**
- **FortiWeb Cloud** (SaaS-delivered WAF)
- **FortiAppSec Cloud** (cloud-delivered, includes WAF + bot management + API protection)

**When FortiWeb beats FortiGate WAF profile**: FortiGate's WAF is a UTM feature; FortiWeb is a dedicated WAF with deeper signature coverage, ML-based anomaly detection, and bot management. For real WAF requirements, FortiWeb. For light internal-app protection, FortiGate's WAF profile may suffice.

**FortiAppSec Cloud** is the unified cloud-delivered application-security suite — WAF, bot management, API security (FortiDAST integration, API discovery), DDoS for L7. Reach for it when the customer wants cloud-delivered WAF without operating an appliance.

### FortiADC

Application Delivery Controller. Load balancing, GLB, link load balancing, app acceleration, optional WAF features. Hardware and VM.

**When to choose**: customer needs L4–L7 load balancing with security features integrated. Competitive with F5, Citrix NetScaler, Kemp/Progress LoadMaster.

**Common gotcha**: FortiADC's WAF features overlap with FortiWeb but are not identical — for serious WAF requirements, FortiWeb is still the answer.

### FortiDAST / FortiAppSec Cloud

Dynamic Application Security Testing. Crawls and tests web apps for vulnerabilities. Often bundled in FortiAppSec Cloud.

### Lacework FortiCNAPP

Cloud-Native Application Protection Platform. Acquired (Lacework) and integrated. Provides:
- CSPM (Cloud Security Posture Management)
- CWPP (Cloud Workload Protection)
- CIEM (Cloud Infrastructure Entitlement Management)
- Container/Kubernetes security
- Cloud risk management with network/data context (expanded Jan 2026)

**When to use**: customers with significant AWS/Azure/GCP footprint and a need for unified cloud security posture + workload protection. Distinct from FortiCWP / FortiCNP (legacy/predecessor naming) — verify with current product page which generation the customer is engaging with.

### FortiMonitor

Digital Experience Monitoring (DEM) and infrastructure monitoring. Watches user experience (synthetic + real user) and infrastructure health.

### FortiFlex

Consumption-based / point-based licensing across the Fortinet portfolio. Customer buys "points" that can be applied to various products as needed (FortiGate-VM, FortiAnalyzer-VM, FortiSASE seats, etc.). Useful for:
- MSSPs with variable customer load
- Enterprises with elastic scaling needs
- Pre-allocated capacity for project-based deployments

---

## 3. Pillar 3: Security Operations

### FortiAnalyzer (also listed under Secure Networking)

Logging, reporting, basic SOC functions. Belongs to both pillars depending on how the customer uses it.

### FortiSIEM

Full SIEM. Multi-tenant, agent-based discovery, CMDB, performance + security monitoring in one. Often deployed where the customer has consolidated SIEM + monitoring requirements.

**When FortiSIEM beats FortiAnalyzer-only**:
- Multi-vendor log collection at scale
- CMDB / service-impact analysis
- Compliance reporting (PCI, HIPAA, ISO) with established templates
- Performance monitoring alongside security

**FortiSIEM vs Splunk/Sentinel/QRadar**: Fortinet's value is integration with the rest of the fabric and consumption pricing. Mature SOCs with existing Splunk investment rarely rip-and-replace; FortiSIEM is typically chosen at greenfield or consolidation moments.

### FortiSOAR

SOAR (Security Orchestration, Automation, Response). Playbook-driven response across the security stack.

**Common deployment patterns**:
- FortiAnalyzer feeds incidents → FortiSOAR runs playbooks
- Multi-source ingest (EDR + SIEM + email + identity) → playbook orchestrates investigation and containment
- Customer-built integrations via FortiSOAR Connector framework

### FortiNDR

Network Detection and Response. Sensor-based (typically TAP/SPAN) deep-flow analysis for threat detection beyond signature.

### FortiDeceptor

Deception platform. Decoys + lures across IT and OT. Particularly relevant for OT environments where active vulnerability scanning is risky.

### FortiSandbox / FortiSandbox Cloud

Dynamic file analysis. Detonates suspicious files in a sandboxed environment, returns verdict to the requesting product (FortiGate, FortiMail, FortiClient, FortiWeb, etc.).

**When to use**: any environment where unknown-file analysis is required for compliance or threat coverage. Common pairing: FortiMail → FortiSandbox for email attachment analysis.

### FortiEDR / FortiEndpoint

Endpoint Detection and Response (FortiEDR) — kernel-level prevention + detection + response for endpoints. **FortiEndpoint** is the new branding/expanded offering announced at Accelerate 2026, integrating endpoint security into the SecOps fabric.

### FortiAI

AI capabilities embedded across the Security Fabric — threat detection, alert triage, agentic workflows (announced at Accelerate 2026 with expanded capabilities). Not a single product per se but a cross-product capability layer.

### FortiSOC (preview, announced March 2026)

Cloud-delivered offering combining FortiAnalyzer, FortiSIEM, FortiSOAR, and FortiTIP into a single integrated service. Currently preview — verify GA status before positioning to customers.

### FortiMail

Email security gateway. Available as:
- **FortiMail appliance / VM**
- **FortiMail Cloud** (SaaS)

Standard pairings: FortiMail + FortiSandbox for attachment analysis, FortiMail with DKIM/DMARC/SPF enforcement, FortiMail with FortiSOAR for phishing-response playbooks.

### FortiRecon

External attack surface management (EASM) + brand protection + dark-web monitoring. Useful for security teams that need outside-in attacker view.

---

## 4. Cross-cutting

### Identity and Access Management

- **FortiAuthenticator** — RADIUS server, SAML IdP, 2FA (with FortiToken), certificate authority
- **FortiToken** — hardware/mobile/email/SMS OTP
- **FortiPAM** — Privileged Access Management
- **FortiTrust** — identity portfolio branding for newer offerings

### Management

- **FortiManager / FortiManager Cloud** (above)
- **FortiPortal** — multi-tenant portal for MSSPs (customer-facing)
- **FortiCloud** — Fortinet's account/asset/management cloud (where FortiCare entitlements, asset registration, FortiSASE tenants live)

### FortiCare (support)

Tiers (verify current names in ordering guide; tiering has been adjusted historically):
- **FortiCare Essential** — basic 24x7 break/fix
- **FortiCare Premium** — accelerated SLA
- **FortiCare Elite** — best response/RMA, additional services

For mission-critical environments, **FortiCare Elite + Advanced Hardware Replacement** is the typical recommendation. RMA logistics matter — Switzerland is well-served from EU stocking; for customers in Liechtenstein or remote areas, confirm RMA shipping windows with channel.

### FortiGuard

The threat-intelligence and signature-update service backing FortiOS subscriptions. UTP/ENT/ATP bundles include various FortiGuard services. Specific services:
- IPS signatures
- AV signatures
- Web filtering categorization
- Application Control signatures
- Antispam
- DNS security
- IoT/OT services
- Industrial protocol signatures (OT bundle)

---

## 5. OT-specific portfolio (cross-pillar)

OT/ICS environments use a subset of the portfolio with specific products:

- **FortiGate Rugged** (FGR-30D / 35D / 60F / 70F / 520D) — ruggedized for industrial environments (IEC 61850-3, EN 50121-4)
- **FortiSwitch Rugged** (FSR-) — ruggedized switching
- **FortiNDR for OT** — passive monitoring on OT/ICS networks (deep-packet inspection of industrial protocols)
- **FortiDeceptor for OT** — decoys for ICS protocols (Modbus, DNP3, S7, etc.)
- **FortiNAC-F** — discovery and visibility for IoT/OT
- **FortiGuard Industrial Security service** — protocol-specific signatures (Modbus TCP, DNP3, IEC 60870-5-104, S7, Ethernet/IP, BACnet, etc.)
- **FortiEDR for OT** — endpoint protection where Windows/Linux exists in OT (HMIs, engineering workstations) — must be tested for ICS-vendor compatibility

For OT-specific design patterns (Purdue model alignment, IEC 62443 zone/conduit), see `references/ot-security.md`.

---

## 6. Choosing between adjacent products

### FortiSASE vs FortiGate SD-WAN

**Not alternatives.** SD-WAN handles the network steering (path selection, application-aware steering, performance SLA). FortiSASE handles cloud-delivered security inspection. The hybrid model uses both: SD-WAN steers, FortiSASE inspects breakout traffic.

### FortiSASE vs FortiClient ZTNA only

Both can deliver ZTNA. FortiSASE includes ZTNA plus SWG/CASB/FWaaS/DLP. If the customer needs only ZTNA for private-app access, FortiClient + FortiGate ZTNA proxy can be cheaper. If they need broader SSE, FortiSASE.

### FortiManager vs FortiManager Cloud

On-prem retains full control and works offline. Cloud removes operational burden. For DACH customers with strict data-residency, verify FortiManager Cloud region availability per service description.

### FortiAnalyzer vs FortiSIEM

FortiAnalyzer for Fortinet-centric log/report. FortiSIEM when the customer needs multi-vendor SIEM + CMDB + performance monitoring. Many customers run both: FortiAnalyzer as Fortinet log collector, FortiSIEM as enterprise SIEM consuming from FortiAnalyzer.

### FortiSOC (when GA) vs FortiAnalyzer + FortiSIEM + FortiSOAR

FortiSOC bundles them as a single SaaS service. For new customers without existing investment in any of the three components, FortiSOC will likely be the recommended path once GA. For customers with existing FortiAnalyzer/FortiSIEM/FortiSOAR investments, migration is a separate conversation.

### FortiWeb vs FortiAppSec Cloud

FortiWeb appliance/VM for on-prem traffic and customer-managed scenarios. FortiAppSec Cloud for cloud-delivered, multi-app, broader application-security scope (WAF + bot + API security + DAST integration).

### FortiEDR vs FortiClient endpoint security

FortiEDR is a dedicated EDR (kernel-level, behavioral, response capability). FortiClient endpoint security features are lighter-weight (web filtering, AV, application control, vulnerability scan). They can coexist but address different needs. For real EDR requirements, FortiEDR (or FortiEndpoint, the newer expanded offering).

### FortiCNAPP vs FortiCWP/FortiCNP

The current Fortinet CNAPP offering is Lacework FortiCNAPP. FortiCWP and FortiCNP are predecessor / partial-overlap names from earlier portfolio iterations — when a customer references them, verify on the current product page which generation they're actually using or considering.

---

## When to ask, not assume

Before designing or recommending, ask the customer:
1. Current FortiOS version (or current vendor + version if displacing)
2. Current FortiCare tier (or willingness to invest in support)
3. Bundle expectations (UTP / ENT / ATP / SP) — drives feature availability
4. Data residency constraints (DACH-specific: often Swiss-only or EU-only)
5. Existing security stack the Fortinet products will integrate with (Active Directory? Existing SIEM? Existing EDR?)
6. Operational model (in-house ops? MSSP? Managed Fortinet Service?)
7. Refresh cycle / commercial constraints (existing assets to retire, budget cycles)

Don't guess any of these. The cost of asking is one extra round-trip; the cost of guessing wrong is a re-architected proposal.
