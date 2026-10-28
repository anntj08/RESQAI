"""Probe the rectangular RF==0 plateaus seen in the LSZ-vs-RF overlay figure.

The overlay figure (outputs/lsz_rf_comparison/overlay_map.png) shows two large,
straight-edged, uniformly dark regions (top-right ~10x15 km, south-central
~19x8 km) where the RF vote-share raster reads ~0. Straight edges are NOT a
terrain pattern; they suggest undeclared nodata / sentinel values inside the
Phase 5 map's valid domain (AGENTS.md care rule 3: CHIRPS stores nodata as
-9999 without declaring it). This probe answers, with numbers:

  1. RF raster: connected components of (rf == 0) within the district mask;
     size + bounding box + rectangularity (fill ratio) of the largest ones.
  2. For every predictor raster used by the map: the fraction of cells inside
     the largest plateau that equals -9999, 0, or the layer's declared nodata,
     vs the fraction over the rest of the district (contrast test).
  3. The RF raster's own nodata accounting: cells == declared nodata, cells
     == 0.0, and where Phase 5 metadata says they should be.

Evidence -> data/interim/lsz_comparison_probe/probe_results.json
(no upstream file is modified)

Run:  python scripts/probe_rf_zero_plateaus.py
"""
from __future__ import annotations

import json
import pathlib
import sys

import numpy as np
import rasterio
from scipy import ndimage

ROOT = pathlib.Path(__file__).resolve().parents[1]
MASK = ROOT / "data" / "processed" / "grid" / "district_mask_30m.tif"
RF_TIF = ROOT / "data" / "processed" / "models" / "susceptibility_rf_baseline_30m.tif"
EXT_CHECKS = ROOT / "data" / "processed" / "models" / "extraction_checks.json"
OUT = ROOT / "data" / "interim" / "lsz_comparison_probe" / "probe_results.json"


def main() -> int:
    with rasterio.open(MASK) as ds:
        dmask = ds.read(1) == 1
        tf = ds.transform
    with rasterio.open(RF_TIF) as ds:
        rf = ds.read(1)
        nod = ds.nodata

    rec: dict = {"rf_nodata_declared": nod,
                 "rf_cells_total_grid": int(rf.size),
                 "rf_cells_nodata": int((rf == nod).sum()),
                 "rf_cells_zero_within_district": int(((rf == 0) & dmask).sum()),
                 "rf_cells_nodata_within_district": int(((rf == nod) & dmask).sum()),
                 "district_cells": int(dmask.sum())}

    # ---- 1. connected components of rf == 0 within the district -------------
    zero = (rf == 0) & dmask
    lab, n = ndimage.label(zero)
    if n:
        sizes = np.bincount(lab.ravel())[1:]
        order = np.argsort(sizes)[::-1]
        objs = ndimage.find_objects(lab)
        comps = []
        for rank, i in enumerate(order[:6], start=1):
            sl = objs[i]
            h = sl[0].stop - sl[0].start
            w = sl[1].stop - sl[1].start
            comps.append({
                "rank": rank,
                "cells": int(sizes[i]),
                "area_km2": round(int(sizes[i]) * 900 / 1e6, 2),
                "bbox_rows": [int(sl[0].start), int(sl[0].stop)],
                "bbox_cols": [int(sl[1].start), int(sl[1].stop)],
                "bbox_km": [round(w * 30 / 1000, 2), round(h * 30 / 1000, 2)],
                "bbox_fill_ratio": round(float(sizes[i] / (h * w)), 4),
            })
        rec["rf_zero_components"] = {"n_components": int(n), "largest": comps}
        biggest = comps[0]
        win = (slice(biggest["bbox_rows"][0], biggest["bbox_rows"][1]),
               slice(biggest["bbox_cols"][0], biggest["bbox_cols"][1]))
        win2 = None
        if len(comps) > 1:
            c2 = comps[1]
            win2 = (slice(c2["bbox_rows"][0], c2["bbox_rows"][1]),
                    slice(c2["bbox_cols"][0], c2["bbox_cols"][1]))
    else:
        rec["rf_zero_components"] = {"n_components": 0}
        win = win2 = None

    # ---- 2. predictor values inside vs outside the plateaus ------------------
    feats = json.loads(EXT_CHECKS.read_text(encoding="utf-8"))["features"]
    rows = []
    for name, spec in feats.items():
        p = ROOT / "data" / "processed" / spec["file"]
        if not p.exists():
            rows.append({"feature": name, "error": f"missing file {spec['file']}"})
            continue
        with rasterio.open(p) as ds:
            band = ds.read(spec.get("band", 1))
            dec = ds.nodata
        decl = spec.get("declared_nodata")
        base = {"feature": name, "file": spec["file"],
                "declared_nodata_raster": None if dec is None else float(dec),
                "declared_nodata_extraction_record": None if decl is None else float(decl)}
        ins = band[win] if win else band
        for label, sel in (("plateau1", band[win]),) + \
                          ((("plateau2", band[win2]),) if win2 else ()) + \
                          (("rest_of_district", band[dmask & ~_expand(zero)]),):
            v = sel[np.isfinite(sel)]
            if v.size == 0:
                base[label] = {"note": "no cells"}
                continue
            base[label] = {
                "n": int(v.size),
                "min": round(float(v.min()), 4),
                "median": round(float(np.median(v)), 4),
                "max": round(float(v.max()), 4),
                "frac_eq_-9999": round(float((v == -9999).mean()), 6),
                "frac_eq_0": round(float((v == 0).mean()), 6),
                "frac_eq_declared": round(
                    float((v == dec).mean()) if dec is not None else 0.0, 6),
            }
        rows.append(base)
    rec["predictor_probe"] = rows

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: rec[k] for k in
                      ("rf_nodata_declared", "rf_cells_nodata",
                       "rf_cells_zero_within_district",
                       "rf_cells_nodata_within_district",
                       "rf_zero_components")}, indent=2))
    print(f"evidence -> {OUT.relative_to(ROOT)}")
    return 0


def _expand(zero: np.ndarray) -> np.ndarray:
    """Dilate the zero-plateau mask a little so 'rest_of_district' excludes rims."""
    return ndimage.binary_dilation(zero, iterations=5)


if __name__ == "__main__":
    sys.exit(main())
