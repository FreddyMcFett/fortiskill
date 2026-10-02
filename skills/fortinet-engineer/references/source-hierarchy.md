# Fortinet Source Hierarchy — Navigation and Citation Guide

This reference explains **where** authoritative Fortinet information lives, **how** to find it efficiently, and **how** to cite it. The skill's anti-hallucination guarantee depends on actually using these sources, not just naming them.

## Table of contents

1. The hierarchy (recap)
2. docs.fortinet.com — navigation patterns
3. Fortinet Knowledge Base — search and citation
4. Datasheets — what they tell you and what they don't
5. Ordering guides — SKU and bundle authority
6. Service descriptions — SaaS/cloud SLA authority
7. Community Forum — when to use, how to cite
8. Third-party sources — when, how, and why explicit flagging matters
9. Search recipes (effective queries per source)
10. Citation format reference

---

## 1. The hierarchy

| Tier | Source | Reliability | Use for |
|---|---|---|---|
| 1 | docs.fortinet.com | Canonical | Product behavior, CLI, configuration, supported features, release notes, hardware guides |
| 2 | community.fortinet.com Knowledge Base | Authoritative | Known issues, workarounds, edge configurations, technical tips |
| 3 | Datasheets (fortinet.com/products/...) | Authoritative for specs | Throughput, port counts, performance figures (always tied to FortiOS version they were measured under) |
| 4 | Ordering guides (fortinet.com/resources/ordering-guides) | Authoritative for SKUs | License bundles, SKU composition, FortiCare tiers, FortiFlex points |
| 5 | Service descriptions (service.fortinet.com or product PDFs) | Authoritative for SaaS scope | SLA, scope, customer/Fortinet responsibility split |
| 6 | community.fortinet.com Discussions | Real-world but unverified | User experience, deployment war stories — **mark as community-sourced** |
| 7 | Reddit (r/fortinet, r/networking, r/sysadmin), blogs, third-party vendor pages | Last resort | Sentiment, third-party perspective — **explicitly flag** |

**Single rule**: every non-trivial claim is anchored to a tier. If you can't anchor it, say so.

---

## 2. docs.fortinet.com — the canonical source

### URL structure

The docs library uses a versioned, product-scoped URL pattern:

```
https://docs.fortinet.com/document/<product>/<version>/<guide-type>/<topic-id>/<slug>
```

Examples:
- `https://docs.fortinet.com/document/fortigate/7.6.6/administration-guide/...` — FortiOS 7.6.6 admin guide
- `https://docs.fortinet.com/document/fortigate/7.6.6/fortios-release-notes/...` — release notes
- `https://docs.fortinet.com/document/fortianalyzer/7.6.0/administration-guide/...` — FortiAnalyzer 7.6 admin guide
- `https://docs.fortinet.com/document/fortimanager/7.6.0/administration-guide/...`
- `https://docs.fortinet.com/document/fortisase/24.4/administration-guide/...` — FortiSASE follows a release-name versioning scheme (e.g., 24.4)
- `https://docs.fortinet.com/document/fortiswitch/7.6.5/administration-guide/...`

### Guide types you'll need most

- **administration-guide** — primary day-to-day reference; CLI, GUI, feature behavior
- **fortios-release-notes** — version-specific changes, known issues, upgrade info
- **cli-reference** — full CLI command reference per version (the authoritative source for command syntax)
- **cookbook** — step-by-step recipes for common deployment scenarios
- **hardware-guide** — physical specs, port maps, transceivers, power, environmental
- **upgrade-path-tool** — official upgrade-path checker (use this, do not guess upgrade paths)
- **rest-api-reference** — API endpoints, payload schemas, response codes
- **new-features-guide** — what's new in a release (use as a starting point, but always verify in admin guide for behavior)
- **best-practices** — Fortinet's published deployment recommendations
- **virtualization-guide** — VM-specific (VMware, KVM, Hyper-V, AWS, Azure, GCP, OCI)

### Version selection

The site has a version dropdown per product. **Always check** that the URL or page shows the version the user is asking about. Same product, different version → different behavior.

For FortiGate as of late 2026:
- **7.6.6** — current GA (released Feb 2026, builds at 3652)
- **7.6.x** — active maintenance branch
- **7.4.x** — mature, still supported, common in production
- **7.2.x** — older, security-only support window narrowing
- **8.0** — announced at Accelerate 2026 (March 2026), early adoption

Always confirm the current version snapshot before answering — release cadence is roughly quarterly for maintenance and ~annually for major.

### Document Library entry points

- Top-level: <https://docs.fortinet.com/>
- By 4D Pillars / 3 Pillars: shows products grouped under Secure Networking, Unified SASE, Security Operations
- By Cloud: shows cloud-specific deployment guides per hyperscaler
- All Products: A–Z product list

For a specific product, fastest path is:
1. Search `<product> docs fortinet` → land on the product hub
2. Pick version from dropdown
3. Pick guide type from left nav

### Language

