"""Compare a baseline snapshot of Phase 3 outputs against the current outputs.

Two distinct questions, both answered here:

  1. "Did this session's recovery change any scientific output?"
     baseline = data/interim/p3/rebuild_backup  (taken before the recovery edits)
     Expected result: everything identical except one JSON that gained three
     *additive* evidence keys. That exception is declared explicitly in ADDITIVE_KEYS,
     never inferred, so an unexplained change fails.

  2. "Are the scripts deterministic?"
     baseline = a snapshot of the outputs taken immediately before a re-run.
     Expected result: no differences at all.

Evidence strength, strongest first:
  IDENTICAL      SHA-256 of the bytes match.
  SAME CONTENT   bytes differ but the parsed content is equal (explained, e.g. a
                 GeoPackage container rewrites internal offsets, or a JSON timer moved).
  EXPECTED_ADDITIVE
                 bytes differ and the only content change is one of the declared
                 additive keys below, in the declared direction.
  DIFFERS        content changed in a way nobody declared.
  MISSING        expected output absent.
  UNEXPECTED     output present that the baseline did not have.

Never "equivalent because sizes match": every non-identical file is parsed by type.

Run:
  python data/interim/p3/compare_rebuild.py
  python data/interim/p3/compare_rebuild.py --baseline data/interim/p3/roundtrip_backup \
      --out data/interim/p3/rebuild_comparison_roundtrip.json
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(r"C:\Major")
DEFAULT_BASELINE = ROOT / "data" / "interim" / "p3" / "rebuild_backup"
DEFAULT_OUT = ROOT / "data" / "interim" / "p3" / "rebuild_comparison.json"

# Volatile JSON keys: values that legitimately change between runs and carry no
# scientific content. Listed explicitly rather than pattern-matched, so an unexpected
# new key fails loudly instead of being silently ignored.
VOLATILE = {"elapsed_s", "elapsed_seconds", "runtime_s", "generated_at",
            "timestamp", "run_started_utc", "duration_s"}

# Declared, justified content changes relative to the original baseline. Any key path
# not listed here that changes will fail the comparison.
ADDITIVE_KEYS = {
    "rainfall/rainfall_validation.json": {
        "all_nan_window_cells",
        "all_nan_window_pct",
        "all_nan_note",
    },
}
ADDITIVE_REASON = (
    "p3_rainfall.py now counts and asserts the all-NaN cells in the padded CHIRPS window "
    "(140 of 1,088 = 12.87%) and records the evidence, instead of letting numpy emit "
    "'Mean of empty slice' / 'All-NaN slice' warnings to stderr. The rainfall rasters and "
    "CSVs were verified byte-identical before and after, so only these additive keys moved."
)

# Phase 1 products consumed by Phase 3. Not regenerated: the roads clip comes from a live
# Overpass query, so re-running it would change the input.
#
# NOTE: data/processed/geology/ and data/processed/additional/ are MIXED directories --
# they hold Phase 1 outputs next to Phase 3 outputs. The rebuild boundary therefore cuts
# through a directory, which is why deleting data/processed/ wholesale is wrong.
PREREQUISITES = {
    "geology/glim_wayanad_clip.gpkg",
    "geology/glim_wayanad_lithology_summary.csv",
    "additional/osm_roads_wayanad_clip.gpkg",
    "additional/hydrorivers_wayanad_clip.gpkg",
}

# Phase 2 inventory products. Deliberately NOT part of the Phase 3 baseline: they are
# inputs, not outputs, and their immutability is checked separately and more strictly by
# scripts/p3_verify_phase2_untouched.py against a recorded SHA-256 manifest. Listed here
# so the "unexpected output" scan does not flag them.
PHASE2_PRODUCTS = {
    "inventory/2024_corroboration.csv",
    "inventory/2024_corroboration.json",
    "inventory/coverage_2000_2026.csv",
    "inventory/duplicate_crosswalk.csv",
    "inventory/inventory_all_source_records.csv",
    "inventory/inventory_events_2000_2026.csv",
    "inventory/inventory_source_records.csv",
}

results: list[dict] = []


def sha(p: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def strip_volatile(obj, path=""):
    """Recursively drop VOLATILE keys. Returns (cleaned, [dropped paths])."""
    dropped: list[str] = []
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if k in VOLATILE:
                dropped.append(f"{path}.{k}" if path else k)
                continue
            out[k], sub = strip_volatile(v, f"{path}.{k}" if path else k)
            dropped += sub
        return out, dropped
    if isinstance(obj, list):
        out = []
        for i, v in enumerate(obj):
            c, sub = strip_volatile(v, f"{path}[{i}]")
            out.append(c)
            dropped += sub
        return out, dropped
    return obj, dropped


def flat(d, p=""):
    out = {}
    if isinstance(d, dict):
        for k, v in d.items():
            out.update(flat(v, f"{p}.{k}" if p else k))
    elif isinstance(d, list):
        for i, v in enumerate(d):
            out.update(flat(v, f"{p}[{i}]"))
    else:
        out[p] = d
    return out


def cmp_json(a: pathlib.Path, b: pathlib.Path, rel: str) -> tuple[str, str]:
    ja = json.loads(a.read_text(encoding="utf-8"))
    jb = json.loads(b.read_text(encoding="utf-8"))
    ca, da = strip_volatile(ja)
    cb, db = strip_volatile(jb)

    if ca == cb:
        note = "same content"
        if da or db:
            note += f"; ignored volatile: {', '.join(sorted(set(da) | set(db)))}"
        return "SAME CONTENT", note

    # Is every difference a declared additive key?
    allow = ADDITIVE_KEYS.get(rel)
    if allow:
        fa, fb = flat(ca), flat(cb)
        added = set(fb) - set(fa)
        removed = set(fa) - set(fb)
        changed = {k for k in set(fa) & set(fb) if fa[k] != fb[k]}
        if added <= allow and not removed and not changed:
            return "EXPECTED_ADDITIVE", (
                f"declared additive keys only: {', '.join(sorted(added))}")

    fa, fb = flat(ca), flat(cb)
    diff = sorted(set(fa) ^ set(fb)) + sorted(k for k in set(fa) & set(fb) if fa[k] != fb[k])
    return "DIFFERS", f"JSON content differs at: {', '.join(diff[:8])}"


def cmp_csvfile(a: pathlib.Path, b: pathlib.Path) -> tuple[str, str]:
    ra = list(csv.reader(open(a, encoding="utf-8")))
    rb = list(csv.reader(open(b, encoding="utf-8")))
    if len(ra) != len(rb):
        return "DIFFERS", f"CSV row count {len(ra)} vs {len(rb)}"
    if ra[0] != rb[0]:
        return "DIFFERS", "CSV header differs"
    worst, worst_cell, n_num, ndiff = 0.0, "", 0, 0
    for i, (rowa, rowb) in enumerate(zip(ra[1:], rb[1:]), start=2):
        if len(rowa) != len(rowb):
            return "DIFFERS", f"CSV column count differs at row {i}"
        for ca, cb in zip(rowa, rowb):
            if ca == cb:
                continue
            try:
                fa, fb = float(ca), float(cb)
            except ValueError:
                ndiff += 1
                continue
            n_num += 1
            d = abs(fa - fb)
            if d > worst:
                worst, worst_cell = d, f"row {i}"
    if ndiff:
        return "DIFFERS", f"{ndiff} non-numeric cell differences"
    if worst == 0.0:
        return "SAME CONTENT", "same content (text differs only in formatting)"
    if worst < 1e-9:
        return "SAME CONTENT", f"max numeric difference {worst:.3e} at {worst_cell} (< 1e-9)"
    return "DIFFERS", f"max numeric difference {worst:.3e} at {worst_cell}"


def cmp_tiff(a: pathlib.Path, b: pathlib.Path) -> tuple[str, str]:
    import rasterio
    with rasterio.open(a) as da, rasterio.open(b) as db:
        if da.shape != db.shape:
            return "DIFFERS", f"shape {da.shape} vs {db.shape}"
        if da.crs != db.crs:
            return "DIFFERS", f"CRS {da.crs} vs {db.crs}"
        if not da.transform.almost_equals(db.transform, precision=1e-9):
            return "DIFFERS", f"transform {tuple(da.transform)[:6]} vs {tuple(db.transform)[:6]}"
        if da.dtypes != db.dtypes:
            return "DIFFERS", f"dtype {da.dtypes} vs {db.dtypes}"
        if da.nodata != db.nodata:
            return "DIFFERS", f"nodata {da.nodata} vs {db.nodata}"
        if da.count != db.count:
            return "DIFFERS", f"band count {da.count} vs {db.count}"
        worst, worst_band, nbad = 0.0, 0, 0
        for i in range(1, da.count + 1):
            xa = da.read(i)
            xb = db.read(i)
            if np.array_equal(xa, xb):
                continue
            if np.issubdtype(xa.dtype, np.floating):
                bad = ~np.isclose(xa, xb, rtol=0, atol=1e-6, equal_nan=True)
                finite = np.isfinite(xa) & np.isfinite(xb)
                d = (float(np.max(np.abs(xa.astype("float64")[finite]
                                        - xb.astype("float64")[finite])))
                     if finite.any() else 0.0)
            else:
                bad = xa != xb
                d = float(np.abs(xa.astype("int64") - xb.astype("int64")).max())
            nbad += int(bad.sum())
            if d > worst:
                worst, worst_band = float(d), i
        if nbad == 0:
            return "SAME CONTENT", "pixels equal, container bytes differ"
        return "DIFFERS", f"{nbad} differing pixels, max |diff| {worst:.3e} in band {worst_band}"


def cmp_gpkg(a: pathlib.Path, b: pathlib.Path) -> tuple[str, str]:
    import geopandas as gpd
    ga, gb = gpd.read_file(a), gpd.read_file(b)
    if len(ga) != len(gb):
        return "DIFFERS", f"feature count {len(ga)} vs {len(gb)}"
    if list(ga.columns) != list(gb.columns):
        return "DIFFERS", f"columns differ: {list(ga.columns)} vs {list(gb.columns)}"
    if str(ga.crs) != str(gb.crs):
        return "DIFFERS", f"CRS {ga.crs} vs {gb.crs}"
    if not ga.geometry.geom_equals_exact(gb.geometry, 1e-12).all():
        return "DIFFERS", "geometry differs"
    try:
        same_attrs = ga.drop(columns="geometry").reset_index(drop=True).equals(
            gb.drop(columns="geometry").reset_index(drop=True))
    except Exception as exc:  # pragma: no cover
        return "DIFFERS", f"attribute comparison failed: {exc}"
    if not same_attrs:
        return "DIFFERS", "attributes differ"
    return "SAME CONTENT", "features, attributes and geometry all equal"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", default=str(DEFAULT_BASELINE))
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    args = ap.parse_args()
    baseline = pathlib.Path(args.baseline)
    if not baseline.is_dir():
        print(f"baseline not found: {baseline}")
        return 2

    files = sorted(p for p in baseline.rglob("*") if p.is_file())
    print(f"baseline: {baseline}")
    print(f"comparing {len(files)} baseline files\n")
    print(f"{'file':<50} {'result':<18} detail")
    print("-" * 124)

    seen: set[pathlib.Path] = set()
    for src in files:
        rel = src.relative_to(baseline).as_posix()
        if rel == "inputs_metadata_before.json":
            dst = ROOT / "data" / "interim" / "p3" / "inputs_metadata.json"
            label = "inputs_metadata.json (raw-input snapshot)"
        else:
            dst = ROOT / "data" / "processed" / rel
            label = rel + (" [Phase 1 prerequisite]" if rel in PREREQUISITES else "")
        seen.add(dst)

        if not dst.exists():
            results.append({"file": rel, "status": "MISSING", "detail": str(dst)})
            print(f"{label:<50} {'MISSING':<18} {dst}")
            continue

        if sha(src) == sha(dst):
            results.append({"file": rel, "status": "IDENTICAL",
                            "detail": "sha256 equal", "size_bytes": dst.stat().st_size})
            print(f"{label:<50} {'IDENTICAL':<18} byte-for-byte "
                  f"({dst.stat().st_size:,} B)")
            continue

        suffix = src.suffix.lower()
        size_note = f"{src.stat().st_size:,} -> {dst.stat().st_size:,} B"
        try:
            if suffix == ".json":
                status, note = cmp_json(src, dst, rel)
            elif suffix == ".csv":
                status, note = cmp_csvfile(src, dst)
            elif suffix in (".tif", ".tiff"):
                status, note = cmp_tiff(src, dst)
            elif suffix == ".gpkg":
                status, note = cmp_gpkg(src, dst)
            else:
                status, note = "DIFFERS", "bytes differ; no content comparison available"
        except Exception as exc:
            status, note = "DIFFERS", f"comparison raised {type(exc).__name__}: {exc}"

        results.append({"file": rel, "status": status, "detail": note,
                        "size_bytes": dst.stat().st_size})
        print(f"{label:<50} {status:<18} {note} [{size_note}]")

    # Outputs that exist now but were not in the baseline. Scoped to the top-level
    # directories the baseline itself covers: this comparator answers "did the recovery
    # change any Phase 3 output", and later phases legitimately add new directories
    # (data/processed/sampling/ from Phase 4) that lie outside that question.
    scope = sorted({p.relative_to(baseline).parts[0] for p in files}) if files else []
    unexpected = []
    for p in sorted((ROOT / "data" / "processed").rglob("*")):
        if not p.is_file():
            continue
        if "rebuild_backup" in p.parts or "roundtrip_backup" in p.parts:
            continue
        rel_parts = p.relative_to(ROOT / "data" / "processed").parts
        if rel_parts[0] not in scope:
            continue
        rel_proc = p.relative_to(ROOT / "data" / "processed").as_posix()
        if rel_proc in PHASE2_PRODUCTS:
            continue
        if p not in seen and p.suffix.lower() in (".tif", ".tiff", ".gpkg", ".json", ".csv"):
            unexpected.append(p.relative_to(ROOT).as_posix())
    for rel in unexpected:
        results.append({"file": rel, "status": "UNEXPECTED", "detail": "not in baseline"})
        print(f"{rel:<50} {'UNEXPECTED':<18} present now, absent from baseline")

    counts: dict[str, int] = {}
    for r in results:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    failed = counts.get("DIFFERS", 0) + counts.get("MISSING", 0)

    summary = {
        "baseline": str(baseline),
        "n_baseline_files": len(files),
        "n_outputs_now": len(seen),
        "counts": counts,
        "failed": failed,
        "prerequisites_not_regenerated": sorted(PREREQUISITES),
        "volatile_keys_ignored": sorted(VOLATILE),
        "declared_additive_keys": {k: sorted(v) for k, v in ADDITIVE_KEYS.items()},
        "declared_additive_reason": ADDITIVE_REASON,
        "tolerances": {
            "tiff_pixel_atol": 1e-6,
            "tiff_transform_precision": 1e-9,
            "gpkg_geometry_tolerance_deg_or_m": 1e-12,
            "csv_numeric_atol": 1e-9,
        },
        "results": results,
    }
    out = pathlib.Path(args.out)
    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("-" * 124)
    print("counts: " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))
    print(f"written -> {out}")
    if failed:
        print(f"FAILED: {failed} file(s) differ or are missing")
        return 1
    print("PASSED: every baseline file is reproduced or declared")
    return 0


if __name__ == "__main__":
    sys.exit(main())
