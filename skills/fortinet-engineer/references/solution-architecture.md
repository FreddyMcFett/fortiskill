# Solution Architecture

Design patterns for Fortinet deployments. Each pattern covers: when to use it, the underlying mechanisms, decision points, common variants, and gotchas.

This is the architect's reference — for sizing/BoM specifics, see `sizing-and-licensing.md`; for OT-specific designs, see `ot-security.md`.

## Table of contents

1. High Availability
2. Multi-VDOM design
3. SD-WAN
4. SASE / SSE deployment models
5. ZTNA architecture
6. Multi-site enterprise WAN
7. Public cloud designs (AWS / Azure / GCP)
8. Hybrid cloud
9. Datacenter (DC) and chassis designs
10. Branch / SD-Branch
11. Security Fabric integration patterns
12. Out-of-band (OOB) management

---

## 1. High Availability

### Active-Passive (A-P) — the default

Two FortiGates in a cluster. One handles all traffic; the other sits hot-standby with synchronized state. Failover triggered by:
- Heartbeat loss
- Monitored interface down
- Override (admin-initiated)

**Why default**: simpler, predictable performance, easier to reason about. UTM proxy-mode features behave normally. No load-balance corner cases.

### Active-Active (A-A) — when more capacity is needed without buying a bigger model

Both units handle traffic. Sessions are distributed across the cluster.

**When A-A makes sense**:
- Capacity ceiling on the largest available model is approached
- Predominantly L4 firewall + flow-based UTM (which load-balances cleanly)
- Performance budget is tight and a bigger box isn't an option

**When A-A doesn't fit well**:
- **Proxy-mode UTM inspection** — A-A doesn't load-balance proxy-mode inspection well, capacity gain is limited
- **Asymmetric routing** scenarios — return traffic landing on a different unit complicates session ownership
- **State-dependent features** that assume single-unit visibility

### HA design checklist

- **Heartbeat interfaces**: dedicated, redundant (two interfaces minimum), no spanning-tree, no other traffic
- **Session pickup**: enabled (so failover preserves sessions)
- **Override**: planned (manual failover capability for change windows)
- **Override priority**: set thoughtfully so unintended fail-back doesn't happen mid-incident
- **Monitor interfaces**: only for interfaces whose loss truly means the unit can't serve
- **Cluster member monitoring**: appropriate timers; too aggressive risks false failover
- **Multicast**: confirm behavior under HA (some multicast designs need special attention)

### Cross-DC HA (FGCP / FGSP)

For DC-to-DC HA across L3 boundaries:
- **FGCP (FortiGate Clustering Protocol)** — typical L2-adjacent HA; can be extended over L2 stretched
- **FGSP (FortiGate Session Life Support Protocol)** — for cross-L3 active-active where session state is synced for stateful failover across separated locations

FGSP is more complex; use only when the topology truly requires it.

---

## 2. Multi-VDOM design

VDOMs (Virtual Domains) partition a FortiGate into administrative domains.

### When to VDOM

- Multi-tenancy (MSSP, internal multi-org, internal multi-environment dev/test/prod)
- Routing-instance separation (overlapping address spaces, VRF-like requirement)
- Administrative-boundary separation (different teams own different VDOMs)

### When not to VDOM

- Simple environments with single admin team and no tenant separation — VDOMs add operational complexity for no benefit
- Performance-constrained environments where every ounce matters (some inter-VDOM traffic patterns add overhead)

### VDOM patterns

- **Root VDOM only** — single tenant, simple
- **Multiple VDOMs in NAT mode** — each VDOM is independent, inter-VDOM traffic via IPv4 routing or VDOM links
- **Transparent-mode VDOM** — bridges traffic without being an L3 hop (specific use cases like inline inspection)
- **Management VDOM separate** — admin / management isolated from data path

### VDOM links

Inter-VDOM communication via VDOM-link interfaces (logical pair) that hairpin between VDOMs. Configure routing and policy as if they were external interfaces.

### Licensing

VDOMs above the model's free-tier count require a VDOM license upgrade. Verify in current ordering guide.

---

## 3. SD-WAN

FortiGate Secure SD-WAN combines:
- **Path selection** (multiple WAN links: MPLS, internet, LTE/5G)
- **Application-aware steering** (steer applications based on policy)
- **Performance SLA** (latency, jitter, packet loss thresholds)
- **Security inspection at the SD-WAN edge** (IPS, AV, web filter, etc., on the same FortiGate)

### Architecture options

**Hub-and-spoke (overlay over multiple transports)**:
- Branch FortiGates establish IPsec overlays to one or more hub FortiGates
- Hub is typically at DC or in cloud
- ADVPN (Auto-Discovery VPN) optimizes spoke-to-spoke without traffic always traversing the hub

