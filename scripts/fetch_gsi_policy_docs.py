"""Download the official GSI/NGDR documents that establish the 1:50K geology
product and its access terms, as evidence for the source notes and manifest.

  1. GSI Data Sharing and Accessibility Policy 2019 (hosted on the NGDR portal):
     section 7.1 defines the compiled 1:50K geological mapping data, its
     WMS/WFS public services and its registered-user condition.
  2. NGDR brochure (Ministry of Mines): lists the "Standard Geological Map
     (1:50K)" product line (5,087 toposheets, 32.7 lakh sq km).

Both are saved UNCHANGED under data/raw/geology/gsi_policy/ with sha256; the
policy's section 7.1 text is extracted to data/interim/gsi_geology/
policy_2019_section71.txt for precise citation.

Run:  python scripts/fetch_gsi_policy_docs.py
"""
from __future__ import annotations

import hashlib
import pathlib
import re
import sys

import requests

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "geology" / "gsi_policy"
INTERIM = ROOT / "data" / "interim" / "gsi_geology"
H = {"User-Agent": "Mozilla/5.0 (RESQAI academic research probe)"}

DOCS = [
    ("Data_Dissemination_policy_2019.pdf",
     "https://geodataindia.gov.in/assets/Document_Pdf/4.%20Data%20Dissemination%20policy%202019.pdf"),
    ("NGDR_brochure_mines_gov_in.pdf",
     "https://mines.gov.in/admin/download/65e1c382744241709294466.pdf"),
]


def sha256(p: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    RAW.mkdir(parents=True, exist_ok=True)
    INTERIM.mkdir(parents=True, exist_ok=True)
    for name, url in DOCS:
        r = requests.get(url, headers=H, timeout=60)
        ok = r.status_code == 200 and r.content[:4] == b"%PDF"
        print(f"{name}: status={r.status_code} bytes={len(r.content)} is_pdf={ok}")
        if not ok:
            continue
        out = RAW / name
        out.write_bytes(r.content)
        print(f"   sha256={sha256(out)} -> {out.relative_to(ROOT)}")

    # extract policy section 7.1 for precise citation
    pdf = RAW / "Data_Dissemination_policy_2019.pdf"
    if pdf.exists():
        from pypdf import PdfReader
        text = "\n".join((pg.extract_text() or "") for pg in PdfReader(str(pdf)).pages)
        text = re.sub(r"[ \t]+", " ", text)
        m = re.search(r"7\.? ?DISSEMINATION OF BASELINE GEOSCIENCE DATA.{0,60}?"
                      r"COMPILED GEOLOGICAL MAPPING DATA.{0,4500}", text, re.S)
        if m:
            sec = m.group(0)
            # stop before section 7.2
            stop = re.search(r"7\.? ?2 ", sec)
            if stop:
                sec = sec[:stop.start()]
            (INTERIM / "policy_2019_section71.txt").write_text(
                sec.strip() + "\n", encoding="utf-8")
            print(f"policy section 7.1 extracted ({len(sec)} chars) -> "
                  f"{(INTERIM / 'policy_2019_section71.txt').relative_to(ROOT)}")
        else:
            print("policy section 7.1 NOT found by regex - inspect manually")
    return 0


if __name__ == "__main__":
    sys.exit(main())
