# Anatomy of a FortiGate log line

## The two formats people confuse

**Raw / wire format** - what a FortiGate writes to disk and sends over syslog and OFTP, and
what `execute log import` expects. One record per line, space-separated `key=value` pairs:

```
date=2026-08-01 time=09:14:02 eventtime=1785568442847113221 tz="+0200" logid="0000000013" type="traffic" subtype="forward" level="notice" vd="root" srcip=10.10.20.25 srcname="WS-06" srcport=51204 ... devid="FGVMEVDEMO0000001" devname="DEMO-HQ-FGT-01" logver=0800000167
```

**FortiAnalyzer CSV export** - what you get from Log View > Download. Fixed positional
columns, no header row, every cell CSV-quoted, and the field name repeated inside each cell:

```
"itime=1787281603","date=""2026-08-21""","time=""05:06:42""","devid=""FGVMEVDEMO0000099""",...
```

The reference logs in this project's source folder are in the second format. **Never feed a
CSV export back into `execute log import` and expect the wire format's semantics** - the
export adds FortiAnalyzer's own envelope fields and re-quotes everything. `fazgen.py` emits
the first format.

Column order in a CSV export is `itime, date, time, devid, vd, type, subtype, action`, then
strictly alphabetical. That alphabetical ordering is a FortiAnalyzer artefact, not FortiOS
field order.

The one stream `fazgen.py` deliberately writes in the **second** format is the security-rating
result stream (`*.xlog.*.csv`): its columns are `itime, <empty date>, <empty time>, devid,
adom_name, idseq, logver, msg, msg_format, msg_tag, reporting_ip, session_id,
session_msg_idx`, `logver` is quoted there, and no raw encoding has ever been observed. See
`references/security-rating.md`.

## Quoting rules

FortiOS quotes string fields and leaves numeric and address fields bare. Getting this wrong
does not usually break the parser but it makes the file obviously synthetic:

| Unquoted | Quoted |
|---|---|
| `date=2026-08-01` `time=09:14:02` | `tz="+0200"` `logid="0000000013"` |
| `eventtime=1785568442847113221` | `type="traffic"` `subtype="forward"` `level="notice"` |
| `srcip=10.10.20.25` `dstip=1.1.1.1` `transip=198.51.100.10` | `srcname="WS-06"` `srcintf="vClients"` |
| `srcport=51204` `dstport=443` `proto=6` `sessionid=15080655` | `srcmac="c8:89:f3:11:22:33"` |
| `policyid=10` `duration=78` `sentbyte=180` `rcvdbyte=180` | `service="HTTPS"` `action="close"` |
| `appid=24466` `countapp=1` `cat=52` `crscore=30` `craction=4096` | `app="Ping"` `appcat="Network.Service"` `catdesc="Information Technology"` |
| `logver=0800000167` | `devid="FGT90GDEMO000001"` `devname="LAB-FGT-01"` |
| VoIP: `session_id=18975` `src_port=5060` `dst_port=5060` `policy_id=1` `event_id=0` `epoch=0` | VoIP: `src_int="port12"` `dst_int="port11"` `voip_proto="sip"` `kind="call"` `call_id="..."` `from="sip:..."` `to="sip:..."` |
| `remip=192.168.1.5` `locip=...` `tunnelip=...` `assignip=N/A` | `user="bob"` `msg="..."` |

`ipaddr` (DNS response answers) is an exception: it is quoted, because it can hold a
comma-separated list - `ipaddr="54.148.45.104, 34.217.203.14"`.

The exact per-field data type is in the FortiOS Log Message Reference: docs.fortinet.com >
FortiGate > FortiOS Log Message Reference > the numeric log-ID page (for example 24 for
LOG_ID_TRAFFIC_ZTNA). Fields typed `ip` are unquoted; `string(n)` are quoted; `uint*` are
unquoted.

## Field order

FortiAnalyzer parses `key=value` pairs order-independently, so order is cosmetic - but
matching FortiOS makes the output indistinguishable from a real disk dump. The observed
FortiOS 7.x/8.x order is:

```
date time eventtime tz logid type subtype [eventtype] level vd [logdesc] <payload...> [msg] [craction crlevel crscore] devid devname logver
```

Older documentation samples (pre-2020) put `logid type subtype level vd` before `eventtime`
with no `tz` at all. Both appear in Fortinet's current docs. `fazgen.py` uses the newer form,
encoded in `FIELD_ORDER` in `scripts/fazgen.py`. The VoIP family has its own order
(`VOIP_ORDER`), taken from the log-reference sample, because its field names differ.

## Timestamps

Four different time concepts, and mixing them up is the most common cause of "the import
worked but nothing shows up":

| Field | Who sets it | Format | What it drives |
|---|---|---|---|
| `date` / `time` | FortiGate | local wall clock, `tz` gives the offset | log retention, the SQL start-time gate, the time column in Log View |
| `eventtime` | FortiGate | **nanosecond** epoch, 19 digits, UTC | sub-second ordering |
| `itime` | FortiAnalyzer, on receipt | second epoch | not present in files you import; FAZ adds it |
| `dtime` | FortiAnalyzer, computed | derived | internal |

`eventtime` was seconds in FortiOS 6.0 and earlier and became nanoseconds in 6.2. Everything
7.x/8.x emits 19 digits. `verify_logs.py` checks this and checks that `date`/`time` and
`eventtime` agree to within two seconds.

## `logver`

A build-stamped format version, emitted unquoted. Observed values:

| Value | Device |
|---|---|
| `0706063652` | FortiGate 90G on FortiOS 7.6.6 build 3652 |
| `0800000167` | FortiGate VM on FortiOS 8.0.0 build 0167 |

The 2-2-2-4 digit split (major, minor, patch, build) is consistent across the values seen but
Fortinet does not document the encoding, so treat it as inference. What is documented: a
**missing** `logver` does not stop ingestion, it only blanks report charts whose dataset SQL
filters on `logver` (Fortinet KB 197511). Always emit one.

## The FortiAnalyzer envelope

Fields FortiAnalyzer adds itself. Do **not** put these in a file you are going to import:

`itime`, `itime_t`, `dtime`, `idseq`, `reporting_ip`, `adom_name`, `session_id`,
`session_msg_idx`, `id`, `euid`, `epid`, `dsteuid`, `dstepid`.

`euid` / `epid` are the UEBA user and endpoint IDs FortiAnalyzer computes. Values below 1024
are reserved status codes (3 = not enough info to identify, 101 = public IP on a non-LAN
interface, 103 = too many IPs on one MAC, and so on - documented at FortiAnalyzer admin guide
564377). They are keyed on `fctuid` when FortiClient is present and on MAC otherwise, which
is why `srcmac` and `mastersrcmac` matter so much for the Asset Identity Center.