**Full mesh**:
- Every site has overlays to every other site
- Operationally heavier; useful when latency-critical site-to-site traffic dominates

**Hybrid (SD-WAN + SASE)**:
- Branch SD-WAN for site connectivity
- Cloud security inspection at FortiSASE for internet-bound traffic
- Optimal blend of performance + cloud-delivered security

### Performance SLAs

- Configure probes to representative targets (per-application target servers, not just generic "ping 8.8.8.8")
- Set thresholds based on application requirements (voice: <150ms latency, <30ms jitter, <1% loss)
- SLA flap protection — set hysteresis so brief blips don't cause noisy failover

### Application steering

- Application detection lag matters — first packets of a flow may go on default path before the app is identified
- For latency-critical apps, prefer explicit destination-based or src-based steering over deep app detection
- Test with the customer's actual apps; commercial app definitions may not match what the customer calls "the ERP"

### SD-WAN orchestrator

FortiManager's SD-WAN orchestrator simplifies large multi-site rollouts. Templates + workflow + per-site overrides. For >20–30 sites, this is the default approach; <10 sites can be handled with direct config or smaller-scale FortiManager deployment.

### Common pitfalls

- Sizing the hub for full-mesh load when only spoke-to-hub is expected
- Forgetting that internet-bound branch traffic via SASE consumes bandwidth on the SASE link, not the SD-WAN underlay
- Asymmetric routing where return traffic doesn't follow the same path — breaks stateful inspection
- Not accounting for cloud-delivered SaaS that should bypass inspection (SaaS optimization)

---

## 4. SASE / SSE deployment models

FortiSASE deployment falls into three patterns:

### A. SASE-only (no SD-WAN)

Remote users connect directly to FortiSASE via FortiClient. Branches send all internet-bound traffic to FortiSASE via tunnel.

**When**: smaller orgs, all-remote workforce, no significant on-prem branch fleet.

### B. Hybrid (SD-WAN at branches + SASE for internet)

Branches have FortiGate SD-WAN. Internet-bound traffic breaks out to FortiSASE; private/intra-WAN traffic stays on SD-WAN overlay. Remote users go directly to FortiSASE.

**When**: typical mid-to-large enterprise. Combines best of both.

### C. ZTNA-only

Use FortiSASE (or FortiClient + FortiGate) as the ZTNA broker for private-app access. No general SWG/CASB usage.

**When**: customer wants ZTNA for privileged-app access but isn't ready to displace existing SWG/CASB.

### PoP selection

For DACH customers, verify EU PoP coverage in the FortiSASE service description. PoP availability includes:
- Multiple EU regions (Frankfurt, Amsterdam, Paris, etc.)
- Verify Switzerland-resident PoP availability if customer requires Swiss-only data flows
- Latency from primary user concentrations to nearest PoP — measure, don't assume

### CASB scope

- **Inline CASB** sees HTTPS traffic flowing through FortiSASE — covers what users access during their session
- **API CASB / SaaS Security** is a separate add-on — connects to SaaS platforms via API for posture, DLP-at-rest, third-party-app discovery
- For full SaaS coverage, both are typically needed

### DLP

FortiSASE includes DLP capabilities. For deeper DLP requirements (data-at-rest scanning, endpoint DLP), pair with other Fortinet or third-party tools.

---

## 5. ZTNA architecture

ZTNA — every connection is authenticated, authorized, and inspected per-session, regardless of network location.

### FortiGate-based ZTNA (universal ZTNA)

FortiGate acts as the ZTNA proxy. FortiClient on endpoint provides device posture. FortiClient EMS or FortiClient Cloud manages the agents.

**Flow**:
1. User runs FortiClient with ZTNA enabled
2. FortiClient registers with EMS/Cloud → device posture evaluated
3. User accesses a protected app → FortiClient routes via the FortiGate ZTNA proxy
4. FortiGate checks posture + identity + access tag → permits or denies

**When to use**: customer has FortiGate at the perimeter and wants to add ZTNA without buying FortiSASE.

### FortiSASE-based ZTNA

FortiSASE acts as the ZTNA broker. Same logical model, but the broker is in the cloud.

**When to use**: cloud-first organization, distributed workforce, no central perimeter to be the broker.

### Posture evaluation

ZTNA posture checks include:
- OS version
- AV/EDR present and up-to-date
- Disk encryption status
- Specific certificates present
- Custom registry/file checks (Windows)
- FortiClient version

Define posture tags that map to access policies. Common tiers:
- "managed-strict" — full enterprise device, all checks pass → broad access
- "managed-basic" — some checks loose → limited access
- "unmanaged-but-known" — BYOD with auth → published-app access only
- Anything else → no access

### ZTNA vs VPN

