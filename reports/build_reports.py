"""Build PDF reports from Markdown sources.

Converts ``reports/src/<name>.md`` to ``reports/<name>.pdf`` by rendering the
Markdown to HTML (Python-Markdown) with an A4 print stylesheet and printing it
with headless Microsoft Edge.

Usage:
    python reports/build_reports.py                    # build every reports/src/*.md
    python reports/build_reports.py outline_report     # build selected reports
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    import markdown
except ImportError:  # pragma: no cover - guidance for first-time users
    sys.exit("The 'markdown' package is required: pip install markdown")

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
EDGE_CANDIDATES = [
    Path("C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"),
    Path("C:/Program Files/Microsoft/Edge/Application/msedge.exe"),
]

CSS = """
@page { size: A4; margin: 22mm 20mm 22mm 22mm; }
html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { font-family: "Times New Roman", "Liberation Serif", "DejaVu Serif", serif;
       font-size: 11.5pt; line-height: 1.45; color: #111; text-align: justify;
       hyphens: auto; }
h1, h2, h3, h4 { font-family: "Times New Roman", serif; color: #0b2a4a;
                 text-align: left; page-break-after: avoid; break-after: avoid; }
h1 { font-size: 20pt; margin: 0 0 10pt; }
h2 { font-size: 15pt; border-bottom: 1px solid #9fb3c8; padding-bottom: 2pt;
     margin-top: 20pt; }
h3 { font-size: 12.5pt; margin-top: 14pt; }
h4 { font-size: 11.5pt; font-style: italic; }
p, li { orphans: 3; widows: 3; }
table { border-collapse: collapse; width: 100%; margin: 8pt 0 12pt;
        font-size: 10pt; page-break-inside: auto; text-align: left; }
tr { page-break-inside: avoid; break-inside: avoid; }
th, td { border: 1px solid #8a8a8a; padding: 3pt 5pt; vertical-align: top; }
th { background: #e6edf4; }
code { font-family: Consolas, "Courier New", monospace; font-size: 9.5pt; }
pre { background: #f5f5f5; border: 1px solid #ddd; padding: 6pt;
      font-size: 9pt; line-height: 1.25; white-space: pre-wrap;
      page-break-inside: avoid; }
blockquote { border-left: 3px solid #9fb3c8; margin: 8pt 0; padding: 2pt 10pt;
             color: #333; background: #f7f9fb; }
img { max-width: 100%; display: block; margin: 8pt auto; }
figure, .figure { text-align: center; page-break-inside: avoid; }
.caption { text-align: center; font-size: 10pt; font-style: italic; }
.titlepage { text-align: center; page-break-after: always; break-after: page;
             padding-top: 30mm; }
.titlepage h1 { text-align: center; font-size: 22pt; }
.titlepage p { text-align: center; }
.titlepage table { width: 85%; margin: 14pt auto; font-size: 11pt; }
.toc { page-break-after: always; break-after: page; }
.toc ul { list-style: none; padding-left: 14pt; }
.toctitle { font-size: 15pt; font-weight: bold; color: #0b2a4a; margin-bottom: 8pt; }
.toc a { color: #111; text-decoration: none; }
.pagebreak { page-break-before: always; break-before: page; }
.refs p, .refs li { text-align: left; }
"""

TEMPLATE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>{title}</title>
<base href="{base}">
<style>{css}</style></head>
<body>
{body}
</body></html>
"""


def find_edge() -> Path:
    env = os.environ.get("MSEDGE_PATH")
    candidates = ([Path(env)] if env else []) + EDGE_CANDIDATES
    for path in candidates:
        if path.is_file():
            return path
    found = shutil.which("msedge")
    if found:
        return Path(found)
    sys.exit("Microsoft Edge (msedge.exe) not found; set MSEDGE_PATH.")


def render_html(md_path: Path) -> str:
    text = md_path.read_text(encoding="utf-8")
    body = markdown.markdown(
        text,
        extensions=["tables", "fenced_code", "toc", "md_in_html", "attr_list"],
        extension_configs={"toc": {"title": "Table of Contents", "toc_depth": "2-3"}},
        output_format="html5",
    )
    match = re.search(r"<h1[^>]*>(.*?)</h1>", body, re.S)
    title = re.sub(r"<[^>]+>", "", match.group(1)) if match else md_path.stem
    base = md_path.parent.resolve().as_uri() + "/"
    return TEMPLATE.format(title=title, base=base, css=CSS, body=body)


def count_pages(pdf: Path) -> int:
    data = pdf.read_bytes()
    return len(re.findall(rb"/Type\s*/Page(?![s\w])", data))


def build(name: str, edge: Path) -> Path:
    md_path = SRC / f"{name}.md"
    if not md_path.is_file():
        raise FileNotFoundError(md_path)
    out_pdf = ROOT / f"{name}.pdf"
    # Write the temporary HTML next to the Markdown so relative image paths
    # (e.g. ../../docs/architecture.png) resolve; the <base> tag is a backup.
    html_path = md_path.with_name(f"_{name}.build.html")
    html_path.write_text(render_html(md_path), encoding="utf-8")
    profile = tempfile.mkdtemp(prefix="edge-pdf-")
    try:
        if out_pdf.exists():
            out_pdf.unlink()
        cmd = [
            str(edge), "--headless", "--disable-gpu", "--no-first-run",
            "--no-pdf-header-footer", "--print-to-pdf-no-header",
            f"--user-data-dir={profile}",
            f"--print-to-pdf={out_pdf}",
            html_path.resolve().as_uri(),
        ]
        subprocess.run(cmd, check=False, timeout=180,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    finally:
        html_path.unlink(missing_ok=True)
        shutil.rmtree(profile, ignore_errors=True)
    if not out_pdf.is_file() or out_pdf.stat().st_size == 0:
        raise RuntimeError(f"Edge did not produce {out_pdf}")
    return out_pdf


def main(argv: list[str]) -> int:
    names = [Path(a).stem for a in argv] or sorted(p.stem for p in SRC.glob("*.md"))
    edge = find_edge()
    status = 0
    for name in names:
        try:
            pdf = build(name, edge)
            pages = count_pages(pdf)
            print(f"[ok] {pdf.relative_to(ROOT.parent)}  ({pages} pages, "
                  f"{pdf.stat().st_size // 1024} KiB)")
            if pages <= 1:
                print(f"[warn] {pdf.name} has only {pages} page(s)")
                status = 1
        except Exception as exc:  # report and continue with remaining files
            print(f"[fail] {name}: {exc}")
            status = 1
    return status


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
