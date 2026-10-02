#!/usr/bin/env python3
"""
ingest_rating_export.py - build data/security_rating_checks.json from real FortiAnalyzer
Xlog CSV exports (Log View > download of the security-rating stream, msg_tag=fgt-security-rating).

Every check name, severity, PSIRT title, observed result, recommendation structure and
per-run multiplicity in the catalogue comes from a real FortiGate. Nothing is invented here;
re-run this whenever you have a newer export so the catalogue tracks new FG-IR advisories.

    python3 scripts/ingest_rating_export.py \
        --export 7.6=FGT90GDEMO000001_root_Xlog_1785650404.csv \
        --export 8.0=FGVMEVDEMO0000099_root_Xlog_1786349661.csv \
        --out data/security_rating_checks.json

Merging: an existing catalogue is loaded first, so checks seen in older exports survive.
"""
import argparse, collections, csv, datetime, json, os, re, sys

csv.field_size_limit(10 ** 9)


def rows(fn):
    with open(fn, newline="", encoding="utf-8") as fh:
        for row in csv.reader(fh):
            d = {}
            for cell in row:
                if "=" in cell:
                    k, v = cell.split("=", 1)
                    d[k] = v
            yield d


def msgjson(d):
    msg = d.get("msg", "")
    if msg.startswith('"') and msg.endswith('"'):
        msg = msg[1:-1]
    try:
        return json.loads(msg)
    except json.JSONDecodeError:
        # FortiOS does not escape double quotes inside PSIRT titles (seen on FG-IR-22-345),
        # which makes the JSON invalid. Repair only the title field and retry.
        fixed = re.sub(r'"title":"(.*?)","severity"',
                       lambda m: '"title":"' + m.group(1).replace('"', '\\"') + '","severity"', msg)
        return json.loads(fixed)


def cluster_runs(recs, gap=120):
    """Group records into scheduler runs: a pause of more than `gap` seconds starts a new run."""
    runs, cur, last = [], [], None
    for r in sorted(recs, key=lambda x: (x["itime"], x["session_id"])):
        if last is not None and r["itime"] - last > gap:
            runs.append(cur); cur = []
        cur.append(r); last = r["itime"]
    if cur:
        runs.append(cur)
    return runs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--export", action="append", required=True,
                    help="<version>=<path>, e.g. 8.0=FGVM..._Xlog_....csv (repeatable)")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                                  "data", "security_rating_checks.json"))
    a = ap.parse_args()

    cat = {"_provenance": {}, "checks": {}, "profiles": {}}
    if os.path.exists(a.out):
        with open(a.out, encoding="utf-8") as fh:
            cat = json.load(fh)
        cat.setdefault("checks", {}); cat.setdefault("profiles", {}); cat.setdefault("_provenance", {})

    for spec in a.export:
        version, _, path = spec.partition("=")
        if not path:
            sys.exit("--export wants <version>=<path>")
        recs = []
        for d in rows(path):
            j = msgjson(d)
            recs.append({"itime": int(d["itime"]), "session_id": int(d["session_id"]), "j": j,
                         "devid": d["devid"].strip('"'), "logver": d["logver"].strip('"'),
                         "reporting_ip": d["reporting_ip"].strip('"')})
        runs = cluster_runs(recs)
        full = [r for r in runs if len(r) > 50]
        partial = [r for r in runs if len(r) <= 50]

        # ---- per-check facts
        for r in recs:
            j = r["j"]
            c = cat["checks"].setdefault(j["check"], {
                "severity": j["severity"], "title": j["title"], "results": {},
                "recommendations": [], "seen_on": [], "kind": "psirt" if j["check"].startswith("FG-IR-") else "config",
            })
            c["results"][j["result"]] = c["results"].get(j["result"], 0) + 1
            if version not in c["seen_on"]:
                c["seen_on"].append(version)
            # PSIRT checks carry the advisory title; keep the longest title seen
            if len(j["title"]) > len(c["title"]):
                c["title"] = j["title"]
            if j.get("severity") and c["severity"] != j["severity"]:
                # a few FortiGuard licence checks flip between medium (expired) and critical
                c.setdefault("severity_alt", [])
                if j["severity"] not in c["severity_alt"] and j["severity"] != c["severity"]:
                    c["severity_alt"].append(j["severity"])
            rec = j.get("recommendations")
            if rec is not None:
                key = json.dumps(rec, sort_keys=True)
                known = {json.dumps(x["structure"], sort_keys=True): x for x in c["recommendations"]}
                if key not in known:
                    c["recommendations"].append({"result": j["result"], "structure": rec})

        # ---- per-version profile: multiplicity per full run, run cadence, batch sizes
        mult = collections.defaultdict(list)
        for run in full:
            cnt = collections.Counter(x["j"]["check"] for x in run)
            for k, v in cnt.items():
                mult[k].append(v)
        prof = cat["profiles"].setdefault(version, {})
        prof["logver"] = recs[0]["logver"]
        prof["source_devid"] = recs[0]["devid"]
        prof["full_runs_observed"] = len(full)
        prof["checks_per_run_avg"] = round(sum(len(r) for r in full) / max(1, len(full)), 1)
        prof["run_start_utc"] = sorted(collections.Counter(
            datetime.datetime.fromtimestamp(r[0]["itime"], datetime.timezone.utc).strftime("%H:%M") for r in full).items(),
            key=lambda x: -x[1])[:3]
        prof["run_span_seconds"] = sorted(set(r[-1]["itime"] - r[0]["itime"] for r in full))
        sess = collections.Counter()
        for run in full:
            sess.update(collections.Counter(x["session_id"] for x in run).values())
        prof["session_size_max"] = max(sess) if sess else 30
        prof["multiplicity"] = {k: collections.Counter(v).most_common(1)[0][0] for k, v in sorted(mult.items())}
        prof["present_in_runs"] = {k: round(len(v) / max(1, len(full)), 2) for k, v in sorted(mult.items())}
        # partial runs: which check groups get re-run outside the schedule
        groups = collections.Counter()
        for run in partial:
            groups[tuple(sorted(set(x["j"]["check"] for x in run)))] += 1
        prof["partial_run_groups"] = [{"checks": list(k), "seen": v} for k, v in groups.most_common(6)]
        cat["_provenance"][version] = (
            "built from FortiAnalyzer Xlog CSV export %s (%d records, %d full runs, %d partial runs)"
            % (os.path.basename(path), len(recs), len(full), len(partial)))

    cat["_provenance"]["note"] = (
        "Every check, severity, title, result and recommendation shape here was observed in a real "
        "fgt-security-rating stream. severity_alt lists the second severity seen for FortiGuard licence "
        "checks (critical when the subscription is valid, medium when it has expired). Do not add checks "
        "by hand - re-run scripts/ingest_rating_export.py on a newer export instead.")
    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump(cat, fh, indent=1, ensure_ascii=False)
    print("checks      : %d (%d PSIRT / %d configuration)" % (
        len(cat["checks"]),
        sum(1 for c in cat["checks"].values() if c["kind"] == "psirt"),
        sum(1 for c in cat["checks"].values() if c["kind"] == "config")))
    for v, p in cat["profiles"].items():
        print("profile %-4s: logver=%s %d full runs, ~%s results/run, starts %s" % (
            v, p["logver"], p["full_runs_observed"], p["checks_per_run_avg"], p["run_start_utc"]))
    print("written     : %s" % a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
