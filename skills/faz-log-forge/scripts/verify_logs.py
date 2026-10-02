#!/usr/bin/env python3
"""
verify_logs.py - sanity-check generated FortiGate logs before importing them.

Checks the things that actually break a FortiAnalyzer import or leave a dashboard empty:
  * every line parses as key=value
  * the mandatory envelope fields are present on every line
  * date/time and eventtime agree (FAZ retention and the SQL start-time gate both key off
    the log's own date, so a mismatch here means silently missing data)
  * devid/vdom are consistent with the filename and with each other
  * numeric fields are unquoted, string fields are quoted
  * field names are ones FortiOS actually emits
  * the asset fields the Asset Identity Center needs are present on traffic logs
  * the security-rating stream (*.xlog.*.csv) has the FortiAnalyzer export column layout,
    valid JSON in every msg, and its vulnerable-MAC list agrees with assets.csv

    python3 verify_logs.py ./out
    python3 verify_logs.py ./out --strict     # exit non-zero on any warning
"""
import argparse, collections, csv, glob, gzip, json, os, re, sys
from datetime import datetime, timedelta

csv.field_size_limit(10 ** 9)

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from fazgen import FIELD_ORDER, UNQUOTED, VERSIONS  # noqa: E402
from rating import XLOG_COLUMNS  # noqa: E402

KV = re.compile(r'(\w+)=("(?:[^"]*)"|\S*)')
REQUIRED = {"date", "time", "eventtime", "logid", "type", "subtype", "level", "vd", "devid"}
ASSET_FIELDS = {"srcmac", "devtype", "osname", "srchwvendor"}
KNOWN = set(FIELD_ORDER) | {
    "nextstat", "total", "used", "limit", "peer_notif", "in_spi", "out_spi", "espauth",
    "esptransform", "version", "phase2_name", "vcluster", "ha_group", "remote", "alert",
    "desc", "session_id", "policymode", "utmref", "vrf", "cve", "viruscat", "forwardedfor",
    "referralurl", "constraint", "login", "command", "from", "to", "sender", "recipient",
    "subject", "size", "attachment", "scertcname", "scertissuer", "appstatus", "srcinetsvc",
    "srcreputation", "srccity", "dstunauthuser", "dstunauthusersource", "dstuser",
    "clientdeviceid", "clientdeviceowner", "emstag", "emsconnection", "fctemsname", "fctemssn",
}


