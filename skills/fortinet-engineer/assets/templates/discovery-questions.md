# Discovery Questions

Comprehensive presales discovery question set, organized by topic and persona. Use selectively — not every question fits every meeting. The goal is to surface the technical, operational, and commercial constraints that shape the BoM and architecture.

For DACH engagements, prefer asking in the customer's preferred language; technical terms can stay English with a German gloss where useful.

---

## Universal opening questions

Ask before anything else:

1. **What's driving this conversation now?** (renewal date, audit finding, project milestone, business event, incident)
2. **What's the timeline?** (decision by, deployment by, go-live by)
3. **Who's involved in the decision?** (technical, security, network, identity, operations, procurement, legal, executive sponsor)
4. **What does success look like 12 months after deployment?**
5. **What's the worst-case scenario you want to avoid?**

These five frame the whole engagement.

---

## Network & topology

### Sites and connectivity

- How many sites? (HQ, datacenters, branches, factories, warehouses, retail, remote workers)
- Per site: user count, device count (incl. IoT/OT), criticality tier.
- WAN connectivity per site type: MPLS, dedicated internet, broadband, LTE/5G, satellite.
- WAN contract end dates (especially MPLS — drives SD-WAN timing).
- Existing SD-WAN deployment? (vendor, status, satisfaction)
- Inter-site routing model: hub-spoke, full mesh, partial mesh, regional hubs.
- Datacenter posture: on-prem DC count, colocation, hybrid cloud, all cloud.
- Cloud presence: AWS, Azure, GCP, Alibaba, OCI. Number of accounts/subscriptions, regions, transit/landing-zone model.
- IPv6 deployment? (status, plans)
- Routing protocols in use (BGP, OSPF, EIGRP from prior Cisco, static).
- Asymmetric routing concerns?

### Traffic profile

- North-south internet egress: peak Mbps/Gbps, average, growth.
- East-west (DC): peak, profile (storage replication? backup? user traffic?).
- Inter-DC: peak, latency-sensitive flows.
- Remote access VPN: peak concurrent users, peak throughput.
- Site-to-site VPN: count of tunnels, throughput.
- B2B / partner traffic: count, type.
- TLS/SSL percentage of total: usually 90%+ today; matters for DPI sizing.
- Proxy posture: explicit proxy in use? Transparent? None?
- DNS architecture: split-DNS? Conditional forwarders? Internal vs external DNS providers?

### Existing inventory

- Current firewall vendor and models (incumbent).
- Switching: vendor, model lines, age.
- Wireless: vendor, deployment density.
- Endpoint security (EDR / AV).
- SIEM / SOC tooling.
- Identity (AD on-prem, Entra ID, hybrid, IdP).
- MDM / UEM (Intune, Jamf, Workspace ONE, MobileIron).
- Cloud-edge / SSE (Zscaler, Netskope, Cato, etc., or none).
- VPN concentrators / dedicated remote-access gear.
- Out-of-band management infrastructure.

---

## Security posture

### Inspection scope

- Where is IPS expected? (internet edge only, all firewall hops, lateral)
- Where is AV expected? (web, email, file shares)
- Application Control scope?
- SSL DPI scope: full DPI on all? Bypass for finance/healthcare? Cert-only?
- Web filtering / URL categorization?
- DNS filtering?
- File-type controls / DLP?
- Sandboxing: inline blocking or out-of-band detonation?

### Detection & response

- SOC model: in-house, MSSP, hybrid, none.
- 24x7 coverage?
- Alert volume tolerance? (small SOC = aggressive tuning needed)
- IR runbook maturity?
- Existing playbook automation? (SOAR in use?)
- MITRE ATT&CK coverage measured?
- Threat-hunting cadence?

### Identity & access

- IdP (Entra ID, Okta, AD, hybrid)?
- MFA coverage: all users? Privileged only?
- Conditional access / device posture in use?
- Privileged access management (PAM) in scope?
- Service accounts: how many, how managed, rotation?
- Federation between domains/forests?
- B2B / guest user model?

### Endpoint

- Managed vs unmanaged endpoints (BYOD, contractor)?
- Endpoint count: Windows / macOS / Linux split?
- Mobile devices in scope?
- EDR vendor and feature scope?
- DLP requirements?
- USB / removable-media controls?

### Compliance

- Frameworks in scope: NIS2, ISO 27001, SOC 2, PCI-DSS, HIPAA-equivalent (CH/DE healthcare), FINMA, BSI Grundschutz, KRITIS, IEC 62443 (OT), GDPR, FADP, GAMP 5, FDA 21 CFR Part 11.
- Audit cycle and recent findings.
- Regulatory contact in the org (legal/compliance lead)?
- Data classification scheme?
- Data residency: must data stay in CH? In EU? Specific jurisdictions excluded?
- Cyber insurance: policy in place? Premium pressures? Questionnaire answers driving security investment?

---

## Cloud

- Workload distribution across cloud providers and regions.
- IaaS vs PaaS vs SaaS mix.
- Cloud-native security tooling in use (AWS Security Hub, Microsoft Defender for Cloud, GCP SCC).
- Cloud-edge security current state.
- CSPM / CNAPP in use?
- Container / Kubernetes footprint? Where? Who manages?
- Serverless usage?
- Multi-cloud connectivity (transit, peering, dedicated)?
- Cloud-firewall presence per provider?
- Egress patterns from cloud — back to on-prem, to internet directly, to other clouds?

---

## Remote access / SASE

