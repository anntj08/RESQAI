"""Phase 4 — verification gates.

Runs after the eligibility audit, the background sample and the fold assignment, and
checks each claim they make against the files on disk rather than against themselves:

  1  Phase 3 baseline intact        scripts/p3_verify_all.py (6 gates, incl. raw hashes)
  2  eligibility completeness       every record has exactly one decision and a reason
  3  the three special records      A/B/C stay distinct and keep their statuses
  4  point integrity                ids unique, counts, district + predictor coverage
  5  background separation          exact distance from every background point to the
                                    nearest recorded positive >= the exclusion radius
  6  leakage                        no event group, 1 km cluster or 3 km block split
                                    across folds (recomputed from saved assignments)
  7  fold support + buffer          support thresholds from config; the retained
                                    train->test minimum gap is INDEPENDENTLY recomputed
                                    from the saved fold_assignments.csv using the saved
                                    fold_drops.csv audit — the fold script's own claim
                                    is cross-checked, not trusted
  8  reproducibility                regenerate every output from scratch and re-hash it

Exit 0 only if all eight pass. Writes data/interim/p4/verify_p4.json.

Run:  python scripts/p4_verify.py
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
import sys

import numpy as np
import pandas as pd
import rasterio
from pathlib import Path
from scipy.spatial import cKDTree

ROOT = pathlib.Path(__file__).resolve().parents[1]
CFG = json.loads((ROOT / "configs" / "p4_sampling.json").read_text(encoding="utf-8"))
SAMP = ROOT / "data" / "processed" / "sampling"
OUT = ROOT / "data" / "interim" / "p4" / "verify_p4.json"

results: list[dict] = []


def gate(name: str, ok: bool, detail: str) -> None:
    results.append({"gate": name, "passed": bool(ok), "detail": detail})
    print(f"[{'PASS' if ok else 'FAIL'}] {name}")
    print(f"       {detail}")


def sha256(p: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def run(cmd: list[str], cwd: pathlib.Path = ROOT) -> tuple[int, str]:
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, errors="replace")
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def main() -> int:
    # ---- 1. Phase 3 baseline ------------------------------------------------
    code, out = run([sys.executable, "scripts/p3_verify_all.py"])
    tail = [ln for ln in out.strip().splitlines() if ln.strip()][-1] if out.strip() else ""
    gate("Phase 3 baseline still valid", code == 0, f"p3_verify_all exit={code}; {tail}")

    audit = pd.read_csv(SAMP / "eligibility_audit.csv")
    bg = pd.read_csv(SAMP / "background_samples.csv")
    fa = pd.read_csv(SAMP / "fold_assignments.csv")
    dr = pd.read_csv(SAMP / "fold_drops.csv")
    run_cfg = json.loads((SAMP / "sampling_run_config.json").read_text(encoding="utf-8"))
    folds_json = json.loads((SAMP / "fold_summary.json").read_text(encoding="utf-8"))
    sp = CFG["spatial_validation"]
    gap = float(sp["buffer_gap_m"])
    k = int(sp["n_folds"])

    # ---- 2. eligibility completeness ---------------------------------------
    exp_counts = {
        "POSITIVE_EVENT": 363, "POSITIVE_EVENT_DUPLICATE": 1,
        "EXCLUDE_SUPERSEDED": 0, "EXCLUDE_WIDEN_REQUIRED": 1,
        "EXCLUDE_BOUNDARY_UNCERTAIN": 5, "EXCLUDE_UNDATED_SITE": 78,
        "EXCLUDE_PRE_2000": 6, "EXCLUDE_NOT_IN_DISTRICT": 12,
        "EXCLUDE_DISTRICT_CENTROID": 1, "EXCLUDE_COORDINATE_ERROR": 1,
    }
    got = audit["p4_use"].value_counts().to_dict()
    problems = []
    if len(audit) != 468:
        problems.append(f"rows={len(audit)} expected 468")
    if set(got) - set(exp_counts):
        problems.append(f"unexpected decisions: {set(got) - set(exp_counts)}")
    for kk, v in exp_counts.items():
        if got.get(kk, 0) != v:
            problems.append(f"{kk}: {got.get(kk, 0)} != {v}")
    if audit["source_record_id"].duplicated().any():
        problems.append("duplicate source_record_id in audit")
    if audit["p4_reason"].isna().any() or (audit["p4_reason"].astype(str).str.strip() == "").any():
        problems.append("a record has no reason")
    gate("every record has exactly one decision and a reason", not problems,
         f"{len(audit)} records, {len(got)} decision classes; " +
         ("; ".join(problems) if problems else "counts match the documented partition"))

    # ---- 3. the three special records --------------------------------------
    a = audit.set_index("source_record_id")
    A, B, C = ("KER/WYD/58A03/2024/01", "14115/p141/row17 (printed Sl.17)",
               "14115/p140/row15 (printed Sl.15)")
    spec = []
    if A not in a.index or a.loc[A, "p4_use"] != "POSITIVE_EVENT":
        spec.append("A is not an eligible positive")
    if B not in a.index or a.loc[B, "p4_use"] != "EXCLUDE_COORDINATE_ERROR":
        spec.append("B is not the coordinate-error exclusion")
    if C not in a.index or a.loc[C, "p4_use"] != "EXCLUDE_BOUNDARY_UNCERTAIN":
        spec.append("C is not the boundary-uncertain exclusion")
    if len({A, B, C}) != 3:
        spec.append("the three records are not distinct")
    gate("three separately validated records stay distinct", not spec,
         "; ".join(spec) if spec else f"A={a.loc[A, 'p4_use']}, B={a.loc[B, 'p4_use']}, "
                                      f"C={a.loc[C, 'p4_use']}")

    # ---- 4. point integrity -------------------------------------------------
    problems = []
    if not fa["point_id"].is_unique:
        problems.append("duplicate point_id")
    posn = int((fa["role"] == "positive").sum())
    bgn = int((fa["role"] == "background").sum())
    if posn != 363:
        problems.append(f"positives={posn} expected 363")
    if bgn != run_cfg["background_samples"]:
        problems.append(f"background={bgn} != config {run_cfg['background_samples']}")
    if fa.loc[fa["role"] == "positive", "event_group_id"].nunique() != 363:
        problems.append("positives do not form 363 distinct event groups")
    if bg["sample_id"].duplicated().any():
        problems.append("duplicate sample_id in background_samples.csv")
    if bg.duplicated(["row", "col"]).any():
        problems.append("two background samples share a grid cell")

    # predictor coverage, read from the rasters rather than trusted from a flag
    with rasterio.open(ROOT / CFG["grid"]["district_mask"]) as ds:
        mask = ds.read(1) == 1
        tf = ds.transform
    rr, cc = rasterio.transform.rowcol(tf, fa["x_32643"].to_numpy(), fa["y_32643"].to_numpy())
    rr, cc = np.asarray(rr), np.asarray(cc)
    if not bool(mask[rr, cc].all()):
        problems.append("a point falls outside the district mask")
    inv = pd.read_csv(ROOT / CFG["grid"]["layer_inventory"], dtype=str)
    layers = [p for p in inv["layer"] if not p.startswith("grid/")]
    bad_layers = []
    for rel in layers:
        with rasterio.open(ROOT / "data" / "processed" / rel) as ds:
            vals = np.array([v for v in ds.sample(
                zip(fa["x_32643"], fa["y_32643"]))], dtype=float)
            good = np.isfinite(vals)
            if ds.nodata is not None:
                good &= vals != ds.nodata
            if not good.all():
                bad_layers.append(f"{rel}: {int((~good).sum())} invalid samples")
    problems += bad_layers
    gate("point integrity and predictor coverage", not problems,
         f"{len(fa)} points, {posn} positives / {bgn} background; " +
         ("; ".join(problems) if problems else f"all {len(layers)} predictor layers valid "
                                               f"at every point, all inside the district"))

    # ---- 5. background separation ------------------------------------------
    pxy = fa.loc[fa["role"] == "positive", ["x_32643", "y_32643"]].to_numpy(float)
    bxy = bg[["x_32643", "y_32643"]].to_numpy(float)
    dmin = float(cKDTree(pxy).query(bxy, k=1)[0].min())
    rad = float(CFG["background"]["exclusion_radius_m"])
    gate("background points respect the exclusion radius", dmin >= rad,
         f"closest background point is {dmin:.1f} m from a recorded positive "
         f"(radius {rad:.0f} m)")

    # ---- 6. leakage ---------------------------------------------------------
    fp = fa[fa["role"] == "positive"]
    per_group = fp.groupby("event_group_id")["fold"].nunique()
    per_cluster = fp.groupby("cluster_id")["fold"].nunique()
    per_block = fa.groupby("block_id")["fold"].nunique()
    leak = []
    if (per_group != 1).any():
        leak.append(f"{int((per_group != 1).sum())} event groups span folds")
    if (per_cluster != 1).any():
        leak.append(f"{int((per_cluster != 1).sum())} clusters span folds")
    if (per_block != 1).any():
        leak.append(f"{int((per_block != 1).sum())} blocks are split across folds")
    gate("no event group, cluster or block leaks across folds", not leak,
         "; ".join(leak) if leak else
         f"{len(per_group)} event groups, {len(per_cluster)} clusters and "
         f"{len(per_block)} blocks each lie in exactly one fold "
         f"(0 mixed-fold blocks, from the saved assignments)")

    # ---- 7. fold support, buffer, and an independent gap recomputation ------
    minp = int(sp["min_test_positives"])
    minc = int(sp["min_test_clusters"])
    xy = fa[["x_32643", "y_32643"]].to_numpy(float)
    issues: list[str] = []
    min_kept_overall = float("inf")
    for f in range(k):
        is_test = (fa["fold"] == f).to_numpy()
        rest_idx = np.flatnonzero(~is_test)
        d_rest = cKDTree(xy[is_test]).query(xy[rest_idx], k=1)[0]
        rest = fa.iloc[rest_idx]
        kept_idx = rest_idx[d_rest > gap]
        dropped_idx = rest_idx[d_rest <= gap]

        # saved fold summary vs independent recomputation
        fj = next((x for x in folds_json["folds"] if x["fold"] == f), None)
        if fj is None:
            issues.append(f"fold {f}: missing from fold_summary.json")
            continue
        recomputed = {
            "test_positives": int(((fa["fold"] == f) & (fa["role"] == "positive")).sum()),
            "test_background": int(((fa["fold"] == f) & (fa["role"] == "background")).sum()),
            "train_positives": int((fa.iloc[kept_idx]["role"] == "positive").sum()),
            "train_background": int((fa.iloc[kept_idx]["role"] == "background").sum()),
            "dropped_from_train": int(len(dropped_idx)),
            "test_clusters": int(fp[fp["fold"] == f]["cluster_id"].nunique()),
        }
        for kk in ("test_positives", "test_background", "train_positives",
                   "train_background", "dropped_from_train", "test_clusters"):
            if int(fj[kk]) != recomputed[kk]:
                issues.append(f"fold {f}: summary says {kk}={fj[kk]}, "
                              f"recomputed {recomputed[kk]}")

        # every point dropped from this fold's training truly lies within the gap,
        # every other rest point truly does not; and the drop audit matches (paired
        # by point_id, since fold_drops.csv row order is the generator's, not ours)
        drop_rows = dr[dr["fold"] == f]
        if len(drop_rows) != len(dropped_idx):
            issues.append(f"fold {f}: fold_drops has {len(drop_rows)} rows, "
                          f"buffer recomputation drops {len(dropped_idx)}")
        if set(drop_rows["point_id"]) != set(fa.iloc[dropped_idx]["point_id"]):
            issues.append(f"fold {f}: fold_drops point set differs from recomputation")
        recomputed_d = dict(zip(fa.iloc[dropped_idx]["point_id"],
                                d_rest[d_rest <= gap]))
        dist_ok = all(abs(float(r.distance_to_test_m) -
                          float(recomputed_d[r.point_id])) <= 0.11
                      for r in drop_rows.itertuples())
        if not dist_ok and len(drop_rows):
            issues.append(f"fold {f}: recorded drop distances do not match recomputation")

        if recomputed["test_positives"] < minp:
            issues.append(f"fold {f}: {recomputed['test_positives']} positives < {minp}")
        if recomputed["test_clusters"] < minc:
            issues.append(f"fold {f}: {recomputed['test_clusters']} clusters < {minc}")

        min_kept = float(d_rest[d_rest > gap].min()) if (d_rest > gap).any() else float("inf")
        min_kept_overall = min(min_kept_overall, min_kept)
        if np.isfinite(min_kept) and abs(min_kept - float(fj["min_train_to_test_m"])) > 0.11:
            issues.append(f"fold {f}: summary gap {fj['min_train_to_test_m']} m, "
                          f"recomputed {min_kept:.1f} m")

    if not np.isfinite(min_kept_overall) or min_kept_overall <= gap:
        issues.append(f"retained train->test gap {min_kept_overall} <= configured "
                      f"{gap:.0f} m")
    inv_gap = float(folds_json["invariants"]["min_train_to_test_m"])
    if abs(inv_gap - round(min_kept_overall, 1)) > 0.11:
        issues.append(f"fold_summary invariants gap {inv_gap} m != recomputed "
                      f"{min_kept_overall:.1f} m")
    gate("fold support and independently verified buffer", not issues,
         "; ".join(issues) if issues else
         f"per-fold support ({minp}+ positives, {minc}+ clusters) holds in every fold "
         f"[{' '.join(str(int(((fa['fold'] == f) & (fa['role'] == 'positive')).sum())) for f in range(k))}], "
         f"saved fold_drops match the recomputation for all {k} folds, and the "
         f"retained train->test minimum gap recomputed from the saved assignments is "
         f"{min_kept_overall:.1f} m > {gap:.0f} m configured")

    # ---- 8. reproducibility -------------------------------------------------
    watched = ["eligibility_audit.csv", "eligibility_summary.json",
               "background_samples.csv", "sampling_run_config.json",
               "spatial_blocks.csv", "fold_assignments.csv", "fold_drops.csv",
               "modelling_points.csv", "fold_summary.json"]
    before = {n: sha256(SAMP / n) for n in watched}
    codes = []
    for script in ("scripts/p4_eligibility.py", "scripts/p4_sample_background.py",
                   "scripts/p4_spatial_folds.py"):
        c, o = run([sys.executable, script])
        codes.append(f"{Path(script).name}={c}")
        if c != 0:
            print(o[-2000:])
    after = {n: sha256(SAMP / n) for n in watched}
    changed = [n for n in watched if before[n] != after[n]]
    gate("outputs regenerate identically from the same inputs and seed",
         all(c.endswith("=0") for c in codes) and not changed,
         f"re-ran 3 scripts ({', '.join(codes)}); " +
         (f"CHANGED: {changed}" if changed else
          f"all {len(watched)} outputs byte-identical after regeneration"))

    n_pass = sum(r["passed"] for r in results)
    verdict = "ALL PHASE 4 GATES PASSED" if n_pass == len(results) else \
        f"{len(results) - n_pass} GATE(S) FAILED"
    print("=" * 78)
    print(f"{n_pass}/{len(results)} gates passed -- {verdict}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"verdict": verdict, "n_gates": len(results),
                               "n_passed": n_pass, "gates": results}, indent=2),
                   encoding="utf-8")
    print(f"written -> {OUT.relative_to(ROOT)}")
    return 0 if n_pass == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
