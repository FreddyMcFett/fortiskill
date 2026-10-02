# Log types, log IDs and field sets

Provenance tags used below:
- **[lab]** observed in the reference FortiGate logs (FortiOS 7.6.6 on a FortiGate 90G and
  FortiOS 8.0.0 on a FortiGate VM, August 2026).
- **[doc]** taken verbatim from a Fortinet documentation sample log line.
- **[ref]** field list only, from the FortiOS Log Message Reference - no full sample line
  exists publicly, so the shape is reconstructed from the field list.

Anything not tagged is a modelling choice made by `fazgen.py`.

---

## traffic

### `type="traffic" subtype="forward"` [lab]

| logid | meaning |
|---|---|
| `0000000013` | session closed / generic forward traffic |
| `0000000020` | periodic session update for a long-lived session (carries `*delta` fields) |
| `0000000022` | session closed after timeout |
| `0000000011` | connection failed (`action="ip-conn"`) |

Core fields: `srcip srcname srcport srcintf srcintfrole srcuuid srccountry dstip dstname
dstport dstintf dstintfrole dstuuid dstcountry sessionid proto action policyid policyname
policytype poluuid service trandisp transip transport duration sentbyte rcvdbyte sentpkt
rcvdpkt`.

Application-control enrichment on the same line: `appid app appcat apprisk applist appact
utmaction countapp`. When the app is unknown FortiOS emits `appcat="unscanned"` with no
`app`/`appid`. `app` **can** appear without `appid` - real logs do this for
`app="DHCP/DHCP Relay"` on local-in traffic - which is why `fazgen.py` tags OT flows with an
app name but no appid.

Asset enrichment (this is what builds FortiAnalyzer assets): `srcmac mastersrcmac devtype
osname srcfamily srchwvendor srchwversion srcswversion srcserver` plus the `dst*` mirrors
`dstdevtype dstosname dstfamily dsthwvendor`.

SD-WAN: `vwlid vwlname vwlquality`, where `vwlquality` looks like
`Seq_num(1 port1 underlay), alive, selected`.

Risk scoring: `crscore craction crlevel` - these are what feed Compromised Hosts / UEBA risk.

### `type="traffic" subtype="local"` [lab]
`logid="0001000014"`, `policytype="local-in-policy"`, `policyid=0`. Traffic to the FortiGate
itself. Internet background noise hitting the WAN interface lands here and it is the cheapest
way to make a demo's "denied traffic" and "top attacker country" views look alive.

### `type="traffic" subtype="ztna"` [ref]
LOG_ID 24. Same shape as forward plus `accessproxy accessctrl clientdeviceems clientdeviceid
clientdevicemanageable clientdeviceowner clientdevicetags`. No public sample line exists;
`fazgen.py` does not emit ZTNA logs for that reason.

---

## utm

### `subtype="app-ctrl"` [lab]
`logid="1059028704"`, `eventtype="signature"`. Fields: `appid app appcat apprisk applist
action appact direction hostname incidentserialno msg` plus the usual 5-tuple. `msg` has the
form `"<appcat>: <app>,"`. For ICMP flows the log also carries `icmpcode icmptype icmpid`.
A blocked application uses `action="block"` with `appact="block"`; the block-specific log ID
is 28705 (LOGID_APP_CTRL_IPS_BLOCK) [ref] - no sample line published.

### `subtype="webfilter"` [lab] [doc]
| logid | eventtype | action |
|---|---|---|
| `0317013312` | `ftgd_allow` | `passthrough` - "URL belongs to an allowed category in policy" |
| `0316013056` [doc] | `ftgd_blk` | `blocked` - "URL belongs to a denied category in policy" |
| `0319013317` | `urlmonitor` | `passthrough` - "URL has been visited" |

Fields: `hostname url reqtype direction ratemethod method cat catdesc profile profilegroup
sentbyte rcvdbyte`. Blocked lines add `crscore=30 craction=4194304 crlevel="high"` [doc].
`cat`/`catdesc` drive every category chart in FortiView and the reports.

### `subtype="dns"` [lab]
| logid | eventtype | note |
|---|---|---|
| `1500054000` | `dns-query` | the question |
| `1501054802` | `dns-response` | "Domain is monitored" / "Domain was blocked by DNS filter" [doc, 7.6.6] |
| `1501054807` | `dns-response` | "Domain is non-existent", `rcode=3` [lab, 8.0 only] |
| `1501054805` | `dns-response` | answer with multiple `ipaddr` values [lab, 7.6] |
| `1501054200` | `dns-response` | "A DNS resolution error occurs", `level="error"` [lab, 7.6] |

Fields: `qname qtype qtypeval qclass xid ipaddr rcode cat catdesc profile`.
**Caveat:** no NXDOMAIN log ID is doc-verified for 7.6. `fazgen.py` falls back to
`1501054802` with `rcode=3` on the 7.6 profile and uses the observed `1501054807` on 8.0.

