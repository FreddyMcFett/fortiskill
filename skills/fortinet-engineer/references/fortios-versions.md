# FortiOS Versions

Version selection, feature deltas, EoL/EoS, upgrade paths. **Verify all dates against fortinet.com / docs.fortinet.com at the time of any binding decision** — this reference captures the shape of how Fortinet versions move, but specific dates drift.

---

## How Fortinet versions FortiOS

- **Major.Minor** (e.g., 7.6) — feature releases, typically annual cadence.
- **Major.Minor.Patch** (e.g., 7.6.6) — maintenance releases on the train; patches roll roughly monthly during active life of the train.
- **GA designation** — the recommended version on a train, typically a few patches in (not the very first .0). Look for the **"Mature" / "Recommended"** label on the Fortinet image-download portal.
- **Branch lifecycle**:
  - **Active** — receives features and fixes (current train)
  - **Maintenance** — receives security and stability fixes only
  - **EOE / EOS / EOL** — End of Engineering / Support / Life — drives renewal and upgrade timing decisions

For binding statements, always check the **Fortinet Product Lifecycle** page at fortinet.com → Support → Product Life Cycle.

---

## Current state (as of skill build, late April 2026)

- **FortiOS 7.6.6** — current GA (build 3652, released February 2026). This is the default recommended train for new deployments and refresh projects.
- **FortiOS 7.4.x** — mature, widely deployed, in maintenance. Many production environments are still on 7.4 — not a problem in itself, but new features ship to 7.6.
- **FortiOS 7.2.x** — older, increasingly nearing EoE; review upgrade plan if customer is here.
- **FortiOS 7.0.x** — old; EoE/EoS dates approaching or passed depending on the patch level. Migration recommended.
- **FortiOS 6.4.x and earlier** — EOL or near-EOL. Strongly recommend upgrade.
- **FortiOS 8.0** — announced at Accelerate 2026 (March 10, 2026). Themes: AI controls, fabric-based AI agents, flexible SASE, quantum-safe cryptography. Mainstream availability typically 6–12 months after announcement; expect 8.0.x GA candidate to land in late 2026 / early 2027. **Not a recommended target for production deployment until GA matures (typically 8.0.2 or 8.0.3).**

For any version-specific question: ask the user to confirm version. The default assumption in this skill if unspecified is **FortiOS 7.6.6 GA**.

---

## Train selection — which version for what

| Scenario | Recommended train |
|---|---|
| New deployment, refresh, or greenfield | Current GA (7.6.x at time of writing) |
| Conservative environment, mature ops | Mature recommended (7.4.x) |
| Production-critical with minimal change appetite | 7.4.x mature; plan annual upgrade reviews |
| Need a specific feature only in 7.6 | 7.6.x GA |
| OT environment | Mature recommended; OT shops generally lag 1 cycle for stability |
| Customer asking about 8.0 | "Announced; not yet recommended for production. Target 8.0.x GA when 7.6 train approaches end-of-engineering" |

Pinning principle: **don't drift mid-deployment.** Pick a target version at design time, lock it across the fabric, upgrade together as a planned activity.

---

## Feature deltas — recent trains (high level)

Always verify specific feature support in the **FortiOS What's New** document for the version in question. This summary is for orientation only.

### FortiOS 7.6 highlights (vs 7.4)

- **SSL VPN tunnel mode replaced by IPsec VPN** — `[Verified, docs.fortinet.com — FortiOS 7.6 What's New]`. Existing SSL VPN tunnel deployments need to migrate to IPsec when upgrading to 7.6+. SSL VPN web mode is now branded "Agentless VPN."
- **FortiSASE flexible SASE / FortiSASE consumption updates**.
- Additional ZTNA enhancements, posture controls.
- **Empty admin password deprecation** — `[Verified, FortiOS 7.6.1+]`: managed FortiSwitches no longer accept empty passwords.
- IPv6 enhancements across SD-WAN, ZTNA, SASE.
- Additional FortiAI integration points.
- Continued NPU offload coverage expansion (verify per platform in admin guide).

### FortiOS 7.4 highlights (vs 7.2) — for context

- ZTNA maturation (proxy + posture).
- SD-WAN enhancements.
- Security Fabric improvements.
- Various inspection and NP7 enhancements.

### FortiOS 8.0 announced themes

- AI controls / fabric AI agents.
- Quantum-safe cryptography (post-quantum cipher options).
- Flexible SASE evolution.
- Continued portfolio integration under the 3-pillar model (Secure Networking, Unified SASE, Security Operations) — not a versioned feature but a portfolio context.

For specifics, refer to the formal FortiOS 8.0 release notes when published.

---

## Upgrade paths

### Standard FortiGate upgrade path

