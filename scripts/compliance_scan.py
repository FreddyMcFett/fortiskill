#!/usr/bin/env python3
"""Compliance scan: the release gate of this public repository.

Everything pushed to this repo is public, so this scanner blocks content that must
not be published:

  secret.*        credentials, tokens, private keys, licence files, FortiOS ENC secrets
  pii.*           e-mail addresses, phone numbers, IBAN, AHV numbers, payment cards, MACs
  network.*       public IPv4 addresses outside RFC 5737 / well-known services
  fortinet.*      real device serial numbers, FortiClient EMS cloud tenant hosts
  confidential.*  classification markings (EN/DE/FR/IT), non-disclosure / not-yet-public references
  internal.*      links into collaboration systems (SharePoint, Salesforce, Teams, ...),
                  personal or engagement-specific notes, internal policy references
  commercial.*    prices next to SKUs, discount rates, Salesforce record IDs
  office.*        author / reviewer identities, comments, sensitivity labels in Office files
  image.* pdf.*   GPS position and author metadata
  file.*          file types that do not belong here (keys, captures, raw logs, configs, and
                  Office/data/archive files that were not explicitly reviewed)
  denylist.term   customer / project names from the COMPLIANCE_DENYLIST secret
  commit.*        personal author e-mail addresses on commits

What is scanned (modes combine):
  default            every git-tracked file in the working tree
  PATH ...           only these files / directories
  --staged           the staged content (pre-commit hook)
  --commits A..B     every file version, message and author of the commits in A..B, so
                     content that was added and removed again inside a PR is caught too
  --commit-msg FILE  a commit message (commit-msg hook)
  --env-text VAR     the text of an environment variable (PR title and body in CI)

A finding can only be accepted through an entry in .compliance/policy.toml (rule +
path [+ match] + mandatory reason, optional expiry). Matched values are never printed
in full: CI logs and annotations of a public repo are public as well.

Exit code: 1 if an error is not covered by the policy (or any warning with
--fail-on-warning), 2 on usage or policy errors, 0 otherwise.
Stdlib only, Python >= 3.11. Run `--list-rules` for the rule catalogue and
`--self-test` to check the rules against built-in samples.
"""
import argparse
import bisect
import dataclasses
import datetime
import fnmatch
import html
import io
import ipaddress
import math
import os
import re
import struct
import subprocess
import sys
import tomllib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POLICY_FILE = ROOT / ".compliance" / "policy.toml"
LOCAL_DENYLIST = ROOT / ".compliance" / "denylist.local.txt"
ERROR, WARNING = "error", "warning"
MAX_BLOB_BYTES = 50 * 1024 * 1024

DEFAULT_SETTINGS = {
    "allowed_email_domains": ["example.com", "example.net", "example.org"],
    "allowed_emails": [],
    "allowed_document_authors": [""],
    "commit_email_patterns": ["*@users.noreply.github.com"],
}
RESERVED_TLDS = (".example", ".test", ".invalid", ".localhost")
FILE_EXT_TLDS = {"png", "jpg", "jpeg", "gif", "svg", "webp", "ico", "js", "ts", "css", "md",
                 "py", "json", "html", "txt", "yml", "yaml", "xml", "pdf"}

# Office parts that carry the identity of authors, reviewers and co-authors. Shared
# with scripts/sanitize_office.py, which removes the PowerPoint ones.
IDENTITY_PARTS = {
    "co-authoring change history": re.compile(r"^ppt/changesInfos/"),
    "comments": re.compile(r"^(?:ppt/comments/|ppt/commentAuthors\.xml$|ppt/authors\.xml$|"
                           r"word/comments[A-Za-z]*\.xml$|xl/comments\d*\.xml$|xl/threadedComments/)"),
    "people list": re.compile(r"^(?:word/people\.xml$|xl/persons/)"),
}
OFFICE_EXT = re.compile(r"(?i)\.(?:pptx|potx|ppsx|pptm|docx|dotx|docm|xlsx|xlsm|xltx)$")


def j(*parts):
    """Join string fragments. Self-test samples are built from fragments so that this
    file never contains a contiguous sample and stays clean under its own scan."""
    return "".join(parts)


# --------------------------------------------------------------------------- findings

@dataclasses.dataclass
class Finding:
    rule: str
    severity: str
    path: str              # repo path, or a pseudo path such as "<PR_BODY>"
    message: str
    line: int | None = None
    match: str = ""        # raw matched value; only ever shown redacted
    where: str = ""        # zip member or commit, when not the plain working-tree file
    in_tree: bool = True   # file exists in the working tree -> annotate it in the PR
    allowed_by: object = None

    def location(self):
        loc = self.path + (f":{self.line}" if self.line else "")
        return f"{loc} [{self.where}]" if self.where else loc

    def shown(self):
        if self.rule == "denylist.term" or not self.match:
            return ""
        return f" [{redact(self.match)}]"


def redact(value):
    s = " ".join(value.split())
    if len(s) <= 6:
        return "*" * len(s)
    return f"{s[:2]}…{s[-2:]}, {len(s)} chars"


# --------------------------------------------------------------------------- validators

PLACEHOLDER_RE = re.compile(
    r"(?i)example|sample|dummy|placeholder|change[_-]?me|your[_-]|redacted|masked|xxxx|\*\*\*|"
    r"<[^>]*>|\{\{|\$\{|\$\(|%[A-Z_]+%|^\$[A-Za-z_]|vault_|\bvar\.|\benv\.|environ|getenv|"
    r"secrets\.|^(?:none|null|true|false|undefined|string|required|optional|str|bytes)$")
CODE_REF_RE = re.compile(r"^[A-Za-z_]\w*(?:\.[A-Za-z_]\w*|\[[^\]]*\]|\([^)]*\)?)+$")


def entropy(s):
    counts = {c: s.count(c) for c in set(s)}
    return -sum(n / len(s) * math.log2(n / len(s)) for n in counts.values())


def looks_secret(value, min_len=8):
    s = value.strip().strip("\"'`")
    if len(s) < min_len or len(set(s)) <= 2 or PLACEHOLDER_RE.search(s) or CODE_REF_RE.match(s):
        return False
    if re.fullmatch(r"[A-Za-z_][A-Za-z_]*", s) or re.fullmatch(r"[a-z]+(?:[-_./ ][a-z]+)*", s):
        return False  # identifiers and plain words
    classes = sum(bool(re.search(p, s)) for p in (r"[a-z]", r"[A-Z]", r"\d", r"[^A-Za-z0-9]"))
    return classes >= 2 and entropy(s) >= 2.8


def chk_secret(min_len=8):
    return lambda m, ctx, v: looks_secret(v, min_len)


def chk_not_placeholder(m, ctx, v):
    return not PLACEHOLDER_RE.search(v) and len(set(v)) > 2


def chk_email(m, ctx, v):
    local, _, domain = v.lower().rpartition("@")
    if domain.rsplit(".", 1)[-1] in FILE_EXT_TLDS or local == "git":
        return False
    if v.lower() in ctx.allowed_emails or domain.endswith(RESERVED_TLDS):
        return False
    return not any(domain == d or domain.endswith("." + d) for d in ctx.allowed_email_domains)


