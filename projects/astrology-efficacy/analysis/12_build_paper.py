"""
12_build_paper.py — Render paper/manuscript.md to .docx and .pdf.

Kept as a pipeline stage rather than a remembered shell incantation, so the
deliverables regenerate with everything else and the font/engine choices are
recorded instead of being rediscovered.

Two details that are easy to get wrong:

  * The PDF is built with xelatex rather than pdflatex because the manuscript
    contains Unicode that pdflatex cannot set (minus signs, subscripts such as
    BF01, set membership, degree and times signs).
  * The main font is Cambria. Segoe UI and Latin Modern were both tried and both
    dropped glyphs -- Segoe UI has no set-membership sign, Latin Modern missed 29
    characters. Cambria rendered the manuscript with zero missing-glyph warnings.
    FONT_CANDIDATES is tried in order, so the build still succeeds elsewhere.

Skipped with a warning (not an error) if pandoc or a LaTeX engine is absent:
the analysis must not fail because a typesetting tool is missing.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

PROJ = Path(__file__).resolve().parent.parent
PAPER = PROJ / "paper"
MD = PAPER / "manuscript.md"
BIB = PROJ / "literature" / "references.bib"

FONT_CANDIDATES = ["Cambria", "Charis SIL", "DejaVu Serif", "Times New Roman"]

COMMON = [
    "--citeproc",
    f"--bibliography={BIB}",
]

PDF_OPTS = [
    "--pdf-engine=xelatex",
    "-V", "sansfont=Calibri",
    "-V", "monofont=Consolas",
    "-V", "geometry:margin=1in",
    "-V", "fontsize=11pt",
    "-V", "linestretch=1.15",
    "-V", "colorlinks=true",
    "-V", "linkcolor=NavyBlue",
    "-V", "urlcolor=NavyBlue",
    "--toc", "--toc-depth=2",
]


def run(cmd: list[str]) -> tuple[int, str]:
    r = subprocess.run(cmd, cwd=str(PAPER), capture_output=True, text=True)
    return r.returncode, (r.stderr or "") + (r.stdout or "")


def main() -> int:
    if not MD.exists():
        print(f"  {MD} not found — nothing to build.")
        return 0
    if shutil.which("pandoc") is None:
        print("  pandoc not found — skipping .docx/.pdf build "
              "(manuscript.md is the source of record).")
        return 0

    code, out = run(["pandoc", MD.name, *COMMON, "-o", "manuscript.docx"])
    if code == 0:
        print(f"  manuscript.docx  "
              f"{(PAPER / 'manuscript.docx').stat().st_size / 1024:.0f} KB")
    else:
        print(f"  docx build FAILED:\n{out[:800]}")

    if shutil.which("xelatex") is None:
        print("  xelatex not found — skipping PDF. Install a LaTeX distribution "
              "(MiKTeX or TeX Live) to enable it.")
        return 0

    for font in FONT_CANDIDATES:
        code, out = run(["pandoc", MD.name, *COMMON, *PDF_OPTS,
                         "-V", f"mainfont={font}", "-o", "manuscript.pdf"])
        if code == 0:
            missing = out.count("Missing character")
            print(f"  manuscript.pdf   "
                  f"{(PAPER / 'manuscript.pdf').stat().st_size / 1024:.0f} KB "
                  f"[{font}]"
                  + (f"  WARNING: {missing} missing glyphs" if missing else ""))
            if missing == 0:
                return 0
            print(f"    trying the next font for full glyph coverage")
        else:
            print(f"    {font}: build failed, trying next")
    print("  PDF build did not produce a clean render with any candidate font.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