Fortinet publishes the official **FortiOS Upgrade Path Tool** (at docs.fortinet.com or fortinet.com → Support → FortiGuard → Upgrade Path Tool). Always use the tool — direct upgrade between non-adjacent majors is often not supported and may require intermediate hops.

Common patterns:

- 7.4.x → 7.6.x: typically one-hop supported within compatible patch levels.
- 7.2.x → 7.6.x: usually requires 7.4 hop.
- 7.0.x → 7.6.x: usually requires multiple hops.
- 6.4.x → 7.x: multi-hop, larger lift, more risk.

### Pre-upgrade checklist

- Read the **release notes** for every hop. Known issues, removed features, behavioral changes.
- Check the **upgrade path tool** for the supported route.
- Validate **license entitlement** — some new features require updated licenses.
- **Backup config** before each hop. Save with hostname + version + timestamp.
- Validate **HA pair compatibility** — HA upgrade requires both units on the path; brief asymmetry windows are normal but bounded.
- For FortiManager-managed devices: upgrade FortiManager first (FMG version must be ≥ device version).
- Test in **lab** for non-trivial upgrades.

### FortiManager upgrade

- FortiManager version ≥ all managed FortiOS versions.
- Upgrade FortiManager first; validate ADOM revisions and device sync.
- Plan FortiAnalyzer upgrade in the same window for fabric coherence.

### FortiAnalyzer upgrade

- Maintain compatibility with FortiManager and managed devices.
- Storage layout migrations across major versions can take time — read release notes.

### FortiSwitch / FortiAP firmware

- Managed via FortiGate (FortiLink) or via FortiManager / FortiAP Cloud.
- Compatibility matrix at docs.fortinet.com. Don't assume — check.

---

## EoO / EoS / EoL — the lifecycle gates

- **End of Order (EoO)** — last date you can purchase. Plan refreshes ahead of EoO of current models.
- **End of Sale (EoS)** — usually equivalent to or near EoO; date after which procurement is closed.
- **End of Engineering (EoE)** — no more new firmware fixes (security exceptions may remain).
- **End of Support (EoS support)** — no more TAC support.
- **End of Life (EoL)** — fully retired.

For binding compliance/risk decisions:

- Check fortinet.com → Support → Product Life Cycle for **per-model dates**. Don't generalize across model lines.
- For audit/compliance contexts (e.g., NIS2, ISO 27001), running EoE/EoS hardware is a finding waiting to happen — flag it in any health-check.

---

## Long-Term Support (LTS) considerations

Fortinet doesn't formally label "LTS" trains the way some other vendors do. The functional equivalent is the **Mature / Recommended** train designation on the download portal at any given time. When a customer asks "what's our long-term-stable choice?" the answer is the current mature recommendation, with a planned annual review against the lifecycle page.

---

## Version selection in customer-facing communication

When recommending a version to a customer:

- **State the version, the train, and why.** "FortiOS 7.6.6 — current GA recommended train, Feb 2026 release, current security and feature posture."
- **State the upgrade horizon.** "Plan to evaluate 8.0.x for adoption when the 8.0 train reaches GA-recommended maturity, likely late 2026 / early 2027."
- **State the lifecycle posture for old hardware.** If you're refreshing 5-year-old gear: "your existing X is at EoE Y; refreshing to current FortiGate Z model gives 5+ years of forward support."
- **Don't recommend the very latest .0 patch** for production. Wait for the recommended designation or at least 2–3 patches.

---

## Special cases

### FortiSASE versioning

FortiSASE is a SaaS service; its versioning is **decoupled from FortiOS**. Updates roll out by Fortinet to PoPs continuously; customers don't pin a "FortiSASE version." However, the **FortiClient** agent has its own versioning that must be kept current. Verify FortiClient version compatibility with the FortiSASE tenant in the FortiClient admin guide.

### FortiManager / FortiAnalyzer versioning

Tied loosely to FortiOS major (e.g., FortiManager 7.6.x corresponds to FortiOS 7.6.x). Maintain alignment.

### FortiSwitchOS and FortiAPOS

Versioned independently from FortiOS but with compatibility constraints. The FortiLink compatibility matrix at docs.fortinet.com is the authoritative source.

### FortiSIEM / FortiSOAR / FortiEDR / FortiNDR / FortiClient EMS

Independent versioning per product. Check the per-product release notes and compatibility matrices.

---

## Quick reference — the version question

Before any version-sensitive answer, ask the user (or state assumed default + invite correction):

1. FortiOS version on FortiGate? (default assumption: 7.6.6 GA)
2. FortiManager version? (if applicable)
3. FortiAnalyzer version? (if applicable)
4. FortiClient version? (if endpoint involved)
5. Any version pinning constraints (compliance, contractual)?

Then answer with version-specific verification.
