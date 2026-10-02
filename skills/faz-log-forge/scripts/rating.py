"""
rating.py - synthetic Security Rating result stream ("Xlog", msg_tag=fgt-security-rating).

Modelled on real FortiAnalyzer exports of the stream from a FortiGate 90G (FortiOS 7.6.6) and
a FortiGate VM (FortiOS 8.0.0): every check name, severity, PSIRT title, result value,
recommendation element type and the per-run multiplicity come from
data/security_rating_checks.json, which scripts/ingest_rating_export.py builds from those
exports. The scheduler behaviour (three full runs a day at 06:00 / 14:00 / 22:00 UTC, results
batched into sessions of up to 30 messages, occasional partial re-runs) is also observed.

What this stream does and does not do in FortiAnalyzer:
  * feeds Fabric View > Security Rating, the FSBP / PCI / CIS security-rating reports and the
    Fabric State of Security monitor
  * the check FortiguardIotVulnerability lists (as MAC addresses) the IoT/OT assets the
    FortiGate found vulnerable - this is the only place in the whole log stream where a
    per-asset vulnerability signal exists
  * the FG-IR-* checks are the FortiGate's OWN PSIRT vulnerabilities, not those of the assets
  * it does NOT populate the per-asset CVE list in the Asset Identity Center; that arrives over
    the OFTP endpoint data link from the FortiGate device store, not as log records
    (see references/assets-and-iot.md)

Unknowns, flagged rather than guessed:
  * the on-the-wire (OFTP) encoding of this stream is not public. The CSV writer reproduces the
    FortiAnalyzer Log View export byte-for-byte; the "raw" writer is an educated guess.
  * whether `execute log import` accepts either form has not been confirmed on a real unit.
  * the recommendation payload of a FAILED FG-IR check was never observed (every PSIRT check in
    the reference exports passed); a failed one is emitted with an empty structure.
"""
import copy, json, os, random, re
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(os.path.dirname(HERE), "data")

MAC_RE = re.compile(r"^([0-9a-f]{2}:){5}[0-9a-f]{2}$")
INTF_RE = re.compile(r"^(port\d+|v[A-Z][\w-]*|FEX-WAN|x\d+|MGMT|wan\d*|lan\d*|internal\d*)$")
SWITCH_RE = re.compile(r"-FSW-\d+$")

# Checks whose result is tied to what the generator knows about the fleet, not sampled.
LICENCE_CHECKS = {
    "FortiguardIps", "FortiguardAntiVirus", "FortiguardWebFiltering", "FortiguardAntiSpam",
    "FortiguardIndustrialDb", "FortiguardFirmwareGeneralUpdates", "FortiguardSecurityRating",
    "FortiguardIotDetection", "FortiguardOutbreakPrevention", "FortiguardFiltering",
}
# The "poor" posture flips these to failed (all have an observed failed recommendation shape).
POOR_FAILS = [
    "WanManagementAccess", "TwoFactorAuthentication", "TrustedHosts", "IdleTimeout",
    "LoginAttempts", "AdminPasswordSecurity", "DefaultPortHttps", "InterfaceClassification",
    "DeviceDiscovery", "EndpointRegistration", "VlanMissingPolicies", "CertificateExpiry",
    "FortiSandboxConfigured", "LoggingReporting", "RogueApDetection", "WidsSignatures",
    "SystemUptime", "TwoFactorAuthenticationVpnUsers",
]
# The "good" posture leaves only these failed (hygiene items almost every real unit fails).
GOOD_KEEPS_FAILED = ["WanManagementAccess", "TwoFactorAuthentication"]
# Checks that get re-run outside the 8-hour schedule after a policy / interface change.
# Order and membership observed in the 8.0 export; the 7.6 unit re-ran a similar policy set.
POLICY_RERUN = [
    "VlanManagement", "VlanMissingPolicies", "WanManagementAccess", "UnsecureProtocolHttp",
    "UnsecureProtocolTelnet", "SsidInsecureProtocols", "SecureWirelessConnections",
    "InterfaceClassification", "DetectBotnetConnections", "LanSegmentServers",
    "EndpointRegistration", "AdminSportIkeTcpPortConfict", "DeviceDiscovery",
]