def chk_phone(m, ctx, v):
    return 9 <= len(re.sub(r"\D", "", v)) <= 15


IBAN_LEN = {"CH": 21, "LI": 21, "DE": 22, "AT": 20, "FR": 27, "IT": 27, "GB": 22, "NL": 18,
            "BE": 16, "ES": 24, "LU": 20, "PL": 28, "SE": 24, "DK": 18, "NO": 15, "FI": 18,
            "IE": 22, "PT": 25, "CZ": 24, "HU": 28, "SK": 24, "SI": 19, "HR": 21, "MC": 27}


def chk_iban(m, ctx, v):
    s = v.replace(" ", "")
    if IBAN_LEN.get(s[:2]) != len(s):
        return False
    digits = "".join(str(int(c, 36)) for c in s[4:] + s[:4])
    return int(digits) % 97 == 1


def ean13_ok(digits):
    total = sum(int(d) * (3 if i % 2 else 1) for i, d in enumerate(digits[:12]))
    return (10 - total % 10) % 10 == int(digits[12])


def chk_ahv(m, ctx, v):
    d = re.sub(r"\D", "", v)
    return len(d) == 13 and ean13_ok(d)


def luhn_ok(digits):
    total = 0
    for i, d in enumerate(reversed(digits)):
        n = int(d) * (2 if i % 2 else 1)
        total += n - 9 if n > 9 else n
    return total % 10 == 0


TEST_PANS = {"4111111111111111", "4242424242424242", "4012888888881881", "5555555555554444",
             "5105105105105100", "378282246310005", "371449635398431", "6011111111111117"}


def chk_card(m, ctx, v):
    d = re.sub(r"\D", "", v)
    if d in TEST_PANS or not 13 <= len(d) <= 19 or not luhn_ok(d):
        return False
    return bool(re.match(r"4|5[1-5]|2[2-7]|3[47]|6(?:011|5)|35", d))


def chk_mac(m, ctx, v):
    s = v.lower().replace("-", ":")
    octets = s.split(":")
    if s.startswith("00:00:5e:00:53:") or len(set(octets)) == 1:
        return False
    return not s.endswith(("11:22:33", "12:34:56", "aa:bb:cc", "de:ad:be:ef", "00:00:00"))


DOC_NETS = [ipaddress.ip_network(n) for n in ("192.0.2.0/24", "198.51.100.0/24", "203.0.113.0/24")]
WELL_KNOWN_IPS = {"8.8.8.8", "8.8.4.4", "1.1.1.1", "1.0.0.1", "9.9.9.9", "149.112.112.112",
                  "208.67.222.222", "208.67.220.220"}


def chk_public_ip(m, ctx, v):
    if v in WELL_KNOWN_IPS or re.search(r"(?i)(?:ver(?:sion)?|build|firmware|release|\bv)\W{0,4}$",
                                         m.string[max(0, m.start() - 24):m.start()]):
        return False
    try:
        ip = ipaddress.ip_address(v)
    except ValueError:
        return False
    return ip.is_global and not any(ip in n for n in DOC_NETS)


def chk_serial(m, ctx, v):
    if re.search(r"DEMO|TEST|EXAMPLE|SAMPLE|XXXX|0{7,}", v):
        return False
    return len(re.findall(r"\d", v)) >= 4


def chk_sfdc(m, ctx, v):
    body = v[3:]
    return bool(re.search(r"[A-Z]", body) and len(re.findall(r"\d", body)) >= 3)


SKU_RE = re.compile(r"\b(?:FC\d?-10-[A-Z0-9]{2,}|F[A-Z]{1,4}-\d{2,4}[A-Z]{0,3}\d?(?:-[A-Z0-9]{2,})*|"
                    r"(?:SP|LIC)-[A-Z0-9-]{3,})\b")


def _line_of(m):
    s = m.string
    return s[s.rfind("\n", 0, m.start()) + 1: (s.find("\n", m.end()) + 1 or len(s) + 1) - 1]


def chk_price_with_sku(m, ctx, v):
    return bool(SKU_RE.search(_line_of(m)))


def chk_price_alone(m, ctx, v):
    return not SKU_RE.search(_line_of(m))


# --------------------------------------------------------------------------- rules

@dataclasses.dataclass(frozen=True)
class Rule:
    id: str
    severity: str
    regex: re.Pattern
    message: str
    check: object = None
    group: int = 0


def rule(rid, sev, pattern, message, check=None, group=0, flags=0):
    return Rule(rid, sev, re.compile(pattern, flags), message, check, group)


I, M = re.IGNORECASE, re.MULTILINE
W = r"[\s_-]+"  # word gap; also keeps the phrase patterns from matching their own source
CURRENCY = (r"(?:\b(?:CHF|USD|EUR|GBP)|(?<![A-Za-z$!:])[$€£])[ \t]?\d[\d',. ]*\d(?:\.-)?(?![\w:])|"
            r"\b\d[\d',.]*\d(?:\.-)?[ \t]?(?:CHF|USD|EUR|GBP|€)(?![A-Za-z])")

