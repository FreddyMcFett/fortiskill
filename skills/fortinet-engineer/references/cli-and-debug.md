# CLI, Diagnostics, and Troubleshooting

A senior engineer's guide to FortiOS diagnostic methodology. The discipline matters more than the command list — the right command on the wrong hypothesis wastes time. This reference combines a **diagnostic methodology** with a **command reference** organized by subsystem.

**Critical reminder**: All commands here are starting points. **Verify exact syntax** for the user's FortiOS version on `docs.fortinet.com` → CLI Reference. Some commands have changed across 6.4 → 7.0 → 7.2 → 7.4 → 7.6 → 8.0.

## Table of contents

1. The hypothesis-driven diagnostic loop
2. Hardware path: NPU / CP / SP fundamentals
3. Universal first commands (always run these)
4. Subsystem command reference
   - 4.1 Sessions and connectivity
   - 4.2 Routing (BGP / OSPF / static)
   - 4.3 IPsec VPN
   - 4.4 SSL VPN / Agentless VPN
   - 4.5 SD-WAN
   - 4.6 HA
   - 4.7 DNS / dnsproxy
   - 4.8 Authentication (FSSO / SAML / RADIUS)
   - 4.9 UTM (IPS / AV / Web filter / App control)
   - 4.10 SSL DPI
   - 4.11 FortiSwitch (FortiLink)
   - 4.12 FortiAP (wireless)
5. Packet capture (sniffer + flow trace)
6. Log analysis and FortiAnalyzer queries
7. Performance and resource diagnostics
8. Common debug-flag reference
9. Anti-patterns

---

## 1. The hypothesis-driven diagnostic loop

For any non-trivial troubleshooting:

```
1. Define the symptom precisely
   - What stopped working / what was expected
   - When did it start (correlated with what change?)
   - Scope: one user / one site / global?
   
2. Form 2–4 hypotheses ranked by likelihood
   - Each hypothesis names a specific subsystem and failure mode
   - Avoid "it might be the firewall" — too vague
   - Better: "outbound DNS to 8.8.8.8 is being dropped by policy", "BGP session is flapping due to control-plane CPU spikes"
   
3. Pick a confirming/denying command per hypothesis
   - Cheap, non-disruptive commands first
   - Output should explicitly distinguish hypotheses
   
4. Run, observe, eliminate
   - Hypothesis confirmed → drill in
   - Hypothesis denied → eliminate, move to next
   - All denied → expand hypothesis set (usually means initial scope was too narrow)
   
5. Once root cause is confirmed, validate the fix
   - Reproduce the symptom (controlled)
   - Apply fix
   - Reconfirm symptom is gone
   - Document
```

This frame keeps you from running random `diagnose debug *` commands hoping something obvious shows up. Diagnostic noise from the wrong command is worse than no output.

---

## 2. Hardware path: NPU / CP / SP fundamentals

Before reading session output, understand the hardware path the session takes. FortiGate hardware accelerates differently per FortiOS version.

- **NPU (Network Processor)** — L2/L3 forwarding, IPsec, sometimes IPS/AV depending on model. Sessions on NPU don't show up in the standard session-table walk because they're offloaded.
- **CP (Content Processor)** — flow-based UTM acceleration (pattern matching, decryption support).
- **SP (Security Processor)** — newer, advanced inspection acceleration.
- **Software / kernel path** — when offload is bypassed (proxy mode, certain features).

**Implication**: a session that "isn't in the session table" may be NPU-offloaded. Use `diagnose sys session` for software-path; `diagnose sys session npu` (varies by version) or NPU-specific commands for offloaded.

`get hardware npu list` and `diagnose npu np6 ...` (or np7, depending on chip) for NPU diagnostics. Exact subcommand varies by NPU generation. Always verify against the hardware-specific guide.

---

## 3. Universal first commands

When unfamiliar with a FortiGate or starting any troubleshooting:

```fortios
# Identity and version
get system status
get system performance status

# Time (matters for logs, certs, BGP)
get system time

# HA state — always check before assuming a single unit
get system ha status
diagnose sys ha status

# Interfaces
diagnose hardware deviceinfo nic     # physical NIC info on hardware models
get system interface physical
get router info routing-table all

# Resource pressure (high CPU/memory often confounds diagnosis)
get system performance status        # snapshot
diagnose hardware sysinfo conserve   # is the system in conserve mode?
diagnose sys top 5 30                # live top-style view

# Process status
diagnose sys top-summary

# Log a quick "everything looks how" snapshot before any change
```

