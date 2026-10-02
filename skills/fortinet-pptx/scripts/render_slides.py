#!/usr/bin/env python3
"""Render a .pptx to per-slide JPEGs for visual QA.

Portable across machines: locates soffice even when it's not on PATH
(common on macOS installs), and falls back to PyMuPDF for the PDF->JPEG
step when Poppler's pdftoppm isn't installed. Prefers pdftoppm when it
is present since it's the faster, more battle-tested path.

Usage: python3 render_slides.py <deck.pptx> <output_dir> [dpi]
"""
import shutil
import subprocess
import sys
from pathlib import Path

SOFFICE_CANDIDATES = [
    "soffice",
    "/Applications/LibreOffice.app/Contents/MacOS/soffice",
    "/usr/bin/soffice",
    "/usr/local/bin/soffice",
    "/opt/homebrew/bin/soffice",
    r"C:\Program Files\LibreOffice\program\soffice.exe",
]


def find_soffice():
    for candidate in SOFFICE_CANDIDATES:
        found = shutil.which(candidate) if "/" not in candidate and "\\" not in candidate else candidate
        if found and Path(found).exists():
            return found
    raise FileNotFoundError(
        "soffice not found. Install LibreOffice, or if it's installed but not "
        "on PATH, symlink its soffice binary into a directory on PATH."
    )


def pptx_to_pdf(pptx_path, out_dir):
    soffice = find_soffice()
    subprocess.run(
        [soffice, "--headless", "--convert-to", "pdf", "--outdir", str(out_dir), str(pptx_path)],
        check=True,
        capture_output=True,
        text=True,
    )
    pdf_path = out_dir / (pptx_path.stem + ".pdf")
    if not pdf_path.exists():
        raise RuntimeError(f"soffice ran but {pdf_path} was not produced")
    return pdf_path


def pdf_to_jpegs(pdf_path, out_dir, dpi):
    if shutil.which("pdftoppm"):
        subprocess.run(
            ["pdftoppm", "-jpeg", "-r", str(dpi), str(pdf_path), str(out_dir / "slide")],
            check=True,
        )
    else:
        import fitz  # PyMuPDF

        doc = fitz.open(str(pdf_path))
        pad = len(str(doc.page_count))
        for i, page in enumerate(doc, start=1):
            pix = page.get_pixmap(dpi=dpi)
            pix.save(str(out_dir / f"slide-{str(i).zfill(pad)}.jpg"))


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    pptx_path = Path(sys.argv[1]).expanduser().resolve()
    out_dir = Path(sys.argv[2]).expanduser().resolve()
    dpi = int(sys.argv[3]) if len(sys.argv) > 3 else 150
    out_dir.mkdir(parents=True, exist_ok=True)

    for stale in out_dir.glob("slide-*.jpg"):
        stale.unlink()

    pdf_path = pptx_to_pdf(pptx_path, out_dir)
    pdf_to_jpegs(pdf_path, out_dir, dpi)

    jpegs = sorted(out_dir.glob("slide-*.jpg"))
    print(f"Rendered {len(jpegs)} slides to {out_dir}")
    for j in jpegs:
        print(j)


if __name__ == "__main__":
    main()