def _load():
    with open(os.path.join(DATA, "security_rating_checks.json"), encoding="utf-8") as fh:
        return json.load(fh)


class SecurityRating:
    def __init__(self, gen):
        self.g = gen
        self.a = gen.a
        self.rnd = random.Random(gen.a.seed * 31 + 7)
        self.cat = _load()
        self.checks = self.cat["checks"]
        prof = self.cat["profiles"].get(gen.a.version)
        if prof is None:  # no export for this FortiOS line yet - borrow the closest one
            prof = self.cat["profiles"][sorted(self.cat["profiles"])[-1]]
        self.prof = prof
        self.posture = getattr(gen.a, "rating_posture", "typical")
        self.psirt_fail = {x.strip() for x in (getattr(gen.a, "psirt_fail", "") or "").split(",") if x.strip()}
        self.remediate_after = getattr(gen.a, "rating_remediate_after", 0) or 0
        self.adom = getattr(gen.a, "adom", "root")
        self.idseq = 171308242746474000 + self.rnd.randint(100, 900)
        self.session_ms = self.rnd.randint(100, 999)
        self.state = {}
        self._decide()

    # ------------------------------------------------------------------ dataset-level state
    def _decide(self):
        """Pick one result per check for the whole dataset. Configuration checks do not flip
        every eight hours on a real unit, so the stream must be stable across runs."""
        rnd = self.rnd
        for name in self.prof["multiplicity"]:
            c = self.checks.get(name)
            if c is None:
                continue
            if c["kind"] == "psirt":
                self.state[name] = "failed" if name in self.psirt_fail else "passed"
                continue
            obs = c["results"]
            if name == "FortiguardIotVulnerability":
                self.state[name] = "dynamic"; continue
            if name in ("FortiAnalyzerConnection", "LoggingReporting", "FortiguardSecurityRating"):
                self.state[name] = "passed"; continue
            if name in LICENCE_CHECKS:
                self.state[name] = "passed"; continue
            if self.posture == "good":
                if name in GOOD_KEEPS_FAILED and "failed" in obs:
                    self.state[name] = "failed"
                elif "passed" in obs or "failed" in obs:
                    self.state[name] = "passed"
                else:  # exempt / unmetDependencies only - not a failure, keep as observed
                    self.state[name] = max(obs, key=obs.get)
                continue
            if self.posture == "poor" and name in POOR_FAILS and "failed" in obs:
                self.state[name] = "failed"; continue
            # typical: weighted sample from what the two reference units reported
            keys = list(obs); weights = [obs[k] for k in keys]
            if "error" in keys:  # a transient FortiCare lookup error - keep it rare
                weights[keys.index("error")] = 1
            self.state[name] = rnd.choices(keys, weights=weights, k=1)[0]
        if self.posture == "poor":
            # one expired FortiGuard subscription and two critical PSIRTs, if none were given
            self.state["FortiguardAntiSpam"] = "failed"
            if not self.psirt_fail:
                crit = [n for n in self.prof["multiplicity"]
                        if n.startswith("FG-IR-") and self.checks[n]["severity"] == "critical"]
                for n in sorted(crit)[-2:]:
                    self.state[n] = "failed"

    def result_for(self, name, day_index):
        r = self.state.get(name, "passed")
        if r == "dynamic":
            return "failed" if any(h.get("vulncnt", 0) > 0 for h in self.g.hosts) else "passed"
        if self.remediate_after and day_index >= self.remediate_after and r == "failed" \
                and name in ("WanManagementAccess", "TwoFactorAuthentication", "IdleTimeout",
                             "LoginAttempts", "TrustedHosts", "DefaultPortHttps"):
            return "passed"
        return r

    # ------------------------------------------------------------------ recommendations
    def _mkeys_for(self, name, sample):
        """What the list entries of a failed check should point at in this fleet."""
        f = self.g.f
        zones = [z["name"] for z in f["zones"]]
        if name == "FortiguardIotVulnerability":
            macs = sorted(h["mac"] for h in self.g.hosts if h.get("vulncnt", 0) > 0)
            return macs[:60]
        if name == "WanManagementAccess":
            return [f["wan"]["intf"]]
        if name in ("DeviceDiscovery", "EndpointRegistration", "VlanMissingPolicies", "VlanManagement"):
            k = max(1, min(len(zones), self.rnd.randint(1, 3)))
            return sorted(self.rnd.sample(zones, k))
        if name == "FortiSwitchFortiLinkRedundancy":
            return ["%s-FSW-01" % self.a.devname.rsplit("-", 2)[0]]
        if name == "CertificateExpiry":
            return ["FAC_SAML"]
        return sample

    def _fill(self, node, name):
        """Deep-copy an observed recommendation structure and re-point fleet-specific values."""
        if isinstance(node, list):
            out = []
            entries = [n for n in node if isinstance(n, dict) and n.get("type") == "OmniSourceDescriptorRecommendationElement"]
            if entries:
                keys = self._mkeys_for(name, [e["mkey"] for e in entries])
                for k in keys:
                    out.append({"type": "OmniSourceDescriptorRecommendationElement", "mkey": k})
                for n in node:
                    if not (isinstance(n, dict) and n.get("type") == "OmniSourceDescriptorRecommendationElement"):
                        out.append(self._fill(n, name))
                return out
            return [self._fill(n, name) for n in node]
        if isinstance(node, dict):
            d = {}
            for k, v in node.items():
                if k == "interpolateData":
                    v = [self._interp(x) for x in v]
                d[k] = self._fill(v, name)
            return d
        return node

    def _interp(self, x):
        x = dict(x)
        if x.get("type") == "date":  # licence expiry - three months before the dataset
            x["value"] = int((self.g.start_dt - timedelta(days=90)).replace(tzinfo=None).timestamp())
        elif x.get("type") == "string" and isinstance(x.get("value"), str):
            users = self.g.f.get("users") or ["admin"]
            x["value"] = self.rnd.choice(users)
        return x

    def recommendation(self, name, result):
        c = self.checks[name]
        cands = [r for r in c["recommendations"] if r["result"] == result]
        if not cands:
            if result == "failed" and c["kind"] == "psirt":
                # never observed - see module docstring
                return [{"structure": []}]
            if result in ("failed", "unmetDependencies", "exempt", "error"):
                any_ = [r for r in c["recommendations"]]
                if any_:
                    return self._fill(copy.deepcopy(self.rnd.choice(any_)["structure"]), name)
                return [{"structure": []}]
            return None
        # prefer the richest observed shape (the one with list entries)
        cands.sort(key=lambda r: len(json.dumps(r["structure"])), reverse=True)
        return self._fill(copy.deepcopy(cands[0]["structure"]), name)

    def severity(self, name, result):
        c = self.checks[name]
        if result == "failed" and "medium" in c.get("severity_alt", []) and name in LICENCE_CHECKS:
            return "medium"  # expired subscription is reported as medium, valid as critical
        return c["severity"]

    # ------------------------------------------------------------------ record assembly
    def _epoch(self, dt):
        return int((dt - datetime(1970, 1, 1)).total_seconds() - self.a.tz * 3600)

    def _emit(self, names, dt, day_index):
        base = self._epoch(dt)
        per_sec = self.rnd.randint(35, 60)
        chunk = 30
        recs = []
        for i, name in enumerate(names):
            itime = base + i // per_sec
            if i % chunk == 0:
                sess_id = itime * 1000 + self.session_ms
                self.idseq += self.rnd.randint(1, 3)
            result = self.result_for(name, day_index)
            msg = {"messageVersion": 1, "check": name, "title": self.checks[name]["title"],
                   "severity": self.severity(name, result),
                   "timestamp": itime * 1000 + self.rnd.randint(-800, 500),
                   "device": self.a.devid, "vdom": self.a.vdom, "result": result}
            rec = self.recommendation(name, result)
            if rec is not None:
                msg["recommendations"] = rec
            recs.append({
                "itime": itime, "devid": self.a.devid, "adom_name": self.adom, "idseq": self.idseq,
                "logver": self.g.v["logver"], "msg": msg, "msg_format": "json",
                "msg_tag": "fgt-security-rating", "reporting_ip": self.g.f["mgmt_ip"],
                "session_id": sess_id, "session_msg_idx": 0,
                "date": dt.strftime("%Y-%m-%d"),
            })
        self.g.xlog.extend(recs)
        return len(recs)

    def full_run(self, dt, day_index):
        """One scheduled run: every check the profile knows, repeated per report membership,
        in the (roughly reverse-alphabetical) order the scheduler emits them."""
        names = []
        for name in sorted(self.prof["multiplicity"], reverse=True):
            if name not in self.checks:
                continue
            if self.rnd.random() > self.prof["present_in_runs"].get(name, 1.0):
                continue
            names += [name] * self.prof["multiplicity"][name]
        # the real stream is not strictly sorted - nudge neighbours
        for i in range(0, len(names) - 3, 3):
            if self.rnd.random() < 0.35:
                j = i + self.rnd.randint(1, 3)
                names[i], names[j] = names[j], names[i]
        return self._emit(names, dt, day_index)

    def partial_run(self, dt, day_index, group="faz"):
        if group == "faz":
            names = ["FortiAnalyzerConnection", "FortiAnalyzerConnection"]
        else:
            names = []
            for name in POLICY_RERUN:
                if name in self.checks and name in self.prof["multiplicity"]:
                    names += [name] * self.prof["multiplicity"][name]
            self.rnd.shuffle(names)
        return self._emit(names, dt, day_index)


