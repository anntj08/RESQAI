"""Phase 5 — susceptibility map from the RF baseline (final refit).

Runs ONLY after the extraction checks and the per-fold evaluation passed; this
is asserted here from the saved JSONs, not taken on trust.

  domain   district mask AND every band of every predictor layer valid
  model    the same single RF configuration refit on ALL 2,460 committed
           points. This final model is NOT cross-validated: its skill
           characterisation is the per-fold evaluation (fold_metrics.json).
  value    predict_proba[:, 1] positive-class vote share — a RELATIVE RANKING
           score conditional on the observed inventory, NOT a calibrated
           probability, forecast, warning or timing prediction.

Outputs (data/processed/models/):
  susceptibility_rf_baseline_30m.tif   float32, declared nodata -9999
  susceptibility_rf_baseline.png       PNG rendering with the label text
  map_metadata.json                    domain counts, value stats, label,
                                       provenance, sha256 of inputs+outputs

Run:  python scripts/p5_map.py
"""
from __future__ import annotations

import hashlib
import io
import json
import pathlib
import sys

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import rasterio
import sklearn
from sklearn.ensemble import RandomForestClassifier

ROOT = pathlib.Path(__file__).resolve().parents[1]
CFG = json.loads((ROOT / "configs" / "p5_baseline.json").read_text(encoding="utf-8"))
PROC = ROOT / "data" / "processed"
MODELS = PROC / "models"
FEAT_CSV = MODELS / "features_point_table.csv"
OUT_TIF = MODELS / "susceptibility_rf_baseline_30m.tif"
OUT_PNG = MODELS / "susceptibility_rf_baseline.png"
OUT_JSON = MODELS / "map_metadata.json"


