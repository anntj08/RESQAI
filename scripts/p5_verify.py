"""Phase 5 — verification gates.

Checks the Phase 5 claims against the files on disk rather than against
themselves:

  1  Phase 4 authority intact     scripts/p4_verify.py (8 gates) still passes
  2  feature-table integrity      extraction_checks.json verdict + independent
                                  re-assertion on the CSV (counts, provenance
                                  equality, finiteness, order, categorical
                                  classes, CHIRPS sentinel)
  3  fold usage = Phase 4         train/test rebuilt from fold_assignments.csv
                                  + fold_drops.csv equal fold_summary.json AND
                                  the counts recorded in fold_metrics.json;
                                  test folds partition all 2,460 points
  4  evaluation completeness      5 folds with both metrics; fold 2 flagged
                                  marginal; correlated-fold mean note; model
                                  params == config; limitations present; and
                                  the saved fold models RECOMPUTE the recorded
                                  AUC/AP exactly (models audited, not trusted)
  5  map checks                   verdict after gates; domain 2,343,343;
                                  tif dtype/nodata/CRS/shape; value stats
                                  recomputed from the tif == metadata; label
                                  present; sha256 of tif == recorded
  6  reproducibility              re-run all three Phase 5 scripts and
                                  byte-compare every output (CSV, JSONs,
                                  models, tif, PNGs)

Exit 0 only if all six pass. Writes data/interim/p5/verify_p5.json.

Run:  python scripts/p5_verify.py      (~10-20 min: full regeneration)
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
import sys

import joblib
import numpy as np
import pandas as pd
import rasterio
from sklearn.metrics import average_precision_score, roc_auc_score

ROOT = pathlib.Path(__file__).resolve().parents[1]
CFG = json.loads((ROOT / "configs" / "p5_baseline.json").read_text(encoding="utf-8"))
PROC = ROOT / "data" / "processed"
MODELS = PROC / "models"
OUT = ROOT / "data" / "interim" / "p5" / "verify_p5.json"

results: list[dict] = []


def gate(name: str, ok: bool, detail: str) -> bool:
    results.append({"gate": name, "passed": bool(ok), "detail": detail})
    print(f"[{'PASS' if ok else 'FAIL'}] {name}")
    print(f"       {detail}")
    return bool(ok)


def sha256(p: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def run(cmd: list[str]) -> tuple[int, str]:
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, errors="replace")
    return p.returncode, (p.stdout or "") + (p.stderr or "")


P5_OUTPUTS = [
    "data/processed/models/features_point_table.csv",
    "data/processed/models/extraction_checks.json",
    "data/processed/models/fold_metrics.json",
    "data/processed/models/map_metadata.json",
    "data/processed/models/final_rf_refit_all_points.joblib",
    "data/processed/models/roc_curves.png",
    "data/processed/models/permutation_importance.png",
    "data/processed/models/susceptibility_rf_baseline_30m.tif",
    "data/processed/models/susceptibility_rf_baseline.png",
] + [f"data/processed/models/fold_{f}_rf.joblib" for f in range(5)]


def main() -> int:
    ok = True
    ROOT.mkdir(parents=True, exist_ok=True)
    (ROOT / "data" / "interim" / "p5").mkdir(parents=True, exist_ok=True)
    spec = CFG["features"]["spec"]
    feat_names = [e["name"] for e in spec]
    PROV_COLS = ["point_id", "role", "label", "event_group_id", "event_year",
                 "cluster_id", "block_id", "fold", "x_32643", "y_32643",
                 "lon_4326", "lat_4326"]

    # ---- 1. Phase 4 authority ------------------------------------------------
    code, out = run([sys.executable, "scripts/p4_verify.py"])
    ok &= gate("Phase 4 authority intact", code == 0,
               f"p4_verify exit={code}; "
               + ([ln for ln in out.splitlines() if "gates passed" in ln] or [""])[-1])

    tab = pd.read_csv(MODELS / "features_point_table.csv")
    fa = pd.read_csv(PROC / "sampling" / "fold_assignments.csv")
    drops = pd.read_csv(PROC / "sampling" / "fold_drops.csv")
    fs = json.loads((PROC / "sampling" / "fold_summary.json").read_text(encoding="utf-8"))
    ext = json.loads((MODELS / "extraction_checks.json").read_text(encoding="utf-8"))
    fm = json.loads((MODELS / "fold_metrics.json").read_text(encoding="utf-8"))
    mm = json.loads((MODELS / "map_metadata.json").read_text(encoding="utf-8"))

    # ---- 2. feature-table integrity ------------------------------------------
    probs = []
    if ext["verdict"] != "ALL EXTRACTION CHECKS PASSED":
        probs.append("saved extraction verdict not green")
    if len(tab) != 2460 or not tab["point_id"].is_unique:
        probs.append(f"rows={len(tab)} or duplicate ids")
    if not tab[PROV_COLS].equals(fa[PROV_COLS]):
        probs.append("provenance columns differ from fold_assignments.csv")
    if list(tab.columns)[len(PROV_COLS):] != feat_names:
        probs.append("feature order != config order")
    X = tab[feat_names].to_numpy(dtype=float)
    if not np.isfinite(X).all():
        probs.append("non-finite feature values")
    rain = [c for c in feat_names if c.startswith("rain_")]
    if float(X[:, [feat_names.index(c) for c in rain]].min()) <= -9998:
        probs.append("rainfall sentinel value present")
    lc = set(tab["landcover_class"].astype(int))
    gl = set(tab["geology_class"].astype(int))
    if not lc <= {10, 20, 30, 40, 50, 60, 70, 80, 90} or not gl <= {1, 2, 3, 4, 5}:
        probs.append(f"categorical classes out of spec: lc={sorted(lc)} gl={sorted(gl)}")
    ok &= gate("feature-table integrity", not probs,
               "2460 rows; provenance byte-equal to fold_assignments.csv; 35 features in "
               "config order, all finite; no rainfall value <= -9998; landcover "
               f"{sorted(lc)} and geology {sorted(gl)} inside spec"
               if not probs else "; ".join(probs))

    # ---- 3. fold usage matches the Phase 4 authority --------------------------
    y = tab["label"].to_numpy(dtype=int)
    fold_arr = tab["fold"].to_numpy()
    ids = tab["point_id"].to_numpy()
    fold_problems = []
    test_union = np.zeros(len(tab), dtype=bool)
    for f in range(fs["n_folds"]):
        tem = fold_arr == f
        drop_ids = set(drops.loc[drops["fold"] == f, "point_id"])
        trm = (~tem) & (~np.isin(ids, sorted(drop_ids)))
        test_union |= tem
        s = fs["folds"][f]
        counts = (int((y[tem] == 1).sum()), int((y[tem] == 0).sum()),
                  int((y[trm] == 1).sum()), int((y[trm] == 0).sum()))
        if counts != (s["test_positives"], s["test_background"],
                      s["train_positives"], s["train_background"]):
            fold_problems.append(f"fold {f} counts {counts} != fold_summary")
        r = fm["fold_metrics"][f]
        if (r["test_positives"], r["test_background"], r["train_positives"],
                r["train_background"], r["dropped_from_train"]) != (
                s["test_positives"], s["test_background"], s["train_positives"],
                s["train_background"], s["dropped_from_train"]):
            fold_problems.append(f"fold {f} recorded metrics counts != fold_summary")
    if not test_union.all():
        fold_problems.append("test folds do not cover all 2460 points")
    ok &= gate("fold usage matches Phase 4 authority", not fold_problems,
               "all 5 folds rebuilt from fold_assignments.csv + fold_drops.csv equal "
               "fold_summary.json and the counts recorded in fold_metrics.json; test "
               "folds partition all 2,460 points; no random split"
               if not fold_problems else "; ".join(fold_problems))

    # ---- 4. evaluation completeness + models audited --------------------------
    ev = []
    if len(fm["fold_metrics"]) != 5:
        ev.append("fold_metrics does not have 5 folds")
    for r in fm["fold_metrics"]:
        if not (0.0 <= r["roc_auc"] <= 1.0) or not (0.0 <= r["average_precision"] <= 1.0):
            ev.append(f"fold {r['fold']} metric out of range")
    if not any(m["fold"] == 2 for m in fm["marginal_folds"]):
        ev.append("fold 2 not flagged marginal")
    if "correlated" not in fm["mean_of_folds"]["note"]:
        ev.append("mean-of-folds note missing correlation caveat")
    if len(fm["limitations"]) < 8:
        ev.append("limitations list incomplete")
    mp_cfg = CFG["model"]
    for k in ("n_estimators", "min_samples_leaf", "max_features", "class_weight",
              "random_state"):
        if fm["model_params"][k] != mp_cfg[k]:
            ev.append(f"model param {k} != config")
    # audit the saved fold models: recompute the recorded metrics from them
    recomputed = []
    for f in range(fs["n_folds"]):
        clf = joblib.load(MODELS / f"fold_{f}_rf.joblib")
        tem = fold_arr == f
        p = clf.predict_proba(X[tem])[:, 1]
        auc = float(roc_auc_score(y[tem], p))
        ap = float(average_precision_score(y[tem], p))
        r = fm["fold_metrics"][f]
        if abs(auc - r["roc_auc"]) > 1e-9 or abs(ap - r["average_precision"]) > 1e-9:
            ev.append(f"fold {f}: saved model recomputes auc={auc:.6f}/ap={ap:.6f} "
                      f"!= recorded {r['roc_auc']:.6f}/{r['average_precision']:.6f}")
        recomputed.append(f"f{f}:{auc:.4f}/{ap:.4f}")
    ok &= gate("evaluation completeness + saved models recompute the metrics", not ev,
               "5 folds x (roc_auc, average_precision); fold 2 flagged marginal (5 "
               "clusters); mean-of-folds carries the correlated-folds caveat; model "
               "params equal config; limitations present; each saved fold model "
               f"recomputes its recorded AUC/AP exactly: {', '.join(recomputed)}"
               if not ev else "; ".join(ev))

    # ---- 5. map checks ---------------------------------------------------------
    map_probs = []
    if mm["verdict"] != "MAP PRODUCED AFTER GATES PASSED":
        map_probs.append("map verdict not green")
    if mm["domain_cells"] != 2343343:
        map_probs.append(f"domain {mm['domain_cells']} != 2343343")
    with rasterio.open(MODELS / "susceptibility_rf_baseline_30m.tif") as ds:
        a = ds.read(1)
        m = a != ds.nodata
        if (ds.dtypes[0], ds.count, ds.crs.to_string(), ds.nodata) != (
                "float32", 1, "EPSG:32643", -9999.0):
            map_probs.append(f"tif profile {ds.dtypes[0]}, n={ds.nodata}, crs={ds.crs}")
        if int(m.sum()) != 2343343 or ds.shape != (2013, 2480):
            map_probs.append(f"tif valid cells {int(m.sum())}, shape {ds.shape}")
        vals = a[m]
    stats = {"min": float(vals.min()), "p05": float(np.percentile(vals, 5)),
             "p25": float(np.percentile(vals, 25)), "median": float(np.percentile(vals, 50)),
             "p75": float(np.percentile(vals, 75)), "p95": float(np.percentile(vals, 95)),
             "max": float(vals.max()), "mean": float(vals.mean())}
    for k, v in stats.items():
        if abs(v - mm["value_stats_over_domain"][k]) > 1e-6:
            map_probs.append(f"stat {k} differs from metadata")
    if "not a probability" not in mm["label"] or "forecast" not in mm["label"]:
        map_probs.append("label text missing required disclaimers")
    if sha256(MODELS / "susceptibility_rf_baseline_30m.tif") != \
            mm["outputs_sha256"]["susceptibility_rf_baseline_30m.tif"]:
        map_probs.append("tif sha256 != recorded")
    ok &= gate("map checks", not map_probs,
               f"verdict green; domain {int(m.sum())} cells (district minus 13,195 "
               f"invalid-predictor); float32, nodata -9999, EPSG:32643, 2013x2480; "
               f"stats recomputed from tif match metadata (min {stats['min']:.4f}, "
               f"median {stats['median']:.4f}, max {stats['max']:.4f}); label carries "
               "ranking/probability/forecast disclaimers; tif sha256 matches"
               if not map_probs else "; ".join(map_probs))

    # ---- 6. reproducibility -----------------------------------------------------
    before = {rel: sha256(ROOT / rel) for rel in P5_OUTPUTS}
    for script in ("scripts/p5_extract_features.py", "scripts/p5_train_baseline.py",
                   "scripts/p5_map.py"):
        code, _ = run([sys.executable, script])
        if code != 0:
            ok &= gate("reproducibility", False, f"{script} exit={code}")
            break
    else:
        diffs = [rel for rel in P5_OUTPUTS
                 if sha256(ROOT / rel) != before[rel]]
        ok &= gate("reproducibility (byte-identical regeneration)", not diffs,
                   f"re-ran p5_extract_features.py, p5_train_baseline.py, p5_map.py; "
                   f"all {len(P5_OUTPUTS)} outputs byte-identical"
                   if not diffs else f"CHANGED: {diffs}")

    verdict = "ALL PHASE 5 GATES PASSED" if ok else "PHASE 5 GATES FAILED"
    n_pass = sum(1 for r in results if r["passed"])
    payload = {"verdict": verdict, "n_gates": len(results), "n_passed": n_pass,
               "gates": results,
               "versions": {"python": sys.version.split()[0], "numpy": np.__version__,
                            "pandas": pd.__version__, "rasterio": rasterio.__version__}}
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print("=" * 78)
    print(f"{n_pass}/{len(results)} gates passed -- {verdict}")
    print(f"written -> {OUT.relative_to(ROOT)}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
