"""Fetch the KSDMA-hosted GSI 2022 Wayanad landslide susceptibility zones archive.

Official source (re-confirmed 2026-10-28 from https://sdma.kerala.gov.in/hazard-maps/):
table row "Landslide Susceptibility zones of District of Kerala (GSI, 2022)- Shape
files", item 11 -> https://sdma.kerala.gov.in/wp-content/uploads/2025/08/Wayanad.zip

This is a SEPARATE COMPARISON / REFERENCE dataset:
  - product = GSI 2022 landslide susceptibility zones (NLSM macro-scale, ~1:50K),
    hosted by KSDMA; it is NOT geology and must never enter the predictor stack
    or be treated as an input to the Phase 5 model.
  - susceptibility zoning estimates WHERE terrain conditions favour failure; it is
    not a forecast, warning or timing prediction (standing AGENTS.md rule).

The download is preserved UNCHANGED under
  data/raw/landslide_susceptibility_reference/Wayanad.zip
(downloaded to a .part file and atomically renamed only after a successful,
complete transfer). No other district's archive is fetched.

Evidence (size, sha256, HTTP headers, magic bytes) is written to
  data/interim/lsz_reference/fetch_evidence.json
The zip's internal integrity is checked by
  scripts/validate_ksdma_lsz_wayanad.py (this script only confirms transfer).

Run:  python scripts/fetch_ksdma_lsz_wayanad.py
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import pathlib
import sys

import requests

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw" / "landslide_susceptibility_reference"
INTERIM = ROOT / "data" / "interim" / "lsz_reference"
EVIDENCE = INTERIM / "fetch_evidence.json"

URL = "https://sdma.kerala.gov.in/wp-content/uploads/2025/08/Wayanad.zip"
SOURCE_PAGE = "https://sdma.kerala.gov.in/hazard-maps/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (RESQAI academic research; dataset acquisition)",
    "Accept": "application/zip,*/*",
}
HEADER_KEYS = ["Content-Type", "Content-Length", "Last-Modified", "Date", "Server",
               "Accept-Ranges", "ETag", "Content-Disposition", "Connection",
               "Cache-Control"]


def sha256_of(p: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    INTERIM.mkdir(parents=True, exist_ok=True)
    final = RAW_DIR / "Wayanad.zip"
    part = RAW_DIR / "Wayanad.zip.part"

    if final.exists() and not part.exists():
        print(f"already downloaded, re-recording evidence: {final.relative_to(ROOT)}")
        data = final.read_bytes()
        status, hdrs, eff = 200, {}, URL
    else:
        print(f"GET {URL}")
        with requests.get(URL, headers=HEADERS, timeout=120, stream=True) as r:
            r.raise_for_status()
            status = r.status_code
            hdrs = {k: v for k, v in r.headers.items() if k in HEADER_KEYS}
            eff = r.url
            buf = bytearray()
            for chunk in r.iter_content(chunk_size=1 << 20):
                buf.extend(chunk)
        data = bytes(buf)

    sha = hashlib.sha256(data).hexdigest()
    magic_ok = data[:4] == b"PK\x03\x04"
    if not magic_ok:
        print("FATAL: first bytes are not a zip local header (PK\\x03\\x04)")
        return 1

    part.write_bytes(data)
    part.replace(final)          # atomic: original appears only when complete

    hdr_len = hdrs.get("Content-Length")
    len_match = (hdr_len is None or int(hdr_len) == len(data)) if hdrs else None

    rec = {
        "fetched_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "source_page": SOURCE_PAGE,
        "page_row": "Landslide Susceptibility zones of District of Kerala (GSI, 2022)- Shape files",
        "page_item": "11. Wayanad",
        "product": "GSI 2022 landslide susceptibility zones (Wayanad district) - "
                   "reference/comparison dataset only; NOT geology, NOT a model input",
        "url": URL,
        "effective_url": eff,
        "http_status": status,
        "headers": hdrs,
        "bytes_downloaded": len(data),
        "size_mb": round(len(data) / (1024 * 1024), 3),
        "sha256": sha,
        "magic_zip_ok": magic_ok,
        "content_length_header": hdr_len,
        "content_length_matches": len_match,
        "saved_to": str(final.relative_to(ROOT)),
        "note": "original preserved unchanged under data/raw/; extracted working "
                "copies belong in data/interim/lsz_reference/ only",
    }
    EVIDENCE.write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
    print(f"saved  : {final.relative_to(ROOT)} ({len(data):,} B = "
          f"{rec['size_mb']} MB)")
    print(f"sha256 : {sha}")
    print(f"status : {status} | content-type: {hdrs.get('Content-Type')} | "
          f"length-match: {len_match}")
    print(f"evidence -> {EVIDENCE.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