TEXT_RULES = [
    # secrets
    rule("secret.private-key", ERROR, r"-----BEGIN (?:[A-Z0-9]+ )*PRIVATE KEY(?: BLOCK)?-----",
         "private key"),
    rule("secret.license-file", ERROR, r"-----BEGIN (?:[A-Z0-9]+ )*LICENSE-----",
         "licence file content (e.g. FortiGate VM licence)"),
    rule("secret.github-token", ERROR, r"\b(?:gh[pousr]_[A-Za-z0-9]{36,255}|github_pat_[A-Za-z0-9_]{50,255})\b",
         "GitHub token"),
    rule("secret.aws-key", ERROR, r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b", "AWS access key ID"),
    rule("secret.anthropic-key", ERROR, r"\bsk-ant-[A-Za-z0-9_-]{20,}", "Anthropic API key"),
    rule("secret.openai-key", ERROR, r"\bsk-(?!ant-)(?:proj-|svcacct-|admin-)?[A-Za-z0-9_-]{32,}",
         "OpenAI-style API key"),
    rule("secret.google-key", ERROR, r"\bAIza[0-9A-Za-z_-]{35}(?![0-9A-Za-z_-])", "Google API key"),
    rule("secret.slack-token", ERROR, r"\bxox[abposr]-[A-Za-z0-9-]{10,}", "Slack token"),
    rule("secret.webhook-url", ERROR,
         r"https://(?:hooks\.slack\.com/(?:services|workflows)/|[A-Za-z0-9-]+\.webhook\.office\.com/webhookb2/|"
         r"(?:discord|discordapp)\.com/api/webhooks/|[A-Za-z0-9-]+\.logic\.azure\.com\S*?[?&]sig=)[^\s\"'<>)]+",
         "incoming-webhook URL (Slack / Teams / Discord / Power Automate)"),
    rule("secret.connection-string", ERROR,
         r"\b(?:AccountKey|SharedAccessKey|SharedAccessSignature)=[A-Za-z0-9+/%]{20,}={0,2}",
         "Azure key / SAS in a connection string"),
    rule("secret.jwt", ERROR, r"\beyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}",
         "JSON Web Token"),
    rule("secret.url-credentials", ERROR,
         r"\b[a-z][a-z0-9+.-]{1,15}://[^\s/:@\"'<>]{1,64}:([^\s/@\"'<>]{1,128})@[A-Za-z0-9.-]+",
         "password embedded in a URL", chk_secret(6), group=1),
    rule("secret.bearer-token", ERROR, r"\bauthorization:\s*bearer\s+([A-Za-z0-9._~+/-]{16,}=*)",
         "bearer token", chk_secret(16), group=1, flags=I),
    rule("secret.fortios-enc", ERROR,
         r"^[ \t]*set[ \t]+[a-z0-9-]*(?:passw(?:or)?d|pwd|secret|psk|key|token|passphrase)[a-z0-9-]*"
         r"[ \t]+ENC[ \t]+([A-Za-z0-9+/]{16,}={0,2})",
         "encrypted FortiOS secret from a configuration backup", chk_not_placeholder, group=1, flags=M | I),
    rule("secret.fortios-plaintext", ERROR,
         r"^[ \t]*set[ \t]+(?:password|passwd|psksecret|secret|pre-shared-key|passphrase|api-key|auth-pwd|"
         r"ldap-password|radius-secret|server-key|sso-password|key-password|ppk-secret|auth-password|"
         r"priv-password)[ \t]+(?!ENC\b)(\"[^\"\n]*\"|'[^'\n]*'|\S+)",
         "plain-text secret in FortiOS CLI", chk_secret(6), group=1, flags=M | I),
    rule("secret.assignment", ERROR,
         r"(?<![A-Za-z0-9])(?:passw(?:or)?d|pwd|secret|client[_-]?secret|api[_-]?key|apikey|access[_-]?key|"
         r"access[_-]?token|auth[_-]?token|private[_-]?key|token|psk)[\"']?[ \t]*[:=][ \t]*[\"']?"
         r"([^\s\"'`,;)}\]{]+)",
         "hard-coded credential", chk_secret(8), group=1, flags=I),
    # personal data
    rule("pii.email", ERROR,
         r"(?<![A-Za-z0-9._%+-])([A-Za-z0-9._%+-]{1,64}@(?:[A-Za-z0-9-]{1,63}\.)+[A-Za-z]{2,24})(?![A-Za-z0-9-])",
         "e-mail address", chk_email, group=1),
    rule("pii.phone", ERROR, r"(?<![\w+=])\+\d{1,3}(?:[ ./-]?\(?\d{1,5}\)?){2,6}(?!\w|\.\d)",
         "phone number", chk_phone),
    rule("pii.phone", ERROR, r"(?<![\w.+/:-])0[1-9]\d[ /.-]?\d{3}[ .-]\d{2}[ .-]\d{2}(?![\w:-]|\.\d)",
         "phone number (Swiss format)", chk_phone),
    rule("pii.iban", ERROR, r"\b([A-Z]{2}\d{2}(?: ?[A-Z0-9]{4}){2,7}(?: ?[A-Z0-9]{1,3})?)\b",
         "IBAN", chk_iban, group=1),
    rule("pii.ahv", ERROR, r"\b756[. ]?\d{4}[. ]?\d{4}[. ]?\d{2}\b", "Swiss AHV/AVS number", chk_ahv),
    rule("pii.payment-card", ERROR,
         r"(?<![\w=:.\-/])(\d{4}(?:[ -]\d{4}){3}|\d{4}[ -]\d{6}[ -]\d{5}|\d{15,16})(?![\w.\-/])",
         "payment card number", chk_card, group=1),
    rule("pii.mac-address", ERROR, r"(?<![\w:-])((?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2})(?![\w:-])",
         "MAC address (device identifier) - use 00:00:5e:00:53:xx or a placeholder", chk_mac, group=1),
    rule("network.public-ip", ERROR,
         r"(?<![\w.:])((?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(?:\.(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})(?!\.?\d)",
         "public IPv4 address - use RFC 5737 ranges unless it is a well-known service", chk_public_ip, group=1),
    rule("fortinet.serial", ERROR,
         r"\b((?:FGT|FGVM|FG|FWF|FAZ|FMG|FAC|FSW|FS|FAP|FP|FCT|FTK|FML|FSA|FPX|FWB|FAD|FDD|FSR|FNC|FEX|"
         r"FCH|FTS|FDC|FIS|FNR|FVE|FBV|FRC|FMR|FPA|FSM|FSF)[A-Z0-9]{10,14})\b",
         "Fortinet device serial number (identifies a customer device) - use a DEMO serial", chk_serial, group=1),
    rule("fortinet.cloud-tenant", ERROR, r"\b(ad-\d{4,}-\d{3,})\.forticlient-emsproxy\.forticloud\.com\b",
         "FortiClient EMS cloud tenant host (identifies a real tenant) - use ad-1000001-0001",
         lambda m, ctx, v: not re.fullmatch(r"ad-[01]+-[01]+", v), group=1),
    # confidentiality
    rule("confidential.marking", ERROR,
         rf"\b(?:fortinet|company|strictly|highly|partner|business|customer){W}confidential\b|"
         rf"\bconfidential{W}(?:and|&){W}proprietary\b|\bproprietary{W}(?:and|&){W}confidential\b|"
         rf"\b(?:for{W})?internal{W}(?:use|distribution){W}only\b|\bfor{W}internal{W}use\b|\binternal{W}only\b|"
         rf"\bnot{W}for{W}(?:external{W}|public{W})?(?:distribution|release|circulation)\b|"
         rf"\bdo{W}not{W}(?:distribute|forward|disclose|share{W}externally)\b|"
         rf"\b(?:classification|sensitivity|klassifizierung)\s*:\s*(?:confidential|internal|restricted|secret|"
         rf"vertraulic[h]|intern)\b|"
         rf"\bstreng{W}vertraulic[h]\b|\bvertraulic[h]\b|\bnur{W}intern\b|\bnicht{W}zur{W}weitergabe\b|"
         rf"\bkeine{W}weitergabe\b|\bnur{W}für{W}(?:den{W})?interne[nr]?{W}(?:gebrauch|verwendung|einsatz)\b|"
         rf"\binterne{W}verwendung\b|"
         rf"\bconfidentiel(?:le)?\b|\busage{W}interne\b|\bdiffusion{W}(?:restreinte|interne|limitée)\b|"
         rf"\b(?:strettamente{W})?riservat[oa]\b|\buso{W}interno\b",
         "confidentiality marking", flags=I),
    rule("confidential.marking", ERROR, r"\bCONFIDENTIA[L]\b|\bRESTRICTE[D]\b|\bTLP:(?:RE[D]|AMBE[R](?:\+STRICT)?)\b",
         "confidentiality marking"),
    rule("confidential.nda", WARNING, r"\bND[A]s?\b|(?i:\b(?:geheimhaltungs|vertraulichkeits)vereinbarung)",
         "reference to non-disclosure material - make sure nothing covered by it is included"),
    rule("confidential.not-public", WARNING,
         rf"\b(?:not{W}(?:yet{W})?(?:publicly{W})?announced|unannounce[d]|pre-?announcemen[t]|under{W}embargo|embargoe[d])\b",
         "reference to information that is not public yet", flags=I),
    # internal systems
    rule("internal.link", ERROR,
         r"\bhttps?://(?:[A-Za-z0-9-]+\.)*(?:sharepoint\.com|sharepoint-df\.com|my\.salesforce\.com|"
         r"lightning\.force\.com|force\.com|atlassian\.net|slack\.com/archives|teams\.microsoft\.com/l/|"
         r"teams\.live\.com|1drv\.ms|onedrive\.live\.com|docs\.google\.com|drive\.google\.com|zoom\.us/j/|"
         r"webex\.com/meet|box\.com/s/|dropbox\.com/s|notion\.so|miro\.com/app/board|lucid\.app|"
         r"figma\.com/(?:file|design))\S*",
         "link into an internal collaboration system", flags=I),
    rule("internal.partner-portal", WARNING, r"\bhttps?://partnerportal\.fortinet\.com\S*",
         "Partner Portal content is partner-only - link to public sources instead", flags=I),
    rule("internal.engagement-note", ERROR,
         rf"\bpersonal{W}note\b|\bnote{W}(?:for|to){W}(?:me|self|myself)\b|\bnotiz{W}für\b|"
         rf"\b(?:from|in){W}(?:prior|previous|past|recent|earlier){W}(?:customer{W})?"
         rf"(?:engagements?|projects?|deals?|pocs?)\b|"
         rf"\b(?:bei|aus|von){W}(?:früheren|vergangenen|bisherigen){W}(?:kunden|projekten|einsätzen)\b|"
         rf"\bemployee{W}handbook\b|\bmitarbeiterhandbuc[h]\b",
         "personal or engagement-specific note / internal policy reference - keep skills generic", flags=I),
    # commercial
    rule("commercial.sfdc-id", ERROR,
         r"\b((?:001|003|005|006|00Q|0Q0|500|800|801)[A-Za-z0-9]{12}(?:[A-Za-z0-9]{3})?)\b",
         "Salesforce record ID (account / opportunity / quote / case)", chk_sfdc, group=1),
    rule("commercial.price", ERROR, CURRENCY, "price next to a Fortinet SKU", chk_price_with_sku),
    rule("commercial.amount", WARNING, CURRENCY, "currency amount - no real prices in the repo", chk_price_alone),
    rule("commercial.discount", ERROR,
         rf"\b(?:discount|rabatt|nachlass|remise|sconto|special{W}pricing)\b[^\n.]{{0,40}}?\d{{1,2}}(?:[.,]\d+)?[ \t]?%|"
         r"\b\d{1,2}(?:[.,]\d+)?[ \t]?%[ \t]*(?:discount|rabatt|nachlass|remise|sconto)\b",
         "discount rate (deal-specific commercial data)", flags=I),
]

FILE_RULES = [
    ("file.key-material", ERROR,
     re.compile(r"(?i)(?:^|/)(?:\.env(?:\.[\w.-]+)?|id_(?:rsa|dsa|ecdsa|ed25519)|[^/]*\."
                r"(?:pem|key|p12|pfx|jks|keystore|kdbx|ovpn|ppk|lic|gpg|asc))$"),
     "key material / licence / credential file"),
    ("file.capture", ERROR, re.compile(r"(?i)\.(?:pcapng|pcap|cap|har|etl|evtx|dmp|core)$"),
     "packet capture / HAR / dump (real traffic, cookies or memory)"),
    ("file.raw-log-or-config", ERROR, re.compile(r"(?i)\.(?:log|conf|cfg)$"),
     "raw log or device configuration backup"),
    ("file.denylist", ERROR, re.compile(r"^\.compliance/denylist"), "the denylist must never be committed"),
    ("file.needs-review", ERROR,
     re.compile(r"(?i)\.(?:pptx?|potx|pps[xm]?|pptm|docx?|dotx|docm|xlsx?|xlsm|xltx|xlsb|csv|tsv|pdf|msg|eml|"
                r"vsdx?|one|zip|7z|rar|tar|t?gz|bz2|xz|sqlite3?|db|bak|pst|ost)$"),
     "Office / data / archive file - review it, then list it in .compliance/policy.toml"),
]

OTHER_RULES = {
    "office.review-identities": "names of co-authors, reviewers or commenters inside an Office file",
    "office.author-metadata": "personal name in Office document properties",
    "office.sensitivity-label": "Office file carries a non-public sensitivity label",
    "pdf.author-metadata": "personal name in PDF metadata",
    "image.gps": "GPS position in image metadata",
    "image.author-metadata": "personal name in image metadata",
    "file.unscanned-binary": "binary file whose content cannot be scanned",
    "denylist.term": "customer / project name from the confidential denylist",
    "commit.author-email": "personal e-mail address as commit author / committer",
    "policy.stale-entry": "policy entry that no longer matches anything",
}


def rule_catalogue():
    cat = {}
    for r in TEXT_RULES:
        cat.setdefault(r.id, (r.severity, r.message))
    for rid, sev, _, msg in FILE_RULES:
        cat[rid] = (sev, msg)
    for rid, msg in OTHER_RULES.items():
        sev = WARNING if rid in ("file.unscanned-binary", "commit.author-email", "policy.stale-entry") else ERROR
        cat[rid] = (sev, msg)
    return cat


# --------------------------------------------------------------------------- policy

@dataclasses.dataclass
class Allow:
    rule: str
    path: str
    reason: str
    match: re.Pattern | None
    expires: datetime.date | None
    index: int
    hits: int = 0


class PolicyError(Exception):
    pass


class Context:
    def __init__(self, settings, allows, denylist):
        self.settings = settings
        self.allows = allows
        self.allowed_emails = {e.lower() for e in settings["allowed_emails"]}
        self.allowed_email_domains = [d.lower() for d in settings["allowed_email_domains"]]
        self.allowed_authors = {a.strip().lower() for a in settings["allowed_document_authors"]}
        self.commit_email_patterns = [p.lower() for p in settings["commit_email_patterns"]]
        self.denylist = denylist
        self.notes = []


def load_policy(path, today=None):
    today = today or datetime.date.today()
    settings, allows, notes = dict(DEFAULT_SETTINGS), [], []
    if not path.exists():
        return settings, allows, notes
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as e:
        raise PolicyError(f"{path.name}: invalid TOML ({e})")
    for key, value in data.get("settings", {}).items():
        if key not in DEFAULT_SETTINGS or not isinstance(value, list):
            raise PolicyError(f"{path.name}: unknown or non-list setting '{key}'")
        settings[key] = value
    known = rule_catalogue()
    for i, entry in enumerate(data.get("allow", []), 1):
        unknown = set(entry) - {"rule", "path", "reason", "match", "expires"}
        missing = [k for k in ("rule", "path", "reason") if not str(entry.get(k, "")).strip()]
        if unknown or missing:
            raise PolicyError(f"{path.name}: [[allow]] #{i}: unknown keys {sorted(unknown)} / missing {missing}")
        if not any(fnmatch.fnmatchcase(r, entry["rule"]) for r in known):
            raise PolicyError(f"{path.name}: [[allow]] #{i}: rule '{entry['rule']}' matches no known rule")
        try:
            match = re.compile(entry["match"]) if entry.get("match") else None
        except re.error as e:
            raise PolicyError(f"{path.name}: [[allow]] #{i}: invalid match regex ({e})")
        expires = entry.get("expires")
        if expires is not None and not isinstance(expires, datetime.date):
            raise PolicyError(f"{path.name}: [[allow]] #{i}: expires must be a date (YYYY-MM-DD)")
        if expires and expires < today:
            notes.append(f"[[allow]] #{i} ({entry['rule']} @ {entry['path']}) expired on {expires} and is ignored")
            continue
        allows.append(Allow(entry["rule"], entry["path"], entry["reason"], match, expires, i))
    return settings, allows, notes


def load_denylist():
    terms = []
    sources = [os.environ.get("COMPLIANCE_DENYLIST", "")]
    if LOCAL_DENYLIST.exists():
        sources.append(LOCAL_DENYLIST.read_text(encoding="utf-8"))
    for src in sources:
        for raw in src.splitlines():
            term = raw.strip()
            if term and not term.startswith("#") and len(term) >= 3:
                terms.append(term)
    return load_denylist_terms(dict.fromkeys(terms))


def load_denylist_terms(terms):
    return [re.compile(r"(?<!\w)" + r"[\s_-]+".join(map(re.escape, t.split())) + r"(?!\w)", re.I) for t in terms]


# --------------------------------------------------------------------------- scanners

def scan_text(text, path, ctx, where="", in_tree=True, with_lines=True):
    findings = []
    newlines = [i for i, c in enumerate(text) if c == "\n"] if with_lines else None

    def add(rid, sev, msg, m, value):
        line = bisect.bisect_right(newlines, m.start()) + 1 if with_lines else None
        findings.append(Finding(rid, sev, path, msg, line, value, where, in_tree))

    for r in TEXT_RULES:
        for m in r.regex.finditer(text):
            value = m.group(r.group)
            if r.check is None or r.check(m, ctx, value):
                add(r.id, r.severity, r.message, m, value)
    for n, rx in enumerate(ctx.denylist, 1):
        for m in rx.finditer(text):
            add("denylist.term", ERROR, f"matches confidential denylist entry #{n}", m, m.group(0))
    return findings


def scan_path_name(path, ctx, where="", in_tree=True):
    findings = []
    for rid, sev, rx, msg in FILE_RULES:
        if rx.search(path):
            findings.append(Finding(rid, sev, path, msg, None, "", where, in_tree))
    for n, rx in enumerate(ctx.denylist, 1):
        if rx.search(path):
            findings.append(Finding("denylist.term", ERROR, path, f"file name matches denylist entry #{n}",
                                    None, "", where, in_tree))
    return findings


XML_BREAK = re.compile(r"</(?:a:p|w:p|si|c|row|c:v|c:pt|p:txBody|Relationship)>|<a:br/>|<w:br/>|<w:tab/>")


def xml_text(xml):
    if "<Relationships" in xml:  # hyperlinks live in .rels targets
        xml = "\n".join(re.findall(r'Target="([^"]+)"[^>]*TargetMode="External"', xml))
        return html.unescape(xml)
    return html.unescape(re.sub(r"<[^>]+>", "", XML_BREAK.sub("\n", xml)))


def scan_office(path, data, ctx, where="", in_tree=True, depth=0):
    findings = []
    label = (where + "!" if where else "")

    def add(rid, msg, member, value=""):
        findings.append(Finding(rid, ERROR, path, msg, None, value, label + member, in_tree))

    try:
        z = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile:
        return [Finding("file.unscanned-binary", WARNING, path, "corrupt Office file", None, "", where, in_tree)]
    names = z.namelist()
    identity_members = set()
    for kind, rx in IDENTITY_PARTS.items():
        hits = [n for n in names if rx.search(n)]
        if not hits:
            continue
        identity_members.update(hits)
        people = set()
        for n in hits:
            people.update(re.findall(rb'\b(?:name|author|displayName|w:author|userId)="([^"]+)"', z.read(n)))
        add("office.review-identities",
            f"{kind} ({len(hits)} part(s), {len(people)} distinct identity value(s)) - "
            f"run scripts/sanitize_office.py", hits[0])
    for member, tags in (("docProps/core.xml", ("dc:creator", "cp:lastModifiedBy")), ("docProps/app.xml", ("Manager",))):
        if member in names:
            xml = z.read(member).decode("utf-8", "replace")
            for tag in tags:
                for value in re.findall(rf"<{tag}>([^<]*)</{tag}>", xml):
                    value = html.unescape(value).strip()
                    if value.lower() not in ctx.allowed_authors:
                        add("office.author-metadata", f"document property {tag} is not an allowed author "
                            "(settings.allowed_document_authors) - run scripts/sanitize_office.py", member, value)
    if "docProps/custom.xml" in names:
        xml = z.read("docProps/custom.xml").decode("utf-8", "replace")
        for label_name in re.findall(r'name="MSIP_Label_[^"]*_Name"[^>]*>\s*<vt:lpwstr>([^<]*)<', xml):
            if not re.search(r"(?i)public|öffentlich|publi[cq]ue", label_name):
                add("office.sensitivity-label", f"sensitivity label '{label_name}'", "docProps/custom.xml")
    if any(n.startswith("docMetadata/LabelInfo") for n in names):
        add("office.sensitivity-label", "Microsoft Purview sensitivity label present", "docMetadata/LabelInfo.xml")
    for member in names:
        if member in identity_members:
            continue
        if member.endswith((".xml", ".rels")) and not member.startswith("docProps/"):
            text = xml_text(z.read(member).decode("utf-8", "replace"))
            if text.strip():
                findings += scan_text(text, path, ctx, label + member, in_tree, with_lines=False)
        elif OFFICE_EXT.search(member) and depth < 2:
            findings += scan_office(path, z.read(member), ctx, label + member, in_tree, depth + 1)
    return findings


def scan_pdf(path, data, ctx, where="", in_tree=True):
    findings = []
    values = [v.decode("latin-1") for v in re.findall(rb"/Author\s*\(((?:[^()\\]|\\.)*)\)", data)]
    values += [v.decode("utf-8", "replace") for v in
               re.findall(rb"<(?:pdf:Author|dc:creator)>\s*(?:<rdf:Seq>\s*<rdf:li[^>]*>)?([^<]*)<", data)]
    for value in values:
        if value.strip().lower() not in ctx.allowed_authors:
            findings.append(Finding("pdf.author-metadata", ERROR, path, "PDF author metadata", None,
                                    value, where, in_tree))
    return findings


def _tiff_tags(tiff):
    """Return {tag: value} for IFD0, the Exif IFD and the GPS IFD of a TIFF/EXIF blob."""
    if tiff[:2] not in (b"II", b"MM"):
        return {}
    e = "<" if tiff[:2] == b"II" else ">"
    sizes = {1: 1, 2: 1, 3: 2, 4: 4, 5: 8, 7: 1, 9: 4, 10: 8}
    out = {}

    def read_ifd(off, prefix=""):
        if off <= 0 or off + 2 > len(tiff):
            return
        (count,) = struct.unpack(e + "H", tiff[off:off + 2])
        for k in range(min(count, 512)):
            p = off + 2 + 12 * k
            if p + 12 > len(tiff):
                return
            tag, typ, n = struct.unpack(e + "HHI", tiff[p:p + 8])
            size = sizes.get(typ, 1) * n
            raw = tiff[p + 8:p + 8 + size] if size <= 4 else None
            if raw is None:
                (voff,) = struct.unpack(e + "I", tiff[p + 8:p + 12])
                raw = tiff[voff:voff + size]
            out[prefix + str(tag)] = (typ, raw)
            if not prefix and tag in (0x8769, 0x8825):
                read_ifd(struct.unpack(e + "I", tiff[p + 8:p + 12])[0], f"{tag}:")

    read_ifd(struct.unpack(e + "I", tiff[4:8])[0])
    return out


def scan_image(path, data, ctx, where="", in_tree=True):
    tiff, findings = b"", []
    if data[:2] == b"\xff\xd8":
        i = data.find(b"Exif\x00\x00")
        tiff = data[i + 6:i + 6 + 65536] if i != -1 else b""
    elif data[:8] == b"\x89PNG\r\n\x1a\n":
        i = data.find(b"eXIf")
        tiff = data[i + 4:i + 4 + 65536] if i != -1 else b""
        for key, value in re.findall(rb"(?:tEXt|iTXt)(Author|Artist)\x00(?:\x00\x00\x00\x00)?([^\x00]{1,200})", data):
            if value.strip().decode("latin-1").lower() not in ctx.allowed_authors:
                findings.append(Finding("image.author-metadata", ERROR, path, f"PNG {key.decode()} text chunk",
                                        None, value.decode("latin-1"), where, in_tree))
    elif data[:4] in (b"II*\x00", b"MM\x00*"):
        tiff = data
    try:
        tags = _tiff_tags(tiff)
    except struct.error:
        tags = {}
    if any(k in tags for k in ("34853:1", "34853:2", "34853:3", "34853:4")):
        findings.append(Finding("image.gps", ERROR, path, "GPS position in EXIF metadata", None, "", where, in_tree))
    for key, label in (("315", "Artist"), ("40093", "XPAuthor"), ("34665:42032", "CameraOwnerName")):
        if key in tags:
            typ, raw = tags[key]
            value = (raw.decode("utf-16-le", "replace") if key == "40093" else raw.decode("latin-1")).strip("\x00 ")
            if value and value.lower() not in ctx.allowed_authors:
                findings.append(Finding("image.author-metadata", ERROR, path, f"EXIF {label}", None,
                                        value, where, in_tree))
    return findings


def scan_blob(path, data, ctx, where="", in_tree=True):
    findings = scan_path_name(path, ctx, where, in_tree)
    if len(data) > MAX_BLOB_BYTES:
        return findings + [Finding("file.unscanned-binary", WARNING, path, "file too large to scan",
                                   None, "", where, in_tree)]
    head = data[:8192]
    if data[:4] == b"PK\x03\x04" and OFFICE_EXT.search(path):
        findings += scan_office(path, data, ctx, where, in_tree)
    elif data[:5] == b"%PDF-":
        findings += scan_pdf(path, data, ctx, where, in_tree)
    elif data[:2] == b"\xff\xd8" or data[:8] == b"\x89PNG\r\n\x1a\n" or data[:4] in (b"II*\x00", b"MM\x00*"):
        findings += scan_image(path, data, ctx, where, in_tree)
    elif b"\x00" in head:
        findings.append(Finding("file.unscanned-binary", WARNING, path, "binary content was not scanned",
                                None, "", where, in_tree))
    else:
        findings += scan_text(data.decode("utf-8", "replace"), path, ctx, where, in_tree)
    return findings


# --------------------------------------------------------------------------- git sources

def git(*args, data=False):
    out = subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, check=False)
    if out.returncode != 0:
        raise PolicyError(f"git {' '.join(args)}: {out.stderr.decode(errors='replace').strip()}")
    return out.stdout if data else out.stdout.decode("utf-8", "replace")