### `subtype="ssl"` [lab]
| logid | eventtype | eventsubtype |
|---|---|---|
| `1704062220` | `ssl-handshake` | `handshake-done` |
| `1703062200` | `ssl-server-cert-info` | `server-cert-info` |
| `1700062307` | `ssl-anomaly` | `certificate-anomaly` (SNI/SAN mismatch) |
| `1700062302` | `ssl-anomaly` | `certificate-anomaly` (re-signed as untrusted) |
| `1700062306` | `ssl-anomaly` | `certificate-probe-failed` (bypassed) |
| `1702062101` | `ssl-negotiation` | `unallowed-version`, `action="blocked"` |
| `1701062004` | `ssl-exempt` | `address`, `action="exempt"` |

Fields: `sni hostname tlsver cipher authalgo kxproto kxcurve handshake mitm certhash cn
issuer keyalgo keysize sn notbefore notafter profile profilegroup`.

### `subtype="ips"` [doc]
`logid="0419016384"`, `eventtype="signature"`. Verbatim doc sample:

```
date=2019-05-15 time=17:56:41 logid="0419016384" type="utm" subtype="ips" eventtype="signature" level="alert" vd="root" eventtime=1557968201 severity="critical" srcip=10.1.100.22 srccountry="Reserved" dstip=172.16.200.55 srcintf="port10" srcintfrole="lan" dstintf="port9" dstintfrole="wan" sessionid=4017 action="dropped" proto=6 service="HTTP" policyid=1 attack="Adobe.Flash.newfunction.Handling.Code.Execution" srcport=46810 dstport=80 hostname="172.16.200.55" url="/ips/sig1.pdf" direction="incoming" attackid=23305 profile="block-critical-ips" ref="http://www.fortinet.com/ids/VID23305" incidentserialno=582633933 msg="applications3: Adobe.Flash.newfunction.Handling.Code.Execution," crscore=50 craction=4096 crlevel="critical"
```

**Only two `attack`/`attackid` pairs are doc-verified** and both are in
`data/catalog.json` under `ips_verified`. Do not invent signature names or IDs - look them
up on fortiguard.com and add them to that file with a note. A wrong `attackid` produces a
dead FortiGuard reference link, which a customer will click.

### `subtype="anomaly"` [doc]
`logid="0720018433"`, `eventtype="anomaly"`, `policytype="DoS-policy"`. Verified attacks:
`icmp_flood` (16777316) and `tcp_syn_flood` (100663396). Fields: `attack attackid count
severity action="clear_session" ref msg crscore craction crlevel`.

### `subtype="virus"` [doc] [lab]
`logid="0211008192"`, `eventtype="infected"`, `msg="File is infected."`. Fields:
`virus virusid dtype filename quarskip url profile agent analyticscksum analyticssubmit
direction crscore=50 craction=2 crlevel="critical"`.
FortiSandbox variants seen in the lab logs use `logid="0201009233"` (`eventtype="analytics"`,
`action="analytics"`, `msg="File submitted to Sandbox."`, `fsadevice="FortiSandbox"`) and
`logid="0201009238"` (`action="monitored"`, `dtype="fortisandbox"`, `fsaverdict="clean"`).

### `subtype="dlp"` [doc]
`logid="0954024576"`, `eventtype="dlp"`. Fields: `filteridx filtertype filtercat dlpextra
severity epoch eventid filetype filename filesize action="block" hostname url httpmethod
agent rawdata profile`. The sensor name field is **`profile`**, not `dlpsensor`.