ZTNA replaces VPN for application access in modern designs. Don't try to make ZTNA do everything a flat VPN did:
- Flat L3 access patterns don't translate well — list each application explicitly
- IP-based access controls in legacy apps need a translation layer or app-layer proxy
- Privileged admin access (SSH, RDP) is well-suited to ZTNA — no full-tunnel needed

---

## 6. Multi-site enterprise WAN

For 50+ site enterprises:

### Design layers

1. **Underlay** — physical/transport: MPLS, broadband, LTE/5G, satellite. Multiple per site for resilience.
2. **Overlay** — IPsec tunnels (full mesh, hub-spoke, ADVPN-augmented hub-spoke)
3. **Routing** — BGP over IPsec is the typical pattern; OSPF in smaller deployments
4. **Policy** — security policy applied at branch and/or hub depending on inspection model
5. **Orchestration** — FortiManager / FortiManager Cloud + SD-WAN orchestrator
6. **Visibility** — FortiAnalyzer + FortiSIEM
7. **Cloud-delivered security** (optional) — FortiSASE for internet breakout

### Hub locations

- **DC-as-hub** — traditional, traffic backhauled to DC
- **Cloud-as-hub** — FortiGate-VM in cloud (close to SaaS apps, lower latency)
- **Multi-hub** — regional hubs (NA / EMEA / APAC) for global enterprises with latency-sensitive traffic

### Branch sizing

- Determine bandwidth per site (peak)
- Inspection scope (branch-side or hub-side)
- HA at branch (single FG vs HA pair) — depends on uptime target
- Cellular failover (FortiExtender or built-in cellular)

### Routing design

