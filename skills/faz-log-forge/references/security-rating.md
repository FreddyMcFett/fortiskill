# The Security Rating stream (FortiAnalyzer "Xlog", msg_tag=fgt-security-rating)

Provenance: two FortiAnalyzer Log View CSV exports of this stream, FortiGate 90G on FortiOS
7.6.6 (9714 records, 22 scheduled runs, 2-9 Aug 2026) and FortiGate VM on FortiOS 8.0.0
(5701 records, 18 runs, 10-16 Aug 2026). Everything below tagged **[lab]** was read off those
files; **[doc]** is docs.fortinet.com. `data/security_rating_checks.json` is generated from
the exports by `scripts/ingest_rating_export.py`, and `scripts/rating.py` replays the model
described here.

## What it is and what it feeds

When a FortiGate runs its Security Rating (Security Fabric > Security Rating), it sends the
per-check results to its FortiAnalyzer as a stream of JSON messages. FortiAnalyzer stores them
outside the normal `type`/`subtype` log tables - the export file name calls them `Xlog` - and
uses them for:

- Fabric View > Security Rating (per-FortiGate score, failed checks, recommendations)
- the FSBP, PCI DSS, CIS Controls, ISO 27001 and NERC CIP security-rating report templates
  [doc, FortiAnalyzer 7.4 new features]
- the FortiView "Fabric State of Security" monitor

Two checks are the reason this stream matters for a vulnerability demo:

| Check | Meaning | Reference |
|---|---|---|
| `FortiguardIotVulnerability` | fails when the FortiGuard IoT/OT service found vulnerabilities on any detected device; the recommendation lists the affected devices **by MAC address** | [lab]; FortiOS 7.2.4 new-feature note "FortiGuard IoT Vulnerability rating check will fail if any IoT vulnerabilities are found" [doc] |
| `FG-IR-YY-NNN` | one check per Fortinet PSIRT advisory that applies to the running firmware; `title` is the advisory title, `result=passed` means the unit is not affected / is patched | [lab]; `diagnose report-runner vuln-read` shows the same advisories on the FortiGate [doc, 7.4.2 admin guide] |

The PSIRT checks are the **FortiGate's own** vulnerabilities. They say nothing about the PLCs,
cameras or workstations behind it.

## What it does NOT do

