#!/usr/bin/env python3
"""Strip personal metadata from Office files before they are committed.

Removes what scripts/compliance_scan.py reports as office.review-identities and
office.author-metadata:

  - PowerPoint co-authoring history (ppt/changesInfos/*, ppt/revisionInfo.xml) and
    PowerPoint comments (ppt/comments/*, ppt/commentAuthors.xml, ppt/authors.xml),
    including their relationships and content-type overrides;
  - author fields in docProps/core.xml (dc:creator, cp:lastModifiedBy -> --author)
    and docProps/app.xml (Manager -> empty);
  - the same in embedded Office files (charts' workbooks, OLE embeddings).

Word and Excel comments are anchored in the document body and cannot be removed
safely by deleting parts; for those the script stops and asks for Review -> Delete
all comments / File -> Info -> Inspect Document in Office. Sensitivity labels are
reported, never removed (classification is a human decision).

  python3 scripts/sanitize_office.py FILE [FILE ...]          # rewrite in place
  python3 scripts/sanitize_office.py --check FILE [FILE ...]  # report only, exit 1 if dirty

Stdlib only.
"""
import argparse
import html
import io
import posixpath
import re
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from compliance_scan import IDENTITY_PARTS, OFFICE_EXT  # noqa: E402

REMOVABLE = re.compile(r"^(?:ppt/changesInfos/|ppt/revisionInfo\.xml$|ppt/comments/|"
                       r"ppt/commentAuthors\.xml$|ppt/authors\.xml$)")
REL_RE = re.compile(r"<Relationship\b[^>]*/>")
OVERRIDE_RE = re.compile(r"<Override\b[^>]*/>")


def rels_source_dir(rels_name):
    """'ppt/slides/_rels/slide1.xml.rels' -> 'ppt/slides'."""
    return posixpath.dirname(posixpath.dirname(rels_name))


def sanitize(data, author, changes, label=""):
    zin = zipfile.ZipFile(io.BytesIO(data))
    names = zin.namelist()
    removed = {n for n in names if REMOVABLE.search(n)}
    removed |= {n for n in names if any(n.startswith(posixpath.dirname(r) + "/_rels/" + posixpath.basename(r))
                                        for r in removed)}
    blocked = [n for kind, rx in IDENTITY_PARTS.items() for n in names if rx.search(n) and n not in removed]
    if blocked:
        raise SystemExit(f"{label or 'file'}: Word/Excel comments or people lists ({', '.join(blocked[:3])}) - "
                         "remove them in Office (Review -> Delete all comments, File -> Info -> Inspect Document)")
    for n in sorted(removed):
        changes.append(f"{label}removed {n}")
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as zout:
        for info in zin.infolist():
            if info.filename in removed:
                continue
            body = zin.read(info.filename)
            name = info.filename
            if name.endswith(".rels") and removed:
                base = rels_source_dir(name)
                xml = body.decode("utf-8")

                def keep(m):
                    rel = m.group(0)
                    if 'TargetMode="External"' in rel:
                        return rel
                    target = re.search(r'Target="([^"]+)"', rel).group(1)
                    path = target.lstrip("/") if target.startswith("/") else posixpath.normpath(
                        posixpath.join(base, target))
                    return "" if path in removed else rel

                new = REL_RE.sub(keep, xml)
                if new != xml:
                    changes.append(f"{label}dropped relationships in {name}")
                    body = new.encode("utf-8")
            elif name == "[Content_Types].xml" and removed:
                xml = body.decode("utf-8")
                new = OVERRIDE_RE.sub(lambda m: "" if re.search(r'PartName="/([^"]+)"', m.group(0)).group(1)
                                      in removed else m.group(0), xml)
                if new != xml:
                    changes.append(f"{label}dropped content-type overrides")
                    body = new.encode("utf-8")
            elif name == "docProps/core.xml":
                xml = body.decode("utf-8")
                new = xml
                for tag in ("dc:creator", "cp:lastModifiedBy"):
                    new = re.sub(rf"<{tag}>[^<]*</{tag}>|<{tag}/>", f"<{tag}>{html.escape(author)}</{tag}>", new)
                if new != xml:
                    changes.append(f"{label}set author fields in {name} to '{author}'")
                    body = new.encode("utf-8")
            elif name == "docProps/app.xml":
                xml = body.decode("utf-8")
                new = re.sub(r"<Manager>[^<]*</Manager>", "<Manager></Manager>", xml)
                if new != xml:
                    changes.append(f"{label}cleared Manager in {name}")
                    body = new.encode("utf-8")
            elif name == "docProps/custom.xml" and b"MSIP_Label_" in body:
                changes.append(f"{label}NOTE sensitivity label present in {name} - left as is")
            elif OFFICE_EXT.search(name):
                body = sanitize(body, author, changes, f"{label}{name}: ")
            zout.writestr(info, body)
    return out.getvalue()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+", type=Path)
    ap.add_argument("--author", default="Fortinet",
                    help="value for dc:creator / cp:lastModifiedBy (default: Fortinet; must be listed in "
                         "settings.allowed_document_authors of .compliance/policy.toml)")
    ap.add_argument("--check", action="store_true", help="only report what would change; exit 1 if anything would")
    args = ap.parse_args()
    dirty = False
    for f in args.files:
        if not OFFICE_EXT.search(f.name):
            print(f"{f}: not an Office Open XML file, skipped")
            continue
        changes = []
        original = f.read_bytes()
        result = sanitize(original, args.author, changes)
        real = [c for c in changes if "NOTE" not in c]
        for c in changes:
            print(f"{f}: {c}")
        if real:
            dirty = True
            if not args.check:
                f.write_bytes(result)
        print(f"{f}: {'clean' if not real else ('would change' if args.check else 'sanitized')}")
    return 1 if args.check and dirty else 0


if __name__ == "__main__":
    sys.exit(main())