A language selector exists in the top-right of docs pages. Coverage of non-English languages is partial — major admin guides have German/French/Japanese/Spanish/Chinese for some products; cookbook content and release notes are typically EN-only. **Default to English** for engineering accuracy and translate yourself where needed.

---

## 3. Fortinet Knowledge Base

The KB lives at `community.fortinet.com` under the **Knowledge Base** tab (separate from Discussions). It contains:

- Technical Tips
- Troubleshooting Tips
- Configuration Guides for specific scenarios

### URL pattern

```
https://community.fortinet.com/t5/<product-board>/<title-slug>/ta-p/<id>
```

The `ta-p` segment indicates a Knowledge Base **article** (vs `td-p` for a discussion thread). Always check this — articles are Fortinet-authored, threads are user-generated.

### When to reach for the KB

- A behavior is documented in the admin guide but the *symptom* isn't matched
- You suspect a known issue on a specific build
- You need a workaround that the admin guide doesn't describe
- You need step-by-step for an edge case (e.g., specific cloud-VM bootstrap, hairpin NAT topologies, BGP route-reflector with overlay)

### Search pattern

Direct search on community.fortinet.com is the most reliable path. Useful patterns:

```
"Technical Tip" <feature> <symptom>
"Troubleshooting Tip" <subsystem>
```

Or via Google / web search:
```
site:community.fortinet.com <topic>
```

### Citation

Cite the KB article ID and full URL. Example: `[Verified, KB FD51234 — community.fortinet.com/t5/.../ta-p/281234]`.

---

## 4. Datasheets

Datasheets are the authoritative source for **hardware specs and performance numbers**. They are **not** authoritative for feature behavior — that lives in admin guides.

### Where to find them

- Product page: `fortinet.com/products/<product>` → Datasheets / Resources
- Direct URL pattern: `fortinet.com/content/dam/fortinet/assets/data-sheets/<product>.pdf`
- Resource library: `fortinet.com/resources/datasheets`

### What datasheets give you

- Model lineup with relative positioning
- Hardware specs: CPU, RAM, NPU/CP/SP presence, port counts, port types (SFP/SFP+/SFP28/QSFP/QSFP28/QSFP-DD), PoE budget, console/management ports, storage, environmental
- Performance figures (throughput, IPS, NGFW, SSL inspection, IPsec VPN, concurrent sessions, new sessions/sec)
- Approximate user/CPE-count guidance
- VM specs and scaling for VM editions

### What datasheets do NOT give you

