# Scenario catalogue

Each scenario injects a correlated burst of logs on top of the baseline traffic. Pass them
comma-separated to `--scenarios`. Over runs longer than three days each fires with the
probability shown, so a two-week dataset gets a realistic scatter rather than the same
incident every day; for runs of three days or fewer each selected scenario fires daily.

Append `:<probability>` to override the default for one scenario. A threat-heavy demo wants
`--scenarios "ransomware:1.0,camera-c2:0.8,inbound-scan"`; a "look how quiet a healthy
network is" demo wants the defaults or lower.

| Scenario | Prob/day | What it emits | Demo target |
|---|---|---|---|
| `shadow-iot` | 0.7 | DHCP ack for an unmanaged consumer device, a FortiGuard vulnerability lookup, then vendor-cloud sessions and a DNS query to a vendor telemetry domain | Asset Identity Center "new/unidentified asset", IoT dashboard "New Devices Detected" |
| `camera-c2` | 0.25 | An IP camera whose `vulncnt` is raised to 12-60 (it then also appears in the failed IoT-vulnerability rating check), blocked DNS lookups to a C2 domain (`cat=26` Malicious Websites), beacon sessions on 8443, periodic IPS drops, then a DLP block on a large upload | IoT dashboard "Top IoT Devices with Vulnerabilities", Compromised Hosts, Threats, Incidents |
| `ransomware` | 0.12 | Phishing DNS + blocked webfilter (`cat=61`), AV block on a downloaded archive, IPS drop, lateral SMB burst with failed auth events, DGA lookups returning NXDOMAIN, a run of DLP blocks, then a `tcp_syn_flood` DoS anomaly | FortiView Threats, Compromised Hosts, UEBA risk score, incident/playbook demos |
| `ot-intrusion` | 0.2 | An engineering workstation opening Modbus sessions to a PLC it never normally talks to, out of hours, then an IPS drop on port 502 and a vulnerability lookup on the target PLC | OT View, Asset Identity Center, "unexpected east-west" story |
| `cryptomining` | 0.3 | Repeated blocked DNS and webfilter hits on `cat=98` Crypto Mining | Webfilter category charts, policy-hygiene story |
| `inbound-scan` | 1.0 | Internet background noise denied by local-in policy on the WAN interface, spread across the day and across ~12 common ports | Denied traffic, top attacker country, local-in policy value |
| `vpn-bruteforce` | 0.3 | A burst of SSL-VPN `ssl-login-fail` events from one source, followed by one successful `tunnel-up` | Event handlers, VPN reports, "why you need MFA" |

## Baseline, always present

Independent of `--scenarios`, every run produces:

- the security-rating stream: three full runs a day plus partial re-runs, with
  `FortiguardIotVulnerability` failing for the assets that carry `iot_vulncnt > 0`
  (`--no-rating` switches it off; `--rating-posture`, `--psirt-fail`,
  `--rating-remediate-after` shape it - `references/security-rating.md`)
- `utm/voip` SIP call logs from every host with the `voip` role (office-hours curve, 70 % to
  the LAN PBX, 30 % out through the trunk)

- per-host application traffic driven by the behaviour list on each device model, shaped by a
  diurnal curve (`office`, `flat` for always-on IoT/OT, `shift` for 3-shift operations) with
  weekends damped for office hosts
- `utm/dns` query + response pairs, `utm/ssl` handshake and server-cert logs, `utm/webfilter`
  allow logs, `utm/app-ctrl` signature logs
- hourly `event/sdwan` SLA and `event/system` performance statistics
- daily DHCP acks, FortiGuard device vulnerability lookups (the `vulncnt` of each asset is
  fixed at generation time - `--vuln-ratio` sets how many IoT/OT assets carry one - and
  scenarios can only raise it), admin logins (with occasional failures), user
  authentications, SSL-VPN connections and the odd config change, which triggers a partial
  security-rating re-run

## Adding a scenario

1. Write a `scenario_<name>(self, day)` method on `Generator` in `scripts/fazgen.py`. Use the
   existing builders - `session`, `dns_pair`, `webfilter`, `ssl_logs`, `appctrl`, `ips`,
   `anomaly`, `virus`, `dlp`, and the `ev_*` event builders - rather than hand-assembling
   dicts, so the envelope and asset fields stay correct.
2. Register it in the `SCENARIOS` dict with a per-day probability.
3. Run `verify_logs.py` on the output. It will flag any field name that is not in the known
   FortiOS set, which catches typos and invented fields.

Before inventing a field or a signature name, check `references/log-types.md` for whether the
value is lab-observed, doc-verified, or unverified. The generator is deliberately conservative
about IPS signature names and OT app IDs for this reason - a Fortinet SE audience will notice
a `VID` link that 404s.

## Choosing volume

`--scale small|medium|large|xlarge` multiplies per-flow session rates by 0.25 / 1 / 3 / 8.
Rough output for the `enterprise` fleet (150 assets):

| scale | records/day | file size/day |
|---|---|---|
| small | ~45 k | ~30 MB |
| medium | ~180 k | ~120 MB |
| large | ~540 k | ~360 MB |

For a demo, `small` over 14-30 days beats `large` over 2 days: the dashboards that impress
are the trend ones, and they need days on the x-axis.
