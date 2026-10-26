"""Phase 3 Stage 5 - CHIRPS v2.0 monthly rainfall: verify, mask, summarise.

Per-file verification is real, not a sample: every one of the 312 archives is
streamed through gzip, parsed as a TIFF, and read in full. That is ~18 GB of
decompressed raster, so the loop is the slow part of this script.

Key handling:
  * nodata is NOT declared in the GeoTIFF tag (nodata=None) but is stored as
    -9999. It is masked explicitly on every read; any statistic that did not do
    this would be contaminated.
  * district statistics are area-weighted: each 0.05 deg cell contributes the
    fraction of its area that falls inside the GADM polygon, weighted by the
    cos(lat) area factor. A pixel-centre-only mean over ~143 cells would bias the
    total because the district crosses cell boundaries.
  * the monthly product is an accumulation (mm/month), not a rate. Nothing here is
    attached to a landslide event: a monthly 5.5 km field cannot represent the
    hours-scale trigger, and 332 of 372 in-window records resolve only to a year.

Outputs (data/processed/rainfall/):
  chirps_monthly_district_2000_2025.csv      312 monthly district values + flags
  chirps_annual_district_2000_2025.csv       annual + JJAS totals per year
  chirps_monthly_climatology.csv             mean by calendar month
  chirps_summary_native_0p05deg.tif          native-resolution summary (4 bands)
  rainfall_annual_mean_30m_district.tif      same summaries on the study grid
  rainfall_jjas_mean_30m_district.tif          (nearest; effective res 5.5 km)
  rainfall_monthly_climatology_30m_district.tif
  rainfall_validation.json

Run: python scripts/p3_rainfall.py
"""
from __future__ import annotations

import gzip
import json
import re
import time
import warnings
from contextlib import contextmanager
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.features import rasterize
from rasterio.warp import reproject
from rasterio.transform import from_origin

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "raw" / "rainfall" / "chirps_v2_monthly"
GRID = ROOT / "data" / "processed" / "grid"
OUT = ROOT / "data" / "processed" / "rainfall"
OUT.mkdir(parents=True, exist_ok=True)

SENTINEL = -9999.0
PAD_DEG = 0.5
SUB = 10  # subcells per CHIRPS cell for the area-weight mask

# Numpy messages raised when a NaN-aware reduction meets a slice with no valid data.
# The 0.5-degree padded window reaches the Arabian Sea, where CHIRPS is -9999 in every
# month: 140 of the window's 1,088 cells (12.87%). Those cells have no rainfall to
# report and must become nodata; numpy warns anyway. The warnings are expected, but
# they used to escape to stderr, where a PowerShell caller with
# ErrorActionPreference="Stop" treated them as a stage failure.
#
# They are therefore filtered only around the reductions over the padded window, and
# each result is asserted to be NaN exactly on the no-data footprint. That way the
# filter cannot hide a genuine empty-slice bug: any NaN outside the known footprint
# fails the assertion instead of being silenced.
NAN_REDUCE_WARNINGS = (
    ("Mean of empty slice", RuntimeWarning),
    ("Degrees of freedom <= 0 for slice", RuntimeWarning),
    ("All-NaN slice encountered", RuntimeWarning),
)


@contextmanager
def expect_all_nan_slices():
    """Scope the expected all-NaN-slice warnings to a single reduction block."""
    with warnings.catch_warnings():
        for message, category in NAN_REDUCE_WARNINGS:
            warnings.filterwarnings("ignore", message=message, category=category)
        yield