It does not populate the CVE list behind the *Vulnerabilities* column of the Asset Identity
Center, nor the OT/IoT vulnerability widgets on the Asset Summary page. That data leaves the
FortiGate's device store (`diagnose user-device-store device memory list`, blocks
`iot_vulnerability` with `vulnerability_id`, `severity`, `type`, `description`, `references`)
over the OFTP **endpoint data link**, which FortiAnalyzer checks with
`diagnose test application oftpd 20 fgt-stat` [doc, FortiAnalyzer 7.4 new features "OT Security
Service"]. No log record carries it. See `references/assets-and-iot.md`.

## Record anatomy [lab]

A FortiAnalyzer CSV export row, exactly as written by Log View > download:

```
"itime=1786349661","","","devid=""FGVMEVDEMO0000099""","adom_name=""root""","idseq=171308242746474517","logver=""0800000167""","msg=""{""messageVersion"":1,""check"":""VlanManagement"",""title"":""audit_package::check::VlanManagement"",""severity"":""medium"",""timestamp"":1786349658454,""device"":""FGVMEVDEMO0000099"",""vdom"":""root"",""result"":""failed"",""recommendations"":[{""structure"":[{""type"":""LabelRecommendationElement"",""text"":""audit_package::recommendation::VlanManagement"",""options"":{}},{""type"":""ListRecommendationElement"",""entries"":[{""type"":""OmniSourceDescriptorRecommendationElement"",""mkey"":""port2""}]}]}]}""","msg_format=""json""","msg_tag=""fgt-security-rating""","reporting_ip=""10.20.1.254""","session_id=1786349661955","session_msg_idx=0"
```

Thirteen positional cells. Compared with a traffic-log export, the second and third cells
(`date`, `time`) are **empty** - the stream carries no wall-clock fields of its own; `itime`
(receipt time on the FortiAnalyzer) is the only timestamp outside the JSON.

| Cell | Origin | Notes |
|---|---|---|
| `itime` | FortiAnalyzer | receipt epoch, seconds |
| `date`, `time` | - | empty |
| `devid` | FortiGate | serial, quoted |
| `adom_name` | FortiAnalyzer | ADOM the device belongs to |
| `idseq` | FortiAnalyzer | 18-digit sequence, constant within a session, grows slowly |
| `logver` | FortiGate | **quoted** here (`logver=""0800000167""`), unlike every other log type where it is bare |
| `msg` | FortiGate | the JSON result, compact (no spaces), key order as shown |
| `msg_format` | FortiGate | always `json` |
| `msg_tag` | FortiGate | always `fgt-security-rating` |
| `reporting_ip` | FortiAnalyzer | source IP the results came from |
| `session_id` | FortiAnalyzer | `itime*1000 + <ms>`; one value per batch of up to 30 messages (60 seen once) |
| `session_msg_idx` | FortiAnalyzer | always `0` in both exports |

JSON keys: `messageVersion` (1), `check`, `title`, `severity` (`critical` / `high` / `medium` /
`low` / `none`), `timestamp` (ms epoch, within about 0.8 s of `itime`), `device`, `vdom`,
`result`, and `recommendations` only when the result is not `passed`.

`result` values seen: `passed`, `failed`, `exempt`, `unmetDependencies`, `error` (a transient
`FortiCareRegistered` lookup failure, 5 occurrences in 9714).

`title` is `audit_package::check::<Name>` for configuration checks (the GUI translates it)
and the plain advisory title for `FG-IR-*` checks. FortiOS does not escape double quotes
inside advisory titles: FG-IR-22-345 `Command injection in "execute restore/backup" CLI
commands` is emitted as invalid JSON on both units. `rating.py` escapes it; a strict parser on
the FortiAnalyzer evidently does not mind either way.

### Recommendation element types [lab]

```
LabelRecommendationElement            text (an i18n key such as audit_package::recommendation::WanManagementAccessv4
                                       or a template "{USER} (ipsec)"), options{ interpolateData[] }
ListRecommendationElement             entries[] - may be absent when the list is empty
OmniSourceDescriptorRecommendationElement   mkey - an object the GUI can link to: interface name,
                                       FortiSwitch name, certificate name, or a MAC address
DropdownRecommendationElement         seen once, empty (InterfaceClassification)
interpolateData items                 { type: "date"|"string", value, translate:false }
```

Failed `FortiguardIotVulnerability` on the 90G:

```json
[{"structure":[
  {"type":"LabelRecommendationElement","text":"audit_package::recommendation::FortiguardIotVulnerability","options":{}},
  {"type":"ListRecommendationElement","entries":[
    {"type":"OmniSourceDescriptorRecommendationElement","mkey":"00:00:5e:00:53:01"},
    {"type":"OmniSourceDescriptorRecommendationElement","mkey":"00:00:5e:00:53:02"}]}]}]
```

An `unmetDependencies` result names the check it depends on:

```json
[{"structure":[
  {"type":"LabelRecommendationElement","text":"audit_package::recommendation::unmetDependencies","options":{}},
  {"type":"ListRecommendationElement","entries":[
    {"type":"LabelRecommendationElement","text":"audit_package::check::InterfaceClassification","options":{}}]}]}]
```

An expired FortiGuard subscription carries the expiry date:
`audit_package::recommendation::FortiGuardSubscriptions::licenseExpired` with
`interpolateData: [{type:"date", value:1776726000}]`, and the check's `severity` drops from
`critical` to `medium` while it is failing.

## Scheduler behaviour [lab]

- Full runs at **06:00, 14:00 and 22:00 UTC** on both units (08:00 / 16:00 / 00:00 CEST),
  each taking 2-14 seconds and producing about 430 results on 7.6.6 and 310 on 8.0.0.
- A run contains every applicable check, most of them more than once: a check belongs to
  several reports (Security Posture, Fabric Coverage, Optimization, PCI, CIS ...) and is
  reported once per report. `FG-IR-23-494` appears six times per run on 7.6.6,
  `UnsecureProtocolTelnet` twice on 7.6.6 and four times on 8.0.0, most others once. The multiplicity per check and per FortiOS line is stored in
  `profiles.<version>.multiplicity` of the catalogue.
- Results come out roughly in **reverse alphabetical order** of the check name, with small
  local swaps.
- Two kinds of partial run appear outside the schedule: `FortiAnalyzerConnection` alone
  (two `passed` messages, or one `failed`), and a policy/interface group of 13-19 checks
  (`VlanManagement`, `WanManagementAccess`, `InterfaceClassification`,
  `DetectBotnetConnections`, `EndpointRegistration`, ...) within minutes of a configuration
  change.
- The check set differs by firmware: 244 PSIRT checks in total, 240 on the 7.6.6 unit and
  174 on the 8.0.0 unit, 170 in common (the 8.0 unit is not tracked against advisories that
  predate its branch). A demo FortiGate on "8.0" must not report a
  7.6-only advisory; the generator only emits checks the matching reference unit reported.

## How `rating.py` uses this

- One result per check is decided **once per dataset** (a configuration does not flip every
  eight hours). `--rating-posture typical` samples from the observed result distribution,
  `good` keeps only `WanManagementAccess` and `TwoFactorAuthentication` failed, `poor` fails
  eighteen hygiene checks, expires the AntiSpam subscription and fails two critical PSIRTs.
- `--psirt-fail FG-IR-25-254,FG-IR-26-060` names the advisories to report as `failed`.
  **The recommendation payload of a failed PSIRT check was never observed** - every advisory
  passed on both reference units - so it is emitted with `[{"structure":[]}]`, the shape other
  failed checks use when they have nothing to list.
- `--rating-remediate-after 7` flips the common hygiene failures to `passed` from day 7, for
  a score-trend story.
- `FortiguardIotVulnerability` is computed from the fleet: it fails while any asset has
  `iot_vulncnt > 0` in `assets.csv` and lists exactly those MACs (up to 60). The same counts
  drive the `0100020150` vulnerability-lookup events, so the three views agree.
- Interface, switch and certificate `mkey` values in recommendations are re-pointed at the
  fleet's zone names, `<site>-FSW-01` and `FAC_SAML`; usernames in `{USER}` templates come
  from the fleet's user list.

## Import - unverified

`fazgen.py` writes the stream as `<devid>.<vdom>.xlog.<epoch>.csv` in the export layout
above, because that is the only encoding of this stream that has been seen. Whether
`execute log import` accepts it is **not confirmed** on any build: the CLI reference documents
`.log` and `.csv` extensions but not the CSV schema, and the on-the-wire OFTP encoding of
`msg_format=json` messages is not public. `--xlog-format raw` writes an educated key=value
guess (`logver=... devid="..." vd="..." msg_format="json" msg_tag="fgt-security-rating"
msg="..."`) for experimenting; it has no evidence behind it.

Test on your unit before promising it to a customer:

```
execute log import sftp <ip> <user> '<pw>' logs/<devid>/<devid>.root.xlog.<epoch>.csv <devid>
diagnose test application sqllogd 5
```

then Fabric View > Security Rating with the time range covering the dataset. If nothing
appears, the stream can only come from a live FortiGate with a Security Rating licence that
has this FortiAnalyzer configured - in which case the `--psirt-fail` and posture options are
moot and the real unit's results are what the customer sees.

## Keeping the catalogue current

PSIRT checks track Fortinet advisories, so a catalogue built in August 2026 will lack the
advisories published after that. Export the stream from any lab FortiGate (Log View, filter
on the device, download as CSV) and merge:

```
python3 scripts/ingest_rating_export.py --export 8.0=<export>.csv
```

The script only adds what it sees; it never invents a check.