**Critical**: if the system is in **conserve mode**, diagnostics interpretations change — many features stop working as expected. Confirm conserve state before diagnosing user-facing symptoms.

---

## 4. Subsystem command reference

### 4.1 Sessions and connectivity

```fortios
# Session table (software path)
diagnose sys session list
diagnose sys session filter src 10.1.1.5
diagnose sys session filter dst 8.8.8.8
diagnose sys session filter dport 443
diagnose sys session list

# Stat overview
diagnose sys session stat

# Clear all sessions matching filter (disruptive)
diagnose sys session clear

# Sessions with specific protocol
diagnose sys session filter proto 6        # TCP
diagnose sys session filter proto 17       # UDP

# Flow trace — see what FortiOS does with a packet end-to-end
diagnose debug reset
diagnose debug flow filter saddr 10.1.1.5
diagnose debug flow filter daddr 8.8.8.8
diagnose debug flow trace start 10
diagnose debug enable
# … reproduce traffic …
diagnose debug disable
diagnose debug reset
```

`diagnose debug flow` is the workhorse — it shows policy match, NAT decision, route lookup, UTM verdict, drop/forward.

### 4.2 Routing

```fortios
# Routing table
get router info routing-table all
get router info routing-table database
get router info routing-table details <prefix>

# BGP
get router info bgp summary
get router info bgp neighbors
get router info bgp neighbors <ip> received-routes
get router info bgp neighbors <ip> advertised-routes

# OSPF
get router info ospf neighbor
get router info ospf interface
get router info ospf database

# Static routes (in config)
show router static
```

**BGP convergence note**: minimum holdtime without BFD is 3 seconds (current as of FortiOS 7.6 — verify in current release). Lower-than-3s holdtime requires BFD; pure timer reduction without BFD risks false flaps under control-plane load.

### 4.3 IPsec VPN

```fortios
# Tunnel status
get vpn ipsec tunnel summary
diagnose vpn tunnel list
diagnose vpn tunnel list name <tunnel-name>

# IKE debug
diagnose debug reset
diagnose vpn ike log-filter dst-addr4 <peer-IP>
diagnose debug application ike -1
diagnose debug enable
# … initiate / re-key …
diagnose debug disable
diagnose debug reset

# Selectors / proposals mismatch
diagnose vpn ike gateway list
```

Common failure modes:
- Phase 1: proposal mismatch, PSK mismatch, certificate trust issues
- Phase 2: selector mismatch (the most common — exact SA selectors must match)
- NAT-T: when behind NAT, ensure NAT-T enabled both ends
- DPD timing causing premature teardown

### 4.4 SSL VPN / Agentless VPN

**Note**: SSL VPN tunnel mode has been replaced with IPsec VPN starting in FortiOS 7.6.x. Agentless VPN (formerly SSL VPN web mode) remains. For new deployments, use IPsec; SSL VPN tunnel mode is on a deprecation track.

```fortios
# Connection status (where still applicable)
diagnose vpn ssl statistics
diagnose vpn ssl list

# User connections
diagnose vpn ssl web user-list
```

Verify in `docs.fortinet.com` → 7.6 admin guide for the current state of SSL VPN / Agentless VPN support per your version.

### 4.5 SD-WAN

```fortios
# SD-WAN service / member status
diagnose sys sdwan service
diagnose sys sdwan member

# SLA health
diagnose sys sdwan health-check
diagnose sys sdwan health-check status

# Per-member packet/jitter/loss
diagnose sys sdwan sla-log <sla-id>

# Steering decision per session
diagnose sys sdwan zebos-cli ...   # varies; check version

# Application steering
diagnose firewall iprope appctrl list
```

Common SD-WAN issues:
- SLA probes failing → wrong probe target or asymmetric routing
- Steering not behaving → policy ordering, application detection lag
- Performance SLA flapping → tune SLA thresholds and packet loss tolerance

### 4.6 HA

```fortios
# HA cluster state
get system ha status
diagnose sys ha status
diagnose sys ha checksum show
diagnose sys ha checksum cluster   # checksum match across cluster?

# Failover-influencing
diagnose sys ha override-table       # any override active?
diagnose sys ha hbdev                # heartbeat interface state

# Force failover (disruptive — only with planned window)
execute ha failover set 1
```