def sha256(p: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def save_png(fig, path: pathlib.Path) -> None:
    """Deterministic PNG (metadata stripped via PIL re-save)."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    buf.seek(0)
    from PIL import Image
    Image.open(buf).save(path, format="png")
    plt.close(fig)


def main() -> int:
    mp = CFG["map"]
    spec = CFG["features"]["spec"]
    feat_names = [e["name"] for e in spec]
    mcfg = CFG["model"]

    # ---- gates: extraction + fold evaluation must have passed ----------------
    ext = json.loads((MODELS / "extraction_checks.json").read_text(encoding="utf-8"))
    fm = json.loads((MODELS / "fold_metrics.json").read_text(encoding="utf-8"))
    assert ext["verdict"] == "ALL EXTRACTION CHECKS PASSED", "extraction checks not green"
    assert fm["verdict"] == "PER-FOLD EVALUATION COMPLETE", "fold evaluation not complete"

    tab = pd = None
    import pandas as pd
    tab = pd.read_csv(FEAT_CSV)
    X_all = tab[feat_names].to_numpy(dtype=float)
    y_all = tab["label"].to_numpy(dtype=int)
    assert len(X_all) == 2460

    # ---- domain: district AND every band valid -------------------------------
    with rasterio.open(PROC / "grid" / "district_mask_30m.tif") as ds:
        dmask = ds.read(1) == 1
        tf, shape = ds.transform, (ds.height, ds.width)
        crs = ds.crs
    valid = dmask.copy()
    per_layer_invalid = {}
    spec_by_file: dict[str, list[dict]] = {}
    for e in spec:
        spec_by_file.setdefault(e["file"], []).append(e)
    n_bands = 0
    for rel, entries in spec_by_file.items():
        with rasterio.open(PROC / rel) as ds:
            assert ds.shape == shape, f"{rel} shape {ds.shape} != grid {shape}"
            nod = ds.nodata
            for e in entries:
                b = int(e["band"])
                a = ds.read(b)
                good = np.isfinite(a.astype("float64"))
                if nod is not None:
                    good &= a != nod
                valid &= good
                per_layer_invalid[e["name"]] = int((~good).sum())
                n_bands += 1
    assert n_bands == 35
    n_valid = int(valid.sum())
    expected = int(dmask.sum()) - 13195   # 13,195 invalid-predictor cells (Phase 4 QA)
    assert n_valid == expected, f"domain {n_valid} != district minus known invalid {expected}"
    print(f"map domain: {n_valid} cells = district {int(dmask.sum())} - 13,195 invalid-predictor")

    # ---- full-grid extraction (band at a time; invalid filled with 0) --------
    idx = np.flatnonzero(valid)
    X_map = np.empty((n_valid, len(feat_names)), dtype=np.float32)
    for j, e in enumerate(spec):
        with rasterio.open(PROC / e["file"]) as ds:
            a = ds.read(int(e["band"])).astype(np.float32)
        col = a.reshape(-1)[idx]
        assert np.isfinite(col).all() and (ds.nodata is None or (col != ds.nodata).all())
        X_map[:, j] = col

    # ---- final refit on ALL committed points (not cross-validated) -----------
    final = RandomForestClassifier(
        n_estimators=mcfg["n_estimators"], criterion=mcfg["criterion"],
        min_samples_leaf=mcfg["min_samples_leaf"], max_features=mcfg["max_features"],
        bootstrap=mcfg["bootstrap"], class_weight=mcfg["class_weight"],
        random_state=mcfg["random_state"], n_jobs=mcfg["n_jobs"])
    final.fit(X_all, y_all)
    proba = final.predict_proba(X_map)[:, 1].astype(np.float32)
    joblib.dump(final, MODELS / "final_rf_refit_all_points.joblib")

    # ---- raster ----------------------------------------------------------------
    out = np.full(shape, float(mp["nodata"]), dtype=np.float32)
    out.reshape(-1)[idx] = proba
    profile = dict(driver="GTiff", height=shape[0], width=shape[1], count=1,
                   dtype="float32", crs=crs, transform=tf, nodata=float(mp["nodata"]),
                   compress="deflate")
    with rasterio.open(OUT_TIF, "w", **profile) as dst:
        dst.write(out, 1)
    stats = {k: float(np.percentile(proba, p)) for k, p in
             [("min", 0), ("p05", 5), ("p25", 25), ("median", 50),
              ("p75", 75), ("p95", 95), ("max", 100)]}
    stats["mean"] = float(proba.mean())
    print("value stats:", {k: round(v, 4) for k, v in stats.items()})

    # ---- PNG -------------------------------------------------------------------
    lo, hi = float(np.percentile(proba, 2)), float(np.percentile(proba, 98))
    fig, ax = plt.subplots(figsize=(8.6, 7.2), dpi=110)
    img = np.full(shape, np.nan, dtype=np.float32)
    img.reshape(-1)[idx] = proba
    im = ax.imshow(img, cmap="viridis", vmin=lo, vmax=hi,
                   extent=[583110, 657510, 1264170, 1324560])
    ax.set_title("Wayanad — RF landslide susceptibility ranking (RF baseline, Phase 5)\n"
                 "relative ranking conditional on the observed inventory —\n"
                 "NOT a probability, forecast, warning, or timing prediction", fontsize=10)
    ax.set_xlabel("Easting (EPSG:32643, m)")
    ax.set_ylabel("Northing (m)")
    cb = fig.colorbar(im, ax=ax, shrink=0.85)
    cb.set_label("RF positive-class vote share (relative ranking)")
    fig.tight_layout()
    save_png(fig, OUT_PNG)

    payload = {
        "verdict": "MAP PRODUCED AFTER GATES PASSED",
        "label": mp["label"],
        "value": mp["value"],
        "domain_rule": mp["domain"],
        "model_type": mcfg["type"],
        "model_params": {k: v for k, v in mcfg.items() if k != "rationale"},
        "random_seed": CFG["random_seed"],
        "refit_note": "final model refit on ALL 2,460 committed points; NOT cross-validated; "
                      "skill characterisation is the per-fold evaluation (fold_metrics.json)",
        "feature_names": feat_names,
        "domain_cells": n_valid,
        "district_cells": int(dmask.sum()),
        "invalid_predictor_cells": int(dmask.sum()) - n_valid,
        "per_layer_invalid_at": per_layer_invalid,
        "nodata_value": float(mp["nodata"]),
        "output_raster_crs": str(crs),
        "value_stats_over_domain": stats,
        "inputs_sha256": {
            "configs/p5_baseline.json": sha256(ROOT / "configs" / "p5_baseline.json"),
            "data/processed/models/features_point_table.csv": sha256(FEAT_CSV),
        },
        "outputs_sha256": {"susceptibility_rf_baseline_30m.tif": sha256(OUT_TIF),
                           "susceptibility_rf_baseline.png": sha256(OUT_PNG)},
        "versions": {"python": sys.version.split()[0], "numpy": np.__version__,
                     "sklearn": sklearn.__version__, "rasterio": rasterio.__version__},
        "not_claimed": [
            "the map is NOT a probability of failure and NOT a forecast, warning, or timing "
            "prediction of any kind",
            "values are RF vote shares (relative ranking) conditional on an inventory that is "
            "92.3% single-year (2018); they must not be read as calibrated likelihoods",
            "background labels mean 'no mapped event in the available inventory', not stable ground",
            "13,195 district cells lack valid predictor values and are excluded (nodata -9999)",
            "skill is characterised by the spatially held-out fold evaluation, not by this map",
        ],
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print("=" * 78)
    print("MAP PRODUCED AFTER GATES PASSED")
    print("label:", mp["label"])
    print(f"written -> {OUT_TIF.relative_to(ROOT)}, {OUT_PNG.relative_to(ROOT)}, "
          f"{OUT_JSON.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
