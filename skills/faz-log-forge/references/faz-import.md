# Importing generated logs into FortiAnalyzer

Verified against the FortiAnalyzer 7.6.x and 8.0.0 CLI reference and administration guide.

## 1. The device must exist first

`execute log import` replaces the device ID on the imported logs with the serial you pass,
and the CLI reference says that serial must be "a device serial number of one of your log
devices". The GUI import path is explicit about the failure mode:

> "Before importing the log file you must add all devices included in the log file to the
> importing FortiAnalyzer."
> "If the device_id field in the uploaded log file does not match the device, the import
> fails ... an error is displayed stating `Invalid Device ID`."

The documented way to create a device that does not physically exist is the **model device**
path - it is a supported ZTP feature, not a workaround:

*Device Manager > Add Device > Link Device By: Serial Number* -> enter Name, Serial Number,
Device Model -> Next.

> "When using the Add Device wizard, model devices added to the FortiAnalyzer unit using a
> serial number are authorized and are ready to begin sending logs."

Nothing validates the serial against a licensing database. Pick a serial that matches the
model prefix you claim (`FGVM...` for a VM, `FGT90G...` for a 90G) so the device list looks
plausible.

Notes:
- There is **no** `execute device add` CLI command. Device creation is GUI or JSON API only.
  The `execute device` branch only has `replace pw|sn|user` and `reset database`.
- `config system dev-group` is a per-administrator access-scoping field, not a device registry.
- A device belongs to exactly one ADOM. Moving it later may require an SQL rebuild in the new
  ADOM.
- Extra VDOMs: `execute log device vdom add <device-name> <adom> <vdom>`.

## 2. Widen the analytics window BEFORE importing

This is the number one reason a backdated import "succeeds" but shows nothing. Straight from
the admin guide:

> "To insert imported logs into the SQL database, the `config system sql` `start-time` and
> `rebuild-event-start-time` must be older than the date of the logs that are imported and
> the storage policy for analytic data (the Keep Logs for Analytics field) must also extend
> back far enough."

```
config system sql
    set start-time <hh:mm yyyy/mm/dd>
    set rebuild-event-start-time <hh:mm yyyy/mm/dd>
end
```

Default `start-time` is `00:00 2000/01/01`, so this only bites if someone raised it - but
the ADOM's *Keep Logs for Analytics* value bites often. Retention is evaluated on the log's
**own embedded date**, not on when it arrived:

> "Delete the log file that contains logs which are all outside the configured day retention
> period."

So a 90-day-old synthetic dataset with a 30-day analytics policy will be indexed and then
pruned on the next retention pass. Either shorten the date range or widen the policy for the
duration of the demo.

## 3. Import

```
execute log import <ftp|sftp|scp|tftp> <ip:port> <user-name> <password> <file-name> <device-id>
```

- Transports are exactly ftp, sftp, scp, tftp. There is no USB option.
- Password may be `-` for none; not required for tftp.
- `<file-name>` may be a **directory** (`logs/FGVMEVDEMO0000001/`), which imports everything
  matching inside - up to 10000 files per run.
- The scanner picks up `.log` and `.csv` extensions. `.tar`, `.tar.gz`, `.tgz` and `.tar.bz2`
  archives of multiple log files are also accepted (documented in an older Fortinet KB;
  re-verify on your build if you rely on it).
- Plain uncompressed `.log` works; gzip is not required. FortiAnalyzer renames the file
  internally to `<serial>/tlog.<epoch>.log` regardless of what you called it.

Expected output:

```
Log Import Info: Connect to ftp server 10.0.0.20 ...
Log Import Info: Found 14 .log or .csv files in remote folder ...
Log Import Info: 14 log files found in remote folder, MAX import file setting is 10000 ...
Log Import Info: Log file ... was successfully imported to FGVMEVDEMO0000001/tlog.1785542400.log.
```

Filename convention for the source files (from the Fortinet KB on moving FortiGate disk logs
to FortiAnalyzer): `<serial>.<vdom>.<tlog|elog|plog|rlog>.<timestamp>.log`. `fazgen.py`
follows it (`plog` = VoIP, as in FortiAnalyzer's own exports).

The security-rating stream is written separately as `<serial>.<vdom>.xlog.<timestamp>.csv`
in the FortiAnalyzer export layout. Import it in its own command, after the `.log` files,
and treat the result as an experiment - see the caveat below. FortiAnalyzer does not depend on it - the `<device-id>` argument is what binds
the logs to a device - but it keeps a multi-device directory readable.

## 4. Verify

```
diagnose test application sqllogd 5       # log device scan info
diagnose test application sqllogd 70      # SQL database building progress
diagnose test application fortilogd 17    # logging rate per device
diagnose sql show db-size
execute log-integrity <device-name> <vdom> <log-file-name>
```

Then Log View > FortiGate > Traffic with the time range set to cover the generated dates.
If Log View has data but FortiView and Reports do not, the SQL insert was gated - go back to
step 2.

Log checksums are **not** required on import: `config system global / set log-checksum` is
`none` by default, and it only applies to files FortiAnalyzer rolls itself. Log signing and
OFTP encryption belong to the live streaming path and have no bearing on file import.

Manual rebuild is rarely needed. If you do need it:

```
execute sql-local rebuild-index <adom> <start-time> <end-time>   # targeted, preferred
execute sql-local rebuild-db                                     # full - REBOOTS the unit
diagnose sql status rebuild-db
```

During a full rebuild FortiView, Log View, Event Management and Reports are all unavailable.
Fortinet's own guidance is to contact support before doing one.

## Other injection paths

| Path | When to use |
|---|---|
| `execute log import` | historical backfill - what this skill is built for |
| Syslog / OFTP to FortiAnalyzer on 514 | live streaming during a demo. OFTP uses TCP 514 (TLS) for control and UDP 514 for records; `config log fortianalyzer setting / set reliable enable` on the FortiGate moves records to the encrypted channel |
| `config system log-forward` | FAZ-to-FAZ (`set fwd-server-type fortianalyzer`), or out to syslog/CEF. Forwards logs already ingested; it cannot get a fictitious device accepted |

To stream `fazgen.py` output live instead of importing it, the files are already
newline-delimited raw records, so a plain `logger`/netcat loop with the right RFC 3164 header
works - but the device still has to exist in FortiAnalyzer first, and unauthorized devices
land in *Device Manager > Unauthorized Devices* until you promote them.

## Things that are not documented anywhere

- The minimum field set FortiAnalyzer requires per line. Nothing in Fortinet's docs states
  it. `type` and `subtype` are structurally necessary because the SQL schema is partitioned
  by log type, and a date/time or eventtime is needed for any time bucketing - but treat any
  specific "minimum list" as inference. `fazgen.py` emits the full envelope, so it does not
  matter here.
- The CSV schema `execute log import` accepts for `.csv` files. The scanner accepts the
  extension; the expected column layout is undocumented. Use `.log` raw format for
  traffic/event/VoIP logs. The security-rating stream has no known raw format at all, so
  it is written in the layout FortiAnalyzer itself exports (the only encoding ever seen);
  whether the importer takes it back is **unverified** - `references/security-rating.md`.
- Whether any FortiAnalyzer view reads per-asset vulnerability data from logs. The documented
  source is the OFTP endpoint data link from a FortiOS 7.4+ device store, checked with
  `diagnose test application oftpd 20 fgt-stat`. Do not promise CVE lists from an import.
- Any maximum file size for a single imported log file.