- Today's RA-VPN model and scale.
- User experience pain points with current VPN?
- SaaS application performance issues?
- Hybrid work distribution: % of users typically remote?
- Privileged remote access for vendors / contractors?
- Posture-based access today?
- ZTNA evaluations in flight?
- Geographic user distribution — where do users physically work?
- Latency-sensitive apps (CAD, real-time collaboration, VoIP) and their location?

---

## Operations

- IT/security org chart (for the relevant teams).
- Network ops team size and skill level.
- Security ops team size and skill level.
- Existing ticketing / ITSM (ServiceNow, Jira, etc.)?
- Change management cadence and rigor?
- Existing runbooks / DR plans?
- Tooling for monitoring and observability (PRTG, Zabbix, Datadog, Dynatrace, Splunk, Elastic)?
- Backup posture for network device configurations?
- Incident history (frequency, severity, root-cause patterns)?
- Patching cadence for security infrastructure?

### Automation maturity

- Network IaC adoption? (Ansible, Terraform, Python tooling)
- Source control for network/security config?
- CI/CD for infrastructure?
- Existing skills / preferred tooling?
- Appetite for adopting new automation?

---

## OT / industrial (if applicable)

Detailed in `references/ot-security.md`. Discovery essentials:

- Plant / site count, type (continuous, batch, hybrid), industry vertical.
- DCS / SCADA vendors per site (Honeywell, Yokogawa, ABB, Emerson, Siemens, Rockwell, etc.).
- Existing OT network architecture: flat? Partial segmentation? Reference-architecture-aligned?
- Existing OT visibility tooling (Claroty, Nozomi, Dragos, Tenable.ot, Microsoft Defender for IoT, none)?
- Remote access for OT vendors and engineers — current model?
- Last incident in OT? Cause? Response?
- Patching posture for OT assets (HMI, historian, engineering workstations, PLC firmware)?
- Backup posture for OT (DCS config, PLC programs, HMI projects)?
- Change-control reality (frequency of allowed change windows, turnaround cycles)?
- Functional safety scope (SIS networks)?
- Hazardous area zones (ATEX/IECEx)?
- Regulatory exposure: NIS2, KRITIS, sector-specific.
- For pharma/CDMO: GMP-regulated systems? GAMP 5 / Annex 11 / 21 CFR Part 11 in scope?

---

## Cloud-specific / hyperscaler

- AWS Transit Gateway design? Or full-mesh VPC peering? Or third-party transit?
- Azure Virtual WAN? Or hub VNet? Or third-party hub?
- Egress posture per region per cloud?
- Cross-region traffic flows?
- Intent for cloud-firewall: per-VPC, regional, central inspection?
- Cloud landing-zone framework in use (AWS Control Tower, Azure CAF, GCP Foundation)?
- Inspection requirements differ by environment (prod vs non-prod)?
- Cost sensitivity for east-west inspection in cloud (high)?

---

## SIEM / SOC

- Current SIEM (Splunk, QRadar, Sentinel, Elastic, Sumo Logic, Exabeam, none)?
- Log sources covered today?
- Daily ingest volume (GB/day, EPS)?
- Retention requirements (regulatory, contractual)?
- SOC analyst staffing?
- Use cases / detection rules implemented?
- Threat intel feeds in use?
- SOAR in use? Playbooks defined?
- Alert volume vs analyst capacity?

---

## Commercial / lifecycle

- Existing Fortinet contract end dates (per product line)?
- Existing competitor contract end dates?
- Buying motion: capex / opex preference, multi-year discount appetite, FortiFlex appetite?
- Channel partner involved?
- Procurement framework / preferred contract vehicle?
- Total budget envelope (rough)?
- Decision process and timeline?
- Required board / executive approval thresholds?
- Multi-year vs annual contract preference?
- Implementation budget vs license budget split?
- Internal capacity vs services from partner / Fortinet vs co-delivery?

---

## Persona-specific question packs

### CIO / CISO

- What's your security strategy 24-month horizon?
- Vendor consolidation appetite?
- Cyber insurance posture and pressure?
- Board-level security metrics you report?
- Recent incidents that informed strategy?
- Talent strategy — hire vs outsource?

### Network architect

- SD-WAN strategy?
- IPv6 plan?
- Cloud connectivity strategy?
- Routing simplification priorities?
- Segmentation strategy (VRF, micro, ZTNA)?
- Branch transformation roadmap?

### Security architect

- Reference architecture in use (NIST CSF, MITRE D3FEND, custom)?
- Zero-trust roadmap and milestones?
- Attack-surface management approach?
- Threat-modeling cadence?
- Pen-test / red-team frequency?

### SOC manager

- MTTD / MTTR metrics?
- Top noisy / silent gaps in detection?
- Analyst tier model (T1/T2/T3)?
- Tooling pain points?
- Automation maturity?

### Plant manager / OT engineer (for OT engagements)

- What's the worst thing IT could do to your plant?
- Top 3 cyber-risk concerns?
- Last unplanned downtime — was it cyber-related?
- Vendor remote-access pain?
- What change cadence can you tolerate without affecting production?

### Procurement

- Preferred contract structure?
- Existing master agreements / framework contracts?
- Approved vendor list status (Fortinet on it)?
- Multi-year appetite?
- Competitive bid requirement?

---

## Output: discovery summary

After discovery, produce a one-page summary covering:

- Customer profile (industry, scale, geography, regulatory)
- Top 3 pains
- Solution shape (high level, not yet detailed)
- Compliance & operational constraints
- Sizing parameters
- Open questions before BoM/proposal
- Decision process and timeline
- Risks (deal-level and architectural)

Share back with the customer technical lead for confirmation. Errors caught at this stage cost minutes; errors caught at proposal stage cost weeks.
