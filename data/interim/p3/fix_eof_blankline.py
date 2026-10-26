"""Remove the extra blank line at EOF flagged by `git diff --check`.

Preserves each file's existing line-ending style (README.md is CRLF, the reports
are LF) and touches nothing but the trailing newlines.

Run: python data/interim/p3/fix_eof_blankline.py
"""
import pathlib

ROOT = pathlib.Path(r"C:\Major")
TARGETS = ["README.md", "docs/data_quality_report.md"]

for rel in TARGETS:
    p = ROOT / rel
    raw = p.read_bytes()
    crlf = b"\r\n" in raw
    eol = b"\r\n" if crlf else b"\n"
    stripped = raw.rstrip(b"\r\n")
    new = stripped + eol
    if new == raw:
        print(f"{rel}: already clean")
        continue
    removed = len(raw) - len(stripped)
    p.write_bytes(new)
    print(f"{rel}: stripped {removed} trailing newline byte(s); "
          f"now ends with exactly one {'CRLF' if crlf else 'LF'}")
