# Implementation Playbook

Field-deployment patterns for Fortinet products. Calibrated for greenfield, refresh, and migration scenarios. Day-0 (build) → Day-1 (cutover) → Day-2 (operate).

The skill assumed by this reference: you can already configure FortiGate, FortiManager, FortiAnalyzer, FortiSwitch, FortiAP. This is **process and pattern**, not a config tutorial.

---

## The deployment lifecycle

```
[Design] → [Lab build] → [Pilot site] → [Phased rollout] → [Cutover] → [Stabilization] → [Handover to ops]
```

Skipping the lab and pilot phases is the most common cause of post-deployment incidents. Always lab. Always pilot.

### Phase outputs (what should exist at each gate)

| Phase | Required outputs |
|---|---|
| Design | Approved HLD + LLD, BoM ordered, IP plan, naming standard, change windows agreed |
| Lab | Lab evidence (configs, screenshots, test results), runbook draft, rollback plan tested |
| Pilot | One real production site running with stakeholders monitoring, KPIs measured, runbook refined |
| Rollout | Wave plan, dependency map, communication plan, change tickets per wave |
| Cutover | Cutover runbook, rollback runbook, on-call roster, war-room channel, success criteria |
| Stabilization | Monitoring dashboards, hypercare period (typically 2–4 weeks), known-issue log |
| Handover | As-built docs, ops runbook, escalation matrix, training delivered, sign-off |

---

## Pre-flight checklist (before any production change)

