"""Phase 4 — background (pseudo-absence) sampling.

Design: presence-background. A background point means *no mapped landslide at that
location in the available inventory*, and it lies outside the exclusion radius of every
mapped landslide. It is NOT a confirmed stable slope, and the resulting quantity is a
relative favourability surface, not a probability of failure.

Separation is enforced against the RECORDED positive coordinates, not against their grid
cells. A 30 m cell containing a positive can hold that record up to ~21 m (half the cell
diagonal) away from the cell centre, so a raster distance filter of 100 m around
positive *cells* does not guarantee 100 m around the points. The sampler therefore

  (a) removes everything further than the radius plus the largest positive-to-own-cell
      offset, and then
  (b) re-admits cells strictly outside that radius but inside the conservative margin
      after measuring the EXACT distance from the cell centre to the nearest recorded
      positive,

so the claimed radius is measured and true, rather than approximate.

The count follows from a stated sampling *density* over the eligible domain, not from
the number of positives: choosing a ratio would make the background size depend on how
many landslides happened to be mapped and would imply a class balance the data cannot
support.

Outputs (data/processed/sampling/):
  background_samples.csv        one row per sample, with provenance columns
  sampling_run_config.json      resolved parameters, seed, counts, library versions

Run:  python scripts/p4_sample_background.py
"""
from __future__ import annotations

import hashlib
import json
import pathlib

import numpy as np
import pandas as pd
import rasterio
from pyproj import Transformer
from scipy.ndimage import distance_transform_edt
from scipy.spatial import cKDTree

ROOT = pathlib.Path(__file__).resolve().parents[1]
CFG = json.loads((ROOT / "configs" / "p4_sampling.json").read_text(encoding="utf-8"))
OUT = ROOT / "data" / "processed" / "sampling"
OUT.mkdir(parents=True, exist_ok=True)