def index_entries(paths=()):
    """(path, blob sha) for tracked files, from the index."""
    out = git("ls-files", "-s", "-z", "--", *paths)
    entries = []
    for rec in filter(None, out.split("\0")):
        meta, path = rec.split("\t", 1)
        mode, sha, _ = meta.split()
        if mode != "160000":
            entries.append((path, sha))
    return entries


def scan_tree(ctx, paths=()):
    findings = []
    if paths:
        files = []
        for p in paths:
            p = Path(p).resolve()
            items = [p] if p.is_file() else [f for f in p.rglob("*") if f.is_file() and ".git" not in f.parts]
            files += items
        for f in sorted(set(files)):
            rel = f.relative_to(ROOT).as_posix() if f.is_relative_to(ROOT) else str(f)
            findings += scan_blob(rel, f.read_bytes(), ctx)
        return findings, set()
    entries = index_entries()
    for path, _ in entries:
        f = ROOT / path
        if f.is_file():
            findings += scan_blob(path, f.read_bytes(), ctx)
    return findings, {sha for _, sha in entries}


def check_commit_email(ctx, email, label, role):
    if any(fnmatch.fnmatchcase(email.lower(), p) for p in ctx.commit_email_patterns):
        return []
    return [Finding("commit.author-email", WARNING, label, f"{role} e-mail is published with every commit - "
                    "use your GitHub noreply address (git config user.email)", None, email, "", False)]