# ---------------------------------------------------------------------- renderers
XLOG_COLUMNS = ["itime", "date", "time", "devid", "adom_name", "idseq", "logver", "msg",
                "msg_format", "msg_tag", "reporting_ip", "session_id", "session_msg_idx"]
XLOG_QUOTED = {"devid", "adom_name", "logver", "msg", "msg_format", "msg_tag", "reporting_ip"}


def xlog_csv_row(rec):
    """Cells in the exact layout of a FortiAnalyzer Log View CSV export of this stream:
    positional columns, the field name repeated inside each cell, string values quoted, the
    date and time cells empty (the stream has neither). Write with csv.QUOTE_ALL so the
    inner quotes are doubled exactly as FortiAnalyzer does."""
    cells = []
    for col in XLOG_COLUMNS:
        if col in ("date", "time"):
            cells.append("")
            continue
        v = rec[col]
        if col == "msg":
            v = json.dumps(v, separators=(",", ":"), ensure_ascii=False)
        if col in XLOG_QUOTED:
            cells.append('%s="%s"' % (col, v))
        else:
            cells.append("%s=%s" % (col, v))
    return cells


def xlog_raw_line(rec):
    """Best guess at a key=value wire form. NOT observed on any FortiGate; the FortiAnalyzer
    envelope fields (itime, idseq, adom_name, reporting_ip, session_*) are left out because
    the FortiAnalyzer assigns them on receipt."""
    js = json.dumps(rec["msg"], separators=(",", ":"), ensure_ascii=False).replace('"', '\\"')
    return ('logver=%s devid="%s" vd="%s" msg_format="json" msg_tag="fgt-security-rating" msg="%s"'
            % (rec["logver"], rec["devid"], rec["msg"]["vdom"], js))
