# Troubleshooting Runbook Template

Structured incident response for Fortinet products. Use this as a working document during an incident — capture state as you go, not from memory afterward.

---

## Header

```
Incident ID:        <ticket / case ID>
Customer:           <name>
Date / time started:<UTC + local>
Severity:           <P1 / P2 / P3 / P4>
Reported by:        <user / system>
Engineer on-call:   <name>
War room channel:   <link>
TAC case opened?:   <Y/N — case ID>
```

---

## 1. Symptom statement

Plain-English description of what is broken from the user/business perspective. **Not** a technical hypothesis — that comes later.

> Example: "Users at Branch A cannot reach Salesforce as of 09:14 local time. Internal apps (file shares, Exchange) are reachable. ~80 users affected. No recent changes reported."

---

## 2. Initial scope assessment

| Question | Answer |
|---|---|
| Single user or many? | |
| Single site or multiple? | |
| Single application or multiple? | |
| Time-correlated with any known event? (change, deployment, vendor maintenance) | |
| Reproducible on demand? | |
| Severity / business impact? | |
| Workaround available? | |
| When did it last work? | |

---

## 3. Environment context

| Element | Value | Source |
|---|---|---|
| Affected device(s) | | |
| FortiOS version | | `get system status` |
| FortiManager version | | |
| FortiAnalyzer version | | |
| HA mode | | `get system ha status` |
| Current uptime / last reboot | | |
| Recent config changes (last 24h) | | FMG revision history / `diagnose sys last-modified` |
| Recent FortiGuard / signature updates | | |
| License posture | | `diagnose autoupdate versions`, `execute update-now` if relevant |

---

## 4. Hypotheses (pre-investigation)

List the candidate root causes ranked by likelihood, **before** running diagnostics. Investigation then either confirms or rules out each.

| # | Hypothesis | Likelihood | How to test |
|---|---|---|---|
| 1 | Routing change / convergence issue | M | `get router info routing-table all` + BGP/OSPF state |
| 2 | UTM profile blocking traffic | M | `diagnose debug flow trace` for affected destination |
| 3 | SSL DPI cert/trust issue | L | endpoint cert store check |
| 4 | Internet path issue (ISP / DNS / SaaS-side) | H | external probes, status pages |
| 5 | Recent config change | L | FMG revision diff |

The most common diagnostic mistake is jumping to a hypothesis before listing alternatives. List, then test.

---

## 5. Diagnostics performed

Capture commands run, output (key snippets, not full dumps), and conclusion drawn from each.

### Universal first commands (FortiGate)

| Command | Purpose | Output summary | Conclusion |
|---|---|---|---|
| `get system status` | Version, uptime, HA, license | | |
| `get system performance status` | CPU, memory, conserve mode | | |
| `get system ha status` | HA state, sync, primary/secondary | | |
| `diagnose sys top 5 30` | Top CPU consumers | | |
| `diagnose sys session full-stat` | Session table sizing | | |
| `diagnose hardware sysinfo conserve` | Conserve mode flags | | |
| `get hardware nic <port>` | Interface link / counters | | |

### Connectivity / flow

```
diagnose debug reset
diagnose debug flow filter saddr <src>
diagnose debug flow filter daddr <dst>
diagnose debug flow filter port <port>
diagnose debug flow show iprope enable
diagnose debug flow trace start 100
diagnose debug enable
```

After investigation:

```
diagnose debug disable
diagnose debug reset
```

Captured:

```
<paste the relevant flow trace lines, not the full output>
```

Interpretation: <which policy matched? Was traffic dropped? Where?>

### Sniffer (when needed)

```
diagnose sniffer packet <iface> '<bpf>' <verbosity 1-6> <count> a
```

Verbosity guide:
- 1: header only
- 2: summary
- 3: header + IP addresses
- 4: + payload (hex)
- 5: full packet hex
- 6: + Ethernet header

Captured:

```
<paste relevant lines>
```

### Routing

```
get router info routing-table all
get router info routing-table details <prefix>
get router info bgp summary
get router info ospf neighbor
diagnose ip route list
```

### IPsec

```
get vpn ipsec tunnel summary
diagnose vpn ike gateway list name <name>
diagnose debug application ike -1 (with caution; verbose)
```

