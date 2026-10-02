#!/usr/bin/env python3
"""
fazgen.py - synthetic FortiGate log generator for FortiAnalyzer demo environments.

Emits FortiOS-native raw key=value log files (tlog / elog / plog) that can be pushed into a
FortiAnalyzer with `execute log import`, plus the Security Rating result stream ("xlog",
msg_tag=fgt-security-rating) in FortiAnalyzer's own CSV export layout. Field names, field
values and log IDs are taken from real FortiOS 7.6.6 / 8.0.0 logs and from Fortinet's
published log message reference.

Usage:
    python3 fazgen.py --fleet ot-manufacturing --days 14 --out ./out
    python3 fazgen.py --list-fleets
    python3 fazgen.py --fleet enterprise --days 7 --scenarios ransomware,shadow-iot --scale large

See references/ for what each field means and how to import the result.
"""

import argparse, csv, gzip, hashlib, json, os, random, sys, uuid
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rating import SecurityRating, xlog_csv_row, xlog_raw_line  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")

# --------------------------------------------------------------------------------------
# version profiles
# --------------------------------------------------------------------------------------
VERSIONS = {
    "7.6": {
        "logver": "0706063652",          # FortiOS 7.6.6 build 3652 (observed)
        "dns_resp_pass": "1501054802",
        "dns_resp_nx":   "1501054802",   # 7.6 NXDOMAIN log ID unverified - see references/log-types.md
        "has_profilegroup": False,
        "has_srcserver": False,
        "has_inetsvc": True,
        "has_logsrc": False,             # voip logsrc="voipd" only observed on 8.0
    },
    "8.0": {
        "logver": "0800000167",          # FortiOS 8.0.0 build 0167 (observed)
        "dns_resp_pass": "1501054802",
        "dns_resp_nx":   "1501054807",
        "has_profilegroup": True,
        "has_srcserver": True,
        "has_inetsvc": True,
        "has_logsrc": True,
    },
}

# Canonical raw-log field order. FortiAnalyzer parses key=value pairs order-independently,
# so this only controls how the file reads to a human - but matching FortiOS makes the
# output indistinguishable from a real `execute backup disk alllogs` dump.
FIELD_ORDER = [
    "date", "time", "eventtime", "tz", "logid", "type", "subtype", "eventtype", "level", "vd",
    "logdesc",
    "session_id", "epoch", "eventid", "event_id",
    "srcip", "srcname", "srcport", "src_port", "srcintf", "src_int", "srcintfrole", "srcuuid", "srccountry",
    "srcmac", "mastersrcmac", "srcserver",
    "dstip", "dstname", "dstport", "dst_port", "dstintf", "dst_int", "dstintfrole", "dstuuid", "dstcountry",
    "dstcity", "dstregion", "dstinetsvc", "dstreputation", "dstserver",
    "poluuid", "sessionid", "proto", "action", "policyid", "policy_id", "policyname", "policytype",
    "profile", "profilegroup", "voip_proto", "kind", "service",
    "trandisp", "transip", "transport", "duration",
    "sentbyte", "rcvdbyte", "sentpkt", "rcvdpkt", "sentdelta", "rcvddelta",
    "sentpktdelta", "rcvdpktdelta", "durationdelta",
    "appid", "app", "appcat", "apprisk", "applist", "appact", "utmaction", "countapp",
    "countweb", "countdns", "countssl", "countav", "countips",
    "hostname", "url", "reqtype", "direction", "method", "ratemethod",
    "cat", "catdesc", "incidentserialno",
    "qname", "qtype", "qtypeval", "qclass", "xid", "ipaddr", "rcode",
    "sni", "eventsubtype", "certhash", "cn", "issuer", "keyalgo", "keysize",
    "notafter", "notbefore", "sn", "cipher", "authalgo", "handshake", "kxcurve", "kxproto",
    "tlsver", "mitm",
    "attack", "attackid", "severity", "ref", "count", "profiletype",
    "icmpid", "icmptype", "icmpcode", "identifier",
    "virus", "virusid", "dtype", "filename", "filetype", "filesize", "quarskip",
    "analyticscksum", "analyticssubmit", "checksum", "agent", "httpmethod", "rawdata",
    "fsadevice", "fsaverdict",
    "filteridx", "filtertype", "filtercat", "dlpextra",
    "user", "group", "authproto", "status", "reason", "ui", "remip", "locip", "remport",
    "locport", "outintf", "cookies", "assignip", "tunnelip", "tunnelid", "tunneltype",
    "vpntunnel", "dst_host", "fctuid", "xauthuser", "xauthgroup", "eapuser", "eapauthgroup",
    "useralt", "advpnsc", "init", "mode", "dir", "call_id", "from", "to", "stage", "role", "result",
    "interface", "ip", "mac", "lease", "dhcp_msg", "model", "product", "vendor",
    "versionmin", "versionmax", "vulncnt", "vulnresult",
    "healthcheck", "slamap", "jitter", "latency", "packetloss", "bandwidth",
    "inbandwidthused", "outbandwidthused", "bibandwidthused",
    "inbandwidthavailable", "outbandwidthavailable", "bibandwidthavailable",
    "mosvalue", "moscodec",
    "cpu", "mem", "disk", "totalsession", "setuprate", "sysuptime", "freediskstorage",
    "disklograte", "fazlograte", "waninfo",
    "cfgpath", "cfgobj", "cfgattr", "cfgtid", "uuid", "profileid", "sn",
    "checkname", "auditreporttype", "server",
    "msg", "craction", "crlevel", "crscore",
    "vwlid", "vwlname", "vwlquality",
    "devtype", "osname", "srcfamily", "srchwvendor", "srchwversion", "srcswversion",
    "dstdevtype", "dstosname", "dstfamily", "dsthwvendor",
    "unauthuser", "unauthusersource",
    "logsrc", "devid", "devname", "logver",
]
_ORDER_IDX = {k: i for i, k in enumerate(FIELD_ORDER)}

# Fields FortiOS emits WITHOUT quotes (numeric / boolean-ish). Everything else is quoted.
UNQUOTED = {
    "eventtime", "srcport", "dstport", "sessionid", "proto", "policyid", "duration",
    "sentbyte", "rcvdbyte", "sentpkt", "rcvdpkt", "sentdelta", "rcvddelta",
    "sentpktdelta", "rcvdpktdelta", "durationdelta", "appid", "countapp", "countweb",
    "countdns", "countssl", "countav", "countips", "cat", "qtypeval", "xid", "rcode",
    "keysize", "attackid", "count", "crscore", "craction", "vwlid", "incidentserialno",
    "dstreputation", "srcserver", "dstserver", "identifier", "filesize", "epoch", "eventid",
    "filteridx", "virusid", "logver", "lease", "vulncnt", "tunnelid", "remport", "locport",
    "date", "time", "srcip", "dstip", "transip", "tranip", "remip", "locip", "ip",
    "assignip", "tunnelip", "trueclntip",
    "advpnsc", "stage", "cpu", "mem", "disk", "totalsession", "setuprate", "sysuptime",
    "freediskstorage", "disklograte", "fazlograte", "cfgtid", "profileid", "nextstat",
    "total", "used", "limit", "channel", "signal", "snr", "radioid", "seq",
    "session_id", "event_id", "src_port", "dst_port", "policy_id",
}


def render(rec):
    """dict -> one raw FortiOS log line. A record may carry `_order`, a list that pins the
    position of its fields (log families such as VoIP use their own order in the reference)."""
    order = rec.get("_order")
    if order:
        idx = {k: i for i, k in enumerate(order)}
        keys = sorted((k for k in rec if k != "_order"),
                      key=lambda k: (idx.get(k, 1_000 + _ORDER_IDX.get(k, 10_000)), k))
    else:
        keys = sorted(rec.keys(), key=lambda k: (_ORDER_IDX.get(k, 10_000), k))
    parts = []
    for k in keys:
        v = rec[k]
        if v is None:
            continue
        if k in UNQUOTED:
            parts.append("%s=%s" % (k, v))
        else:
            parts.append('%s="%s"' % (k, str(v).replace('"', "'")))
    return " ".join(parts)


