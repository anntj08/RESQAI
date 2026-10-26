"""Verify every raw input is byte-identical to the acquisition-time checksum manifest.

Stage 7 of the recovery: prove the raw data was not modified by any Phase 3 work.

Two independent lines of evidence are reported:
  A. Content hashes. data/file_inventory.csv records sha256 for every raw file at
     acquisition time. It is git-tracked and unmodified, so it is a credible baseline.
     Every raw file is re-hashed here and compared.
  B. Metadata snapshots. data/interim/p3/rebuild_backup/inputs_metadata_before.json
     (pre-recovery) is compared field-by-field with the current inputs_metadata.json.

B alone is weaker than A: it records size_bytes and *sampled* value ranges, not a full
content hash. A is the authoritative test; B is reported as corroboration and its
limitation is stated rather than glossed over.

Exit 0 only if A passes in full and B is field-identical.

Run:  python scripts/p3_verify_raw_immutable.py
"""
from __future__ import annotations

import csv
import hashlib
import json
import pathlib
import sys
import time

ROOT = pathlib.Path(r"C:\Major")
INVENTORY = ROOT / "data" / "file_inventory.csv"
BEFORE = ROOT / "data" / "interim" / "p3" / "rebuild_backup" / "inputs_metadata_before.json"
AFTER = ROOT / "data" / "interim" / "p3" / "inputs_metadata.json"


def sha(p: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(4 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    rows = list(csv.DictReader(open(INVENTORY, encoding="utf-8")))
    print(f"A. content hashes vs {INVENTORY.name}  ({len(rows)} recorded raw files)")

    on_disk = {p.relative_to(ROOT).as_posix(): p
               for p in (ROOT / "data" / "raw").rglob("*") if p.is_file()}
    print(f"   raw files on disk: {len(on_disk)}")

    missing, size_bad, hash_bad, n = [], [], [], 0
    total_bytes = 0
    t0 = time.time()
    for r in rows:
        rel = r["relative_path"].replace("\\", "/")
        p = ROOT / rel
        if not p.exists():
            # try relative to data/raw in case the manifest stores a bare name
            alt = ROOT / "data" / "raw" / r["filename"]
            p = alt if alt.exists() else p
        if not p.exists():
            missing.append(rel)
            continue
        n += 1
        total_bytes += p.stat().st_size
        if p.stat().st_size != int(r["size_bytes"]):
            size_bad.append((rel, p.stat().st_size, int(r["size_bytes"])))
            continue
        if sha(p) != r["sha256"].strip().lower():
            hash_bad.append(rel)
        if n % 100 == 0:
            print(f"   ...{n} verified ({time.time() - t0:.0f}s)")

    recorded = {r["relative_path"].replace("\\", "/") for r in rows}
    unrecorded = sorted(set(on_disk) - recorded)

    print(f"   verified        : {n} / {len(rows)}")
    print(f"   bytes hashed    : {total_bytes / 1e6:.1f} MB in {time.time() - t0:.0f}s")
    print(f"   missing on disk : {len(missing)}")
    for m in missing[:10]:
        print(f"     - {m}")
    print(f"   size mismatches : {len(size_bad)}")
    for s in size_bad[:10]:
        print(f"     - {s[0]}: disk {s[1]} vs manifest {s[2]}")
    print(f"   hash mismatches : {len(hash_bad)}")
    for h in hash_bad[:10]:
        print(f"     - {h}")
    print(f"   on disk but not in manifest: {len(unrecorded)}")
    for u in unrecorded[:10]:
        print(f"     - {u}")

    a_ok = not (missing or size_bad or hash_bad)

    print("\nB. metadata snapshots (corroboration)")
    if not (BEFORE.exists() and AFTER.exists()):
        print("   one snapshot absent -- cannot corroborate")
        b_ok = False
        b_note = "snapshot absent"
    else:
        jb = json.loads(BEFORE.read_text(encoding="utf-8"))
        ja = json.loads(AFTER.read_text(encoding="utf-8"))
        b_ok = jb == ja
        b_note = ("field-identical (sizes, dims, CRS, transforms, tags, feature counts, "
                  "sampled value ranges)" if b_ok else "fields differ")
        print(f"   before vs after: {b_note}")
        print("   limitation: these snapshots record size_bytes and *sampled* value ranges, "
              "not a full content hash; line A is the authoritative test.")

    print("\n" + "-" * 70)
    ok = a_ok and b_ok
    print(f"A. raw content hashes : {'PASS' if a_ok else 'FAIL'} "
          f"({n} files, {total_bytes / 1e6:.1f} MB)")
    print(f"B. metadata snapshots : {'PASS' if b_ok else 'FAIL'} ({b_note})")
    print("RAW INPUTS: " + ("UNCHANGED — verified by content hash"
                            if a_ok else "CHANGED OR UNVERIFIABLE — do not commit"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