- Per-feature behavior or limitations (that's the admin guide)
- Version-by-version delta (that's release notes)
- Real-world performance under your specific traffic mix (datasheet figures are lab figures, typically with specific traffic profiles — see footnotes)
- SKU / pricing detail (that's the ordering guide)

### Reading datasheet performance numbers

Datasheets always footnote the test methodology and the FortiOS version. Two critical implications:

- **Traffic profile matters**. "IPS throughput" tested with HTTP transactions of a specific size will not match throughput in a customer's traffic mix.
- **FortiOS version matters**. NPU offload paths and inspection engines change between versions. A figure measured on FortiOS 7.4 may differ on 7.6.

Always include both in citations: `[Datasheet, FortiGate-100F rev Feb 2026, FortiOS 7.6 measured]`.

---

## 5. Ordering guides

Authoritative for **SKUs, license bundles, FortiCare tiers, and bundle composition**. The structure of Fortinet's commercial offering changes — these guides are versioned and dated; always use the current one.

### Where to find them

- Library: <https://www.fortinet.com/resources/ordering-guides>
- Filter by product to find the specific guide

### What ordering guides cover

- Hardware model SKUs (e.g., `FG-100F`, `FG-100F-BDL-950-12`)
- Software / VM model SKUs
- Subscription bundles:
  - **A-la-carte / individual services** (FortiGuard IPS, AV, Web Filter, App Control, Antispam, FortiSandbox Cloud, FortiCASB Cloud, FortiAI subscription, etc.)
  - **UTP** (Unified Threat Protection) — bundled traditional UTM services
  - **Enterprise Bundle (ENT)** — UTP + SD-WAN + ZTNA + additional services
  - **ATP** (Advanced Threat Protection) — narrower bundle focused on threat prevention
  - **SP** (Security Protection) — varies; check current guide
- FortiCare support tiers:
  - **FortiCare Essential** (basic 24x7 break/fix)
  - **FortiCare Premium** (faster SLA)
  - **FortiCare Elite** (including Advanced Hardware Replacement, dedicated TAM-style features in some packages)
- FortiFlex consumption-based licensing options
- Specific add-ons (FortiPAM seats, FortiAuthenticator user counts, FortiAnalyzer storage upgrades, etc.)

### What changes regularly

Bundle composition shifts over time. **Never quote bundle contents from memory** — always pull the current guide. Recent shifts to be aware of:
- ZTNA being moved into ENT
- FortiAI subscription emerging as a separate or bundled item depending on product
- FortiSASE consumption units evolving
- FortiCare tier names having been simplified/renamed in past iterations

### Citation

`[Ordering guide, FortiGate <month/year of guide>]` and link to the PDF.

---

## 6. Service descriptions

For SaaS or cloud-delivered services (FortiSASE, FortiAnalyzer Cloud, FortiManager Cloud, FortiClient Cloud, FortiSandbox Cloud, FortiGate-CNF, FortiAppSec Cloud, FortiMail Cloud, FortiCASB, FortiCNAPP, FortiSOC), the **service description** is the authoritative source for:

- Service scope (what's included)
- SLA (uptime, response/restoration targets)
- Data residency (region availability)
- Customer responsibility vs Fortinet responsibility (the shared-responsibility model for that service)
- Data retention and deletion policies
- Security controls and certifications (ISO 27001, SOC 2, FedRAMP where applicable)

### Where to find them

- `service.fortinet.com` — central portal
- Per-product service description PDFs, often linked from the product page or available via the Fortinet Trust Center (`fortinet.com/trust`)

### Why this matters in DACH

Swiss/EU customers often have explicit data-residency requirements. Service descriptions tell you which regions each SaaS offers. Check before promising data residency to a customer — region availability changes (PoPs added/retired).

---

## 7. Community Forum (Discussions)

The Discussions tab at `community.fortinet.com` is user-generated. Useful for:

- Confirming someone else has hit the same symptom
- Finding an in-flight workaround before a KB is published
- Sentiment / common gotchas

**Citation requirement**: always mark as `[Community-sourced, <link>]`. Cross-check the underlying claim against an authoritative source before treating as fact. A Discussions thread suggesting "it works if you do X" can be wrong, outdated, or version-mismatched.

---

## 8. Third-party sources

In order of typical reliability:

- **Fortinet Fuse** community (a Fortinet-run user community) — semi-authoritative; treat as Discussions
- **Reddit** (r/fortinet, r/networking, r/sysadmin) — useful for sentiment, hit-or-miss for technical accuracy
- **Independent Fortinet bloggers** (e.g., Yuri Slobodyanyuk, FortinetGuru, the network engineer's individual blog scene) — quality varies wildly; some are authoritative, many are outdated
- **YouTube** — useful for visual walkthroughs; always verify command syntax against docs
- **Vendor comparison content** (Gartner, Forrester, NSS Labs successors, third-party test labs) — useful for positioning, not for technical claims

**The user's preference is explicit**: "if you take something from reddit, please mark it and say this comes from reddit." Honor this. Tag third-party sources clearly:

- `[Reddit, r/fortinet thread <link>]`
- `[Third-party blog, <author> <link>]`
- `[Third-party report, <publisher> <date>]`

Never cite third-party as the sole source for a load-bearing claim. If a third-party source makes a technical claim, find the corresponding docs.fortinet.com / KB confirmation before relying on it.

---

## 9. Search recipes

### docs.fortinet.com

Direct search on docs is sometimes weaker than Google site search:

```
site:docs.fortinet.com <feature> <version>
```

For CLI command lookup:
```
site:docs.fortinet.com "config <command>" <version>
site:docs.fortinet.com "diagnose <subsystem>" <version>
```

For known-issue verification:
```
site:docs.fortinet.com "release-notes" <version> <symptom keyword>
```

### Knowledge Base

```
site:community.fortinet.com "Technical Tip" <feature>
site:community.fortinet.com "Troubleshooting Tip" <symptom>
"FD" <id-or-keyword> fortinet
```

### Datasheets

```
"FortiGate-<model>" datasheet site:fortinet.com
site:fortinet.com/content/dam/fortinet/assets/data-sheets <product>
```

### Ordering guides

```
"<product> ordering guide" site:fortinet.com
site:fortinet.com/resources/ordering-guides <product>
```

### Service descriptions

```
"service description" <product> site:fortinet.com
```

---

## 10. Citation format reference

For inline use in any response:

| Source type | Citation format |
|---|---|
| docs.fortinet.com | `[Verified, docs.fortinet.com — <full URL>]` |
| Specific admin-guide page | `[FortiOS 7.6.6 admin guide, <section name> — <URL>]` |
| Release notes | `[FortiOS 7.6.6 release notes, <section> — <URL>]` |
| KB article | `[KB <FD-id>, <URL>]` |
| Datasheet | `[Datasheet, <product> rev <date>]` |
| Ordering guide | `[Ordering guide, <product> <date>]` |
| Service description | `[Service description, <product> <date>]` |
| Community thread | `[Community-sourced, <URL>]` |
| Reddit | `[Reddit r/<sub> — <URL>]` |
| Third-party blog | `[Third-party blog, <author> — <URL>]` |
| Training data only | `[Training data, unverified — recommend confirming in <specific source>]` |
| Inferred across multiple | `[Inferred from <sources>]` |

These tags belong **inline** next to the specific claim they support, not as a footer block. Trivial framing sentences ("FortiSASE is Fortinet's SSE offering") don't need tags; non-trivial technical claims do.

### Anti-pattern: source laundering

Do not present a third-party blog claim as if it were Fortinet-authoritative just because the blogger sounds confident. Do not present a community thread as a KB. Do not present an inferred conclusion as a verified fact. The tagging is the integrity check.
