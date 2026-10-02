# Assets, IoT and what actually populates the FortiAnalyzer views

## The three different IoT/asset surfaces

They are separately licensed and separately fed. Conflating them is the fastest way to build
a demo that does not light up.

### 1. Fabric View > Asset Identity Center
Per-ADOM. Sub-pages: Asset Summary, Identity Summary, Asset List, Identity List, OT View.
Data sources are configurable per ADOM under *Asset Identity List > More > Data Sources*:
FortiGate Log (on), FortiClient Log (on), FortiWeb Log (on), FortiNAC Log (on),
FortiMail Log (**off** by default), EMS Connector (**off** by default). Fortinet's own docs
call this "UEBA identification".

**Fed by log fields.** This is the surface synthetic logs can drive completely.

### 2. Dashboards > IOT
A separate, licence-gated dashboard. Quoting the admin guide:
> "To display OT devices in this dashboard, the FortiAnalyzer and FortiGate devices must have
> OT Security Service entitlements."
> "To display IoT devices in this dashboard, the FortiGate devices must be licensed for the
> IoT Detection Service."
> "FortiOS devices must use version 7.4 or higher to send OT information to FortiAnalyzer."

Widgets: Total/New/Identified/Unidentified Devices, Total & New IoT Devices, Device Category
donut, IoT Vendors donut, Vulnerabilities by Vendor, New Devices Detected over time, Alerts
Distribution (Sankey severity -> category), Top IoT Devices with Vulnerabilities, IoT Devices
with Internet Connection.

On the FortiGate side the entitlement is formally part of the **Attack Surface Security
Rating service**; the FortiAnalyzer docs call the same capability the *IoT Detection Service*.
Expect the two names on a licence sheet not to line up 1:1.

### 3. Asset Identity Center > OT View
A topology graph, not charts. Grouped by **Purdue level**.

**Purdue level is not a log field.** Grepping the entire FortiOS 7.6 Log Message Reference for
"purdue" returns nothing. It is an attribute in the FortiGate's live device store
(`purdue_level`), surfaced to FortiAnalyzer over the Security Fabric, settable with
`config system global / set purdue-level`, per managed switch, per WTP, or per interface via
`set default-purdue-level`, and overridable with
`diagnose user-device-store device memory ot-purdue-set <mac> <ip> <level>`.

Consequence: **you cannot populate the OT View by importing logs.** `fazgen.py` still records
a Purdue level per asset in `assets.csv`, so you can drive it into a lab FortiGate's device
store by hand or via API and get the topology to match the logs. The settable enum is
1, 1.5, 2, 2.5, 3, 3.5, 4, 5, 5.5 (levels S, 0 and "external" are auto-assigned only).
In FortiOS 8.0 the GUI toggle for this was renamed from "Operational Technology (OT)" to
"Purdue Levels"; the CLI flag is still `set gui-ot enable`.

---

## Where vulnerabilities come from, and why logs cannot fake them