def parse(line):
    d = {}
    for k, v in KV.findall(line):
        d[k] = (v[1:-1], True) if v.startswith('"') else (v, False)
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--tz", type=int, default=2)
    a = ap.parse_args()

    files = sorted(glob.glob(os.path.join(a.path, "*.log")) + glob.glob(os.path.join(a.path, "*.log.gz")))
    if not files:
        print("no .log files under %s" % a.path); return 2

    err = collections.Counter()
    warn = collections.Counter()
    kinds = collections.Counter()
    logids = collections.Counter()
    unknown = collections.Counter()
    devids, vdoms, logvers = set(), set(), set()
    tmin, tmax = None, None
    nlines = 0
    asset_traffic = 0
    traffic_total = 0

    for path in files:
        base = os.path.basename(path)
        m = re.match(r"([^.]+)\.([^.]+)\.(tlog|elog|plog|xlog)\.(\d+)\.log(\.gz)?$", base)
        if not m:
            warn["filename does not match <devid>.<vdom>.<tlog|elog|plog>.<epoch>.log"] += 1
            fdev = fvd = None
        else:
            fdev, fvd = m.group(1), m.group(2)
        op = gzip.open if path.endswith(".gz") else open
        if m and m.group(3) == "xlog":
            # raw-format security-rating guess: only check that the JSON payload parses
            with op(path, "rt", encoding="utf-8") as fh:
                for line in fh:
                    mm = re.search(r' msg="(.*)"$', line.rstrip("\n"))
                    try:
                        json.loads(mm.group(1).replace('\\"', '"'))
                    except Exception:
                        err["raw xlog line has no parseable msg JSON"] += 1
                    else:
                        xraw = globals().setdefault("_xraw", [0]); xraw[0] += 1
            warn["raw xlog format is an unverified guess - prefer the CSV export layout"] += 1
            continue
        with op(path, "rt", encoding="utf-8") as fh:
            for ln, line in enumerate(fh, 1):
                line = line.rstrip("\n")
                if not line:
                    continue
                nlines += 1
                d = parse(line)
                if not d:
                    err["unparseable line"] += 1; continue
                missing = REQUIRED - set(d)
                if missing:
                    err["missing required field(s): %s" % ",".join(sorted(missing))] += 1
                    continue
                t, st = d["type"][0], d["subtype"][0]
                kinds[t + "/" + st] += 1
                logids["%s %s/%s" % (d["logid"][0], t, st)] += 1
                devids.add(d["devid"][0]); vdoms.add(d["vd"][0])
                if "logver" in d:
                    logvers.add(d["logver"][0])
                # date/time vs eventtime
                try:
                    wall = datetime.strptime(d["date"][0] + " " + d["time"][0], "%Y-%m-%d %H:%M:%S")
                    ev = datetime.utcfromtimestamp(int(d["eventtime"][0]) / 1e9) + timedelta(hours=a.tz)
                    if abs((wall - ev).total_seconds()) > 2:
                        err["date/time disagrees with eventtime"] += 1
                    tmin = wall if tmin is None or wall < tmin else tmin
                    tmax = wall if tmax is None or wall > tmax else tmax
                except Exception:
                    err["bad date/time/eventtime value"] += 1
                if len(d["eventtime"][0]) != 19:
                    err["eventtime is not a 19-digit nanosecond epoch"] += 1
                if fdev and d["devid"][0] != fdev:
                    err["devid does not match filename"] += 1
                if fvd and d["vd"][0] != fvd:
                    err["vdom does not match filename"] += 1
                # quoting
                for k, (v, quoted) in d.items():
                    if k not in KNOWN:
                        unknown[k] += 1
                    if k in UNQUOTED and quoted:
                        err["numeric field %s is quoted" % k] += 1
                    if k not in UNQUOTED and not quoted and v != "":
                        warn["field %s is unquoted" % k] += 1
                if t == "traffic" and st == "forward":
                    traffic_total += 1
                    if ASSET_FIELDS <= set(d):
                        asset_traffic += 1

    # ---- security-rating stream (FortiAnalyzer CSV export layout)
    xfiles = sorted(glob.glob(os.path.join(a.path, "*.xlog.*.csv")))
    xrows = 0; xchecks = collections.Counter(); xres = collections.Counter(); xfail = collections.Counter()
    xmacs = set(); xdays = set()
    for path in xfiles:
        with open(path, newline="", encoding="utf-8") as fh:
            for row in csv.reader(fh):
                xrows += 1
                if len(row) != len(XLOG_COLUMNS):
                    err["xlog row has %d columns, export layout has %d" % (len(row), len(XLOG_COLUMNS))] += 1
                    continue
                cells = {}
                for i, cell in enumerate(row):
                    if cell == "":
                        continue
                    k, _, v = cell.partition("=")
                    if k != XLOG_COLUMNS[i]:
                        err["xlog column %d is %s, expected %s" % (i, k, XLOG_COLUMNS[i])] += 1
                    cells[k] = v
                missing = {"itime", "devid", "msg", "msg_tag", "session_id"} - set(cells)
                if missing:
                    err["xlog row missing %s" % ",".join(sorted(missing))] += 1; continue
                if cells["msg_tag"] != '"fgt-security-rating"':
                    err["xlog msg_tag is not fgt-security-rating"] += 1
                try:
                    j = json.loads(cells["msg"][1:-1])
                except Exception:
                    err["xlog msg is not valid JSON"] += 1; continue
                for k in ("messageVersion", "check", "title", "severity", "timestamp", "device", "vdom", "result"):
                    if k not in j:
                        err["xlog msg missing key %s" % k] += 1
                if j.get("device") != cells["devid"].strip('"'):
                    err["xlog msg.device differs from devid"] += 1
                if abs(int(cells["itime"]) * 1000 - int(j.get("timestamp", 0))) > 5000:
                    err["xlog msg.timestamp drifts from itime by >5s"] += 1
                xchecks[j.get("check")] += 1; xres[j.get("result")] += 1
                xdays.add(datetime.utcfromtimestamp(int(cells["itime"])).strftime("%Y-%m-%d"))
                if j.get("result") == "failed":
                    xfail[j.get("check")] += 1
                if j.get("check") == "FortiguardIotVulnerability":
                    for blk in j.get("recommendations", []):
                        for el in blk.get("structure", []):
                            for e in el.get("entries", []) if isinstance(el, dict) else []:
                                if e.get("type") == "OmniSourceDescriptorRecommendationElement":
                                    xmacs.add(e["mkey"])
    assets_vuln = None
    apath = os.path.join(a.path, "assets.csv")
    if os.path.exists(apath):
        with open(apath, newline="", encoding="utf-8") as fh:
            rd = list(csv.DictReader(fh))
        if rd and "iot_vulncnt" in rd[0]:
            assets_vuln = {r["mac"] for r in rd if int(r["iot_vulncnt"] or 0) > 0}

    print("files            : %d log, %d xlog csv" % (len(files), len(xfiles)))
    print("lines            : %d" % nlines)
    print("time range       : %s .. %s" % (tmin, tmax))
    print("devid            : %s" % ", ".join(sorted(devids)))
    print("vdom             : %s" % ", ".join(sorted(vdoms)))
    print("logver           : %s  (%s)" % (", ".join(sorted(logvers)),
          ", ".join(k for k, v in VERSIONS.items() if v["logver"] in logvers) or "UNKNOWN"))
    print("asset coverage   : %d/%d forward-traffic logs carry srcmac+devtype+osname+srchwvendor (%.1f%%)"
          % (asset_traffic, traffic_total, 100.0 * asset_traffic / max(1, traffic_total)))
    print("\nlog types:")
    for k, v in kinds.most_common():
        print("  %-28s %8d" % (k, v))
    print("\nlog IDs:")
    for k, v in logids.most_common(40):
        print("  %-44s %8d" % (k, v))
    if xrows:
        print("\nsecurity-rating stream:")
        print("  results                 : %d over %d days, %d distinct checks" % (xrows, len(xdays), len(xchecks)))
        print("  results by outcome      : %s" % ", ".join("%s=%d" % kv for kv in xres.most_common()))
        psirt = sorted(k for k in xfail if k.startswith("FG-IR-"))
        cfg = sorted(k for k in xfail if not k.startswith("FG-IR-"))
        print("  failed config checks    : %s" % (", ".join(cfg) or "none"))
        print("  failed PSIRT checks     : %s" % (", ".join(psirt) or "none"))
        print("  IoT-vulnerable MACs     : %d listed by FortiguardIotVulnerability" % len(xmacs))
        if assets_vuln is not None:
            if xmacs and not xmacs <= assets_vuln:
                err["rating lists MACs that assets.csv does not flag vulnerable"] += 1
            elif assets_vuln and not xmacs:
                warn["assets.csv has vulnerable devices but no rating run lists them"] += 1
            else:
                print("  cross-check assets.csv  : ok (%d/%d flagged assets appear in the last run)"
                      % (len(xmacs & assets_vuln), len(assets_vuln)))
        print("  NOTE: this stream feeds Fabric View > Security Rating only; per-asset CVE lists in the")
        print("        Asset Identity Center come over the OFTP endpoint data link, not from logs.")
    if unknown:
        print("\nfield names not in the known FortiOS set (check them against the log reference):")
        for k, v in unknown.most_common():
            print("  %-24s %8d" % (k, v))
    if warn:
        print("\nWARNINGS:")
        for k, v in warn.most_common():
            print("  %-60s %8d" % (k, v))
    if err:
        print("\nERRORS:")
        for k, v in err.most_common():
            print("  %-60s %8d" % (k, v))
        return 1
    print("\nOK - no errors.")
    return 1 if (a.strict and (warn or unknown)) else 0


if __name__ == "__main__":
    sys.exit(main())