Common HA issues:
- Heartbeat interface flap → check physical, dedicated heartbeat link, no spanning-tree on heartbeat interface
- Checksum mismatch → typically a config sync issue or management-on-secondary causing drift
- Active-Active session-table issues → verify load-balance method and session-pickup config

### 4.7 DNS / dnsproxy

```fortios
# DNS proxy state
diagnose test application dnsproxy 1   # show stats
diagnose test application dnsproxy 2   # show DNS database
diagnose test application dnsproxy 3   # clear DNS database

# DNS lookups from FortiGate itself
execute ping host www.example.com
diagnose sniffer packet any 'port 53' 4

# DNS server config
get system dns
show system dns-database
```

Known issue worth flagging: in some FortiOS 7.6.x versions, dnsproxy CPU spikes have been observed in conjunction with wildcard FQDN objects under specific conditions. If diagnosing high `dnsproxy` CPU with wildcard FQDNs, search KB for the FortiOS build's known issues and check release notes.

### 4.8 Authentication (FSSO / SAML / RADIUS)

```fortios
# FSSO collector status
diagnose debug authd fsso list
diagnose debug authd fsso server-status

# RADIUS
diagnose test authserver radius <server-name> <auth-method> <user> <pass>

# LDAP
diagnose test authserver ldap <server-name> <user> <pass>

# SAML
diagnose debug application samld -1
diagnose debug enable
# … initiate SAML auth …
diagnose debug disable
```

For SAML / Entra ID outbound-policy authentication: configure SAML SP on the FortiGate, IdP on Entra, and policy with `auth-cert + saml-sp-realm` style — check the current admin guide for the exact wiring per FortiOS version.

### 4.9 UTM (IPS, AV, Web filter, App control)

```fortios
# Engine status
diagnose autoupdate versions
get system fortiguard

# IPS
diagnose ips status
diagnose ips packet log status
diagnose test application ipsmonitor 5

# AV
diagnose antivirus database-info
diagnose antivirus quarantine list

# Web filter
diagnose webfilter fortiguard cache list

# Application control
diagnose application list
```

### 4.10 SSL DPI / Deep Inspection

```fortios
# Certificate verification
diagnose vpn certificate ca list
diagnose vpn certificate local list

# SSL exemptions and policy hits
get firewall ssl-ssh-profile <profile>

# Sniffer for SSL handshake
diagnose sniffer packet any 'port 443 and host <client-ip>' 4
```

Common SSL DPI issues:
- Certificate not in client trust store → for transparent SSL DPI to work, the FortiGate's CA must be in the client's trusted root (Windows machine store, not user store, for service traffic)
- Apps that pin certificates (Apple, banks, some mobile apps) → must be exempted, not inspected
- Performance regression with SSL DPI on → see sizing notes; SSL DPI throughput is the constraining figure

### 4.11 FortiSwitch (FortiLink)

```fortios
# Switch list
get switch-controller managed-switch
diagnose switch-controller switch-info

# Per-switch status
execute switch-controller managed-switch get-stats <switch-id>
diagnose switch-controller switch-info dynamic-port <switch-id>

# Switch CLI passthrough (run a command on the switch from the FortiGate)
execute switch-controller switch-action <switch-id> ...
```

**Empty admin password gotcha**: FortiOS 7.6.1+ no longer permits empty admin passwords on managed FortiSwitches. On upgrade, FortiGate will auto-generate one. Document this for customers.

### 4.12 FortiAP (wireless)

```fortios
# AP status
get wireless-controller managed-ap
diagnose wireless-controller wlac -c

# Client list
diagnose wireless-controller wlac -d sta

# RF / signal
diagnose wireless-controller wlac -d ap

# Specific debug
diagnose debug application wpad -1
diagnose debug application cw_acd -1
```

---

## 5. Packet capture

The sniffer is invaluable. Verbosity levels:

```fortios
diagnose sniffer packet <interface> '<filter>' <verbosity> <count> <a/l/none>

# verbosity:
#   1 = headers only
#   2 = headers + packet data
#   3 = headers + ethernet + IP + payload
#   4 = like 3, with interface name
#   5 = like 3, with interface name and packet data
#   6 = like 4, with interface name and ascii dump

# count: 0 = unlimited (Ctrl-C to stop)
# a/l: 'a' for absolute time, 'l' for local time
```