Three different vulnerability sources land in FortiAnalyzer, and **none of them is a
FortiGate log record**. Verified against docs.fortinet.com (FortiAnalyzer 7.4 new features
"Operational Technology (OT) Security Service", FortiAnalyzer 8.0 admin guide "Endpoint
vulnerability dashboard", FortiOS 7.6 admin guide "Asset Identity Center page").

| What the customer sees | Where the data comes from | What a log import can do |
|---|---|---|
| Asset Identity Center > *Vulnerabilities* column for IoT/OT devices; Asset Summary OT/IoT vulnerability widgets (severity breakdown, top-10 CVEs, top-10 assets); the CVE list with Type / Severity / Reference / Description; KEV flags (7.6.1+) | The FortiGate's device store (`diagnose user-device-store device memory list`, `iot_vulnerability` blocks with `vulnerability_id`, `severity`, `type`, `description`, `references`, filled by the FortiGuard IoT/OT query service). The FortiGate pushes it to FortiAnalyzer over the OFTP **endpoint data link**. Needs FortiOS 7.4+ and the OT Security Service entitlement on both units. Status: `diagnose test application oftpd 20 fgt-stat` on the FortiAnalyzer. | **Nothing.** No log field carries a CVE for a detected device. |
| *Vulnerabilities* for FortiClient endpoints; Dashboards > Endpoint vulnerability; Endpoint Security Vulnerability report | The FortiClient EMS connector. Its default playbook *Update Asset, Identity and Vulnerability in Sequence* calls the EMS API once a day and inserts the result as Fabric (SIEM) logs, parsed by the predefined EMS-Connector log parser (FortiAnalyzer 7.6.2 adds `event_subtype=endpoint-vuln`). Needs a Fabric ADOM and an authorised EMS device. FortiClient's own vulnerability logs (`vulnid vulnname vulnseverity vulncat vulncvss vulnref vulnengine vulnsignature vulnproducts`, FortiClient 7.4.1 Log Reference) are a second path, from the EMS as log source. | Nothing through the FortiGate device. A FortiClient-format log file for an EMS device is conceivable but neither the format nor the import path is verified, so this project does not attempt it. |
| Security Rating check `FortiguardIotVulnerability` failed, listing the vulnerable devices by MAC; `FG-IR-*` PSIRT checks for the FortiGate itself | The FortiGate's security-rating stream (`msg_tag=fgt-security-rating`), shown in Fabric View > Security Rating and the FSBP/PCI/CIS reports | `fazgen.py` generates this stream (`*.xlog.*.csv`) - see `references/security-rating.md`. Import is unverified. |
| `0100020150` "Device vulnerability lookup on FortiGuard" event with `vulncnt` | FortiGate event log | Generated. It is a **count**, and no FortiAnalyzer view is documented to chart it. |

So a dataset built by this skill can make a customer see: assets with vendor, model and OS;
IoT devices with internet exposure; a security rating that fails on IoT vulnerabilities and
names the devices; and, if you choose, an unpatched FortiGate. It cannot make the Asset
Identity Center open a CVE list for a PLC. For that, put one real FortiGate 7.4+ with the OT
Security Service into the Fabric of the demo FortiAnalyzer and let its device store contain
the devices (the generator's `assets.csv` gives you the MACs, models and firmware versions to
reproduce, e.g. with a small lab VLAN or a FortiTester/traffic generator), and confirm the
link with `diagnose test application oftpd 20 fgt-stat`.

`assets.csv` carries `iot_vulncnt` per asset; the same numbers appear in the `0100020150`
events and as the MAC list of the failed rating check, so the log side of the story is at
least self-consistent.

## Which log fields build an asset record

From LOG_ID_TRAFFIC_ALLOW (message ID 2) and confirmed against the lab logs:

| Field | Role |
|---|---|
| `srcmac`, `mastersrcmac` | the identity key when no FortiClient is present. `mastersrcmac` is the master MAC of a multi-NIC host |
| `srcip`, `srcname` | address and resolved/DHCP name |
| `devtype` | device type - drives the Device Category donut |
| `osname` | OS product name |
| `srcfamily` | product family |
| `srchwvendor` | vendor per FortiGuard fingerprinting - drives the IoT Vendors donut |
| `srcmacvendor` | vendor per raw IEEE OUI lookup. A distinct field from `srchwvendor` and they can disagree; Fortinet documents neither in prose |
| `srchwversion` | hardware model |
| `srcswversion` | firmware / OS version |
| `fctuid` | FortiClient UID - becomes the endpoint identity key when present |
| `user`, `unauthuser`, `unauthusersource` | identity. `unauthusersource` is the *detection method*, e.g. `kerberos`, not a source address |
| `emsconnection`, `emstag`, `emstag2`, `clientdevice*` | EMS / ZTNA posture |
| `srcssid`, `ap`, `apsn` | wireless identity |

Every one of these has a `dst*` mirror (`dstdevtype`, `dstosname`, `dstfamily`,
`dsthwvendor`, `dstunauthuser`, ...) which is how internal server-to-server flows still
enrich both ends.

`fazgen.py` puts the full source set on **every** forward-traffic log; `verify_logs.py`
reports the coverage percentage.

---

## The devtype taxonomy

Fortinet does not publish an authoritative list of `devtype` strings for FortiOS 7.6/8.0 -
the values come from FortiGuard's device-fingerprinting content, not from a CLI enum. So
this project works in two tiers.

**Tier 1, observed in the reference logs** (`--devtype-mode verified` restricts output to
these):

```
Unknown, Virtual Machine, Firewall, Phone, Network Generic, Computer, Laptop,
Network, Television, Media Player, IOT, Switch
```

Note `IOT` is upper-case in real logs, not "IoT".

Corresponding observed values:

| field | observed values |
|---|---|
| `osname` | Unknown, Windows, macOS, iOS, Debian, FortiManager OS, FortiAnalyzer OS, FortiSandbox OS |
| `srcfamily` | iPhone, Mac, Computer, TV, Cloud, Network Appliance, FortiManager, FortiAnalyzer, FortiSandbox |
| `srchwvendor` | VMware, Apple, Fortinet |
| `srchwversion` | "MacBook Pro", "Workstation Pro", "Virtualized on VMWare vSphere Hy" |
| `srcswversion` | "10/11", "18.7", "10.15.7", "7.2.123.16565" |

**Tier 2, extended** (the default). Strings such as `IP Camera`, `IP Phone`, `Printer`,
`Programmable Logic Controller`, `Human Machine Interface`, `Medical Device`, `HVAC`,
`Access Control`, `Barcode Scanner`, `Industrial Device`, `Smart Speaker`, `Thermostat`,
`Smart Plug`, `Smart Lighting`. These follow Fortinet's **FortiNAC-F** device-type taxonomy,
which FortiNAC-F 7.6.3 and later derives from FortiGuard category/subcategory mappings (about
140 types). FortiAnalyzer stores `devtype` as an opaque string and will chart whatever you
send, so these render correctly - but they are **not confirmed as strings FortiOS itself
emits**. If a customer will compare the demo against their own FortiGate, run with
`--devtype-mode verified`, or check the real strings first with:

```
diagnose user-device-store device memory list
diagnose user device list
```

which show the backing record: `hardware_vendor`, `hardware_type`, `hardware_family`,
`os_name`, `os_version`, `host_src`, `purdue_level`, plus `iot_info` (vendor/product/version)
and `iot_vulnerability` (vulnerability_id, severity, references) blocks.

Detection-method tags visible there (`src` attribute): `lldp`, `arp`, `dhcp`, `http`, `dns`,
`mac`, `tcp`, `kerberos`, `mwbs`, `fortiguard`.

---

## MAC addresses

`data/oui.json` maps each vendor to real IEEE-registered OUIs (104 vendors, 452 prefixes,
extracted from the IEEE OUI registry bundled with the `netaddr` package). `fazgen.py`
generates deterministic MACs by picking a prefix for the model's vendor and hashing the
host's identity into the last three octets, so the same fleet and seed always produce the
same MAC for the same asset - re-running the generator does not create duplicate assets in
FortiAnalyzer.

To add a vendor, add real OUIs. A made-up prefix will resolve to the wrong vendor (or none)
in any tool the customer checks it against, including FortiAnalyzer's own vendor lookup.

---

## Industrial protocols and application control

The `appcat` for industrial protocols was renamed in FortiOS 7.4.1 from `Industrial` to
Operational Technology; the log string is `appcat="Operational.Technology"`.

The **only** app name/appid pair verifiable in Fortinet documentation is:

```
appid=49890 app="RealPort.DNP3"         appcat="Operational.Technology" service="RLDNP3"
appid=49899 app="RealPort.DNP3_Confirm" appcat="Operational.Technology" service="RLDNP3"
```

(DNP3 tunnelled over RealPort serial-over-TCP.) Names for Modbus, S7, BACnet, EtherNet/IP,
PROFINET and OPC could not be confirmed. `fazgen.py` therefore emits OT flows with an app
name and `appcat="Operational.Technology"` but **deliberately no `appid`**, a shape FortiOS
itself produces. The names are in `OT_APP` in `scripts/fazgen.py`; verify them on
fortiguard.com before putting them in front of a customer, or run with `--no-ot-appctrl` to
emit the OT flows as plain `appcat="unscanned"` traffic identified only by port and service.

OT virtual patching has its own log **type**: `type="virtual-patch" subtype="ot-vpatch"`,
log IDs 64600 (block) and 64601 (detect). Field list only - no public sample line - so
`fazgen.py` does not emit them.

FortiOS 7.6.1 added device detection through IoT/OT application signatures without an
application-control profile. The doc sample of such a log [doc, FortiOS 7.6 new features
"Streamline IoT/OT device detection"] is a plain `utm/app-ctrl` signature log with
`appcat="OT"`, `app="Advantech.R-SeeNet"`, `appid=10002847` and an extra field
`clouddevice="Vendor=Advantech, Product=R-SeeNet, Version=2.4.15"`. `appcat="OT"` here is the
detection-signature category, not the traffic category `Operational.Technology`; only that one
app/appid pair is verified, so `fazgen.py` does not emit these.

`appcat="IoT"` is a real application-control category, separate from Operational.Technology.
Observed IoT-category apps use 8-digit app IDs in the 100xxxxx range
(`Fortinet.FortiClient` 10005193, `Apple.Devices` 10002332). FortiView > IoT ("IoT Inventory"
widget) is driven by this app category, not by device detection.

---

## Checklist: making the IoT dashboard look right

1. Every endpoint's traffic logs carry `srcmac`, `devtype`, `osname`, `srchwvendor`,
   `srchwversion`, `srcswversion`. (`verify_logs.py` reports coverage.)
2. Vendors are spread across enough distinct `srchwvendor` values that the IoT Vendors donut
   is not one slice.
3. Some devices have `0100020150` events with a non-zero `vulncnt`, and the security-rating
   stream fails `FortiguardIotVulnerability` with their MACs. Whether the IoT dashboard's
   "Vulnerabilities by Vendor" and "Top IoT Devices with Vulnerabilities" widgets read either
   of these is **not documented**; the documented source for per-device vulnerability data is
   the OFTP endpoint data link (see above). Treat these widgets as needing a live FortiGate.
4. Some IoT devices talk to the internet (`dstintfrole="wan"`) so "IoT Devices with Internet
   Connection" is not empty.
5. Devices appear for the first time on different days, so "New Devices Detected" has a
   curve rather than one spike. `fazgen.py` staggers DHCP-ack events for this.
6. The FortiGate model device in FortiAnalyzer has the IoT Detection Service (and OT Security
   Service, for OT devices) entitlement, or the dashboard stays empty regardless of the logs.
