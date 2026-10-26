"""Phase 3 Stages 10-11 - cross-layer integrity checks and readiness metrics.

Nothing here produces a feature table. The predictor layers are sampled at
inventory points ONLY to count how many points land on a valid pixel; the sampled
values are discarded immediately and never written. That is a coverage test, not
a training table.

Checks
  1. every processed raster shares the grid transform, CRS and shape;
  2. nodata accounting per layer inside the district;
  3. coverage of the usable in-window point labels, per layer;
  4. spatial clustering of event groups, as the quantitative basis for the
     spatially blocked validation design (not a modelling result).

Outputs (data/processed/qa/):
  grid_alignment_report.json
  layer_inventory.csv
  readiness_metrics.json

Run: python scripts/p3_verify_processed.py
"""
from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"
GRID = PROC / "grid"
QA = PROC / "qa"
QA.mkdir(parents=True, exist_ok=True)

# predictor layers that are expected on the common 30 m grid
LAYERS = [
    "grid/district_mask_30m.tif",
    "dem/dem_glo30_30m_district.tif",
    "dem/slope_deg_30m_district.tif",
    "dem/aspect_deg_30m_district.tif",
    "dem/profile_curv_30m_district.tif",
    "dem/plan_curv_30m_district.tif",
    "landcover/landcover_worldcover2021_30m_district.tif",
    "soil/soil_clay_0-5cm_30m_district.tif",
    "soil/soil_clay_15-30cm_30m_district.tif",
    "soil/soil_sand_0-5cm_30m_district.tif",
    "soil/soil_sand_15-30cm_30m_district.tif",
    "soil/soil_silt_0-5cm_30m_district.tif",
    "soil/soil_silt_15-30cm_30m_district.tif",
    "soil/soil_bdod_0-5cm_30m_district.tif",
    "soil/soil_bdod_15-30cm_30m_district.tif",
    "soil/soil_soc_0-5cm_30m_district.tif",
    "soil/soil_soc_15-30cm_30m_district.tif",
    "soil/soil_cec_0-5cm_30m_district.tif",
    "soil/soil_cec_15-30cm_30m_district.tif",
    "soil/soil_cfvo_0-5cm_30m_district.tif",
    "soil/soil_cfvo_15-30cm_30m_district.tif",
    "rainfall/rainfall_annual_mean_30m_district.tif",
    "rainfall/rainfall_jjas_mean_30m_district.tif",
    "rainfall/rainfall_monthly_climatology_30m_district.tif",
    "geology/geology_class_30m_district.tif",
]