- [ ] HLD + LLD approved by customer architect
- [ ] FortiOS version selected and locked (don't drift mid-deployment) — see `references/fortios-versions.md`
- [ ] Hardware delivered, RMA'd in advance if needed, serial numbers captured
- [ ] Licenses provisioned in FortiCare, validated against entitlement
- [ ] FortiCloud Premium (or equivalent) registered if needed for fabric features
- [ ] IP plan signed off (mgmt, HA heartbeats, routing peers, transit nets)
- [ ] DNS records reserved (mgmt FQDNs, FortiManager, FortiAnalyzer, syslog targets)
- [ ] NTP source agreed (FortiOS is sensitive to time skew — HA, SAML, certs all break with bad time)
- [ ] Change window booked with rollback time buffer (typical: 2x estimated cutover duration)
- [ ] Customer signoff on success/failure criteria
- [ ] Backup of any existing config (FortiGate config file, ASA running-config, PA snapshot, etc.)
- [ ] Console + OOB access verified — never deploy without serial console reachability
- [ ] FortiManager / FortiAnalyzer pre-staged with target config in lab-state
- [ ] Communication channel (war room) established

---

## FortiGate deployment

### Greenfield / new site

Day-0 build steps in canonical order:

1. **Initial bring-up** via console (admin password, mgmt IP, DNS, NTP).
2. **Register and license** — FortiCare registration, contract attach, FortiGuard refresh.
3. **Hostname + admin domain** — apply naming standard now, not later.
4. **Time sources** — NTP first; nothing else works correctly without good time.
5. **DNS** — internal + external DNS configured; for FortiOS 7.6.x verify dnsproxy behavior with conditional forwarding (note: known dnsproxy CPU issue on wildcard FQDN objects — verify against current KB before relying on heavy wildcard FQDN policy).
6. **FortiManager onboarding** — central management before policy work, not after. Get the device into FMG with the right ADOM and a sane revision baseline.
7. **FortiAnalyzer onboarding** — log forwarding configured before traffic; you want logs from the first packet.
8. **Interfaces, zones, VDOMs** — per LLD.
9. **Routing** — static, BGP, OSPF; verify convergence behavior in lab first. For BGP, default holdtime is 180s; 3s minimum without BFD; BFD recommended where supported.
10. **HA** — covered separately below.
11. **Policy** — start from a documented policy structure (object naming, address groups, schedule discipline). Top-down policy ordering with explicit deny at end.
12. **UTM profiles** — IPS/AV/AppCtrl/WebFilter/DNSFilter/SSL DPI per inspection scope.
13. **Logging** — verify logs are reaching FortiAnalyzer, retention is correct, key event types are logged.
14. **Security Fabric** — root + downstream device authorization.
15. **Test plan execution** — connectivity matrix, throughput baseline, failover drills.
16. **Backup** — config file out, hash recorded.

### Refresh / replace existing FortiGate

- Full config backup of outgoing unit before anything.
- Use FortiConverter for cross-version or cross-vendor; budget time for cleanup — the tool is a starting point, not a finished migration.
- HA pairs: replace the secondary first, validate, then the primary; never both at once.
- FortiManager makes refresh much easier — push policy and objects from FMG; the new device picks up the same operational profile.

### Migration from competitor (PA / Cisco / Check Point)

- **FortiConverter** handles common policy translations from PAN-OS, Cisco ASA/FTD, Check Point. Always treat output as draft.
- Manual cleanup areas: NAT translation semantics, application-id mappings, identity policy, SD-WAN steering, advanced UTM profiles.
- Run the migrated config in a lab against captured pcap traffic before cutover. Compare action logs to the original.
- Cutover patterns:
  - **Big-bang** — single window, full swap. Lower complexity, higher risk. OK for small sites.
  - **Parallel** — both firewalls live, traffic shifted incrementally via routing or DNS. Lower risk, more operational overhead. Default for DC/HQ.
  - **Per-VLAN / per-application** — rare but useful when policy translation has hot spots (legacy app with tight ACLs).

### HA setup (FGCP)

- Two units, same model, same FortiOS, same hardware revision (NPU generation matters).
- Heartbeat on dedicated interfaces (typically `ha1`/`ha2` or chosen high-priority); never share with data.
- Monitor priority interfaces (only those whose link loss should trigger failover).
- Override + priority configured deliberately — default behavior favors stability over predictability; for predictable primary, set `override enable` on the preferred unit with higher priority.
- Session sync enabled; consider session-pickup-delay tuning per traffic profile.
- Test both unplanned failover (pull cable) and planned (`execute ha manage` / config push). Measure dwell time.
- Cross-DC HA → use FGSP (session sync without cluster ownership) or active/active routed designs; FGCP across L3 is usually wrong.

A-A clusters: limited use cases (load distribution for non-stateful flows); proxy-mode inspection in A-A has known constraints — verify current limits in docs.fortinet.com for the specific FortiOS version.

---

## FortiManager deployment

- ADOM strategy first — by customer / by region / by environment. Get this right at the start; reorganizing ADOMs later is painful.
- Versioning: FortiManager version must be ≥ managed FortiGate version. Plan upgrade paths together.
- **Workflow mode** if multi-engineer team — adds approval gates on policy commits.
- **Provisioning templates** — system, IPsec, BGP, SD-WAN, SD-Branch, NSX-T (if applicable). Templates are how you scale; if you're not using them, you'll diverge across devices.
- **CLI scripts** — for custom config blocks not covered by GUI. Version-control the scripts (Git).
- **Backup / DR** — FortiManager DB snapshot + remote backup. FMG-as-secondary clustering for HA where the customer requires it.
- **Health monitoring** — FortiManager itself needs to be in monitoring (FortiAnalyzer or external).

---

## FortiAnalyzer deployment

- Sizing: log rate (logs/sec) × retention period. Use FortiAnalyzer sizing tool from docs.fortinet.com — don't eyeball.
- Storage type: SSDs for analytics, archive on slower tier if supported.
- **ADOM model** must match FortiManager ADOM model where both are deployed.
- Log forwarding from devices: configured on the device side (FortiGate) AND accepted on the FortiAnalyzer side (device authorization).
- SOC view vs reporting view — both are useful; tune dashboards before handover.
- Reports: schedule the recurring reports the customer needs (monthly compliance, weekly threat summary). Don't leave this to ops.
- Forwarding to FortiSIEM / external SIEM via syslog — verify format compatibility (CEF/LEEF vs Fortinet native).

---

## FortiSwitch + FortiAP (FortiLink-managed)

### FortiSwitch via FortiLink

- FortiLink interface configured on the FortiGate (dedicated physical port group or LAG).
- FortiSwitch in FortiLink mode (factory default for new units; reset if previously standalone).
- Zero-touch provisioning works when DHCP options are configured properly; for static IP environments, pre-stage management IPs.
- VLANs are managed from the FortiGate side under `config switch-controller`. Don't edit FortiSwitch CLI directly — it diverges from FMG/FortiGate config.
- PoE budget: verify per-port budget vs total budget vs simultaneous load. PoE+ vs PoE++ depends on model.
- Stacking / MCLAG: validate the topology against the specific FortiSwitch model's stacking guide; not all combinations supported.

### FortiAP via FortiLink (or FortiGate-managed standalone)

- AP profile design first — SSIDs, security mode (WPA2 vs WPA3), VLAN per SSID, captive portal.
- 5 GHz channel planning for dense deployments — DFS channels available in EU; verify per country regulatory.
- 6 GHz (Wi-Fi 6E / 7) — verify model support; ETSI rules in EU constrain power and channel use vs FCC.
- Roaming: 802.11k/v/r — enable per profile if clients support.
- FortiPresence / location services — add-on, not default.
- For large deployments, FortiCloud-managed (FortiAP Cloud) is an alternative to FortiGate-managed FortiLink — choose based on operational model, not technical preference.

---

## FortiSASE deployment

Reference: `references/solution-architecture.md` for design patterns. Implementation specifics:

- **Tenant provisioning** in FortiCloud — region selection (EU PoPs for DACH residency: typically Frankfurt, Amsterdam, Zurich; verify current PoP list at provisioning time).
- **Identity provider integration** — Entra ID / Okta / Google / on-prem AD via FortiAuthenticator. SCIM where available for user/group sync.
- **FortiClient deployment** — package downloaded from the FortiSASE tenant; deploy via Intune / Workspace ONE / Jamf / SCCM. Pre-configure the SASE profile so users don't need to enter anything.
- **Posture checks** — define the posture tags up front (managed device, OS patch level, EDR running, disk encryption); apply differentially per app/policy.
- **Inline CASB** — define which SaaS apps are sanctioned, which are tolerated, which are blocked. Expect tuning iterations during pilot.
- **Private access (ZTNA)** — connector deployment in DC / cloud. Define apps, set up access policies. ZTNA proxy on FortiGate is the alternative for self-hosted.
- **DNS filtering** — enable from start for visibility even if blocking policy is conservative.
- **Logging integration** — to FortiAnalyzer / FortiSIEM. Verify retention covers compliance needs.
- **Pilot wave**: small group (10–20 users), 2 weeks, structured feedback, then expand.

---

## FortiClient EMS deployment

- EMS instance: on-prem vs FortiClient Cloud. FortiClient Cloud (now FortiSASE-bundled in some packages) reduces ops; on-prem EMS gives full control.
- Endpoint profile design: ZTNA, EDR, vulnerability scan, web filter, USB control. Profiles per persona (admin, user, contractor).
- Deployment package generation in EMS → distribution via standard MDM/endpoint mgmt.
- ZTNA tags on FortiClient → consumed by FortiGate / FortiSASE policies.
- Integration with FortiSandbox, FortiEDR/FortiEndpoint, FortiAnalyzer.

---

## FortiSIEM / FortiSOAR deployment

- Sizing first — events per second (EPS), retention, parsing complexity. EPS is usually under-estimated; budget headroom.
- Architecture: super, worker, collector tiers. Collectors close to log sources for bandwidth efficiency.
- Parser tuning — out-of-box parsers for Fortinet products are good; expect tuning for non-Fortinet sources.
- CMDB hygiene — discovery scopes, credentials, business services. CMDB drives correlation; bad CMDB = noisy SIEM.
- Use cases / rules — start with the Fortinet-shipped rule pack, then add customer-specific rules iteratively. Don't enable everything on day one — alert volume kills SOC adoption.
- FortiSOAR playbooks — start with 3–5 high-value automations (phishing triage, malware response, account compromise, brute-force, IOC lookup). Expand from there.
- Integration map — which connectors are needed (AD, ITSM, EDR, threat intel, ticketing). Document credentials and scope.

---

## OT / industrial deployments

Detailed in `references/ot-security.md`. Implementation-specific notes:

- **Never** deploy OT firewalls without a working OOB management plan — IT-style remote management often violates OT change-control rules.
- Engage the OT/process-engineering team **before** the IT team — OT projects fail when IT runs them in isolation.
- Deploy in **monitor mode** first (sniffer / SPAN), build a baseline, then enforce. Day-1 enforcement on an unfamiliar OT environment is how you cause an outage.
- Industrial protocols (Modbus, DNP3, S7, OPC UA, EtherNet/IP, BACnet, IEC 60870-5-104) — verify protocol support against the specific FortiOS version + Industrial Security service.
- Ruggedized hardware (FortiGate Rugged series) for harsh environments — temperature, shock, vibration ratings.

---

## Cutover patterns

### The cutover runbook

A cutover runbook is **executable** — every step has a command, expected output, pass/fail criterion, and rollback action. Template in `assets/templates/troubleshooting-runbook.md` (the format adapts for cutover too).

Sections every cutover runbook needs:

1. Pre-cutover validation (all green before starting)
2. Comms plan (who's in the war room, escalation tree, status update cadence)
3. Step-by-step actions with timing
4. Validation steps after each major action
5. Decision points (go/no-go gates)
6. Rollback procedure (full and partial)
7. Post-cutover validation (smoke tests + business validation)
8. Sign-off criteria

### War-room discipline

- One technical owner with the keyboard. Others observe, advise, document.
- Status updates on a fixed cadence (every 30 min during cutover, hourly during stabilization).
- Issues logged in real time — don't trust memory.
- Hard rollback gate at a defined time (e.g., "if not green by 04:00, we roll back regardless").

---

## Day-2 / handover

- **As-built documentation**: HLD updated to reflect actual deployment, LLD with all config-relevant details (interfaces, IPs, VLANs, BGP ASNs, IPsec parameters, HA priorities, SD-WAN rules, policy structure).
- **Ops runbook**: routine tasks (cert renewal, FortiGuard updates, backup verification), incident playbooks (HA failover, link failure, license expiry), escalation matrix.
- **Monitoring**: FortiAnalyzer dashboards, FortiManager device health, optional integration with NMS (PRTG, Zabbix, Datadog, Dynatrace).
- **Knowledge transfer**: structured sessions, not "shadowing." Cover normal ops, common incidents, escalation, change procedure.
- **Hypercare**: 2–4 weeks of close monitoring with the deployment team available. Defined exit criteria (incident count, severity, response time).
- **Lessons learned**: internal retro within 2 weeks of project closure. Captures what should improve in the next deployment.

---

## Common implementation pitfalls

| Pitfall | Why it happens | How to avoid |
|---|---|---|
| Time skew between FortiGate / FortiManager / FortiAnalyzer | NTP not configured first | NTP step #4 in build sequence |
| Logs missing in FortiAnalyzer | Device authorized but log forwarding misconfigured | Validate end-to-end log path during build |
| HA failover doesn't work in production despite working in lab | Heartbeat interface shared with data; or asymmetric routing post-failover | Dedicated heartbeats + monitor priority interfaces + failover drill in pilot |
| FortiSwitch shows offline in FortiGate | FortiLink trust mismatch / version skew | Pre-stage in lab; verify before shipping to site |
| FortiClient policy doesn't apply | EMS posture tag not propagating; cert trust on endpoint | Pilot phase exposes this; verify ZTNA token flow end-to-end |
| Policy bloat after migration | FortiConverter output accepted as final | Always treat conversion as draft; clean up |
| FortiManager push fails after manual CLI on FortiGate | Out-of-band changes break revision baseline | Enforce FMG-only changes; if CLI is required, sync back to FMG immediately |
| BGP convergence too slow during failover | Default 180s holdtime, no BFD | Tune holdtime + enable BFD where supported |
| SSL DPI breaks specific apps | Cert trust issues / cert pinning / TLS 1.3 | Pilot with the affected user group; build exemption list |
| FortiSASE PoP latency higher than expected | Wrong PoP region / ECMP picking suboptimal path | Verify PoP selection at tenant provisioning; test from end-user network |

---

## Documentation deliverables (minimum set)

- [ ] HLD (high-level design) — architecture, design decisions, alternatives considered
- [ ] LLD (low-level design) — IPs, VLANs, interfaces, routing, IPsec, policies, HA, SD-WAN, UTM profiles
- [ ] As-built — LLD updated post-deployment with reality
- [ ] BoM with serial numbers, license entitlements, contract IDs
- [ ] Runbook for ops (routine + incident)
- [ ] Cutover and rollback procedures (archived after cutover, kept for audit)
- [ ] Test report — test cases executed, results, issues found and resolution
- [ ] Sign-off document — customer acceptance, scope completion, hypercare exit