def scan_staged(ctx):
    staged = [p for p in git("diff", "--cached", "--name-only", "-z", "--diff-filter=ACMRT").split("\0") if p]
    ident = re.search(r"<([^>]*)>", git("var", "GIT_AUTHOR_IDENT"))
    findings = check_commit_email(ctx, ident.group(1), "<git config user.email>", "commit author") if ident else []
    for path, sha in index_entries(staged) if staged else []:
        findings += scan_blob(path, git("cat-file", "blob", sha, data=True), ctx)
    return findings


def scan_commit_msg(ctx, path):
    """Commit message as git will store it: without comment lines and the `commit -v` diff."""
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    text = re.split(r"(?m)^# -+ >8 -+$", text)[0]
    text = "\n".join("" if line.startswith("#") else line for line in text.splitlines())
    return scan_text(text, "<commit message>", ctx, in_tree=False)


def scan_commits(ctx, rng, seen):
    findings = []
    for sha in git("rev-list", "--reverse", rng).split():
        short = sha[:7]
        meta = git("show", "-s", "--format=%ae%x00%ce%x00%B", sha).split("\0", 2)
        for role, email in (("author", meta[0]), ("committer", meta[1])):
            findings += check_commit_email(ctx, email, f"<commit {short}>", f"commit {role}")
        findings += scan_text(meta[2], f"<commit {short} message>", ctx, in_tree=False)
        parents = git("rev-list", "--parents", "-n", "1", sha).split()[1:]
        base = [parents[0]] if parents else ["--root"]
        diff = git("diff-tree", "-r", "-z", "--no-renames", "--no-commit-id", "--diff-filter=ACMT", *base, sha)
        recs = diff.split("\0")
        for meta_rec, path in zip(recs[0::2], recs[1::2]):
            fields = meta_rec.split()
            if len(fields) < 5 or fields[1] == "160000" or fields[3] in seen:
                continue
            seen.add(fields[3])
            for f in scan_blob(path, git("cat-file", "blob", fields[3], data=True), ctx,
                               where=f"commit {short}", in_tree=False):
                f.message += " - this version is already pushed: rotate/revoke it and rewrite the branch"
                findings.append(f)
    return findings