def main() -> None:
    spec = json.loads((GRID / "grid_spec.json").read_text(encoding="utf-8"))
    tf_ref = tuple(spec["transform"])
    with rasterio.open(GRID / "district_mask_30m.tif") as ds:
        dmask = ds.read(1) == 1
    H, W, crs = spec["height"], spec["width"], spec["work_crs"]
    nd = int(dmask.sum())

    # ---- 1-2. alignment and nodata accounting ------------------------------
    rows, problems = [], []
    for rel in LAYERS:
        p = PROC / rel
        assert p.exists(), f"missing expected layer: {rel}"
        with rasterio.open(p) as ds:
            tf = tuple(ds.transform)[:6]
            same_grid = (tf == tf_ref and str(ds.crs) == crs and ds.height == H and ds.width == W)
            if not same_grid:
                problems.append(f"{rel}: grid mismatch")
            arr = ds.read(masked=True)
            data = np.ma.masked_invalid(arr.astype("float64"))
            band_stats = []
            for b in range(ds.count):
                v = data[b]
                in_d = v[dmask]
                valid = int(in_d.count())
                band_stats.append({
                    "band": b + 1,
                    "description": ds.descriptions[b] or "",
                    "valid_in_district": valid,
                    "nodata_in_district": int(nd - valid),
                    "min": float(in_d.min()) if valid else None,
                    "median": float(np.ma.median(in_d)) if valid else None,
                    "max": float(in_d.max()) if valid else None,
                })
            rows.append({
                "layer": rel,
                "bands": ds.count,
                "dtype": ds.dtypes[0],
                "nodata_declared": str(ds.nodata),
                "same_grid": same_grid,
                "crs_tags": str(ds.crs),
                **{f"b{s['band']}_valid": s["valid_in_district"] for s in band_stats},
                **{f"b{s['band']}_min": s["min"] for s in band_stats},
                **{f"b{s['band']}_max": s["max"] for s in band_stats},
            })
            if ds.count == 1:
                st = band_stats[0]
                rows[-1].update({"valid_in_district": st["valid_in_district"],
                                 "nodata_in_district": st["nodata_in_district"],
                                 "nodata_pct": round(st["nodata_in_district"] / nd * 100, 3),
                                 "min": st["min"], "median": st["median"], "max": st["max"]})
    layer_df = pd.DataFrame(rows)
    layer_df.to_csv(QA / "layer_inventory.csv", index=False)

    # ---- 3. coverage of usable point labels --------------------------------
    suit = pd.read_csv(PROC / "inventory/inventory_spatial_suitability.csv")
    pts = suit[suit["spatial_suitability_use"] == "point_label_ok"].copy()
    pts_g = gpd.GeoDataFrame(
        pts, geometry=gpd.points_from_xy(pts["lon_original"], pts["lat_original"]),
        crs="EPSG:4326").to_crs(crs)

    coverage = {}
    for rel in LAYERS:
        if rel.startswith("grid/"):
            continue
        with rasterio.open(PROC / rel) as ds:
            vals = np.array([v[0] for v in ds.sample(
                [(g.x, g.y) for g in pts_g.geometry])], dtype="float64")
            ok = np.isfinite(vals)
            if ds.nodata is not None:
                ok &= vals != ds.nodata
        coverage[rel] = {
            "points_tested": int(len(vals)),
            "valid": int(ok.sum()),
            "nodata": int((~ok).sum()),
            "coverage_pct": round(float(ok.mean() * 100), 2),
        }

    # ---- 4. clustering of event groups (basis for spatial blocking) --------
    ev = pts[pts["label_role"] == "EVENT_POINT_IN_WINDOW"].copy()
    ev_g = gpd.GeoDataFrame(ev, geometry=gpd.points_from_xy(ev["lon_original"],
                                                            ev["lat_original"]),
                            crs="EPSG:4326").to_crs(crs)
    grp = ev_g.groupby("event_group_id").geometry.apply(
        lambda s: s.union_all().centroid).reset_index()
    coords = np.column_stack([grp.geometry.x, grp.geometry.y])
    tree = cKDTree(coords)
    dist, _ = tree.query(coords, k=2)
    nn = dist[:, 1]

    cluster_counts = {}
    for thr in (250, 500, 1000, 2000, 5000):
        pairs = tree.query_pairs(thr, output_type="ndarray")
        parent = list(range(len(coords)))

        def find(a):
            while parent[a] != a:
                parent[a] = parent[parent[a]]
                a = parent[a]
            return a

        for a, b in pairs:
            ra, rb = find(int(a)), find(int(b))
            if ra != rb:
                parent[rb] = ra
        cluster_counts[f"{thr}_m"] = len({find(i) for i in range(len(coords))})

    yr = ev["event_year"].value_counts().sort_index()
    metrics = {
        "point_label_records_tested": int(len(pts)),
        "in_window_point_records": int(len(ev)),
        "distinct_event_groups": int(len(grp)),
        "nearest_neighbour_distance_m": {
            "median": round(float(np.median(nn)), 1),
            "p10": round(float(np.percentile(nn, 10)), 1),
            "p25": round(float(np.percentile(nn, 25)), 1),
            "min": round(float(nn.min()), 1),
            "n_within_250m": int((nn <= 250).sum()),
            "n_within_1000m": int((nn <= 1000).sum()),
        },
        "single_linkage_clusters": cluster_counts,
        "records_per_year": {str(int(k)): int(v) for k, v in yr.items()},
        "share_2018_pct": round(float((ev["event_year"] == 2018).mean() * 100), 1),
        "date_precision": ev["date_certainty"].value_counts().to_dict(),
        "coverage_by_layer": coverage,
        "layers_off_grid": problems,
        "grid": {"crs": crs, "cell_m": spec["cell_size_m"], "shape": [H, W],
                 "district_pixels": nd},
    }
    (QA / "readiness_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    (QA / "grid_alignment_report.json").write_text(
        json.dumps({"all_on_grid": len(problems) == 0, "problems": problems,
                    "n_layers": len(LAYERS),
                    "layers": layer_df.to_dict("records")}, indent=2), encoding="utf-8")

    print(json.dumps({k: metrics[k] for k in
                      ("point_label_records_tested", "in_window_point_records",
                       "distinct_event_groups", "nearest_neighbour_distance_m",
                       "single_linkage_clusters", "share_2018_pct",
                       "layers_off_grid", "grid")}, indent=2))
    print("\ncoverage (usable point labels on a valid pixel):")
    for k, v in coverage.items():
        print(f"  {k:56s} {v['valid']}/{v['points_tested']} = {v['coverage_pct']:.2f}%")
    print(f"\nall {len(LAYERS)} layers on the common grid: {len(problems) == 0}")
    print(layer_df[["layer", "bands", "dtype", "valid_in_district", "nodata_pct"]]
          .to_string(index=False))


if __name__ == "__main__":
    main()
