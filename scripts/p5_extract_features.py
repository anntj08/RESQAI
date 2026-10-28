"""Phase 5 — predictor extraction at the committed Phase 4 points.

Reads the 24 Phase 3 predictor layers (35 bands) at the 2,460 committed
analysis points and writes one feature table + one checks file:

  data/processed/models/features_point_table.csv
      the 12 provenance columns from fold_assignments.csv, carried through
      UNCHANGED, followed by the 35 features in the config's fixed order.
      Every feature is the value of the source cell CONTAINING the point:
      no resampling, no interpolation, source rasters opened read-only.

  data/processed/models/extraction_checks.json
      every gate below with its measured detail, so the training script and
      the verifier can re-assert rather than re-derive.

Checks (all must pass; exit 1 otherwise):
  1 grid alignment        all 24 layers share one grid == grid_spec.json
  2 points in bounds      every point maps into the grid via rowcol
  3 finiteness            all 35 x 2,460 sampled values finite
  4 declared nodata       no sampled value equals a layer's declared nodata
  5 CHIRPS sentinel       no rainfall feature <= -9998 (sentinel is -9999 and
                          was masked in Phase 3; re-asserted here explicitly)
  6 soil plausibility     the 14 soil features lie in the config's physical
                          ranges (scale factors were ALREADY applied in
                          scripts/p3_soil.py — they are NOT re-applied here)
  7 categorical classes   land cover in WorldCover codes 10..90, geology in
                          1..5 (observed sets recorded)
  8 provenance preserved  point ids unique; the 12 provenance columns read
                          back from the CSV byte-equal to fold_assignments.csv;
                          role/label/fold counts match fold_summary.json

No model is fitted here. Run:  python scripts/p5_extract_features.py
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys

import numpy as np
import pandas as pd
import rasterio
from rasterio.transform import rowcol

ROOT = pathlib.Path(__file__).resolve().parents[1]
CFG = json.loads((ROOT / "configs" / "p5_baseline.json").read_text(encoding="utf-8"))
PROC = ROOT / "data" / "processed"
MODELS = PROC / "models"
OUT_CSV = MODELS / "features_point_table.csv"
OUT_JSON = MODELS / "extraction_checks.json"
PROV_COLS = ["point_id", "role", "label", "event_group_id", "event_year",
             "cluster_id", "block_id", "fold", "x_32643", "y_32643",
             "lon_4326", "lat_4326"]

results: list[dict] = []


def check(name: str, ok: bool, detail: str) -> bool:
    results.append({"check": name, "passed": bool(ok), "detail": detail})
    print(f"[{'PASS' if ok else 'FAIL'}] {name}")
    print(f"       {detail}")
    return bool(ok)


def sha256(p: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    MODELS.mkdir(parents=True, exist_ok=True)
    spec = CFG["features"]["spec"]
    fa = pd.read_csv(PROC / "sampling" / "fold_assignments.csv")
    inv = pd.read_csv(PROC / "qa" / "layer_inventory.csv").set_index("layer")
    grid = json.loads((PROC / "grid" / "grid_spec.json").read_text(encoding="utf-8"))

    ok = True
    ok &= check("input counts", len(fa) == 2460 and fa["point_id"].is_unique
                and (fa["role"] == "positive").sum() == 363
                and (fa["role"] == "background").sum() == 2097,
                f"{len(fa)} points ({(fa['role'] == 'positive').sum()} positive /"
                f" {(fa['role'] == 'background').sum()} background), ids unique")

    # ---- 1. grid alignment ---------------------------------------------------
    ref_tf, ref_shape, ref_crs = None, None, None
    grids: dict[tuple, list[str]] = {}
    layer_paths: list[tuple[str, pathlib.Path]] = []
    for entry in spec:
        rel = entry["file"]
        if (entry["name"], rel) not in [(a, b) for a, b in layer_paths]:
            layer_paths.append((entry["name"], rel))
    seen_files = {rel for _, rel in layer_paths}
    with rasterio.open(PROC / "grid" / "district_mask_30m.tif") as ds:
        ref_tf, ref_shape, ref_crs = ds.transform, (ds.height, ds.width), ds.crs
        grids[(str(ds.transform), ds.height, ds.width, str(ds.crs))] = ["grid/district_mask_30m.tif"]
    for rel in sorted(seen_files):
        with rasterio.open(PROC / rel) as ds:
            key = (str(ds.transform), ds.height, ds.width, str(ds.crs))
            grids.setdefault(key, []).append(rel)
    aligned = (len(grids) == 1
               and ref_shape == (grid["height"], grid["width"])
               and tuple(float(v) for v in ref_tf)[:6]
                   == tuple(float(v) for v in grid["transform"])
               and ref_crs.to_string() == "EPSG:32643")
    tf_match = (tuple(float(v) for v in ref_tf)[:6]
                == tuple(float(v) for v in grid["transform"]))
    ok &= check("grid alignment", aligned,
                f"{len(seen_files)} layer files + district mask: "
                f"{len(grids)} distinct grid(s); reference shape {ref_shape}, "
                f"crs {ref_crs}, transform matches grid_spec.json: {tf_match}")

    # ---- 2. points in bounds -------------------------------------------------
    tf = ref_tf
    rows, cols = rowcol(tf, fa["x_32643"].to_numpy(), fa["y_32643"].to_numpy())
    rows = np.asarray(rows)
    cols = np.asarray(cols)
    inb = bool(((rows >= 0) & (rows < ref_shape[0])
                & (cols >= 0) & (cols < ref_shape[1])).all())
    ok &= check("points in bounds", inb,
                f"all {len(fa)} points map to rows {rows.min()}..{rows.max()}, "
                f"cols {cols.min()}..{cols.max()} inside {ref_shape}")

    # ---- sample every feature (cell containing the point) --------------------
    xy = list(zip(fa["x_32643"].to_numpy(), fa["y_32643"].to_numpy()))
    feats: dict[str, np.ndarray] = {}
    band_info: dict[str, dict] = {}
    for entry in spec:
        rel = entry["file"]
        path = PROC / rel
        band = int(entry["band"])
        with rasterio.open(path) as ds:  # read-only use
            arr = np.array([v for v in ds.sample(xy, indexes=band)]).ravel()
        feats[entry["name"]] = arr
        nod = inv.loc[rel, "nodata_declared"]
        nod = float(nod) if pd.notna(nod) else None
        band_info[entry["name"]] = {
            "file": rel, "band": band, "kind": entry["kind"],
            "dtype": str(arr.dtype), "declared_nodata": nod,
            "min_at_points": float(np.nanmin(arr)), "max_at_points": float(np.nanmax(arr)),
            "sha256": sha256(path),
        }
    X = pd.DataFrame(feats, index=fa.index)
    feat_names = [e["name"] for e in spec]
    X = X[feat_names]
    assert list(X.columns) == feat_names, "feature order changed"

    # ---- 3./4. finiteness + declared nodata ---------------------------------
    allfinite = bool(np.isfinite(X.to_numpy(dtype=float)).all())
    ok &= check("all features finite", allfinite,
                f"{X.shape[0]} x {X.shape[1]} values, "
                f"{int((~np.isfinite(X.to_numpy(dtype=float))).sum())} non-finite")
    badnod = {n: float((X[n] == band_info[n]["declared_nodata"]).sum())
              for n in feat_names if band_info[n]["declared_nodata"] is not None}
    badnod = {n: c for n, c in badnod.items() if c > 0}
    ok &= check("no declared nodata at points", not badnod,
                f"no sampled value equals its layer's declared nodata"
                + (f"; violations: {badnod}" if badnod else ""))

    # ---- 5. CHIRPS sentinel --------------------------------------------------
    rain_cols = [n for n in feat_names if n.startswith("rain_")]
    vmin = float(min(X[c].min() for c in rain_cols))
    ok &= check("rainfall sentinel rule", vmin > -9998,
                f"min over {len(rain_cols)} rainfall features at points = {vmin:.4f}"
                f" (> -9998; sentinel -9999 was already masked in Phase 3)")

    # ---- 6. soil plausibility -----------------------------------------------
    soil_cols = [e for e in spec if e["name"].startswith("soil_")]
    viol = []
    for e in soil_cols:
        lo, hi = e["plausible"]
        c = e["name"]
        if X[c].min() < lo or X[c].max() > hi:
            viol.append(f"{c}=[{X[c].min():.3f},{X[c].max():.3f}] not in [{lo},{hi}]")
    ok &= check("soil plausibility (physical units)", not viol,
                f"{len(soil_cols)} soil features inside config ranges"
                + (f"; violations: {viol}" if viol else "")
                + " (SoilGrids scale factors were applied in Phase 3; not re-applied)")

    # ---- 7. categorical classes ---------------------------------------------
    lc = sorted(set(int(v) for v in X["landcover_class"]))
    gl = sorted(set(int(v) for v in X["geology_class"]))
    lc_ok = set(lc) <= set(next(e["classes"] for e in spec if e["name"] == "landcover_class"))
    gl_ok = set(gl) <= set(next(e["classes"] for e in spec if e["name"] == "geology_class"))
    ok &= check("categorical classes", lc_ok and gl_ok,
                f"landcover classes at points {lc}; geology classes at points {gl}")

    # ---- 8. provenance -------------------------------------------------------
    out = pd.concat([fa[PROV_COLS].copy(), X], axis=1)
    out.to_csv(OUT_CSV, index=False)
    back = pd.read_csv(OUT_CSV)
    prov_ok = back[PROV_COLS].equals(fa[PROV_COLS])
    counts_ok = True
    fs = json.loads((PROC / "sampling" / "fold_summary.json").read_text(encoding="utf-8"))
    for f in fs["folds"]:
        t = fa[fa["fold"] == f["fold"]]
        counts_ok &= bool((t["role"] == "positive").sum() == f["test_positives"]
                          and (t["role"] == "background").sum() == f["test_background"])
    ok &= check("provenance preserved", prov_ok and counts_ok,
                f"12 provenance columns round-trip byte-equal to fold_assignments.csv:"
                f" {prov_ok}; per-fold test counts equal fold_summary.json: {counts_ok}")

    payload = {
        "verdict": "ALL EXTRACTION CHECKS PASSED" if ok else "EXTRACTION CHECKS FAILED",
        "n_points": int(len(out)),
        "feature_names": feat_names,
        "feature_order_source": "configs/p5_baseline.json features.spec",
        "features": band_info,
        "checks": results,
        "inputs_sha256": {
            "configs/p5_baseline.json": sha256(ROOT / "configs" / "p5_baseline.json"),
            "data/processed/sampling/fold_assignments.csv":
                sha256(PROC / "sampling" / "fold_assignments.csv"),
            "data/processed/sampling/fold_drops.csv":
                sha256(PROC / "sampling" / "fold_drops.csv"),
            "data/processed/qa/layer_inventory.csv":
                sha256(PROC / "qa" / "layer_inventory.csv"),
        },
        "outputs": {"features_point_table.csv": OUT_CSV.name,
                    "extraction_checks.json": OUT_JSON.name},
        "versions": {"python": sys.version.split()[0],
                     "numpy": np.__version__, "pandas": pd.__version__,
                     "rasterio": rasterio.__version__},
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print("=" * 78)
    print(payload["verdict"])
    print(f"written -> {OUT_CSV.relative_to(ROOT)}")
    print(f"          {OUT_JSON.relative_to(ROOT)}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