Examples:
```fortios
# All traffic on port1
diagnose sniffer packet port1 '' 4 0 l

# Specific host both directions
diagnose sniffer packet any 'host 10.1.1.5' 4 100 l

# DNS only
diagnose sniffer packet any 'port 53' 4 100 l

# IPsec (UDP 500/4500 + ESP)
diagnose sniffer packet any '(port 500 or port 4500 or proto 50)' 4 100 l
```

For longer captures or when you need a real PCAP, two options (the CLI has **no** output redirection):

- **CLI + conversion**: run the sniffer at verbosity 6 with your terminal client logging the session to a file, then convert the text log to PCAP with Fortinet's `fgt2eth` conversion tool (available via Fortinet KB — search "fgt2eth") and open in Wireshark.
- **GUI packet capture**: Network → Diagnostics → Packet Capture (location varies slightly by FortiOS version) produces a downloadable `.pcap` directly — usually the faster path when GUI access exists.

---

## 6. Log analysis and FortiAnalyzer queries

When the FortiGate alone is insufficient (history beyond memory buffer), turn to FortiAnalyzer.

FortiAnalyzer query language allows:
- Time-bounded queries
- Field-specific filters
- Aggregations (top-N, time-series)
- Cross-device queries within an ADOM

For event correlation across multiple devices, FortiAnalyzer's event handlers + FortiView are typically faster than building queries from scratch.

For complex investigations: pull logs to FortiSIEM or FortiSOAR for advanced correlation.

---

## 7. Performance and resource diagnostics

```fortios
# CPU per process
diagnose sys top 5 30

# Memory pressure / conserve mode
diagnose hardware sysinfo memory
diagnose hardware sysinfo conserve

# Per-CPU
diagnose sys cpuset

# NPU offload status
diagnose npu np6 list   # or np7, depending on hardware
diagnose npu np6 sse-stats
```

When the system is in **conserve mode**, expect:
- Some new sessions dropped
- UTM features may degrade
- Logging may throttle
- Common cause: under-sized FortiGate for the actual load, or memory leak (escalate to TAC)

---

## 8. Common debug-flag reference

```fortios
# Enable debug for a specific application
diagnose debug application <app> <level>
# Levels: 0 = off, -1 = max verbose, 1-7 = increasing verbosity (varies)

# Common applications
diagnose debug application ike -1
diagnose debug application sslvpn -1
diagnose debug application authd -1
diagnose debug application dhcprelay -1
diagnose debug application dnsproxy -1
diagnose debug application httpsd -1
diagnose debug application miglogd -1
diagnose debug application updated -1   # FortiGuard updates

# Always pair with:
diagnose debug enable      # turn on debug output
diagnose debug disable     # turn it off when done
diagnose debug reset       # clear all debug state
```

**Discipline**: always end a debug session with `diagnose debug disable` and `diagnose debug reset`. Forgetting this leaves debug output streaming, occasionally degrades performance, and pollutes logs.

---

## 9. Anti-patterns

- **Running `diagnose debug` without flow filters** in a production environment — output is overwhelming and may impact CPU
- **Using `execute` commands without verifying impact** — e.g., `execute factoryreset` is unrecoverable; `execute reboot` interrupts service
- **Misreading session table empty as "no traffic"** — sessions may be NPU-offloaded; check NPU stats
- **Diagnosing in conserve mode without addressing conserve mode first** — many symptoms are downstream of conserve
- **Comparing across FortiOS versions without verifying behavior changed** — the same command may produce different output on 7.4 vs 7.6
- **Relying on `get system status` alone** — confirm HA state, conserve state, and FortiGuard status separately
- **Citing CLI from memory** — verify against the CLI reference for the exact version, especially when crossing major versions

---

## Standard troubleshooting deliverable

When writing up a troubleshooting investigation for a customer or a peer, include:

```
Symptom
  Concrete description, scope, time of onset

Hypothesis tested
  Prioritized list with rationale

Diagnostics run
  Commands, expected output to confirm/deny each hypothesis

Findings
  What was confirmed/denied

Root cause
  Specific subsystem and failure mode

Fix
  Steps applied, with rollback path

Validation
  How the fix was verified

Lessons / preventive actions
  Config or process change to prevent recurrence

Open items
  What's still uncertain
```

This frame is good for runbook entries, RCA documents, and customer-facing summaries.
