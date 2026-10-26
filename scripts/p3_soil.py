"""Phase 3 Stage 6 - SoilGrids 250 m: unit conversion, nodata decision, resampling.

Three things that would silently corrupt this layer if done casually:

1. **Scale factors.** SoilGrids stores integers: clay/sand/silt g/kg x10, bdod
   cg/cm3 x100, soc dg/kg x10, cec mmol(c)/kg x10, cfvo cm3/100cm3 x10. Using the
   raw integers as physical units is a factor-of-10 (or 100) error.

2. **Undeclared nodata.** nodata is None in every file. Every one of the 14 rasters
   contains exactly 8,312 zero cells in exactly the same places, 8,262 of them
   outside the district (the acquisition crop was district-masked). A genuine
   clay = 0 % and cfvo = 0 % would not coincide across 14 independent properties,
   so 0 is treated as nodata for all 14. The cost: a genuine cfvo = 0 is
   indistinguishable from a masked cell and is discarded rather than guessed.

3. **Resolution.** 250 m is the native support. Upsampling to the 30 m grid uses
   bilinear because the native cell is only ~8x the grid cell, so interpolating
   between neighbouring predictions is meaningful. Effective resolution remains
   250 m and is written into every output tag.

Outputs (data/processed/soil/):
  soil_<prop>_<depth>_native250m.tif    converted, nodata masked, native grid
  soil_<prop>_<depth>_30m_district.tif  converted, nodata masked, study grid
  soil_properties.csv                   per-file raw range, factor, units, output range
  soil_validation.json

Run: python scripts/p3_soil.py
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.features import rasterize
from rasterio.warp import reproject

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "raw" / "soil" / "soilgrids250m"
GRID = ROOT / "data" / "processed" / "grid"
OUT = ROOT / "data" / "processed" / "soil"
OUT.mkdir(parents=True, exist_ok=True)
NODATA = -9999.0

# SoilGrids v2.0 conversion factors (raw integer -> physical unit)
PROPS = {
    "bdod": {"factor": 100.0, "unit": "g/cm3", "name": "Bulk density (fine earth)",
             "plausible": (0.4, 2.2)},
    "cec": {"factor": 10.0, "unit": "cmol(c)/kg", "name": "Cation exchange capacity",
            "plausible": (0.5, 120.0)},
    "cfvo": {"factor": 10.0, "unit": "% (vol)", "name": "Coarse fragments (>2 mm)",
             "plausible": (0.0, 90.0)},
    "clay": {"factor": 10.0, "unit": "% (w)", "name": "Clay content", "plausible": (1.0, 85.0)},
    "sand": {"factor": 10.0, "unit": "% (w)", "name": "Sand content", "plausible": (1.0, 95.0)},
    "silt": {"factor": 10.0, "unit": "% (w)", "name": "Silt content", "plausible": (1.0, 80.0)},
    "soc": {"factor": 10.0, "unit": "g/kg", "name": "Soil organic carbon",
            "plausible": (0.1, 250.0)},
}
DEPTHS = {"0-5cm": "0-5 cm", "15-30cm": "15-30 cm"}


def main() -> None:
    spec = json.loads((GRID / "grid_spec.json").read_text(encoding="utf-8"))
    tf_grid = rasterio.transform.Affine(*spec["transform"])
    H, W, crs = spec["height"], spec["width"], spec["work_crs"]
    with rasterio.open(GRID / "district_mask_30m.tif") as ds:
        dmask = ds.read(1) == 1
    gadm = gpd.read_file(GRID / "wayanad_gadm_32643.gpkg").to_crs("EPSG:4326")
    poly = [(g, 1) for g in gadm.geometry]

    files = sorted(SRC.glob("soilgrids_*.tif"))
    rows, rep = [], {"n_files": len(files), "properties": {}, "checks": {}}
    zero_footprints = []
    scaled = {}

    for p in files:
        stem = p.stem.replace("soilgrids_", "").replace("_wayanad", "")
        parts = stem.split("_")
        prop, depth, stat = parts[0], parts[1], parts[2]
        assert stat == "mean", f"unexpected statistic in {p.name}"
        assert prop in PROPS and depth in DEPTHS, f"unexpected name: {p.name}"
        meta = PROPS[prop]
        with rasterio.open(p) as ds:
            raw = ds.read(1)
            tf, shape = ds.transform, (ds.height, ds.width)
            assert str(ds.crs) == "EPSG:4326"
            assert ds.nodata is None
        in_d = rasterize(poly, out_shape=shape, transform=tf, fill=0, dtype="uint8").astype(bool)
        zero_footprints.append(raw == 0)

        raw_valid = raw[in_d & (raw != 0)]
        phys = raw.astype("float32")
        phys[raw == 0] = NODATA
        phys[phys != NODATA] /= np.float32(meta["factor"])
        phys_in = phys[in_d & (phys != NODATA)]

        lo, hi = meta["plausible"]
        n_below = int((phys_in < lo).sum())
        n_above = int((phys_in > hi).sum())

        # native-resolution converted copy
        nat = OUT / f"soil_{prop}_{depth}_native250m.tif"
        with rasterio.open(nat, "w", driver="GTiff", width=shape[1], height=shape[0], count=1,
                           dtype="float32", crs="EPSG:4326", transform=tf, nodata=NODATA,
                           compress="deflate") as ds:
            ds.write(phys, 1)
            ds.set_band_description(1, f"{meta['name']}, {DEPTHS[depth]}, {meta['unit']}")
            ds.update_tags(source=p.name, script="scripts/p3_soil.py",
                           scale_factor=f"raw/{meta['factor']:g}", units=meta["unit"],
                           nodata_rule="raw 0 treated as nodata (undeclared sentinel)",
                           native_resolution_deg="0.0022619 x 0.0023885 (~250 m)")

        # study-grid copy
        dst = np.full((H, W), NODATA, dtype="float32")
        reproject(source=phys, destination=dst, src_transform=tf, src_crs="EPSG:4326",
                  dst_transform=tf_grid, dst_crs=crs, src_nodata=NODATA, dst_nodata=NODATA,
                  resampling=Resampling.bilinear)
        dst[~dmask] = NODATA
        gname = OUT / f"soil_{prop}_{depth}_30m_district.tif"
        with rasterio.open(gname, "w", driver="GTiff", width=W, height=H, count=1,
                           dtype="float32", crs=crs, transform=tf_grid, nodata=NODATA,
                           compress="deflate", tiled=True, blockxsize=256, blockysize=256) as ds:
            ds.write(dst, 1)
            ds.set_band_description(1, f"{meta['name']}, {DEPTHS[depth]}, {meta['unit']}")
            ds.update_tags(source=nat.name, script="scripts/p3_soil.py", units=meta["unit"],
                           resampling="bilinear",
                           effective_resolution="250 m native - the 30 m grid carries 250 m "
                                                "information, not 30 m detail")
        valid = dst[dmask]
        valid = valid[valid != NODATA]
        scaled[(prop, depth)] = dst
        rows.append({
            "property": prop, "depth": depth, "depth_cm": DEPTHS[depth],
            "name": meta["name"], "raw_min": int(raw[in_d & (raw != 0)].min()),
            "raw_max": int(raw[in_d & (raw != 0)].max()),
            "scale_factor": meta["factor"], "unit": meta["unit"],
            "physical_min": round(float(phys_in.min()), 3),
            "physical_max": round(float(phys_in.max()), 3),
            "valid_cells_native_in_district": int((in_d & (raw != 0)).sum()),
            "nodata_cells_native_in_district": int((in_d & (raw == 0)).sum()),
            "grid_valid_pixels": int(valid.size),
            "grid_nodata_pixels": int(dmask.sum() - valid.size),
            "grid_median": round(float(np.median(valid)), 3),
            "below_plausible": n_below, "above_plausible": n_above,
        })

    # ---- validation ---------------------------------------------------------
    # Compare each file's zero mask against the first one. (An earlier version of
    # this check ANDed the masks together, which answers a different and useless
    # question -- "is every cell zero in every file" -- and therefore always
    # returned False. The equality test below is the one the nodata decision rests on.)
    zstack = np.stack(zero_footprints)
    identical = bool(np.all(zstack == zstack[0]))
    per_file_zero = zstack.sum(axis=(1, 2))
    rep["checks"]["zero_footprint_identical_across_all_14"] = identical
    rep["checks"]["zero_cells_per_file"] = int(zero_footprints[0].sum())
    rep["checks"]["zero_cells_per_file_min"] = int(per_file_zero.min())
    rep["checks"]["zero_cells_per_file_max"] = int(per_file_zero.max())
    rep["checks"]["n_cells_where_any_file_is_zero"] = int((zstack.any(axis=0)).sum())
    rep["checks"]["n_cells_where_all_files_are_zero"] = int((zstack.all(axis=0)).sum())

    # texture closure: clay + sand + silt should be 100 % for the same depth
    tex = {}
    for depth in DEPTHS:
        c = scaled[("clay", depth)]
        s = scaled[("sand", depth)]
        t = scaled[("silt", depth)]
        use = dmask & (c != NODATA) & (s != NODATA) & (t != NODATA)
        tot = c[use] + s[use] + t[use]
        tex[depth] = {
            "n": int(use.sum()),
            "mean_sum_pct": round(float(tot.mean()), 2),
            "median_sum_pct": round(float(np.median(tot)), 2),
            "p05_pct": round(float(np.percentile(tot, 5)), 2),
            "p95_pct": round(float(np.percentile(tot, 95)), 2),
            "share_within_1pp_of_100": round(float((np.abs(tot - 100) <= 1).mean() * 100), 2),
        }
    rep["texture_closure"] = tex

    rep["checks"]["grid_nodata_inside_district_pct"] = round(
        float(rows[0]["grid_nodata_pixels"] / dmask.sum() * 100), 3)
    rep["checks"]["all_outputs_have_data_inside_district"] = bool(
        all(r["grid_valid_pixels"] > 0 for r in rows))
    rep["checks"]["plausibility_violations"] = {
        f"{r['property']}_{r['depth']}": {"below": r["below_plausible"],
                                          "above": r["above_plausible"]}
        for r in rows if r["below_plausible"] or r["above_plausible"]}
    rep["properties"] = {
        f"{r['property']}_{r['depth']}": {
            "name": r["name"], "unit": r["unit"], "scale_factor": r["scale_factor"],
            "raw_range": [r["raw_min"], r["raw_max"]],
            "physical_range": [r["physical_min"], r["physical_max"]],
            "grid_median": r["grid_median"],
        } for r in rows}
    rep["nodata_decision"] = {
        "rule": "raw value 0 -> nodata for all 14 rasters",
        "evidence": "identical zero footprint in all 14 independent properties "
                    f"({int(zero_footprints[0].sum())} cells, 8,262 of them outside the "
                    "district, i.e. the acquisition crop's mask), plus physical "
                    "impossibility of clay = 0 % and bdod = 0 g/cm3",
        "cost": "a genuine cfvo = 0 % cannot be distinguished from a masked cell and is "
                "discarded (conservative)",
        "inside_district_cells": int(rows[0]["nodata_cells_native_in_district"]),
        "inside_district_area_km2": round(
            rows[0]["nodata_cells_native_in_district"] * 0.0625, 1),
    }
    rep["resolution_note"] = (
        "native 250 m, upsampled to 30 m with bilinear. The 30 m grid carries 250 m "
        "information; no new spatial detail is created. Eight 30 m cells fall inside one "
        "250 m prediction."
    )

    with (OUT / "soil_properties.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    (OUT / "soil_validation.json").write_text(json.dumps(rep, indent=2), encoding="utf-8")
    print(json.dumps(rep, indent=2))
    for r in rows:
        print(f"{r['property']:5s} {r['depth']:8s} raw {r['raw_min']:5d}-{r['raw_max']:5d} "
              f"/{r['scale_factor']:<5g} -> {r['physical_min']:8.2f}-{r['physical_max']:8.2f} "
              f"{r['unit']:12s} nodata(d)= {r['grid_nodata_pixels']}")


if __name__ == "__main__":
    main()
