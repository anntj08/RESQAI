"""Phase 3 Stage 4 - ESA WorldCover 2021 v200: verify, resample, quantify loss.

Categorical product, so:
  * class codes are never interpolated;
  * 10 m -> 30 m aggregation uses GDAL mode (majority class of the contributing
    cells), not nearest or bilinear;
  * the class composition is measured on the native 10 m grid and again on the
    produced 30 m grid, so the information cost of the downsample is a number in
    the report rather than a claim.

Outputs (data/processed/landcover/):
  landcover_worldcover2021_30m_district.tif
  landcover_class_legend.csv
  landcover_validation.json

Run: python scripts/p3_landcover.py
"""
from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.features import rasterize
from rasterio.warp import reproject
from rasterio.windows import from_bounds

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "raw" / "landcover/ESA_WorldCover_10m_2021_v200_N09E075_Map.tif"
GRID = ROOT / "data" / "processed" / "grid"
OUT = ROOT / "data" / "processed" / "landcover"
OUT.mkdir(parents=True, exist_ok=True)
NODATA = 0

LEGEND = {
    10: "Tree cover", 20: "Shrubland", 30: "Grassland", 40: "Cropland", 50: "Built-up",
    60: "Bare / sparse vegetation", 70: "Snow and ice", 80: "Permanent water bodies",
    90: "Herbaceous wetland", 95: "Mangroves", 100: "Moss and lichen",
}