# --------------------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------------------
def load(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as fh:
        return json.load(fh)


def mkuuid(seed):
    h = hashlib.md5(seed.encode()).hexdigest()
    return "%s-%s-51f1-%s-%s" % (h[0:8], h[8:12], h[12:16], h[16:28])


class Clock:
    """Turns a wall-clock datetime into the four time fields FortiOS emits."""

    def __init__(self, tzoffset_hours=2):
        self.tzoff = tzoffset_hours
        self.tzs = "%+03d00" % tzoffset_hours

    def fields(self, dt):
        epoch_ns = int((dt - datetime(1970, 1, 1)).total_seconds() - self.tzoff * 3600) * 1_000_000_000
        epoch_ns += random.randint(0, 999_999_999)
        return {
            "date": dt.strftime("%Y-%m-%d"),
            "time": dt.strftime("%H:%M:%S"),
            "eventtime": epoch_ns,
            "tz": self.tzs,
        }


# Diurnal weight per hour (index 0..23) for office-hours traffic.
OFFICE_CURVE = [2, 1, 1, 1, 1, 2, 6, 18, 45, 70, 85, 90, 75, 88, 92, 85, 70, 45, 28, 20, 15, 10, 6, 3]
# OT / IoT devices run flat around the clock with a small day bump.
FLAT_CURVE = [60, 58, 57, 57, 58, 62, 70, 78, 84, 86, 88, 88, 86, 88, 88, 86, 82, 76, 72, 70, 68, 66, 64, 62]
SHIFT_CURVE = [70, 70, 68, 66, 66, 78, 92, 95, 95, 93, 92, 84, 88, 95, 95, 93, 90, 80, 88, 92, 92, 88, 80, 74]

SCALE = {"small": 0.25, "medium": 1.0, "large": 3.0, "xlarge": 8.0}


# --------------------------------------------------------------------------------------
# destination catalogue
# Each entry: key -> (fqdn, ip, country, internet-service-name or None)
# Internet-service names follow the FortiGuard "<Vendor>-<Service>" convention observed in
# real logs (Fortinet-FortiGuard, Microsoft-Office365.Published, Cloudflare-DNS, ...).
# --------------------------------------------------------------------------------------
DEST = {
    "resolver_cf":   ("one.one.one.one", "1.1.1.1", "Australia", "Cloudflare-DNS"),
    "resolver_q9":   ("dns.quad9.net", "9.9.9.9", "Switzerland", "Quad9-Quad9.Standard.DNS"),
    "ntp_pool":      ("2.ch.pool.ntp.org", "162.23.41.10", "Switzerland", "ntp.org-NTP"),
    "ntp_fortinet":  ("time.fortiguard.com", "173.243.141.10", "United States", "Fortinet-NTP"),
    "ftgd":          ("usdevquery.fortinet.net", "173.243.141.16", "United States", "Fortinet-FortiGuard"),
    "fctems":        ("ad-1000001-0001.forticlient-emsproxy.forticloud.com", "194.69.172.81", "United Kingdom", "Fortinet-FortiClient.EMS"),
    "m365":          ("outlook.office365.com", "52.98.148.226", "Ireland", "Microsoft-Office365.Published"),
    "teams":         ("teams.microsoft.com", "52.113.194.132", "Netherlands", "Microsoft-Teams.Published.Worldwide.Allow"),
    "msupdate":      ("fe3cr.delivery.mp.microsoft.com", "20.73.194.208", "Netherlands", "Microsoft-Windows.Update"),
    "msauth":        ("login.microsoftonline.com", "20.190.160.22", "Netherlands", "Microsoft-Azure.Front.Door"),
    "apple_cloud":   ("gateway.icloud.com", "17.253.144.10", "United States", "Apple-Apple.Services"),
    "apple_ota":     ("gdmf.apple.com", "17.253.11.201", "United States", "Apple-Software.Update"),
    "google":        ("www.google.com", "142.250.203.100", "United States", "Google-Google.Services"),
    "youtube":       ("rr3---sn-4g5e6nsz.googlevideo.com", "74.125.206.91", "United States", "Google-YouTube"),
    "cdn_fastly":    ("cdn.jsdelivr.net", "151.101.129.91", "United States", "Fastly-CDN"),
    "anthropic":     ("api.anthropic.com", "160.79.104.10", "United States", "Anthropic-Claude"),
    "axis_cloud":    ("device.axis.com", "13.53.106.44", "Sweden", None),
    "hik_cloud":     ("dev.hik-connect.com", "47.91.88.171", "Singapore", None),
    "dahua_cloud":   ("www.easy4ipcloud.com", "47.254.34.11", "Singapore", None),
    "reolink_cloud": ("apis.reolink.com", "52.221.14.9", "Singapore", None),
    "hp_cloud":      ("h20180.www2.hp.com", "15.73.152.20", "United States", None),
    "brother_cloud": ("update.brother.co.jp", "203.180.145.12", "Japan", None),
    "sonos_cloud":   ("msp.sonos.com", "54.72.163.11", "Ireland", None),
    "amazon_cloud":  ("device-metrics-us.amazon.com", "52.94.228.167", "United States", "Amazon-AWS.EC2"),
    "nest_cloud":    ("frontdoor.nest.com", "35.190.19.24", "United States", None),
    "tuya_cloud":    ("a2.tuyaeu.com", "52.28.147.31", "Germany", None),
    "tado_cloud":    ("my.tado.com", "35.156.201.14", "Germany", None),
    "signify_cloud": ("api.interact-lighting.com", "20.31.163.44", "Netherlands", None),
    "sma_cloud":     ("sunnyportal.com", "62.146.238.40", "Germany", None),
    "tesla_cloud":   ("ownership.tesla.com", "8.45.124.19", "United States", None),
    "viessmann":     ("api.viessmann.com", "3.68.211.24", "Germany", None),
    "yealink_prov":  ("prov.yealink.com", "47.88.216.51", "United States", None),
    "netflix":       ("ipv4-c001-zrh001.1.oca.nflxvideo.net", "45.57.40.10", "Switzerland", "Netflix-Netflix"),
    "spotify":       ("audio-fa.scdn.co", "35.186.224.25", "United States", "Spotify-Spotify"),
    "tiktok":        ("v19.tiktokcdn.com", "23.62.61.10", "United States", "TikTok-TikTok"),
    "facebook":      ("scontent-zrh1-1.xx.fbcdn.net", "157.240.253.63", "Ireland", "Facebook-Facebook"),
    "whatsapp":      ("g.whatsapp.net", "157.240.212.60", "Ireland", "Facebook-WhatsApp"),
    "ubnt_cloud":    ("device-airos.svc.ui.com", "3.33.152.10", "United States", None),
    "syno_cloud":    ("checkip.synology.com", "13.35.63.14", "United States", None),
    "generic_web":   ("www.example.ch", "185.199.108.153", "Switzerland", None),
    "sip_trunk":     ("sip.trunk-provider.example", "185.20.208.20", "Switzerland", None),
}

# Field order of the utm/voip log family as printed in the FortiOS log reference sample
# (LOG_ID 44032). It differs from the traffic-log order, hence the per-record override.
VOIP_ORDER = ["date", "time", "logid", "type", "subtype", "eventtype", "level", "vd", "eventtime",
              "tz", "session_id", "epoch", "event_id", "srcip", "src_port", "dstip", "dst_port",
              "proto", "src_int", "dst_int", "policy_id", "profile", "voip_proto", "kind", "action",
              "status", "duration", "dir", "call_id", "from", "to", "logsrc", "devid", "devname",
              "logver"]

# Roles the FortiGuard IoT/OT vulnerability service can have an opinion about. Workstations,
# servers and mobiles are FortiClient / EMS territory and get no IoT vulnerability count.
IOT_ROLES = {
    "camera", "plc", "hmi", "rtu", "drive", "robot", "sensor", "bms", "lighting", "access",
    "elevator", "energy", "evcharger", "medical", "printer", "voip", "consumer", "handheld",
    "gateway", "otswitch", "network",
}

# Threat destinations used by scenarios. RFC 5737 / TEST-NET and reserved-ish space is NOT
# used here because FortiAnalyzer geo-enriches on IP; these are plausible-looking hoster IPs.
THREAT = {
    "c2_primary":    ("cdn-node-7734.ddns-static.net", "45.147.230.114", "Russian Federation"),
    "c2_backup":     ("relay02.dyn-host.cc", "185.220.101.44", "Netherlands"),
    "c2_dga":        ("kqwlmxvpzr.top", "91.219.236.18", "Seychelles"),
    "exfil":         ("upload-eu.filedrop-share.io", "104.21.34.77", "United States"),
    "phish":         ("login-microsft-verify.secure-acc.top", "198.54.117.210", "United States"),
    "crypto":        ("eu.minerpool-xmr.net", "51.15.77.190", "France"),
    "scanner":       ("o061.scanner.modat.io", "85.217.149.61", "Canada"),
    "tor":           ("relay.torproject.example", "51.15.43.205", "France"),
}

# Behaviour -> list of flow templates.
#  dst        destination key
#  dport      destination port
#  proto      6=tcp 17=udp 1=icmp
#  service    FortiOS service name (or None -> derived)
#  app        app catalogue key or None
#  utm        which UTM logs this flow also produces
#  rate       (min,max) sessions per active hour at scale=1.0
#  bytes      (sent_lo, sent_hi, rcvd_lo, rcvd_hi)
FLOWS = {
    "dns":            [dict(dst="resolver_cf", dport=53, proto=17, service="DNS", app="DNS", utm=["dns"], rate=(6, 24), bytes=(80, 260, 120, 900))],
    "ping":           [dict(dst="resolver_cf", dport=0, proto=1, service="PING", app="Ping", utm=[], rate=(2, 8), bytes=(180, 720, 180, 720))],
    "ntp":            [dict(dst="ntp_pool", dport=123, proto=17, service="NTP", app="NTP", utm=[], rate=(1, 3), bytes=(90, 90, 90, 90))],
    "ot-ntp":         [dict(dst="ntp_pool", dport=123, proto=17, service="NTP", app="NTP", utm=[], rate=(2, 4), bytes=(90, 90, 90, 90))],
    "https-generic":  [dict(dst="generic_web", dport=443, proto=6, service="HTTPS", app="SSL_TLSv1.3", utm=["ssl"], rate=(4, 20), bytes=(1200, 60000, 4000, 400000))],
    "browsing":       [dict(dst="google", dport=443, proto=6, service="HTTPS", app="HTTP.BROWSER", utm=["ssl", "webfilter"], rate=(8, 40), bytes=(1500, 40000, 8000, 900000)),
                       dict(dst="cdn_fastly", dport=443, proto=6, service="HTTPS", app="SSL_TLSv1.3", utm=["ssl", "webfilter"], rate=(4, 22), bytes=(900, 20000, 10000, 1500000))],
    "m365":           [dict(dst="m365", dport=443, proto=6, service="HTTPS", app="Microsoft.365.Portal", utm=["ssl"], rate=(6, 26), bytes=(2000, 50000, 5000, 300000)),
                       dict(dst="teams", dport=443, proto=6, service="HTTPS", app="Microsoft.Teams", utm=["ssl"], rate=(4, 30), bytes=(3000, 200000, 3000, 400000)),
                       dict(dst="msauth", dport=443, proto=6, service="HTTPS", app="Microsoft.Authentication", utm=["ssl"], rate=(1, 6), bytes=(1200, 9000, 2000, 30000))],
    "apple-cloud":    [dict(dst="apple_cloud", dport=443, proto=6, service="HTTPS", app="Apple.Services", utm=["ssl"], rate=(3, 14), bytes=(1000, 30000, 2000, 200000))],
    "social":         [dict(dst="tiktok", dport=443, proto=6, service="HTTPS", app="TikTok", utm=["ssl", "webfilter"], rate=(2, 18), bytes=(2000, 40000, 200000, 9000000)),
                       dict(dst="facebook", dport=443, proto=6, service="HTTPS", app="Facebook", utm=["ssl", "webfilter"], rate=(1, 10), bytes=(1500, 30000, 20000, 900000))],
    "streaming":      [dict(dst="netflix", dport=443, proto=6, service="HTTPS", app="Netflix", utm=["ssl"], rate=(1, 6), bytes=(3000, 60000, 900000, 40000000)),
                       dict(dst="spotify", dport=443, proto=6, service="HTTPS", app="Spotify", utm=["ssl"], rate=(1, 8), bytes=(2000, 20000, 300000, 6000000)),
                       dict(dst="youtube", dport=443, proto=6, service="HTTPS", app="YouTube", utm=["ssl", "webfilter"], rate=(1, 7), bytes=(3000, 40000, 500000, 20000000))],
    "update":         [dict(dst="msupdate", dport=443, proto=6, service="HTTPS", app="Microsoft.Windows.Update", utm=["ssl"], rate=(0, 2), bytes=(2000, 20000, 100000, 60000000))],
    "firmware-update":[dict(dst="ftgd", dport=443, proto=6, service="HTTPS", app="SSL_TLSv1.3", utm=["ssl"], rate=(0, 1), bytes=(1500, 8000, 50000, 8000000))],
    "vendor-cloud":   [dict(dst="__vendor__", dport=443, proto=6, service="HTTPS", app="SSL_TLSv1.3", utm=["ssl"], rate=(2, 10), bytes=(600, 9000, 800, 40000))],
    "bms-cloud":      [dict(dst="__vendor__", dport=443, proto=6, service="HTTPS", app="SSL_TLSv1.2", utm=["ssl"], rate=(1, 5), bytes=(500, 6000, 700, 20000))],
    "mqtt":           [dict(dst="__vendor__", dport=8883, proto=6, service="tcp/8883", app="SSL_TLSv1.2", utm=["ssl"], rate=(2, 8), bytes=(300, 4000, 400, 9000))],
    "ocpp":           [dict(dst="__vendor__", dport=443, proto=6, service="HTTPS", app="WebSocket", utm=["ssl"], rate=(2, 8), bytes=(800, 12000, 900, 24000))],
    "onvif-discovery":[dict(dst="__lan_nvr__", dport=3702, proto=17, service="udp/3702", app=None, utm=[], rate=(1, 4), bytes=(400, 1600, 0, 0))],
    "rtsp-nvr":       [dict(dst="__lan_nvr__", dport=554, proto=6, service="tcp/554", app=None, utm=[], rate=(1, 3), bytes=(2000000, 90000000, 20000, 200000))],
    "sip-registrar":  [dict(dst="__lan_pbx__", dport=5060, proto=17, service="SIP", app=None, utm=[], rate=(2, 10), bytes=(600, 9000, 600, 9000))],
    "provisioning":   [dict(dst="yealink_prov", dport=443, proto=6, service="HTTPS", app="SSL_TLSv1.2", utm=["ssl"], rate=(0, 1), bytes=(600, 4000, 4000, 90000))],
    "print-spool":    [dict(dst="__lan_srv__", dport=9100, proto=6, service="tcp/9100", app=None, utm=[], rate=(0, 6), bytes=(20000, 4000000, 200, 2000))],
    "snmp":           [dict(dst="__lan_srv__", dport=161, proto=17, service="SNMP", app=None, utm=[], rate=(4, 12), bytes=(300, 3000, 400, 6000))],
    "smb-internal":   [dict(dst="__lan_srv__", dport=445, proto=6, service="SMB", app=None, utm=[], rate=(2, 20), bytes=(3000, 900000, 5000, 8000000))],
    "ad-auth":        [dict(dst="__lan_dc__", dport=389, proto=6, service="LDAP", app=None, utm=[], rate=(2, 14), bytes=(900, 12000, 1200, 30000)),
                       dict(dst="__lan_dc__", dport=88, proto=6, service="KERBEROS", app=None, utm=[], rate=(2, 12), bytes=(700, 9000, 900, 14000))],
    "ssh-admin":      [dict(dst="__lan_srv__", dport=22, proto=6, service="SSH", app=None, utm=[], rate=(0, 3), bytes=(3000, 90000, 4000, 200000))],
    "wms-backend":    [dict(dst="__lan_srv__", dport=443, proto=6, service="HTTPS", app="SSL_TLSv1.2", utm=["ssl"], rate=(6, 30), bytes=(700, 12000, 900, 40000))],
    "access-backend": [dict(dst="__lan_srv__", dport=443, proto=6, service="HTTPS", app="SSL_TLSv1.2", utm=["ssl"], rate=(2, 10), bytes=(600, 8000, 700, 20000))],
    "medical-backend":[dict(dst="__lan_srv__", dport=443, proto=6, service="HTTPS", app="SSL_TLSv1.2", utm=["ssl"], rate=(4, 18), bytes=(900, 30000, 1200, 90000))],
    "historian-write":[dict(dst="__lan_srv__", dport=1433, proto=6, service="MS-SQL", app=None, utm=[], rate=(4, 16), bytes=(2000, 60000, 900, 9000))],
    "hl7":            [dict(dst="__lan_srv__", dport=2575, proto=6, service="tcp/2575", app=None, utm=[], rate=(3, 16), bytes=(1200, 40000, 300, 2000))],
    "dicom":          [dict(dst="__lan_srv__", dport=104, proto=6, service="tcp/104", app=None, utm=[], rate=(0, 5), bytes=(500000, 60000000, 3000, 40000))],
    # -------- OT protocols (dst is another OT node) --------
    "modbus":         [dict(dst="__ot_peer__", dport=502, proto=6, service="tcp/502", app=None, utm=[], rate=(20, 60), bytes=(600, 9000, 600, 12000), otproto="Modbus")],
    "s7comm":         [dict(dst="__ot_peer__", dport=102, proto=6, service="tcp/102", app=None, utm=[], rate=(20, 60), bytes=(700, 12000, 700, 16000), otproto="S7COMM")],
    "enip":           [dict(dst="__ot_peer__", dport=44818, proto=6, service="tcp/44818", app=None, utm=[], rate=(18, 50), bytes=(600, 9000, 600, 11000), otproto="EtherNet/IP")],
    "dnp3-realport":  [dict(dst="__ot_peer__", dport=771, proto=6, service="RLDNP3", app=None, utm=[], rate=(8, 24), bytes=(400, 4000, 400, 6000), otproto="DNP3")],
    "profinet-peer":  [dict(dst="__ot_peer__", dport=34962, proto=17, service="udp/34962", app=None, utm=[], rate=(20, 60), bytes=(500, 7000, 500, 7000), otproto="PROFINET")],
    "bacnet":         [dict(dst="__ot_peer__", dport=47808, proto=17, service="udp/47808", app=None, utm=[], rate=(10, 30), bytes=(400, 5000, 400, 6000), otproto="BACnet")],
    "hmi-poll":       [dict(dst="__ot_peer__", dport=102, proto=6, service="tcp/102", app=None, utm=[], rate=(12, 40), bytes=(500, 8000, 600, 14000), otproto="S7COMM")],
    "syslog-out":     [dict(dst="__lan_srv__", dport=514, proto=17, service="SYSLOG", app=None, utm=[], rate=(2, 12), bytes=(300, 4000, 0, 0))],
}


# OT application-control naming. Only "RealPort.DNP3" is confirmed verbatim in Fortinet docs
# (application signature dissector for DNP3, appid 49890). The others follow the same
# convention but were NOT confirmed against the FortiGuard encyclopedia - appid is therefore
# deliberately omitted, which is a shape FortiOS itself produces (see traffic/local logs where
# app= appears without appid=). Verify names on fortiguard.com before quoting them to a customer.
OT_APP = {
    "Modbus": ("Modbus", "Operational.Technology", "elevated"),
    "S7COMM": ("S7comm", "Operational.Technology", "elevated"),
    "EtherNet/IP": ("EtherNet-IP", "Operational.Technology", "elevated"),
    "DNP3": ("RealPort.DNP3", "Operational.Technology", "elevated"),
    "PROFINET": ("PROFINET", "Operational.Technology", "elevated"),
    "BACnet": ("BACnet", "Operational.Technology", "medium"),
}


class Generator:
    def __init__(self, fleet, args):
        self.f = fleet
        self.a = args
        self.v = VERSIONS[args.version]
        self.cat = load("catalog.json")
        self.dev = load("devices.json")
        self.oui = load("oui.json")
        self.apps = {a[0]: a for a in self.cat["apps"]}
        self.webcat = {int(k): v for k, v in self.cat["webcat"].items()}
        self.clock = Clock(args.tz)
        self.rnd = random.Random(args.seed)
        random.seed(args.seed)
        self.tlog, self.elog, self.plog, self.xlog = [], [], [], []
        self.sessid = self.rnd.randint(1_000_000, 90_000_000)
        self.hosts = []
        self.by_role = {}
        self.start_dt = None
        self._materialize()
        self.rating = SecurityRating(self) if getattr(args, "rating", True) else None

    # ---------------------------------------------------------------- fleet -> hosts
    def _mac(self, vendor, seed):
        prefixes = self.oui.get(vendor)
        if not prefixes:
            raise SystemExit("no IEEE OUI on file for vendor %r - add it to data/oui.json" % vendor)
        r = random.Random(seed)
        return "%s:%02x:%02x:%02x" % (r.choice(prefixes), r.randint(0, 255), r.randint(0, 255), r.randint(0, 255))

    def _materialize(self):
        models = self.dev["models"]
        for z in self.f["zones"]:
            base = z["subnet"].rsplit(".", 1)[0]
            nexthost = z.get("first_host", 10)
            for grp in z["hosts"]:
                m = models[grp["model"]]
                for i in range(grp["count"]):
                    seed = "%s|%s|%d" % (z["name"], grp["model"], i)
                    devtype = m["devtype"]
                    if self.a.devtype_mode == "verified" and m.get("tier") == "extended":
                        devtype = m.get("fallback_devtype", "Unknown")
                    name = grp.get("name", grp["model"]).replace("_", "-").upper()
                    h = {
                        "id": "%s-%02d" % (name, i + 1),
                        "hostname": "%s-%02d" % (name, i + 1),
                        "ip": "%s.%d" % (base, nexthost),
                        "mac": self._mac(m["vendor"], seed),
                        "zone": z,
                        "model": grp["model"],
                        "devtype": devtype,
                        "osname": m["osname"],
                        "srcfamily": m["srcfamily"],
                        "srchwvendor": m["vendor"].split(",")[0].strip(),
                        "srchwversion": m["srchwversion"],
                        "srcswversion": m["srcswversion"],
                        "purdue": m["purdue"],
                        "role": m["role"],
                        "behaviours": list(m["behaviours"]),
                        "vendor_key": m["vendor"],
                        "curve": z.get("curve", "office"),
                        "user": None,
                        # FortiGuard IoT/OT vulnerability count for this asset. Decided once so
                        # the 0100020150 event, the FortiguardIotVulnerability rating check and
                        # assets.csv all agree on which devices are vulnerable.
                        "vulncnt": 0,
                    }
                    if m["role"] in IOT_ROLES:
                        r_ = random.Random(seed + "|vuln")
                        if r_.random() < self.a.vuln_ratio:
                            h["vulncnt"] = r_.choice([1, 1, 2, 2, 3, 4, 5, 6, 8, 11, 14, 19, 27, 40])
                    nexthost += 1
                    self.hosts.append(h)
                    self.by_role.setdefault(h["role"], []).append(h)
        # assign users to workstations / laptops / mobiles
        users = self.f.get("users", [])
        idx = 0
        for h in self.hosts:
            if h["role"] in ("workstation", "mobile") and users:
                h["user"] = users[idx % len(users)]
                idx += 1

    # ---------------------------------------------------------------- infrastructure
    def _anchor(self, key, host):
        """Resolve pseudo-destinations (__lan_srv__, __ot_peer__, ...) to a real host."""
        pools = {
            "__lan_srv__": ("server", None), "__lan_dc__": ("server", None),
            "__lan_nvr__": ("server", None), "__lan_pbx__": ("server", None),
            "__ot_peer__": ("plc", ("hmi", "rtu", "otswitch")),
        }
        if key not in pools:
            return None
        primary, alt = pools[key]
        pool = list(self.by_role.get(primary, []))
        if alt:
            for r in alt:
                pool += self.by_role.get(r, [])
        pool = [p for p in pool if p["id"] != host["id"]]
        if not pool:
            return None
        return self.rnd.choice(pool)

    def _vendor_dest(self, host):
        m = {
            "Axis Communications AB": "axis_cloud", "Hangzhou Hikvision": "hik_cloud",
            "Zhejiang Dahua Technology": "dahua_cloud", "Reolink": "reolink_cloud",
            "Hewlett Packard": "hp_cloud", "Brother industries": "brother_cloud",
            "Sonos": "sonos_cloud", "Amazon Technologies": "amazon_cloud",
            "Nest Labs": "nest_cloud", "Tuya Smart": "tuya_cloud", "tado GmbH": "tado_cloud",
            "Signify B.V.": "signify_cloud", "SMA Solar Technology AG": "sma_cloud",
            "Tesla,Inc.": "tesla_cloud", "Viessmann Elektronik": "viessmann",
            "YEALINK": "yealink_prov", "Ubiquiti Inc": "ubnt_cloud",
            "Synology Incorporated": "syno_cloud", "Apple, Inc.": "apple_cloud",
            "Espressif Inc.": "amazon_cloud",
        }
        return m.get(host["vendor_key"], "generic_web")

    # ---------------------------------------------------------------- record scaffolds
    def _base(self, dt, logtype, subtype, logid, level):
        r = self.clock.fields(dt)
        r.update({
            "logid": logid, "type": logtype, "subtype": subtype, "level": level,
            "vd": self.a.vdom, "devid": self.a.devid, "devname": self.a.devname,
            "logver": self.v["logver"],
        })
        return r

    def _asset_fields(self, h):
        """The fields FortiAnalyzer's Asset Identity Center and IoT dashboard consume."""
        d = {
            "srcmac": h["mac"], "mastersrcmac": h["mac"],
            "devtype": h["devtype"], "osname": h["osname"],
            "srcfamily": h["srcfamily"], "srchwvendor": h["srchwvendor"],
            "srchwversion": h["srchwversion"], "srcswversion": h["srcswversion"],
        }
        if self.v["has_srcserver"]:
            d["srcserver"] = 0
        return d

    def _nextsess(self):
        self.sessid += self.rnd.randint(1, 40)
        return self.sessid

    # ---------------------------------------------------------------- session emitter
    def session(self, dt, host, flow, override=None):
        """Emit one traffic/forward log plus whatever UTM logs the flow declares."""
        o = override or {}
        z = host["zone"]
        dstkey = flow["dst"]
        peer = None
        if dstkey.startswith("__"):
            if dstkey == "__vendor__":
                fq, dip, country, isvc = DEST[self._vendor_dest(host)]
            else:
                peer = self._anchor(dstkey, host)
                if peer is None:
                    return
                fq, dip, country, isvc = peer["hostname"] + "." + self.f["domain"], peer["ip"], "Reserved", None
        else:
            fq, dip, country, isvc = DEST[dstkey]
        fq = o.get("dstname", fq); dip = o.get("dstip", dip)
        country = o.get("dstcountry", country); isvc = o.get("dstinetsvc", isvc)

        internal = peer is not None
        dstintf = peer["zone"]["name"] if internal else self.f["wan"]["intf"]
        dstrole = peer["zone"]["role"] if internal else "wan"
        pol = z["policy_internal"] if internal else z["policy_wan"]
        sid = self._nextsess()
        sb = self.rnd.randint(flow["bytes"][0], max(flow["bytes"][0], flow["bytes"][1]))
        rb = self.rnd.randint(flow["bytes"][2], max(flow["bytes"][2], flow["bytes"][3]))
        dur = self.rnd.randint(1, 600)
        proto = flow["proto"]
        sport = self.rnd.randint(1024, 65500)

        rec = self._base(dt, "traffic", "forward", o.get("logid", "0000000013"), o.get("level", "notice"))
        rec.update({
            "srcip": host["ip"], "srcname": host["hostname"], "srcport": sport,
            "srcintf": z["name"], "srcintfrole": z["role"], "srccountry": "Reserved",
            "srcuuid": mkuuid("intf" + z["name"]),
            "dstip": dip, "dstname": fq, "dstport": flow["dport"],
            "dstintf": dstintf, "dstintfrole": dstrole, "dstcountry": country,
            "sessionid": sid, "proto": proto,
            "action": o.get("action", "close" if not flow.get("otproto")
                             else self.rnd.choice(["close", "close", "close", "accept"])),
            "policyid": pol["id"], "policyname": pol["name"], "policytype": "policy",
            "poluuid": mkuuid("pol%d" % pol["id"]),
            "service": flow["service"] or ("tcp/%d" % flow["dport"]),
            "duration": dur, "sentbyte": sb, "rcvdbyte": rb,
            "sentpkt": max(1, sb // 900), "rcvdpkt": max(1, rb // 1200),
        })
        rec.update(self._asset_fields(host))
        if proto == 1:
            rec["identifier"] = self.rnd.randint(1, 4000)
            rec.pop("srcport", None)
            rec.pop("dstport", None)
        if not internal:
            rec.update({"trandisp": "snat", "transip": self.f["wan"]["ip"], "transport": sport,
                        "dstcity": "Undefined", "dstregion": "Undefined", "dstreputation": self.rnd.choice([4, 5, 5, 5])})
            if isvc and self.v["has_inetsvc"]:
                rec["dstinetsvc"] = isvc
                rec["service"] = isvc
            if self.f["wan"].get("sdwan"):
                rec.update({"vwlid": 1, "vwlname": self.f["wan"]["sdwan"],
                            "vwlquality": "Seq_num(1 %s underlay), alive, selected" % self.f["wan"]["intf"]})
        else:
            rec["trandisp"] = "noop"
            rec.update({"dstdevtype": peer["devtype"], "dstosname": peer["osname"],
                        "dstfamily": peer["srcfamily"], "dsthwvendor": peer["srchwvendor"]})
        if host.get("user"):
            rec["user"] = host["user"]

        appname = o.get("app", flow.get("app"))
        otp = flow.get("otproto")
        if otp and self.a.ot_appctrl:
            an, ac, ar = OT_APP[otp]
            rec.update({"app": an, "appcat": ac, "apprisk": ar, "applist": self.f["profiles"]["applist"],
                        "countapp": 1, "utmaction": "allow"})
        elif appname and appname in self.apps:
            a = self.apps[appname]
            rec.update({"app": a[0], "appid": a[1], "appcat": a[2], "apprisk": a[3],
                        "applist": self.f["profiles"]["applist"], "countapp": 1, "utmaction": "allow"})
        else:
            rec["appcat"] = "unscanned"
        self.tlog.append(rec)

        # Long-lived sessions emit periodic updates (logid 0000000020) carrying delta counters.
        if dur > 240 and self.rnd.random() < 0.25:
            upd = dict(rec)
            upd["logid"] = "0000000020"
            upd["action"] = "accept"
            upd.pop("msg", None)
            sd = max(1, sb // self.rnd.randint(3, 20))
            rd = max(1, rb // self.rnd.randint(3, 20))
            upd.update({"durationdelta": 120, "sentdelta": sd, "rcvddelta": rd,
                        "sentpktdelta": max(1, sd // 900), "rcvdpktdelta": max(1, rd // 1200)})
            upd.update(self.clock.fields(dt + timedelta(seconds=self.rnd.randint(30, 200))))
            self.tlog.append(upd)

        for u in flow.get("utm", []):
            if u == "dns":
                self.dns_pair(dt, host, z, sid, fq if not internal else "internal.local")
            elif u == "ssl" and self.rnd.random() < 0.7:
                self.ssl_logs(dt, host, z, sid, fq, dip, country, pol)
            elif u == "webfilter" and self.rnd.random() < 0.5:
                self.webfilter(dt, host, z, sid, fq, dip, country, pol, sb)
        if appname and appname in self.apps and self.rnd.random() < 0.6:
            self.appctrl(dt, host, z, sid, fq, dip, country, pol, self.apps[appname], proto, flow)

    # ---------------------------------------------------------------- UTM builders
    def appctrl(self, dt, host, z, sid, fq, dip, country, pol, app, proto, flow, action="pass"):
        r = self._base(dt, "utm", "app-ctrl", "1059028704", "information" if action == "pass" else "warning")
        r.update({
            "eventtype": "signature", "appid": app[1], "app": app[0], "appcat": app[2],
            "apprisk": app[3], "applist": self.f["profiles"]["applist"], "action": action,
            "srcip": host["ip"], "srcport": self.rnd.randint(1024, 65500), "srcintf": z["name"],
            "srcintfrole": z["role"], "srccountry": "Reserved",
            "dstip": dip, "dstintf": self.f["wan"]["intf"],
            "dstintfrole": "wan", "dstcountry": country,
            "proto": proto, "service": flow["service"] or ("tcp/%d" % flow["dport"]),
            "sessionid": sid, "policyid": pol["id"], "policytype": "policy",
            "poluuid": mkuuid("pol%d" % pol["id"]), "direction": "outgoing",
            "hostname": fq, "incidentserialno": self.rnd.randint(10_000_000, 999_999_999),
            "msg": "%s: %s," % (app[2], app[0]),
        })
        if proto == 1:
            r.update({"icmptype": "0x08", "icmpcode": "0x00",
                      "icmpid": "0x%04x" % self.rnd.randint(1, 65535)})
            r.pop("srcport", None)
        else:
            r["dstport"] = flow["dport"]
        if action != "pass":
            r["appact"] = "block"
        self.tlog.append(r)

    def dns_pair(self, dt, host, z, sid, qname, blocked=False, cat=52, nxdomain=False):
        res = DEST["resolver_cf"]
        common = {
            "srcip": host["ip"], "srcport": self.rnd.randint(1024, 65500), "srcintf": z["name"],
            "srcintfrole": z["role"], "srccountry": "Reserved",
            "dstip": res[1], "dstport": 53, "dstintf": self.f["wan"]["intf"], "dstintfrole": "wan",
            "dstcountry": res[2], "proto": 17, "sessionid": sid,
            "policyid": self.f["zones"][0]["policy_wan"]["id"], "policytype": "policy",
            "poluuid": mkuuid("pol%d" % self.f["zones"][0]["policy_wan"]["id"]),
            "profile": self.f["profiles"]["dnsfilter"],
            "qname": qname, "qtype": "A", "qtypeval": 1, "qclass": "IN",
            "xid": self.rnd.randint(1, 65535),
        }
        q = self._base(dt, "utm", "dns", "1500054000", "information")
        q.update(common); q["eventtype"] = "dns-query"
        self.tlog.append(q)
        logid = self.v["dns_resp_nx"] if nxdomain else self.v["dns_resp_pass"]
        a = self._base(dt, "utm", "dns", logid, "notice")
        a.update(common)
        a.update({"eventtype": "dns-response", "action": "block" if blocked else "pass",
                  "cat": cat, "catdesc": self.webcat.get(cat, "Unknown")})
        if nxdomain:
            a.update({"msg": "Domain is non-existent", "rcode": 3})
        else:
            a.update({"msg": "Domain was blocked by DNS filter" if blocked else "Domain is monitored",
                      "ipaddr": "%d.%d.%d.%d" % tuple(self.rnd.randint(1, 254) for _ in range(4))})
        self.tlog.append(a)

    def ssl_logs(self, dt, host, z, sid, sni, dip, country, pol):
        common = {
            "srcip": host["ip"], "srcport": self.rnd.randint(1024, 65500), "srcintf": z["name"],
            "srcintfrole": z["role"], "srccountry": "Reserved", "srcuuid": mkuuid("intf" + z["name"]),
            "dstip": dip, "dstport": 443, "dstintf": self.f["wan"]["intf"], "dstintfrole": "wan",
            "dstcountry": country, "dstuuid": mkuuid("wan"), "proto": 6, "service": "SSL",
            "sessionid": sid, "policyid": pol["id"], "policytype": "policy",
            "poluuid": mkuuid("pol%d" % pol["id"]), "profile": self.f["profiles"]["sslssh"],
            "hostname": sni, "sni": sni, "action": "info",
        }
        if self.v["has_profilegroup"]:
            common["profilegroup"] = self.f["profiles"]["group"]
        h = self._base(dt, "utm", "ssl", "1704062220", "information")
        h.update(common)
        h.update({"eventtype": "ssl-handshake", "eventsubtype": "handshake-done",
                  "tlsver": self.rnd.choice(["tls1.3", "tls1.3", "tls1.2"]),
                  "cipher": "0x1301", "authalgo": "rsa", "kxproto": "ecdhe", "kxcurve": "x25519",
                  "handshake": "full", "mitm": self.rnd.choice(["yes", "no"])})
        self.tlog.append(h)
        if self.rnd.random() < 0.35:
            c = self._base(dt, "utm", "ssl", "1703062200", "information")
            c.update(common)
            c.update({"eventtype": "ssl-server-cert-info", "eventsubtype": "server-cert-info",
                      "certhash": hashlib.sha1(sni.encode()).hexdigest(), "cn": sni.split(".", 1)[-1],
                      "issuer": "DigiCert Global G2 TLS RSA SHA256 2020 CA1", "keyalgo": "rsa",
                      "keysize": 2048, "sn": hashlib.md5(sni.encode()).hexdigest()[:6],
                      "notbefore": "2025-01-14T00:00:00Z", "notafter": "2027-02-13T23:59:59Z"})
            self.tlog.append(c)

    def webfilter(self, dt, host, z, sid, fq, dip, country, pol, sentbyte,
                  blocked=False, cat=52, url=None):
        logid = "0316013056" if blocked else "0317013312"
        r = self._base(dt, "utm", "webfilter", logid, "warning" if blocked else "notice")
        r.update({
            "eventtype": "ftgd_blk" if blocked else "ftgd_allow",
            "action": "blocked" if blocked else "passthrough",
            "srcip": host["ip"], "srcport": self.rnd.randint(1024, 65500), "srcintf": z["name"],
            "srcintfrole": z["role"], "srccountry": "Reserved", "srcuuid": mkuuid("intf" + z["name"]),
            "dstip": dip, "dstport": 443, "dstintf": self.f["wan"]["intf"], "dstintfrole": "wan",
            "dstcountry": country, "dstuuid": mkuuid("wan"), "proto": 6, "service": "HTTPS",
            "sessionid": sid, "policyid": pol["id"], "policytype": "policy",
            "poluuid": mkuuid("pol%d" % pol["id"]), "profile": self.f["profiles"]["webfilter"],
            "hostname": fq, "url": url or ("https://%s/" % fq), "reqtype": "direct",
            "direction": "outgoing", "ratemethod": "domain",
            "sentbyte": sentbyte, "rcvdbyte": 0,
            "cat": cat, "catdesc": self.webcat.get(cat, "Unknown"),
            "msg": "URL belongs to a denied category in policy" if blocked
                   else "URL belongs to an allowed category in policy",
        })
        if self.v["has_profilegroup"]:
            r["profilegroup"] = self.f["profiles"]["group"]
        if blocked:
            r.update({"method": "domain", "crscore": 30, "craction": 4194304, "crlevel": "high"})
        if host.get("user"):
            r["user"] = host["user"]
        self.tlog.append(r)

    # ---------------------------------------------------------------- threat builders
    def ips(self, dt, host, z, dst, attack, attackid, severity, action="dropped",
            proto=6, dport=443, service="HTTPS", url=None, dstzone=None):
        crmap = {"critical": (50, 4096, "critical"), "high": (30, 4194304, "high"),
                 "medium": (20, 2097152, "medium"), "info": (5, 262144, "low")}
        cs, ca, cl = crmap.get(severity, crmap["medium"])
        r = self._base(dt, "utm", "ips", "0419016384", "alert")
        r.update({
            "eventtype": "signature", "severity": severity,
            "srcip": host["ip"], "srccountry": "Reserved", "srcport": self.rnd.randint(1024, 65500),
            "srcintf": z["name"], "srcintfrole": z["role"],
            "dstip": dst[1], "dstport": dport,
            "dstintf": dstzone["name"] if dstzone else self.f["wan"]["intf"],
            "dstintfrole": dstzone["role"] if dstzone else "wan",
            "dstcountry": dst[2] if len(dst) > 2 else "United States",
            "sessionid": self._nextsess(), "action": action, "proto": proto, "service": service,
            "policyid": z["policy_wan"]["id"], "attack": attack, "attackid": attackid,
            "hostname": dst[0], "url": url or "/", "direction": "outgoing",
            "profile": self.f["profiles"]["ips"],
            "ref": "http://www.fortinet.com/ids/VID%d" % attackid,
            "incidentserialno": self.rnd.randint(10_000_000, 999_999_999),
            "msg": "%s: %s," % ("applications3", attack),
            "crscore": cs, "craction": ca, "crlevel": cl,
        })
        if host.get("user"):
            r["user"] = host["user"]
        self.tlog.append(r)

    def anomaly(self, dt, host, z, attack, attackid, count):
        r = self._base(dt, "utm", "anomaly", "0720018433", "alert")
        r.update({
            "eventtype": "anomaly", "severity": "critical",
            "srcip": host["ip"], "srccountry": "Reserved",
            "dstip": self.f["wan"]["ip"], "srcintf": z["name"], "srcintfrole": z["role"],
            "sessionid": 0, "action": "clear_session", "proto": 6, "service": "tcp/443",
            "count": count, "attack": attack, "attackid": attackid,
            "policyid": 1, "policytype": "DoS-policy",
            "ref": "http://www.fortinet.com/ids/VID%d" % attackid,
            "msg": "anomaly: %s, %d > threshold 500" % (attack, count),
            "crscore": 50, "craction": 4096, "crlevel": "critical",
        })
        self.tlog.append(r)

    def virus(self, dt, host, z, dst, virusname, filename, url, action="blocked"):
        r = self._base(dt, "utm", "virus", "0211008192", "warning")
        r.update({
            "eventtype": "infected", "msg": "File is infected.", "action": action,
            "service": "HTTP", "sessionid": self._nextsess(),
            "srcip": host["ip"], "srcport": self.rnd.randint(1024, 65500),
            "dstip": dst[1], "dstport": 80,
            "srcintf": z["name"], "srcintfrole": z["role"],
            "dstintf": self.f["wan"]["intf"], "dstintfrole": "wan",
            "policyid": z["policy_wan"]["id"], "proto": 6, "direction": "incoming",
            "filename": filename, "quarskip": "File-was-not-quarantined.",
            "virus": virusname, "dtype": "Virus",
            "ref": "http://www.fortinet.com/ve?vn=%s" % virusname,
            "virusid": self.rnd.randint(1000, 99999), "url": url,
            "profile": self.f["profiles"]["av"], "agent": "curl/8.5.0",
            "analyticscksum": hashlib.sha256((filename + virusname).encode()).hexdigest(),
            "analyticssubmit": "false",
            "crscore": 50, "craction": 2, "crlevel": "critical",
        })
        self.tlog.append(r)

    def dlp(self, dt, host, z, dst, filename, filetype, filesize, ftype="file-type"):
        r = self._base(dt, "utm", "dlp", "0954024576", "warning")
        r.update({
            "eventtype": "dlp", "filteridx": 1, "dlpextra": self.f["profiles"]["dlp"],
            "filtertype": ftype, "filtercat": "file", "severity": "medium",
            "policyid": z["policy_wan"]["id"], "policytype": "policy",
            "sessionid": self._nextsess(), "epoch": self.rnd.randint(100000, 999999999), "eventid": 0,
            "srcip": host["ip"], "srcport": self.rnd.randint(1024, 65500), "srccountry": "Reserved",
            "srcintf": z["name"], "srcintfrole": z["role"],
            "dstip": dst[1], "dstport": 443, "dstcountry": dst[2],
            "dstintf": self.f["wan"]["intf"], "dstintfrole": "wan",
            "proto": 6, "service": "HTTPS", "filetype": filetype, "direction": "outgoing",
            "action": "block", "hostname": dst[0], "url": "https://%s/upload" % dst[0],
            "httpmethod": "POST", "filename": filename, "filesize": filesize,
            "profile": self.f["profiles"]["dlp"],
        })
        if host.get("user"):
            r["user"] = host["user"]
        self.tlog.append(r)

    # ---------------------------------------------------------------- event builders
    def ev_iot_vuln(self, dt, host, vulncnt=None):
        """FortiGuard device vulnerability lookup. Carries only a COUNT - the CVE list itself
        never appears in any log record (see references/assets-and-iot.md)."""
        if vulncnt is not None:
            host["vulncnt"] = max(host.get("vulncnt", 0), vulncnt)
        vulncnt = host.get("vulncnt", 0)
        r = self._base(dt, "event", "system", "0100020150", "notice")
        r.update({
            "logdesc": "Device vulnerability lookup on FortiGuard",
            "ip": host["ip"], "mac": host["mac"], "model": host["srchwversion"],
            "product": host["osname"], "vendor": host["srchwvendor"],
            "versionmin": host["srcswversion"], "versionmax": "N/A",
            "vulncnt": vulncnt, "vulnresult": "success",
        })
        self.elog.append(r)

    def ev_dhcp_ack(self, dt, host):
        r = self._base(dt, "event", "system", "0100026001", "information")
        r.update({
            "logdesc": "DHCP Ack log", "msg": "DHCP server sends a DHCPACK",
            "dhcp_msg": "Ack", "interface": host["zone"]["name"], "ip": host["ip"],
            "mac": host["mac"].upper(), "lease": 604800, "hostname": host["hostname"],
        })
        self.elog.append(r)

    def ev_admin_login(self, dt, user, srcip, ok=True):
        r = self._base(dt, "event", "system", "0100032001" if ok else "0100032002",
                       "information" if ok else "alert")
        r.update({
            "logdesc": "Admin login successful" if ok else "Admin login failed",
            "sn": str(int(dt.timestamp())) if ok else "0", "user": user,
            "ui": "https(%s)" % srcip, "method": "https", "srcip": srcip,
            "dstip": self.f["mgmt_ip"], "action": "login",
            "status": "success" if ok else "failed",
            "reason": "none" if ok else "name_invalid",
            "msg": "Administrator %s %s from https(%s)" % (
                user, "logged in successfully" if ok else "login failed", srcip),
        })
        if ok:
            r["profile"] = "super_admin"
        self.elog.append(r)

    def ev_user_auth(self, dt, host, ok=True):
        r = self._base(dt, "event", "user", "0102043008", "notice" if ok else "warning")
        r.update({
            "logdesc": "Authentication success" if ok else "Authentication failure",
            "srcip": host["ip"], "dstip": self.f["mgmt_ip"],
            "policyid": host["zone"]["policy_wan"]["id"], "interface": host["zone"]["name"],
            "user": host.get("user") or "unknown", "group": self.f.get("authgroup", "N/A"),
            "authproto": "HTTPS(%s)" % host["ip"], "action": "authentication",
            "status": "success" if ok else "failed", "reason": "N/A",
            "msg": "User %s %s in authentication" % (host.get("user") or "unknown",
                                                     "succeeded" if ok else "failed"),
        })
        self.elog.append(r)

    def ev_sslvpn(self, dt, user, remip, country, action="tunnel-up", reason="tunnel established"):
        logid = {"tunnel-up": "0101039947", "ssl-login-fail": "0101039426",
                 "tunnel-down": "0101039426"}[action]
        r = self._base(dt, "event", "vpn", logid,
                       "information" if action == "tunnel-up" else "alert")
        r.update({
            "logdesc": "SSL VPN tunnel up" if action == "tunnel-up" else "SSL VPN login fail",
            "action": action, "tunneltype": "ssl-tunnel",
            "tunnelid": self.rnd.randint(100000000, 999999999),
            "remip": remip, "user": user, "group": self.f.get("authgroup", "N/A"),
            "dst_host": "N/A", "reason": reason, "srccountry": country,
            "msg": "SSL tunnel established" if action == "tunnel-up"
                   else "SSL user failed to logged in",
        })
        if action == "tunnel-up":
            r["tunnelip"] = self.f.get("vpn_pool", "10.212.134.%d") % self.rnd.randint(2, 250)
        self.elog.append(r)

    def ev_sdwan(self, dt):
        w = self.f["wan"]
        r = self._base(dt, "event", "sdwan", "0113022925", "information")
        r.update({
            "logdesc": "SDWAN SLA information", "eventtype": "SLA",
            "msg": "Health Check SLA status.", "healthcheck": "DNS_Cloudflare",
            "interface": w["intf"], "status": "up", "slamap": "0x1",
            "latency": "%.3f" % self.rnd.uniform(1.0, 22.0),
            "jitter": "%.3f" % self.rnd.uniform(0.05, 4.5),
            "packetloss": "%.3f" % (self.rnd.choice([0, 0, 0, 0.2, 1.4])),
            "mosvalue": "%.3f" % self.rnd.uniform(4.1, 4.4), "moscodec": "g711",
            "inbandwidthused": "%.2fMbps" % self.rnd.uniform(1, 400),
            "outbandwidthused": "%.2fMbps" % self.rnd.uniform(1, 120),
            "bibandwidthused": "%.2fMbps" % self.rnd.uniform(2, 500),
            "inbandwidthavailable": "9.99Gbps", "outbandwidthavailable": "10.00Gbps",
            "bibandwidthavailable": "19.99Gbps",
        })
        self.elog.append(r)

    def ev_perfstat(self, dt, uptime):
        r = self._base(dt, "event", "system", "0100040704", "notice")
        cpu = self.rnd.randint(2, 34); mem = self.rnd.randint(38, 72)
        sess = self.rnd.randint(400, 9000)
        r.update({
            "logdesc": "System performance statistics", "action": "perf-stats",
            "cpu": cpu, "mem": mem, "disk": self.rnd.randint(8, 40),
            "totalsession": sess, "setuprate": self.rnd.randint(4, 320),
            "sysuptime": uptime, "freediskstorage": self.rnd.randint(12000, 40000),
            "disklograte": self.rnd.randint(5, 120), "fazlograte": self.rnd.randint(5, 120),
            "bandwidth": "%d/%d" % (self.rnd.randint(200, 9000), self.rnd.randint(200, 9000)),
            "waninfo": "name=%s,bytes=%d/%d,packets=%d/%d;" % (
                self.f["wan"]["intf"], self.rnd.randint(10**9, 10**11), self.rnd.randint(10**9, 10**12),
                self.rnd.randint(10**6, 10**8), self.rnd.randint(10**6, 10**9)),
            "msg": "Performance statistics: average CPU: %d, memory: %d, concurrent sessions: %d, setup-rate: %d"
                   % (cpu, mem, sess, self.rnd.randint(4, 320)),
        })
        self.elog.append(r)

    def ev_cfg_change(self, dt, user, path, obj):
        r = self._base(dt, "event", "system", "0100044547", "information")
        r.update({
            "logdesc": "Object attribute configured", "action": "Edit",
            "cfgpath": path, "cfgobj": obj, "cfgtid": self.rnd.randint(1000000, 999999999),
            "msg": "Edit %s %s" % (path, obj), "ui": "https(10.0.0.5)", "user": user,
            "uuid": mkuuid(path + obj),
        })
        self.elog.append(r)

    # ---------------------------------------------------------------- VoIP (plog)
    def voip_call(self, dt, host, external=False):
        """utm/voip SIP call log, logid 0814044032 [doc 7.4.3 log reference] [lab 8.0.0].
        Note the field names: this log family uses src_port / dst_port / src_int / dst_int /
        policy_id / session_id, not the traffic-log spellings."""
        z = host["zone"]
        peer = None if external else self._anchor("__lan_pbx__", host)
        if peer is None:
            fq, dip, country, _ = DEST["sip_trunk"]
            dst_int, pol = self.f["wan"]["intf"], z["policy_wan"]
        else:
            dip = peer["ip"]
            dst_int, pol = peer["zone"]["name"], z["policy_internal"]
        r = self._base(dt, "utm", "voip", "0814044032", "information")
        ext = 100 + (sum(ord(c) for c in host["id"]) % 800)
        r.update({
            "eventtype": "voip", "session_id": self._nextsess(), "epoch": 0, "event_id": 0,
            "srcip": host["ip"], "src_port": self.rnd.randint(1024, 65500),
            "dstip": dip, "dst_port": 5060, "proto": 17,
            "src_int": z["name"], "dst_int": dst_int, "policy_id": pol["id"],
            "profile": self.f["profiles"].get("voip", "default"),
            "voip_proto": "sip", "kind": "call", "action": "permit", "status": "start",
            "duration": 0, "dir": "session_origin",
            "call_id": "%06d@%s" % (self.rnd.randint(100000, 999999), dip),
            "from": "sip:%d@%s" % (ext, self.f["domain"]),
            "to": "sip:%s@%s" % ("%d" % self.rnd.randint(100, 899) if peer else
                                 "+41%09d" % self.rnd.randint(310000000, 799999999), dip),
        })
        if self.v["has_logsrc"]:
            r["logsrc"] = "voipd"
        r["_order"] = VOIP_ORDER
        self.plog.append(r)

    # ---------------------------------------------------------------- scenarios
    def scenario_shadow_iot(self, day):
        """An unmanaged consumer IoT device appears on a corporate VLAN and phones home."""
        pool = [h for h in self.hosts if h["role"] == "consumer"] or self.hosts
        h = self.rnd.choice(pool)
        t = day.replace(hour=9, minute=self.rnd.randint(0, 59), second=self.rnd.randint(0, 59))
        self.ev_dhcp_ack(t, h)
        self.ev_iot_vuln(t + timedelta(seconds=8), h, max(h["vulncnt"], self.rnd.randint(3, 40)))
        for i in range(self.rnd.randint(6, 20)):
            self.session(t + timedelta(minutes=i * 7), h, FLOWS["vendor-cloud"][0])
        self.dns_pair(t + timedelta(minutes=2), h, h["zone"], self._nextsess(),
                      "telemetry.iot-vendor-cloud.cn", blocked=False, cat=52)

    def scenario_camera_c2(self, day):
        """A compromised IP camera beacons to C2, then tries to exfiltrate."""
        cams = [h for h in self.hosts if h["role"] == "camera"]
        if not cams:
            return
        h = self.rnd.choice(cams)
        t = day.replace(hour=self.rnd.randint(1, 4), minute=self.rnd.randint(0, 59))
        self.ev_iot_vuln(t, h, max(h["vulncnt"], self.rnd.randint(12, 60)))
        c2 = THREAT["c2_primary"]
        for i in range(self.rnd.randint(20, 45)):
            tt = t + timedelta(minutes=i * 12)
            self.dns_pair(tt, h, h["zone"], self._nextsess(), c2[0], blocked=True, cat=26)
            self.session(tt + timedelta(seconds=3), h,
                         dict(dst="generic_web", dport=8443, proto=6, service="tcp/8443",
                              app=None, utm=[], rate=(1, 1), bytes=(900, 4000, 400, 2000)),
                         override=dict(dstname=c2[0], dstip=c2[1], dstcountry=c2[2],
                                       action="close", dstinetsvc=None))
            if i % 7 == 0:
                self.ips(tt + timedelta(seconds=5), h, h["zone"], c2,
                         "Adobe.Flash.newfunction.Handling.Code.Execution", 23305, "critical",
                         action="dropped", dport=8443, service="tcp/8443")
        ex = THREAT["exfil"]
        self.dlp(t + timedelta(hours=5), h, h["zone"], ex, "camera_archive_2026.zip", "zip", 84_221_440)

    def scenario_ransomware(self, day):
        """Phish -> download -> lateral SMB -> mass exfil, over one working day."""
        ws = [h for h in self.hosts if h["role"] == "workstation"]
        if not ws:
            return
        pat = self.rnd.choice(ws)
        t0 = day.replace(hour=9, minute=self.rnd.randint(5, 50))
        ph = THREAT["phish"]
        self.dns_pair(t0, pat, pat["zone"], self._nextsess(), ph[0], blocked=False, cat=61)
        self.webfilter(t0 + timedelta(seconds=4), pat, pat["zone"], self._nextsess(),
                       ph[0], ph[1], ph[2], pat["zone"]["policy_wan"], 1450,
                       blocked=True, cat=61, url="https://%s/o365/login" % ph[0])
        self.virus(t0 + timedelta(minutes=6), pat, pat["zone"], ph,
                   "W32/Generic.AP.5C1B7A!tr", "Rechnung_08_2026.zip",
                   "https://%s/dl/Rechnung_08_2026.zip" % ph[0])
        self.ips(t0 + timedelta(minutes=9), pat, pat["zone"], THREAT["c2_primary"],
                 "Eicar.Virus.Test.File", 29844, "critical", action="dropped")
        srv = self.by_role.get("server", [])
        for i in range(self.rnd.randint(8, 25)):
            tt = t0 + timedelta(minutes=14 + i * 3)
            self.session(tt, pat, FLOWS["smb-internal"][0])
            if srv and i % 5 == 0:
                self.ev_user_auth(tt, pat, ok=False)
        for i in range(self.rnd.randint(4, 12)):
            dga = "%s.top" % "".join(self.rnd.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(12))
            self.dns_pair(t0 + timedelta(minutes=40 + i * 5), pat, pat["zone"],
                          self._nextsess(), dga, cat=88, nxdomain=True)
        ex = THREAT["exfil"]
        for i in range(self.rnd.randint(3, 9)):
            self.dlp(t0 + timedelta(minutes=70 + i * 8), pat, pat["zone"], ex,
                     "HR_Payroll_export_%02d.csv" % i, "csv", self.rnd.randint(2_000_000, 90_000_000))
        self.anomaly(t0 + timedelta(minutes=95), pat, pat["zone"], "tcp_syn_flood", 100663396,
                     self.rnd.randint(900, 9000))

    def scenario_ot_intrusion(self, day):
        """Engineering workstation reaches a PLC it never talks to, then a write burst."""
        plcs = self.by_role.get("plc", [])
        ws = [h for h in self.hosts if h["role"] in ("workstation", "server")]
        if not plcs or not ws:
            return
        att = self.rnd.choice(ws); tgt = self.rnd.choice(plcs)
        t = day.replace(hour=self.rnd.randint(19, 23), minute=self.rnd.randint(0, 59))
        for i in range(self.rnd.randint(30, 80)):
            self.session(t + timedelta(seconds=i * 20), att,
                         dict(dst="__ot_peer__", dport=502, proto=6, service="tcp/502",
                              app=None, utm=[], rate=(1, 1), bytes=(200, 1200, 200, 1400),
                              otproto="Modbus"),
                         override=dict(dstip=tgt["ip"], dstname=tgt["hostname"] + "." + self.f["domain"],
                                       action="close"))
        self.ips(t + timedelta(minutes=12), att, att["zone"],
                 (tgt["hostname"], tgt["ip"], "Reserved"),
                 "Adobe.Flash.newfunction.Handling.Code.Execution", 23305, "critical",
                 action="dropped", dport=502, service="tcp/502", dstzone=tgt["zone"])
        self.ev_iot_vuln(t + timedelta(minutes=15), tgt, max(tgt["vulncnt"], self.rnd.randint(2, 14)))

    def scenario_cryptomining(self, day):
        pool = [h for h in self.hosts if h["role"] in ("workstation", "server", "consumer")]
        if not pool:
            return
        h = self.rnd.choice(pool)
        t = day.replace(hour=self.rnd.randint(0, 23), minute=self.rnd.randint(0, 59))
        cm = THREAT["crypto"]
        for i in range(self.rnd.randint(20, 60)):
            tt = t + timedelta(minutes=i * 9)
            self.dns_pair(tt, h, h["zone"], self._nextsess(), cm[0], blocked=True, cat=98)
            self.webfilter(tt + timedelta(seconds=2), h, h["zone"], self._nextsess(),
                           cm[0], cm[1], cm[2], h["zone"]["policy_wan"], 900,
                           blocked=True, cat=98, url="https://%s:3333/" % cm[0])

    def scenario_inbound_scan(self, day):
        """Internet background noise hitting the WAN interface - feeds local-in / deny views."""
        sc = THREAT["scanner"]
        base = day.replace(hour=0, minute=0)
        for i in range(int(self.rnd.randint(120, 400) * SCALE[self.a.scale])):
            tt = base + timedelta(seconds=self.rnd.randint(0, 86399))
            port = self.rnd.choice([22, 23, 80, 443, 445, 502, 1433, 3389, 5060, 8080, 8443, 9200])
            r = self._base(tt, "traffic", "local", "0001000014", "notice")
            r.update({
                "action": "deny", "srcip": sc[1], "srcname": sc[0], "srcport": self.rnd.randint(1024, 65500),
                "srcintf": self.f["wan"]["intf"], "srcintfrole": "wan", "srccountry": sc[2],
                "dstip": self.f["wan"]["ip"], "dstname": self.f["wan"]["fqdn"], "dstport": port,
                "dstintf": "root", "dstintfrole": "undefined", "dstcountry": self.f["wan"]["country"],
                "sessionid": self._nextsess(), "proto": 6, "policyid": 0,
                "policytype": "local-in-policy", "service": "tcp/%d" % port,
                "duration": 0, "sentbyte": 0, "rcvdbyte": 0, "sentpkt": 0, "rcvdpkt": 0,
                "trandisp": "noop", "msg": "Connection Failed", "app": "tcp/%d" % port,
                "craction": 262144, "crlevel": "low", "crscore": 5,
            })
            self.tlog.append(r)

    def scenario_vpn_bruteforce(self, day):
        t = day.replace(hour=self.rnd.randint(2, 5), minute=self.rnd.randint(0, 59))
        users = ["admin", "administrator", "test", "backup", "svc_scan", "jdoe"]
        for i in range(self.rnd.randint(30, 90)):
            self.ev_sslvpn(t + timedelta(seconds=i * 11), self.rnd.choice(users),
                           THREAT["tor"][1], "France", action="ssl-login-fail",
                           reason="sslvpn_login_permission_denied")
        self.ev_sslvpn(t + timedelta(minutes=20), "jdoe", THREAT["tor"][1], "France")

    SCENARIOS = {
        "shadow-iot": ("scenario_shadow_iot", 0.7),
        "camera-c2": ("scenario_camera_c2", 0.25),
        "ransomware": ("scenario_ransomware", 0.12),
        "ot-intrusion": ("scenario_ot_intrusion", 0.2),
        "cryptomining": ("scenario_cryptomining", 0.3),
        "inbound-scan": ("scenario_inbound_scan", 1.0),
        "vpn-bruteforce": ("scenario_vpn_bruteforce", 0.3),
    }

    # ---------------------------------------------------------------- main loop
    def run(self, start, days):
        self.start_dt = start
        scale = SCALE[self.a.scale]
        curves = {"office": OFFICE_CURVE, "flat": FLAT_CURVE, "shift": SHIFT_CURVE}
        uptime = self.rnd.randint(200000, 900000)
        # Security Rating scheduler: three full runs a day at 06:00 / 14:00 / 22:00 UTC on
        # both reference units, expressed here in the dataset's local time.
        rating_hours = sorted(((h + self.a.tz) % 24) for h in (6, 14, 22))
        # --scenarios accepts "name" or "name:probability-per-day" (e.g. ransomware:0.6)
        want = []
        for tok in (self.a.scenarios or "").split(","):
            tok = tok.strip()
            if not tok:
                continue
            name, _, prob = tok.partition(":")
            want.append((name, float(prob) if prob else None))

        for d in range(days):
            day = start + timedelta(days=d)
            weekend = day.weekday() >= 5
            for hour in range(24):
                hdt = day.replace(hour=hour)
                # ---- baseline traffic
                for h in self.hosts:
                    curve = curves.get(h["curve"], OFFICE_CURVE)
                    w = curve[hour] / 100.0
                    if weekend and h["curve"] == "office":
                        w *= 0.12
                    if w <= 0.005:
                        continue
                    for bname in h["behaviours"]:
                        for flow in FLOWS.get(bname, []):
                            n = flow["rate"][0] + self.rnd.random() * (flow["rate"][1] - flow["rate"][0])
                            n = int(round(n * w * scale))
                            for _ in range(n):
                                t = hdt + timedelta(seconds=self.rnd.randint(0, 3599))
                                self.session(t, h, flow)
                # ---- VoIP: IP phones place calls, mostly to the PBX, some out via the trunk
                for h in self.by_role.get("voip", []):
                    w = OFFICE_CURVE[hour] / 100.0  # people phone during office hours, whatever VLAN the phone sits in
                    if weekend:
                        w *= 0.15
                    for _ in range(int(round(self.rnd.uniform(0.5, 4.0) * w * scale))):
                        self.voip_call(hdt + timedelta(seconds=self.rnd.randint(0, 3599)), h,
                                       external=self.rnd.random() < 0.3)
                # ---- housekeeping events
                self.ev_sdwan(hdt + timedelta(minutes=self.rnd.randint(0, 59)))
                self.ev_perfstat(hdt + timedelta(minutes=self.rnd.randint(0, 59)), uptime)
                uptime += 3600
                # ---- Security Rating scheduled run
                if self.rating and hour in rating_hours:
                    self.rating.full_run(hdt + timedelta(seconds=self.rnd.randint(2, 9)), d)
            # ---- daily events
            for h in self.rnd.sample(self.hosts, min(len(self.hosts), max(1, len(self.hosts) // 4))):
                self.ev_dhcp_ack(day.replace(hour=self.rnd.randint(0, 23),
                                             minute=self.rnd.randint(0, 59)), h)
            iot = [h for h in self.hosts if h["role"] in IOT_ROLES]
            vuln = [h for h in iot if h["vulncnt"] > 0]
            pick = vuln + self.rnd.sample(iot, min(len(iot), max(1, len(iot) // 8)))
            for h in self.rnd.sample(pick, min(len(pick), max(1, len(pick) * 2 // 3))):
                self.ev_iot_vuln(day.replace(hour=self.rnd.randint(0, 23),
                                             minute=self.rnd.randint(0, 59)), h)
            for u in self.f.get("admins", ["fwadmin"]):
                if self.rnd.random() < 0.6:
                    self.ev_admin_login(day.replace(hour=self.rnd.randint(7, 18),
                                                    minute=self.rnd.randint(0, 59)),
                                        u, self.f.get("admin_src", "10.0.0.5"),
                                        ok=self.rnd.random() > 0.12)
            for h in self.rnd.sample([x for x in self.hosts if x.get("user")] or self.hosts,
                                     min(6, len(self.hosts))):
                if h.get("user"):
                    self.ev_user_auth(day.replace(hour=self.rnd.randint(7, 18),
                                                  minute=self.rnd.randint(0, 59)), h)
            for u in self.f.get("users", [])[:4]:
                if self.rnd.random() < 0.5:
                    self.ev_sslvpn(day.replace(hour=self.rnd.randint(6, 21),
                                               minute=self.rnd.randint(0, 59)),
                                   u, "62.204.108.%d" % self.rnd.randint(2, 250), "Switzerland")
            if self.rnd.random() < 0.3:
                tc = day.replace(hour=self.rnd.randint(8, 17), minute=self.rnd.randint(0, 59))
                self.ev_cfg_change(tc, self.f.get("admins", ["fwadmin"])[0],
                                   self.rnd.choice(["firewall.policy", "firewall.address",
                                                    "webfilter.profile", "application.list"]),
                                   self.rnd.choice(["DIA Clients", "IoT-VLAN", "MP-Default", "Corporate"]))
                if self.rating:  # a policy edit makes the rating engine re-run the policy checks
                    self.rating.partial_run(tc + timedelta(minutes=self.rnd.randint(1, 4)), d, "policy")
            if self.rating and self.rnd.random() < 0.4:
                self.rating.partial_run(day.replace(hour=self.rnd.randint(7, 20),
                                                    minute=self.rnd.randint(0, 59)), d, "faz")
            # ---- scenarios
            for name, override in want:
                meth, prob = self.SCENARIOS.get(name, (None, 0))
                if meth is None:
                    continue
                p = override if override is not None else (prob if days > 3 else 1.0)
                if self.rnd.random() < p:
                    getattr(self, meth)(day)

        # Keep every record inside the requested window: a periodic session update or a
        # scenario tail can otherwise spill a handful of records into an extra day and
        # produce a one-line log file.
        lo = start.strftime("%Y-%m-%d")
        hi = (start + timedelta(days=days - 1)).strftime("%Y-%m-%d")
        self.tlog = [r for r in self.tlog if lo <= r["date"] <= hi]
        self.elog = [r for r in self.elog if lo <= r["date"] <= hi]
        self.plog = [r for r in self.plog if lo <= r["date"] <= hi]
        self.xlog = [r for r in self.xlog if lo <= r["date"] <= hi]
        self.tlog.sort(key=lambda r: r["eventtime"])
        self.elog.sort(key=lambda r: r["eventtime"])
        self.plog.sort(key=lambda r: r["eventtime"])
        self.xlog.sort(key=lambda r: (r["itime"], r["session_id"]))


# --------------------------------------------------------------------------------------
# output
# --------------------------------------------------------------------------------------
def write_logs(gen, outdir, gzip_out=False):
    os.makedirs(outdir, exist_ok=True)
    written = []
    for kind, recs in (("tlog", gen.tlog), ("elog", gen.elog), ("plog", gen.plog)):
        byday = {}
        for r in recs:
            byday.setdefault(r["date"], []).append(r)
        for date, rows in sorted(byday.items()):
            epoch = int(datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp())
            fn = "%s.%s.%s.%d.log" % (gen.a.devid, gen.a.vdom, kind, epoch)
            path = os.path.join(outdir, fn + (".gz" if gzip_out else ""))
            op = gzip.open if gzip_out else open
            with op(path, "wt", encoding="utf-8") as fh:
                for r in rows:
                    fh.write(render(r) + "\n")
            written.append((path, len(rows)))
    # Security Rating stream. Default is the FortiAnalyzer CSV export layout (observed
    # byte-for-byte); "raw" is an unverified key=value guess - see references/security-rating.md
    if gen.xlog:
        byday = {}
        for r in gen.xlog:
            byday.setdefault(r["date"], []).append(r)
        for date, rows in sorted(byday.items()):
            epoch = int(datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp())
            if gen.a.xlog_format == "csv":
                fn = "%s.%s.xlog.%d.csv" % (gen.a.devid, gen.a.vdom, epoch)
                path = os.path.join(outdir, fn)
                with open(path, "w", newline="", encoding="utf-8") as fh:
                    w = csv.writer(fh, quoting=csv.QUOTE_ALL, lineterminator="\n")
                    for r in rows:
                        w.writerow(xlog_csv_row(r))
            else:
                fn = "%s.%s.xlog.%d.log" % (gen.a.devid, gen.a.vdom, epoch)
                path = os.path.join(outdir, fn + (".gz" if gzip_out else ""))
                op = gzip.open if gzip_out else open
                with op(path, "wt", encoding="utf-8") as fh:
                    for r in rows:
                        fh.write(xlog_raw_line(r) + "\n")
            written.append((path, len(rows)))
    return written


def write_assets(gen, outdir):
    p = os.path.join(outdir, "assets.csv")
    with open(p, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["hostname", "ip", "mac", "devtype", "osname", "srcfamily", "srchwvendor",
                    "srchwversion", "srcswversion", "purdue_level", "zone", "role", "user",
                    "iot_vulncnt"])
        for h in gen.hosts:
            w.writerow([h["hostname"], h["ip"], h["mac"], h["devtype"], h["osname"], h["srcfamily"],
                        h["srchwvendor"], h["srchwversion"], h["srcswversion"], h["purdue"],
                        h["zone"]["name"], h["role"], h.get("user") or "", h.get("vulncnt", 0)])
    return p


RUNBOOK = """# Import runbook - {devname} ({devid})

Generated {now} by fazgen.py
FortiOS profile: {version} (logver={logver}) | vdom: {vdom} | {ndays} days from {start}
{ntlog} traffic/UTM records, {nelog} event records, {nplog} VoIP records,
{nxlog} security-rating results ({nvuln} of {nhosts} assets flagged IoT/OT-vulnerable).

## 1. Create the device on the FortiAnalyzer (once)

Device Manager > Add Device > Link Device By: **Serial Number**
  Name:          {devname}
  Serial Number: {devid}
  Device Model:  {model}

A model device added by serial number is authorized immediately and is ready to receive
logs. `execute log import` refuses any serial that is not already in the device list
("Invalid Device ID"), so this step is mandatory.

## 2. Widen the analytics window BEFORE importing

Backdated logs are silently dropped if the SQL start time or the ADOM retention policy is
newer than the logs. This is the single most common reason an import "succeeds" but nothing
shows up in FortiView.

    config system sql
        set start-time 00:00 {sqlstart}
        set rebuild-event-start-time 00:00 {sqlstart}
    end

Also check the ADOM's "Keep Logs for Analytics" value covers {ndays}+ days:
System Settings > Storage Info (or Log Storage policy for the ADOM).

## 3. Copy the files to an FTP/SFTP/SCP/TFTP server and import

    execute log import sftp <ip:port> <user> <password> <dir-or-file> {devid}

Directory import pulls every .log / .csv in the folder (up to 10000 files), so pointing it
at this output directory imports the whole date range in one command:

    execute log import sftp 10.0.0.20 fazimport '<password>' logs/{devid}/ {devid}

## 4. Verify

    diagnose test application sqllogd 5      # log device scan info
    diagnose sql show db-size
    execute log-integrity {devid} {vdom} <one of the imported file names>

Then: Log View > FortiGate > Traffic (set the time range to cover {start} .. {end}),
FortiView, Fabric View > Asset Identity Center, Dashboards > IOT.

## 5. Security Rating stream (the *.xlog.*.csv files)

These are the FortiGate's security-rating results, in the exact layout FortiAnalyzer itself
exports for this stream. They feed Fabric View > Security Rating, the FSBP/PCI/CIS rating
reports and the Fabric State of Security monitor. Two checks matter for a vulnerability
story:

  - FortiguardIotVulnerability  -> {rating_iot} - lists the MAC of every asset in
                                    assets.csv with iot_vulncnt > 0
  - FG-IR-*  (PSIRT)            -> the FortiGate's OWN advisories; {npsirt_fail} set to failed

Import them separately, after the .log files, and confirm on YOUR build that
`execute log import` accepts the stream at all - this has not been verified:

    execute log import sftp 10.0.0.20 fazimport '<password>' logs/{devid}/{devid}.{vdom}.xlog.<epoch>.csv {devid}

If the import is refused, the stream can only come from a live FortiGate with a Security
Rating licence sending to this FortiAnalyzer. Details: references/security-rating.md

## 6. Per-asset vulnerabilities: what this dataset CANNOT do

The CVE list behind the "Vulnerabilities" column in Asset Identity Center (and the OT/IoT
vulnerability widgets on the Asset Summary page) is not carried by any log record. The
FortiGate pushes it from its device store over the OFTP endpoint data link, which needs
FortiOS 7.4+ and the OT Security Service entitlement on both units. Check the link with

    diagnose test application oftpd 20 fgt-stat      # on the FortiAnalyzer

The 0100020150 events in the elog files carry a vulnerability COUNT per asset (same numbers
as iot_vulncnt in assets.csv) and the rating check above names the vulnerable MACs - that is
the whole log-side story. FortiClient/endpoint vulnerabilities come through the EMS
connector playbook, also not through FortiGate logs. See references/assets-and-iot.md.

## What feeds which view

| View | Needs |
|---|---|
| Log View / FortiView | any traffic + utm logs |
| Fabric View > Asset Identity Center | srcmac, srcip, srcname, devtype, osname, srcfamily, srchwvendor, srchwversion, srcswversion on traffic logs |
| Dashboards > IOT | the same asset fields + FortiGate IoT Detection Service entitlement, and OT Security Service entitlement for OT devices |
| Asset Identity Center > OT View | FortiOS >= 7.4 sending OT information; Purdue level is a Security Fabric asset attribute, NOT a log field - see references/assets-and-iot.md |
| Threat / Compromised Hosts | crscore / craction / crlevel on traffic, IPS and webfilter logs |
| Applications & Websites | app / appid / appcat / apprisk (app-ctrl) and cat / catdesc (webfilter, dnsfilter) |
| FortiView > VPN / VoIP, VoIP report | utm/voip logs (plog files) |
| Fabric View > Security Rating, FSBP/PCI/CIS reports | the xlog security-rating stream (import unverified) |
| Asset Identity Center > Vulnerabilities column, OT/IoT vulnerability widgets | NOT logs - OFTP endpoint data link from a live FortiGate with OT Security Service |

Full detail: references/faz-import.md
"""


def write_runbook(gen, outdir, start, days, model):
    end = start + timedelta(days=days - 1)
    nvuln = sum(1 for h in gen.hosts if h.get("vulncnt", 0) > 0)
    npsirt = len(gen.rating.psirt_fail) if gen.rating else 0
    if gen.rating and gen.a.rating_posture == "poor" and not npsirt:
        npsirt = sum(1 for k, v in gen.rating.state.items() if k.startswith("FG-IR-") and v == "failed")
    txt = RUNBOOK.format(
        devname=gen.a.devname, devid=gen.a.devid, now=datetime.now().strftime("%Y-%m-%d %H:%M"),
        version=gen.a.version, logver=gen.v["logver"], vdom=gen.a.vdom, ndays=days,
        start=start.strftime("%Y-%m-%d"), end=end.strftime("%Y-%m-%d"),
        ntlog=len(gen.tlog), nelog=len(gen.elog), nplog=len(gen.plog), nxlog=len(gen.xlog),
        nhosts=len(gen.hosts), nvuln=nvuln, model=model,
        rating_iot="failed" if nvuln else "passed", npsirt_fail=npsirt,
        sqlstart=(start - timedelta(days=7)).strftime("%Y/%m/%d"))
    p = os.path.join(outdir, "IMPORT.md")
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(txt)
    return p


# --------------------------------------------------------------------------------------
def main():
    fleetdir = os.path.join(DATA, "fleets")
    available = sorted(x[:-5] for x in os.listdir(fleetdir) if x.endswith(".json"))

    ap = argparse.ArgumentParser(description="Generate importable FortiGate logs for FortiAnalyzer demos.")
    ap.add_argument("--fleet", help="fleet blueprint name (%s)" % ", ".join(available))
    ap.add_argument("--list-fleets", action="store_true")
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--start", help="YYYY-MM-DD, default = today - days")
    ap.add_argument("--out", default="./out")
    ap.add_argument("--version", choices=sorted(VERSIONS), default="8.0")
    ap.add_argument("--scale", choices=sorted(SCALE), default="medium")
    ap.add_argument("--scenarios", default="",
                    help="comma list, each optionally with a per-day probability "
                         "(e.g. ransomware:0.6,inbound-scan). Available: %s"
                         % ",".join(Generator.SCENARIOS))
    ap.add_argument("--devid", help="FortiGate serial to stamp on every log")
    ap.add_argument("--devname")
    ap.add_argument("--vdom", default="root")
    ap.add_argument("--tz", type=int, default=2, help="UTC offset hours, default +2 (CEST)")
    ap.add_argument("--seed", type=int, default=1337)
    ap.add_argument("--gzip", action="store_true")
    ap.add_argument("--devtype-mode", choices=["extended", "verified"], default="extended",
                    help="'verified' restricts devtype to strings observed in real FortiOS logs")
    ap.add_argument("--ot-appctrl", action="store_true", default=True,
                    help="tag OT flows with app/appcat Operational.Technology (default on)")
    ap.add_argument("--no-ot-appctrl", dest="ot_appctrl", action="store_false")
    ap.add_argument("--vuln-ratio", type=float, default=0.3,
                    help="share of IoT/OT assets the FortiGuard lookup flags as vulnerable (0..1, default 0.3)")
    ap.add_argument("--no-rating", dest="rating", action="store_false", default=True,
                    help="do not generate the security-rating (xlog) stream")
    ap.add_argument("--rating-posture", choices=["good", "typical", "poor"], default="typical",
                    help="how many configuration checks fail: good / typical (as observed) / poor")
    ap.add_argument("--psirt-fail", default="",
                    help="comma list of FG-IR-* checks to report as failed (unpatched FortiGate story)")
    ap.add_argument("--rating-remediate-after", type=int, default=0,
                    help="day index from which the common hygiene failures flip to passed (score trend)")
    ap.add_argument("--xlog-format", choices=["csv", "raw"], default="csv",
                    help="csv = FortiAnalyzer export layout (observed); raw = unverified key=value guess")
    ap.add_argument("--adom", default="root", help="adom_name stamped on the xlog stream")
    a = ap.parse_args()
    if a.psirt_fail:
        bad = [x for x in a.psirt_fail.split(",") if x.strip() and not x.strip().startswith("FG-IR-")]
        if bad:
            ap.error("--psirt-fail expects FG-IR-* names, got %s" % ",".join(bad))

    if a.list_fleets or not a.fleet:
        print("Available fleets:\n")
        for name in available:
            f = json.load(open(os.path.join(fleetdir, name + ".json")))
            n = sum(g["count"] for z in f["zones"] for g in z["hosts"])
            print("  %-20s %-52s %3d hosts" % (name, f.get("description", ""), n))
        print("\nScenarios: %s" % ", ".join(Generator.SCENARIOS))
        return 0

    fleet = json.load(open(os.path.join(fleetdir, a.fleet + ".json")))
    a.devid = a.devid or fleet["devid"]
    a.devname = a.devname or fleet["devname"]
    start = (datetime.strptime(a.start, "%Y-%m-%d") if a.start
             else datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
             - timedelta(days=a.days))
    start = start.replace(hour=0, minute=0, second=0, microsecond=0)

    gen = Generator(fleet, a)
    if gen.rating:
        unknown = sorted(gen.rating.psirt_fail - set(gen.rating.prof["multiplicity"]))
        if unknown:
            print("warning      : %s not in the %s check set (never reported by the reference unit) - ignored"
                  % (",".join(unknown), a.version))
    gen.run(start, a.days)
    files = write_logs(gen, a.out, a.gzip)
    write_assets(gen, a.out)
    write_runbook(gen, a.out, start, a.days, fleet.get("model", "FortiGate-VM64"))

    total = sum(n for _, n in files)
    print("fleet        : %s (%d assets, %d zones)" % (a.fleet, len(gen.hosts), len(fleet["zones"])))
    print("device       : %s / %s  vdom=%s  FortiOS %s (logver=%s)"
          % (a.devname, a.devid, a.vdom, a.version, gen.v["logver"]))
    print("range        : %s .. %s (%d days, scale=%s)"
          % (start.date(), (start + timedelta(days=a.days - 1)).date(), a.days, a.scale))
    nvuln = sum(1 for h in gen.hosts if h.get("vulncnt", 0) > 0)
    print("records      : %d traffic/utm + %d event + %d voip + %d rating = %d"
          % (len(gen.tlog), len(gen.elog), len(gen.plog), len(gen.xlog), total))
    print("vulnerable   : %d/%d assets flagged by the IoT/OT lookup (count only - see IMPORT.md section 6)"
          % (nvuln, len(gen.hosts)))
    if gen.rating:
        st = gen.rating.state
        nf = sum(1 for k, v in st.items() if v == "failed" and not k.startswith("FG-IR-"))
        pf = sorted(k for k, v in st.items() if v == "failed" and k.startswith("FG-IR-"))
        print("rating       : posture=%s, %d config checks failed, PSIRT failed: %s, xlog format=%s"
              % (gen.a.rating_posture, nf, ",".join(pf) or "none", gen.a.xlog_format))
    print("files        : %d in %s" % (len(files), os.path.abspath(a.out)))
    print("next         : read %s/IMPORT.md" % a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