# --------------------------------------------------------------------------- reporting

def apply_policy(findings, ctx):
    for f in findings:
        for a in ctx.allows:
            if (fnmatch.fnmatchcase(f.rule, a.rule) and fnmatch.fnmatchcase(f.path, a.path)
                    and (a.match is None or a.match.search(f.match))):
                f.allowed_by = a
                a.hits += 1
                break
    stale = [a for a in ctx.allows if a.hits == 0]
    return [f for f in findings if not f.allowed_by], [f for f in findings if f.allowed_by], stale


def gh_escape(s, prop=False):
    s = s.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
    return s.replace(":", "%3A").replace(",", "%2C") if prop else s


def report(open_findings, accepted, stale, ctx, partial):
    order = {ERROR: 0, WARNING: 1}
    open_findings.sort(key=lambda f: (order[f.severity], f.path, f.line or 0, f.rule))
    for f in open_findings:
        print(f"{f.severity.upper():7} {f.rule:26} {f.location()}  {f.message}{f.shown()}")
    for a in stale if not partial else []:
        print(f"WARNING policy.stale-entry          .compliance/policy.toml  [[allow]] #{a.index} "
              f"({a.rule} @ {a.path}) matched nothing - remove it")
    for note in ctx.notes:
        print(f"NOTE    {note}")
    errors = sum(f.severity == ERROR for f in open_findings)
    warnings = len(open_findings) - errors + (0 if partial else len(stale))
    print(f"\ncompliance scan: {errors} error(s), {warnings} warning(s), {len(accepted)} finding(s) "
          f"accepted by .compliance/policy.toml")
    if errors:
        print("\nHow to resolve:\n"
              "  - remove the data: RFC 5737 IPs, example.com, DEMO serials, placeholder names, no real prices;\n"
              "  - Office files: python3 scripts/sanitize_office.py <file>;\n"
              "  - a genuine false positive: add an [[allow]] entry with a reason to .compliance/policy.toml;\n"
              "  - findings 'in commit ...' are already public on the pushed branch: revoke/rotate first,\n"
              "    then rewrite the branch (see README, section Compliance-Check).")
    if os.environ.get("GITHUB_ACTIONS") == "true":
        for f in open_findings:
            props = f"title={gh_escape(f.rule, True)}"
            if f.in_tree and not f.where:
                props = f"file={gh_escape(f.path, True)}" + (f",line={f.line}" if f.line else "") + "," + props
            print(f"::{f.severity} {props}::{gh_escape(f.location() + ': ' + f.message + f.shown())}")
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as out:
            icon = "❌" if errors else ("⚠️" if warnings else "✅")
            out.write(f"### {icon} Compliance scan: {errors} error(s), {warnings} warning(s)\n\n")
            if open_findings:
                out.write("| Severity | Rule | Location | Finding |\n|---|---|---|---|\n")
                for f in open_findings:
                    loc = f.location().replace("|", "\\|")
                    out.write(f"| {f.severity} | `{f.rule}` | `{loc}` | {f.message}{f.shown()} |\n")
                out.write("\n")
            if stale and not partial:
                out.write("Stale policy entries: " + ", ".join(f"#{a.index}" for a in stale) + "\n\n")
            out.write(f"{len(accepted)} finding(s) accepted by `.compliance/policy.toml`.\n")
    return errors, warnings