def main() -> None:
    spec = json.loads((GRID / "grid_spec.json").read_text(encoding="utf-8"))
    tf_grid = rasterio.transform.Affine(*spec["transform"])
    H, W, cell, crs = spec["height"], spec["width"], spec["cell_size_m"], spec["work_crs"]
    with rasterio.open(GRID / "district_mask_30m.tif") as ds:
        dmask = ds.read(1) == 1
    gadm = gpd.read_file(GRID / "wayanad_gadm_32643.gpkg")
    gadm4326 = gadm.to_crs("EPSG:4326")

    rep: dict = {}

    with rasterio.open(SRC) as ds:
        rep["product"] = {
            "path": str(SRC.relative_to(ROOT)),
            "driver": ds.driver,
            "shape": [ds.height, ds.width],
            "dtype": ds.dtypes[0],
            "crs": str(ds.crs),
            "res_deg": list(ds.res),
            "nodata_declared": ds.nodata,
            "compression": str(ds.compression),
            "size_mb": round(SRC.stat().st_size / 1e6, 1),
            "tags": {k: v for k, v in ds.tags().items()},
        }
        minx, miny, maxx, maxy = gadm4326.total_bounds
        pad = 0.02
        win = from_bounds(minx - pad, miny - pad, maxx + pad, maxy + pad, ds.transform)
        win = win.round_offsets().round_lengths()
        native = ds.read(1, window=win)
        tf_nat = ds.window_transform(win)
        rep["native_window"] = {"shape": list(native.shape), "transform": list(tf_nat)[:6],
                                "offset": [win.row_off, win.col_off]}

    # district mask on the native 10 m window (pixel-centre rule)
    nat_mask = rasterize([(g, 1) for g in gadm4326.geometry], out_shape=native.shape,
                         transform=tf_nat, fill=0, dtype="uint8").astype(bool)
    rep["native_window"]["district_pixels"] = int(nat_mask.sum())

    # Row-wise geodesic pixel area: a 1/12000 deg cell is not 100 m2 at 11.5 N,
    # so a flat 10x10 m assumption would overstate the area by ~11 %.
    from pyproj import Geod
    geod = Geod(ellps="WGS84")
    res_deg = abs(tf_nat.e)
    row_area = np.empty(native.shape[0])
    for r in range(native.shape[0]):
        lat_c = tf_nat.f + (r + 0.5) * tf_nat.e
        _, _, dy = geod.inv(tf_nat.c, lat_c, tf_nat.c, lat_c + res_deg)
        _, _, dx = geod.inv(tf_nat.c, lat_c, tf_nat.c + res_deg, lat_c)
        row_area[r] = dx * dy
    nat_area_km2 = float((nat_mask.sum(axis=1) * row_area).sum() / 1e6)
    rep["native_window"]["district_area_km2"] = round(nat_area_km2, 1)
    rep["native_window"]["pixel_area_m2_at_centre_lat"] = round(float(row_area.mean()), 2)
    rep["native_window"]["naive_100m2_area_km2"] = round(float(nat_mask.sum()) * 100 / 1e6, 1)

    # ---- native (10 m) class composition -----------------------------------
    vals, counts = np.unique(native[nat_mask], return_counts=True)
    nat_counts = {int(v): int(c) for v, c in zip(vals, counts)}
    nat_total = int(counts.sum())
    rep["native_classes"] = {
        str(v): {"name": LEGEND.get(int(v), "unknown"), "pixels": int(c),
                 "share_pct": round(c / nat_total * 100, 3)}
        for v, c in nat_counts.items()
    }
    rep["native_unexpected_codes"] = sorted(v for v in nat_counts if v not in LEGEND and v != NODATA)

    # ---- sub-30m heterogeneity in the native grid ---------------------------
    # A 3x3 block of native cells is the information a single 30 m cell replaces.
    sub = native[1:-1, 1:-1]
    differs = (
        (native[:-2, :-2] != sub) | (native[:-2, 1:-1] != sub) | (native[:-2, 2:] != sub)
        | (native[1:-1, :-2] != sub) | (native[1:-1, 2:] != sub)
        | (native[2:, :-2] != sub) | (native[2:, 1:-1] != sub) | (native[2:, 2:] != sub)
    )
    inner_mask = nat_mask[1:-1, 1:-1]
    rep["native_heterogeneity_3x3"] = {
        "cells_considered": int(inner_mask.sum()),
        "pct_with_any_differing_neighbour": round(float(differs[inner_mask].mean() * 100), 2),
        "interpretation": "share of 30 m-equivalent blocks that are NOT class-pure; a mode "
                          "resample necessarily discards the minority classes in these blocks",
    }

    # ---- aggregate to the study grid ---------------------------------------
    lc = np.full((H, W), NODATA, dtype="uint8")
    with rasterio.open(SRC) as ds:
        reproject(
            source=rasterio.band(ds, 1), destination=lc,
            src_transform=ds.transform, src_crs=ds.crs,
            dst_transform=tf_grid, dst_crs=crs,
            src_nodata=NODATA, dst_nodata=NODATA,
            resampling=Resampling.mode,
        )
    lc_district = lc.copy()
    lc_district[~dmask] = NODATA

    # nearest-neighbour control: quantify what mode is buying / costing
    lc_nn = np.full((H, W), NODATA, dtype="uint8")
    with rasterio.open(SRC) as ds:
        reproject(source=rasterio.band(ds, 1), destination=lc_nn,
                  src_transform=ds.transform, src_crs=ds.crs,
                  dst_transform=tf_grid, dst_crs=crs,
                  src_nodata=NODATA, dst_nodata=NODATA, resampling=Resampling.nearest)

    vals2, counts2 = np.unique(lc_district[dmask], return_counts=True)
    new_total = int(counts2.sum())
    res_classes = {int(v): int(c) for v, c in zip(vals2, counts2)}

    rows = []
    for code in sorted(set(nat_counts) | set(res_classes)):
        ns = nat_counts.get(code, 0) / nat_total * 100
        rs = res_classes.get(code, 0) / new_total * 100
        rows.append((code, LEGEND.get(code, "unknown"), nat_counts.get(code, 0),
                     res_classes.get(code, 0), round(ns, 3), round(rs, 3), round(rs - ns, 3)))
    with (OUT / "landcover_class_legend.csv").open("w", newline="", encoding="utf-8") as f:
        f.write("code,class_name,native_10m_pixels,grid_30m_pixels,native_share_pct,"
                "grid_share_pct,share_change_pp\n")
        for r in rows:
            f.write(",".join(str(x) for x in r) + "\n")

    rep["aggregation"] = {
        "method": "rasterio.warp.reproject with Resampling.mode (majority class)",
        "why": "categorical product; bilinear/bicubic would invent non-existent class codes "
               "and nearest would alias the 10 m pattern. Mode is the defensible reduction.",
        "valid_pixels_district": new_total,
        "district_pixels": int(dmask.sum()),
        "nodata_inside_district": int((lc_district[dmask] == NODATA).sum()),
        "pixels_set_to_nodata_outside_district": int((~dmask).sum()),
        "classes_retained": sorted(res_classes),
        "unexpected_codes": sorted(c for c in res_classes if c not in LEGEND),
        "max_abs_share_change_pp": round(max(abs(r[6]) for r in rows), 3),
        "disagreement_vs_nearest_pct": round(
            float((lc_district[dmask] != lc_nn[dmask]).mean() * 100), 2),
        "interpretation": "a 2021 10 m snapshot reduced to 30 m; effective resolution stays "
                          "30 m, nothing finer is created",
    }

    with rasterio.open(
        OUT / "landcover_worldcover2021_30m_district.tif", "w", driver="GTiff",
        width=W, height=H, count=1, dtype="uint8", crs=crs, transform=tf_grid,
        nodata=NODATA, compress="deflate", tiled=True, blockxsize=256, blockysize=256,
    ) as ds:
        ds.write(lc_district, 1)
        ds.set_band_description(1, "ESA WorldCover 2021 v200 class code")
        ds.update_tags(source=str(SRC.relative_to(ROOT)), script="scripts/p3_landcover.py",
                       resampling="mode (majority of contributing 10 m cells)",
                       product_year="2021", nodata_semantics="0 = outside district / no data",
                       legend=json.dumps(LEGEND))

    (OUT / "landcover_validation.json").write_text(json.dumps(rep, indent=2), encoding="utf-8")
    print(json.dumps(rep, indent=2))


if __name__ == "__main__":
    main()
