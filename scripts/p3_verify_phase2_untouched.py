"""Verify the Phase 2 inventory products are byte-identical to the pre-Phase-3 baseline.

Phase 3 must not modify Phase 2 outputs. This compares the SHA-256 recorded in
data/interim/p3/inventory_hashes_before.json against the files on disk now, and
additionally confirms the on-disk backup under data/interim/p3/inventory_backup/
still matches. Exit 0 only if all three agree.

Run:  python scripts/p3_verify_phase2_untouched.py
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path(r"C:\Major")
INV = ROOT / "data" / "processed" / "inventory"
BACKUP = ROOT / "data" / "interim" / "p3" / "inventory_backup"
HASHES = ROOT / "data" / "interim" / "p3" / "inventory_hashes_before.json"


def sha(p: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    baseline = json.loads(HASHES.read_text(encoding="utf-8"))
    bad = 0
    print(f"{'file':<40} {'on disk':<10} {'backup':<10} result")
    print("-" * 82)
    for name, want in sorted(baseline.items()):
        live = INV / name
        bk = BACKUP / name
        if not live.exists():
            print(f"{name:<40} {'MISSING':<10} {'-':<10} FAIL")
            bad += 1
            continue
        got = sha(live)
        bk_status = "n/a"
        if bk.exists():
            bk_status = "match" if sha(bk) == want else "DIFF"
            if bk_status == "DIFF":
                bad += 1
        ok = got == want
        if not ok:
            bad += 1
        print(f"{name:<40} {('match' if ok else 'DIFF'):<10} {bk_status:<10} "
              f"{'OK' if ok and bk_status != 'DIFF' else 'FAIL'}")
    print("-" * 82)
    if bad:
        print(f"FAILED: {bad} problem(s) -- Phase 2 inventory products changed")
        return 1
    print(f"PASSED: all {len(baseline)} Phase 2 inventory products byte-identical "
          f"to the pre-Phase-3 baseline")
    return 0


if __name__ == "__main__":
    sys.exit(main())
