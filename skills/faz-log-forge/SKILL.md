---
name: faz-log-forge
description: >-
  Generate synthetic FortiGate logs that import cleanly into a FortiAnalyzer, populating demo
  environments with assets, IoT/OT devices, traffic, VoIP calls, security events and a
  Security Rating stream that do not exist in real life. Use whenever the user wants to feed
  FortiAnalyzer dashboards, FortiView, Asset Identity Center, the IoT dashboard, OT View,
  Compromised Hosts, Security Rating / FSBP / PCI reports or playbooks with fake-but-realistic
  data; asks why OT/IoT or endpoint vulnerabilities do not show up in FortiAnalyzer and what
  a log import can do about it; wants a FAZ demo, lab or PoC dataset; or asks about "execute
  log import", backfilling FortiGate logs, FortiGate raw log format, FortiAnalyzer CSV
  exports, the fgt-security-rating (Xlog) stream or FG-IR PSIRT checks. Also triggers on FAZ
  demo data, FAZ log generator, synthetic or fake FortiGate logs, populating the IoT dashboard,
  FortiGate traffic generator, and ingesting real FortiAnalyzer exports to extend the generator.
---

# FortiAnalyzer log forge

Generates FortiOS-native raw log files (`date=... time=... key=value ...`) for FortiGates
that do not exist, so a FortiAnalyzer demo has assets, IoT and OT devices, application
traffic, VoIP calls, threats, incidents and a Security Rating to display.

Field names, values, log IDs and quoting are taken from real FortiOS 7.6.6 and 8.0.0 logs,
from FortiAnalyzer CSV exports of the same units, and from Fortinet's published log message
reference. Where a value could not be verified it is flagged in the references rather than
guessed - **keep it that way**. The audience for these logs is Fortinet SEs and their
customers, who will spot an invented `attackid`, a `devtype` string their own FortiGate never
emits, or a PSIRT ID that does not exist.

## Workflow

1. **Clarify** (unless the user already said): which fleet, how many days, which FortiOS
   version (7.6 or 8.0 - it changes `logver`, a few log IDs and the PSIRT check set), and
   which use cases matter. Ask what they want the demo to *show*, not what logs they want.
   If the answer involves "vulnerabilities", read the boundary in section "Four things"
   below first and tell the user before generating.
2. **Generate.** `python3 scripts/fazgen.py --fleet <n> --days <n> --out <dir> ...`
3. **Verify.** `python3 scripts/verify_logs.py <dir>` - always run this. It catches missing
   envelope fields, date/eventtime drift, wrong quoting, field names FortiOS does not emit,
   reports asset-field coverage, and cross-checks the security-rating stream's vulnerable
   MAC list against `assets.csv`.
4. **Hand over.** The output directory contains the log files (`tlog` traffic/UTM, `elog`
   events, `plog` VoIP, `xlog` security rating), `assets.csv` (the asset inventory with
   Purdue level and `iot_vulncnt`, useful for a slide or for seeding a FortiGate device
   store) and `IMPORT.md` (the runbook with the exact CLI for this dataset and the section
   on what the dataset cannot show).

## Commands

```bash
python3 scripts/fazgen.py --list-fleets

python3 scripts/fazgen.py \
  --fleet ot-manufacturing \
  --days 21 --start 2026-08-01 \
  --version 8.0 --scale small \
  --scenarios ot-intrusion,camera-c2,inbound-scan,shadow-iot \
  --rating-posture typical --psirt-fail FG-IR-25-254 --rating-remediate-after 14 \
  --devid FGVMEVDEMO0000002 --devname DEMO-OT-FGT-01 \
  --out ./demo-ot

python3 scripts/verify_logs.py ./demo-ot
```

Useful flags: `--vdom` (default root), `--tz` (UTC offset hours, default +2), `--seed`
(deterministic - same seed gives the same MACs, IPs and vulnerable devices, so re-running
does not duplicate assets in FortiAnalyzer), `--gzip`, `--devtype-mode verified` (restrict
`devtype` to strings observed in real FortiOS logs), `--no-ot-appctrl` (drop the unverified
OT application names), `--vuln-ratio 0.3` (share of IoT/OT assets the FortiGuard lookup
flags), `--rating-posture good|typical|poor`, `--psirt-fail FG-IR-..,..` (unpatched
FortiGate story), `--rating-remediate-after N` (score improves from day N), `--no-rating`,
`--xlog-format csv|raw`.

To extend the PSIRT/check catalogue from a newer FortiAnalyzer export of the security-rating
stream: `python3 scripts/ingest_rating_export.py --export 8.0=<export>.csv`.

## Fleets

| Fleet | Assets | What it demonstrates |
|---|---|---|
| `enterprise` | 150 | Corporate HQ: offices, datacenter, IoT VLAN, VoIP, printers, cameras, guest wifi |
| `ot-manufacturing` | 124 | Purdue-layered plant: PLCs, HMIs, robots, drives, historian, engineering workstations, physical security |
| `healthcare` | 165 | Hospital: patient monitors, infusion pumps, imaging, lab analyzers, clinical workstations, patient wifi |
| `smartbuilding` | 140 | BMS, HVAC, lighting, access control, elevators, EV charging, PV |
| `retail` | 114 | Branch: POS, handheld scanners, digital signage, cameras, customer wifi |