def sha256(p: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def predictor_layers() -> list[str]:
    """The 24 predictor layers Phase 3 validated, excluding the district mask."""
    inv = pd.read_csv(ROOT / CFG["grid"]["layer_inventory"], dtype=str)
    return [p for p in inv["layer"] if not p.startswith("grid/")]


def valid_mask(shape: tuple[int, int]) -> tuple[np.ndarray, dict]:
    """True where every band of every predictor layer has a usable value.

    Takes the shape only; the transform is not needed and is read per file.
    """
    m = np.ones(shape, dtype=bool)
    per_layer = {}
    for rel in predictor_layers():
        with rasterio.open(ROOT / "data" / "processed" / rel) as ds:
            if ds.shape != shape:
                raise SystemExit(f"{rel} has shape {ds.shape}, grid is {shape}")
            nod = ds.nodata
            ok = np.ones(shape, dtype=bool)
            for b in range(1, ds.count + 1):
                a = ds.read(b)
                good = np.isfinite(a.astype("float64"))
                if nod is not None:
                    good &= a != nod
                ok &= good
        per_layer[rel] = int((~ok).sum())
        m &= ok
    return m, per_layer


def main() -> None:
    bgcfg = CFG["background"]
    radius = float(bgcfg["exclusion_radius_m"])
    density = float(bgcfg["sampling_density_per_km2"])
    rng_seed = int(CFG["random_seed"])

    with rasterio.open(ROOT / CFG["grid"]["district_mask"]) as ds:
        dmask = ds.read(1) == 1
        transform = ds.transform
        shape = (ds.height, ds.width)

    audit = pd.read_csv(OUT / "eligibility_audit.csv")
    pos = audit[audit["p4_use"] == "POSITIVE_EVENT"].copy()
    assert len(pos) == pos["event_group_id"].nunique(), "positive set is not one-per-group"

    inv = pd.read_csv(ROOT / "data/processed/inventory/inventory_spatial_suitability.csv")
    inv = inv.set_index("source_record_id")
    tr = Transformer.from_crs(CFG["storage_crs"], CFG["analysis_crs"], always_xy=True)
    lon = inv.loc[pos["source_record_id"], "lon_original"].to_numpy(float)
    lat = inv.loc[pos["source_record_id"], "lat_original"].to_numpy(float)
    px, py = np.asarray(tr.transform(lon, lat))

    # Recorded positives -> their containing 30 m cells, and how far each record sits
    # from its own cell centre (the offset a raster filter would hide).
    rows, cols = rasterio.transform.rowcol(transform, px, py)
    rows, cols = np.asarray(rows), np.asarray(cols)
    inside = (rows >= 0) & (rows < shape[0]) & (cols >= 0) & (cols < shape[1])
    assert inside.all(), f"{int((~inside).sum())} positives fall outside the analysis grid"
    seed_cells = np.zeros(shape, dtype=bool)
    seed_cells[rows, cols] = True

    cell_r = np.hypot(transform.a / 2, abs(transform.e) / 2)      # ceil: half diagonal
    offsets = np.hypot(px - (transform.c + (cols + 0.5) * transform.a),
                       py - (transform.f + (rows + 0.5) * transform.e))
    max_offset = float(offsets.max())

    # Cell-centre distance to the nearest positive *cell*.
    dist_cell = distance_transform_edt(~seed_cells) * abs(transform.a)

    valid, per_layer_nodata = valid_mask(shape)
    n_invalid = {k: v for k, v in per_layer_nodata.items() if v}
    base = dmask & valid

    conservative = base & (dist_cell > radius + max_offset)
    band = base & (dist_cell > radius) & ~conservative
    band_rows, band_cols = np.nonzero(band)
    band_x = transform.c + (band_cols + 0.5) * transform.a
    band_y = transform.f + (band_rows + 0.5) * transform.e
    band_exact = cKDTree(np.c_[px, py]).query(np.c_[band_x, band_y], k=1)[0]
    band_keep = band_exact >= radius

    eligible = conservative | band
    # Cells in the band that fail the exact test must not be sampled.
    eligible[band_rows[~band_keep], band_cols[~band_keep]] = False

    n_district = int(dmask.sum())
    n_eligible = int(eligible.sum())
    area_km2 = n_eligible * abs(transform.a) * abs(transform.e) / 1e6
    n_target = int(round(density * area_km2))

    idx = np.flatnonzero(eligible.ravel())
    if n_target > idx.size:
        raise SystemExit(f"requested {n_target} samples but only {idx.size} cells eligible")
    rng = np.random.default_rng(rng_seed)
    picked = rng.choice(idx, size=n_target, replace=False)
    picked.sort()                       # stable output ordering (independent of masked set)

    pr, pc = np.unravel_index(picked, shape)
    cx = transform.c + (pc + 0.5) * transform.a
    cy = transform.f + (pr + 0.5) * transform.e
    tr_inv = Transformer.from_crs(CFG["analysis_crs"], CFG["storage_crs"], always_xy=True)
    slon, slat = tr_inv.transform(cx, cy)
    exact = cKDTree(np.c_[px, py]).query(np.c_[cx, cy], k=1)[0]

    assert float(exact.min()) >= radius, (
        f"sampler produced a bg point {exact.min():.1f} m from a positive "
        f"(radius {radius:.0f} m)")

    out = pd.DataFrame({
        "sample_id": [f"BG-{i + 1:05d}" for i in range(n_target)],
        "x_32643": np.round(cx, 2),
        "y_32643": np.round(cy, 2),
        "lon_4326": np.round(slon, 7),
        "lat_4326": np.round(slat, 7),
        "row": pr.astype(int),
        "col": pc.astype(int),
        "dist_to_nearest_positive_m": np.round(exact, 1),
        "in_district": True,
        "all_predictors_valid": True,
        "role": "background",
        "label": 0,
    })
    out.to_csv(OUT / "background_samples.csv", index=False, encoding="utf-8",
               lineterminator="\n")

    run = {
        "config_file": "configs/p4_sampling.json",
        "config_sha256": sha256(ROOT / "configs" / "p4_sampling.json"),
        "random_seed": rng_seed,
        "analysis_crs": CFG["analysis_crs"],
        "storage_crs": CFG["storage_crs"],
        "cell_size_m": abs(transform.a),
        "grid": {"width": shape[1], "height": shape[0], "transform": list(transform)[:6]},
        "positives": int(len(pos)),
        "positives_sha256": sha256(OUT / "eligibility_audit.csv"),
        "exclusion_radius_m": radius,
        "sampling_density_per_km2": density,
        "separation": {
            "measured_against": "recorded positive coordinates (EPSG:32643)",
            "max_positive_to_own_cell_centre_m": round(max_offset, 2),
            "cell_half_diagonal_m": round(cell_r, 2),
            "exact_min_after_sampling_m": round(float(exact.min()), 1),
            "conservative_margin_m": round(radius + max_offset, 1),
            "band_cells_exact": int(band_keep.sum()),
            "band_cells_rejected_by_exact_test": int((~band_keep).sum()),
        },
        "district_cells": n_district,
        "district_km2": round(n_district * abs(transform.a) * abs(transform.e) / 1e6, 2),
        "cells_with_invalid_predictor": int((dmask & ~valid).sum()),
        "eligible_cells": n_eligible,
        "eligible_km2": round(area_km2, 2),
        "eligible_pct_of_district": round(100 * n_eligible / n_district, 3),
        "background_samples": n_target,
        "background_per_positive": round(n_target / len(pos), 2),
        "layers_with_nodata_in_district": n_invalid,
        "sampling_unit": "30 m grid cell centre, uniform without replacement",
        "interpretation": "background = no mapped landslide at this location in the "
                          "available inventory; not confirmed stable ground",
        "sensitivity": CFG["sensitivity"],
    }
    (OUT / "sampling_run_config.json").write_text(json.dumps(run, indent=2),
                                                  encoding="utf-8")

    print(f"positives            : {len(pos):>10,}")
    print(f"district             : {n_district:>10,} cells  {run['district_km2']:>9,.2f} km2")
    print(f"invalid predictor    : {run['cells_with_invalid_predictor']:>10,} cells removed")
    print(f"max pos cell offset  : {max_offset:>10.2f} m (half cell diagonal "
          f"{cell_r:.2f} m)")
    print(f"band cells kept      : {int(band_keep.sum()):>10,}  "
          f"rejected by exact test {int((~band_keep).sum()):,}")
    print(f"eligible (> {radius:.0f} m) : {n_eligible:>10,} cells  "
          f"{area_km2:>9,.2f} km2  ({run['eligible_pct_of_district']}% of district)")
    print(f"background samples   : {n_target:>10,}  at {density} / km2")
    print(f"per positive         : {run['background_per_positive']:>10}")
    print(f"exact min separation : {exact.min():>10.1f} m")
    print(f"seed                 : {rng_seed}")
    print(f"\nwritten -> {OUT / 'background_samples.csv'}")
    print(f"written -> {OUT / 'sampling_run_config.json'}")


if __name__ == "__main__":
    main()