- BGP with private ASN per site (or per region)
- Route reflectors for scale (when full-mesh BGP is unworkable)
- Selective route advertisement (don't propagate everything to every site)
- BFD for sub-second convergence on critical adjacencies

### DACH-specific

- MPLS providers like Swisscom, Sunrise (CH), Deutsche Telekom (DE), A1 (AT) — confirm CE-side requirements with provider
- Cross-border traffic regulatory (data residency, lawful intercept) — verify per-customer
- Disaster-recovery sites typically in EU (Frankfurt is a common choice for Swiss companies)

---

## 7. Public cloud designs

### AWS

**Common patterns**:
- **Hub-and-spoke with Transit Gateway** — FortiGate-VM as a security hub in inspection VPC, customer VPCs spoke off TGW
- **Native FortiGate-CNF** — Fortinet-managed cloud-native firewall, less operational overhead
- **Auto-scaling groups** — FortiGate-VM behind AWS NLB for elastic capacity
- **Per-VPC FortiGate** — older pattern, useful for strong isolation

For high-availability:
- AWS supports FortiGate HA with cross-AZ failover (specific HA modes per FortiOS version)
- VIPs use AWS API to move EIP/route-table associations on failover
- Configure with proper IAM permissions for HA failover

### Azure

**Common patterns**:
- **Azure Virtual WAN with FortiGate as NVA** — FortiGate inspects VWAN traffic
- **Hub-and-spoke with Azure Firewall replaced/augmented by FortiGate**
- **FortiGate-CNF on Azure** — managed
- **Active-Passive HA via Load Balancer + ARM API**

### GCP

- **FortiGate-VM in shared VPC**
- **Network Connectivity Center (NCC) integration** — FortiGate as security hub
- HA via internal load balancer

### Cloud sizing nuances

- Cloud instance type matters more than vCPU count (AES-NI generation, network-performance tier)
- Network throughput is often the actual bottleneck (instance network limits, not FortiOS)
- Egress cost — inspecting then routing to internet costs egress; design to minimize unnecessary path through inspection

### Cloud licensing

- **BYOL** — bring your own FortiOS license (typical for enterprise)
- **PAYG** — pay-as-you-go via cloud marketplace (lower commitment, higher per-hour cost)
- **FortiFlex** — points-based, allocate to cloud instances on demand

---

## 8. Hybrid cloud

- Connect on-prem to cloud via IPsec or cloud-native interconnect (AWS Direct Connect, Azure ExpressRoute, GCP Cloud Interconnect)
- FortiGate at on-prem edge + FortiGate-VM in cloud
- BGP between them for dynamic routing
- Inspection symmetry — both sides should be in the inspection path or neither (asymmetric inspection breaks stateful UTM)

---

## 9. Datacenter and chassis designs

For large DC environments:

### FortiGate chassis (5000F / 6000F / 7000E / 7000F)

- High-throughput aggregation point
- Multiple service modules (FPMs / SPMs) for capacity
- Internal switch fabric (ISF) connects modules
- Used in carrier, large enterprise, MSP DCs

### Inline vs out-of-band

- **Inline at DC perimeter** — FortiGate in the data path; direct inspection
- **Inline at internal segmentation boundary** — east-west inspection between security zones
- **Out-of-band TAP/SPAN** — FortiNDR for detection without inline risk

### East-west micro-segmentation

For DC east-west, FortiGate VDOMs or FortiGate-VM per zone. ZTNA can layer on top for application-level controls. FortiNAC-F for endpoint enforcement.

---

## 10. Branch / SD-Branch

SD-Branch is Fortinet's term for converged branch (FortiGate + FortiSwitch + FortiAP managed as a unit).

### Patterns

- **All-Fortinet branch** — FortiGate + FortiSwitch + FortiAP, one management plane via FortiGate or FortiManager
- **Mixed branch** — FortiGate at edge, third-party switching/AP — works but loses single-pane-of-glass benefits
- **Cellular-only branch** — FortiExtender as primary or backup
- **Pop-up / event branch** — small FortiGate (FG-30/40/60) + FortiAP, deployed quickly

### Zero-touch provisioning

FortiGate Cloud / FortiManager + Auto-Provisioning enables ZTP:
1. Pre-stage device serial in FortiManager / FortiGate Cloud
2. Ship to site
3. Site staff plugs in WAN cable + powers on
4. Device phones home, downloads config, comes online

For >20 sites, ZTP is essential. Saves field-engineering visits.

---

## 11. Security Fabric integration patterns

The Security Fabric is Fortinet's term for tight integration between products via a federated trust model.

### Fabric root + downstream

- One FortiGate is the **fabric root** (typically the perimeter or DC FortiGate)
- Other FortiGates, FortiSwitch, FortiAP, FortiAnalyzer, FortiManager, FortiClient, etc., federate to the root
- FortiAnalyzer/FortiManager federation provides centralized telemetry/management
- Security Rating service evaluates overall fabric posture

### Common integration pairs

- **FortiGate ↔ FortiAnalyzer**: log forwarding, FortiView, indicator sharing
- **FortiGate ↔ FortiClient EMS**: ZTNA posture, agent config, vulnerability scan results
- **FortiGate ↔ FortiSandbox**: file analysis offload, IOC propagation
- **FortiGate ↔ FortiAuthenticator**: SAML IdP, RADIUS, FSSO collector
- **FortiMail ↔ FortiSandbox**: attachment analysis
- **FortiAnalyzer ↔ FortiSIEM**: log feed (FortiAnalyzer as log collector, FortiSIEM as analytics layer)
- **FortiAnalyzer/FortiSIEM ↔ FortiSOAR**: incident escalation and orchestration
- **FortiNDR ↔ FortiSandbox**: file/URL detonation from network captures
- **FortiClient ↔ FortiEDR / FortiEndpoint**: coexistence on the endpoint

### Anti-pattern

Don't fabric-federate everything blindly. Each integration adds operational complexity and trust surface. Federate where there's a clear use case (telemetry sharing, automated response, posture-aware policy); skip where it's "because you can."

---

## 12. Out-of-band (OOB) management

Fortinet does not have a native console-server / OOB management product that competes with OpenGear, Lantronix, ZPE Nodegrid in capability.

**FortiExtender** can carry OOB traffic via cellular, but doesn't aggregate serial console connections from multiple devices.

**Hybrid OOB recommendation**:
- Third-party console server (OpenGear Lighthouse, ZPE Nodegrid, etc.) for serial console aggregation and L3 OOB connectivity
- FortiExtender for cellular last-mile to the OOB network
- FortiGate at OOB-network edge for policy enforcement (separate from production data path)

Be honest with customers about this gap. Conflating "OOB management" with "FortiExtender" produces gaps in disaster recovery scenarios where production network is down.

---

## Design review checklist

Before signing off any design:

- [ ] FortiOS / product version specified for all components
- [ ] BoM aligns with design (no hardware in the diagram missing from BoM, no SKU in BoM not used in diagram)
- [ ] HA strategy defined for each tier
- [ ] Inspection requirements clearly tied to sized throughput
- [ ] Routing protocols and convergence times sized to SLA
- [ ] OOB management addressed
- [ ] Logging/telemetry destination specified (FortiAnalyzer? FortiAnalyzer Cloud? Third-party SIEM via syslog?)
- [ ] Authentication source specified (AD? Entra? FortiAuthenticator? Mixed?)
- [ ] Backup/restore strategy (config backups, automation state, etc.)
- [ ] Change management workflow defined (FortiManager workflow mode? CI/CD? Manual?)
- [ ] Disaster recovery posture (DR site? RPO/RTO targets? Tested?)
- [ ] Compliance constraints (FADP, GDPR, FINMA, IEC 62443, etc.) explicitly addressed
- [ ] Data residency for cloud / SaaS components
- [ ] Cost (CapEx + OpEx + subscriptions) calculated for the term
- [ ] Refresh cycle aligned with EoS / EoL of selected models
- [ ] Risks and assumptions documented
- [ ] Open questions for customer captured separately from the design

A design without these isn't done — it's a draft.
