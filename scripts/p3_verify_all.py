"""Run every Phase 3 verification gate in order and report a single verdict.

This is the one command that answers "is Phase 3 still trustworthy?" It does not
re-test the pipeline; it runs the independent checkers, each of which compares a
different class of claim against the files on disk:

  1  raw inputs unchanged           scripts/p3_verify_raw_immutable.py      431 files, by sha256
  2  Phase 2 products untouched     scripts/p3_verify_phase2_untouched.py  7 files, by sha256
  3  every layer on the study grid  scripts/p3_verify_processed.py         25 rasters
  4  docs match outputs             scripts/p3_check_consistency.py        the quoted figures
  5  Phase 2 docs still hold        scripts/p2_check_consistency.py        inventory invariants
  6  outputs reproduce              data/interim/p3/compare_rebuild.py     74 files vs baseline

Exit 0 only if all six pass. Writes data/interim/p3/verify_all.json.

Run:  python scripts/p3_verify_all.py
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "interim" / "p3" / "verify_all.json"

GATES = [
    ("raw inputs unchanged (sha256)",
     [sys.executable, "scripts/p3_verify_raw_immutable.py"]),
    ("Phase 2 products untouched (sha256)",
     [sys.executable, "scripts/p3_verify_phase2_untouched.py"]),
    ("all layers on the study grid",
     [sys.executable, "scripts/p3_verify_processed.py"]),
    ("documentation matches outputs",
     [sys.executable, "scripts/p3_check_consistency.py"]),
    ("Phase 2 invariants still hold",
     [sys.executable, "scripts/p2_check_consistency.py"]),
    ("outputs reproduce from raw",
     [sys.executable, "data/interim/p3/compare_rebuild.py"]),
]


def main() -> int:
    results = []
    print("=" * 78)
    for name, cmd in GATES:
        t0 = time.time()
        proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                              errors="replace")
        dt = time.time() - t0
        # The meaningful summary line is the last non-empty one in each case.
        tail = [ln for ln in (proc.stdout or "").strip().splitlines() if ln.strip()]
        summary = tail[-1] if tail else "(no stdout)"
        ok = proc.returncode == 0
        print(f"[{'PASS' if ok else 'FAIL'}] {name}")
        print(f"       {summary}")
        print(f"       exit={proc.returncode}  {dt:.1f}s")
        if not ok and tail:
            print("       tail of output:")
            for ln in tail[-12:]:
                print(f"         {ln}")
        results.append({
            "gate": name,
            "command": " ".join(cmd),
            "exit_code": proc.returncode,
            "passed": ok,
            "seconds": round(dt, 1),
            "summary": summary,
        })
    print("=" * 78)

    n_pass = sum(r["passed"] for r in results)
    verdict = "ALL GATES PASSED" if n_pass == len(results) else f"{len(results) - n_pass} GATE(S) FAILED"
    print(f"{n_pass}/{len(results)} gates passed -- {verdict}")

    OUT.write_text(json.dumps({"verdict": verdict, "n_gates": len(results),
                               "n_passed": n_pass, "gates": results}, indent=2),
                   encoding="utf-8")
    print(f"written -> {OUT.relative_to(ROOT)}")
    return 0 if n_pass == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