# --------------------------------------------------------------------------- self-test

def self_test():
    ctx = Context(DEFAULT_SETTINGS | {"allowed_emails": [j("noreply", "@anthropic.com")],
                                      "allowed_document_authors": ["", "Fortinet"]},
                  [], load_denylist_terms(["Acme Muster AG"]))

    def card(prefix):
        for d in range(10):
            if luhn_ok(prefix + str(d)):
                return prefix + str(d)

    def ahv(prefix):
        for d in range(10):
            if ean13_ok(prefix + str(d)):
                return prefix + str(d)

    a = ahv("756123456789")
    hits = [
        ("secret.private-key", j("-----BEGIN ", "RSA PRIVATE KEY-----")),
        ("secret.license-file", j("-----BEGIN FGT VM ", "LICENSE-----")),
        ("secret.github-token", j("gh", "p_", "A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8")),
        ("secret.aws-key", j("AKIA", "Z7Q3K2M4N8P5R6T1")),
        ("secret.anthropic-key", j("sk-", "ant-api03-", "Qx7Lm2Pz9Rt4Vb8Nc3Kd6Wf1")),
        ("secret.slack-token", j("xox", "b-123456789012-AbCdEfGhIj")),
        ("secret.webhook-url", j("https://hooks.slack", ".com/services/", "T0000/B0000/AbC123dEf456")),
        ("secret.jwt", j("eyJ", "hbGciOiJIUzI1NiJ9.", "eyJ", "zdWIiOiIxMjM0NSJ9.", "c2lnbmF0dXJlLXZhbHVl")),
        ("secret.url-credentials", j("https://admin:", "Fz7!kq29Lm", "@fw.acme-ag.ch/api")),
        ("secret.bearer-token", j("Authorization: Bearer ", "q8Z2xL7mP4vR9tK1wN6sQ3")),
        ("secret.fortios-enc", j("    set password ENC ", "SH2a8F3kL0pQ9zX7cV1bN4mW2eR6tY")),
        ("secret.fortios-plaintext", j("    set psksecret ", "Zr8#vL2qP9xT")),
        ("secret.assignment", j('api_key = "', 'q8Z2xL7mP4vR9tK1wN6s"')),
        ("pii.email", j("max.muster", "@", "acme-ag.ch")),
        ("pii.phone", j("+41 44 ", "123 45 67")),
        ("pii.phone", j("Tel. 079 ", "123 45 67")),
        ("pii.iban", j("CH93 0076 ", "2011 6238 5295 7")),
        ("pii.ahv", j(a[:3], ".", a[3:7], ".", a[7:11], ".", a[11:])),
        ("pii.payment-card", " ".join(card("400012345678901")[i:i + 4] for i in range(0, 16, 4))),
        ("pii.mac-address", j('srcmac="3c:22:fb:7a:', '19:e4"')),
        ("network.public-ip", j("dstip=", "185.12.", "64.7")),
        ("fortinet.serial", j('devid="FG100F', 'TK21012345"')),
        ("fortinet.cloud-tenant", j("ad-2731904-", "5521.forticlient-emsproxy.forticloud.com")),
        ("internal.engagement-note", j("**Personal ", "note for Max**: see the eval")),
        ("internal.engagement-note", j("Note from prior ", "engagements: WCCP needs care")),
        ("internal.engagement-note", j("per the employee ", "handbook rule")),
        ("confidential.marking", j("Fortinet ", "Confidential")),
        ("confidential.marking", j("STRICTLY CONFIDENTIA", "L")),
        ("confidential.marking", j("Nur für den internen ", "Gebrauch")),
        ("confidential.marking", j("Strictement confidenti", "el")),
        ("confidential.marking", j("TLP:", "AMBER")),
        ("confidential.nda", j("shared under N", "DA")),
        ("confidential.not-public", j("not yet ", "publicly announced")),
        ("internal.link", j("https://fortinet.share", "point.com/sites/x")),
        ("internal.link", j("https://acme.my.sales", "force.com/006")),
        ("commercial.sfdc-id", j("Opportunity ", "0065g00000", "AbCdE")),
        ("commercial.price", j("FG-100F | 1 | CH", "F 4'250.00")),
        ("commercial.amount", j("Budget: CH", "F 12'000")),
        ("commercial.discount", j("Rab", "att 35", "%")),
        ("denylist.term", j("Kunde: Acme ", "Muster AG")),
    ]
    clean = [
        j("ops@example.com, git@github.com:FreddyMcFett/fortiskill.git, noreply", "@anthropic.com, icon@2x.png"),
        'devid="FGVMEVDEMO0000001" devname="DEMO-HQ-FGT-01" logver=0800000167 eventtime=1785568442847113221',
        "set password ENC <encrypted>\n    set psksecret <your-psk>\n    set password fortinet",
        'ansible_password: "{{ vault_fgt_token }}"\ntoken    = var.fortigate_api_token\napi_key=args.api_key',
        "# Optional repo secret: customer/project names, one per line",
        'srcip=10.10.20.25 dstip=203.0.113.10 dns=8.8.8.8 "srcswversion": "96.86.0.85" tz="+0200"',
        "a customer's confidential data; Medical Restricted Internet; internal margins",
        "placeholder MACs like 11:11:11:11:11:11 or 00:00:5e:00:53:01, c8:89:f3:11:22:33",
        "UID,Quantity,Disti Discount,Quote Line Item Notes; Listenpreis exkl. Rabatt/MwSt.",
        "https://docs.fortinet.com/document/fortigate/7.6.6/administration-guide FortiOS 7.6.6",
        "FC-10-F100F-950-02-12 FG-100F FortiGate 100F, 2026-08-01 09:14:02, port 443, 51204",
        "Sheet1!$C$2:$C$21 and $A$10, shell args $1 $2; FG-100F row",
        j("fctems ad-1000001-", "0001.forticlient-emsproxy.forticloud.com; confirmed against the lab logs"),
    ]
    failed = 0
    for rid, sample in hits:
        got = {f.rule for f in scan_text(sample, "<self-test>", ctx)}
        if rid not in got:
            failed += 1
            print(f"FAIL  expected {rid} for sample #{hits.index((rid, sample)) + 1}, got {sorted(got)}")
    for n, sample in enumerate(clean, 1):
        got = sorted({f.rule for f in scan_text(sample, "<self-test>", ctx)})
        if got:
            failed += 1
            print(f"FAIL  clean sample #{n} produced {got}")
    pptx = io.BytesIO()
    with zipfile.ZipFile(pptx, "w") as z:
        z.writestr("[Content_Types].xml", "<Types/>")
        z.writestr("docProps/core.xml", "<cp:coreProperties><dc:creator>Erika Muster</dc:creator>"
                   "<cp:lastModifiedBy>Fortinet</cp:lastModifiedBy></cp:coreProperties>")
        z.writestr("ppt/changesInfos/changesInfo1.xml", '<pc:chgData name="Erika Muster" userId="x"/>')
        z.writestr("ppt/slides/slide1.xml", j("<a:p><a:r><a:t>Fortinet Confid", "ential</a:t></a:r></a:p>"))
    got = {f.rule for f in scan_blob("deck.pptx", pptx.getvalue(), ctx)}
    for rid in ("file.needs-review", "office.review-identities", "office.author-metadata", "confidential.marking"):
        if rid not in got:
            failed += 1
            print(f"FAIL  office sample: expected {rid}, got {sorted(got)}")
    total = len(hits) + len(clean) + 4
    print(f"self-test: {total - failed}/{total} passed")
    return 1 if failed else 0