To build a new fleet, copy a file in `data/fleets/` and edit it. A fleet defines zones
(subnet, interface name, role, activity curve, policy IDs) and how many of each device model
sits in each zone. Device models come from `data/devices.json`; each carries its FortiOS
attribute tuple (`devtype`, `osname`, `srcfamily`, `srchwvendor`, `srchwversion`,
`srcswversion`), a Purdue level and a behaviour list. Adding a model needs a vendor that
exists in `data/oui.json` so its MACs come from a real IEEE OUI block. Hosts with the `voip`
role produce SIP call logs; hosts with an IoT/OT role can carry an `iot_vulncnt`.

## Scenarios

`shadow-iot`, `camera-c2`, `ransomware`, `ot-intrusion`, `cryptomining`, `inbound-scan`,
`vpn-bruteforce`. Each has a per-day probability so a long dataset gets a realistic scatter;
append `:<probability>` to override it, e.g.
`--scenarios "ransomware:1.0,camera-c2:0.8,inbound-scan"` for a threat-heavy demo.
See `references/scenarios.md` for what each emits and which FortiAnalyzer view it targets.

## Four things that will waste an afternoon if you skip them

1. **The device must exist in FortiAnalyzer before you import.** Device Manager > Add Device
   > Link Device By: Serial Number. A model device added by serial is authorized immediately.
   `execute log import` rejects any serial that is not already in the device list.
2. **Backdated logs are silently dropped** if `config system sql` `start-time` /
   `rebuild-event-start-time` or the ADOM's *Keep Logs for Analytics* window is newer than
   the log dates. The import reports success and FortiView stays empty.
3. **Purdue level is not a log field.** OT View groups on an asset attribute held in the
   FortiGate device store and carried over the Security Fabric, not on anything in a log
   record. Logs alone populate the Asset Identity Center and the IoT dashboard, but not the
   OT View topology. `assets.csv` carries the Purdue level so you can set it separately.
4. **Per-asset vulnerabilities are not a log field either.** The CVE list behind the
   *Vulnerabilities* column in Asset Identity Center and the OT/IoT vulnerability widgets
   comes from the FortiGate device store over the OFTP endpoint data link (FortiOS 7.4+, OT
   Security Service on both units; check with `diagnose test application oftpd 20 fgt-stat`).
   Endpoint vulnerabilities come from the EMS connector playbook. What logs can carry is a
   `vulncnt` per device (`0100020150`) and the security-rating check
   `FortiguardIotVulnerability`, which fails and lists the vulnerable devices by MAC - and
   that stream feeds Fabric View > Security Rating, not the asset list. Say this to the user
   **before** they import anything expecting CVEs; the details and the only real fix (a live
   FortiGate in the Fabric) are in `references/assets-and-iot.md`.

Also: the IoT dashboard is licence-gated (IoT Detection Service on the FortiGate for IoT
devices, OT Security Service on both FortiGate and FortiAnalyzer for OT devices). No amount
of log data will fill it without the entitlement. And whether `execute log import` accepts
the security-rating stream at all is unverified - the runbook says how to test it.

## References

Read the relevant one before changing the generator or answering a question about the format.

| File | Contents |
|---|---|
| `references/log-anatomy.md` | raw vs FAZ-CSV format, quoting rules, field order (including the VoIP family's own spellings), the four timestamp fields, `logver`, the FortiAnalyzer envelope |
| `references/log-types.md` | per type/subtype field sets and log IDs, with `[lab]` / `[doc]` / `[ref]` provenance on every claim, plus the FortiGuard category map |
| `references/assets-and-iot.md` | what populates Asset Identity Center vs the IoT dashboard vs OT View, **where vulnerabilities really come from**, the `devtype` taxonomy and its two tiers, MAC/OUI handling, OT application control |
| `references/security-rating.md` | the `fgt-security-rating` (Xlog) stream: what it feeds, record anatomy, recommendation element types, scheduler cadence, the IoT-vulnerability and PSIRT checks, unknowns |
| `references/faz-import.md` | `execute log import` syntax, model devices, the SQL start-time trap, verification commands, alternative injection paths |
| `references/scenarios.md` | scenario catalogue, baseline streams, how to add one, volume guidance |

## Data files

| File | Contents |
|---|---|
| `data/catalog.json` | FortiGuard web filter categories, application catalogue (`app`/`appid`/`appcat`/`apprisk`), verified IPS signatures and DoS anomalies, verified `devtype`/`osname`/`srcfamily`/`appcat` value lists |
| `data/devices.json` | ~55 device models with their FortiOS attribute tuples and behaviours |
| `data/oui.json` | 104 vendors mapped to real IEEE OUI prefixes |
| `data/fleets/*.json` | fleet blueprints |
| `data/security_rating_checks.json` | 351 security-rating checks (107 configuration, 244 FG-IR PSIRT) with severity, title, observed results, recommendation shapes and per-run multiplicity per FortiOS line; rebuilt by `scripts/ingest_rating_export.py` |

## Scripts

| File | Purpose |
|---|---|
| `scripts/fazgen.py` | the generator (traffic, UTM, events, VoIP, scenarios, output files, runbook) |
| `scripts/rating.py` | the security-rating stream model and its two writers (FAZ-export CSV, raw guess) |
| `scripts/verify_logs.py` | pre-import sanity checks for every output stream |
| `scripts/ingest_rating_export.py` | turns real FortiAnalyzer Xlog CSV exports into the check catalogue |