### `subtype="voip"` [lab] [doc]
`logid="0814044032"`, `eventtype="voip"`, `kind="call"`, `status="start"`, `action="permit"`,
`voip_proto="sip"`, `dir="session_origin"`. Doc sample (log message reference 7.4.3, "VoIP log
support for CEF") and 55 lab lines from the 8.0.0 unit agree on the shape. **This family
spells its fields differently from every other log type**: `session_id`, `src_port`,
`dst_port`, `src_int`, `dst_int`, `policy_id`, `event_id`, `call_id` - not `sessionid`,
`srcport`, `srcintf`, `policyid`. Other fields: `epoch`, `duration`, `profile`, `from`, `to`
(`sip:<user>@<host>`), `proto=17`. The 8.0.0 unit adds `logsrc="voipd"`; the 6.0-era doc
sample has no `logsrc`, so the 7.6 profile omits it (unverified either way). Only
`status="start"` was observed; a call-end log almost certainly exists but no sample was
available, so the generator emits starts only. Files go to `<devid>.<vdom>.plog.<epoch>.log`,
matching FortiAnalyzer's own naming for this type.

### Other UTM subtypes, doc-verified samples exist but `fazgen.py` does not emit them
`emailfilter` (`0508020503`), `waf` (`1203030258`), `ssh` (`1600061002`). Field sets are in
the log message reference. `file-filter` has no published sample line at all.

---

## event

### `subtype="system"` [lab] [doc]
| logid | logdesc |
|---|---|
| `0100032001` / `0100032002` | Admin login successful / failed [doc] |
| `0100032003` | Admin logout successful |
| `0100044547` | Object attribute configured (`cfgpath cfgobj cfgattr cfgtid uuid`) |
| `0100026001` | DHCP Ack (`dhcp_msg ip mac lease hostname interface`) |
| `0100026003` / `0100026004` | DHCP statistics / client lease granted |
| `0100040704` | System performance statistics (`cpu mem disk totalsession setuprate sysuptime waninfo`) |
| `0100020150` | **Device vulnerability lookup on FortiGuard** - the IoT vulnerability log |
| `0100022100` | Files dropped by quarantine daemon |
| `0100038420` | HTTPS connection error |
| `0100053400` / `0100053401` | Central Management connectivity active / inactive |

`0100020150` = LOG_ID_DEV_VUNL_FTGD_LOOKUP (message ID 20150) [ref, and observed in the lab
logs]. Fields: `ip mac model product vendor versionmin versionmax vulncnt vulnresult`. This
is the only per-device vulnerability log line FortiOS has, and it carries a **count**, not
the CVEs. The CVE list reaches FortiAnalyzer over the OFTP endpoint data link from the
device store, and endpoint vulnerabilities through the EMS connector - neither is a log. See
`references/assets-and-iot.md`, section "Where vulnerabilities come from".

### `subtype="ha"` [doc]
`logid="0108037894"` - "Virtual cluster member joined", fields `vcluster ha_group sn`.

### `subtype="vpn"` [lab] [doc]
IPsec: `0101037120` negotiate phase 1, `0101037122` negotiate phase 2, `0101037124` phase 1
error, `0101037127`/`0101037128` progress phase 1, `0101037129` progress phase 2,
`0101037133` SA installed, `0101037138` connection status changed, `0101037139` phase 2
status changed, `0101037141` tunnel statistics.
SSL-VPN [doc]: `0101039943` new connection, `0101039424` tunnel up (`tunneltype="ssl-web"`),
`0101039947` tunnel up (`tunneltype="ssl-tunnel"`, adds `tunnelip`), `0101039426` login fail
(`reason="sslvpn_login_permission_denied"`).
Common fields: `action tunneltype tunnelid tunnelip remip locip remport locport outintf user
group cookies vpntunnel dst_host reason status fctuid`. Unused string fields are literally
`"N/A"`, not omitted.

### `subtype="user"` [lab] [doc]
`0102043008` authentication success/failure (`srcip user group authproto action="authentication"
status reason msg`) [doc]. `0102043050`/`0102043051` FSSO server connected/disconnected [lab].

### `subtype="sdwan"` [lab]
`0113022925` (7.6) / `0113022941` (8.0, "Application Performance Metrics via kernel"). Fields:
`eventtype="SLA" healthcheck interface status slamap latency jitter packetloss mosvalue
moscodec inbandwidthused outbandwidthused bibandwidthused *available`.

### `subtype="wireless"` [lab]
A large family (`0104043573`-`0104043699`) covering association, 4-way handshake, client IP
detection, roaming. Fields: `ap sn stamac ssid vap radioid radioband channel signal snr
security encryption trafficmode mpsk authserver remotewtptime`.

### `subtype="endpoint"` [lab]
`0107045121` EMS WebSocket notification, `0107045122` EMS REST API error, plus the
FortiClient registration IDs. Fields include `fctemsname fctemssn fctuid httpcode url`.

### `subtype="security-rating"` [lab]
`0110052000` / `0110052002`. Fields: `auditreporttype checkname result msg`. The detailed
per-check JSON results travel in a separate stream (`msg_format="json"`,
`msg_tag="fgt-security-rating"`) that FortiAnalyzer stores as **Xlog** and shows under
Fabric View > Security Rating. `fazgen.py` generates that stream from a catalogue of 351
observed checks (107 configuration, 244 `FG-IR-*` PSIRT advisories) - anatomy, cadence and
the unverified import path are in `references/security-rating.md`.

---

## FortiGuard web filter categories

`data/catalog.json` holds the full `cat` -> `catdesc` map. 38 of the IDs were confirmed
directly against the lab logs; the rest come from the current Fortinet community category
table. The **pre-FortiOS-5.0** category list still circulating on the web is wrong for 7.x/8.x
(it has 26 = "Spyware and Malware"; the current value is 26 = "Malicious Websites").

Security-relevant IDs worth knowing for demos: 26 Malicious Websites, 61 Phishing,
86 Spam URLs, 88 Dynamic DNS, 90 Newly Observed Domain, 91 Newly Registered Domain,
98 Crypto Mining, 99 Potentially Unwanted Program, 3 Hacking, 59 Proxy Avoidance.

There is **no** botnet/C2 web filter category. Botnet C&C detection is a separate
IP/domain blocklist enforced through DNS Filter or IPS, and it does not surface in
`cat`/`catdesc`.