# --------------------------------------------------------------------------- main

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="*", help="scan only these files/directories instead of all tracked files")
    ap.add_argument("--staged", action="store_true", help="scan staged content only (pre-commit hook)")
    ap.add_argument("--commits", metavar="A..B", help="also scan every commit in this range")
    ap.add_argument("--commit-msg", metavar="FILE", help="scan a commit message file (commit-msg hook)")
    ap.add_argument("--env-text", metavar="VAR", action="append", default=[],
                    help="also scan the text of this environment variable (repeatable)")
    ap.add_argument("--fail-on-warning", action="store_true", help="exit 1 on warnings too")
    ap.add_argument("--list-rules", action="store_true", help="print the rule catalogue and exit")
    ap.add_argument("--self-test", action="store_true", help="check the rules against built-in samples")
    args = ap.parse_args(argv)

    if args.list_rules:
        for rid, (sev, msg) in sorted(rule_catalogue().items()):
            print(f"{rid:28} {sev:8} {msg}")
        return 0
    if args.self_test:
        return self_test()
    try:
        settings, allows, notes = load_policy(POLICY_FILE)
        ctx = Context(settings, allows, load_denylist())
        ctx.notes = notes
        findings, seen = [], set()
        partial = bool(args.staged or args.paths or args.commit_msg)
        if args.commit_msg:
            findings += scan_commit_msg(ctx, args.commit_msg)
        if args.staged:
            findings += scan_staged(ctx)
        elif not args.commit_msg:
            tree_findings, seen = scan_tree(ctx, args.paths)
            findings += tree_findings
        if args.commits:
            findings += scan_commits(ctx, args.commits, seen)
        for var in args.env_text:
            findings += scan_text(os.environ.get(var, ""), f"<{var}>", ctx, in_tree=False)
    except PolicyError as e:
        print(f"compliance scan: {e}", file=sys.stderr)
        return 2
    open_findings, accepted, stale = apply_policy(findings, ctx)
    errors, warnings = report(open_findings, accepted, stale, ctx, partial)
    return 1 if errors or (args.fail_on_warning and warnings) else 0


if __name__ == "__main__":
    sys.exit(main())
