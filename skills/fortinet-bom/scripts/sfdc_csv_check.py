#!/usr/bin/env python3
"""Validate an SFDC Quote Lines import CSV (see references/sfdc-import.md).

Checks:
  - header is exactly: UID,Quantity,Disti Discount,Quote Line Item Notes
  - file is UTF-8 WITHOUT BOM, CRLF line endings
  - every UID ends with EMEA (warns per row otherwise)
  - no duplicate UIDs (importer expects one row per SKU)
  - Quantity is a positive integer on every row
  - with --pricelist: every base SKU (UID minus EMEA) exists in the DataSet sheet

Usage:
  python sfdc_csv_check.py <import.csv> [--pricelist fortinet-pricelist.xlsx]

Exit code 1 on any hard failure (header/BOM/duplicates/missing SKU), 0 otherwise.
"""
import sys, csv, io, argparse

EXPECTED_HEADER = ["UID", "Quantity", "Disti Discount", "Quote Line Item Notes"]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csvfile")
    ap.add_argument("--pricelist")
    a = ap.parse_args()

    raw = open(a.csvfile, "rb").read()
    fail = False
    if raw.startswith(b"\xef\xbb\xbf"):
        print("FAIL: file has a UTF-8 BOM — UID column will not match on import"); fail = True
    if b"\r\n" not in raw:
        print("WARN: no CRLF line endings found (reference exports use CRLF)")

    rows = list(csv.reader(io.StringIO(raw.decode("utf-8-sig"))))
    rows = [r for r in rows if any(c.strip() for c in r)]
    if not rows or rows[0] != EXPECTED_HEADER:
        print(f"FAIL: header is {rows[0] if rows else 'missing'!r}, expected {EXPECTED_HEADER!r}"); fail = True

    seen, base_skus = {}, []
    for i, r in enumerate(rows[1:], start=2):
        if len(r) != 4:
            print(f"FAIL: line {i}: {len(r)} columns (expected 4)"); fail = True; continue
        uid, qty = r[0].strip(), r[1].strip()
        if not uid.endswith("EMEA"):
            print(f"WARN: line {i}: UID {uid!r} does not end with EMEA")
            base_skus.append(uid)
        else:
            base_skus.append(uid[:-4])
        if uid in seen:
            print(f"FAIL: line {i}: duplicate UID {uid!r} (first at line {seen[uid]})"); fail = True
        seen[uid] = i
        if not qty.isdigit() or int(qty) <= 0:
            print(f"FAIL: line {i}: Quantity {qty!r} is not a positive integer"); fail = True

    if a.pricelist:
        sys.path.insert(0, __file__.rsplit("/", 1)[0])
        from pricelist_lookup import load_rows
        known = {row[0] for row in load_rows(a.pricelist)}
        for sku in base_skus:
            if sku not in known:
                print(f"FAIL: base SKU {sku!r} not found in price list"); fail = True

    n = len(rows) - 1
    print(f"{'FAILED' if fail else 'OK'}: {n} data rows checked" + (", SKUs verified against price list" if a.pricelist else ""))
    sys.exit(1 if fail else 0)

if __name__ == "__main__":
    main()