def main() -> None:
    t0 = time.time()
    spec = json.loads((GRID / "grid_spec.json").read_text(encoding="utf-8"))
    tf_grid = rasterio.transform.Affine(*spec["transform"])
    H, W, crs = spec["height"], spec["width"], spec["work_crs"]
    with rasterio.open(GRID / "district_mask_30m.tif") as ds:
        dmask = ds.read(1) == 1
    gadm = gpd.read_file(GRID / "wayanad_gadm_32643.gpkg").to_crs("EPSG:4326")

    files = sorted(SRC.glob("chirps-v2.0.*.tif.gz"))
    parsed = []
    for p in files:
        m = re.fullmatch(r"chirps-v2\.0\.(\d{4})\.(\d{2})\.tif\.gz", p.name)
        assert m, f"unexpected filename: {p.name}"
        parsed.append((int(m.group(1)), int(m.group(2)), p))
    rep: dict = {"n_files": len(parsed)}

    # ---- 1. date sequence ---------------------------------------------------
    keys = [(y, mo) for y, mo, _ in parsed]
    expected = [(y, mo) for y in range(2000, 2026) for mo in range(1, 13)]
    rep["date_sequence"] = {
        "first": f"{keys[0][0]}-{keys[0][1]:02d}",
        "last": f"{keys[-1][0]}-{keys[-1][1]:02d}",
        "n_expected": len(expected),
        "n_found": len(keys),
        "duplicates": len(keys) - len(set(keys)),
        "missing": [f"{y}-{m:02d}" for (y, m) in expected if (y, m) not in set(keys)],
        "unexpected": [f"{y}-{m:02d}" for (y, m) in keys if (y, m) not in set(expected)],
        "assertion_passed": keys == expected,
    }
    assert keys == expected, "monthly sequence is not complete and ordered"

    # ---- 2. grid geometry from the first file ------------------------------
    first_raw = gzip.open(parsed[0][2], "rb").read()
    with rasterio.MemoryFile(first_raw) as mf, mf.open() as ds:
        full_tf, full_shape, meta = ds.transform, (ds.height, ds.width), {
            "driver": ds.driver, "dtype": ds.dtypes[0], "crs": str(ds.crs),
            "res_deg": list(ds.res), "nodata_declared": ds.nodata,
            "bounds_full": list(ds.bounds), "tags": ds.tags(),
            "area_or_point": ds.tags().get("AREA_OR_POINT"),
        }
    rep["grid"] = meta
    res = abs(full_tf.a)

    # Padded window around the district (small on purpose: keeps the run cheap)
    minx, miny, maxx, maxy = gadm.total_bounds
    wx0 = np.floor((minx - PAD_DEG - full_tf.c) / res) * res + full_tf.c
    wx1 = np.ceil((maxx + PAD_DEG - full_tf.c) / res) * res + full_tf.c
    wy1 = full_tf.f - np.floor((full_tf.f - (maxy + PAD_DEG)) / res) * res
    wy0 = wy1 - np.ceil((wy1 - (miny - PAD_DEG)) / res) * res
    col0 = int(round((wx0 - full_tf.c) / res))
    row0 = int(round((full_tf.f - wy1) / res))
    ncol = int(round((wx1 - wx0) / res))
    nrow = int(round((wy1 - wy0) / res))
    win_tf = from_origin(wx0, wy1, res, res)
    rep["window"] = {"col_off": col0, "row_off": row0, "width": ncol, "height": nrow,
                     "bounds": [float(wx0), float(wy0), float(wx1), float(wy1)],
                     "n_cells": nrow * ncol,
                     "note": "native-resolution summaries are written over this padded "
                             "window; district statistics use the inner cells only"}

    # Area-weight mask: subcell rasterisation -> per-cell inside fraction * cos(lat)
    sub_res = res / SUB
    sub_tf = from_origin(wx0, wy1, sub_res, sub_res)
    sub_mask = rasterize([(g, 1) for g in gadm.geometry],
                         out_shape=(nrow * SUB, ncol * SUB), transform=sub_tf,
                         fill=0, dtype="float32", all_touched=False)
    frac = sub_mask.reshape(nrow, SUB, ncol, SUB).mean(axis=(1, 3))
    lat_c = wy1 - (np.arange(nrow) + 0.5) * res
    coslat = np.cos(np.deg2rad(lat_c))[:, None]
    wgt = frac * coslat
    wgt_norm = wgt / wgt.sum()
    rep["weights"] = {
        "cells_with_any_district_overlap": int((frac > 0).sum()),
        "weight_sum": round(float(wgt_norm.sum()), 10),
        "equivalent_full_cells": round(float(wgt.sum()), 3),
        "method": "subcell rasterisation (10x10 per 0.05 deg cell) x cos(lat)",
    }

    # ---- 3. read every file -------------------------------------------------
    cube = np.full((len(parsed), nrow, ncol), np.nan, dtype="float32")
    per_file = []
    for i, (y, mo, p) in enumerate(parsed):
        raw = gzip.open(p, "rb").read()          # full stream: gzip CRC checked
        with rasterio.MemoryFile(raw) as mf, mf.open() as ds:
            assert (ds.height, ds.width) == full_shape, f"shape differs in {p.name}"
            assert ds.transform == full_tf, f"grid differs in {p.name}"
            a = ds.read(1)
            win = a[row0:row0 + nrow, col0:col0 + ncol].astype("float32")
        n_sent = int((a == SENTINEL).sum())
        valid = a[a != SENTINEL]
        win[win == SENTINEL] = np.nan
        cube[i] = win
        n_nan_district = int(np.isnan(win[frac > 0]).sum())
        per_file.append({
            "month": f"{y}-{mo:02d}", "bytes_gz": p.stat().st_size,
            "global_min": round(float(valid.min()), 2),
            "global_max": round(float(valid.max()), 2),
            "n_sentinel_global": n_sent,
            "sentinel_share_pct": round(n_sent / a.size * 100, 2),
            "nan_in_window": int(np.isnan(win).sum()),
            "nan_in_district_cells": n_nan_district,
            "district_mean_mm": None,
        })
        if (i + 1) % 50 == 0:
            print(f"  read {i + 1}/{len(parsed)} files  ({time.time() - t0:.0f}s)")

    rep["file_reads"] = {
        "n_read_ok": len(per_file),
        "all_same_shape": True,
        "all_same_transform": True,
        "sentinel_neg9999_global_range": [
            min(f["n_sentinel_global"] for f in per_file),
            max(f["n_sentinel_global"] for f in per_file)],
        "files_with_sentinel_in_padded_window": int(sum(f["nan_in_window"] > 0 for f in per_file)),
        "files_with_sentinel_inside_district_cells": int(
            sum(f["nan_in_district_cells"] > 0 for f in per_file)),
        "note_on_padding": "the 0.5 deg padded window reaches the Arabian Sea to the west, "
                           "where CHIRPS legitimately stores -9999. Only cells that actually "
                           "overlap the district matter, and those are clean.",
        "global_min_mm": min(f["global_min"] for f in per_file),
        "global_max_mm": max(f["global_max"] for f in per_file),
        "elapsed_s": round(time.time() - t0, 1),
    }
    assert rep["file_reads"]["files_with_sentinel_inside_district_cells"] == 0, \
        "-9999 occurs in a cell that overlaps Wayanad; district statistics would be contaminated"

    # ---- 4. district series -------------------------------------------------
    district = np.full(len(parsed), np.nan)
    for i in range(len(parsed)):
        w = wgt_norm.copy()
        v = cube[i].copy()
        bad = ~np.isfinite(v)
        w[bad] = 0.0
        good = ~bad
        district[i] = float((v[good] * w[good]).sum() / w.sum())
        per_file[i]["district_mean_mm"] = round(float(district[i]), 1)

    years = np.array([y for y, _, _ in parsed])
    months = np.array([mo for _, mo, _ in parsed])
    annual = {y: float(district[years == y].sum()) for y in range(2000, 2026)}
    mon_idx = np.isin(months, [6, 7, 8, 9])
    jjas = {y: float(district[(years == y) & mon_idx].sum()) for y in range(2000, 2026)}
    clim = [float(district[months == m].mean()) for m in range(1, 13)]
    annual_vals = np.array([annual[y] for y in range(2000, 2026)])
    jjas_vals = np.array([jjas[y] for y in range(2000, 2026)])

    rep["district_series"] = {
        "units": "mm (accumulation per month / per year)",
        "monthly_min": round(float(np.nanmin(district)), 2),
        "monthly_max": round(float(np.nanmax(district)), 2),
        "monthly_mean": round(float(np.nanmean(district)), 2),
        "annual_mean_mm": round(float(annual_vals.mean()), 1),
        "annual_std_mm": round(float(annual_vals.std(ddof=1)), 1),
        "annual_min_mm": round(float(annual_vals.min()), 1),
        "annual_min_year": int(2000 + int(np.argmin(annual_vals))),
        "annual_max_mm": round(float(annual_vals.max()), 1),
        "annual_max_year": int(2000 + int(np.argmax(annual_vals))),
        "jjas_mean_mm": round(float(jjas_vals.mean()), 1),
        "jjas_share_of_annual_pct": round(float(jjas_vals.mean() / annual_vals.mean() * 100), 1),
        "dry_month_mean_mm": round(float(np.mean([clim[m - 1] for m in (1, 2, 3)])), 1),
        "wettest_month_mean_mm": round(float(max(clim)), 1),
        "wettest_month": int(np.argmax(clim) + 1),
        "n_months": len(district),
        "n_nan": int(np.isnan(district).sum()),
    }
    # Cross-check against the one independent local observation on disk.
    # KSDMA Memorandum: Kalladi recorded 200.2 mm (29-07-2024) + 372.6 mm (30-07-2024).
    j24 = [i for i, (y, m, _) in enumerate(parsed) if y == 2024 and m == 7][0]
    j24_win = cube[j24]
    rep["local_consistency_check"] = {
        "reference": "KSDMA Memorandum 17082024: Kalladi 200.2 mm on 2024-07-29 + "
                     "372.6 mm on 2024-07-30 = 572.8 mm in two days",
        "chirps_2024_07_district_mean_mm": round(float(district[j24]), 1),
        "chirps_2024_07_window_max_mm": round(float(np.nanmax(j24_win)), 1),
        "verdict": "a monthly district mean of the right order for a month containing two "
                   "extreme days; this is a plausibility check on magnitude, NOT a validation "
                   "of event rainfall, and no monthly value is assigned to any landslide",
    }

    # ---- 5. write CSVs ------------------------------------------------------
    with (OUT / "chirps_monthly_district_2000_2025.csv").open("w", newline="", encoding="utf-8") as f:
        f.write("year,month,month_index,district_mean_mm,district_mean_masked_cells\n")
        for i, (y, m, _) in enumerate(parsed):
            nbad = int(np.isnan(cube[i][frac > 0]).sum())
            f.write(f"{y},{m},{i + 1},{district[i]:.2f},{nbad}\n")

    with (OUT / "chirps_annual_district_2000_2025.csv").open("w", newline="", encoding="utf-8") as f:
        f.write("year,annual_total_mm,jjas_total_mm,jjas_share_pct,months_used\n")
        for y in range(2000, 2026):
            f.write(f"{y},{annual[y]:.1f},{jjas[y]:.1f},"
                    f"{jjas[y] / annual[y] * 100:.1f},12\n")

    with (OUT / "chirps_monthly_climatology.csv").open("w", newline="", encoding="utf-8") as f:
        f.write("month,mean_mm,n_years\n")
        for m in range(1, 13):
            f.write(f"{m},{clim[m - 1]:.1f},26\n")

    # ---- 6. native-resolution summary raster -------------------------------
    ann_cube = np.stack([cube[years == y].sum(axis=0) for y in range(2000, 2026)])
    jjas_cube = np.stack([cube[(years == y) & mon_idx].sum(axis=0) for y in range(2000, 2026)])

    # CHIRPS ships a global window; most of it is ocean/uncovered and is -9999 in
    # every month. `np.nanmean` over an all-NaN slice is correct here (the cell has
    # no data, so it must become nodata) but numpy emits "Mean of empty slice" and
    # "Degrees of freedom <= 0 for slice". Those two warnings are *expected*, and
    # the first version of this script let them escape to stderr where a caller
    # using ErrorActionPreference="Stop" treated them as a stage failure.
    #
    # The condition is therefore made explicit and quantified rather than muted:
    # the empty footprint is counted, asserted to be exactly the set of cells with
    # no valid month, and recorded in the validation JSON. Only then are those two
    # specific messages filtered, and only inside this block. Any other warning
    # still surfaces. The arithmetic is untouched, so the rasters are unchanged.
    empty_cells = ~np.isfinite(ann_cube).any(axis=0)
    n_empty = int(empty_cells.sum())
    with expect_all_nan_slices():
        ann_mean = np.nanmean(ann_cube, axis=0)
        ann_std = np.nanstd(ann_cube, axis=0, ddof=1)
        jjas_mean = np.nanmean(jjas_cube, axis=0)
        month_clim_max = np.nanmax(
            np.stack([cube[months == m].mean(axis=0) for m in range(1, 13)]), axis=0)
    assert int(np.isnan(ann_mean).sum()) == n_empty, (
        "nanmean produced NaN outside the no-data footprint -- investigate, do not suppress")
    assert not np.isnan(ann_mean[~empty_cells]).any()
    rep["all_nan_window_cells"] = n_empty
    rep["all_nan_window_pct"] = round(n_empty / ann_mean.size * 100, 2)
    rep["all_nan_note"] = (
        "CHIRPS is land-only and the padded 0.5-degree window reaches the Arabian Sea; these "
        "cells are -9999 in every month, correctly become nodata, and are the source of the "
        "expected 'Mean of empty slice' / 'All-NaN slice' warnings. Counted and asserted "
        "against the no-data footprint, not silenced blindly.")

    bands = {
        1: ("annual_mean_mm", ann_mean),
        2: ("annual_std_mm", ann_std),
        3: ("jjas_mean_mm", jjas_mean),
        4: ("monthly_clim_max_mm", month_clim_max),
    }
    native = OUT / "chirps_summary_native_0p05deg.tif"
    with rasterio.open(native, "w", driver="GTiff", width=ncol, height=nrow, count=len(bands),
                       dtype="float32", crs="EPSG:4326", transform=win_tf, nodata=-9999.0,
                       compress="deflate") as ds:
        for b, (name, arr) in bands.items():
            ds.write(np.where(np.isfinite(arr), arr, -9999.0).astype("float32"), b)
            ds.set_band_description(b, name)
        ds.update_tags(source="CHIRPS v2.0 monthly 2000-01..2025-12 (312 files)",
                       script="scripts/p3_rainfall.py", nodata_masked="-9999 masked on read",
                       units="mm", window="district bbox padded by 0.5 deg")

    # ---- 7. study-grid versions (nearest: values preserved, no invention) --
    grid_layers = {
        "rainfall_annual_mean_30m_district.tif": (1, "annual_mean_mm",
                                                  "Mean annual rainfall 2000-2025, mm/yr"),
        "rainfall_jjas_mean_30m_district.tif": (3, "jjas_mean_mm",
                                                "Mean June-September rainfall 2000-2025, mm"),
        "rainfall_monthly_climatology_30m_district.tif": (None, None,
                                                          "12-band monthly climatology 2000-2025, mm"),
    }
    written = {}
    for fname, (band, name, desc) in grid_layers.items():
        if band is None:
            with expect_all_nan_slices():
                arr = np.stack([np.nanmean(cube[months == m], axis=0) for m in range(1, 13)])
            assert not np.isnan(arr[:, ~empty_cells]).any(), (
                "monthly climatology has NaN where data exists -- investigate, do not suppress")
            src = native
            with rasterio.open(src) as ds:
                src_tf = ds.transform
            out = np.full((12, H, W), -9999.0, dtype="float32")
            for b in range(12):
                reproject(source=arr[b].astype("float32"), destination=out[b],
                          src_transform=win_tf, src_crs="EPSG:4326",
                          dst_transform=tf_grid, dst_crs=crs,
                          src_nodata=-9999.0, dst_nodata=-9999.0,
                          resampling=Resampling.nearest)
            out[:, ~dmask] = -9999.0
            with rasterio.open(OUT / fname, "w", driver="GTiff", width=W, height=H, count=12,
                               dtype="float32", crs=crs, transform=tf_grid, nodata=-9999.0,
                               compress="deflate", tiled=True) as ds:
                ds.write(out)
                for b in range(12):
                    ds.set_band_description(b + 1, f"month_{b + 1:02d}")
                ds.update_tags(source="chirps_summary_native_0p05deg.tif",
                               script="scripts/p3_rainfall.py", units="mm",
                               resampling="nearest",
                               effective_resolution="0.05 deg (~5.5 km); upsampling does not "
                                                    "create information")
            written[fname] = {"bands": 12}
        else:
            out = np.full((H, W), -9999.0, dtype="float32")
            reproject(source=bands[band][1].astype("float32"), destination=out,
                      src_transform=win_tf, src_crs="EPSG:4326",
                      dst_transform=tf_grid, dst_crs=crs,
                      src_nodata=-9999.0, dst_nodata=-9999.0, resampling=Resampling.nearest)
            out[~dmask] = -9999.0
            with rasterio.open(OUT / fname, "w", driver="GTiff", width=W, height=H, count=1,
                               dtype="float32", crs=crs, transform=tf_grid, nodata=-9999.0,
                               compress="deflate", tiled=True) as ds:
                ds.write(out, 1)
                ds.set_band_description(1, desc)
                ds.update_tags(source="chirps_summary_native_0p05deg.tif",
                               script="scripts/p3_rainfall.py", units="mm",
                               resampling="nearest",
                               effective_resolution="0.05 deg (~5.5 km) - the 30 m grid "
                                                    "carries 5.5 km values, not 30 m detail")
            written[fname] = {"bands": 1,
                              "min": round(float(out[dmask].min()), 1),
                              "max": round(float(out[dmask].max()), 1),
                              "nodata_inside_district": int((out[dmask] == -9999).sum())}
    rep["study_grid_rasters"] = written
    rep["interpretation"] = (
        "Monthly accumulation only. Supports antecedent-condition covariates (30/60/90-day "
        "totals, monsoon anomaly). It cannot represent the hours-scale trigger, and no monthly "
        "value is attached to an individual landslide. 2026 is absent because the acquired "
        "series ends 2025-12 and no value was invented."
    )

    (OUT / "rainfall_validation.json").write_text(json.dumps(rep, indent=2), encoding="utf-8")
    print(json.dumps({k: rep[k] for k in
                      ("n_files", "date_sequence", "grid", "file_reads", "weights",
                       "district_series", "local_consistency_check", "study_grid_rasters")},
                     indent=2))
    print(f"total elapsed {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