### DNS (per known dnsproxy issues)

```
diagnose test application dnsproxy 6
get system fortiguard
```

For wildcard FQDN object–related dnsproxy CPU issues: verify against current KB before reproducing.

### Logs

- FortiAnalyzer search filtered by source IP / dest IP / time window.
- FortiGate local logs: `execute log filter ...` then `execute log display`.

---

## 6. Findings

Plain-language summary of what the diagnostics revealed.

> Example: "Flow trace shows packets matched policy ID 47 and were forwarded to gateway 10.0.0.1; gateway is reachable; downstream BGP route to Salesforce SaaS prefix is missing. Comparison with FortiAnalyzer logs shows the prefix was withdrawn at 09:13 local. Cause: ISP BGP route maintenance window — third-party root cause."

---

## 7. Root cause

| Element | Detail |
|---|---|
| Immediate cause | |
| Underlying cause (5-whys) | |
| Contributing factors | |
| Failed safeguards (what should have caught it earlier) | |

---

## 8. Resolution / mitigation

| Step | Action | Time | Outcome |
|---|---|---|---|
| 1 | <e.g., switched failover to backup ISP via SD-WAN rule> | | restored |
| 2 | <e.g., escalated to ISP via TAC> | | acknowledged |
| 3 | <e.g., monitored BGP convergence post-maintenance> | | reconverged 11:42 |

---

## 9. Customer communication log

| Time | Channel | To | Message summary |
|---|---|---|---|
| 09:25 | email | customer technical lead | acknowledged, investigating |
| 09:55 | war room | all | mitigation in progress, ETA 30 min |
| 10:30 | email | customer leadership | restored, monitoring; full RCA in 24h |

---

## 10. Validation

- [ ] Original symptom confirmed cleared
- [ ] Application owners confirmed (not just "ping works")
- [ ] No regression in adjacent services
- [ ] HA / failover state validated
- [ ] Logs flowing to FortiAnalyzer
- [ ] No alarms in FortiManager / FortiAnalyzer / NMS
- [ ] Customer signed off on closure

---

## 11. Post-incident actions

| # | Action | Owner | Due |
|---|---|---|---|
| 1 | Add monitoring alert for missing-route condition | | |
| 2 | Update SD-WAN failover rule for similar outage class | | |
| 3 | Review change-management for ISP maintenance notifications | | |
| 4 | Add this scenario to chaos / failover drill | | |

---

## 12. Lessons learned

For internal / customer review (RCA document):

- What worked well in the response?
- What slowed us down?
- What detection or prevention should we add?
- What recurring patterns does this incident reveal?

---

## 13. References

- Relevant docs.fortinet.com pages: <links>
- Relevant KB articles: <IDs>
- Internal runbook section: <link>
- TAC case (if opened): <ID>

---

## Standard "level-1" snapshot script (FortiGate)

If you're handing off to TAC or to another engineer, run this and paste the output. Avoids back-and-forth.

```
# Identity
get system status
get system performance status
get system ha status

# License
diagnose autoupdate versions
get system fortiguard

# Health
diagnose hardware sysinfo conserve
diagnose sys top 5 30
diagnose sys session full-stat

# Routing snapshot
get router info routing-table summary

# Recent log hot-spots
diagnose log test
diagnose log filter category 0
diagnose log filter device disk
diagnose log filter dump
```

(Adjust per investigation; this is an opening ledger, not a complete diagnostic.)

---

## Discipline points

- **Capture state at the start** — `get system status`, FMG revision, FAZ snapshot. You'll need it to compare against later.
- **Don't change two things at once.** Single-variable changes are debuggable; combined changes aren't.
- **Always have a rollback** before mitigating. "I'll just try this" without a rollback path is how mitigations become incidents.
- **Don't trust your memory after the fact.** Write the log as you go. The post-mortem suffers when the runbook is reconstructed.
- **TAC is your friend** for hardware behavior, suspected bugs, license/entitlement issues. Open a case early — you can always close it. Have the snapshot script output ready.
- **Communicate at fixed cadence** — even "no update yet, still investigating" is a valuable signal.
- **Resist the urge to mass-update or mass-change.** Tempting under pressure; usually compounds the incident.
